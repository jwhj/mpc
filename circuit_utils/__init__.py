from typing import List


def int2bits(x: int, bit_length: int) -> List[int]:
    result = []
    for _ in range(bit_length):
        result.append(x % 2)
        x >>= 1
    return result


def bits2int(bits: List[int]) -> int:
    return sum(x * (1 << i) for i, x in enumerate(bits))
