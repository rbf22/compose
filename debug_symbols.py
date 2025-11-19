import sys
sys.path.insert(0, 'src')

from pytex.build_common import SYMBOLS, get_character_metrics, lookup_symbol
from pytex.font_metrics import load_metrics
from pytex.font_metrics_data import FONT_METRICS_DATA

# Initialize metrics
load_metrics(FONT_METRICS_DATA)

print(f"SYMBOLS keys: {list(SYMBOLS.keys())}")
if 'math' in SYMBOLS:
    print(f"SYMBOLS['math'] has \\infty: {'\\infty' in SYMBOLS['math']}")
    if '\\infty' in SYMBOLS['math']:
        print(f"SYMBOLS['math']['\\infty']: {SYMBOLS['math']['\\infty']}")

print("-" * 20)
print("Lookup '\\infty':")
res = lookup_symbol('\\infty', 'Math-Italic', 'math')
print(res)

print("-" * 20)
print("Lookup '\\infty ' (with space):")
res_space = lookup_symbol('\\infty ', 'Math-Italic', 'math')
print(res_space)
