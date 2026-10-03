#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path.home() / "NovaBW" / "stardust-env"
ADAPTER = ROOT / "src/NovaBW/OpenBWAdapter.cpp"
TEST = ROOT / "test/NovaBW.cpp"

COMMIT = "HEAD"
BASE = "https://raw.githubusercontent.com/jinwuuju/NovaBW/main"

if not ROOT.exists():
    raise SystemExit(f"NovaBW root not found: {ROOT}")

def fetch(path):
    with urllib.request.urlopen(
        f"{BASE}/{path}",
        timeout=30,
    ) as response:
        return response.read().decode("utf-8")

def matching_brace(text, opening):
    depth = 0
    in_string = False
    escape = False

    for i in range(opening, len(text)):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i

    raise RuntimeError("matching brace not found")

def replace_function_body(text, signature, body):
    start = text.find(signature)
    if start < 0:
        raise RuntimeError(f"function signature not found: {signature}")

    opening = text.find("{", start)
    closing = matching_brace(text, opening)

    return (
        text[:opening + 1]
        + "\n"
        + body.rstrip()
        + "\n"
        + text[closing:]
    )

def replace_once(text, old, new, label):
    if old not in text:
        if new in text:
            print(f"[MIGRATE] already migrated: {label}")
            return text

        raise RuntimeError(
            f"expected source block missing: {label}"
        )

    return text.replace(old, new, 1)

backup_dir = Path(
    tempfile.mkdtemp(prefix="novabw_registry_backup_")
)

tracked = [
    ADAPTER,
    TEST,
    ROOT / "src/NovaBW/CapabilityRegistry.h",
    ROOT / "src/NovaBW/ScenarioHarness.h",
    ROOT / "scripts/novabw_test.py",
]

existing = {}

for path in tracked:
    if path.exists():
        target = backup_dir / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        existing[path] = True
    else:
        existing[path] = False

try:
    print("[MIGRATE] installing registry/harness/runner")

    (ROOT / "src/NovaBW/CapabilityRegistry.h").write_text(
        fetch("src/NovaBW/CapabilityRegistry.h")
    )

    (ROOT / "src/NovaBW/ScenarioHarness.h").write_text(
        fetch("src/NovaBW/ScenarioHarness.h")
    )

    runner = ROOT / "scripts/novabw_test.py"
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_text(fetch("scripts/novabw_test.py"))
    runner.chmod(0o755)

    s = ADAPTER.read_text()

    if '#include "CapabilityRegistry.h"' not in s:
        first_include = s.find("#include")
        if first_include < 0:
            raise RuntimeError("OpenBWAdapter.cpp has no include")

        line_end = s.find("\n", first_include)

        s = (
            s[:line_end + 1]
            + '#include "CapabilityRegistry.h"\n'
            + s[line_end + 1:]
        )

    if "static std::string canonicalUnitTypeKey" in s:
        s = replace_function_body(
            s,
            "static std::string canonicalUnitTypeKey",
            """    return capabilityUnitTypeKey(type);""",
        )

    observe_return = """    return observation;
}

bool OpenBWAdapter::execute"""

    registry_return = """    appendRegisteredCandidates(
        observation
    );

    return observation;
}

bool OpenBWAdapter::execute"""

    s = replace_once(
        s,
        observe_return,
        registry_return,
        "append registry candidates",
    )

    old = """            if (requestedType !=
                    BWAPI::UnitTypes::Zerg_Drone &&
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Overlord &&
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Zergling &&
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Hydralisk &&
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Lair)
            {
                return false;
            }
"""

    new = """            if (!isRegisteredMorph(
                    requestedType
                ))
            {
                return false;
            }
"""

    s = replace_once(
        s,
        old,
        new,
        "Morph registry allowlist",
    )

    old = """            if (
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Spawning_Pool &&
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Extractor &&
                requestedType !=
                    BWAPI::UnitTypes::Zerg_Hydralisk_Den
            )
            {
                return false;
            }
"""

    new = """            if (!isRegisteredBuild(
                    requestedType
                ))
            {
                return false;
            }
"""

    s = replace_once(
        s,
        old,
        new,
        "Build registry allowlist",
    )

    old = """            if (
                tech !=
                    BWAPI::TechTypes::Burrowing
            )
            {
                return false;
            }
"""

    new = """            if (!isRegisteredResearch(
                    tech
                ))
            {
                return false;
            }
"""

    s = replace_once(
        s,
        old,
        new,
        "Research registry allowlist",
    )

    old = """            if (
                upgrade !=
                    BWAPI::UpgradeTypes::Muscular_Augments &&
                upgrade !=
                    BWAPI::UpgradeTypes::Grooved_Spines
            )
            {
                return false;
            }
"""

    new = """            if (!isRegisteredUpgrade(
                    upgrade
                ))
            {
                return false;
            }
"""

    s = replace_once(
        s,
        old,
        new,
        "Upgrade registry allowlist",
    )

    ADAPTER.write_text(s)

    test_text = TEST.read_text()

    if '#include "NovaBW/ScenarioHarness.h"' not in test_text:
        first_include = test_text.find("#include")
        if first_include < 0:
            raise RuntimeError("NovaBW.cpp has no include")

        line_end = test_text.find("\n", first_include)

        test_text = (
            test_text[:line_end + 1]
            + '#include "NovaBW/ScenarioHarness.h"\n'
            + test_text[line_end + 1:]
        )

        TEST.write_text(test_text)

    print("[MIGRATE] building")
    jobs = str(os.cpu_count() or 8)

    subprocess.run(
        ["cmake", "--build", "build", "-j" + jobs],
        cwd=ROOT,
        check=True,
    )

    print("[MIGRATE] running core regression")
    subprocess.run(
        [
            sys.executable,
            "scripts/novabw_test.py",
            "core",
            "--no-build",
        ],
        cwd=ROOT,
        check=True,
    )

except Exception:
    print(
        "[MIGRATE] FAILED - restoring previous source",
        file=sys.stderr,
    )

    for path in tracked:
        backup = backup_dir / path.relative_to(ROOT)

        if existing[path]:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, path)
        elif path.exists():
            path.unlink()

    raise

finally:
    shutil.rmtree(backup_dir, ignore_errors=True)

print()
print("===============================================")
print(" NOVABW CAPABILITY REGISTRY MIGRATION: PASSED")
print("===============================================")
print("Future capability additions should start in:")
print("  src/NovaBW/CapabilityRegistry.h")
print("Regression:")
print("  python scripts/novabw_test.py core")
