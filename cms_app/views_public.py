from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core_micelio.context_processors import site_root_path
from ontologizar_app.models import Concept, Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode
from ontologizar_app.services.jsonld import topic_page_jsonld
from ontologizar_app.services.subject_body import render_subject_body
from ontologizar_app.services.topic_body import render_topic_body
from ontologizar_app.services.wiki_content import (
    get_concept_references,
    get_concept_wiki_body,
    save_concept_references,
    save_concept_wiki_body,
    save_subject_description,
    save_subject_material,
)
from ontologizar_app.services.concept_indicators import (
    compute_concept_indicators,
    dictionary_concept_rows,
    topic_indicator_anchors,
)
from ontologizar_app.services.knowledge_depth import build_taxonomy_tree_roots
from ontologizar_app.services.subject_curriculum import (
    ROLE_LABELS, concept_classifications, subject_curriculum_profile,
)
from ontologizar_app.services.taxonomy_nodes import add_taxonomy_node
from research_app.models import LearningMarker

CMS_LOGIN = "/cms/login/"


def _topic_markers(concept):
    """Una entrada por cuaderno que cita este concepto."""
    seen = {}
    for marker in LearningMarker.objects.filter(
        concept_uuid=concept.uuid,
    ).select_related("project").order_by("-created_at", "-id"):
        if marker.project_id not in seen:
            seen[marker.project_id] = marker
    return list(seen.values())


def biblioteca_index(request):
    return render(request, "cms/public/index.html", {
        "subjects": Subject.objects.filter(is_active=True),
        "taxonomies": Taxonomy.objects.filter(is_active=True).order_by("name")[:6],
    })


def subject_detail(request, slug):
    subject = get_object_or_404(Subject, slug=slug, is_active=True)
    profile = subject_curriculum_profile(subject)
    taxonomy_sections = []
    for role in ("class", "property", "thematic"):
        rows = profile.taxonomies_by_role.get(role, [])
        if rows:
            taxonomy_sections.append({
                "role": role,
                "role_label": ROLE_LABELS[role],
                "rows": rows,
            })
    return render(request, "cms/public/subject.html", {
        "subject": subject,
        "body_html": render_subject_body(subject, site_root=site_root_path(settings.SITE_URL)),
        "edit_url": reverse("biblioteca:subject_edit", kwargs={"slug": subject.slug}),
        "curriculum": profile,
        "taxonomy_sections": taxonomy_sections,
    })


def dictionary_detail(request, subject_slug, dict_slug):
    dictionary = get_object_or_404(Dictionary, subject__slug=subject_slug, slug=dict_slug, is_active=True)
    return render(request, "cms/public/dictionary.html", {
        "dictionary": dictionary,
        "concept_rows": dictionary_concept_rows(dictionary),
    })


def taxonomy_list(request):
    return render(request, "cms/public/taxonomy_list.html", {
        "taxonomies": Taxonomy.objects.filter(is_active=True).order_by("name"),
    })


def taxonomy_detail(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    roots = build_taxonomy_tree_roots(taxonomy)
    return render(request, "cms/public/taxonomy.html", {
        "taxonomy": taxonomy,
        "roots": roots,
        "cms_editor_url": reverse("cms:taxonomy_editor", kwargs={"uuid": taxonomy.uuid}),
    })


@login_required(login_url=CMS_LOGIN)
def taxonomy_add_node(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    if request.method != "POST":
        return redirect("biblioteca:taxonomy", slug=slug)

    label = request.POST.get("label", "").strip()
    parent_uuid = request.POST.get("parent_uuid", "").strip()
    parent = None
    if parent_uuid:
        parent = get_object_or_404(TaxonomyNode, uuid=parent_uuid, taxonomy=taxonomy)

    try:
        add_taxonomy_node(taxonomy, label, parent=parent)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Clase «{label}» añadida.")

    return redirect("biblioteca:taxonomy", slug=slug)


def topic_detail(request, uuid):
    concept = get_object_or_404(
        Concept.objects.prefetch_related(
            "definitions",
            "properties",
            "outgoing_relations__target__dictionary",
            "incoming_relations__source__dictionary",
        ),
        uuid=uuid,
    )
    markers = _topic_markers(concept)
    root = site_root_path(settings.SITE_URL)
    return render(request, "cms/public/topic.html", {
        "concept": concept,
        "body_html": render_topic_body(concept, site_root=root),
        "classifications": concept_classifications(concept),
        "markers": markers,
        "jsonld": topic_page_jsonld(concept, request),
        "indicators": compute_concept_indicators(concept),
        "indicator_anchors": topic_indicator_anchors(concept),
        "edit_url": reverse("biblioteca:topic_edit", kwargs={"uuid": concept.uuid}),
        "advanced_edit_url": reverse("cms:concept_edit", kwargs={"uuid": concept.uuid}),
    })


@login_required(login_url=CMS_LOGIN)
def topic_edit(request, uuid):
    concept = get_object_or_404(Concept, uuid=uuid)
    if request.method == "POST":
        save_concept_wiki_body(concept, request.POST.get("body", ""))
        save_concept_references(concept, request.POST.get("references", ""))
        messages.success(request, "Tema guardado.")
        return redirect("biblioteca:topic", uuid=concept.uuid)
    return render(request, "cms/public/topic_edit.html", {
        "concept": concept,
        "body_text": get_concept_wiki_body(concept),
        "references_text": get_concept_references(concept),
        "public_url": reverse("biblioteca:topic", kwargs={"uuid": concept.uuid}),
        "advanced_edit_url": reverse("cms:concept_edit", kwargs={"uuid": concept.uuid}),
    })


@login_required(login_url=CMS_LOGIN)
def subject_edit(request, slug):
    subject = get_object_or_404(Subject, slug=slug, is_active=True)
    if request.method == "POST":
        save_subject_description(subject, request.POST.get("description", ""))
        messages.success(request, "Asignatura guardada.")
        return redirect("biblioteca:subject", slug=subject.slug)
    return render(request, "cms/public/subject_edit.html", {
        "subject": subject,
        "materials": subject.materials.all(),
        "public_url": reverse("biblioteca:subject", kwargs={"slug": subject.slug}),
    })


@login_required(login_url=CMS_LOGIN)
def material_edit(request, slug, mat_slug):
    subject = get_object_or_404(Subject, slug=slug, is_active=True)
    material = get_object_or_404(SubjectMaterial, subject=subject, slug=mat_slug)
    if request.method == "POST":
        save_subject_material(
            material,
            title=request.POST.get("title", ""),
            summary=request.POST.get("summary", ""),
            body=request.POST.get("body", ""),
        )
        messages.success(request, "Sección guardada.")
        return redirect("biblioteca:subject", slug=subject.slug)
    return render(request, "cms/public/material_edit.html", {
        "subject": subject,
        "material": material,
        "public_url": reverse("biblioteca:subject", kwargs={"slug": subject.slug}),
    })
