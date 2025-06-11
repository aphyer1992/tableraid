class EncounterBase:
    def get_name(self) -> str:
        """Returns the unique identifier for the encounter."""
        return self.name
    
    def get_deployment_zone(self):
        assert(False), "EncounterBase.get_deployment_zone() must be overridden in the subclass"

    def setup_map(self, map):
        assert(False), "EncounterBase.setup_map() must be overridden in the subclass"

    def get_map_dimensions(self):
        return(11, 11)  # Default dimensions, can be overridden