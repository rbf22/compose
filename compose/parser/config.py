# compose/parser/config.py
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback (but we want to avoid this)

def parse_config(path: str) -> dict:
    with open(path, 'rb') as f:
        return tomllib.load(f)
