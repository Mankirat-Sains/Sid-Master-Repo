#!/bin/bash
# Safe wrapper for parse_workbook.py that always uses -B flag
# This prevents Python 3.13 bytecode hang issues

cd "$(dirname "$0")"
python -B parse_workbook.py "$@"

