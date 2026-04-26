from map import Map
from heroes.hero import Hero
from heroes.hero_archetypes import hero_archetypes
from campaign import Campaign
import ui
import random

def main():
    #random.seed(421)  # For reproducibility in random actions
    
    # Create campaign and show encounter selection
    campaign = Campaign()
    encounter_class = campaign.show_encounter_select()
    
    # If user closed the window without selecting, exit
    if encounter_class is None:
        return
    
    # Create map with selected encounter
    map = Map(encounter_class())
    heroes = [Hero(archetype) for archetype in hero_archetypes]

    game_ui = ui.GameUI(map, heroes)
    map.ui = game_ui  # Store UI reference in map for card effects that need it
    game_ui.run()

if __name__ == "__main__":
    main()