import unittest
from comm.multi_threading import SenderThread, ReceiverThread


class MailboxTest(unittest.TestCase):
    def test_1(self):
        sender = SenderThread(0)
        receiver = ReceiverThread(1)
        for i in range(10):
            sender.send(1, i)
        for i in range(10):
            sender_id, msg = receiver.receive()
            assert sender_id == 0 and msg == i

    def test_2(self):
        sender = SenderThread(0)
        receiver = ReceiverThread(1)
        sender.send(1, 0)
        sender.send(1, 1)
        sender_id, msg = receiver.receive()
        assert sender_id == 0 and msg == 0
        sender.send(1, 2)
        sender_id, msg = receiver.receive()
        assert sender_id == 0 and msg == 1
        sender_id, msg = receiver.receive()
        assert sender_id == 0 and msg == 2


if __name__ == '__main__':
    unittest.main()
