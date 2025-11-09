from enum import Enum
class TargetingContext(Enum):
    ENEMY_TARGETABLE = "enemy_targetable"
    ALLY_TARGETABLE = "ally_targetable"
    AOE_ABILITY_HITTABLE = "aoe_ability_hittable"
    TARGETING_PRIORITY = "targeting_priority"
    RENDERING_PRIORITY = "rendering_priority"

default_targeting_parameters = {
    TargetingContext.ENEMY_TARGETABLE: True,
    TargetingContext.ALLY_TARGETABLE: True,
    TargetingContext.AOE_ABILITY_HITTABLE: True,
    TargetingContext.TARGETING_PRIORITY: 0,
    TargetingContext.RENDERING_PRIORITY: 0,
}

marker_targeting_parameters = {
    TargetingContext.ENEMY_TARGETABLE: False,
    TargetingContext.ALLY_TARGETABLE: False,
    TargetingContext.AOE_ABILITY_HITTABLE: False,
    TargetingContext.TARGETING_PRIORITY: None,
    TargetingContext.RENDERING_PRIORITY: -1,
}