def cast_dict(d, converter):
    """
    recursively convert fields by converter
    """
    for key, value in d:
        if isinstance(value, dict):
            d[key] = cast_dict(value, converter)
        else:
            d[key] = converter(value)
    return d
