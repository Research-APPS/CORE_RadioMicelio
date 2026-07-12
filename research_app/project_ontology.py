from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.urls import reverse

from core_micelio.core_urls import module_url
from ontologizar_app.models import Concept
from ontologizar_app.services.concept_graph import concept_graph_jsonld
from research_app.models import ProyectoInvestigacion
from research_app.project_hub import ProjectDigitalProfile, _distinct_project_markers


def build_project_ontology_graph(project_uuid: UUID) -> dict | None:
    project = ProyectoInvestigacion.objects.filter(uuid=project_uuid, activo=True).first()
    if not project:
        return None

    base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_concepts: set[str] = set()
    seen_edges: set[str] = set()

    project_id = f"project:{project.uuid}"
    nodes.append({
        "id": project_id,
        "label": project.titulo,
        "kind": "project",
        "acron": project.acron,
    })

    for marker in _distinct_project_markers(project):
        cu = str(marker.concept_uuid)
        concept = Concept.objects.filter(uuid=marker.concept_uuid).select_related(
            "dictionary__subject",
        ).prefetch_related(
            "properties",
            "outgoing_relations__target__dictionary__subject",
            "incoming_relations__source__dictionary__subject",
        ).first()
        if not concept:
            continue

        cid = f"concept:{cu}"
        if cu not in seen_concepts:
            seen_concepts.add(cu)
            nodes.append({
                "id": cid,
                "label": concept.label,
                "kind": "class",
                "subject": concept.dictionary.subject.name,
                "subject_slug": concept.dictionary.subject.slug,
                "topic_url": f"{base}/biblioteca/temas/{cu}/",
            })
            for prop in concept.properties.all():
                pid = f"property:{cu}:{prop.key}"
                nodes.append({
                    "id": pid,
                    "label": f"{prop.key}: {prop.value}",
                    "kind": "property",
                    "property_key": prop.key,
                    "property_value": prop.value,
                    "parent_concept": cid,
                })
                edges.append({
                    "id": f"edge:{pid}",
                    "from": cid,
                    "to": pid,
                    "label": prop.key,
                    "kind": "property",
                })

            for rel in concept.outgoing_relations.all():
                tid = str(rel.target.uuid)
                target_cid = f"concept:{tid}"
                if tid not in seen_concepts:
                    seen_concepts.add(tid)
                    nodes.append({
                        "id": target_cid,
                        "label": rel.target.label,
                        "kind": "class",
                        "subject": rel.target.dictionary.subject.name,
                        "subject_slug": rel.target.dictionary.subject.slug,
                        "topic_url": f"{base}/biblioteca/temas/{tid}/",
                        "inferred": True,
                    })
                eid = f"rel:{cu}:{rel.relation_type}:{tid}"
                if eid not in seen_edges:
                    seen_edges.add(eid)
                    edges.append({
                        "id": eid,
                        "from": cid,
                        "to": target_cid,
                        "label": rel.relation_type,
                        "kind": "relation",
                    })

        edges.append({
            "id": f"cite:{project.uuid}:{cu}",
            "from": project_id,
            "to": cid,
            "label": marker.get_status_display(),
            "kind": "citation",
            "status": marker.status,
            "note": marker.note,
        })

    return {
        "project_uuid": str(project.uuid),
        "project_title": project.titulo,
        "project_acron": project.acron,
        "nodes": nodes,
        "edges": edges,
        "viz_url": f"{base}{reverse('research:proyecto_ontology', kwargs={'uuid': project.uuid})}",
    }


def build_digital_profile_jsonld(profile: ProjectDigitalProfile) -> dict:
    ns = getattr(settings, "CORE_JSONLD_NAMESPACE", "https://core.radiomicelio/ns/")
    base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    graph: list[dict] = [{
        "@id": f"project:{profile.project_uuid}",
        "@type": ["ResearchProject", "core:ResearchNotebook"],
        "name": profile.titulo,
        "alternateName": profile.acron or None,
        "core:curriculum": profile.curriculum,
        "core:metrics": profile.metrics,
        "url": module_url("research", f"proyectos/{profile.project_uuid}"),
        "core:ontologyView": f"{base}/research/proyectos/{profile.project_uuid}/ontologia/",
    }]

    project = ProyectoInvestigacion.objects.filter(uuid=profile.project_uuid).first()
    if project:
        for marker in _distinct_project_markers(project):
            concept = Concept.objects.filter(uuid=marker.concept_uuid).prefetch_related(
                "properties", "outgoing_relations__target", "incoming_relations__source",
            ).first()
            if not concept:
                continue
            subgraph = concept_graph_jsonld(concept, base_url=base)
            marker_node = {
                "@id": f"marker:{profile.project_uuid}:{marker.concept_uuid}",
                "@type": "core:LearningMarker",
                "name": marker.concept_label,
                "core:status": marker.status,
                "core:note": marker.note or "",
                "core:cites": {"@id": f"concept:{marker.concept_uuid}"},
            }
            graph.append(marker_node)
            for item in subgraph["@graph"]:
                if not any(n.get("@id") == item.get("@id") for n in graph):
                    graph.append(item)
            graph[0].setdefault("core:markers", []).append({"@id": marker_node["@id"]})

    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "core": ns,
            "core:ResearchNotebook": f"{ns}ResearchNotebook",
            "core:LearningMarker": f"{ns}LearningMarker",
            "core:OntologyClass": f"{ns}OntologyClass",
            "core:OntologyProperty": f"{ns}OntologyProperty",
            "core:RelationAssertion": f"{ns}RelationAssertion",
            "core:cites": f"{ns}cites",
            "core:markers": f"{ns}markers",
            "core:ontologyView": f"{ns}ontologyView",
            "core:curriculum": f"{ns}curriculum",
            "core:metrics": f"{ns}metrics",
            "core:status": f"{ns}status",
            "core:note": f"{ns}note",
            "core:relations": f"{ns}relations",
            "core:relationType": f"{ns}relationType",
        },
        "@graph": graph,
    }
