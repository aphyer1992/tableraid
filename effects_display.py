# effects_display.py (or in your Figure class/module)
EFFECTS_DISPLAY = {
    "Burn": {
        "icon": "🔥",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#ff4500",  # Optional color for display
    },
    "Bleed": {
        "icon" : "🩸",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#8b0000",  # Optional color for display
    },
    "shield_counters": {
        "icon": "🛡️",
        "position": "left",
        "show_quantity": False,
        "is_condition": False,  
        "color" : "#4682b4",  # Optional color for display
    },
    "Stunned": {
        "icon": "⏳",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#ff4500",  # Optional color for display
    },
    "Slowed": {
        "icon": "❄️",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#1e90ff",  # Optional color for display
    },
    "Regen": {
        "icon": "🌱",      # Unicode or path to image
        "position": "left",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#32cd32",  # Optional color for display
    },
    "combo_points": {
        "icon": "⚡",      # Unicode or path to image
        "position": "left",
        "show_quantity": False,
        "is_condition": False,  
        "color" : "#ffd700",  # Optional color for display
    },
}