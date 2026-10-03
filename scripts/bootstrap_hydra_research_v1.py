#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys
import textwrap
import time

ROOT = Path(os.environ.get("NOVABW_ROOT", Path.home() / "NovaBW" / "stardust-env")).resolve()
if not ROOT.exists():
    raise SystemExit(f"NovaBW root not found: {ROOT}")

def run(cmd, cwd=ROOT, env=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    merged = os.environ.copy()
    if env:
        merged.update(env)
    subprocess.run(cmd, cwd=cwd, env=merged, check=True)

def require(path, tokens):
    text = (ROOT / path).read_text()
    missing = [t for t in tokens if t not in text]
    if missing:
        raise SystemExit(f"{path}: missing prior patch markers: {missing}")
    return text

print("[BOOTSTRAP] validating partial Hydra/Research patch", flush=True)
require("src/NovaBW/Protocol.h", [
    "ResearchOptionObservation",
    "UpgradeOptionObservation",
    "Research,",
    "Upgrade,",
    "techTypeId",
    "upgradeTypeId",
])
require("src/NovaBW/OpenBWAdapter.cpp", [
    "Zerg_Hydralisk_Den",
    "Zerg_Hydralisk",
    "case ActionType::Research:",
    "case ActionType::Upgrade:",
    "Current executable research options",
    "Current executable upgrade options",
])
require("src/NovaBW/PythonBridge.cpp", [
    'actionType == "Research"',
    'actionType == "Upgrade"',
    'message["researchOptions"]',
    'message["upgradeOptions"]',
])

adapter_path = ROOT / "src/NovaBW/OpenBWAdapter.cpp"
adapter = adapter_path.read_text()
old = """            if (
                !denBuilder &&
                unit->getType() ==
                    BWAPI::UnitTypes::Zerg_Drone &&
                unit->isCompleted()
            )
"""
new = """            if (
                !denBuilder &&
                unit->getType() ==
                    BWAPI::UnitTypes::Zerg_Drone &&
                unit->isCompleted() &&
                !unit->isGatheringGas() &&
                !unit->isConstructing()
            )
"""
if old in adapter:
    adapter = adapter.replace(old, new, 1)
    adapter_path.write_text(adapter)
    print("[BOOTSTRAP] Hydralisk Den builder mask hardened", flush=True)

jobs = str(os.cpu_count() or 8)
run(["cmake", "--build", "build", "-j" + jobs])

server = r'''import json
import socket

HOST = "127.0.0.1"
PORT = 8765
MINERAL_RESERVE = 700

pool_issued = False
extractor_issued = False
den_issued = False
gas_worker_id = None
hydra_issued = False
research_issued = False
upgrade_issued = False

def act(kind="None", unit=-1, target=-1, unit_type=-1, tech=-1, upgrade=-1, tx=-1, ty=-1):
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
    global pool_issued, extractor_issued, den_issued
    global gas_worker_id, hydra_issued, research_issued, upgrade_issued

    minerals = obs.get("minerals", 0)
    gas = obs.get("gas", 0)
    own = obs.get("ownUnits", [])
    resources = obs.get("resourceUnits", [])
    builds = obs.get("buildCandidates", [])
    morphs = obs.get("morphOptions", [])
    research = obs.get("researchOptions", [])
    upgrades = obs.get("upgradeOptions", [])

    workers = [u for u in own if u.get("worker") and u.get("completed")]
    worker_ids = {u["id"] for u in workers}
    if gas_worker_id is not None and gas_worker_id not in worker_ids:
        gas_worker_id = None

    pool_complete = any(
        u.get("unitTypeKey") == "zerg_spawning_pool" and u.get("completed")
        for u in own
    )
    extractor = next(
        (u for u in own if u.get("unitTypeKey") == "zerg_extractor" and u.get("completed")),
        None,
    )
    den_complete = any(
        u.get("unitTypeKey") == "zerg_hydralisk_den" and u.get("completed")
        for u in own
    )
    hydra_complete = any(
        u.get("unitTypeKey") == "zerg_hydralisk" and u.get("completed")
        for u in own
    )

    if not pool_issued and minerals >= MINERAL_RESERVE:
        c = next((c for c in builds if c.get("unitTypeKey") == "zerg_spawning_pool"), None)
        if c and minerals >= c.get("mineralCost", 0) and gas >= c.get("gasCost", 0):
            pool_issued = True
            print("[Nova-Z][PY-HYDRA] Build Pool", flush=True)
            return act("Build", c["builderUnitId"], unit_type=c["unitTypeId"], tx=c["tileX"], ty=c["tileY"])

    if pool_issued and not extractor_issued:
        c = next((c for c in builds if c.get("unitTypeKey") == "zerg_extractor"), None)
        if c and minerals >= c.get("mineralCost", 0) and gas >= c.get("gasCost", 0):
            extractor_issued = True
            print("[Nova-Z][PY-HYDRA] Build Extractor", flush=True)
            return act("Build", c["builderUnitId"], unit_type=c["unitTypeId"], tx=c["tileX"], ty=c["tileY"])

    if extractor and gas_worker_id is None:
        candidates = [w for w in workers if not w.get("idle") or True]
        if candidates:
            gas_worker_id = candidates[0]["id"]
            print(f"[Nova-Z][PY-HYDRA] Gather gas worker={gas_worker_id}", flush=True)
            return act("Gather", gas_worker_id, target=extractor["id"])

    if pool_complete and not den_issued:
        c = next((c for c in builds if c.get("unitTypeKey") == "zerg_hydralisk_den"), None)
        if c and minerals >= c.get("mineralCost", 0) and gas >= c.get("gasCost", 0):
            den_issued = True
            print("[Nova-Z][PY-HYDRA] Build Hydralisk Den", flush=True)
            return act("Build", c["builderUnitId"], unit_type=c["unitTypeId"], tx=c["tileX"], ty=c["tileY"])

    if den_complete and not hydra_issued:
        o = next((o for o in morphs if o.get("unitTypeKey") == "zerg_hydralisk"), None)
        if o and minerals >= o.get("mineralCost", 0) and gas >= o.get("gasCost", 0):
            hydra_issued = True
            print("[Nova-Z][PY-HYDRA] Morph Hydralisk", flush=True)
            return act("Morph", o["actorUnitId"], unit_type=o["unitTypeId"])

    if hydra_complete and not research_issued:
        o = next((o for o in research if o.get("techKey") == "burrowing"), None)
        if o and minerals >= o.get("mineralCost", 0) and gas >= o.get("gasCost", 0):
            research_issued = True
            print("[Nova-Z][PY-HYDRA] Research Burrowing", flush=True)
            return act("Research", o["actorUnitId"], tech=o["techTypeId"])

    if research_issued and not upgrade_issued:
        o = next((o for o in upgrades if o.get("upgradeKey") == "muscular_augments"), None)
        if o and minerals >= o.get("mineralCost", 0) and gas >= o.get("gasCost", 0):
            upgrade_issued = True
            print("[Nova-Z][PY-HYDRA] Upgrade Muscular Augments", flush=True)
            return act("Upgrade", o["actorUnitId"], upgrade=o["upgradeTypeId"])

    mineral_fields = [r for r in resources if r.get("mineralField") and r.get("resources", 0) > 0]
    for w in workers:
        if w["id"] == gas_worker_id or not w.get("idle") or not mineral_fields:
            continue
        m = min(mineral_fields, key=lambda r: (w["x"]-r["x"])**2 + (w["y"]-r["y"])**2)
        return act("Gather", w["id"], target=m["id"])

    return act()

def main():
    print(f"[Nova-Z][PY-HYDRA] listening on {HOST}:{PORT}", flush=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)
        conn, addr = server.accept()
        print(f"[Nova-Z][PY-HYDRA] connected from {addr}", flush=True)
        with conn:
            r = conn.makefile("r", encoding="utf-8")
            w = conn.makefile("w", encoding="utf-8")
            for line in r:
                line = line.strip()
                if not line:
                    continue
                obs = json.loads(line)
                if obs.get("type") != "observation":
                    continue
                w.write(json.dumps(choose(obs)) + "\n")
                w.flush()

if __name__ == "__main__":
    main()
'''
(ROOT / "python/hydra_research_test_server.py").write_text(server)
run([sys.executable, "-m", "py_compile", "python/hydra_research_test_server.py"])

test_path = ROOT / "test/NovaBW.cpp"
tests = test_path.read_text()
if "TEST(NovaBW, ZergHydraResearchDeterministic)" not in tests:
    addition = r'''

struct NovaZHydraResearchState
{
    bool poolAccepted = false;
    bool poolCompleted = false;
    bool extractorAccepted = false;
    bool extractorCompleted = false;
    bool gasGatherAccepted = false;
    bool denAccepted = false;
    bool denCompleted = false;
    bool hydraAccepted = false;
    bool hydraCompleted = false;
    bool researchAccepted = false;
    bool burrowCompleted = false;
    bool upgradeAccepted = false;
    bool muscularCompleted = false;
    int gasWorkerId = -1;
    int poolBuilderId = -1;
    int extractorBuilderId = -1;
    int denBuilderId = -1;
    bool passPrinted = false;
};

class NovaZHydraResearchModule : public BWAPI::AIModule
{
public:
    NovaZHydraResearchModule(
        std::shared_ptr<NovaZHydraResearchState> state,
        bool throughAdapter
    )
        : state(std::move(state)),
          throughAdapter(throughAdapter)
    {
    }

    void onStart() override
    {
        BWAPI::Broodwar->setLocalSpeed(0);
        std::cout
            << "[NOVA-Z][HYDRA] mode="
            << (throughAdapter ? "adapter" : "direct")
            << std::endl;
    }

    void onFrame() override
    {
        auto self = BWAPI::Broodwar->self();
        if (!self)
        {
            return;
        }

        BWAPI::Unit hatchery = nullptr;
        BWAPI::Unit extractor = nullptr;
        BWAPI::Unit den = nullptr;

        for (auto unit : self->getUnits())
        {
            if (!unit || !unit->exists())
            {
                continue;
            }

            const auto type = unit->getType();

            if (type == BWAPI::UnitTypes::Zerg_Hatchery)
            {
                hatchery = unit;
            }

            if (type == BWAPI::UnitTypes::Zerg_Spawning_Pool)
            {
                state->poolBuilderId = -1;
                if (unit->isCompleted())
                {
                    state->poolCompleted = true;
                }
            }

            if (type == BWAPI::UnitTypes::Zerg_Extractor)
            {
                extractor = unit;
                state->extractorBuilderId = -1;
                if (unit->isCompleted())
                {
                    state->extractorCompleted = true;
                }
            }

            if (type == BWAPI::UnitTypes::Zerg_Hydralisk_Den)
            {
                den = unit;
                state->denBuilderId = -1;
                if (unit->isCompleted())
                {
                    state->denCompleted = true;
                }
            }

            if (
                type == BWAPI::UnitTypes::Zerg_Hydralisk &&
                unit->isCompleted()
            )
            {
                state->hydraCompleted = true;
            }
        }

        state->burrowCompleted =
            self->hasResearched(BWAPI::TechTypes::Burrowing);

        state->muscularCompleted =
            self->getUpgradeLevel(
                BWAPI::UpgradeTypes::Muscular_Augments
            ) >= 1;

        if (
            state->hydraCompleted &&
            state->burrowCompleted &&
            state->muscularCompleted
        )
        {
            if (!state->passPrinted)
            {
                state->passPrinted = true;
                std::cout
                    << "[NOVA-Z][HYDRA][PASS] mode="
                    << (throughAdapter ? "adapter" : "direct")
                    << " frame="
                    << BWAPI::Broodwar->getFrameCount()
                    << std::endl;
            }
            return;
        }

        assignIdleMineralWorkers();

        const auto poolType = BWAPI::UnitTypes::Zerg_Spawning_Pool;
        const auto extractorType = BWAPI::UnitTypes::Zerg_Extractor;
        const auto denType = BWAPI::UnitTypes::Zerg_Hydralisk_Den;
        const auto hydraType = BWAPI::UnitTypes::Zerg_Hydralisk;
        const auto burrow = BWAPI::TechTypes::Burrowing;
        const auto muscular = BWAPI::UpgradeTypes::Muscular_Augments;

        const int reserve =
            poolType.mineralPrice() +
            extractorType.mineralPrice() +
            denType.mineralPrice() +
            hydraType.mineralPrice() +
            burrow.mineralPrice() +
            muscular.mineralPrice(1);

        if (!state->poolAccepted && self->minerals() >= reserve)
        {
            auto builder = firstDrone();
            if (builder && hatchery)
            {
                auto tile = BWAPI::Broodwar->getBuildLocation(
                    poolType,
                    hatchery->getTilePosition(),
                    20
                );
                if (
                    tile != BWAPI::TilePositions::None &&
                    issueBuild(builder, poolType, tile)
                )
                {
                    state->poolAccepted = true;
                    state->poolBuilderId = builder->getID();
                    std::cout << "[NOVA-Z][HYDRA] Pool accepted" << std::endl;
                    return;
                }
            }
        }

        if (
            state->poolAccepted &&
            !state->extractorAccepted &&
            self->minerals() >= extractorType.mineralPrice()
        )
        {
            auto builder = firstDrone();
            auto geyser = nearestGeyser(hatchery);
            if (
                builder &&
                geyser &&
                issueBuild(
                    builder,
                    extractorType,
                    geyser->getTilePosition()
                )
            )
            {
                state->extractorAccepted = true;
                state->extractorBuilderId = builder->getID();
                std::cout << "[NOVA-Z][HYDRA] Extractor accepted" << std::endl;
                return;
            }
        }

        if (
            state->extractorCompleted &&
            extractor &&
            state->gasWorkerId < 0
        )
        {
            auto worker = firstDrone();
            if (worker && issueGather(worker, extractor))
            {
                state->gasWorkerId = worker->getID();
                state->gasGatherAccepted = true;
                std::cout
                    << "[NOVA-Z][HYDRA] gas worker="
                    << state->gasWorkerId
                    << std::endl;
                return;
            }
        }

        if (
            state->poolCompleted &&
            !state->denAccepted &&
            hatchery &&
            self->minerals() >= denType.mineralPrice() &&
            self->gas() >= denType.gasPrice()
        )
        {
            auto builder = firstDrone();
            if (builder)
            {
                auto tile = BWAPI::Broodwar->getBuildLocation(
                    denType,
                    hatchery->getTilePosition(),
                    20
                );
                if (
                    tile != BWAPI::TilePositions::None &&
                    issueBuild(builder, denType, tile)
                )
                {
                    state->denAccepted = true;
                    state->denBuilderId = builder->getID();
                    std::cout
                        << "[NOVA-Z][HYDRA] Hydralisk Den accepted"
                        << std::endl;
                    return;
                }
            }
        }

        if (
            state->denCompleted &&
            !state->hydraAccepted &&
            self->minerals() >= hydraType.mineralPrice() &&
            self->gas() >= hydraType.gasPrice()
        )
        {
            for (auto unit : self->getUnits())
            {
                if (
                    unit &&
                    unit->exists() &&
                    unit->getType() == BWAPI::UnitTypes::Zerg_Larva &&
                    issueMorph(unit, hydraType)
                )
                {
                    state->hydraAccepted = true;
                    std::cout
                        << "[NOVA-Z][HYDRA] Hydralisk accepted"
                        << std::endl;
                    return;
                }
            }
        }

        if (
            state->hydraCompleted &&
            !state->researchAccepted &&
            hatchery &&
            self->minerals() >= burrow.mineralPrice() &&
            self->gas() >= burrow.gasPrice() &&
            issueResearch(hatchery, burrow)
        )
        {
            state->researchAccepted = true;
            std::cout
                << "[NOVA-Z][HYDRA] Burrowing accepted"
                << std::endl;
            return;
        }

        if (
            state->burrowCompleted &&
            !state->upgradeAccepted &&
            den &&
            den->isCompleted() &&
            self->minerals() >= muscular.mineralPrice(1) &&
            self->gas() >= muscular.gasPrice(1) &&
            issueUpgrade(den, muscular)
        )
        {
            state->upgradeAccepted = true;
            std::cout
                << "[NOVA-Z][HYDRA] Muscular Augments accepted"
                << std::endl;
        }
    }

private:
    std::shared_ptr<NovaZHydraResearchState> state;
    bool throughAdapter = false;
    novabw::OpenBWAdapter adapter;

    bool reserved(int id) const
    {
        return
            id == state->gasWorkerId ||
            id == state->poolBuilderId ||
            id == state->extractorBuilderId ||
            id == state->denBuilderId;
    }

    BWAPI::Unit firstDrone()
    {
        auto self = BWAPI::Broodwar->self();
        if (!self)
        {
            return nullptr;
        }

        for (auto unit : self->getUnits())
        {
            if (
                unit &&
                unit->exists() &&
                unit->isCompleted() &&
                unit->getType() == BWAPI::UnitTypes::Zerg_Drone &&
                !reserved(unit->getID())
            )
            {
                return unit;
            }
        }
        return nullptr;
    }

    BWAPI::Unit nearestMineral(BWAPI::Unit worker)
    {
        BWAPI::Unit best = nullptr;
        long long bestD = std::numeric_limits<long long>::max();

        for (auto mineral : BWAPI::Broodwar->getMinerals())
        {
            if (!mineral || !mineral->exists())
            {
                continue;
            }

            auto a = worker->getPosition();
            auto b = mineral->getPosition();
            long long dx = static_cast<long long>(a.x - b.x);
            long long dy = static_cast<long long>(a.y - b.y);
            long long d = dx * dx + dy * dy;

            if (d < bestD)
            {
                bestD = d;
                best = mineral;
            }
        }

        return best;
    }

    BWAPI::Unit nearestGeyser(BWAPI::Unit hatchery)
    {
        if (!hatchery)
        {
            return nullptr;
        }

        BWAPI::Unit best = nullptr;
        long long bestD = std::numeric_limits<long long>::max();

        for (auto geyser : BWAPI::Broodwar->getGeysers())
        {
            if (!geyser || !geyser->exists())
            {
                continue;
            }

            auto a = hatchery->getPosition();
            auto b = geyser->getPosition();
            long long dx = static_cast<long long>(a.x - b.x);
            long long dy = static_cast<long long>(a.y - b.y);
            long long d = dx * dx + dy * dy;

            if (d < bestD)
            {
                bestD = d;
                best = geyser;
            }
        }

        return best;
    }

    void assignIdleMineralWorkers()
    {
        auto self = BWAPI::Broodwar->self();
        if (!self)
        {
            return;
        }

        for (auto worker : self->getUnits())
        {
            if (
                !worker ||
                !worker->exists() ||
                !worker->isCompleted() ||
                worker->getType() != BWAPI::UnitTypes::Zerg_Drone ||
                reserved(worker->getID()) ||
                !worker->isIdle()
            )
            {
                continue;
            }

            auto mineral = nearestMineral(worker);
            if (mineral)
            {
                issueGather(worker, mineral);
            }
        }
    }

    bool issueGather(BWAPI::Unit actor, BWAPI::Unit target)
    {
        if (!throughAdapter)
        {
            return actor->gather(target);
        }

        novabw::Action a;
        a.type = novabw::ActionType::Gather;
        a.unitId = actor->getID();
        a.targetUnitId = target->getID();
        return adapter.execute(a);
    }

    bool issueBuild(
        BWAPI::Unit actor,
        BWAPI::UnitType type,
        BWAPI::TilePosition tile
    )
    {
        if (!throughAdapter)
        {
            return actor->build(type, tile);
        }

        novabw::Action a;
        a.type = novabw::ActionType::Build;
        a.unitId = actor->getID();
        a.unitTypeId = type.getID();
        a.targetTileX = tile.x;
        a.targetTileY = tile.y;
        return adapter.execute(a);
    }

    bool issueMorph(BWAPI::Unit actor, BWAPI::UnitType type)
    {
        if (!throughAdapter)
        {
            return actor->canMorph(type) && actor->morph(type);
        }

        novabw::Action a;
        a.type = novabw::ActionType::Morph;
        a.unitId = actor->getID();
        a.unitTypeId = type.getID();
        return adapter.execute(a);
    }

    bool issueResearch(BWAPI::Unit actor, BWAPI::TechType tech)
    {
        if (!throughAdapter)
        {
            return actor->canResearch(tech) && actor->research(tech);
        }

        novabw::Action a;
        a.type = novabw::ActionType::Research;
        a.unitId = actor->getID();
        a.techTypeId = tech.getID();
        return adapter.execute(a);
    }

    bool issueUpgrade(BWAPI::Unit actor, BWAPI::UpgradeType upgrade)
    {
        if (!throughAdapter)
        {
            return actor->canUpgrade(upgrade) && actor->upgrade(upgrade);
        }

        novabw::Action a;
        a.type = novabw::ActionType::Upgrade;
        a.unitId = actor->getID();
        a.upgradeTypeId = upgrade.getID();
        return adapter.execute(a);
    }
};

static void runNovaZHydraResearch(bool throughAdapter)
{
    auto state = std::make_shared<NovaZHydraResearchState>();

    BWTest test;
    test.map = Maps::GetOne("Python");
    test.myRace = BWAPI::Races::Zerg;
    test.opponentRace = BWAPI::Races::Terran;
    test.randomSeed = 12345;
    test.frameLimit = 30000;
    test.timeLimit = 90;
    test.expectWin = false;
    test.writeReplay = false;

    test.myModule = [state, throughAdapter]()
    {
        return new NovaZHydraResearchModule(
            state,
            throughAdapter
        );
    };

    test.onEndMine = [state](bool)
    {
        std::cout
            << "[NOVA-Z][HYDRA] SUMMARY"
            << " pool=" << state->poolCompleted
            << " extractor=" << state->extractorCompleted
            << " gasGather=" << state->gasGatherAccepted
            << " den=" << state->denCompleted
            << " hydra=" << state->hydraCompleted
            << " research=" << state->researchAccepted
            << " burrow=" << state->burrowCompleted
            << " upgrade=" << state->upgradeAccepted
            << " muscular=" << state->muscularCompleted
            << std::endl;

        EXPECT_TRUE(state->poolCompleted);
        EXPECT_TRUE(state->extractorCompleted);
        EXPECT_TRUE(state->gasGatherAccepted);
        EXPECT_TRUE(state->denCompleted);
        EXPECT_TRUE(state->hydraCompleted);
        EXPECT_TRUE(state->researchAccepted);
        EXPECT_TRUE(state->burrowCompleted);
        EXPECT_TRUE(state->upgradeAccepted);
        EXPECT_TRUE(state->muscularCompleted);
    };

    test.run();
}

TEST(NovaBW, ZergHydraResearchDeterministic)
{
    runNovaZHydraResearch(false);
}

TEST(NovaBW, ZergHydraResearchThroughAdapter)
{
    runNovaZHydraResearch(true);
}

struct NovaPythonHydraResearchState
{
    bool connected = false;
    bool denBuildExecuted = false;
    bool hydraMorphExecuted = false;
    bool researchExecuted = false;
    bool upgradeExecuted = false;
    bool denCompleted = false;
    bool hydraCompleted = false;
    bool burrowCompleted = false;
    bool muscularCompleted = false;
    int lastDecisionFrame = -999;
};

class NovaPythonHydraResearchModule : public BWAPI::AIModule
{
public:
    explicit NovaPythonHydraResearchModule(
        std::shared_ptr<NovaPythonHydraResearchState> state
    )
        : state(std::move(state))
    {
    }

    void onStart() override
    {
        BWAPI::Broodwar->setLocalSpeed(0);
        state->connected = bridge.connectToServer();
        std::cout
            << "[NOVA-Z][PY-HYDRA] connected="
            << state->connected
            << std::endl;
    }

    void onFrame() override
    {
        if (!state->connected)
        {
            return;
        }

        auto self = BWAPI::Broodwar->self();
        if (!self)
        {
            return;
        }

        const auto obs = adapter.observe();

        for (const auto &unit : obs.ownUnits)
        {
            if (
                unit.typeId ==
                    BWAPI::UnitTypes::Zerg_Hydralisk_Den.getID() &&
                unit.completed
            )
            {
                state->denCompleted = true;
            }

            if (
                unit.typeId ==
                    BWAPI::UnitTypes::Zerg_Hydralisk.getID() &&
                unit.completed
            )
            {
                state->hydraCompleted = true;
            }
        }

        state->burrowCompleted =
            self->hasResearched(BWAPI::TechTypes::Burrowing);

        state->muscularCompleted =
            self->getUpgradeLevel(
                BWAPI::UpgradeTypes::Muscular_Augments
            ) >= 1;

        if (
            state->hydraCompleted &&
            state->burrowCompleted &&
            state->muscularCompleted
        )
        {
            return;
        }

        if (obs.frame - state->lastDecisionFrame < 8)
        {
            return;
        }

        state->lastDecisionFrame = obs.frame;

        novabw::Action action;
        if (!bridge.requestAction(obs, action))
        {
            return;
        }

        const bool executed = adapter.execute(action);
        if (!executed)
        {
            return;
        }

        if (
            action.type == novabw::ActionType::Build &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Hydralisk_Den.getID()
        )
        {
            state->denBuildExecuted = true;
        }

        if (
            action.type == novabw::ActionType::Morph &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Hydralisk.getID()
        )
        {
            state->hydraMorphExecuted = true;
        }

        if (
            action.type == novabw::ActionType::Research &&
            action.techTypeId ==
                BWAPI::TechTypes::Burrowing.getID()
        )
        {
            state->researchExecuted = true;
        }

        if (
            action.type == novabw::ActionType::Upgrade &&
            action.upgradeTypeId ==
                BWAPI::UpgradeTypes::Muscular_Augments.getID()
        )
        {
            state->upgradeExecuted = true;
        }
    }

private:
    std::shared_ptr<NovaPythonHydraResearchState> state;
    novabw::OpenBWAdapter adapter;
    novabw::PythonBridge bridge;
};

TEST(NovaBW, PythonHydraResearchIntegration)
{
    auto state =
        std::make_shared<NovaPythonHydraResearchState>();

    BWTest test;
    test.map = Maps::GetOne("Python");
    test.myRace = BWAPI::Races::Zerg;
    test.opponentRace = BWAPI::Races::Terran;
    test.randomSeed = 12345;
    test.frameLimit = 30000;
    test.timeLimit = 90;
    test.expectWin = false;
    test.writeReplay = false;

    test.myModule = [state]()
    {
        return new NovaPythonHydraResearchModule(state);
    };

    test.onEndMine = [state](bool)
    {
        std::cout
            << "[NOVA-Z][PY-HYDRA] SUMMARY"
            << " connected=" << state->connected
            << " denBuild=" << state->denBuildExecuted
            << " denCompleted=" << state->denCompleted
            << " hydraMorph=" << state->hydraMorphExecuted
            << " hydraCompleted=" << state->hydraCompleted
            << " research=" << state->researchExecuted
            << " burrow=" << state->burrowCompleted
            << " upgrade=" << state->upgradeExecuted
            << " muscular=" << state->muscularCompleted
            << std::endl;

        EXPECT_TRUE(state->connected);
        EXPECT_TRUE(state->denBuildExecuted);
        EXPECT_TRUE(state->denCompleted);
        EXPECT_TRUE(state->hydraMorphExecuted);
        EXPECT_TRUE(state->hydraCompleted);
        EXPECT_TRUE(state->researchExecuted);
        EXPECT_TRUE(state->burrowCompleted);
        EXPECT_TRUE(state->upgradeExecuted);
        EXPECT_TRUE(state->muscularCompleted);
    };

    test.run();
}
'''
    test_path.write_text(tests + addition)
    print("[BOOTSTRAP] Hydra/Research C++ tests installed", flush=True)
else:
    print("[BOOTSTRAP] Hydra/Research C++ tests already present", flush=True)

runner = r'''#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "build" / "test"
BASE_ENV = os.environ.copy()
BASE_ENV["OPENBW_GAME_SPEED"] = "0"
BASE_ENV["OPENBW_ENABLE_UI"] = "0"

def run(cmd, cwd, env=None):
    print("\n+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env or BASE_ENV, check=True)

def run_gtest(name):
    run(["./tests", "--gtest_filter=" + name], TEST)

def run_python_test(server, test):
    log_dir = ROOT / "runs" / "hydra_research_bundle"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = open(log_dir / (Path(server).stem + ".log"), "w")
    proc = subprocess.Popen(
        [sys.executable, server],
        cwd=ROOT,
        env=os.environ.copy(),
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(1)
        run_gtest(test)
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
        log.close()

jobs = str(os.cpu_count() or 8)
run(["cmake", "--build", "build", "-j" + jobs], ROOT, os.environ.copy())

run_gtest("NovaBW.ZergGasToLairDeterministic")
run_gtest("NovaBW.ZergGasToLairThroughAdapter")
run_python_test("python/gas_lair_test_server.py", "NovaBW.PythonGasToLairIntegration")

run_gtest("NovaBW.ZergHydraResearchDeterministic")
run_gtest("NovaBW.ZergHydraResearchThroughAdapter")
run_python_test("python/hydra_research_test_server.py", "NovaBW.PythonHydraResearchIntegration")

print("\n====================================================")
print(" NOVA-Z HYDRA & RESEARCH v1: ALL TESTS PASSED")
print("====================================================")
'''
runner_path = ROOT / "scripts/test_novaz_hydra_bundle.py"
runner_path.parent.mkdir(parents=True, exist_ok=True)
runner_path.write_text(runner)
runner_path.chmod(0o755)

run([sys.executable, "scripts/test_novaz_hydra_bundle.py"])
