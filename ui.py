import tkinter as tk
from figure import FigureType
from coords import Coords
from effects_display import EFFECTS_DISPLAY
from game_targeting import TargetingContext
from game_state_snapshot import GameStateSnapshot

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
        self.placement_queue = list(heroes)
        self.placement_label = None
        self.placing = True

        # used to prompt for hero actions
        self.select_mode = None
        self.valid_choices = []
        self.select_color = None
        self.select_cmd = None
        self.end_round_button = None
        self.restart_round_button = None
        self.round_snapshot = None  # Stores state at start of round for restart

        self.setup_placement()
        self.draw_everything()
        self.update_placement_label()

    def setup_placement(self):
        self.select_mode = 'hero_placement'
        self.valid_choices = [Coords(x, y) for y in range(self.map.height - 2, self.map.height) for x in range(self.map.width)]
        self.select_color = "lightblue"
        self.select_cmd = lambda coords: self.place_hero(coords.x, coords.y)

    def update_placement_label(self):
        if hasattr(self, "placement_label") and self.placement_label:
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
            # Create initial snapshot at start of round 1
            self.round_snapshot = GameStateSnapshot(self.map)
            self.draw_hero_panel()
            self.draw_map()

    def draw_hero_panel(self):
        # Clear previous
        for widget in self.left_panel.winfo_children():
            widget.destroy()

        # Add round number display at the top
        round_frame = tk.Frame(self.left_panel, borderwidth=2, relief="ridge", padx=5, pady=3)
        round_frame.pack(fill=tk.X, pady=(0, 5))
        
        round_label = tk.Label(round_frame, text=f"Round {self.map.current_round}", font=("Arial", 12, "bold"))
        round_label.pack()

        hero_figures = self.map.get_figures_by_type(FigureType.HERO)
        for hero_figure in hero_figures:
            hero = hero_figure.hero
            frame = tk.Frame(self.left_panel, borderwidth=2, relief="groove", padx=3, pady=3)
            frame.pack(fill=tk.X, pady=2)

            # Hero info row (name, health, energy)
            info_row = tk.Frame(frame)
            info_row.pack(fill=tk.X)
            
            name_label = tk.Label(info_row, text=hero.name, width=10, anchor="w", font=("Arial", 9, "bold"))
            name_label.pack(side=tk.LEFT, padx=2)
            
            health_label = tk.Label(info_row, text=f"HP {hero_figure.current_health}/{hero_figure.max_health}", width=7, anchor="center", font=("Arial", 8))
            health_label.pack(side=tk.LEFT, padx=2)
            
            energy_label = tk.Label(info_row, text=f"E {hero.current_energy}", width=5, anchor="center", font=("Arial", 8))
            energy_label.pack(side=tk.LEFT, padx=2)

            # Action buttons row (Activate, Move, Attack)
            action_row = tk.Frame(frame)
            action_row.pack(fill=tk.X, pady=1)
            
            # Activate button with energy cost
            activation_cost = self.map.heroes_activated  # 0-5 energy based on turn order
            btn_activate = self.create_button_with_costs(
                action_row, "Activate",
                command=lambda h=hero: self.activate_hero(h),
                state=tk.NORMAL if (not hero.activated and hero.can_activate) else tk.DISABLED,
                width=7,
                energy_cost=activation_cost
            )
            
            # Move button with move cost indicator
            btn_move = self.create_button_with_costs(
                action_row, "Move",
                command=lambda h=hero: self.hero_basic_move_action(h),
                state=tk.NORMAL if hero.move_available else tk.DISABLED,
                width=7,
                move_cost=True
            )
            
            # Attack button with attack cost indicator
            btn_attack = self.create_button_with_costs(
                action_row, "Attack", 
                command=lambda h=hero: self.hero_basic_attack_action(h),
                state=tk.NORMAL if hero.attack_available else tk.DISABLED,
                width=7,
                attack_cost=True
            )

            # Abilities - split into multiple rows if needed
            abilities_per_row = 2  # Limit abilities per row
            ability_rows = []
            current_row = None
            
            for i, ability in enumerate(hero.abilities):
                if i % abilities_per_row == 0:
                    current_row = tk.Frame(frame)
                    current_row.pack(fill=tk.X, pady=1)
                    ability_rows.append(current_row)
                
                frame_ability = tk.Frame(current_row)
                frame_ability.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

                if ability.variable_cost:
                    energy_var = tk.IntVar(value=1)
                    
                    if hero.current_energy > 0:
                        spin = tk.Spinbox(frame_ability, from_=1, to=hero.current_energy, width=2, textvariable=energy_var)
                    else:
                        # When no energy, create a disabled spinbox with 0 value
                        energy_var.set(0)
                        spin = tk.Spinbox(frame_ability, from_=0, to=0, width=2, textvariable=energy_var, state=tk.DISABLED)
                    
                    btn = self.create_button_with_costs(
                        frame_ability,
                        ability.name,
                        command=lambda h=hero, a=ability, e=energy_var: self.use_ability(h, a, e.get()),
                        state=tk.NORMAL if ability.is_castable() else tk.DISABLED,
                        width=10,
                        energy_cost="X",  # Variable cost shown as X
                        move_cost=ability.move_cost,
                        attack_cost=ability.attack_cost
                    )
                    spin.pack(side=tk.LEFT, padx=1)
                else:
                    btn = self.create_button_with_costs(
                        frame_ability,
                        ability.name,
                        command=lambda h=hero, a=ability: self.use_ability(h, a),
                        state=tk.NORMAL if ability.is_castable() else tk.DISABLED,
                        width=10,
                        energy_cost=ability.energy_cost if ability.energy_cost > 0 else None,
                        move_cost=ability.move_cost,
                        attack_cost=ability.attack_cost
                    )

        # Bottom button panel
        button_panel = tk.Frame(self.left_panel)
        button_panel.pack(side=tk.BOTTOM, pady=10)
        
        self.restart_round_button = tk.Button(button_panel, text="Restart Round", command=self.restart_round)
        self.restart_round_button.pack(side=tk.LEFT, padx=5)
        
        self.end_round_button = tk.Button(button_panel, text="End Round", command=self.end_round)
        self.end_round_button.pack(side=tk.LEFT, padx=5)

    def create_button_with_costs(self, parent, text, command, state, width=8, energy_cost=None, move_cost=False, attack_cost=False):
        """Create a button with cost indicators in the text"""
        # Build cost string
        costs = []
        if energy_cost is not None:
            costs.append(str(energy_cost))
        if move_cost:
            costs.append("M")  # M for Move
        if attack_cost:
            costs.append("A")  # A for Attack
        
        # Format button text with costs
        if costs:
            cost_str = "".join(costs)
            button_text = f"{text} ({cost_str})"
        else:
            button_text = text
        
        # Create the button with cost in text
        btn = tk.Button(
            parent,
            text=button_text,
            command=command,
            state=state,
            width=width + 4  # Make wider to accommodate cost text
        )
        btn.pack(side=tk.LEFT, padx=1)
        
        return btn

    def get_figure_representation(self, cell_contents):
        if not cell_contents:
            return {
                "center": " ",
                "right_effects": [],
                "left_effects": [],
                "background_color": None
            }
        
        # Find the maximum render priority among all figures in the cell
        max_priority = max(f.targeting_parameters[TargetingContext.RENDERING_PRIORITY] for f in cell_contents)
        
        # Filter for figures with the maximum render priority
        max_priority_figures = [f for f in cell_contents if f.targeting_parameters[TargetingContext.RENDERING_PRIORITY] == max_priority]
        
        assert(len(max_priority_figures) == 1), f"There should be only one figure with max render priority {max_priority}, but found {len(max_priority_figures)}"
        figure = max_priority_figures[0]

        right_effects = []
        left_effects = []
        base_text = figure.get_representation_text()
        
        # Check for figure-specific background color, prioritizing by render priority
        background_color = None
        figures_with_colors = [f for f in cell_contents if hasattr(f, 'cell_color') and f.cell_color]
        if figures_with_colors:
            # Sort by rendering priority (highest first) and take the first one's color
            figures_with_colors.sort(key=lambda f: f.targeting_parameters[TargetingContext.RENDERING_PRIORITY], reverse=True)
            background_color = figures_with_colors[0].cell_color
        
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
            "background_color": background_color
        }

    def draw_map(self):
        # Clear previous widgets
        for widget in self.map_panel.winfo_children():
            widget.destroy()

        if hasattr(self, 'select_mode') and not self.valid_choices:
            print("No valid choices for selection mode, resetting.")
            self.select_mode = None

        for y in range(self.map.height):
            for x in range(self.map.width):
                cell = self.map.cell_contents[y][x]
                if cell:
                    rep = self.get_figure_representation(cell)
                else:
                    rep = {"center": " ", "right_effects": [], "left_effects": [], "background_color": None}

                # Collect all background colors for this cell
                bg_colors = []
                
                # Check for selection mode color (highest priority)
                if hasattr(self, 'select_mode') and self.select_mode and Coords(x, y) in self.valid_choices:    
                    assert self.select_cmd is not None, "select_cmd must be set when in select_mode"
                    bg_colors.append(self.select_color)
                    cmd = lambda _e, x=x, y=y: self.select_cmd(Coords(x, y))
                else:
                    cmd = None
                
                # Check for figure-specific color
                if rep["background_color"]:
                    bg_colors.append(rep["background_color"])
                
                # Check for special tiles with different colors
                if 'special_tiles' in self.map.encounter.__dict__:
                    for path in self.map.encounter.special_tiles.values():
                        if Coords(x, y) in path["coords"]:
                            bg_colors.append(path["color"])
                            break
                
                # Default white if no colors
                if not bg_colors:
                    bg_colors.append("white")
                
                # Create cell with potentially multiple background colors
                if len(bg_colors) == 1:
                    # Single color - use simple frame
                    cell_frame = tk.Frame(self.map_panel, width=65, height=65, bg=bg_colors[0], borderwidth=1, relief="solid")
                    cell_frame.grid_propagate(False)
                    bg_color = bg_colors[0]
                else:
                    # Multiple colors - use canvas with diagonal stripes
                    cell_frame = tk.Canvas(self.map_panel, width=65, height=65, borderwidth=1, relief="solid", highlightthickness=0)
                    cell_frame.grid_propagate(False)
                    
                    # Draw vertical stripes (8 total, alternating between colors)
                    stripe_width = 65 / 8
                    for i in range(8):
                        color = bg_colors[i % len(bg_colors)]
                        x1 = int(i * stripe_width)
                        x2 = int((i + 1) * stripe_width)
                        cell_frame.create_rectangle(x1, 0, x2, 65, fill=color, outline="")
                    
                    bg_color = bg_colors[0]  # Use first color for text background

                cell_frame.grid(row=y, column=x)

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

                # Bind click events
                if cmd is not None:
                    cell_frame.bind("<Button-1>", cmd)
                    center_label.bind("<Button-1>", cmd)

                
    def draw_boss_window(self):
        # Clear previous content
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        # Get display items from encounter
        display_items = self.map.encounter.get_boss_display_info()
        
        # Create a frame for each display item
        for item in display_items:
            card_frame = tk.Frame(self.right_panel, bg="#f8f4e3", bd=3, relief="ridge", padx=10, pady=10)
            card_frame.pack(pady=10, padx=20, fill=tk.BOTH)

            name_label = tk.Label(card_frame, text=item['name'], font=("Arial", 14, "bold"), bg="#f8f4e3")
            name_label.pack(pady=(0, 10))

            text_label = tk.Label(card_frame, text=item['text'], font=("Arial", 11), wraplength=160, justify="left", bg="#f8f4e3")
            text_label.pack()
    
    def draw_everything(self):
        self.draw_hero_panel()
        self.draw_map()
        self.draw_boss_window()

    def end_round(self):
        self.map.end_hero_turn()
        self.map.execute_boss_turn()
        self.map.begin_hero_turn()
        # Create snapshot at start of new round
        self.round_snapshot = GameStateSnapshot(self.map)
        # Reset UI for new hero turn
        self.draw_everything()
    
    def restart_round(self):
        """Restart the current round from the beginning."""
        if self.round_snapshot is None:
            print("No snapshot available - cannot restart round")
            return
        
        # Restore the game state
        self.round_snapshot.restore(self.map)
        
        # Reset any active selection mode
        self.select_mode = None
        self.valid_choices = []
        
        # Refresh the UI to reflect restored state
        self.draw_everything()
        print(f"Round {self.map.current_round} restarted")

    def activate_hero(self, hero):
        if hero.activate():  # activate() now returns True/False
            self.draw_hero_panel()
        else:
            print(f"Failed to activate {hero.name}")
            self.draw_hero_panel()  # Refresh to show disabled state

    def hero_basic_move_action(self, hero):
        # Consume the move action before initiating the move
        hero.move_available = False
        self.hero_move(hero)

    def hero_move(self, hero, move_distance=None, valid_destinations=None):
        if move_distance is None:
            move_distance = hero.figure.move  # Use the property that triggers GET_MOVE events
        self.select_mode = 'hero_move'
        
        # Use custom destinations if provided, otherwise calculate normal movement
        if valid_destinations is not None:
            # Handle legacy list format (convert to dict)
            if isinstance(valid_destinations, list):
                self.valid_choices = valid_destinations
                self.move_paths = None
            else:
                # New dict format with path info
                self.valid_choices = list(valid_destinations.keys())
                self.move_paths = valid_destinations
        else:
            move_info = hero.get_valid_move_destinations(move_distance)
            self.valid_choices = list(move_info.keys())
            self.move_paths = move_info
        
        self.select_color = "lightgreen"
        self.select_cmd = lambda coords: self.execute_move(hero, coords)
        self.draw_map()
    
    def execute_move(self, hero, coords):
        # Only move if the destination is different from current position
        if coords != hero.figure.position:
            # Use path information if available
            if hasattr(self, 'move_paths') and self.move_paths and coords in self.move_paths:
                path = self.move_paths[coords]['path']
                self.map.move_figure(hero.figure, coords, path=path)
            else:
                # Legacy path-less movement
                self.map.move_figure(hero.figure, coords)
        self.select_mode = None
        self.move_paths = None
        self.draw_map()
        self.draw_hero_panel()

    def hero_basic_attack_action(self, hero):
        # Consume the attack action before initiating the attack
        hero.attack_available = False
        self.hero_attack(hero)

    def hero_attack(self, hero, range=None, physical_damage=None, elemental_damage=None, after_attack_callback=None):
        if physical_damage is None and elemental_damage is None:
            physical_damage = hero.archetype['physical_dmg']
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
        self.select_cmd = lambda coords: self.execute_attack(hero.figure, targets_dict[coords], physical_damage, elemental_damage, after_attack_callback)
        self.draw_map()

    def execute_attack(self, attacking_figure, target_figure, physical_damage, elemental_damage, after_attack_callback=None):
        dmg_dealt = self.map.deal_damage(attacking_figure, target_figure, physical_damage, elemental_damage)    
        if after_attack_callback:
            after_attack_callback(attacking_figure, target_figure, dmg_dealt, self)
        self.select_mode = None
        self.draw_map()
        self.draw_hero_panel()

    def choose_friendly_target(self, coords, range, callback_fn, auto_cleanup=True):
        valid_targets = self.map.get_figures_within_distance(coords, range)
        valid_targets = [f for f in valid_targets if f.figure_type == FigureType.HERO]
        if not valid_targets:
            print("No valid friendly targets in range")
            return
        self.select_mode = 'choose_friendly_target'
        self.valid_choices = [f.position for f in valid_targets]
        self.select_color = "lightgreen"
        targets_dict = {f.position: f for f in valid_targets}

        def wrapped_callback(coords):
            callback_fn(targets_dict[coords])
            if auto_cleanup:
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
        
        # Handle move and attack costs
        if ability.move_cost:
            hero.move_available = False
        if ability.attack_cost:
            hero.attack_available = False
            
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