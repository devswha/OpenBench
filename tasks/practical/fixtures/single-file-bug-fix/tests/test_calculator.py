from calculator import add_numbers


def test_add_numbers() -> None:
    assert add_numbers(2, 3) == 5


def test_add_numbers_with_negatives() -> None:
    assert add_numbers(-2, 1) == -1
