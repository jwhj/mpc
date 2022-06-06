import ast
import random
from concurrent.futures import ThreadPoolExecutor
from circuit_utils import int2bits
from comm.multi_threading import SenderThread, ReceiverThread
from agent import Agent
from garbled_circuit import GarbledCircuitProtocol
from compiler.main import ASTCompiler


def main():
    with open('demo/scripts/billionaire.py', 'r') as f:
        code = f.read()
    compiler = ASTCompiler()
    circuit = compiler.compile(ast.parse(code))

    bit_length = 64
    protocol = GarbledCircuitProtocol(circuit, bit_length + 3, bit_length, 0, 1)

    Alice = Agent()
    Alice.id = protocol.alice_id
    Alice.sender = SenderThread(Alice.id)
    Alice.receiver = ReceiverThread(Alice.id)

    Bob = Agent()
    Bob.id = protocol.bob_id
    Bob.sender = SenderThread(Bob.id)
    Bob.receiver = ReceiverThread(Bob.id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        alice_asset = random.randint(0, (1 << (bit_length - 1)) - 1)
        if random.randint(0, 1):
            bob_asset = random.randint(0, (1 << (bit_length - 1)) - 1)
        else:
            bob_asset = alice_asset
        flag = random.randint(0, 1)
        print(
            'Alice: {}\n  Bob: {}\n Type: {}'.format(
                alice_asset, bob_asset, 'Le' if flag else 'Lt'
            )
        )
        a = executor.submit(
            protocol.alice, Alice, [0, 1] + int2bits(alice_asset, bit_length) + [flag]
        )
        b = executor.submit(protocol.bob, Bob, int2bits(bob_asset, bit_length))
        print(b.result())


if __name__ == '__main__':
    main()
