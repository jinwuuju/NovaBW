#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path.home() / "NovaBW" / "stardust-env"

REGISTRY = ROOT / "src/NovaBW/CapabilityRegistry.h"
RUNNER = ROOT / "scripts/novabw_test.py"
SERVER = ROOT / "python/lurker_test_server.py"
HEADER = ROOT / "test/NovaBWLurker.h"
TEST_MAIN = ROOT / "test/NovaBW.cpp"
TEST_BIN = ROOT / "build/test/tests"

URLS = {
    "registry_v2": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "ff894c3cbfe8b8c27922d40b979b3c9b56b4adfe/"
        "src/NovaBW/CapabilityRegistry.h"
    ),
    "registry_v3": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "d07d9ec4aed06cf586dc0cdfd273ca304ed04105/"
        "src/NovaBW/CapabilityRegistry.h"
    ),
    "runner_v2": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "2045d5b4f6583acb8d3b4f77899387a43e50fa57/"
        "scripts/novabw_test.py"
    ),
    "runner_v3": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "17732719c101ebcf3adfcb5469c5e93e9886f4eb/"
        "scripts/novabw_test.py"
    ),
    "server_v1": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "a4b3a609d58b23694ad82dd4ec4ea46c9024fc99/"
        "python/lurker_test_server.py"
    ),
    "header_v1": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "95226c8c2aa39308c89092c1c8ad1cbcfba2942a/"
        "test/NovaBWLurker.h"
    ),
}

if not ROOT.exists():
    raise SystemExit(f"NovaBW root not found: {ROOT}")


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def run(cmd, cwd=ROOT, env=None, capture=False):
    print("\n+ " + " ".join(str(x) for x in cmd), flush=True)

    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=capture,
        text=True,
    )


print("[LURKER] preflight", flush=True)

registry_v2 = fetch(URLS["registry_v2"])
registry_v3 = fetch(URLS["registry_v3"])
runner_v2 = fetch(URLS["runner_v2"])
runner_v3 = fetch(URLS["runner_v3"])
server_v1 = fetch(URLS["server_v1"])
header_v1 = fetch(URLS["header_v1"])

if "leaveGame()" in header_v1:
    raise SystemExit(
        "Pinned Lurker header unexpectedly contains leaveGame()."
    )

if "PASS-NO-LEAVE-v1" not in header_v1:
    raise SystemExit(
        "Pinned Lurker binary marker is missing."
    )

local_registry = REGISTRY.read_text()
local_runner = RUNNER.read_text()

if local_registry not in (registry_v2, registry_v3):
    raise SystemExit(
        "CapabilityRegistry.h is not a known Spire/Lurker state. "
        "No files changed."
    )

if local_runner not in (runner_v2, runner_v3):
    raise SystemExit(
        "scripts/novabw_test.py is not a known Spire/Lurker state. "
        "No files changed."
    )

test_text = TEST_MAIN.read_text()

if '#include "NovaBWLurker.h"' not in test_text:
    test_text = (
        test_text.rstrip()
        + '\n\n#include "NovaBWLurker.h"\n'
    )

backup_dir = Path(
    tempfile.mkdtemp(prefix="novabw_lurker_backup_")
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
        backup = backup_dir / path.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)


def restore():
    print(
        "[LURKER] FAILED - restoring previous local source",
        file=sys.stderr,
        flush=True,
    )

    for path in tracked:
        backup = backup_dir / path.relative_to(ROOT)

        if existed[path]:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, path)
        elif path.exists():
            path.unlink()


try:
    print("[LURKER] installing pinned capability bundle", flush=True)

    REGISTRY.write_text(registry_v3)
    RUNNER.write_text(runner_v3)
    RUNNER.chmod(0o755)

    SERVER.parent.mkdir(parents=True, exist_ok=True)
    SERVER.write_text(server_v1)

    HEADER.write_text(header_v1)
    TEST_MAIN.write_text(test_text)

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

    # Force the translation unit containing the new scenario header to rebuild.
    os.utime(TEST_MAIN, None)

    jobs = str(os.cpu_count() or 8)

    run(
        [
            "cmake",
            "--build",
            "build",
            "--target",
            "tests",
            "-j" + jobs,
        ],
        env=os.environ.copy(),
    )

    if not TEST_BIN.exists():
        raise RuntimeError("test binary missing after build")

    binary_strings = run(
        ["strings", str(TEST_BIN)],
        env=os.environ.copy(),
        capture=True,
    ).stdout

    if "PASS-NO-LEAVE-v1" not in binary_strings:
        raise RuntimeError(
            "Rebuilt test binary does not contain "
            "PASS-NO-LEAVE-v1 marker"
        )

    print(
        "[LURKER] binary marker verified: PASS-NO-LEAVE-v1",
        flush=True,
    )

    env = os.environ.copy()
    env["OPENBW_GAME_SPEED"] = "0"
    env["OPENBW_ENABLE_UI"] = "0"

    print(
        "\n[LURKER] compatibility smoke: Spire adapter path",
        flush=True,
    )

    run(
        [
            "./tests",
            "--gtest_filter=NovaBW.ZergSpireAirThroughAdapter",
        ],
        cwd=ROOT / "build/test",
        env=env,
    )

    print(
        "\n[LURKER] Direct / Adapter / Python bundle",
        flush=True,
    )

    run(
        [
            sys.executable,
            "scripts/novabw_test.py",
            "lurker",
            "--no-build",
        ],
        env=os.environ.copy(),
    )

except Exception:
    restore()
    raise

finally:
    shutil.rmtree(backup_dir, ignore_errors=True)


print()
print("=======================================")
print(" NOVA-Z LURKER v1: ALL TESTS PASSED")
print("=======================================")
print("Registered:")
print("  Research lurker_aspect")
print("  Morph    zerg_lurker")
print()
print("Full regression:")
print("  python scripts/novabw_test.py core")
