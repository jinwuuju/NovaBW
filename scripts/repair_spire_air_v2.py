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
SERVER = ROOT / "python/spire_air_test_server.py"
HEADER = ROOT / "test/NovaBWSpireAir.h"
TEST_MAIN = ROOT / "test/NovaBW.cpp"
TEST_BIN = ROOT / "build/test/tests"

URLS = {
    "registry_v1": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "cd1bfe85b1c9cedd1cd26fb4136f747cc64fc44f/"
        "src/NovaBW/CapabilityRegistry.h"
    ),
    "runner_v1": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "11ca5f4de4134c153f7d95c084feef72ed660c95/"
        "scripts/novabw_test.py"
    ),
    "registry_v2": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "ff894c3cbfe8b8c27922d40b979b3c9b56b4adfe/"
        "src/NovaBW/CapabilityRegistry.h"
    ),
    "runner_v2": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "2045d5b4f6583acb8d3b4f77899387a43e50fa57/"
        "scripts/novabw_test.py"
    ),
    "server_v2": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "aa9ef752d8831596d85a4343896d927a78b0e6e1/"
        "python/spire_air_test_server.py"
    ),
    "header_v2": (
        "https://raw.githubusercontent.com/"
        "jinwuuju/NovaBW/"
        "4fa362e64eb828143bf989380d0a5156474e4180/"
        "test/NovaBWSpireAir.h"
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


print("[SPIRE-v2] preflight", flush=True)

registry_v1 = fetch(URLS["registry_v1"])
runner_v1 = fetch(URLS["runner_v1"])
registry_v2 = fetch(URLS["registry_v2"])
runner_v2 = fetch(URLS["runner_v2"])
server_v2 = fetch(URLS["server_v2"])
header_v2 = fetch(URLS["header_v2"])

if "leaveGame()" in header_v2:
    raise SystemExit(
        "Pinned Spire header unexpectedly contains leaveGame()."
    )

if "[PASS-NO-LEAVE-v2]" not in header_v2:
    raise SystemExit(
        "Pinned Spire header marker missing."
    )

local_registry = REGISTRY.read_text()
local_runner = RUNNER.read_text()

if local_registry not in (registry_v1, registry_v2):
    raise SystemExit(
        "CapabilityRegistry.h is not a known v1/v2 state. "
        "No files changed."
    )

if local_runner not in (runner_v1, runner_v2):
    raise SystemExit(
        "scripts/novabw_test.py is not a known v1/v2 state. "
        "No files changed."
    )

test_text = TEST_MAIN.read_text()

if '#include "NovaBWSpireAir.h"' not in test_text:
    test_text = (
        test_text.rstrip()
        + '\n\n#include "NovaBWSpireAir.h"\n'
    )

backup_dir = Path(
    tempfile.mkdtemp(prefix="novabw_spire_v2_backup_")
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
        "[SPIRE-v2] FAILED - restoring previous local source",
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
    print("[SPIRE-v2] installing pinned sources", flush=True)

    REGISTRY.write_text(registry_v2)
    RUNNER.write_text(runner_v2)
    RUNNER.chmod(0o755)

    SERVER.parent.mkdir(parents=True, exist_ok=True)
    SERVER.write_text(server_v2)

    HEADER.write_text(header_v2)
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

    # Force the translation unit that includes NovaBWSpireAir.h to rebuild,
    # even if the previous attempt left a stale dependency timestamp.
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

    marker = run(
        ["strings", str(TEST_BIN)],
        env=os.environ.copy(),
        capture=True,
    ).stdout

    if "PASS-NO-LEAVE-v2" not in marker:
        raise RuntimeError(
            "Rebuilt test binary does not contain "
            "PASS-NO-LEAVE-v2 marker"
        )

    print(
        "[SPIRE-v2] binary marker verified: PASS-NO-LEAVE-v2",
        flush=True,
    )

    env = os.environ.copy()
    env["OPENBW_GAME_SPEED"] = "0"
    env["OPENBW_ENABLE_UI"] = "0"

    print(
        "\n[SPIRE-v2] direct scenario first",
        flush=True,
    )

    run(
        [
            "./tests",
            "--gtest_filter=NovaBW.ZergSpireAirDeterministic",
        ],
        cwd=ROOT / "build/test",
        env=env,
    )

    print(
        "\n[SPIRE-v2] direct passed; running Adapter + Python",
        flush=True,
    )

    # Run only the remaining two layers here to avoid repeating direct.
    run(
        [
            "./tests",
            "--gtest_filter=NovaBW.ZergSpireAirThroughAdapter",
        ],
        cwd=ROOT / "build/test",
        env=env,
    )

    log_dir = ROOT / "runs/spire_air_v2"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "python_server.log"

    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(SERVER)],
            cwd=ROOT,
            env=os.environ.copy(),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            import time
            time.sleep(1)

            run(
                [
                    "./tests",
                    "--gtest_filter=NovaBW.PythonSpireAirIntegration",
                ],
                cwd=ROOT / "build/test",
                env=env,
            )
        finally:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

except Exception:
    restore()
    raise

finally:
    shutil.rmtree(backup_dir, ignore_errors=True)


print()
print("========================================")
print(" NOVA-Z SPIRE AIR v2: ALL TESTS PASSED")
print("========================================")
print("Verified pinned no-leave test binary.")
print("Direct / Adapter / Python all passed.")
