import random
import hashlib

from typing import List
from agent import Agent

# Bellare-Micali Construction
# https://crypto.stanford.edu/pbc/notes/crypto/ot.html

P = 998244353
g0 = 3


def pwr(x, k):
    # compute x^k mod P
    # kuai su mi
    ans = 1
    while k:
        if k & 1:
            ans = (ans * x) % P
        x = (x * x) % P
        k >>= 1
    return ans


def H(x):
    s = hashlib.sha256()
    s.update(str(x).encode())
    h = int(s.hexdigest(), base=16)
    # print(x,str(x).encode(), s.hexdigest(), h)
    return h


def OT_Alice(agent: Agent, bob_id, messages: List[int]):
    assert len(messages) == 2

    # import pdb
    # pdb.set_trace()
    # A publish a random c from G
    c = random.randint(1, P - 1)
    agent.sender.send(bob_id, c)
    PK = [None, None]
    _, PK[0] = agent.receiver.receive()
    _, PK[1] = agent.receiver.receive()
    assert (PK[0] * PK[1]) % P == c
    # A encrypts x0,x1 with El Gamal
    C = [None, None]
    for i in range(2):
        r = random.randint(0, P - 2)
        C[i] = (pwr(g0, r), H(pwr(PK[i], r)) ^ messages[i])
    agent.sender.send(bob_id, C[0])
    agent.sender.send(bob_id, C[1])


def OT_Bob(agent: Agent, alice_id, index: int):
    assert index in [0, 1]

    # A publish a random c
    _, c = agent.receiver.receive()
    # B pick k from Z_p, and sends PK0, PK1 to A
    k = random.randint(0, P - 1)
    PK = [None, None]
    PK[index] = pwr(g0, k)
    PK[1 - index] = c * pwr(g0, P - 1 - k) % P
    agent.sender.send(alice_id, PK[0])
    agent.sender.send(alice_id, PK[1])
    # B receive C0, C1
    C = [None, None]
    _, C[0] = agent.receiver.receive()
    _, C[1] = agent.receiver.receive()
    # B decrypts Cb
    V1, V2 = C[index]
    return H(pwr(V1, k)) ^ V2
