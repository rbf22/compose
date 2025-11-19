import sys
sys.path.insert(0, 'src')

from pytex.font_metrics_data import FONT_METRICS_DATA

print("Available fonts:")
for font in FONT_METRICS_DATA.keys():
    print(font)
