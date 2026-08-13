import pytest

from diem10_api.core.option_labels import (
    mc_label_from_position,
    mc_position_from_label,
    tf_label_from_position,
    tf_position_from_label,
)


def test_mc_labels_round_trip() -> None:
    assert mc_label_from_position(1) == "A"
    assert mc_label_from_position(4) == "D"
    assert mc_position_from_label("b") == 2
    assert mc_position_from_label("D") == 4


def test_tf_labels_round_trip() -> None:
    assert tf_label_from_position(1) == "a"
    assert tf_label_from_position(4) == "d"
    assert tf_position_from_label("C") == 3
    assert tf_position_from_label("d") == 4


def test_invalid_labels_raise() -> None:
    with pytest.raises(ValueError):
        mc_label_from_position(5)
    with pytest.raises(ValueError):
        mc_position_from_label("E")
