import typing as typ

# ChatGPT solution.
def evaluate_condition(condition: typ.Dict[str, typ.Any], payload: typ.Dict[str, typ.Any]) -> bool:
    """
    Recursive evaluation of condition against the payload.
    Supports AND/OR nesting.
    """

    if 'AND' in condition:
        return all(evaluate_condition(sub, payload) for sub in condition['AND'])
    if 'OR' in condition:
        return any(evaluate_condition(sub, payload) for sub in condition['OR'])

    # Simple condition: field + operator + value
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")
    actual = payload.get(field)

    ops = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "contains": lambda a, b: b in a if isinstance(a, (list, str)) else False,
    }

    if operator not in ops:
        raise ValueError(f"Unsupported operator: {operator}")

    return ops[operator](actual, value)
