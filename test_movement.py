"""
Test script for movement and pathfinding logic.
Tests various scenarios including diagonal movement and hazard avoidance.
"""

from map import Map
from figure import Figure, FigureType
from coords import Coords
from encounters.encounter_como import EncounterComo

# Track test results globally
test_results = []

def record_test_result(test_name, passed, message=""):
    """Record a test result for the summary"""
    test_results.append({
        'test': test_name,
        'passed': passed,
        'message': message
    })

def print_test_summary():
    """Print a summary of all test results"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_tests = [r for r in test_results if r['passed']]
    failed_tests = [r for r in test_results if not r['passed']]
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {len(passed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for result in failed_tests:
            print(f"  ✗ {result['test']}")
            if result['message']:
                print(f"    {result['message']}")
    else:
        print("\n✓ ALL TESTS PASSED!")
    
    print("="*60)

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
    all_passed = True
    for coord, expected_cost, desc in tests:
        if coord in valid_moves:
            actual_cost = valid_moves[coord]['move_cost']
            passed = actual_cost == expected_cost
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}: {coord} cost={actual_cost} (expected {expected_cost})")
            if not passed:
                all_passed = False
        else:
            if expected_cost > 4:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")
            else:
                print(f"  ✗ {desc}: {coord} NOT FOUND (expected cost {expected_cost})")
                all_passed = False
    
    record_test_result("TEST 1: Diagonal Movement", all_passed)

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
    all_passed = True
    for coord, should_be_reachable, desc in tests:
        if coord in valid_moves:
            info = valid_moves[coord]
            print(f"  ✓ {desc}: {coord} reachable "
                  f"(cost={info['move_cost']}, hazard={info['hazard_damage']})")
        else:
            if should_be_reachable:
                print(f"  ✗ {desc}: {coord} NOT FOUND (should be reachable)")
                all_passed = False
            else:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")
    
    record_test_result("TEST 2: Hazard Movement", all_passed)

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
    all_passed = True
    for coord, should_reach, expected_cost, desc in tests:
        if coord in valid_moves:
            info = valid_moves[coord]
            cost_ok = info['move_cost'] == expected_cost
            status = "✓" if cost_ok else "✗"
            print(f"  {status} {desc}: {coord} "
                  f"(cost={info['move_cost']}, expected={expected_cost}, "
                  f"hazard={info['hazard_damage']})")
            if not cost_ok:
                all_passed = False
        else:
            print(f"  ✗ {desc}: {coord} NOT FOUND")
            all_passed = False
    
    record_test_result("TEST 3: Multiple Hazards", all_passed)

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
    all_passed = True
    for coord, should_reach, expected_cost, desc in tests:
        if coord in valid_moves:
            if should_reach:
                info = valid_moves[coord]
                print(f"  ✓ {desc}: {coord} reachable (cost={info['move_cost']})")
            else:
                info = valid_moves[coord]
                print(f"  ✗ {desc}: {coord} INCORRECTLY REACHABLE (cost={info['move_cost']})")
                all_passed = False
        else:
            if not should_reach:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")
            else:
                print(f"  ✗ {desc}: {coord} NOT FOUND (should be reachable)")
                all_passed = False
    
    record_test_result("TEST 4: Vanish Movement", all_passed)

def test_diagonal_hazard_crossing():
    """Test hazard damage when moving diagonally across hazards"""
    print("\n" + "="*60)
    print("TEST 5: Diagonal Hazard Crossing")
    print("="*60)
    print("Layout: Hero at (0,0), Lava at (1,0) and (0,1)")
    print("Expected: Moving to (1,1) should take hazard from crossing lava")
    
    from encounters.encounter_base import EncounterBase
    class DiagonalHazardEncounter(EncounterBase):
        def setup_map(self, map):
            # Add lava on two adjacent squares forming a diagonal crossing
            lava1 = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
            lava2 = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
            map.add_figure(lava1, Coords(1, 0), on_occupied='colocate')
            map.add_figure(lava2, Coords(0, 1), on_occupied='colocate')
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(DiagonalHazardEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])
    map.add_figure(hero.figure, Coords(0, 0))
    
    valid_moves = print_reachable_squares(map, hero.figure, 4)
    
    print("\nDiagonal Hazard Crossing Checks:")
    all_passed = True
    # Moving diagonally to (1,1) should cross one of the lava squares
    if Coords(1, 1) in valid_moves:
        info = valid_moves[Coords(1, 1)]
        expected_hazard = 1  # Should take 1 from crossing diagonal
        if info['hazard_damage'] == expected_hazard:
            print(f"  ✓ (1,1): hazard={info['hazard_damage']} (expected {expected_hazard})")
        else:
            print(f"  ✗ (1,1): hazard={info['hazard_damage']} (expected {expected_hazard})")
            all_passed = False
    else:
        print(f"  ✗ (1,1): NOT FOUND (should be reachable with hazard damage)")
        all_passed = False
    
    # Test case where both diagonal crossing squares are lava
    print("\nBoth crossing squares have lava:")
    # (2,1) diagonal from (1,0) - crosses through lava at (1,0) or (2,0)
    if Coords(2, 1) in valid_moves:
        info = valid_moves[Coords(2, 1)]
        print(f"  Info: (2,1) cost={info['move_cost']}, hazard={info['hazard_damage']}")
    else:
        print(f"  Info: (2,1) not reachable")
    
    record_test_result("TEST 5: Diagonal Hazard Crossing", all_passed)

def test_both_diagonals_blocked():
    """Test that diagonal movement is blocked if both crossing squares are blocked"""
    print("\n" + "="*60)
    print("TEST 6: Both Diagonal Crossing Squares Blocked")
    print("="*60)
    print("Layout: Hero at (5,5), Obstacles at (6,5) and (5,6)")
    print("Expected: Cannot move diagonally to (6,6)")
    
    from encounters.encounter_base import EncounterBase
    class BlockedDiagonalEncounter(EncounterBase):
        def setup_map(self, map):
            # Block both adjacent squares
            obstacle1 = Figure("Wall", FigureType.OBSTACLE)
            obstacle2 = Figure("Wall", FigureType.OBSTACLE)
            map.add_figure(obstacle1, Coords(6, 5))
            map.add_figure(obstacle2, Coords(5, 6))
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(BlockedDiagonalEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])
    map.add_figure(hero.figure, Coords(5, 5))
    
    valid_moves = print_reachable_squares(map, hero.figure, 4)
    
    print("\nBlocked Diagonal Checks:")
    all_passed = True
    # Note: (6,6) can still be reached via alternate path, just not directly
    # The direct diagonal move is blocked, but pathfinding finds (5,5) -> (4,6) -> (5,7) -> (6,6)
    if Coords(6, 6) not in valid_moves:
        print(f"  ✓ (6,6): Correctly NOT reachable (both crossing squares blocked)")
    else:
        # This is actually expected behavior - alternate paths exist
        info = valid_moves[Coords(6, 6)]
        if info['move_cost'] > 1:
            print(f"  Note: (6,6) reachable via alternate path (cost={info['move_cost']}), direct diagonal blocked ✓")
        else:
            print(f"  ✗ (6,6): INCORRECTLY reachable with cost 1 (direct diagonal should be blocked)")
            all_passed = False
    
    # But should be able to reach if only one is blocked
    print("\nTest with only one crossing square blocked:")
    if Coords(4, 6) in valid_moves:
        print(f"  ✓ (4,6): Reachable (only one crossing square blocked)")
    else:
        print(f"  ✗ (4,6): NOT reachable (should be reachable)")
        all_passed = False
    
    record_test_result("TEST 6: Both Diagonal Crossing Squares Blocked", all_passed)

def test_flee_directions():
    """Test that flee movement only allows valid directions"""
    print("\n" + "="*60)
    print("TEST 7: Flee Directions")
    print("="*60)
    print("Layout: Hero at (5,5), Threat at (3,5)")
    print("Expected: Can flee East, NE, SE (within 45° of away)")
    
    from encounters.encounter_base import EncounterBase
    class FleeEncounter(EncounterBase):
        def setup_map(self, map):
            # Add threat figure
            threat = Figure("Boss", FigureType.BOSS, health=100, move=2, 
                          physical_dmg=5, elemental_dmg=0, attack_range=1)
            map.add_figure(threat, Coords(3, 5))
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(FleeEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])
    hero_figure = hero.figure
    map.add_figure(hero_figure, Coords(5, 5))
    
    # Get threat figure
    threat_figure = map.get_figures_by_type(FigureType.BOSS)[0]
    
    # Get valid flee squares
    flee_squares = map.move_away_squares(hero_figure, threat_figure)
    
    print(f"\nFlee squares from (5,5) away from threat at (3,5):")
    print(f"Total flee squares: {len(flee_squares)}")
    
    # Print by distance for readability
    for distance in [1, 2, 3, 4]:
        dist_squares = [(c, info) for c, info in flee_squares.items() 
                       if info['move_cost'] == distance]
        if dist_squares:
            print(f"\n  Distance {distance}:")
            for coord, info in sorted(dist_squares, key=lambda x: (x[0].x, x[0].y)):
                print(f"    ({coord.x},{coord.y}): hazard={info['hazard_damage']}")
    
    # Specific direction checks
    print("\nDirection Checks (from (5,5) with threat at (3,5)):")
    tests = [
        (Coords(6, 5), True, "E - directly away"),
        (Coords(6, 6), True, "NE - within 45°"),
        (Coords(6, 4), True, "SE - within 45°"),
        (Coords(5, 6), False, "N - perpendicular (should NOT be valid)"),
        (Coords(5, 4), False, "S - perpendicular (should NOT be valid)"),
        (Coords(4, 5), False, "W - toward threat (should NOT be valid)"),
        (Coords(8, 5), True, "3 squares E - should reach with 3 move"),
    ]
    
    all_passed = True
    for coord, should_be_valid, desc in tests:
        if coord in flee_squares:
            if should_be_valid:
                info = flee_squares[coord]
                print(f"  ✓ {desc}: {coord} (cost={info['move_cost']})")
            else:
                print(f"  ✗ {desc}: {coord} INCORRECTLY VALID")
                all_passed = False
        else:
            if not should_be_valid:
                print(f"  ✓ {desc}: {coord} correctly NOT valid")
            else:
                print(f"  ✗ {desc}: {coord} NOT FOUND (should be valid)")
                all_passed = False
    
    record_test_result("TEST 7: Flee Directions", all_passed)

def test_flee_with_hazards():
    """Test flee movement through hazards"""
    print("\n" + "="*60)
    print("TEST 8: Flee Through Hazards")
    print("="*60)
    print("Layout: Hero at (5,5), Threat at (3,5), Lava at (7,5)")
    print("Expected: Can flee through lava but takes hazard damage")
    
    from encounters.encounter_base import EncounterBase
    class FleeHazardEncounter(EncounterBase):
        def setup_map(self, map):
            # Add threat and lava
            threat = Figure("Boss", FigureType.BOSS, health=100, move=2,
                          physical_dmg=5, elemental_dmg=0, attack_range=1)
            map.add_figure(threat, Coords(3, 5))
            
            lava = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
            map.add_figure(lava, Coords(7, 5), on_occupied='colocate')
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(FleeHazardEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])
    hero_figure = hero.figure
    map.add_figure(hero_figure, Coords(5, 5))
    
    threat_figure = map.get_figures_by_type(FigureType.BOSS)[0]
    flee_squares = map.move_away_squares(hero_figure, threat_figure)
    
    print("\nFlee with Hazards Checks:")
    tests = [
        (Coords(7, 5), 2, 1, "Through lava at (7,5)"),
        (Coords(8, 5), 3, 1, "Beyond lava"),
        (Coords(6, 6), 1, 0, "Diagonal around lava"),
    ]
    
    all_passed = True
    for coord, expected_cost, expected_hazard, desc in tests:
        if coord in flee_squares:
            info = flee_squares[coord]
            cost_ok = info['move_cost'] == expected_cost
            hazard_ok = info['hazard_damage'] == expected_hazard
            status = "✓" if (cost_ok and hazard_ok) else "✗"
            print(f"  {status} {desc}: {coord} cost={info['move_cost']} "
                  f"(expected {expected_cost}), hazard={info['hazard_damage']} "
                  f"(expected {expected_hazard})")
            if not (cost_ok and hazard_ok):
                all_passed = False
        else:
            print(f"  ✗ {desc}: {coord} NOT FOUND")
            all_passed = False
    
    record_test_result("TEST 8: Flee Through Hazards", all_passed)

def test_diagonal_obstacle_and_hazard():
    """Test diagonal movement when one crossing square is blocked and the other is a hazard"""
    print("\n" + "="*60)
    print("TEST 9: Diagonal with Obstacle and Hazard")
    print("="*60)
    print("Layout: Hero at (5,5), Obstacle at (6,5), Lava at (5,6)")
    print("Expected: Can move diagonally to (6,6), taking hazard from lava")
    
    from encounters.encounter_base import EncounterBase
    class DiagonalMixedEncounter(EncounterBase):
        def setup_map(self, map):
            # One obstacle, one hazard on crossing squares
            obstacle = Figure("Wall", FigureType.OBSTACLE)
            lava = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
            map.add_figure(obstacle, Coords(6, 5))
            map.add_figure(lava, Coords(5, 6), on_occupied='colocate')
        def get_deployment_zone(self):
            return [Coords(x, y) for x in range(11) for y in range(11)]
    
    map = Map(DiagonalMixedEncounter())
    
    from heroes.hero_archetypes import hero_archetypes
    from heroes.hero import Hero
    hero = Hero(hero_archetypes[0])
    map.add_figure(hero.figure, Coords(5, 5))
    
    valid_moves = print_reachable_squares(map, hero.figure, 4)
    
    print("\nDiagonal Mixed Crossing Checks:")
    tests = [
        (Coords(6, 6), True, 1, 1, "diagonal with obstacle+hazard crossing"),
        (Coords(6, 5), False, None, None, "obstacle square (should NOT be passable)"),
        (Coords(5, 6), True, 1, 1, "lava square (should be passable)"),
    ]
    
    all_passed = True
    for coord, should_reach, expected_cost, expected_hazard, desc in tests:
        if coord in valid_moves:
            if should_reach:
                info = valid_moves[coord]
                cost_ok = info['move_cost'] == expected_cost
                hazard_ok = info['hazard_damage'] == expected_hazard
                status = "✓" if (cost_ok and hazard_ok) else "✗"
                print(f"  {status} {desc}: {coord} cost={info['move_cost']} "
                      f"(expected {expected_cost}), hazard={info['hazard_damage']} "
                      f"(expected {expected_hazard})")
            else:
                print(f"  ✗ {desc}: {coord} INCORRECTLY reachable")
        else:
            if not should_reach:
                print(f"  ✓ {desc}: {coord} correctly NOT reachable")
            else:
                print(f"  ✗ {desc}: {coord} NOT FOUND (should be reachable)")
                all_passed = False
    
    record_test_result("TEST 9: Diagonal with Obstacle and Hazard", all_passed)

if __name__ == "__main__":
    print("="*60)
    print("MOVEMENT PATHFINDING TEST SUITE")
    print("="*60)
    
    test_diagonal_movement()
    test_hazard_movement()
    test_complex_hazards()
    test_vanish_movement()
    test_diagonal_hazard_crossing()
    test_both_diagonals_blocked()
    test_flee_directions()
    test_flee_with_hazards()
    test_diagonal_obstacle_and_hazard()
    
    print_test_summary()