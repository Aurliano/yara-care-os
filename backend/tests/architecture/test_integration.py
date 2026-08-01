"""Architecture tests for integration layer boundaries."""

import importlib
import pkgutil

import pytest


@pytest.mark.parametrize(
    "forbidden_suffix",
    [
        "domains.care.models",
        "domains.workflow.models",
        "domains.device.models",
        "domains.communication.models",
        "domains.synchronization.models",
        "domains.scheduling.models",
        "domains.event.models",
    ],
)
def test_integration_does_not_import_domain_models(forbidden_suffix: str):
    package = importlib.import_module("integration")
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "migrations" in module_name or "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert forbidden_suffix not in content, f"{module_name} imports {forbidden_suffix}"
