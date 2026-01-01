class EncounterBase:
    def __init__(self):
        self.name = "Base Encounter"
        self.map = None  # Will be set as we join to a map object

    def get_name(self) -> str:
        """Returns the unique identifier for the encounter."""
        return self.name
    
    def get_boss_display_info(self):
        """
        Returns a list of display items for the boss panel.
        Each item is a dict with 'name' and 'text' keys.
        Default implementation shows only the next card.
        """
        if hasattr(self, 'next_card'):
            return [self.next_card]
        return []
    
    def get_deployment_zone(self):
        assert(False), "EncounterBase.get_deployment_zone() must be overridden in the subclass"

    def setup_map(self, map):
        assert(False), "EncounterBase.setup_map() must be overridden in the subclass"

    def get_map_dimensions(self):
        return(11, 11)  # Default dimensions, can be overridden