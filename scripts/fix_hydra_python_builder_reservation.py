#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys
import time

ROOT = Path.home() / "NovaBW" / "stardust-env"
SERVER = ROOT / "python" / "hydra_research_test_server.py"
TEST_DIR = ROOT / "build" / "test"

if not ROOT.exists():
    raise SystemExit(f"NovaBW root not found: {ROOT}")

server_code = r'''import json
import socket

HOST = "127.0.0.1"
PORT = 8765
MINERAL_RESERVE = 700
BUILD_TIMEOUT = 720

pool_issued = False
pool_builder_id = None
pool_issue_frame = -1

extractor_issued = False
extractor_builder_id = None
extractor_issue_frame = -1

den_issued = False
den_builder_id = None
den_issue_frame = -1

gas_worker_id = None

hydra_issued = False
research_issued = False
upgrade_issued = False


def act(
    kind="None",
    unit=-1,
    target=-1,
    unit_type=-1,
    tech=-1,
    upgrade=-1,
    tx=-1,
    ty=-1,
):
    return {
        "type": "action",
        "actionType": kind,
        "unitId": unit,
        "targetUnitId": target,
        "unitTypeId": unit_type,
        "techTypeId": tech,
        "upgradeTypeId": upgrade,
        "targetTileX": tx,
        "targetTileY": ty,
        "targetX": 0,
        "targetY": 0,
    }


def choose(obs):
    global pool_issued, pool_builder_id, pool_issue_frame
    global extractor_issued, extractor_builder_id, extractor_issue_frame
    global den_issued, den_builder_id, den_issue_frame
    global gas_worker_id
    global hydra_issued, research_issued, upgrade_issued

    frame = obs.get("frame", 0)
    minerals = obs.get("minerals", 0)
    gas = obs.get("gas", 0)

    own = obs.get("ownUnits", [])
    resources = obs.get("resourceUnits", [])
    builds = obs.get("buildCandidates", [])
    morphs = obs.get("morphOptions", [])
    research = obs.get("researchOptions", [])
    upgrades = obs.get("upgradeOptions", [])

    workers = [
        u for u in own
        if u.get("worker") and u.get("completed")
    ]
    worker_ids = {u["id"] for u in workers}

    pool_present = any(
        u.get("unitTypeKey") == "zerg_spawning_pool"
        for u in own
    )
    pool_complete = any(
        u.get("unitTypeKey") == "zerg_spawning_pool"
        and u.get("completed")
        for u in own
    )

    extractor = next(
        (
            u for u in own
            if u.get("unitTypeKey") == "zerg_extractor"
            and u.get("completed")
        ),
        None,
    )
    extractor_present = any(
        u.get("unitTypeKey") == "zerg_extractor"
        for u in own
    )

    den_present = any(
        u.get("unitTypeKey") == "zerg_hydralisk_den"
        for u in own
    )
    den_complete = any(
        u.get("unitTypeKey") == "zerg_hydralisk_den"
        and u.get("completed")
        for u in own
    )

    hydra_complete = any(
        u.get("unitTypeKey") == "zerg_hydralisk"
        and u.get("completed")
        for u in own
    )

    # Release builder reservations only after the building actually appears.
    if pool_present:
        pool_builder_id = None

    if extractor_present:
        extractor_builder_id = None

    if den_present:
        den_builder_id = None

    # Retry only if a previously accepted Build never materialized.
    if pool_issued and not pool_present and frame - pool_issue_frame > BUILD_TIMEOUT:
        print("[Nova-Z][PY-HYDRA] Pool build timeout -> retry", flush=True)
        pool_issued = False
        pool_builder_id = None
        pool_issue_frame = -1

    if (
        extractor_issued
        and not extractor_present
        and frame - extractor_issue_frame > BUILD_TIMEOUT
    ):
        print("[Nova-Z][PY-HYDRA] Extractor build timeout -> retry", flush=True)
        extractor_issued = False
        extractor_builder_id = None
        extractor_issue_frame = -1

    if den_issued and not den_present and frame - den_issue_frame > BUILD_TIMEOUT:
        print("[Nova-Z][PY-HYDRA] Den build timeout -> retry", flush=True)
        den_issued = False
        den_builder_id = None
        den_issue_frame = -1

    if gas_worker_id is not None and gas_worker_id not in worker_ids:
        gas_worker_id = None

    reserved = {
        x for x in (
            pool_builder_id,
            extractor_builder_id,
            den_builder_id,
            gas_worker_id,
        )
        if x is not None
    }

    # Pool. Reserve the builder until the structure appears.
    if not pool_issued and minerals >= MINERAL_RESERVE:
        c = next(
            (
                c for c in builds
                if c.get("unitTypeKey") == "zerg_spawning_pool"
                and c.get("builderUnitId") not in reserved
            ),
            None,
        )

        if (
            c
            and minerals >= c.get("mineralCost", 0)
            and gas >= c.get("gasCost", 0)
        ):
            pool_issued = True
            pool_builder_id = c["builderUnitId"]
            pool_issue_frame = frame

            print(
                f"[Nova-Z][PY-HYDRA] Build Pool builder={pool_builder_id} frame={frame}",
                flush=True,
            )

            return act(
                "Build",
                pool_builder_id,
                unit_type=c["unitTypeId"],
                tx=c["tileX"],
                ty=c["tileY"],
            )

    # Do not try to start Extractor until Pool construction has actually appeared.
    # This prevents the same Drone from being reused during the build-order transition.
    if pool_present and not extractor_issued:
        c = next(
            (
                c for c in builds
                if c.get("unitTypeKey") == "zerg_extractor"
                and c.get("builderUnitId") not in reserved
            ),
            None,
        )

        if (
            c
            and minerals >= c.get("mineralCost", 0)
            and gas >= c.get("gasCost", 0)
        ):
            extractor_issued = True
            extractor_builder_id = c["builderUnitId"]
            extractor_issue_frame = frame

            print(
                f"[Nova-Z][PY-HYDRA] Build Extractor builder={extractor_builder_id} frame={frame}",
                flush=True,
            )

            return act(
                "Build",
                extractor_builder_id,
                unit_type=c["unitTypeId"],
                tx=c["tileX"],
                ty=c["tileY"],
            )

    # Dedicated gas worker.
    if extractor and gas_worker_id is None:
        available = [
            w for w in workers
            if w["id"] not in reserved
        ]

        if available:
            gas_worker_id = available[0]["id"]

            print(
                f"[Nova-Z][PY-HYDRA] Gather gas worker={gas_worker_id} frame={frame}",
                flush=True,
            )

            return act(
                "Gather",
                gas_worker_id,
                target=extractor["id"],
            )

    reserved = {
        x for x in (
            pool_builder_id,
            extractor_builder_id,
            den_builder_id,
            gas_worker_id,
        )
        if x is not None
    }

    # Hydralisk Den. Also reserve this Drone until the Den appears.
    if pool_complete and not den_issued:
        c = next(
            (
                c for c in builds
                if c.get("unitTypeKey") == "zerg_hydralisk_den"
                and c.get("builderUnitId") not in reserved
            ),
            None,
        )

        if (
            c
            and minerals >= c.get("mineralCost", 0)
            and gas >= c.get("gasCost", 0)
        ):
            den_issued = True
            den_builder_id = c["builderUnitId"]
            den_issue_frame = frame

            print(
                f"[Nova-Z][PY-HYDRA] Build Hydralisk Den builder={den_builder_id} frame={frame}",
                flush=True,
            )

            return act(
                "Build",
                den_builder_id,
                unit_type=c["unitTypeId"],
                tx=c["tileX"],
                ty=c["tileY"],
            )

    if den_complete and not hydra_issued:
        o = next(
            (
                o for o in morphs
                if o.get("unitTypeKey") == "zerg_hydralisk"
            ),
            None,
        )

        if (
            o
            and minerals >= o.get("mineralCost", 0)
            and gas >= o.get("gasCost", 0)
        ):
            hydra_issued = True

            print(
                f"[Nova-Z][PY-HYDRA] Morph Hydralisk frame={frame}",
                flush=True,
            )

            return act(
                "Morph",
                o["actorUnitId"],
                unit_type=o["unitTypeId"],
            )

    if hydra_complete and not research_issued:
        o = next(
            (
                o for o in research
                if o.get("techKey") == "burrowing"
            ),
            None,
        )

        if (
            o
            and minerals >= o.get("mineralCost", 0)
            and gas >= o.get("gasCost", 0)
        ):
            research_issued = True

            print(
                f"[Nova-Z][PY-HYDRA] Research Burrowing frame={frame}",
                flush=True,
            )

            return act(
                "Research",
                o["actorUnitId"],
                tech=o["techTypeId"],
            )

    if research_issued and not upgrade_issued:
        o = next(
            (
                o for o in upgrades
                if o.get("upgradeKey") == "muscular_augments"
            ),
            None,
        )

        if (
            o
            and minerals >= o.get("mineralCost", 0)
            and gas >= o.get("gasCost", 0)
        ):
            upgrade_issued = True

            print(
                f"[Nova-Z][PY-HYDRA] Upgrade Muscular Augments frame={frame}",
                flush=True,
            )

            return act(
                "Upgrade",
                o["actorUnitId"],
                upgrade=o["upgradeTypeId"],
            )

    # Idle mineral workers must never overwrite an outstanding Build or gas order.
    mineral_fields = [
        r for r in resources
        if r.get("mineralField")
        and r.get("resources", 0) > 0
    ]

    reserved = {
        x for x in (
            pool_builder_id,
            extractor_builder_id,
            den_builder_id,
            gas_worker_id,
        )
        if x is not None
    }

    for w in workers:
        if (
            w["id"] in reserved
            or not w.get("idle")
            or not mineral_fields
        ):
            continue

        m = min(
            mineral_fields,
            key=lambda r: (
                (w["x"] - r["x"]) ** 2
                + (w["y"] - r["y"]) ** 2
            ),
        )

        return act(
            "Gather",
            w["id"],
            target=m["id"],
        )

    return act()


def main():
    print(
        f"[Nova-Z][PY-HYDRA] listening on {HOST}:{PORT}",
        flush=True,
    )

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as server:
        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )
        server.bind((HOST, PORT))
        server.listen(1)

        conn, addr = server.accept()

        print(
            f"[Nova-Z][PY-HYDRA] connected from {addr}",
            flush=True,
        )

        with conn:
            reader = conn.makefile("r", encoding="utf-8")
            writer = conn.makefile("w", encoding="utf-8")

            for line in reader:
                line = line.strip()
                if not line:
                    continue

                obs = json.loads(line)

                if obs.get("type") != "observation":
                    continue

                writer.write(
                    json.dumps(choose(obs)) + "\n"
                )
                writer.flush()


if __name__ == "__main__":
    main()
'''

SERVER.write_text(server_code)

subprocess.run(
    [sys.executable, "-m", "py_compile", str(SERVER)],
    check=True,
)

print("[FIX] builder reservation + staged construction policy installed")

env = os.environ.copy()
env["OPENBW_GAME_SPEED"] = "0"
env["OPENBW_ENABLE_UI"] = "0"

proc = subprocess.Popen(
    [sys.executable, str(SERVER)],
    cwd=ROOT,
    env=os.environ.copy(),
)

try:
    time.sleep(1)

    result = subprocess.run(
        [
            "./tests",
            "--gtest_filter=NovaBW.PythonHydraResearchIntegration",
        ],
        cwd=TEST_DIR,
        env=env,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)
finally:
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

print("NOVA-Z PYTHON HYDRA/RESEARCH: PASSED")
