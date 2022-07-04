from typing import Optional


def filter_dict(mapping: dict, keys: list[str]) -> dict:
    return {key: mapping.get(key) for key in keys}


def get_timestamp_in_us(ccxt_structure: dict) -> Optional[int]:
    if timestamp_in_ms := ccxt_structure.get("timestamp"):
        return timestamp_in_ms * 1000


def _fill_empty_keys(dictionary: dict, data: dict) -> dict:
    filled_dict = dictionary.copy()
    empty_keys = [key for key, value in dictionary.items() if value is None]
    filled_dict.update((key, data.get(key)) for key in empty_keys)
    return filled_dict


def _convert_ms_to_us(ms: int) -> int:
    return ms * 1000
