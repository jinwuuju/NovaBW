#!/usr/bin/env python3
from pathlib import Path
import argparse
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "build" / "test"
RUN_DIR = ROOT / "runs" / "core_regression"
RUN_DIR.mkdir(parents=True, exist_ok=True)

ENV = os.environ.copy()
ENV["OPENBW_GAME_SPEED"] = "0"
ENV["OPENBW_ENABLE_UI"] = "0"

def run(cmd, cwd=ROOT, env=None):
    print("\n+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run(
        cmd,
        cwd=cwd,
        env=env or ENV,
        check=True,
    )

def gtest(name):
    run(
        ["./tests", "--gtest_filter=" + name],
        cwd=TEST_DIR,
    )

def python_test(server, test_name):
    log_path = RUN_DIR / (Path(server).stem + ".log")

    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, server],
            cwd=ROOT,
            env=os.environ.copy(),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            time.sleep(1)
            gtest(test_name)
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

def gas_lair():
    gtest("NovaBW.ZergGasToLairDeterministic")
    gtest("NovaBW.ZergGasToLairThroughAdapter")
    python_test(
        "python/gas_lair_test_server.py",
        "NovaBW.PythonGasToLairIntegration",
    )

def hydra():
    gtest("NovaBW.ZergHydraResearchDeterministic")
    gtest("NovaBW.ZergHydraResearchThroughAdapter")
    python_test(
        "python/hydra_research_test_server.py",
        "NovaBW.PythonHydraResearchIntegration",
    )

def spire_air():
    gtest("NovaBW.ZergSpireAirDeterministic")
    gtest("NovaBW.ZergSpireAirThroughAdapter")
    python_test(
        "python/spire_air_test_server.py",
        "NovaBW.PythonSpireAirIntegration",
    )

parser = argparse.ArgumentParser()
parser.add_argument(
    "suite",
    nargs="?",
    default="core",
    choices=["core", "gas-lair", "hydra", "spire-air"],
)
parser.add_argument(
    "--no-build",
    action="store_true",
)
args = parser.parse_args()

if not args.no_build:
    jobs = str(os.cpu_count() or 8)
    run(
        ["cmake", "--build", "build", "-j" + jobs],
        env=os.environ.copy(),
    )

if args.suite in ("core", "gas-lair"):
    gas_lair()

if args.suite in ("core", "hydra"):
    hydra()

if args.suite in ("core", "spire-air"):
    spire_air()

print("\n======================================")
print(" NOVABW REGRESSION PASSED:", args.suite)
print("======================================")
