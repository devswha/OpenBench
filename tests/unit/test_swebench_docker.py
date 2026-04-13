from __future__ import annotations

from openbench.suites.swebench.docker import image_name_for_instance


def test_image_name_for_instance():
    instance = {"instance_id": "django__django-16379"}
    name = image_name_for_instance(instance)
    assert name == "ghcr.io/epoch-research/swe-bench.eval.x86_64.django__django-16379:latest"


def test_image_name_for_instance_with_dots():
    instance = {"instance_id": "scikit-learn__scikit-learn-25570"}
    name = image_name_for_instance(instance)
    assert "scikit-learn__scikit-learn-25570" in name
