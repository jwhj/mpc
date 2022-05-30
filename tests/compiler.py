import unittest
import random
import ast
from concurrent.futures import ThreadPoolExecutor
from circuit_utils import bits2int, int2bits
from compiler.main import ASTCompiler
from comm.multi_threading import SenderThread, ReceiverThread
from agent import Agent
from garbled_circuit import GarbledCircuitProtocol


class CompilerTest(unittest.TestCase):
    def setup_agents(self, protocol: GarbledCircuitProtocol):
        Alice = Agent()
        Alice.id = protocol.alice_id
        Alice.sender = SenderThread(Alice.id)
        Alice.receiver = ReceiverThread(Alice.id)

        Bob = Agent()
        Bob.id = protocol.bob_id
        Bob.sender = SenderThread(Bob.id)
        Bob.receiver = ReceiverThread(Bob.id)

        return Alice, Bob

    def test_1(self):
        with open('tests/demos/a+b.py', 'r') as f:
            code = f.read()
        compiler = ASTCompiler()
        circuit = compiler.compile(ast.parse(code))
        bit_length = compiler.default_bit_length

        for _ in range(10):
            x = random.randint(0, (1 << bit_length) - 1)
            y = random.randint(0, (1 << bit_length) - 1)
            result = circuit.evaluate(
                [0, 1] + int2bits(x, bit_length) + int2bits(y, bit_length)
            )
            assert (bits2int(result) - x - y) % (1 << bit_length) == 0

    def test_if_expr(self):
        with open('tests/demos/if_expr.py', 'r') as f:
            code = f.read()
        compiler = ASTCompiler()
        circuit = compiler.compile(ast.parse(code))
        bit_length = compiler.default_bit_length

        for _ in range(10):
            x = random.randint(0, (1 << bit_length) - 1)
            y = random.randint(0, (1 << bit_length) - 1)
            c = random.randint(0, 1)
            result = circuit.evaluate(
                [0, 1] + int2bits(x, bit_length) + int2bits(y, bit_length) + [c]
            )
            if c == 0:
                assert (bits2int(result) - x + y) % (1 << bit_length) == 0
            else:
                assert (bits2int(result) - x - y) % (1 << bit_length) == 0

    def test_billionaire(self):
        bit_length = 64
        with open('tests/demos/billionaire.py', 'r') as f:
            code = f.read()
        compiler = ASTCompiler()
        circuit = compiler.compile(ast.parse(code))

        for _ in range(10):
            x = random.randint(0, (1 << (bit_length - 1)) - 1)
            y = random.randint(0, (1 << (bit_length - 1)) - 1)
            result = circuit.evaluate(
                [0, 1] + int2bits(x, bit_length) + int2bits(y, bit_length)
            )
            assert bool(result[0]) == (x < y), f'\n{result}\n{x}\n{y}'

    def test_billionaire_gc(self):
        bit_length = 64
        with open('tests/demos/billionaire.py', 'r') as f:
            code = f.read()
        compiler = ASTCompiler()
        circuit = compiler.compile(ast.parse(code))

        protocol = GarbledCircuitProtocol(circuit, bit_length + 2, bit_length, 0, 1)
        Alice, Bob = self.setup_agents(protocol)

        executor = ThreadPoolExecutor(max_workers=2)
        for _ in range(10):
            x = random.randint(0, (1 << (bit_length - 1)) - 1)
            y = random.randint(0, (1 << (bit_length - 1)) - 1)
            a = executor.submit(protocol.alice, Alice, [0, 1] + int2bits(x, bit_length))
            b = executor.submit(protocol.bob, Bob, int2bits(y, bit_length))
            result = b.result()
            assert bool(result[0]) == (x < y), f'\n{result}\n{x}\n{y}'


if __name__ == '__main__':
    unittest.main()
