from map import Map
from heroes.hero import Hero
from heroes.hero_archetypes import hero_archetypes
import ui
from encounters.encounter_sael import EncounterSael
import random

def main():
    random.seed(420)  # For reproducibility in random actions
    map = Map(EncounterSael())
    heroes = [Hero(archetype) for archetype in hero_archetypes]

    game_ui = ui.GameUI(map, heroes)
    game_ui.run()

if __name__ == "__main__":
    main()