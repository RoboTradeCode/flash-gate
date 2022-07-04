def _filter_keys(dictionary: dict, keys: list[str]) -> dict:
    return {key: dictionary.get(key) for key in keys}


def _fill_empty_keys(dictionary: dict, data: dict) -> dict:
    filled_dict = dictionary.copy()
    empty_keys = [key for key, value in dictionary.items() if value is None]
    filled_dict.update((key, data.get(key)) for key in empty_keys)
    return filled_dict


def _convert_ms_to_us(ms: int) -> int:
    return ms * 1000
