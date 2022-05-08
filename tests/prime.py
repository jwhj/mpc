import unittest
from prime import pwr, gen_g0


class primeTest(unittest.TestCase):
    def test_1(self):
        for i in range(100):
            g, q = gen_g0(10000)
            for i in range(1, q - 1):
                assert pwr(g, i, q) != 1


if __name__ == '__main__':
    unittest.main()
