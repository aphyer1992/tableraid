# effects_display.py (or in your Figure class/module)
from game_conditions import Condition

EFFECTS_DISPLAY = {
    Condition.BURN.value: {
        "icon": "🔥",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#ff4500",  # Optional color for display
    },
    Condition.BLEED.value: {
        "icon" : "🩸",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#8b0000",  # Optional color for display
    },
    Condition.SHIELDED.value: {
        "icon": "🛡️",
        "position": "left",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#4682b4",  # Optional color for display
    },
    Condition.STUNNED.value: {
        "icon": "⏳",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#ff4500",  # Optional color for display
    },
    Condition.SLOWED.value: {
        "icon": "❄️",      # Unicode or path to image
        "position": "right",
        "show_quantity": True,
        "is_condition": True,  
        "color" : "#1e90ff",  # Optional color for display
    },
    Condition.REGEN.value: {
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