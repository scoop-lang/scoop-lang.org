#!/bin/sh
# Publish an explicit component manifest; run with --help for options.
set -eu
exec python3 "$(dirname "$0")/publish_release_index.py" "$@"
