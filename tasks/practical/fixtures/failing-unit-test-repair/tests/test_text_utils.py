from text_utils import slugify


def test_slugify_spaces_become_hyphens() -> None:
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_outer_whitespace() -> None:
    assert slugify("  Open Bench  ") == "open-bench"
