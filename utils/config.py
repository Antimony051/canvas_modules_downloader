import yaml


def load_credentials(path: str) -> dict:
    """Load credentials from YAML file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.full_load(f) or {}
    except FileNotFoundError:
        return {}