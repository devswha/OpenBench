def create_user(email: str, name: str) -> dict:
    return {"email": email, "name": name.strip()}
