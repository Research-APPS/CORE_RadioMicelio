from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ontologizar_app.models import Concept, ConceptDefinition, ConceptProperty, ConceptRelation, Dictionary, Taxonomy
from ontologizar_app.services.taxonomy_import import import_taxonomy_from_json, parse_indentation_to_json


@login_required
def dashboard(request):
    return render(request, "cms/dashboard.html", {
        "subjects_count": __import__("ontologizar_app.models", fromlist=["Subject"]).Subject.objects.filter(is_active=True).count(),
        "taxonomies": Taxonomy.objects.filter(is_active=True).order_by("name")[:12],
        "concepts": Concept.objects.select_related("dictionary__subject").order_by("-id")[:12],
    })


@login_required
def taxonomy_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        slug = request.POST.get("slug", "").strip()
        if name and slug:
            tax = Taxonomy.objects.create(name=name, slug=slug)
            return redirect("cms:taxonomy_editor", uuid=tax.uuid)
    return render(request, "cms/taxonomy_create.html")


@login_required
def taxonomy_editor(request, uuid):
    taxonomy = get_object_or_404(Taxonomy, uuid=uuid)
    dictionaries = Dictionary.objects.filter(is_active=True).select_related("subject")
    dictionary = None
    dict_id = request.POST.get("dictionary_id") or request.GET.get("dictionary_id")
    if dict_id:
        dictionary = dictionaries.filter(pk=dict_id).first()
    if request.method == "POST" and dictionary:
        text = request.POST.get("texto_taxonomia", "")
        data = parse_indentation_to_json(text)
        if not data:
            messages.error(request, "No se pudo parsear la taxonomía.")
        else:
            ok, err, total = import_taxonomy_from_json(taxonomy, dictionary, data, replace=True)
            if ok:
                messages.success(request, f"Taxonomía importada: {total} nodos.")
            else:
                messages.error(request, err)
    return render(request, "cms/taxonomy_editor.html", {
        "taxonomy": taxonomy, "dictionaries": dictionaries, "dictionary": dictionary,
    })


@login_required
def concept_edit(request, uuid):
    concept = get_object_or_404(Concept, uuid=uuid)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "definition":
            ConceptDefinition.objects.create(
                concept=concept, text=request.POST.get("text", "").strip(), kind=request.POST.get("kind", "definition"),
            )
        elif action == "property":
            ConceptProperty.objects.update_or_create(
                concept=concept, key=request.POST.get("key", "").strip(),
                defaults={"value": request.POST.get("value", "").strip()},
            )
        elif action == "relation":
            target = Concept.objects.filter(uuid=request.POST.get("target_uuid")).first()
            if target:
                ConceptRelation.objects.get_or_create(
                    source=concept, target=target, relation_type=request.POST.get("relation_type", "related"),
                )
        return redirect("cms:concept_edit", uuid=concept.uuid)
    return render(request, "cms/concept_edit.html", {
        "concept": concept,
        "definitions": concept.definitions.all(),
        "properties": concept.properties.all(),
        "relations": concept.outgoing_relations.select_related("target"),
        "taxonomies": concept.taxonomies(),
    })
