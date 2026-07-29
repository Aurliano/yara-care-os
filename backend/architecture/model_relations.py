"""Inspect Django model relations for architecture compliance checks."""

from __future__ import annotations

from dataclasses import dataclass

from django.apps import apps
from django.db.models import ForeignKey, OneToOneField


@dataclass(frozen=True, slots=True)
class ModelRelation:
    """A directed foreign-key relation between two Django models."""

    from_app: str
    from_model: str
    field_name: str
    to_app: str
    to_model: str


def collect_foreign_key_relations(
    *,
    app_labels: set[str] | None = None,
) -> list[ModelRelation]:
    """Return all FK/OneToOne relations, optionally filtered by source app."""
    relations: list[ModelRelation] = []

    for model in apps.get_models():
        source_app = model._meta.app_label
        if app_labels is not None and source_app not in app_labels:
            continue

        for field in model._meta.get_fields():
            if not isinstance(field, (ForeignKey, OneToOneField)):
                continue

            target_model = field.remote_field.model
            relations.append(
                ModelRelation(
                    from_app=source_app,
                    from_model=model.__name__,
                    field_name=field.name,
                    to_app=target_model._meta.app_label,
                    to_model=target_model.__name__,
                )
            )

    return sorted(
        relations,
        key=lambda relation: (
            relation.from_app,
            relation.from_model,
            relation.field_name,
        ),
    )


def find_cross_domain_relations(
    *,
    domain_apps: set[str],
    allowed_cross_domain_fks: set[tuple[str, str, str, str]] | None = None,
) -> list[ModelRelation]:
    """Return cross-domain FK relations that are not explicitly allowed.

    Each allowed entry is (from_app, from_model, field_name, to_app).
    """
    allowed = allowed_cross_domain_fks or set()
    violations: list[ModelRelation] = []

    for relation in collect_foreign_key_relations(app_labels=domain_apps):
        if relation.to_app not in domain_apps:
            continue
        if relation.from_app == relation.to_app:
            continue

        key = (
            relation.from_app,
            relation.from_model,
            relation.field_name,
            relation.to_app,
        )
        if key not in allowed:
            violations.append(relation)

    return violations
