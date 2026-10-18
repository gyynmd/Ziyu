#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def slot(
    name: str,
    families: list[str],
    *,
    han: bool = False,
    latin: bool = False,
    digits: bool = False,
    replaceable: bool | None = None,
    runtime: bool = False,
    xml_lang: str = "",
) -> dict:
    coverage = {
        "hasHan": han,
        "hanCount": 64 if han else 0,
        "hasLatin": latin,
        "latinCount": 52 if latin else 0,
        "hasDigits": digits,
        "digitCount": 10 if digits else 0,
    }
    value = {
        "slotName": name,
        "families": families,
        "partition": "system",
        "source": "xml" if families else "verified-scan",
        "sourceXmls": ["/system/etc/fonts.xml"] if families else [],
        "metrics": {"coverage": coverage},
        "runtimeEvidence": {"fontManager": runtime, "mount": False},
    }
    if xml_lang:
        value["xmlRefs"] = [{
            "sourceXml": "/system/etc/fonts.xml",
            "family": families[0] if families else "",
            "familyAttributes": {"lang": xml_lang},
            "resolvedPath": "/system/fonts/" + name,
        }]
    if replaceable is not None:
        value["legacyReplaceable"] = replaceable
    return value


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    script = root / "common/font_role_shadow.py"

    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        topology = temp / "device_font_topology.json"
        roles = temp / "device_font_roles.json"
        plan = temp / "device_font_shadow_plan.json"

        slots = {
            "/system/fonts/Roboto-Regular.ttf": slot(
                "Roboto-Regular.ttf", ["sans-serif"], latin=True, digits=True,
                replaceable=True, runtime=True,
            ),
            "/product/fonts/CjkFallback.otf": slot(
                "CjkFallback.otf", ["fallback"], han=True, latin=True, digits=True,
                replaceable=False, xml_lang="zh-Hans",
            ),
            "/product/fonts/LatinFallback.ttf": slot(
                "LatinFallback.ttf", ["fallback"], latin=True, digits=True,
                replaceable=False, xml_lang="en",
            ),
            "/system_ext/fonts/OemNumeric.ttf": slot(
                "OemNumeric.ttf", [], digits=True, replaceable=False,
            ),
            "/system/fonts/AndroidClock.ttf": slot(
                "AndroidClock.ttf", ["clock-ui"], latin=True, digits=True,
                replaceable=True,
            ),
            # Explicit monospace family must beat the Mitype filename clock hint.
            "/system/fonts/MitypeMono.ttf": slot(
                "MitypeMono.ttf", ["monospace"], latin=True, digits=True,
                replaceable=True,
            ),
            "/system/fonts/RobotoMono-Regular.ttf": slot(
                "RobotoMono-Regular.ttf", [], latin=True, digits=True,
                replaceable=False,
            ),
            "/system/fonts/NotoSerif-Regular.ttf": slot(
                "NotoSerif-Regular.ttf", ["serif"], latin=True, digits=True,
                replaceable=False,
            ),
            "/system/fonts/NotoColorEmoji.ttf": slot(
                "NotoColorEmoji.ttf", ["emoji"], replaceable=True,
            ),
            "/system/fonts/MaterialSymbols.ttf": slot(
                "MaterialSymbols.ttf", ["material-symbols"], replaceable=True,
            ),
            "/system/fonts/MysteryFallback.otf": slot(
                "MysteryFallback.otf", ["fallback"], latin=True, digits=True,
                replaceable=False, xml_lang="ja",
            ),
            "/vendor/fonts/MysteryBroad.ttf": slot(
                "MysteryBroad.ttf", [], han=True, latin=True, digits=True,
                replaceable=True,
            ),
        }

        topology.write_text(
            json.dumps(
                {
                    "schema": "device-font-topology-v1",
                    "topologyRevision": 2,
                    "state": "ready",
                    "buildKey": "role-shadow-test",
                    "romKind": "generic",
                    "slots": slots,
                    "families": {},
                    "summary": {"slotCount": len(slots)},
                    "runtime": {},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        built = run(
            [
                sys.executable,
                str(script),
                "--topology", str(topology),
                "--roles-output", str(roles),
                "--plan-output", str(plan),
            ]
        )
        assert built.returncode == 0, built.stderr or built.stdout
        result = json.loads(built.stdout)
        role_map = json.loads(roles.read_text(encoding="utf-8"))
        shadow = json.loads(plan.read_text(encoding="utf-8"))

        assert result["status"] == "ok"
        assert role_map["schema"] == "device-font-roles-v1"
        assert shadow["schema"] == "device-font-shadow-plan-v1"
        assert shadow["state"] == "shadow"
        assert shadow["mutatesSystem"] is False

        def role(path: str) -> str:
            return role_map["slots"][path]["role"]

        def action(path: str) -> str:
            return shadow["slots"][path]["action"]

        assert role("/system/fonts/Roboto-Regular.ttf") == "ui-sans"
        assert action("/system/fonts/Roboto-Regular.ttf") == "replace"

        assert role("/product/fonts/CjkFallback.otf") == "cjk"
        assert action("/product/fonts/CjkFallback.otf") == "conditional"
        assert role_map["slots"]["/product/fonts/CjkFallback.otf"]["evidence"]["xmlSemantics"]["lang"] == ["zh-Hans"]
        assert shadow["slots"]["/product/fonts/CjkFallback.otf"]["comparison"] == "current-gap"

        assert role("/product/fonts/LatinFallback.ttf") == "latin"
        assert action("/product/fonts/LatinFallback.ttf") == "conditional"

        assert role("/system_ext/fonts/OemNumeric.ttf") == "numeric"
        assert action("/system_ext/fonts/OemNumeric.ttf") == "specialized"

        assert role("/system/fonts/AndroidClock.ttf") == "clock"
        assert action("/system/fonts/AndroidClock.ttf") == "specialized"

        assert role("/system/fonts/MitypeMono.ttf") == "monospace"
        assert action("/system/fonts/MitypeMono.ttf") == "preserve"
        assert shadow["slots"]["/system/fonts/MitypeMono.ttf"]["comparison"] == "current-overreach"

        assert role("/system/fonts/RobotoMono-Regular.ttf") == "monospace"
        assert action("/system/fonts/RobotoMono-Regular.ttf") == "preserve"
        assert "monospace-file-identity" in role_map["slots"]["/system/fonts/RobotoMono-Regular.ttf"]["reasons"]

        assert role("/system/fonts/NotoSerif-Regular.ttf") == "serif"
        assert action("/system/fonts/NotoSerif-Regular.ttf") == "preserve"

        assert role("/system/fonts/NotoColorEmoji.ttf") == "emoji"
        assert action("/system/fonts/NotoColorEmoji.ttf") == "preserve"
        assert shadow["slots"]["/system/fonts/NotoColorEmoji.ttf"]["comparison"] == "current-overreach"

        assert role("/system/fonts/MaterialSymbols.ttf") == "symbol-icon"
        assert action("/system/fonts/MaterialSymbols.ttf") == "preserve"

        assert role("/system/fonts/MysteryFallback.otf") == "special-fallback"
        assert action("/system/fonts/MysteryFallback.otf") == "preserve"
        assert "xml-language-special-fallback" in role_map["slots"]["/system/fonts/MysteryFallback.otf"]["reasons"]

        assert role("/vendor/fonts/MysteryBroad.ttf") == "unknown-protected"
        assert action("/vendor/fonts/MysteryBroad.ttf") == "review"

        # Phase 2 safety invariants.
        for item in shadow["slots"].values():
            if item["role"] in {"emoji", "symbol-icon", "serif", "monospace", "special-fallback"}:
                assert item["action"] == "preserve"
            if item["role"] in {"clock", "numeric"}:
                assert item["action"] == "specialized"
            if item["role"] == "unknown-protected":
                assert item["action"] == "review"

        assert shadow["summary"]["actionCounts"]["preserve"] == 6
        assert shadow["summary"]["actionCounts"]["specialized"] == 2
        assert shadow["summary"]["actionCounts"]["conditional"] == 2
        assert shadow["summary"]["actionCounts"]["replace"] == 1
        assert shadow["summary"]["actionCounts"]["review"] == 1

        validated = run(
            [
                sys.executable,
                str(script),
                "--validate",
                "--topology", str(topology),
                "--roles-output", str(roles),
                "--plan-output", str(plan),
            ]
        )
        assert validated.returncode == 0, validated.stderr or validated.stdout

        # ColorOS physical discovery can retain a broken pathname with no stock
        # bytes or metrics. Preserve that case, while a scanner-validated stock
        # contract on the same source class remains eligible for replacement.
        coloros_topology = temp / "coloros_topology.json"
        coloros_roles = temp / "coloros_roles.json"
        coloros_plan = temp / "coloros_plan.json"
        coloros_groups = temp / "coloros_slot_groups.conf"
        trusted_metrics = {
            "upem": 1000,
            "hhea": {"ascent": 800, "descent": -200},
            "coverage": {
                "hasHan": True, "hanCount": 40,
                "hasLatin": True, "latinCount": 26,
                "hasDigits": True, "digitCount": 10,
            },
        }
        verified_physical = {
            **slot("SysFont-Regular.ttf", ["sans-serif"], han=True, latin=True, digits=True),
            "source": "physical-scan",
            "format": "TTF",
            "validatedFormat": "TTF",
            "validatedBy": "fontTools-stock-metrics",
            "metrics": trusted_metrics,
        }
        dangling_physical = {
            "slotName": "SysSans-Hans-Regular.ttf",
            "families": ["sans-serif"],
            "partition": "system",
            "source": "physical-scan",
            "physicalCandidate": True,
            "physicalReason": "dangling-symlink",
        }
        digit_physical = {
            **slot("OSans-Solid-Digits.ttf", [], digits=True),
            "source": "physical-scan",
            "format": "TTF",
            "validatedFormat": "TTF",
            "validatedBy": "fontTools-stock-metrics",
            "metrics": trusted_metrics,
        }
        coloros_topology.write_text(
            json.dumps({
                "schema": "device-font-topology-v1",
                "topologyRevision": 2,
                "state": "ready",
                "buildKey": "coloros-role-shadow-test",
                "romKind": "coloros",
                "slots": {
                    "/system/fonts/SysFont-Regular.ttf": verified_physical,
                    "/system/fonts/SysSans-Hans-Regular.ttf": dangling_physical,
                    "/system/fonts/OSans-Solid-Digits.ttf": digit_physical,
                },
                "families": {},
                "summary": {"slotCount": 3},
                "runtime": {},
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        coloros_groups.write_text("osans_digits = 0 # disabled\r\n", encoding="utf-8")
        coloros_build = run([
            sys.executable, str(script),
            "--topology", str(coloros_topology),
            "--roles-output", str(coloros_roles),
            "--plan-output", str(coloros_plan),
            "--slot-groups", str(coloros_groups),
        ])
        assert coloros_build.returncode == 0, coloros_build.stderr or coloros_build.stdout
        coloros_role_map = json.loads(coloros_roles.read_text(encoding="utf-8"))
        coloros_shadow = json.loads(coloros_plan.read_text(encoding="utf-8"))
        verified_path = "/system/fonts/SysFont-Regular.ttf"
        dangling_path = "/system/fonts/SysSans-Hans-Regular.ttf"
        digit_path = "/system/fonts/OSans-Solid-Digits.ttf"
        assert coloros_shadow["slots"][verified_path]["action"] == "replace"
        assert coloros_role_map["slots"][verified_path]["evidence"]["stockMetadataVerified"] is True
        assert coloros_shadow["slots"][dangling_path]["action"] == "preserve"
        assert "coloros-physical-slot-stock-content-unverified" in coloros_shadow["slots"][dangling_path]["reasons"]
        assert coloros_role_map["slots"][digit_path]["role"] == "numeric"
        assert coloros_shadow["slots"][digit_path]["action"] == "preserve"
        assert "osans_digits" not in coloros_role_map["colorosPolicy"]["enabledGroups"]

        coloros_groups.write_text("osans_digits = 1 # enabled\r\n", encoding="utf-8")
        enabled_build = run([
            sys.executable, str(script),
            "--topology", str(coloros_topology),
            "--roles-output", str(coloros_roles),
            "--plan-output", str(coloros_plan),
            "--slot-groups", str(coloros_groups),
        ])
        assert enabled_build.returncode == 0, enabled_build.stderr or enabled_build.stdout
        enabled_shadow = json.loads(coloros_plan.read_text(encoding="utf-8"))
        assert enabled_shadow["slots"][digit_path]["action"] == "specialized"

    print("font_role_shadow_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
