import random
import hashlib

from typing import List, Any
from agent import Agent
from prime import pwr, gen_g0

# Bellare-Micali Construction
# https://crypto.stanford.edu/pbc/notes/crypto/ot.html


def H(x):
    s = hashlib.sha256()
    s.update(str(x).encode())
    h = int(s.hexdigest(), base=16)
    # print(x,str(x).encode(), s.hexdigest(), h)
    return h


class ObliviousTransferProtocol:
    P: int
    g0: int
    alice_id: Any
    bob_id: Any

    def __init__(self, n=1e50) -> None:
        # TODO:
        self.g0, self.P = gen_g0(n)

    def alice(self, agent: Agent, messages: List[int]):
        assert len(messages) == 2

        # import pdb
        # pdb.set_trace()
        # A publish a random c from G
        c = random.randint(1, self.P - 1)
        agent.sender.send(self.bob_id, c)
        PK = [None, None]
        _, PK[0] = agent.receiver.receive()
        _, PK[1] = agent.receiver.receive()
        assert (PK[0] * PK[1]) % self.P == c
        # A encrypts x0,x1 with El Gamal
        C = [None, None]
        for i in range(2):
            r = random.randint(0, self.P - 2)
            C[i] = (pwr(self.g0, r, self.P), H(pwr(PK[i], r, self.P)) ^ messages[i])
        agent.sender.send(self.bob_id, C[0])
        agent.sender.send(self.bob_id, C[1])

    def bob(self, agent: Agent, index: int):
        assert index in [0, 1]

        # A publish a random c
        _, c = agent.receiver.receive()
        # B pick k from Z_p, and sends PK0, PK1 to A
        k = random.randint(0, self.P - 1)
        PK = [None, None]
        PK[index] = pwr(self.g0, k, self.P)
        PK[1 - index] = c * pwr(self.g0, self.P - 1 - k, self.P) % self.P
        agent.sender.send(self.alice_id, PK[0])
        agent.sender.send(self.alice_id, PK[1])
        # B receive C0, C1
        C = [None, None]
        _, C[0] = agent.receiver.receive()
        _, C[1] = agent.receiver.receive()
        # B decrypts Cb
        V1, V2 = C[index]
        return H(pwr(V1, k, self.P)) ^ V2
