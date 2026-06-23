from __future__ import annotations

from ontologizar_app.models import Concept, ConceptDefinition, Subject, SubjectMaterial


def get_concept_wiki_body(concept: Concept) -> str:
    definition = concept.definitions.filter(is_active=True, kind="definition").first()
    return definition.text if definition else ""


def save_concept_wiki_body(concept: Concept, text: str) -> None:
    text = text.strip()
    definition = concept.definitions.filter(is_active=True, kind="definition").first()
    if definition:
        definition.text = text
        definition.save(update_fields=["text"])
    elif text:
        ConceptDefinition.objects.create(
            concept=concept, text=text, kind="definition", is_active=True,
        )


def save_subject_description(subject: Subject, description: str) -> None:
    subject.description = description.strip()
    subject.save(update_fields=["description"])


def save_subject_material(material: SubjectMaterial, *, title: str, summary: str, body: str) -> None:
    material.title = title.strip()
    material.summary = summary.strip()
    material.body = body.strip()
    material.save(update_fields=["title", "summary", "body"])
