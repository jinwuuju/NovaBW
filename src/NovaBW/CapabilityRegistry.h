#pragma once

#include "Protocol.h"

#include <BWAPI.h>

#include <algorithm>
#include <set>
#include <string>
#include <tuple>
#include <vector>

namespace novabw
{

enum class BuildPlacement
{
    NearLarvaProducer,
    Geyser
};

struct BuildCapability
{
    BWAPI::UnitType type;
    const char *key;
    BuildPlacement placement;
    int requiredCompletedTypeId;
    bool suppressWhenPresent;
};

struct MorphCapability
{
    BWAPI::UnitType type;
    const char *key;
};

struct ResearchCapability
{
    BWAPI::TechType type;
    const char *key;
};

struct UpgradeCapability
{
    BWAPI::UpgradeType type;
    const char *key;
};

inline const std::vector<BuildCapability> &buildCapabilities()
{
    static const std::vector<BuildCapability> values =
    {
        {
            BWAPI::UnitTypes::Zerg_Spawning_Pool,
            "zerg_spawning_pool",
            BuildPlacement::NearLarvaProducer,
            -1,
            true
        },
        {
            BWAPI::UnitTypes::Zerg_Extractor,
            "zerg_extractor",
            BuildPlacement::Geyser,
            -1,
            false
        },
        {
            BWAPI::UnitTypes::Zerg_Hydralisk_Den,
            "zerg_hydralisk_den",
            BuildPlacement::NearLarvaProducer,
            BWAPI::UnitTypes::Zerg_Spawning_Pool.getID(),
            true
        },
        {
            BWAPI::UnitTypes::Zerg_Spire,
            "zerg_spire",
            BuildPlacement::NearLarvaProducer,
            BWAPI::UnitTypes::Zerg_Lair.getID(),
            true
        }
    };

    return values;
}

inline const std::vector<MorphCapability> &morphCapabilities()
{
    static const std::vector<MorphCapability> values =
    {
        { BWAPI::UnitTypes::Zerg_Drone, "zerg_drone" },
        { BWAPI::UnitTypes::Zerg_Overlord, "zerg_overlord" },
        { BWAPI::UnitTypes::Zerg_Zergling, "zerg_zergling" },
        { BWAPI::UnitTypes::Zerg_Hydralisk, "zerg_hydralisk" },
        { BWAPI::UnitTypes::Zerg_Lair, "zerg_lair" },
        { BWAPI::UnitTypes::Zerg_Mutalisk, "zerg_mutalisk" },
        { BWAPI::UnitTypes::Zerg_Scourge, "zerg_scourge" }
    };

    return values;
}

inline const std::vector<ResearchCapability> &researchCapabilities()
{
    static const std::vector<ResearchCapability> values =
    {
        { BWAPI::TechTypes::Burrowing, "burrowing" }
    };

    return values;
}

inline const std::vector<UpgradeCapability> &upgradeCapabilities()
{
    static const std::vector<UpgradeCapability> values =
    {
        {
            BWAPI::UpgradeTypes::Muscular_Augments,
            "muscular_augments"
        },
        {
            BWAPI::UpgradeTypes::Grooved_Spines,
            "grooved_spines"
        },
        {
            BWAPI::UpgradeTypes::Zerg_Flyer_Attacks,
            "zerg_flyer_attacks"
        }
    };

    return values;
}

inline std::string capabilityUnitTypeKey(
    BWAPI::UnitType type
)
{
    if (type == BWAPI::UnitTypes::Zerg_Larva)
    {
        return "zerg_larva";
    }

    if (type == BWAPI::UnitTypes::Zerg_Hatchery)
    {
        return "zerg_hatchery";
    }

    for (const auto &capability : buildCapabilities())
    {
        if (type == capability.type)
        {
            return capability.key;
        }
    }

    for (const auto &capability : morphCapabilities())
    {
        if (type == capability.type)
        {
            return capability.key;
        }
    }

    return "";
}

inline bool isRegisteredBuild(
    BWAPI::UnitType type
)
{
    return std::any_of(
        buildCapabilities().begin(),
        buildCapabilities().end(),
        [type](const auto &capability)
        {
            return capability.type == type;
        }
    );
}

inline bool isRegisteredMorph(
    BWAPI::UnitType type
)
{
    return std::any_of(
        morphCapabilities().begin(),
        morphCapabilities().end(),
        [type](const auto &capability)
        {
            return capability.type == type;
        }
    );
}

inline bool isRegisteredResearch(
    BWAPI::TechType type
)
{
    return std::any_of(
        researchCapabilities().begin(),
        researchCapabilities().end(),
        [type](const auto &capability)
        {
            return capability.type == type;
        }
    );
}

inline bool isRegisteredUpgrade(
    BWAPI::UpgradeType type
)
{
    return std::any_of(
        upgradeCapabilities().begin(),
        upgradeCapabilities().end(),
        [type](const auto &capability)
        {
            return capability.type == type;
        }
    );
}

inline bool hasCompletedUnitType(
    BWAPI::Player self,
    int typeId
)
{
    if (!self || typeId < 0)
    {
        return true;
    }

    for (auto unit : self->getUnits())
    {
        if (
            unit &&
            unit->exists() &&
            unit->isCompleted() &&
            unit->getType().getID() == typeId
        )
        {
            return true;
        }
    }

    return false;
}

inline bool hasAnyUnitType(
    BWAPI::Player self,
    BWAPI::UnitType type
)
{
    if (!self)
    {
        return false;
    }

    for (auto unit : self->getUnits())
    {
        if (
            unit &&
            unit->exists() &&
            unit->getType() == type
        )
        {
            return true;
        }
    }

    return false;
}

inline BWAPI::Unit firstAvailableDrone(
    BWAPI::Player self
)
{
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
            !unit->isConstructing() &&
            !unit->isGatheringGas()
        )
        {
            return unit;
        }
    }

    return nullptr;
}

inline BWAPI::Unit firstCompletedLarvaProducer(
    BWAPI::Player self
)
{
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

inline BWAPI::Unit nearestAvailableGeyser(
    BWAPI::Unit anchor
)
{
    if (!anchor)
    {
        return nullptr;
    }

    BWAPI::Unit best = nullptr;
    long long bestDistance = -1;

    const auto anchorPosition =
        anchor->getPosition();

    for (auto geyser : BWAPI::Broodwar->getGeysers())
    {
        if (!geyser || !geyser->exists())
        {
            continue;
        }

        const auto geyserPosition =
            geyser->getPosition();

        const long long dx =
            static_cast<long long>(
                anchorPosition.x - geyserPosition.x
            );

        const long long dy =
            static_cast<long long>(
                anchorPosition.y - geyserPosition.y
            );

        const long long distance =
            dx * dx + dy * dy;

        if (
            bestDistance < 0 ||
            distance < bestDistance
        )
        {
            bestDistance = distance;
            best = geyser;
        }
    }

    return best;
}

inline void appendRegisteredBuildCandidates(
    Observation &observation
)
{
    auto self = BWAPI::Broodwar->self();

    if (!self)
    {
        return;
    }

    auto builder = firstAvailableDrone(self);
    auto anchor = firstCompletedLarvaProducer(self);

    if (!builder || !anchor)
    {
        return;
    }

    for (const auto &capability : buildCapabilities())
    {
        if (
            capability.suppressWhenPresent &&
            hasAnyUnitType(self, capability.type)
        )
        {
            continue;
        }

        if (
            !hasCompletedUnitType(
                self,
                capability.requiredCompletedTypeId
            )
        )
        {
            continue;
        }

        BWAPI::TilePosition tile =
            BWAPI::TilePositions::None;

        if (
            capability.placement ==
            BuildPlacement::Geyser
        )
        {
            auto geyser =
                nearestAvailableGeyser(anchor);

            if (!geyser)
            {
                continue;
            }

            tile = geyser->getTilePosition();
        }
        else
        {
            tile =
                BWAPI::Broodwar->getBuildLocation(
                    capability.type,
                    anchor->getTilePosition(),
                    20
                );
        }

        if (
            tile == BWAPI::TilePositions::None ||
            !BWAPI::Broodwar->canBuildHere(
                tile,
                capability.type,
                builder
            )
        )
        {
            continue;
        }

        BuildCandidateObservation candidate;

        candidate.builderUnitId =
            builder->getID();

        candidate.unitTypeId =
            capability.type.getID();

        candidate.unitTypeKey =
            capability.key;

        candidate.tileX = tile.x;
        candidate.tileY = tile.y;

        candidate.mineralCost =
            capability.type.mineralPrice();

        candidate.gasCost =
            capability.type.gasPrice();

        candidate.refinery =
            capability.type.isRefinery();

        observation.buildCandidates.push_back(
            candidate
        );
    }
}

inline void appendRegisteredMorphOptions(
    Observation &observation
)
{
    auto self = BWAPI::Broodwar->self();

    if (!self)
    {
        return;
    }

    for (auto unit : self->getUnits())
    {
        if (
            !unit ||
            !unit->exists() ||
            !unit->isCompleted()
        )
        {
            continue;
        }

        for (const auto &capability : morphCapabilities())
        {
            if (!unit->canMorph(capability.type))
            {
                continue;
            }

            MorphOptionObservation option;

            option.actorUnitId =
                unit->getID();

            option.unitTypeId =
                capability.type.getID();

            option.unitTypeKey =
                capability.key;

            option.mineralCost =
                capability.type.mineralPrice();

            option.gasCost =
                capability.type.gasPrice();

            option.worker =
                capability.type.isWorker();

            option.supplyProvider =
                capability.type.supplyProvided() > 0;

            option.canAttack =
                capability.type.canAttack();

            option.building =
                capability.type.isBuilding();

            option.producesLarva =
                capability.type.producesLarva();

            observation.morphOptions.push_back(
                option
            );
        }
    }
}

inline void appendRegisteredResearchOptions(
    Observation &observation
)
{
    auto self = BWAPI::Broodwar->self();

    if (!self)
    {
        return;
    }

    for (auto unit : self->getUnits())
    {
        if (
            !unit ||
            !unit->exists() ||
            !unit->isCompleted()
        )
        {
            continue;
        }

        for (const auto &capability : researchCapabilities())
        {
            if (!unit->canResearch(capability.type))
            {
                continue;
            }

            ResearchOptionObservation option;

            option.actorUnitId =
                unit->getID();

            option.techTypeId =
                capability.type.getID();

            option.techKey =
                capability.key;

            option.mineralCost =
                capability.type.mineralPrice();

            option.gasCost =
                capability.type.gasPrice();

            observation.researchOptions.push_back(
                option
            );
        }
    }
}

inline void appendRegisteredUpgradeOptions(
    Observation &observation
)
{
    auto self = BWAPI::Broodwar->self();

    if (!self)
    {
        return;
    }

    for (auto unit : self->getUnits())
    {
        if (
            !unit ||
            !unit->exists() ||
            !unit->isCompleted()
        )
        {
            continue;
        }

        for (const auto &capability : upgradeCapabilities())
        {
            if (!unit->canUpgrade(capability.type))
            {
                continue;
            }

            UpgradeOptionObservation option;

            option.actorUnitId =
                unit->getID();

            option.upgradeTypeId =
                capability.type.getID();

            option.upgradeKey =
                capability.key;

            option.currentLevel =
                self->getUpgradeLevel(
                    capability.type
                );

            option.nextLevel =
                option.currentLevel + 1;

            option.mineralCost =
                capability.type.mineralPrice(
                    option.nextLevel
                );

            option.gasCost =
                capability.type.gasPrice(
                    option.nextLevel
                );

            observation.upgradeOptions.push_back(
                option
            );
        }
    }
}

inline void deduplicateRegisteredCandidates(
    Observation &observation
)
{
    {
        std::set<
            std::tuple<int, std::string, int, int>
        > seen;

        auto &values =
            observation.buildCandidates;

        values.erase(
            std::remove_if(
                values.begin(),
                values.end(),
                [&seen](const auto &value)
                {
                    return !seen.emplace(
                        value.builderUnitId,
                        value.unitTypeKey,
                        value.tileX,
                        value.tileY
                    ).second;
                }
            ),
            values.end()
        );
    }

    {
        std::set<
            std::tuple<int, std::string>
        > seen;

        auto &values =
            observation.morphOptions;

        values.erase(
            std::remove_if(
                values.begin(),
                values.end(),
                [&seen](const auto &value)
                {
                    return !seen.emplace(
                        value.actorUnitId,
                        value.unitTypeKey
                    ).second;
                }
            ),
            values.end()
        );
    }

    {
        std::set<
            std::tuple<int, std::string>
        > seen;

        auto &values =
            observation.researchOptions;

        values.erase(
            std::remove_if(
                values.begin(),
                values.end(),
                [&seen](const auto &value)
                {
                    return !seen.emplace(
                        value.actorUnitId,
                        value.techKey
                    ).second;
                }
            ),
            values.end()
        );
    }

    {
        std::set<
            std::tuple<int, std::string, int>
        > seen;

        auto &values =
            observation.upgradeOptions;

        values.erase(
            std::remove_if(
                values.begin(),
                values.end(),
                [&seen](const auto &value)
                {
                    return !seen.emplace(
                        value.actorUnitId,
                        value.upgradeKey,
                        value.nextLevel
                    ).second;
                }
            ),
            values.end()
        );
    }
}

inline void appendRegisteredCandidates(
    Observation &observation
)
{
    appendRegisteredBuildCandidates(observation);
    appendRegisteredMorphOptions(observation);
    appendRegisteredResearchOptions(observation);
    appendRegisteredUpgradeOptions(observation);
    deduplicateRegisteredCandidates(observation);
}

} // namespace novabw
