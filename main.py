from map import Map
from heroes.hero import Hero
from heroes.hero_archetypes import hero_archetypes
import ui
from encounters.encounter_sael import EncounterSael
from encounters.encounter_como import EncounterComo
import random

def main():
    #random.seed(421)  # For reproducibility in random actions
    map = Map(EncounterComo())
    heroes = [Hero(archetype) for archetype in hero_archetypes]

    game_ui = ui.GameUI(map, heroes)
    map.ui = game_ui  # Store UI reference in map for card effects that need it
    game_ui.run()

if __name__ == "__main__":
    main()