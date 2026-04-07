from config_loader import load_timeout


def test_new_schema_timeout_seconds_is_supported() -> None:
    assert load_timeout({"timeout_seconds": 9}) == 9


def test_old_schema_timeout_ms_still_works() -> None:
    assert load_timeout({"timeout_ms": 3000}) == 3
