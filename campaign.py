import tkinter as tk
from encounters.encounter_sael import EncounterSael
from encounters.encounter_como import EncounterComo
from encounters.encounter_across import EncounterAcross

# Define available encounters
ENCOUNTERS = {
    "Sa'el, Frozen Queen": {
        "class": EncounterSael,
        "description": ""
    },
    "Comorragh, Hellfire Prince": {
        "class": EncounterComo,
        "description": ""
    },
    "Across the Wall": {
        "class": EncounterAcross,
        "description": ""
    }
}

class Campaign:
    """Manages campaign progression, items, and encounter selection."""
    
    def __init__(self):
        self.completed_encounters = []
        self.items = []  # Future: track items earned from encounters
        self.hero_upgrades = {}  # Future: track hero-specific upgrades
    
    def show_encounter_select(self):
        """Display encounter selection screen and return the chosen encounter class."""
        selected_encounter = [None]  # Use list to allow modification in nested function
        
        root = tk.Tk()
        root.title("Tableraid - Select Encounter")
        root.geometry("600x500")
        root.configure(bg="#2b2b2b")
        
        # Title
        title = tk.Label(root, text="Select Encounter", font=("Arial", 24, "bold"), 
                         bg="#2b2b2b", fg="#ffffff")
        title.pack(pady=20)
        
        def start_encounter(encounter_class):
            selected_encounter[0] = encounter_class
            root.destroy()
        
        # Create buttons for each encounter
        for encounter_name, encounter_info in ENCOUNTERS.items():
            frame = tk.Frame(root, bg="#3b3b3b", relief=tk.RAISED, borderwidth=2)
            frame.pack(pady=10, padx=40, fill=tk.X)
            
            name_label = tk.Label(frame, text=encounter_name, font=("Arial", 16, "bold"),
                                 bg="#3b3b3b", fg="#ffcc00")
            name_label.pack(pady=(10, 5))
            
            desc_label = tk.Label(frame, text=encounter_info["description"], 
                                 font=("Arial", 11), bg="#3b3b3b", fg="#cccccc",
                                 wraplength=500, justify=tk.LEFT)
            desc_label.pack(pady=(0, 10), padx=20)
            
            start_btn = tk.Button(frame, text="Start", font=("Arial", 12, "bold"),
                                 bg="#4CAF50", fg="white", activebackground="#45a049",
                                 command=lambda ec=encounter_info["class"]: start_encounter(ec))
            start_btn.pack(pady=(0, 10))
        
        root.mainloop()
        return selected_encounter[0]
    
    def complete_encounter(self, encounter_name, victory=True):
        """Record encounter completion. Future: award items/upgrades."""
        self.completed_encounters.append({
            "name": encounter_name,
            "victory": victory
        })
        # Future: Add item rewards, hero upgrades, etc.
    
    def get_available_items(self):
        """Future: Return items available to equip."""
        return self.items
    
    def add_item(self, item):
        """Future: Add an item to the campaign inventory."""
        self.items.append(item)
