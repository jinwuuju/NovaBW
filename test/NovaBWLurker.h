#pragma once

#include "NovaBW/OpenBWAdapter.h"
#include "NovaBW/PythonBridge.h"
#include "NovaBW/ScenarioHarness.h"

#include <BWAPI.h>

#include <iostream>
#include <limits>
#include <memory>
#include <string>

struct NovaZLurkerState
{
    bool poolIssued = false;
    bool poolCompleted = false;
    int poolBuilderId = -1;

    bool extractorIssued = false;
    bool extractorCompleted = false;
    int extractorBuilderId = -1;

    bool gasGatherIssued = false;
    int gasWorkerId = -1;

    bool lairIssued = false;
    bool lairCompleted = false;

    bool denIssued = false;
    bool denCompleted = false;
    int denBuilderId = -1;

    bool aspectIssued = false;
    bool aspectCompleted = false;

    bool hydraIssued = false;
    bool hydraCompleted = false;

    bool lurkerIssued = false;
    bool lurkerCompleted = false;

    bool passPrinted = false;
};


class NovaZLurkerModule : public BWAPI::AIModule
{
public:
    NovaZLurkerModule(
        std::shared_ptr<NovaZLurkerState> state,
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
            << "[NOVA-Z][LURKER]"
            << " mode="
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

        BWAPI::Unit extractor = nullptr;

        for (auto unit : self->getUnits())
        {
            if (!unit || !unit->exists())
            {
                continue;
            }

            const auto type = unit->getType();

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

            if (
                type == BWAPI::UnitTypes::Zerg_Lair &&
                unit->isCompleted()
            )
            {
                state->lairCompleted = true;
            }

            if (type == BWAPI::UnitTypes::Zerg_Hydralisk_Den)
            {
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

            if (
                type == BWAPI::UnitTypes::Zerg_Lurker &&
                unit->isCompleted()
            )
            {
                state->lurkerCompleted = true;
            }
        }

        state->aspectCompleted =
            self->hasResearched(
                BWAPI::TechTypes::Lurker_Aspect
            );

        if (state->lurkerCompleted)
        {
            if (!state->passPrinted)
            {
                state->passPrinted = true;

                std::cout
                    << "[NOVA-Z][LURKER][PASS-NO-LEAVE-v1]"
                    << " mode="
                    << (throughAdapter ? "adapter" : "direct")
                    << " frame="
                    << BWAPI::Broodwar->getFrameCount()
                    << std::endl;
            }

            return;
        }

        assignIdleMineralWorkers();

        const auto poolType =
            BWAPI::UnitTypes::Zerg_Spawning_Pool;

        const auto extractorType =
            BWAPI::UnitTypes::Zerg_Extractor;

        const auto lairType =
            BWAPI::UnitTypes::Zerg_Lair;

        const auto denType =
            BWAPI::UnitTypes::Zerg_Hydralisk_Den;

        const auto hydraType =
            BWAPI::UnitTypes::Zerg_Hydralisk;

        const auto lurkerType =
            BWAPI::UnitTypes::Zerg_Lurker;

        const auto aspect =
            BWAPI::TechTypes::Lurker_Aspect;

        const int mineralReserve =
            poolType.mineralPrice() +
            extractorType.mineralPrice() +
            lairType.mineralPrice() +
            denType.mineralPrice() +
            aspect.mineralPrice() +
            hydraType.mineralPrice() +
            lurkerType.mineralPrice() +
            125;

        if (
            !state->poolIssued &&
            self->minerals() >= mineralReserve
        )
        {
            int builderId = -1;

            if (
                startBuild(
                    poolType,
                    "zerg_spawning_pool",
                    builderId
                )
            )
            {
                state->poolIssued = true;
                state->poolBuilderId = builderId;

                std::cout
                    << "[NOVA-Z][LURKER] Pool accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->poolIssued &&
            !state->extractorIssued
        )
        {
            int builderId = -1;

            if (
                startBuild(
                    extractorType,
                    "zerg_extractor",
                    builderId
                )
            )
            {
                state->extractorIssued = true;
                state->extractorBuilderId = builderId;

                std::cout
                    << "[NOVA-Z][LURKER] Extractor accepted"
                    << std::endl;

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

            if (
                worker &&
                issueGather(worker, extractor)
            )
            {
                state->gasWorkerId =
                    worker->getID();

                state->gasGatherIssued = true;

                std::cout
                    << "[NOVA-Z][LURKER]"
                    << " gas worker="
                    << state->gasWorkerId
                    << std::endl;

                return;
            }
        }

        if (
            state->poolCompleted &&
            !state->lairIssued &&
            self->minerals() >=
                lairType.mineralPrice() &&
            self->gas() >=
                lairType.gasPrice()
        )
        {
            if (
                startMorph(
                    lairType,
                    "zerg_lair"
                )
            )
            {
                state->lairIssued = true;

                std::cout
                    << "[NOVA-Z][LURKER] Lair accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->lairCompleted &&
            !state->denIssued &&
            self->minerals() >=
                denType.mineralPrice() &&
            self->gas() >=
                denType.gasPrice()
        )
        {
            int builderId = -1;

            if (
                startBuild(
                    denType,
                    "zerg_hydralisk_den",
                    builderId
                )
            )
            {
                state->denIssued = true;
                state->denBuilderId = builderId;

                std::cout
                    << "[NOVA-Z][LURKER]"
                    << " Hydralisk Den accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->denCompleted &&
            !state->aspectIssued &&
            self->minerals() >=
                aspect.mineralPrice() &&
            self->gas() >=
                aspect.gasPrice()
        )
        {
            if (
                startResearch(
                    aspect,
                    "lurker_aspect"
                )
            )
            {
                state->aspectIssued = true;

                std::cout
                    << "[NOVA-Z][LURKER]"
                    << " Lurker Aspect accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->denCompleted &&
            state->aspectIssued &&
            !state->hydraIssued &&
            self->minerals() >=
                hydraType.mineralPrice() &&
            self->gas() >=
                hydraType.gasPrice()
        )
        {
            if (
                startMorph(
                    hydraType,
                    "zerg_hydralisk"
                )
            )
            {
                state->hydraIssued = true;

                std::cout
                    << "[NOVA-Z][LURKER]"
                    << " Hydralisk accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->aspectCompleted &&
            state->hydraCompleted &&
            !state->lurkerIssued &&
            self->minerals() >=
                lurkerType.mineralPrice() &&
            self->gas() >=
                lurkerType.gasPrice()
        )
        {
            if (
                startMorph(
                    lurkerType,
                    "zerg_lurker"
                )
            )
            {
                state->lurkerIssued = true;

                std::cout
                    << "[NOVA-Z][LURKER]"
                    << " Lurker accepted"
                    << std::endl;

                return;
            }
        }
    }

private:
    std::shared_ptr<NovaZLurkerState> state;
    bool throughAdapter = false;

    novabw::OpenBWAdapter adapter;

    bool reserved(int unitId) const
    {
        return
            unitId == state->poolBuilderId ||
            unitId == state->extractorBuilderId ||
            unitId == state->denBuilderId ||
            unitId == state->gasWorkerId;
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
                unit->getType() ==
                    BWAPI::UnitTypes::Zerg_Drone &&
                !reserved(unit->getID())
            )
            {
                return unit;
            }
        }

        return nullptr;
    }

    BWAPI::Unit firstLarvaProducer()
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
                unit->getType().producesLarva()
            )
            {
                return unit;
            }
        }

        return nullptr;
    }

    BWAPI::Unit nearestMineral(
        BWAPI::Unit worker
    )
    {
        BWAPI::Unit best = nullptr;

        long long bestDistance =
            std::numeric_limits<long long>::max();

        for (
            auto mineral :
            BWAPI::Broodwar->getMinerals()
        )
        {
            if (!mineral || !mineral->exists())
            {
                continue;
            }

            const auto a =
                worker->getPosition();

            const auto b =
                mineral->getPosition();

            const long long dx =
                static_cast<long long>(a.x - b.x);

            const long long dy =
                static_cast<long long>(a.y - b.y);

            const long long distance =
                dx * dx + dy * dy;

            if (distance < bestDistance)
            {
                bestDistance = distance;
                best = mineral;
            }
        }

        return best;
    }

    BWAPI::Unit nearestGeyser(
        BWAPI::Unit anchor
    )
    {
        if (!anchor)
        {
            return nullptr;
        }

        BWAPI::Unit best = nullptr;

        long long bestDistance =
            std::numeric_limits<long long>::max();

        for (
            auto geyser :
            BWAPI::Broodwar->getGeysers()
        )
        {
            if (!geyser || !geyser->exists())
            {
                continue;
            }

            const auto a =
                anchor->getPosition();

            const auto b =
                geyser->getPosition();

            const long long dx =
                static_cast<long long>(a.x - b.x);

            const long long dy =
                static_cast<long long>(a.y - b.y);

            const long long distance =
                dx * dx + dy * dy;

            if (distance < bestDistance)
            {
                bestDistance = distance;
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
                worker->getType() !=
                    BWAPI::UnitTypes::Zerg_Drone ||
                reserved(worker->getID()) ||
                !worker->isIdle()
            )
            {
                continue;
            }

            auto mineral =
                nearestMineral(worker);

            if (mineral)
            {
                issueGather(worker, mineral);
            }
        }
    }

    bool issueGather(
        BWAPI::Unit actor,
        BWAPI::Unit target
    )
    {
        if (!throughAdapter)
        {
            return actor->gather(target);
        }

        novabw::Action action;

        action.type =
            novabw::ActionType::Gather;

        action.unitId =
            actor->getID();

        action.targetUnitId =
            target->getID();

        return adapter.execute(action);
    }

    bool startBuild(
        BWAPI::UnitType type,
        const std::string &key,
        int &builderId
    )
    {
        if (throughAdapter)
        {
            const auto observation =
                adapter.observe();

            const auto *candidate =
                novabw::scenario::findBuildCandidate(
                    observation,
                    key
                );

            if (!candidate)
            {
                return false;
            }

            const auto action =
                novabw::scenario::makeBuildAction(
                    *candidate
                );

            if (!adapter.execute(action))
            {
                return false;
            }

            builderId =
                candidate->builderUnitId;

            return true;
        }

        auto builder = firstDrone();
        auto anchor = firstLarvaProducer();

        if (!builder || !anchor)
        {
            return false;
        }

        BWAPI::TilePosition tile =
            BWAPI::TilePositions::None;

        if (
            type ==
            BWAPI::UnitTypes::Zerg_Extractor
        )
        {
            auto geyser =
                nearestGeyser(anchor);

            if (!geyser)
            {
                return false;
            }

            tile =
                geyser->getTilePosition();
        }
        else
        {
            tile =
                BWAPI::Broodwar->getBuildLocation(
                    type,
                    anchor->getTilePosition(),
                    20
                );
        }

        if (
            tile == BWAPI::TilePositions::None ||
            !BWAPI::Broodwar->canBuildHere(
                tile,
                type,
                builder
            )
        )
        {
            return false;
        }

        if (!builder->build(type, tile))
        {
            return false;
        }

        builderId =
            builder->getID();

        return true;
    }

    bool startMorph(
        BWAPI::UnitType type,
        const std::string &key
    )
    {
        if (throughAdapter)
        {
            const auto observation =
                adapter.observe();

            const auto *option =
                novabw::scenario::findMorphOption(
                    observation,
                    key
                );

            if (!option)
            {
                return false;
            }

            return adapter.execute(
                novabw::scenario::makeMorphAction(
                    *option
                )
            );
        }

        auto self = BWAPI::Broodwar->self();

        for (auto unit : self->getUnits())
        {
            if (
                unit &&
                unit->exists() &&
                unit->isCompleted() &&
                unit->canMorph(type)
            )
            {
                return unit->morph(type);
            }
        }

        return false;
    }

    bool startResearch(
        BWAPI::TechType type,
        const std::string &key
    )
    {
        if (throughAdapter)
        {
            const auto observation =
                adapter.observe();

            const auto *option =
                novabw::scenario::findResearchOption(
                    observation,
                    key
                );

            if (!option)
            {
                return false;
            }

            return adapter.execute(
                novabw::scenario::makeResearchAction(
                    *option
                )
            );
        }

        auto self = BWAPI::Broodwar->self();

        for (auto unit : self->getUnits())
        {
            if (
                unit &&
                unit->exists() &&
                unit->isCompleted() &&
                unit->canResearch(type)
            )
            {
                return unit->research(type);
            }
        }

        return false;
    }
};


static void runNovaZLurkerTest(
    bool throughAdapter
)
{
    auto state =
        std::make_shared<NovaZLurkerState>();

    BWTest test;

    test.map =
        Maps::GetOne("Python");

    test.myRace =
        BWAPI::Races::Zerg;

    test.opponentRace =
        BWAPI::Races::Terran;

    test.randomSeed = 12345;

    test.frameLimit = 30000;
    test.timeLimit = 90;

    test.expectWin = false;
    test.writeReplay = false;

    test.myModule =
        [state, throughAdapter]()
    {
        return new NovaZLurkerModule(
            state,
            throughAdapter
        );
    };

    test.onEndMine = [state](bool)
    {
        std::cout
            << "[NOVA-Z][LURKER] SUMMARY"
            << " pool=" << state->poolCompleted
            << " extractor=" << state->extractorCompleted
            << " gas=" << state->gasGatherIssued
            << " lair=" << state->lairCompleted
            << " den=" << state->denCompleted
            << " aspect=" << state->aspectCompleted
            << " hydra=" << state->hydraCompleted
            << " lurker=" << state->lurkerCompleted
            << std::endl;

        EXPECT_TRUE(state->poolCompleted);
        EXPECT_TRUE(state->extractorCompleted);
        EXPECT_TRUE(state->gasGatherIssued);
        EXPECT_TRUE(state->lairCompleted);
        EXPECT_TRUE(state->denCompleted);
        EXPECT_TRUE(state->aspectIssued);
        EXPECT_TRUE(state->aspectCompleted);
        EXPECT_TRUE(state->hydraIssued);
        EXPECT_TRUE(state->hydraCompleted);
        EXPECT_TRUE(state->lurkerIssued);
        EXPECT_TRUE(state->lurkerCompleted);
    };

    test.run();
}


TEST(NovaBW, ZergLurkerDeterministic)
{
    runNovaZLurkerTest(false);
}


TEST(NovaBW, ZergLurkerThroughAdapter)
{
    runNovaZLurkerTest(true);
}


struct NovaPythonLurkerState
{
    bool connected = false;

    bool lairMorphExecuted = false;
    bool lairCompleted = false;

    bool denBuildExecuted = false;
    bool denCompleted = false;

    bool aspectResearchExecuted = false;
    bool aspectCompleted = false;

    bool hydraMorphExecuted = false;
    bool hydraCompleted = false;

    bool lurkerMorphExecuted = false;
    bool lurkerCompleted = false;

    int lastDecisionFrame = -999;
};


class NovaPythonLurkerModule :
    public BWAPI::AIModule
{
public:
    explicit NovaPythonLurkerModule(
        std::shared_ptr<NovaPythonLurkerState> state
    )
        : state(std::move(state))
    {
    }

    void onStart() override
    {
        BWAPI::Broodwar->setLocalSpeed(0);

        state->connected =
            bridge.connectToServer();

        std::cout
            << "[NOVA-Z][PY-LURKER]"
            << " connected="
            << state->connected
            << std::endl;
    }

    void onFrame() override
    {
        if (!state->connected)
        {
            return;
        }

        auto self =
            BWAPI::Broodwar->self();

        if (!self)
        {
            return;
        }

        const auto observation =
            adapter.observe();

        for (const auto &unit :
             observation.ownUnits)
        {
            if (
                unit.unitTypeKey == "zerg_lair" &&
                unit.completed
            )
            {
                state->lairCompleted = true;
            }

            if (
                unit.unitTypeKey == "zerg_hydralisk_den" &&
                unit.completed
            )
            {
                state->denCompleted = true;
            }

            if (
                unit.unitTypeKey == "zerg_hydralisk" &&
                unit.completed
            )
            {
                state->hydraCompleted = true;
            }

            if (
                unit.unitTypeKey == "zerg_lurker" &&
                unit.completed
            )
            {
                state->lurkerCompleted = true;
            }
        }

        state->aspectCompleted =
            self->hasResearched(
                BWAPI::TechTypes::Lurker_Aspect
            );

        if (state->lurkerCompleted)
        {
            return;
        }

        if (
            observation.frame -
            state->lastDecisionFrame <
            8
        )
        {
            return;
        }

        state->lastDecisionFrame =
            observation.frame;

        novabw::Action action;

        if (!bridge.requestAction(
                observation,
                action
            ))
        {
            return;
        }

        const bool executed =
            adapter.execute(action);

        if (!executed)
        {
            return;
        }

        if (
            action.type ==
                novabw::ActionType::Morph &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Lair.getID()
        )
        {
            state->lairMorphExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Build &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Hydralisk_Den.getID()
        )
        {
            state->denBuildExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Research &&
            action.techTypeId ==
                BWAPI::TechTypes::Lurker_Aspect.getID()
        )
        {
            state->aspectResearchExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Morph &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Hydralisk.getID()
        )
        {
            state->hydraMorphExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Morph &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Lurker.getID()
        )
        {
            state->lurkerMorphExecuted = true;
        }
    }

private:
    std::shared_ptr<NovaPythonLurkerState> state;

    novabw::OpenBWAdapter adapter;
    novabw::PythonBridge bridge;
};


TEST(NovaBW, PythonLurkerIntegration)
{
    auto state =
        std::make_shared<NovaPythonLurkerState>();

    BWTest test;

    test.map =
        Maps::GetOne("Python");

    test.myRace =
        BWAPI::Races::Zerg;

    test.opponentRace =
        BWAPI::Races::Terran;

    test.randomSeed = 12345;

    test.frameLimit = 30000;
    test.timeLimit = 90;

    test.expectWin = false;
    test.writeReplay = false;

    test.myModule = [state]()
    {
        return new NovaPythonLurkerModule(
            state
        );
    };

    test.onEndMine = [state](bool)
    {
        std::cout
            << "[NOVA-Z][PY-LURKER] SUMMARY"
            << " connected=" << state->connected
            << " lairMorph=" << state->lairMorphExecuted
            << " lair=" << state->lairCompleted
            << " denBuild=" << state->denBuildExecuted
            << " den=" << state->denCompleted
            << " aspectResearch=" << state->aspectResearchExecuted
            << " aspect=" << state->aspectCompleted
            << " hydraMorph=" << state->hydraMorphExecuted
            << " hydra=" << state->hydraCompleted
            << " lurkerMorph=" << state->lurkerMorphExecuted
            << " lurker=" << state->lurkerCompleted
            << std::endl;

        EXPECT_TRUE(state->connected);
        EXPECT_TRUE(state->lairMorphExecuted);
        EXPECT_TRUE(state->lairCompleted);
        EXPECT_TRUE(state->denBuildExecuted);
        EXPECT_TRUE(state->denCompleted);
        EXPECT_TRUE(state->aspectResearchExecuted);
        EXPECT_TRUE(state->aspectCompleted);
        EXPECT_TRUE(state->hydraMorphExecuted);
        EXPECT_TRUE(state->hydraCompleted);
        EXPECT_TRUE(state->lurkerMorphExecuted);
        EXPECT_TRUE(state->lurkerCompleted);
    };

    test.run();
}
