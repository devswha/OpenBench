from helpers.math_ops import safe_add


def render_total(a: int, b: int) -> str:
    return f"total={safe_add(a, b)}"
