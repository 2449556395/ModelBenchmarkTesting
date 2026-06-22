def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = int(round((len(values) - 1) * p))
    return values[k]
