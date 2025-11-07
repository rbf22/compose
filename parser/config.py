# compose/parser/config.py
def parse_config(path: str) -> dict:
    cfg = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, val = map(str.strip, line.split(':', 1))
                cfg[key] = val.strip('"\'')
    return cfg
