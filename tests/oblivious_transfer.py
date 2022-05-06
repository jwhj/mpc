import unittest
import random
from concurrent.futures import ThreadPoolExecutor

from agent import Agent
from oblivious_transfer import OT_Alice, OT_Bob
from comm.multi_threading import SenderThread, ReceiverThread


class OTTest(unittest.TestCase):
    def test_1(self):

        Alice = Agent()
        Alice.id = 0
        Alice.sender = SenderThread(Alice.id)
        Alice.receiver = ReceiverThread(Alice.id)

        Bob = Agent()
        Bob.id = 1
        Bob.sender = SenderThread(Bob.id)
        Bob.receiver = ReceiverThread(Bob.id)

        for i in range(100):
            messages = [random.randint(0, 10), random.randint(0, 10)]
            index = random.randint(0, 1)

            executor = ThreadPoolExecutor(max_workers=2)
            a = executor.submit(OT_Alice, Alice, Bob.id, messages)
            b = executor.submit(OT_Bob, Bob, Alice.id, index)
            result = b.result()
            assert result == messages[index]


if __name__ == '__main__':
    unittest.main()
