#pragma once

#include "NovaBW/OpenBWAdapter.h"
#include "NovaBW/PythonBridge.h"
#include "NovaBW/ScenarioHarness.h"

#include <BWAPI.h>

#include <iostream>
#include <limits>
#include <memory>
#include <string>

struct NovaZSpireAirState
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

    bool spireIssued = false;
    bool spireCompleted = false;
    int spireBuilderId = -1;

    bool mutaIssued = false;
    bool mutaCompleted = false;

    bool scourgeIssued = false;
    bool scourgeCompleted = false;

    bool flyerUpgradeIssued = false;
    bool flyerUpgradeCompleted = false;

    bool passPrinted = false;
};


class NovaZSpireAirModule : public BWAPI::AIModule
{
public:
    NovaZSpireAirModule(
        std::shared_ptr<NovaZSpireAirState> state,
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
            << "[NOVA-Z][SPIRE]"
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

            if (type == BWAPI::UnitTypes::Zerg_Lair)
            {
                if (unit->isCompleted())
                {
                    state->lairCompleted = true;
                }
            }

            if (type == BWAPI::UnitTypes::Zerg_Spire)
            {
                state->spireBuilderId = -1;

                if (unit->isCompleted())
                {
                    state->spireCompleted = true;
                }
            }

            if (
                type == BWAPI::UnitTypes::Zerg_Mutalisk &&
                unit->isCompleted()
            )
            {
                state->mutaCompleted = true;
            }

            if (
                type == BWAPI::UnitTypes::Zerg_Scourge &&
                unit->isCompleted()
            )
            {
                state->scourgeCompleted = true;
            }
        }

        state->flyerUpgradeCompleted =
            self->getUpgradeLevel(
                BWAPI::UpgradeTypes::Zerg_Flyer_Attacks
            ) >= 1;

        if (
            state->mutaCompleted &&
            state->scourgeCompleted &&
            state->flyerUpgradeCompleted
        )
        {
            if (!state->passPrinted)
            {
                state->passPrinted = true;

                std::cout
                    << "[NOVA-Z][SPIRE][PASS]"
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

        const auto spireType =
            BWAPI::UnitTypes::Zerg_Spire;

        const auto mutaType =
            BWAPI::UnitTypes::Zerg_Mutalisk;

        const auto scourgeType =
            BWAPI::UnitTypes::Zerg_Scourge;

        const auto flyerUpgrade =
            BWAPI::UpgradeTypes::Zerg_Flyer_Attacks;

        const int mineralReserve =
            poolType.mineralPrice() +
            extractorType.mineralPrice() +
            lairType.mineralPrice() +
            spireType.mineralPrice() +
            mutaType.mineralPrice() +
            scourgeType.mineralPrice() +
            flyerUpgrade.mineralPrice(1) +
            100;

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
                    << "[NOVA-Z][SPIRE] Pool accepted"
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
                    << "[NOVA-Z][SPIRE] Extractor accepted"
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
                    << "[NOVA-Z][SPIRE]"
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
                    << "[NOVA-Z][SPIRE] Lair accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->lairCompleted &&
            !state->spireIssued &&
            self->minerals() >=
                spireType.mineralPrice() &&
            self->gas() >=
                spireType.gasPrice()
        )
        {
            int builderId = -1;

            if (
                startBuild(
                    spireType,
                    "zerg_spire",
                    builderId
                )
            )
            {
                state->spireIssued = true;
                state->spireBuilderId = builderId;

                std::cout
                    << "[NOVA-Z][SPIRE] Spire accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->spireCompleted &&
            !state->mutaIssued &&
            self->minerals() >=
                mutaType.mineralPrice() &&
            self->gas() >=
                mutaType.gasPrice()
        )
        {
            if (
                startMorph(
                    mutaType,
                    "zerg_mutalisk"
                )
            )
            {
                state->mutaIssued = true;

                std::cout
                    << "[NOVA-Z][SPIRE] Mutalisk accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->mutaCompleted &&
            !state->scourgeIssued &&
            self->minerals() >=
                scourgeType.mineralPrice() &&
            self->gas() >=
                scourgeType.gasPrice()
        )
        {
            if (
                startMorph(
                    scourgeType,
                    "zerg_scourge"
                )
            )
            {
                state->scourgeIssued = true;

                std::cout
                    << "[NOVA-Z][SPIRE] Scourge accepted"
                    << std::endl;

                return;
            }
        }

        if (
            state->scourgeCompleted &&
            !state->flyerUpgradeIssued &&
            self->minerals() >=
                flyerUpgrade.mineralPrice(1) &&
            self->gas() >=
                flyerUpgrade.gasPrice(1)
        )
        {
            if (
                startUpgrade(
                    flyerUpgrade,
                    "zerg_flyer_attacks"
                )
            )
            {
                state->flyerUpgradeIssued = true;

                std::cout
                    << "[NOVA-Z][SPIRE]"
                    << " Zerg Flyer Attacks accepted"
                    << std::endl;

                return;
            }
        }
    }

private:
    std::shared_ptr<NovaZSpireAirState> state;
    bool throughAdapter = false;

    novabw::OpenBWAdapter adapter;

    bool reserved(int unitId) const
    {
        return
            unitId == state->poolBuilderId ||
            unitId == state->extractorBuilderId ||
            unitId == state->spireBuilderId ||
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

            auto action =
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

        builderId = builder->getID();

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

    bool startUpgrade(
        BWAPI::UpgradeType type,
        const std::string &key
    )
    {
        if (throughAdapter)
        {
            const auto observation =
                adapter.observe();

            const auto *option =
                novabw::scenario::findUpgradeOption(
                    observation,
                    key
                );

            if (!option)
            {
                return false;
            }

            return adapter.execute(
                novabw::scenario::makeUpgradeAction(
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
                unit->canUpgrade(type)
            )
            {
                return unit->upgrade(type);
            }
        }

        return false;
    }
};


static void runNovaZSpireAirTest(
    bool throughAdapter
)
{
    auto state =
        std::make_shared<NovaZSpireAirState>();

    BWTest test;

    test.map =
        Maps::GetOne("Python");

    test.myRace =
        BWAPI::Races::Zerg;

    test.opponentRace =
        BWAPI::Races::Terran;

    test.randomSeed = 12345;

    test.frameLimit = 24000;
    test.timeLimit = 90;

    test.expectWin = false;
    test.writeReplay = false;

    test.myModule =
        [state, throughAdapter]()
    {
        return new NovaZSpireAirModule(
            state,
            throughAdapter
        );
    };

    test.onEndMine = [state](bool)
    {
        std::cout
            << "[NOVA-Z][SPIRE] SUMMARY"
            << " pool=" << state->poolCompleted
            << " extractor=" << state->extractorCompleted
            << " gas=" << state->gasGatherIssued
            << " lair=" << state->lairCompleted
            << " spire=" << state->spireCompleted
            << " muta=" << state->mutaCompleted
            << " scourge=" << state->scourgeCompleted
            << " flyerUpgrade="
            << state->flyerUpgradeCompleted
            << std::endl;

        EXPECT_TRUE(state->poolCompleted);
        EXPECT_TRUE(state->extractorCompleted);
        EXPECT_TRUE(state->gasGatherIssued);
        EXPECT_TRUE(state->lairCompleted);
        EXPECT_TRUE(state->spireCompleted);
        EXPECT_TRUE(state->mutaCompleted);
        EXPECT_TRUE(state->scourgeCompleted);
        EXPECT_TRUE(state->flyerUpgradeIssued);
        EXPECT_TRUE(state->flyerUpgradeCompleted);
    };

    test.run();
}


TEST(NovaBW, ZergSpireAirDeterministic)
{
    runNovaZSpireAirTest(false);
}


TEST(NovaBW, ZergSpireAirThroughAdapter)
{
    runNovaZSpireAirTest(true);
}


struct NovaPythonSpireAirState
{
    bool connected = false;

    bool spireBuildExecuted = false;
    bool spireCompleted = false;

    bool mutaMorphExecuted = false;
    bool mutaCompleted = false;

    bool scourgeMorphExecuted = false;
    bool scourgeCompleted = false;

    bool flyerUpgradeExecuted = false;
    bool flyerUpgradeCompleted = false;

    int lastDecisionFrame = -999;
};


class NovaPythonSpireAirModule :
    public BWAPI::AIModule
{
public:
    explicit NovaPythonSpireAirModule(
        std::shared_ptr<NovaPythonSpireAirState> state
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
            << "[NOVA-Z][PY-SPIRE]"
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

        auto self = BWAPI::Broodwar->self();

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
                unit.unitTypeKey ==
                    "zerg_spire" &&
                unit.completed
            )
            {
                state->spireCompleted = true;
            }

            if (
                unit.unitTypeKey ==
                    "zerg_mutalisk" &&
                unit.completed
            )
            {
                state->mutaCompleted = true;
            }

            if (
                unit.unitTypeKey ==
                    "zerg_scourge" &&
                unit.completed
            )
            {
                state->scourgeCompleted = true;
            }
        }

        state->flyerUpgradeCompleted =
            self->getUpgradeLevel(
                BWAPI::UpgradeTypes::Zerg_Flyer_Attacks
            ) >= 1;

        if (
            state->mutaCompleted &&
            state->scourgeCompleted &&
            state->flyerUpgradeCompleted
        )
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
                novabw::ActionType::Build &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Spire.getID()
        )
        {
            state->spireBuildExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Morph &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Mutalisk.getID()
        )
        {
            state->mutaMorphExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Morph &&
            action.unitTypeId ==
                BWAPI::UnitTypes::Zerg_Scourge.getID()
        )
        {
            state->scourgeMorphExecuted = true;
        }

        if (
            action.type ==
                novabw::ActionType::Upgrade &&
            action.upgradeTypeId ==
                BWAPI::UpgradeTypes::Zerg_Flyer_Attacks.getID()
        )
        {
            state->flyerUpgradeExecuted = true;
        }
    }

private:
    std::shared_ptr<NovaPythonSpireAirState> state;

    novabw::OpenBWAdapter adapter;
    novabw::PythonBridge bridge;
};


TEST(NovaBW, PythonSpireAirIntegration)
{
    auto state =
        std::make_shared<NovaPythonSpireAirState>();

    BWTest test;

    test.map =
        Maps::GetOne("Python");

    test.myRace =
        BWAPI::Races::Zerg;

    test.opponentRace =
        BWAPI::Races::Terran;

    test.randomSeed = 12345;

    test.frameLimit = 24000;
    test.timeLimit = 90;

    test.expectWin = false;
    test.writeReplay = false;

    test.myModule = [state]()
    {
        return new NovaPythonSpireAirModule(
            state
        );
    };

    test.onEndMine = [state](bool)
    {
        std::cout
            << "[NOVA-Z][PY-SPIRE] SUMMARY"
            << " connected=" << state->connected
            << " spireBuild=" << state->spireBuildExecuted
            << " spire=" << state->spireCompleted
            << " mutaMorph=" << state->mutaMorphExecuted
            << " muta=" << state->mutaCompleted
            << " scourgeMorph=" << state->scourgeMorphExecuted
            << " scourge=" << state->scourgeCompleted
            << " upgrade=" << state->flyerUpgradeExecuted
            << " flyerAttack=" << state->flyerUpgradeCompleted
            << std::endl;

        EXPECT_TRUE(state->connected);
        EXPECT_TRUE(state->spireBuildExecuted);
        EXPECT_TRUE(state->spireCompleted);
        EXPECT_TRUE(state->mutaMorphExecuted);
        EXPECT_TRUE(state->mutaCompleted);
        EXPECT_TRUE(state->scourgeMorphExecuted);
        EXPECT_TRUE(state->scourgeCompleted);
        EXPECT_TRUE(state->flyerUpgradeExecuted);
        EXPECT_TRUE(state->flyerUpgradeCompleted);
    };

    test.run();
}
