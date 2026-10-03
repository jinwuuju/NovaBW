#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path.home() / "NovaBW" / "stardust-env"

REGISTRY = ROOT / "src/NovaBW/CapabilityRegistry.h"
RUNNER = ROOT / "scripts/novabw_test.py"
SERVER = ROOT / "python/spire_air_test_server.py"
HEADER = ROOT / "test/NovaBWSpireAir.h"
TEST_MAIN = ROOT / "test/NovaBW.cpp"

REGISTRY_V1_URL = (
    "https://raw.githubusercontent.com/"
    "jinwuuju/NovaBW/"
    "cd1bfe85b1c9cedd1cd26fb4136f747cc64fc44f/"
    "src/NovaBW/CapabilityRegistry.h"
)

RUNNER_V1_URL = (
    "https://raw.githubusercontent.com/"
    "jinwuuju/NovaBW/"
    "11ca5f4de4134c153f7d95c084feef72ed660c95/"
    "scripts/novabw_test.py"
)

BASE = (
    "https://raw.githubusercontent.com/"
    "jinwuuju/NovaBW/main/"
)

if not ROOT.exists():
    raise SystemExit(
        f"NovaBW root not found: {ROOT}"
    )


def fetch(url):
    with urllib.request.urlopen(
        url,
        timeout=30,
    ) as response:
        return response.read().decode("utf-8")


def run(cmd, cwd=ROOT, env=None):
    print(
        "\n+ " + " ".join(str(part) for part in cmd),
        flush=True,
    )

    subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=True,
    )


print("[SPIRE] preflight", flush=True)

registry_v1 = fetch(REGISTRY_V1_URL)
registry_v2 = fetch(
    BASE + "src/NovaBW/CapabilityRegistry.h"
)

runner_v1 = fetch(RUNNER_V1_URL)
runner_v2 = fetch(
    BASE + "scripts/novabw_test.py"
)

server_v1 = fetch(
    BASE + "python/spire_air_test_server.py"
)

header_v1 = fetch(
    BASE + "test/NovaBWSpireAir.h"
)

local_registry = REGISTRY.read_text()
local_runner = RUNNER.read_text()

if local_registry not in (
    registry_v1,
    registry_v2,
):
    raise SystemExit(
        "CapabilityRegistry.h differs from the known "
        "NovaBW v1/v2 registry. No files changed."
    )

if local_runner not in (
    runner_v1,
    runner_v2,
):
    raise SystemExit(
        "scripts/novabw_test.py differs from the known "
        "NovaBW v1/v2 runner. No files changed."
    )

test_text = TEST_MAIN.read_text()

if '#include "NovaBWSpireAir.h"' not in test_text:
    test_text_v2 = (
        test_text.rstrip()
        + '\n\n#include "NovaBWSpireAir.h"\n'
    )
else:
    test_text_v2 = test_text


backup_dir = Path(
    tempfile.mkdtemp(
        prefix="novabw_spire_air_backup_"
    )
)

tracked = [
    REGISTRY,
    RUNNER,
    SERVER,
    HEADER,
    TEST_MAIN,
]

existed = {}

for path in tracked:
    existed[path] = path.exists()

    if path.exists():
        backup = (
            backup_dir
            / path.relative_to(ROOT)
        )

        backup.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            path,
            backup,
        )


def restore():
    print(
        "[SPIRE] restoring previous local source",
        file=sys.stderr,
        flush=True,
    )

    for path in tracked:
        backup = (
            backup_dir
            / path.relative_to(ROOT)
        )

        if existed[path]:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                backup,
                path,
            )

        elif path.exists():
            path.unlink()


try:
    print(
        "[SPIRE] installing declarative capabilities",
        flush=True,
    )

    REGISTRY.write_text(registry_v2)
    RUNNER.write_text(runner_v2)
    RUNNER.chmod(0o755)

    SERVER.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    HEADER.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SERVER.write_text(server_v1)
    HEADER.write_text(header_v1)
    TEST_MAIN.write_text(test_text_v2)

    run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(SERVER),
            str(RUNNER),
        ],
        env=os.environ.copy(),
    )

    jobs = str(
        os.cpu_count() or 8
    )

    run(
        [
            "cmake",
            "--build",
            "build",
            "-j" + jobs,
        ],
        env=os.environ.copy(),
    )

    test_env = os.environ.copy()
    test_env["OPENBW_GAME_SPEED"] = "0"
    test_env["OPENBW_ENABLE_UI"] = "0"

    print(
        "\n[SPIRE] compatibility smoke: "
        "existing Hydra adapter path",
        flush=True,
    )

    run(
        [
            "./tests",
            "--gtest_filter="
            "NovaBW.ZergHydraResearchThroughAdapter",
        ],
        cwd=ROOT / "build/test",
        env=test_env,
    )

    print(
        "\n[SPIRE] new Direct/Adapter/Python bundle",
        flush=True,
    )

    run(
        [
            sys.executable,
            "scripts/novabw_test.py",
            "spire-air",
            "--no-build",
        ],
        env=os.environ.copy(),
    )

except Exception:
    restore()
    raise

finally:
    shutil.rmtree(
        backup_dir,
        ignore_errors=True,
    )


print()
print("==========================================")
print(" NOVA-Z SPIRE AIR v1: ALL TESTS PASSED")
print("==========================================")
print("Registered:")
print("  Build   zerg_spire")
print("  Morph   zerg_mutalisk")
print("  Morph   zerg_scourge")
print("  Upgrade zerg_flyer_attacks")
print()
print("Full core regression:")
print("  python scripts/novabw_test.py core")
