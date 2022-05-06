import unittest
import random
from concurrent.futures import ThreadPoolExecutor

from agent import Agent
from oblivious_transfer import ObliviousTransferProtocol
from comm.multi_threading import SenderThread, ReceiverThread


class OTTest(unittest.TestCase):
    def test_1(self):

        protocol = ObliviousTransferProtocol()
        protocol.alice_id = 0
        protocol.bob_id = 1

        Alice = Agent()
        Alice.id = protocol.alice_id
        Alice.sender = SenderThread(Alice.id)
        Alice.receiver = ReceiverThread(Alice.id)

        Bob = Agent()
        Bob.id = protocol.bob_id
        Bob.sender = SenderThread(Bob.id)
        Bob.receiver = ReceiverThread(Bob.id)

        for i in range(100):
            messages = [random.randint(0, 10), random.randint(0, 10)]
            index = random.randint(0, 1)

            executor = ThreadPoolExecutor(max_workers=2)
            a = executor.submit(protocol.alice, Alice, messages)
            b = executor.submit(protocol.bob, Bob, index)
            result = b.result()
            assert result == messages[index]


if __name__ == '__main__':
    unittest.main()
