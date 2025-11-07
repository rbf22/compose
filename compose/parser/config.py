# compose/parser/config.py
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback (but we want to avoid this)

def parse_config(path: str) -> dict:
    with open(path, 'rb') as f:
        config = tomllib.load(f)

    # Set defaults for missing configuration options
    defaults = {
        'mode': 'document',
        'output': 'text',
        'typography': {
            'line_length': 80,
            'font_family': 'serif',
            'font_size': 12,
            'line_height': 1.5,
            'paragraph_spacing': 1.0,
            'heading_scale': [2.0, 1.8, 1.6, 1.4, 1.2, 1.1],  # h1 to h6 scaling
        },
        'colors': {
            'text': '#333333',
            'headings': '#222222',
            'links': '#0066cc',
            'code_background': '#f4f4f4',
            'blockquote_border': '#dddddd',
        },
        'margins': {
            'top': 20,
            'bottom': 20,
            'left': 20,
            'right': 20,
        },
        'features': {
            'syntax_highlighting': True,
            'smart_quotes': True,
            'smart_dashes': True,
            'math_rendering': True,
        }
    }

    # Deep merge defaults with user config
    return _deep_merge(defaults, config)

def _deep_merge(defaults: dict, user_config: dict) -> dict:
    """Deep merge user config into defaults"""
    result = defaults.copy()

    for key, value in user_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result
