import unittest
import csprng
from concurrent.futures import ThreadPoolExecutor
from torchvision import datasets

from agent import Agent
from garbled_circuit import GarbledCircuitProtocol
from comm.multi_threading import SenderThread, ReceiverThread

from linear.main import build_circuit, Transform


class LinearTest(unittest.TestCase):
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
        circuit, params = build_circuit('linear/linear.pt')
        transform = Transform()

        test_set = datasets.MNIST('../data', train=False)

        protocol = GarbledCircuitProtocol(circuit, 28 * 28, len(params), 0, 1)
        Alice, Bob = self.setup_agents(protocol)

        executor = ThreadPoolExecutor(max_workers=2)

        import time

        t1 = time.time()
        print('start!')
        for x, y in test_set:
            x = transform.forward(x)
            x = [0 if _ > 0 else 1 for _ in x]
            a = executor.submit(protocol.alice, Alice, x)
            break
        b = executor.submit(protocol.bob, Bob, params)
        result = b.result()
        print(y, result)

        print('elapsed: {}'.format(time.time() - t1))
        # assert result == [0]


if __name__ == '__main__':
    unittest.main()
