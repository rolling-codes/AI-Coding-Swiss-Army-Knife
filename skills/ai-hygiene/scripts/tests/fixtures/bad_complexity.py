"""A deliberately bad sample: one long, deeply nested, high-complexity function.

Used by the test suite to confirm complexity_check flags function-length,
nesting-depth, and cyclomatic violations. Not meant to be imported.
"""


def tangled(items, mode, flag, extra, limit):
    total = 0
    for item in items:
        if item is not None:
            if mode == "a":
                if flag:
                    if extra:
                        if limit > 0:
                            if item > limit:
                                total += item
                            else:
                                total -= item
                        else:
                            total += 1
                    else:
                        total += 2
                else:
                    total += 3
            elif mode == "b":
                if item % 2 == 0:
                    total += item * 2
                elif item % 3 == 0:
                    total += item * 3
                else:
                    total += item
            elif mode == "c":
                total += item and 1 or 0
            else:
                total += 0
        else:
            total -= 1
    if total > 100:
        total = 100
    elif total < -100:
        total = -100
    for _ in range(3):
        if total > 0:
            total -= 1
        elif total < 0:
            total += 1
        else:
            break
    while total > 50:
        total -= 10
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    return total
