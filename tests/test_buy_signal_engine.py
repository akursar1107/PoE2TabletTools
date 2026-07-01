"""Tests for buy_signal_engine utility functions."""

from poe_tablet_tool.buy_signal_engine import _median, _pair_key


# ---------------------------------------------------------------------------
# _median
# ---------------------------------------------------------------------------


def test_median_empty():
    assert _median([]) is None


def test_median_single():
    assert _median([3.0]) == 3.0


def test_median_odd():
    assert _median([1.0, 2.0, 3.0]) == 2.0


def test_median_even():
    assert _median([1.0, 2.0, 3.0, 4.0]) == 2.5


def test_median_unsorted():
    assert _median([5.0, 1.0, 3.0]) == 3.0


def test_median_duplicates():
    assert _median([2.0, 2.0, 2.0]) == 2.0


def test_median_two_elements():
    assert _median([4.0, 6.0]) == 5.0


# ---------------------------------------------------------------------------
# _pair_key
# ---------------------------------------------------------------------------


def test_pair_key_is_sorted():
    """Key should be the same regardless of argument order."""
    k1 = _pair_key("mod_b", "mod_a")
    k2 = _pair_key("mod_a", "mod_b")
    assert k1 == k2


def test_pair_key_format():
    key = _pair_key("mod_a", "mod_b")
    assert key == "mod_a|mod_b"


def test_pair_key_same_mod():
    key = _pair_key("mod_x", "mod_x")
    assert key == "mod_x|mod_x"


def test_pair_key_preserves_pipe_separator():
    key = _pair_key("z", "a")
    assert "|" in key
    assert key.startswith("a|")
