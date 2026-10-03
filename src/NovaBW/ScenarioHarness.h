#pragma once

#include "Protocol.h"

#include <string>

namespace novabw
{
namespace scenario
{

inline const UnitObservation *findOwnUnit(
    const Observation &observation,
    const std::string &unitTypeKey,
    bool completedOnly = false
)
{
    for (const auto &unit : observation.ownUnits)
    {
        if (
            unit.unitTypeKey == unitTypeKey &&
            (!completedOnly || unit.completed)
        )
        {
            return &unit;
        }
    }

    return nullptr;
}

inline const BuildCandidateObservation *findBuildCandidate(
    const Observation &observation,
    const std::string &unitTypeKey
)
{
    for (const auto &candidate : observation.buildCandidates)
    {
        if (candidate.unitTypeKey == unitTypeKey)
        {
            return &candidate;
        }
    }

    return nullptr;
}

inline const MorphOptionObservation *findMorphOption(
    const Observation &observation,
    const std::string &unitTypeKey
)
{
    for (const auto &option : observation.morphOptions)
    {
        if (option.unitTypeKey == unitTypeKey)
        {
            return &option;
        }
    }

    return nullptr;
}

inline const ResearchOptionObservation *findResearchOption(
    const Observation &observation,
    const std::string &techKey
)
{
    for (const auto &option : observation.researchOptions)
    {
        if (option.techKey == techKey)
        {
            return &option;
        }
    }

    return nullptr;
}

inline const UpgradeOptionObservation *findUpgradeOption(
    const Observation &observation,
    const std::string &upgradeKey
)
{
    for (const auto &option : observation.upgradeOptions)
    {
        if (option.upgradeKey == upgradeKey)
        {
            return &option;
        }
    }

    return nullptr;
}

inline Action makeBuildAction(
    const BuildCandidateObservation &candidate
)
{
    Action action;

    action.type = ActionType::Build;
    action.unitId = candidate.builderUnitId;
    action.unitTypeId = candidate.unitTypeId;
    action.targetTileX = candidate.tileX;
    action.targetTileY = candidate.tileY;

    return action;
}

inline Action makeMorphAction(
    const MorphOptionObservation &option
)
{
    Action action;

    action.type = ActionType::Morph;
    action.unitId = option.actorUnitId;
    action.unitTypeId = option.unitTypeId;

    return action;
}

inline Action makeResearchAction(
    const ResearchOptionObservation &option
)
{
    Action action;

    action.type = ActionType::Research;
    action.unitId = option.actorUnitId;
    action.techTypeId = option.techTypeId;

    return action;
}

inline Action makeUpgradeAction(
    const UpgradeOptionObservation &option
)
{
    Action action;

    action.type = ActionType::Upgrade;
    action.unitId = option.actorUnitId;
    action.upgradeTypeId = option.upgradeTypeId;

    return action;
}

} // namespace scenario
} // namespace novabw
