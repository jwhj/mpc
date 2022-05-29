import unittest
import random
from concurrent.futures import ThreadPoolExecutor

from agent import Agent
from circuit import AndGate, Circuit, Wire
from circuit_utils import int2bits, bits2int
from circuit_utils.modules import Adder
from oblivious_transfer import ObliviousTransferProtocol
from garbled_circuit import GarbledCircuitProtocol
from comm.multi_threading import SenderThread, ReceiverThread


class GCTest(unittest.TestCase):
    def test_1(self):

        circuit = Circuit()
        w_a, w_b, w_c = Wire(), Wire(), Wire()
        g = AndGate(w_a, w_b, w_c)
        w_a.outputs = w_b.outputs = [g]
        w_c.input = g

        w_a.index, w_b.index, w_c.index = 0, 1, 2
        g.index = 0

        circuit.wires = [w_a, w_b, w_c]
        circuit.gates = [g]
        circuit.inputs = [w_a, w_b]
        circuit.outputs = [w_c]

        protocol = GarbledCircuitProtocol(circuit, 1, 1, 0, 1)

        Alice = Agent()
        Alice.id = protocol.alice_id
        Alice.sender = SenderThread(Alice.id)
        Alice.receiver = ReceiverThread(Alice.id)

        Bob = Agent()
        Bob.id = protocol.bob_id
        Bob.sender = SenderThread(Bob.id)
        Bob.receiver = ReceiverThread(Bob.id)

        executor = ThreadPoolExecutor(max_workers=2)
        a = executor.submit(protocol.alice, Alice, [0])
        b = executor.submit(protocol.bob, Bob, [1])
        result = b.result()
        print(result)
        assert result == [0]

    def test_add(self):
        bit_length = 64
        circuit = Circuit()
        adder = Adder(circuit, bit_length)
        circuit.inputs = adder.in_0 + adder.in_1
        circuit.outputs = adder.out

        protocol = GarbledCircuitProtocol(circuit, bit_length, bit_length, 0, 1)

        Alice = Agent()
        Alice.id = protocol.alice_id
        Alice.sender = SenderThread(Alice.id)
        Alice.receiver = ReceiverThread(Alice.id)

        Bob = Agent()
        Bob.id = protocol.bob_id
        Bob.sender = SenderThread(Bob.id)
        Bob.receiver = ReceiverThread(Bob.id)

        executor = ThreadPoolExecutor(max_workers=2)
        for _ in range(10):
            x = random.randint(0, (1 << bit_length) - 1)
            y = random.randint(0, (1 << bit_length) - 1)
            a = executor.submit(protocol.alice, Alice, int2bits(x, bit_length))
            b = executor.submit(protocol.bob, Bob, int2bits(y, bit_length))
            result = b.result()
            assert bits2int(result) == (x + y) % (1 << bit_length)


if __name__ == '__main__':
    unittest.main()
