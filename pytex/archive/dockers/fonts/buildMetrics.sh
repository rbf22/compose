#!/bin/sh
# Generates fontMetricsData.js without requiring Perl
PYTHON="python3"

cd "$(dirname "$0")/../../src/metrics"
$PYTHON ./mapping.py | $PYTHON ./extract_tfms.py | $PYTHON ./extract_ttfs.py | $PYTHON ./format_json.py --width > ../fontMetricsData.js
