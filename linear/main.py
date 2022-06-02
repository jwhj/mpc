import torch
from torchvision import datasets, transforms
import matplotlib.pylab as plt
import math
import numpy as np
from typing import List

from circuit import Circuit, Wire
from circuit_utils import bits2int, int2bits
from circuit_utils.gates import And, Not, Xor
from circuit_utils.modules import Add, Negate, Select, Lt


def bits2int_signed(bits: List[int]) -> int:
    n = len(bits)
    x = bits2int(bits)
    if x >= (1 << (n - 1)):
        x -= 1 << n
    return x


# def get_bits(x, bit_length):
#     x = int(x)
#     ret = [1 if x & (1 << i) else 0 for i in range(bit_length)]
#     return ret


def get_wires1d(x, bit_length=1):
    n = x.shape[0]
    wires = []
    params = []
    for i in range(n):
        t = int(x[i])
        wires.extend([Wire() for _ in range(bit_length)])
        params.extend(int2bits(t, bit_length))
    return wires, params


def get_wires2d(x, bit_length=1):
    n, m = x.shape
    wires = []
    params = []
    for i in range(n):
        for j in range(m):
            t = int(x[i, j])
            wires.extend([Wire() for _ in range(bit_length)])
            params.extend(int2bits(t, bit_length))
    return wires, params


class Fc:
    def __init__(self, in_c, out_c) -> None:
        self.in_c = in_c
        self.out_c = out_c
        self.weight = torch.zeros(out_c, in_c)
        self.bias = torch.zeros(out_c)

    def load(self, weight, bias):
        self.weight = weight.clone()
        self.bias = bias.clone()
        self.bias = (self.bias * 100000).trunc()
        self.weight = (self.weight * 100000).trunc()

    def forward(self, x):
        ret = torch.zeros(self.out_c)
        for i in range(self.out_c):
            ret[i] = torch.dot(x, self.weight[i])
            # for j in range(self.in_c):
            #     ret[i] = ret[i] + (x[j] * self.weight[i,j])
            ret[i] = ret[i] + self.bias[i]
        return ret

    def parameters(self):

        bit_length = 32
        self.wires = {}
        self.params = {}
        self.wires['weight'], self.params['weight'] = get_wires2d(
            self.weight, bit_length
        )
        self.wires['bias'], self.params['bias'] = get_wires1d(self.bias, bit_length)

        wires = [y for x in self.wires.values() for y in x]
        params = [y for x in self.params.values() for y in x]
        return wires, params

    def build_circuit(self, circuit: Circuit, x: List[Wire], zero, one):
        bit_length = 32

        ret = []
        for i in range(self.out_c):
            adder = self.wires['bias'][i * bit_length : (i + 1) * bit_length]
            for j in range(self.in_c):
                t = i * self.in_c + j
                pos = self.wires['weight'][t * bit_length : (t + 1) * bit_length]
                neg = Negate(circuit, bit_length, one, pos).out
                tmp = [
                    Select(circuit, pos[_], neg[_], x[j]).out for _ in range(bit_length)
                ]
                adder = Add(circuit, bit_length, adder, tmp).out
            ret.append(adder)
        # print(self.weight[:, 0])
        # print(self.bias)

        return ret


class Net:
    def __init__(self) -> None:
        self.fc = Fc(784, 10)

    def load(self, c):
        self.fc.load(
            c['fc.weight'],
            c['fc.bias'],
        )

    def forward(self, x):
        x = self.fc.forward(x)
        return x

    def parameters(self):
        modules = ['fc']
        wires = []
        params = []
        for module in modules:
            _wires, _params = getattr(self, module).parameters()
            wires.extend(_wires)
            params.extend(_params)
        return wires, params

    def build_circuit(self, circuit: Circuit, x: List[Wire], zero, one):
        x = self.fc.build_circuit(circuit, x, zero, one)
        bit_length = 32
        ret = []
        for i in range(10):
            now = one
            for j in range(10):
                if i != j:
                    tmp = Lt(circuit, bit_length, one, x[j], x[i]).out[0]
                    out = Wire()
                    circuit.add_wire(out)
                    circuit.add_gate(And(now, tmp, out))
                    now = out
            ret.append(now)
        return ret


class BinarizeTransform:
    def __init__(self, th=0.5) -> None:
        self.th = th

    def __call__(self, x):
        return (x > self.th).float() * 2 - 1


class Transform:
    def __init__(self) -> None:
        self.t = transforms.Compose([transforms.ToTensor(), BinarizeTransform()])

    def forward(self, x):
        x = self.t(x)
        x = x.view(-1)
        return x


def build_circuit(load_path):
    checkpoint = torch.load(load_path, map_location='cpu')
    model = Net()
    model.load(checkpoint)
    circuit = Circuit()
    input = [Wire() for _ in range(28 * 28)]
    zero = Wire()
    one = Wire()

    [circuit.add_wire(_) for _ in input]
    circuit.add_wire(zero)
    circuit.add_wire(one)

    param_wires, params = model.parameters()
    [circuit.add_wire(_) for _ in param_wires]

    circuit.inputs = input + param_wires + [zero, one]
    circuit.outputs = []
    output = model.build_circuit(circuit, input, zero, one)
    circuit.outputs = output
    # for _ in output:
    #     circuit.outputs.extend(_)
    return circuit, params + [0, 1]


def eval():
    checkpoint = torch.load('linear/linear.pt', map_location='cpu')
    model = Net()
    model.load(checkpoint)
    transform = Transform()

    test_set = datasets.MNIST('../data', train=False)

    cnt, pos = 0, 0
    for x, y in test_set:
        x = transform.forward(x)
        # plt.imshow(x.reshape(28,28).numpy())
        # plt.show()
        # plt.close()
        p = model.forward(x)
        cnt += 1
        pos += p.argmax().item() == y
        print(cnt, pos, pos / cnt)


if __name__ == '__main__':
    circuit, params = build_circuit('linear/linear.pt')
    transform = Transform()

    test_set = datasets.MNIST('../data', train=False)
    cnt, pos = 0, 0
    for x, y in test_set:
        x = transform.forward(x)
        x = [0 if _ > 0 else 1 for _ in x]
        p = circuit.evaluate(x + params)
        print(y, p)
        # bit_length = 32
        # p = [
        #     bits2int_signed(p[i * bit_length : (i + 1) * bit_length]) for i in range(10)
        # ]
        # p = np.array(p)
        # cnt += 1
        # pos += p.argmax().item() == y
        # print(cnt, pos, pos / cnt)
