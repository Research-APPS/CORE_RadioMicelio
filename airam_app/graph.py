from django.conf import settings

from ontologizar_app.models import Concept, ConceptRelation, Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode
from research_app.models import LearningMarker, ProyectoInvestigacion, ScientificActivity, ScientificResult


def build_graph() -> dict:
    nodes = [{"id": "centro:radio-micelio", "type": "Institute", "label": getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio")}]
    edges = []
    seen_concepts = set()

    def add_concept(concept):
        cid = f"concepto:{concept.uuid}"
        if cid not in seen_concepts:
            nodes.append({"id": cid, "type": "Concept", "label": concept.label, "uuid": str(concept.uuid)})
            seen_concepts.add(cid)
            did = f"diccionario:{concept.dictionary.subject.slug}:{concept.dictionary.slug}"
            edges.append({"from": did, "to": cid, "relation": "has_concept"})
        return cid

    for subject in Subject.objects.filter(is_active=True):
        sid = f"asignatura:{subject.slug}"
        nodes.append({"id": sid, "type": "Subject", "label": subject.name, "uuid": str(subject.uuid)})
        edges.append({"from": "centro:radio-micelio", "to": sid, "relation": "has_subject"})
        for mat in subject.materials.all():
            mid = f"material:{subject.slug}:{mat.slug}"
            nodes.append({"id": mid, "type": "SubjectMaterial", "label": mat.title})
            edges.append({"from": sid, "to": mid, "relation": "has_material"})
        for dic in subject.dictionaries.filter(is_active=True):
            did = f"diccionario:{subject.slug}:{dic.slug}"
            nodes.append({"id": did, "type": "Dictionary", "label": dic.name})
            edges.append({"from": sid, "to": did, "relation": "has_dictionary"})

    for tax in Taxonomy.objects.filter(is_active=True):
        tid = f"taxonomia:{tax.slug}"
        nodes.append({"id": tid, "type": "Taxonomy", "label": tax.name})
        edges.append({"from": "centro:radio-micelio", "to": tid, "relation": "has_taxonomy"})
        for node in TaxonomyNode.objects.filter(taxonomy=tax, concept__isnull=False).select_related("concept"):
            cid = add_concept(node.concept)
            edges.append({"from": tid, "to": cid, "relation": "classifies"})

    for rel in ConceptRelation.objects.select_related("source", "target"):
        add_concept(rel.source)
        add_concept(rel.target)
        edges.append({
            "from": f"concepto:{rel.source.uuid}", "to": f"concepto:{rel.target.uuid}",
            "relation": rel.relation_type,
        })

    for project in ProyectoInvestigacion.objects.filter(activo=True):
        pid = f"proyecto:{project.acron or project.uuid}"
        nodes.append({"id": pid, "type": "Project", "label": project.titulo, "uuid": str(project.uuid)})
        edges.append({"from": "centro:radio-micelio", "to": pid, "relation": "has_project"})
        for marker in project.markers.all():
            mid = f"marcador:{marker.uuid}"
            cid = f"concepto:{marker.concept_uuid}"
            nodes.append({"id": mid, "type": "Marker", "label": marker.concept_label, "status": marker.status})
            edges.append({"from": pid, "to": mid, "relation": "marks"})
            edges.append({"from": mid, "to": cid, "relation": "references_concept"})
            if marker.subject_slug:
                edges.append({"from": pid, "to": f"asignatura:{marker.subject_slug}", "relation": "touches_subject"})
        for activity in project.activities.all():
            aid = f"actividad:{project.acron}:{activity.slug}"
            nodes.append({"id": aid, "type": "Activity", "label": activity.title})
            edges.append({"from": pid, "to": aid, "relation": "has_activity"})
            for result in activity.results.all():
                rid = f"resultado:{result.uuid}"
                nodes.append({"id": rid, "type": "Result", "label": result.title, "result_type": result.result_type})
                edges.append({"from": aid, "to": rid, "relation": "produces"})

    return {"nodes": nodes, "edges": edges}
