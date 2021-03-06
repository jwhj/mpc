import csprng
import sympy


def pwr(x, k, P):
    # compute x^k mod P
    # kuai su mi
    ans = 1
    while k:
        if k & 1:
            ans = (ans * x) % P
        x = (x * x) % P
        k >>= 1
    return ans


def gen_prime(n: int):
    while 1:
        p = csprng.randint(n, n * 2 - 1)
        p |= 1
        if p % 3 != 2:
            continue
        if sympy.isprime(p) and sympy.isprime(2 * p + 1):
            return p, 2 * p + 1


def gen_g0(n: int):
    p, q = gen_prime(n)
    while 1:
        g = csprng.randint(2, q - 2)
        if pwr(g, 2, q) != 1 and pwr(g, p, q) != 1:
            return g, q
