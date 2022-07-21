from decimal import Decimal, ROUND_DOWN
from typing import Union


def calc_multiplier(x) -> Decimal:
    out = to_decimal(2 ** x - decay(x))
    print(out)
    return out


def decay(x):
    if x == 1:
        return 0.06
    return pow(x, 1.05 + x / 4) / 10


def to_decimal(n: Union[int, float, str, Decimal]) -> Decimal:
    if isinstance(n, Decimal):
        return n.quantize(Decimal('.01'), ROUND_DOWN)
    else:
        return Decimal(str(n)).quantize(Decimal('.01'), ROUND_DOWN)
