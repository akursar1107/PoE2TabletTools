"""Tests for snapshot differ classification."""

from poe_tablet_tool.differ import MIN_SNAPSHOTS_FOR_SOLD, RELIST_PRICE_TOLERANCE


def test_relist_detection():
    """Test relist detection price tolerance constant."""
    assert RELIST_PRICE_TOLERANCE > 0
    assert RELIST_PRICE_TOLERANCE <= 0.5  # Should be reasonable


def test_min_snapshots_constant():
    """Verify the MIN_SNAPSHOTS_FOR_SOLD constant."""
    assert MIN_SNAPSHOTS_FOR_SOLD >= 1


def test_classification_constants_exist():
    """Verify key classification constants are defined."""
    from poe_tablet_tool.differ import PRICE_UPDATE_THRESHOLD, MAX_VISIBILITY_DURATION_HOURS
    assert PRICE_UPDATE_THRESHOLD > RELIST_PRICE_TOLERANCE
    assert MAX_VISIBILITY_DURATION_HOURS > 0
