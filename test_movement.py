"""
Test script for movement and pathfinding logic.
Tests various scenarios including diagonal movement and hazard avoidance.
"""

from map import Map
from figure import Figure, FigureType
from coords import Coords
from encounters.encounter_como import EncounterComo

def print_reachable_squares(map, figure, move_distance):
    """Print all reachable squares with their costs and hazard damage."""
    valid_moves = figure.hero.get_valid_move_destinations(move_distance)
    
    print(f"\n{'='*60}")
    print(f"Testing: {figure.name} at {figure.position} with {move_distance} move")
    print(f"{'='*60}")
    
    # Sort by cost, then hazard
    sorted_moves = sorted(valid_moves.items(), 
                         key=lambda x: (x[1]['move_cost'], x[1]['hazard_damage']))
    
    for coords, info in sorted_moves:
        path_str = " -> ".join(f"({c.x},{c.y})" for c in info['path'])
        print(f"  ({coords.x},{coords.y}): "
              f"cost={info['move_cost']}, "
              f"hazard={info['hazard_damage']}, "
              f"path={path_str}")
    
    print(f"Total reachable: {len(valid_moves)} squares")
    return valid_moves

def test_diagonal_movement():
    """Test basic diagonal movement with D&D rules (1,2,1,2,...)"""
    print("\n" + "="*60)
    print("TEST 1: Diagonal Movement")
    print("="*60)
    print("Expected: 4 move should reach 3 diagonals (cost 1+2+1=4)")
    
    # Create a simple map with no obstacles
    from encounters.encounter_base import EncounterBase
    class EmptyEncounter(EncounterBase):
        def setup_map(self, map):
            pass
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(EmptyEncounter())
    
    # Create a test hero
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])  # Use first archetype
    map.add_figure(hero.figure, Coords(0, 0))
    
    # Test with 4 move
    valid_moves = print_reachable_squares(map, hero.figure, 4)
    
    # Check specific diagonal squares
    tests = [
        (Coords(1, 1), 1, "1st diagonal"),
        (Coords(2, 2), 3, "2nd diagonal"),
        (Coords(3, 3), 4, "3rd diagonal"),
        (Coords(4, 4), 6, "4th diagonal (should NOT be reachable)"),
    ]
    
    print("\nDiagonal Checks:")
    for coord, expected_cost, desc in tests:
        if coord in valid_moves:
            actual_cost = valid_moves[coord]['move_cost']
            status = "✓" if actual_cost == expected_cost else "✗"
            print(f"  {status} {desc}: {coord} cost={actual_cost} (expected {expected_cost})")
        else:
            if expected_cost > 4:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")
            else:
                print(f"  ✗ {desc}: {coord} NOT FOUND (expected cost {expected_cost})")

def test_hazard_movement():
    """Test movement through and around hazards"""
    print("\n" + "="*60)
    print("TEST 2: Hazard Movement")
    print("="*60)
    print("Layout: Rogue at (0,0), Lava at (0,2), 4 move")
    print("Expected: Can reach (4,0) through lava (cost 4, hazard 1)")
    
    from encounters.encounter_base import EncounterBase
    class HazardEncounter(EncounterBase):
        def setup_map(self, map):
            # Add lava at (0,2)
            lava = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
            map.add_figure(lava, Coords(0, 2), on_occupied='colocate')
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(HazardEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[2])  # Rogue
    map.add_figure(hero.figure, Coords(0, 0))
    
    # Test with 4 move
    valid_moves = print_reachable_squares(map, hero.figure, 4)
    
    # Check specific squares
    tests = [
        (Coords(4, 0), True, "straight line through lava"),
        (Coords(3, 3), True, "diagonal (no lava)"),
        (Coords(4, 1), True, "around lava"),
    ]
    
    print("\nHazard Checks:")
    for coord, should_be_reachable, desc in tests:
        if coord in valid_moves:
            info = valid_moves[coord]
            print(f"  ✓ {desc}: {coord} reachable "
                  f"(cost={info['move_cost']}, hazard={info['hazard_damage']})")
        else:
            if should_be_reachable:
                print(f"  ✗ {desc}: {coord} NOT FOUND (should be reachable)")
            else:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")

def test_complex_hazards():
    """Test movement with multiple hazards"""
    print("\n" + "="*60)
    print("TEST 3: Multiple Hazards")
    print("="*60)
    print("Layout: Hero at (5,5), Lava at (4,5), (5,4), (6,5), (5,6)")
    print("Expected: Can reach adjacent squares through lava")
    
    from encounters.encounter_base import EncounterBase
    class ComplexHazardEncounter(EncounterBase):
        def setup_map(self, map):
            # Surround center with lava
            for coords in [Coords(4,5), Coords(5,4), Coords(6,5), Coords(5,6)]:
                lava = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
                map.add_figure(lava, coords, on_occupied='colocate')
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(ComplexHazardEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])
    map.add_figure(hero.figure, Coords(5, 5))
    
    # Test with 4 move
    valid_moves = print_reachable_squares(map, hero.figure, 4)
    
    # Check that we can reach beyond the lava ring
    tests = [
        (Coords(3, 5), True, 2, "2 moves through 1 lava"),
        (Coords(7, 5), True, 2, "2 moves through 1 lava"),
        (Coords(2, 5), True, 3, "3 moves through 2 lava"),
    ]
    
    print("\nComplex Hazard Checks:")
    for coord, should_reach, expected_cost, desc in tests:
        if coord in valid_moves:
            info = valid_moves[coord]
            cost_ok = info['move_cost'] == expected_cost
            status = "✓" if cost_ok else "✗"
            print(f"  {status} {desc}: {coord} "
                  f"(cost={info['move_cost']}, expected={expected_cost}, "
                  f"hazard={info['hazard_damage']})")
        else:
            print(f"  ✗ {desc}: {coord} NOT FOUND")

def test_vanish_movement():
    """Test Vanish ability with 2 move (should reach 1 diagonal only)"""
    print("\n" + "="*60)
    print("TEST 4: Vanish Movement (2 move)")
    print("="*60)
    print("Expected: 2 move should reach 1 diagonal (cost 1) but NOT 2 diagonals (cost 3)")
    
    from encounters.encounter_base import EncounterBase
    class EmptyEncounter(EncounterBase):
        def setup_map(self, map):
            pass
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(EmptyEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[2])  # Rogue
    map.add_figure(hero.figure, Coords(5, 5))
    
    # Test with 2 move (like Vanish)
    valid_moves = print_reachable_squares(map, hero.figure, 2)
    
    # Check diagonal limits
    tests = [
        (Coords(6, 6), True, 1, "1st diagonal"),
        (Coords(7, 7), False, 3, "2nd diagonal (should NOT reach)"),
    ]
    
    print("\nVanish Movement Checks:")
    for coord, should_reach, expected_cost, desc in tests:
        if coord in valid_moves:
            if should_reach:
                info = valid_moves[coord]
                print(f"  ✓ {desc}: {coord} reachable (cost={info['move_cost']})")
            else:
                info = valid_moves[coord]
                print(f"  ✗ {desc}: {coord} INCORRECTLY REACHABLE (cost={info['move_cost']})")
        else:
            if not should_reach:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")
            else:
                print(f"  ✗ {desc}: {coord} NOT FOUND (should be reachable)")

if __name__ == "__main__":
    print("="*60)
    print("MOVEMENT PATHFINDING TEST SUITE")
    print("="*60)
    
    test_diagonal_movement()
    test_hazard_movement()
    test_complex_hazards()
    test_vanish_movement()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
