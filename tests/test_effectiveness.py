"""Tests for gobattlekit.data.effectiveness — type chart consistency."""
import pytest

from gobattlekit.data.effectiveness import (
    effectiveness,
    effectiveness_to_words,
    effectiveness_to_emoji,
    emoji_to_effectiveness,
)

TYPES = [
    'normal', 'fire', 'water', 'electric', 'grass', 'ice',
    'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
    'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy',
]

VALID_VALUES = {0.0, 0.5, 1.0, 2.0}

# Known immunities in Pokémon: attacker -> defender -> 0.0
IMMUNITIES = [
    ('normal', 'ghost'),
    ('electric', 'ground'),
    ('fighting', 'ghost'),
    ('poison', 'steel'),
    ('ground', 'flying'),
    ('psychic', 'dark'),
    ('ghost', 'normal'),
    ('dragon', 'fairy'),
]

# Some well-known super-effective matchups
SUPER_EFFECTIVE = [
    ('water', 'fire'),
    ('fire', 'grass'),
    ('grass', 'water'),
    ('electric', 'water'),
    ('ice', 'dragon'),
    ('fighting', 'normal'),
    ('ground', 'electric'),
    ('flying', 'fighting'),
    ('psychic', 'fighting'),
    ('bug', 'psychic'),
    ('rock', 'fire'),
    ('ghost', 'ghost'),
    ('dark', 'psychic'),
    ('steel', 'fairy'),
    ('fairy', 'dragon'),
]


class TestEffectivenessMatrix:
    def test_has_18_attacking_types(self):
        assert len(effectiveness) == 18

    def test_each_row_has_18_defending_types(self):
        for atk_type, row in effectiveness.items():
            assert len(row) == 18, f"{atk_type} has {len(row)} entries, expected 18"

    def test_all_types_present_as_attackers(self):
        for t in TYPES:
            assert t in effectiveness, f"Missing attacker type: {t}"

    def test_all_types_present_as_defenders(self):
        for t in TYPES:
            for atk_type, row in effectiveness.items():
                assert t in row, f"Missing defender type {t} in {atk_type}'s row"

    def test_all_values_valid(self):
        for atk_type, row in effectiveness.items():
            for def_type, val in row.items():
                assert val in VALID_VALUES, (
                    f"Invalid value {val} for {atk_type} -> {def_type}"
                )

    def test_no_extra_types(self):
        """No types outside the standard 18."""
        for atk_type in effectiveness:
            assert atk_type in TYPES, f"Unexpected attacker type: {atk_type}"
            for def_type in effectiveness[atk_type]:
                assert def_type in TYPES, f"Unexpected defender type: {def_type}"


class TestImmunities:
    @pytest.mark.parametrize("atk,dfn", IMMUNITIES)
    def test_immunity(self, atk, dfn):
        assert effectiveness[atk][dfn] == 0.0, f"{atk} -> {dfn} should be immune (0.0)"


class TestSuperEffective:
    @pytest.mark.parametrize("atk,dfn", SUPER_EFFECTIVE)
    def test_super_effective(self, atk, dfn):
        assert effectiveness[atk][dfn] == 2.0, f"{atk} -> {dfn} should be super effective"


class TestEffectivenessLabels:
    def test_all_effectiveness_values_have_words(self):
        for val in VALID_VALUES:
            assert val in effectiveness_to_words

    def test_all_word_values_have_emoji(self):
        for word in effectiveness_to_words.values():
            assert word in effectiveness_to_emoji

    def test_emoji_reverse_map(self):
        for word, emoji in effectiveness_to_emoji.items():
            assert emoji in emoji_to_effectiveness
            assert emoji_to_effectiveness[emoji] == word

    def test_four_categories(self):
        assert len(effectiveness_to_words) == 4
        assert len(effectiveness_to_emoji) == 4
        assert len(emoji_to_effectiveness) == 4
