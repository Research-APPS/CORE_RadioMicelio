from django.db.models import Count
from django.db.models.functions import TruncMonth

from logs_app.models import EventLog
from logs_app.platforms import get_platform


def _email_profile(email: str) -> str:
    email = (email or "").lower()
    if not email or "@" not in email:
        return "unknown"
    domain = email.split("@", 1)[1]
    if domain.endswith(".edu") or domain.endswith(".ac.") or "ucm" in domain:
        return "institutional"
    if any(v in domain for v in ("gmail", "hotmail", "yahoo", "outlook")):
        return "external"
    return "other"


def build_segment_summary(platform_slug: str) -> dict:
    spec = get_platform(platform_slug)
    if not spec:
        return {}

    qs = EventLog.objects.filter(spec.filter_q)
    total = qs.count()
    unique_users = qs.values("email").distinct().count()

    by_section = list(
        qs.values("name")
        .annotate(count=Count("pk"), unique_users=Count("email", distinct=True))
        .order_by("-count")[:20]
    )

    by_month = list(
        qs.annotate(month=TruncMonth("timestamp"))
        .values("month")
        .annotate(count=Count("pk"), unique_users=Count("email", distinct=True))
        .order_by("month")
    )

    # Pareto: top sections cover 80% traffic
    pareto_sections = by_section[:10]
    pareto_share = 0
    if total:
        pareto_share = round(sum(r["count"] for r in pareto_sections) / total * 100, 1)

    # Recurrence: users with >1 event
    user_counts = qs.values("email").annotate(n=Count("pk"))
    recurring = user_counts.filter(n__gt=1).count()
    recurrence_rate = round(recurring / unique_users * 100, 1) if unique_users else 0

    # Profile breakdown
    emails = qs.values_list("email", flat=True).distinct()[:5000]
    profiles = {"external": 0, "institutional": 0, "other": 0, "unknown": 0}
    for e in emails:
        profiles[_email_profile(e)] += 1

    return {
        "platform_slug": platform_slug,
        "platform_label": spec.label,
        "total_events": total,
        "unique_users": unique_users,
        "adoption": {"unique_users": unique_users, "total_events": total},
        "usage": {"by_section": by_section, "top_sections": by_section[:5]},
        "recurrence": {"recurring_users": recurring, "rate_percent": recurrence_rate},
        "pareto": {"top_sections": pareto_sections, "share_percent": pareto_share},
        "evolution": {"by_month": [
            {"month": r["month"].isoformat() if r["month"] else None, "count": r["count"], "unique_users": r["unique_users"]}
            for r in by_month
        ]},
        "profiles": profiles,
    }
