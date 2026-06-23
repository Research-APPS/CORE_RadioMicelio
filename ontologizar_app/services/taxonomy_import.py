from __future__ import annotations
import json
from typing import Any

from django.db import transaction

from ontologizar_app.models import Concept, Dictionary, Taxonomy, TaxonomyNode


def validar_estructura_json(data: dict, nivel: int = 0) -> tuple[bool, list[str]]:
    errores = []
    if nivel > 10:
        errores.append(f"Profundidad excesiva: {nivel}")
    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            errores.append(f"Nombre inválido: {key!r}")
            continue
        if value is not None and not isinstance(value, dict):
            errores.append(f"Valor inválido para {key!r}")
            continue
        if isinstance(value, dict):
            ok, sub = validar_estructura_json(value, nivel + 1)
            errores.extend(sub)
    return len(errores) == 0, errores


def _get_or_create_concept(dictionary: Dictionary, label: str) -> Concept:
    label = label.strip()
    concept, _ = Concept.objects.get_or_create(dictionary=dictionary, label=label)
    return concept


def _create_nodes(data: dict, taxonomy: Taxonomy, dictionary: Dictionary, parent=None) -> int:
    count = 0
    for key, value in data.items():
        concept = _get_or_create_concept(dictionary, key)
        node = TaxonomyNode.objects.create(
            taxonomy=taxonomy, label=key.strip(), concept=concept, parent=parent,
        )
        count += 1
        if isinstance(value, dict):
            count += _create_nodes(value, taxonomy, dictionary, parent=node)
    return count


@transaction.atomic
def import_taxonomy_from_json(
    taxonomy: Taxonomy,
    dictionary: Dictionary,
    data: dict,
    *,
    replace: bool = True,
) -> tuple[bool, str, int]:
    ok, errores = validar_estructura_json(data)
    if not ok:
        return False, "\n".join(errores), 0
    if replace:
        TaxonomyNode.objects.filter(taxonomy=taxonomy).delete()
    total = _create_nodes(data, taxonomy, dictionary)
    return True, "", total


def import_taxonomy_from_text(taxonomy, dictionary, text: str, **kwargs):
    from ontologizar_app.services.taxonomy_import import parse_indentation_to_json
    data = parse_indentation_to_json(text)
    if data is None:
        return False, "Texto vacío o inválido", 0
    return import_taxonomy_from_json(taxonomy, dictionary, data, **kwargs)


def parse_indentation_to_json(text: str) -> dict | None:
    """Parser de taxonomía por indentación (texto → árbol JSON)."""
    lines = []
    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        expanded = line.replace("\t", "    ")
        leading = len(expanded) - len(expanded.lstrip())
        lines.append((line.strip(), leading))
    if not lines:
        return None
    unit = next((l for _, l in lines if l > 0), 0) or 4
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    prev = 0
    for text_line, leading in lines:
        level = round(leading / unit) if unit else 0
        if level > prev + 1:
            level = prev + 1
        while len(stack) > 1 and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1]
        parent[text_line] = {}
        stack.append((level, parent[text_line]))
        prev = level

    def nullify(obj: dict) -> dict:
        for k, v in list(obj.items()):
            obj[k] = nullify(v) if v else None
        return obj
    return nullify(root)
