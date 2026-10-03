import json
import socket

HOST = "127.0.0.1"
PORT = 8765

MINERAL_RESERVE = 950
BUILD_TIMEOUT = 720

pool_issued = False
pool_builder_id = None
pool_issue_frame = -1

extractor_issued = False
extractor_builder_id = None
extractor_issue_frame = -1

gas_worker_id = None

lair_issued = False

den_issued = False
den_builder_id = None
den_issue_frame = -1

aspect_issued = False
hydra_issued = False
lurker_issued = False


def act(
    kind="None",
    unit=-1,
    target=-1,
    unit_type=-1,
    tech=-1,
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
        "upgradeTypeId": -1,
        "targetTileX": tx,
        "targetTileY": ty,
        "targetX": 0,
        "targetY": 0,
    }


def choose(obs):
    global pool_issued, pool_builder_id, pool_issue_frame
    global extractor_issued, extractor_builder_id, extractor_issue_frame
    global gas_worker_id
    global lair_issued
    global den_issued, den_builder_id, den_issue_frame
    global aspect_issued, hydra_issued, lurker_issued

    frame = obs.get("frame", 0)
    minerals = obs.get("minerals", 0)
    gas = obs.get("gas", 0)

    own = obs.get("ownUnits", [])
    resources = obs.get("resourceUnits", [])
    builds = obs.get("buildCandidates", [])
    morphs = obs.get("morphOptions", [])
    research = obs.get("researchOptions", [])

    workers = [
        unit for unit in own
        if unit.get("worker") and unit.get("completed")
    ]
    worker_ids = {unit["id"] for unit in workers}

    pool_present = any(
        unit.get("unitTypeKey") == "zerg_spawning_pool"
        for unit in own
    )
    pool_complete = any(
        unit.get("unitTypeKey") == "zerg_spawning_pool"
        and unit.get("completed")
        for unit in own
    )

    extractor = next(
        (
            unit for unit in own
            if unit.get("unitTypeKey") == "zerg_extractor"
            and unit.get("completed")
        ),
        None,
    )
    extractor_present = any(
        unit.get("unitTypeKey") == "zerg_extractor"
        for unit in own
    )

    lair_complete = any(
        unit.get("unitTypeKey") == "zerg_lair"
        and unit.get("completed")
        for unit in own
    )

    den_present = any(
        unit.get("unitTypeKey") == "zerg_hydralisk_den"
        for unit in own
    )
    den_complete = any(
        unit.get("unitTypeKey") == "zerg_hydralisk_den"
        and unit.get("completed")
        for unit in own
    )

    if pool_present:
        pool_builder_id = None

    if extractor_present:
        extractor_builder_id = None

    if den_present:
        den_builder_id = None

    if (
        pool_issued
        and not pool_present
        and frame - pool_issue_frame > BUILD_TIMEOUT
    ):
        pool_issued = False
        pool_builder_id = None
        pool_issue_frame = -1
        print("[Nova-Z][PY-LURKER] Pool build timeout -> retry", flush=True)

    if (
        extractor_issued
        and not extractor_present
        and frame - extractor_issue_frame > BUILD_TIMEOUT
    ):
        extractor_issued = False
        extractor_builder_id = None
        extractor_issue_frame = -1
        print("[Nova-Z][PY-LURKER] Extractor build timeout -> retry", flush=True)

    if (
        den_issued
        and not den_present
        and frame - den_issue_frame > BUILD_TIMEOUT
    ):
        den_issued = False
        den_builder_id = None
        den_issue_frame = -1
        print("[Nova-Z][PY-LURKER] Den build timeout -> retry", flush=True)

    if gas_worker_id is not None and gas_worker_id not in worker_ids:
        gas_worker_id = None

    reserved = {
        unit_id
        for unit_id in (
            pool_builder_id,
            extractor_builder_id,
            den_builder_id,
            gas_worker_id,
        )
        if unit_id is not None
    }

    if not pool_issued and minerals >= MINERAL_RESERVE:
        candidate = next(
            (
                c for c in builds
                if c.get("unitTypeKey") == "zerg_spawning_pool"
                and c.get("builderUnitId") not in reserved
            ),
            None,
        )

        if candidate:
            pool_issued = True
            pool_builder_id = candidate["builderUnitId"]
            pool_issue_frame = frame

            print(
                f"[Nova-Z][PY-LURKER] Build Pool builder={pool_builder_id} frame={frame}",
                flush=True,
            )

            return act(
                "Build",
                pool_builder_id,
                unit_type=candidate["unitTypeId"],
                tx=candidate["tileX"],
                ty=candidate["tileY"],
            )

    if pool_present and not extractor_issued:
        candidate = next(
            (
                c for c in builds
                if c.get("unitTypeKey") == "zerg_extractor"
                and c.get("builderUnitId") not in reserved
            ),
            None,
        )

        if candidate:
            extractor_issued = True
            extractor_builder_id = candidate["builderUnitId"]
            extractor_issue_frame = frame

            print(
                f"[Nova-Z][PY-LURKER] Build Extractor builder={extractor_builder_id} frame={frame}",
                flush=True,
            )

            return act(
                "Build",
                extractor_builder_id,
                unit_type=candidate["unitTypeId"],
                tx=candidate["tileX"],
                ty=candidate["tileY"],
            )

    if extractor and gas_worker_id is None:
        available = [
            worker
            for worker in workers
            if worker["id"] not in reserved
        ]

        if available:
            gas_worker_id = available[0]["id"]

            print(
                f"[Nova-Z][PY-LURKER] Gather gas worker={gas_worker_id} frame={frame}",
                flush=True,
            )

            return act(
                "Gather",
                gas_worker_id,
                target=extractor["id"],
            )

    if pool_complete and not lair_issued:
        option = next(
            (
                option for option in morphs
                if option.get("unitTypeKey") == "zerg_lair"
            ),
            None,
        )

        if option:
            lair_issued = True

            print(
                f"[Nova-Z][PY-LURKER] Morph Lair frame={frame}",
                flush=True,
            )

            return act(
                "Morph",
                option["actorUnitId"],
                unit_type=option["unitTypeId"],
            )

    reserved = {
        unit_id
        for unit_id in (
            pool_builder_id,
            extractor_builder_id,
            den_builder_id,
            gas_worker_id,
        )
        if unit_id is not None
    }

    if lair_complete and not den_issued:
        candidate = next(
            (
                c for c in builds
                if c.get("unitTypeKey") == "zerg_hydralisk_den"
                and c.get("builderUnitId") not in reserved
            ),
            None,
        )

        if candidate:
            den_issued = True
            den_builder_id = candidate["builderUnitId"]
            den_issue_frame = frame

            print(
                f"[Nova-Z][PY-LURKER] Build Hydralisk Den builder={den_builder_id} frame={frame}",
                flush=True,
            )

            return act(
                "Build",
                den_builder_id,
                unit_type=candidate["unitTypeId"],
                tx=candidate["tileX"],
                ty=candidate["tileY"],
            )

    if den_complete and not aspect_issued:
        option = next(
            (
                option for option in research
                if option.get("techKey") == "lurker_aspect"
            ),
            None,
        )

        if option:
            aspect_issued = True

            print(
                f"[Nova-Z][PY-LURKER] Research Lurker Aspect frame={frame}",
                flush=True,
            )

            return act(
                "Research",
                option["actorUnitId"],
                tech=option["techTypeId"],
            )

    if den_complete and aspect_issued and not hydra_issued:
        option = next(
            (
                option for option in morphs
                if option.get("unitTypeKey") == "zerg_hydralisk"
            ),
            None,
        )

        if option:
            hydra_issued = True

            print(
                f"[Nova-Z][PY-LURKER] Morph Hydralisk frame={frame}",
                flush=True,
            )

            return act(
                "Morph",
                option["actorUnitId"],
                unit_type=option["unitTypeId"],
            )

    if hydra_issued and not lurker_issued:
        option = next(
            (
                option for option in morphs
                if option.get("unitTypeKey") == "zerg_lurker"
            ),
            None,
        )

        if option:
            lurker_issued = True

            print(
                f"[Nova-Z][PY-LURKER] Morph Lurker frame={frame}",
                flush=True,
            )

            return act(
                "Morph",
                option["actorUnitId"],
                unit_type=option["unitTypeId"],
            )

    mineral_fields = [
        resource
        for resource in resources
        if resource.get("mineralField")
        and resource.get("resources", 0) > 0
    ]

    reserved = {
        unit_id
        for unit_id in (
            pool_builder_id,
            extractor_builder_id,
            den_builder_id,
            gas_worker_id,
        )
        if unit_id is not None
    }

    for worker in workers:
        if (
            worker["id"] in reserved
            or not worker.get("idle")
            or not mineral_fields
        ):
            continue

        mineral = min(
            mineral_fields,
            key=lambda resource: (
                (worker["x"] - resource["x"]) ** 2
                + (worker["y"] - resource["y"]) ** 2
            ),
        )

        return act(
            "Gather",
            worker["id"],
            target=mineral["id"],
        )

    return act()


def main():
    print(
        f"[Nova-Z][PY-LURKER] listening on {HOST}:{PORT}",
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

        connection, address = server.accept()

        print(
            f"[Nova-Z][PY-LURKER] connected from {address}",
            flush=True,
        )

        with connection:
            reader = connection.makefile("r", encoding="utf-8")
            writer = connection.makefile("w", encoding="utf-8")

            for line in reader:
                line = line.strip()

                if not line:
                    continue

                observation = json.loads(line)

                if observation.get("type") != "observation":
                    continue

                writer.write(
                    json.dumps(choose(observation)) + "\n"
                )
                writer.flush()


if __name__ == "__main__":
    main()
