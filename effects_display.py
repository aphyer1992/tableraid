# effects_display.py (or in your Figure class/module)
EFFECTS_DISPLAY = {
    "Burn": {
        "icon": "🔥",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
    },
    "Bleed": {
        "icon" : "🩸",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
    },
    "shield_counters": {
        "icon": "🛡️",
        "position": "left",
        "show_quantity": False,
        "is_condition": False,  
    },
    "Stunned": {
        "icon": "⏳",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
    },
    "Slowed": {
        "icon": "❄️",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
    },
    "Regen": {
        "icon": "🌱",      # Unicode or path to image
        "position": "left",
        "show_quantity": True,
        "is_condition": True,  
    },
    "combo_points": {
        "icon": "⚡",      # Unicode or path to image
        "position": "left",
        "show_quantity": False,
        "is_condition": False,  
    },
}