"""Deterministic harness test double; never use its output as benchmark evidence."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path


def replace(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if old not in source:
        raise RuntimeError(f"expected smoke-test fixture text missing from {path}")
    path.write_text(source.replace(old, new), encoding="utf-8")


workspace = Path(os.environ["ARI_WORKSPACE"])
issue = (workspace / "ISSUE.md").read_text(encoding="utf-8")
events = []

if os.environ.get("ARI_EXECUTION_MODE") == "docker":
    forbidden = [
        workspace / "evaluator",
        workspace / "oracle.toml",
        workspace / "benchmark_hidden_tests",
        Path("/benchmark"),
        Path("/host"),
    ]
    if any(path.exists() for path in forbidden):
        raise RuntimeError("agent sandbox exposed evaluator or host benchmark material")
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=0.25).close()
    except OSError:
        pass
    else:
        raise RuntimeError("agent sandbox unexpectedly has network access")
    events.append(
        {
            "type": "isolation",
            "message": "Confirmed hidden evaluator paths and network are unavailable.",
        }
    )

if "Profile response field changed" in issue:
    target = workspace / "api" / "serializers.py"
    replace(
        target,
        '    name = serializers.CharField(source="display_name")\n',
        "    display_name = serializers.CharField()\n",
    )
    events.append({"type": "edit", "message": "Restored the established serializer field name.", "path": "api/serializers.py"})
elif "active=false" in issue:
    target = workspace / "api" / "views.py"
    replace(
        target,
        """        if raw_active is not None:\n            active = bool(raw_active)\n            integrations = [item for item in integrations if item[\"active\"] is active]\n""",
        """        if raw_active is not None:\n            normalized = raw_active.lower()\n            if normalized not in {\"true\", \"false\"}:\n                raise ValidationError({\"active\": \"Use 'true' or 'false'.\"})\n            active = normalized == \"true\"\n            integrations = [item for item in integrations if item[\"active\"] is active]\n""",
    )
    events.append({"type": "edit", "message": "Parsed documented boolean values explicitly.", "path": "api/views.py"})
elif "orphan orders" in issue:
    target = workspace / "api" / "serializers.py"
    replace(
        target,
        "from rest_framework import serializers\n",
        "from django.db import transaction\n\nfrom rest_framework import serializers\n",
    )
    replace(
        target,
        """        order = Order.objects.create(**validated_data)\n        for item in items:\n            if item[\"quantity\"] <= 0:\n                raise serializers.ValidationError(\n                    {\"items\": [\"Quantity must be greater than zero.\"]}\n                )\n            OrderItem.objects.create(order=order, **item)\n        return order\n""",
        """        with transaction.atomic():\n            order = Order.objects.create(**validated_data)\n            for item in items:\n                if item[\"quantity\"] <= 0:\n                    raise serializers.ValidationError(\n                        {\"items\": [\"Quantity must be greater than zero.\"]}\n                    )\n                OrderItem.objects.create(order=order, **item)\n            return order\n""",
    )
    events.append({"type": "edit", "message": "Made the nested database write atomic.", "path": "api/serializers.py"})
else:
    raise RuntimeError("unknown smoke-test case")

trajectory_path = Path(os.environ["ARI_TRAJECTORY_PATH"])
trajectory_path.write_text(
    "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
    encoding="utf-8",
)
print("Smoke-test agent applied its deterministic fixture patch.")
