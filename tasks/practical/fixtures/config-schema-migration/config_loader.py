def load_timeout(config: dict) -> int:
    return config["timeout_ms"] // 1000
