#!/usr/bin/env python3
import datetime
import json
import sys

import yaml


def _json_default(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <insomnia-doc.yaml> <output.json>", file=sys.stderr)
    sys.exit(1)

src_path, out_path = sys.argv[1], sys.argv[2]

with open(src_path) as f:
    doc = yaml.safe_load(f)

try:
    openapi = doc["spec"]["contents"]
except (KeyError, TypeError):
    print(f"No spec.contents OpenAPI document found in {src_path}", file=sys.stderr)
    sys.exit(1)

with open(out_path, "w") as f:
    json.dump(openapi, f, default=_json_default)

print(f"Extracted {openapi.get('info', {}).get('title', '(untitled)')} "
      f"v{openapi.get('info', {}).get('version', '?')} -> {out_path}")
