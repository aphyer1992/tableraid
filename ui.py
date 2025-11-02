import tkinter as tk
from figure import FigureType
from coords import Coords
from effects_display import EFFECTS_DISPLAY

class GameUI:
    def __init__(self, map, heroes):
        self.map = map
        self.heroes = heroes
        self.root = tk.Tk()
        self.root.title("Tableraid")
        self.left_panel = tk.Frame(self.root)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.map_panel = tk.Frame(self.root)
        self.map_panel.pack(side=tk.LEFT, padx=20, pady=20)
        self.right_panel = tk.Frame(self.root, width=200, bg="#e0e0e0")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.hero_rows = []
        self.placement_queue = [hero for hero in heroes]
        self.placing = True

        # used to prompt for hero actions
        self.select_mode = None
        self.valid_choices = []
        self.select_color = None
        self.select_cmd = None

        self.setup_placement()
        self.draw_everything()
        self.update_placement_label()

    def setup_placement(self):
        self.select_mode = 'hero_placement'
        self.valid_choices = [Coords(x, y) for y in range(self.map.height - 2, self.map.height) for x in range(self.map.width)]
        self.select_color = "lightblue"
        self.select_cmd = lambda coords: self.place_hero(coords.x, coords.y)

    def update_placement_label(self):
        if hasattr(self, "placement_label"):
            self.placement_label.destroy()
        if self.placement_queue:
            hero = self.placement_queue[0]
            self.placement_label = tk.Label(self.left_panel, text=f"Place {hero.name}")
            self.placement_label.pack()
        else:
            self.placement_label = tk.Label(self.left_panel, text="All heroes placed!")
            self.placement_label.pack()

    def place_hero(self, x, y):
        hero = self.placement_queue.pop(0)
        self.map.add_figure(hero.figure, Coords(x, y))
        if self.placement_queue:
            self.valid_choices.remove(Coords(x, y))  # Remove the placed hero's position from valid choices
            self.update_placement_label()
            self.draw_map()
        else:
            self.select_mode = None
            self.placement_label.destroy()
            self.draw_hero_panel()
            self.draw_map()

    def draw_hero_panel(self):
        # Clear previous
        for widget in self.left_panel.winfo_children():
            widget.destroy()

        hero_figures = self.map.get_figures_by_type(FigureType.HERO)
        for hero_figure in hero_figures:
            hero = hero_figure.hero
            frame = tk.Frame(self.left_panel, borderwidth=2, relief="groove", padx=2, pady=2)
            frame.pack(fill=tk.X, pady=4)

            # Add hero name label
            name_label = tk.Label(frame, text=hero.name, width=12, anchor="w")
            name_label.pack(side=tk.LEFT, padx=2)
            # Add hero health label and
            health_label = tk.Label(frame, text=f"HP {hero_figure.current_health}/{hero_figure.max_health}", width=6, anchor="w")
            health_label.pack(side=tk.LEFT, padx=2)
            # Add hero energy label
            energy_label = tk.Label(frame, text=f"Energy {hero.current_energy}", width=8, anchor="w")
            energy_label.pack(side=tk.LEFT, padx=2)

            # Top row: Activate, Move, Attack
            top_row = tk.Frame(frame)
            top_row.pack(fill=tk.X)
            btn_activate = tk.Button(
                top_row, text="Activate",
                command=lambda h=hero: self.activate_hero(h),
                state=tk.NORMAL if not hero.activated else tk.DISABLED,
                width=8
            )
            btn_activate.pack(side=tk.LEFT, padx=1)
            btn_move = tk.Button(
                top_row, text="Move",
                command=lambda h=hero: self.hero_basic_move_action(h),
                state=tk.NORMAL if hero.move_available else tk.DISABLED,
                width=8
            )
            btn_move.pack(side=tk.LEFT, padx=1)
            btn_attack = tk.Button(
                top_row, text="Attack",
                command=lambda h=hero: self.hero_basic_attack_action(h),
                state=tk.NORMAL if hero.attack_available else tk.DISABLED,
                width=8
            )
            btn_attack.pack(side=tk.LEFT, padx=1)

            # Bottom row: Abilities
            bottom_row = tk.Frame(frame)
            bottom_row.pack(fill=tk.X)

            # ...inside your draw_hero_panel method, in the abilities loop...
            for ability in hero.abilities:
                frame_ability = tk.Frame(bottom_row)
                # Add more horizontal padding between abilities
                frame_ability.pack(side=tk.LEFT, padx=6)

                if ability.variable_cost:
                    energy_var = tk.IntVar(value=1)
                    spin = tk.Spinbox(frame_ability, from_=1, to=hero.current_energy, width=3, textvariable=energy_var)
                    btn = tk.Button(
                        frame_ability,
                        text=ability.name,
                        command=lambda h=hero, a=ability, e=energy_var: self.use_ability(h, a, e.get()),
                        state=tk.NORMAL if ability.is_castable() else tk.DISABLED,
                        width=12
                    )
                    btn.pack(side=tk.LEFT)
                    spin.pack(side=tk.LEFT)
                else:
                    btn = tk.Button(
                        frame_ability,
                        text=ability.name,
                        command=lambda h=hero, a=ability: self.use_ability(h, a),
                        state=tk.NORMAL if ability.is_castable() else tk.DISABLED,
                        width=12
                    )
                    btn.pack(side=tk.LEFT)

        self.end_round_button = tk.Button(self.left_panel, text="End Round", command=self.end_round)
        self.end_round_button.pack(side=tk.BOTTOM, pady=10)

    def get_figure_representation(self, cell_contents):
        if not cell_contents:
            return " "
        if len(cell_contents) > 1:
            front_figures = [f for f in cell_contents if f.figure_type != FigureType.MARKER]
            if front_figures:
                assert(len(front_figures) == 1), "There should be only one front figure in a cell"
                figure = front_figures[0]
            else:
                figure = cell_contents[0]
        else:
            figure = cell_contents[0]

        right_effects = []
        left_effects = []
        base_text = figure.get_representation_text()
        
        for effect, details in EFFECTS_DISPLAY.items():
            # Get quantity from the appropriate source
            if details['is_condition']:
                quantity = figure.conditions.get(effect, 0)
            else:
                quantity = figure.active_effects.get(effect, 0)
            
            # Only add if quantity > 0
            if quantity > 0:
                effect_text = f"{details['icon']} {quantity}"
                effect_data = {"text": effect_text, "color": details['color']}
                
                if details['position'] == 'right':
                    right_effects.append(effect_data)
                elif details['position'] == 'left':
                    left_effects.append(effect_data)

        return {
            "center": base_text,
            "right_effects": right_effects,
            "left_effects": left_effects,
        }

    def draw_map(self):
        # Clear previous
        for widget in self.map_panel.winfo_children():
            widget.destroy()

        if hasattr(self, 'select_mode') and not len(self.valid_choices):
            print("No valid choices for selection mode, resetting.")
            self.select_mode = None

        for y in range(self.map.height):
            for x in range(self.map.width):
                cell = self.map.cell_contents[y][x]
                if cell:
                    rep = self.get_figure_representation(cell)
                else:
                    rep = {"center": " ", "right_effects": [], "left_effects": []}

                if hasattr(self, 'select_mode') and self.select_mode and Coords(x, y) in self.valid_choices:    
                    bg_color = self.select_color
                    cmd = lambda _e, x=x, y=y: self.select_cmd(Coords(x, y))
                else:
                    bg_color = "white"
                    cmd = None
                
                # Check if this cell is in any special path
                for path in self.map.encounter.special_tiles.values():
                    if Coords(x, y) in path["coords"]:
                        bg_color = path["color"]
                        break

                cell_frame = tk.Frame(self.map_panel, width=65, height=65, bg=bg_color, borderwidth=1, relief="solid")
                cell_frame.grid_propagate(False)  # Prevent resizing to fit contents

                # Center: main figure info
                center_label = tk.Label(cell_frame, text=rep["center"], bg=bg_color)
                center_label.place(relx=0.5, rely=0.5, anchor="center")

                # Right effects (stacked from bottom up)
                for i, eff in enumerate(reversed(rep["right_effects"])):
                    eff_label = tk.Label(cell_frame, text=eff['text'], fg=eff['color'], font=("Arial", 7), bg=bg_color)
                    eff_label.place(relx=1.0, rely=1.0 - i*0.18, anchor="se")

                # Left effects (stacked from bottom up)
                for i, eff in enumerate(reversed(rep["left_effects"])):
                    eff_label = tk.Label(cell_frame, text=eff['text'], fg=eff['color'], font=("Arial", 7), bg=bg_color)
                    eff_label.place(relx=0.0, rely=1.0 - i*0.18, anchor="sw")

                if cmd is not None:
                    cell_frame.bind("<Button-1>", cmd)
                    center_label.bind("<Button-1>", cmd)
                    # Optionally bind effect labels too

                cell_frame.grid(row=y, column=x)

                
    def draw_boss_window(self):
        # Clear previous card
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        card_frame = tk.Frame(self.right_panel, bg="#f8f4e3", bd=3, relief="ridge", padx=10, pady=10)
        card_frame.pack(pady=30, padx=20, fill=tk.BOTH, expand=True)

        name_label = tk.Label(card_frame, text=self.map.encounter.next_card['name'], font=("Arial", 16, "bold"), bg="#f8f4e3")
        name_label.pack(pady=(0, 10))

        text_label = tk.Label(card_frame, text=self.map.encounter.next_card['text'], font=("Arial", 12), wraplength=160, justify="left", bg="#f8f4e3")
        text_label.pack()
    
    def draw_everything(self):
        self.draw_hero_panel()
        self.draw_map()
        self.draw_boss_window()

    def end_round(self):
        self.map.end_hero_turn()
        self.map.execute_boss_turn()
        self.map.begin_hero_turn()
        # Reset UI for new hero turn
        self.draw_everything()

    def activate_hero(self, hero):
        hero.activate()
        self.draw_hero_panel()

    def hero_basic_move_action(self, hero):
        self.hero_move(hero, costs_move_action=True)

    def hero_move(self, hero, move_distance=None, costs_move_action=False):
        if move_distance is None:
            move_distance = hero.archetype['move']
        self.select_mode = 'hero_move'
        self.valid_choices = hero.get_valid_move_destinations(move_distance)
        self.select_color = "lightgreen"
        self.select_cmd = lambda coords: self.execute_move(hero, coords, costs_move_action)
        self.draw_map()
    
    def execute_move(self, hero, coords, costs_move_action=False):
        self.map.move_figure(hero.figure, coords)
        if costs_move_action:
            hero.move_available = False
        self.select_mode = None
        self.draw_map()
        self.draw_hero_panel()

    def hero_basic_attack_action(self, hero):
        self.hero_attack(hero, costs_attack_action=True)

    def hero_attack(self, hero, range=None, physical_damage=None, elemental_damage=None, costs_attack_action=False, after_attack_callback=None):
        if physical_damage is None:
            physical_damage = hero.archetype['physical_dmg']
        if elemental_damage is None:
            elemental_damage = hero.archetype['elemental_dmg']
        if range is None:
            range = hero.archetype['attack_range']
        targets = hero.get_valid_attack_targets(range)
        targets_dict = {t.position: t for t in targets}  # Use a dictionary for quick access
        if not targets:
            print(f"No valid attack targets for {hero.name}")
            return
        self.select_mode = 'hero_attack'
        self.valid_choices = [t.position for t in targets]  # Use targets as valid moves for attack selection   
        self.select_color = "#ff2222"
        self.select_cmd = lambda coords: self.execute_attack(hero.figure, targets_dict[coords], physical_damage, elemental_damage, costs_attack_action, after_attack_callback)
        self.draw_map()

    def execute_attack(self, attacking_figure, target_figure, physical_damage, elemental_damage, costs_attack_action=False, after_attack_callback=None):
        if target_figure:
            dmg_dealt = self.map.deal_damage(attacking_figure, target_figure, physical_damage, elemental_damage)
        if costs_attack_action and attacking_figure.figure_type == FigureType.HERO:
            attacking_figure.hero.attack_available = False
        if after_attack_callback:
            after_attack_callback(attacking_figure, target_figure, dmg_dealt, self)
        self.select_mode = None
        self.draw_map()
        self.draw_hero_panel()

    def choose_friendly_target(self, coords, range, callback_fn):
        valid_targets = self.map.get_figures_within_distance(coords, range)
        valid_targets = [f for f in valid_targets if f.figure_type == FigureType.HERO]
        if not valid_targets:
            print("No valid friendly targets in range")
            return None
        self.select_mode = 'choose_friendly_target'
        self.valid_choices = [f.position for f in valid_targets]
        self.select_color = "lightgreen"
        targets_dict = {f.position: f for f in valid_targets}

        def wrapped_callback(coords):
            callback_fn(targets_dict[coords])
            self.select_mode = None
            self.draw_map()
            self.draw_hero_panel()

        self.select_cmd = wrapped_callback
        self.draw_map()

    def use_ability(self, hero, ability, energy_amount=None):
        assert ability.is_castable
        
        if energy_amount is None:
            assert not ability.variable_cost, "Energy amount must be specified for variable cost abilities"
            energy_amount = ability.energy_cost

        hero.spend_energy(energy_amount)
        ability.effect_fn(hero.figure, energy_amount, ui=self)  # No x-cost for now
        ability.used = True
        print(f"{hero.name} used {ability.name} with {energy_amount} energy")
        self.draw_everything()

    def run(self):
        self.root.mainloop()

# Usage example (in your main.py or similar):
# from ui import GameUI
# game_ui = GameUI(map)
# game_ui.run()