class Item:
    def __init__(self, id, name, slot, description):
        self.id = id
        self.name = name
        self.slot = slot        # 'head','neck','both_hands','off_hand','body','consumable'
        self.description = description

    def apply(self, hero, fight_map):
        """Called at fight start for each hero carrying this item. Register listeners, modify stats, add abilities."""
        pass

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slot': self.slot,
            'description': self.description,
        }
