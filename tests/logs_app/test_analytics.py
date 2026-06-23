from django.test import TestCase
from django.utils import timezone

from logs_app.analytics import build_segment_summary
from logs_app.models import EventLog


class AnalyticsTests(TestCase):
    def test_segment_summary_counts_events(self):
        EventLog.objects.create(
            source_id=1, email="alumna@colegio.edu", timestamp=timezone.now(),
            name="leccion-hongos", application="aula-virtual", orig_id="1",
        )
        summary = build_segment_summary("aula-virtual")
        self.assertGreaterEqual(summary["total_events"], 1)
        self.assertIn("adoption", summary)
