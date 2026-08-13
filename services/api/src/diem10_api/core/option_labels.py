_MC_LABELS = ("A", "B", "C", "D")
_TF_LABELS = ("a", "b", "c", "d")


def mc_label_from_position(position: int) -> str:
    if position < 1 or position > len(_MC_LABELS):
        msg = f"MC option position must be 1-{len(_MC_LABELS)}, got {position}"
        raise ValueError(msg)
    return _MC_LABELS[position - 1]


def mc_position_from_label(label: str) -> int:
    normalized = label.strip().upper()
    try:
        return _MC_LABELS.index(normalized) + 1
    except ValueError as exc:
        msg = f"Invalid MC option label: {label!r}"
        raise ValueError(msg) from exc


def tf_label_from_position(position: int) -> str:
    if position < 1 or position > len(_TF_LABELS):
        msg = f"TF statement position must be 1-{len(_TF_LABELS)}, got {position}"
        raise ValueError(msg)
    return _TF_LABELS[position - 1]


def tf_position_from_label(label: str) -> int:
    normalized = label.strip().lower()
    try:
        return _TF_LABELS.index(normalized) + 1
    except ValueError as exc:
        msg = f"Invalid TF statement label: {label!r}"
        raise ValueError(msg) from exc
