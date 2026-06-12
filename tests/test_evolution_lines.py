"""Tests for gobattlekit.data.evolution_lines — generation and cycle safety."""
import json
import pytest

from gobattlekit.data.evolution_lines import generate_evolution_lines


class TestGenerateEvolutionLines:
    def test_simple_two_stage(self):
        """Marill -> Azumarill."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'marill',
                    'speciesName': 'Marill',
                    'family': {'id': 'marill', 'parent': None, 'evolutions': ['azumarill']},
                },
                {
                    'speciesId': 'azumarill',
                    'speciesName': 'Azumarill',
                    'family': {'id': 'marill', 'parent': 'marill', 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        assert 'Azumarill' in lines
        assert lines['Azumarill'] == ['Marill', 'Azumarill']

    def test_three_stage(self):
        """Bulbasaur -> Ivysaur -> Venusaur."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'bulbasaur',
                    'speciesName': 'Bulbasaur',
                    'family': {'id': 'bulbasaur', 'parent': None, 'evolutions': ['ivysaur']},
                },
                {
                    'speciesId': 'ivysaur',
                    'speciesName': 'Ivysaur',
                    'family': {'id': 'bulbasaur', 'parent': 'bulbasaur', 'evolutions': ['venusaur']},
                },
                {
                    'speciesId': 'venusaur',
                    'speciesName': 'Venusaur',
                    'family': {'id': 'bulbasaur', 'parent': 'ivysaur', 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        assert 'Venusaur' in lines
        assert lines['Venusaur'] == ['Bulbasaur', 'Ivysaur', 'Venusaur']

    def test_branching_evolution(self):
        """Eevee -> Vaporeon / Jolteon / Flareon."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'eevee',
                    'speciesName': 'Eevee',
                    'family': {'id': 'eevee', 'parent': None,
                               'evolutions': ['vaporeon', 'jolteon', 'flareon']},
                },
                {
                    'speciesId': 'vaporeon',
                    'speciesName': 'Vaporeon',
                    'family': {'id': 'eevee', 'parent': 'eevee', 'evolutions': []},
                },
                {
                    'speciesId': 'jolteon',
                    'speciesName': 'Jolteon',
                    'family': {'id': 'eevee', 'parent': 'eevee', 'evolutions': []},
                },
                {
                    'speciesId': 'flareon',
                    'speciesName': 'Flareon',
                    'family': {'id': 'eevee', 'parent': 'eevee', 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        assert lines['Vaporeon'] == ['Eevee', 'Vaporeon']
        assert lines['Jolteon'] == ['Eevee', 'Jolteon']
        assert lines['Flareon'] == ['Eevee', 'Flareon']

    def test_single_stage_pokemon(self):
        """A pokemon with no evolutions and no parent is its own line."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'registeel',
                    'speciesName': 'Registeel',
                    'family': {'id': 'registeel', 'parent': None, 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        assert 'Registeel' in lines
        assert lines['Registeel'] == ['Registeel']

    def test_no_family_field_skipped(self):
        """Pokemon without a 'family' key should be skipped."""
        gm = {
            'pokemon': [
                {'speciesId': 'missingno', 'speciesName': 'MissingNo'},
            ],
        }
        lines = generate_evolution_lines(gm)
        assert len(lines) == 0

    def test_cycle_safety(self):
        """A cycle in the evolution data should not cause infinite recursion."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'a',
                    'speciesName': 'A',
                    'family': {'id': 'fam', 'parent': None, 'evolutions': ['b']},
                },
                {
                    'speciesId': 'b',
                    'speciesName': 'B',
                    'family': {'id': 'fam', 'parent': 'a', 'evolutions': ['a']},
                },
            ],
        }
        # Should not hang or raise RecursionError
        lines = generate_evolution_lines(gm)
        # B's evolution back to A is blocked by visited set,
        # so B is treated as a leaf → line [A, B] is emitted
        assert 'B' in lines
        assert lines['B'] == ['A', 'B']

    def test_self_referencing_evolution(self):
        """A pokemon that lists itself as its own evolution."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'loop',
                    'speciesName': 'Loop',
                    'family': {'id': 'loop', 'parent': None, 'evolutions': ['loop']},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        # Self-reference blocked by visited set → treated as leaf
        assert 'Loop' in lines
        assert lines['Loop'] == ['Loop']

    def test_shared_final_across_multiple_roots(self):
        """Burmy-style: three parentless roots all evolve into the same
        final (plus per-root variants). The shared final must list EVERY
        root as a pre-evo — the family-wide visited set previously kept
        only the first root's chain (CP13), so Burmy (Sandy)/(Trash)
        never mapped to Mothim."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'burmy_plant',
                    'speciesName': 'Burmy (Plant)',
                    'family': {'id': 'burmy', 'parent': None,
                               'evolutions': ['wormadam_plant', 'mothim']},
                },
                {
                    'speciesId': 'burmy_sandy',
                    'speciesName': 'Burmy (Sandy)',
                    'family': {'id': 'burmy', 'parent': None,
                               'evolutions': ['wormadam_sandy', 'mothim']},
                },
                {
                    'speciesId': 'wormadam_plant',
                    'speciesName': 'Wormadam (Plant)',
                    'family': {'id': 'burmy', 'parent': 'burmy_plant', 'evolutions': []},
                },
                {
                    'speciesId': 'wormadam_sandy',
                    'speciesName': 'Wormadam (Sandy)',
                    'family': {'id': 'burmy', 'parent': 'burmy_sandy', 'evolutions': []},
                },
                {
                    'speciesId': 'mothim',
                    'speciesName': 'Mothim',
                    'family': {'id': 'burmy', 'parent': 'burmy_plant', 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        assert lines['Wormadam (Plant)'] == ['Burmy (Plant)', 'Wormadam (Plant)']
        assert lines['Wormadam (Sandy)'] == ['Burmy (Sandy)', 'Wormadam (Sandy)']
        assert set(lines['Mothim'][:-1]) == {'Burmy (Plant)', 'Burmy (Sandy)'}
        assert lines['Mothim'][-1] == 'Mothim'

    def test_empty_gamemaster(self):
        gm = {'pokemon': []}
        lines = generate_evolution_lines(gm)
        assert lines == {}

    def test_orphan_members_no_root(self):
        """If all family members have parents (no root), no lines are generated."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'orphan',
                    'speciesName': 'Orphan',
                    'family': {'id': 'fam', 'parent': 'nonexistent', 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        # No root → build_lines returns empty → no lines
        assert 'Orphan' not in lines

    def test_final_is_last_in_line(self):
        """The key in the result dict should be the last element of the line."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'charmander',
                    'speciesName': 'Charmander',
                    'family': {'id': 'charmander', 'parent': None, 'evolutions': ['charmeleon']},
                },
                {
                    'speciesId': 'charmeleon',
                    'speciesName': 'Charmeleon',
                    'family': {'id': 'charmander', 'parent': 'charmander', 'evolutions': ['charizard']},
                },
                {
                    'speciesId': 'charizard',
                    'speciesName': 'Charizard',
                    'family': {'id': 'charmander', 'parent': 'charmeleon', 'evolutions': []},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        for final_name, line in lines.items():
            assert line[-1] == final_name

    def test_evolution_to_missing_id(self):
        """If an evolution references an ID not in the family, treat as leaf."""
        gm = {
            'pokemon': [
                {
                    'speciesId': 'base',
                    'speciesName': 'Base',
                    'family': {'id': 'fam', 'parent': None, 'evolutions': ['ghost_id']},
                },
            ],
        }
        lines = generate_evolution_lines(gm)
        # ghost_id not in id_map → traverse returns False, so base
        # is treated as a leaf and emitted
        assert 'Base' in lines
        assert lines['Base'] == ['Base']
