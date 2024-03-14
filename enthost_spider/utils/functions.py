def strip(string: str, default=None):
    if string is None:
        return default
    if not isinstance(string, str):
        return string
    return string.strip() or default
