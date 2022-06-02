import torch
from torchvision import datasets, transforms
import matplotlib.pylab as plt
import math
import numpy as np
from typing import List

from circuit import Circuit, Wire
from circuit_utils.gates import Not, Xor
from circuit_utils.modules import Add, Negate


def get_bits(x, bit_length):
    ret = [1 if x & (1 << i) else 0 for i in range(bit_length)]
    return ret


def get_wires1d(x, bit_length=1):
    n = x.shape[0]
    wires = []
    params = []
    for i in range(n):
        t = x[i]
        wires.extend([Wire() for _ in range(bit_length)])
        params.extend(get_bits(t, bit_length))
    return wires, params


def get_wires2d(x, bit_length=1):
    n, m = x.shape
    wires = []
    params = []
    for i in range(n):
        for j in range(m):
            t = x[i, j]
            wires.extend([Wire() for _ in range(bit_length)])
            params.extend(get_bits(t, bit_length))
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
        self.bias = self.bias.trunc()
        self.weight = (self.weight * 100000).trunc()

    def forward(self, x):
        ret = torch.zeros(self.out_c)
        for i in range(self.out_c):
            ret[i] = torch.dot(x, self.weight[i])
            # for j in range(self.in_c):
            #     ret[i] = ret[i] + (x[j] * self.weight[i,j])
            ret[i] = ret[i] + self.bias[i]
        return ret


class Block:
    def __init__(self, in_c, out_c) -> None:
        self.in_c = in_c
        self.out_c = out_c
        self.weight = torch.zeros(out_c, in_c)
        self.bias = torch.zeros(out_c)
        self.bn_weight = torch.zeros(out_c)
        self.bn_bias = torch.zeros(out_c)
        self.bn_mean = torch.zeros(out_c)
        self.bn_var = torch.zeros(out_c)

    def load(self, weight, bias, bn_weight, bn_bias, bn_mean, bn_var):
        self.weight = weight.clone()
        self.bias = bias.clone()
        self.bn_weight = bn_weight.clone()
        self.bn_bias = bn_bias.clone()
        self.bn_mean = bn_mean.clone()
        self.bn_var = bn_var.clone()

        self.s = self.bn_weight < 0  # bn_weight != 0
        self.b = (
            self.bias
            - self.bn_mean
            + self.bn_bias * torch.sqrt(self.bn_var) / self.bn_weight
        )  # bn_weight != 0
        self.b = self.b.trunc()

    def forward(self, x):
        ret = torch.zeros(self.out_c)
        for i in range(self.out_c):
            # ret[i] = torch.dot(x, self.weight[i])
            for j in range(self.in_c):
                ret[i] = ret[i] + (x[j] * self.weight[i, j])
            if 0:
                ret[i] = ret[i] + self.bias[i]
                ret[i] = (ret[i] - self.bn_mean[i]) / math.sqrt(
                    self.bn_var[i]
                ) * self.bn_weight[i] + self.bn_bias[i]
                ret[i] = 1 if ret[i] > 0 else -1
            else:
                ret[i] = ret[i] + self.b[i]
                ret[i] = 1 if (ret[i] > 0) ^ self.s[i] else -1
        return ret

    def parameters(self):
        # print(self.weight)
        # print(self.s)
        # print(self.b)

        bit_length = 16
        self.wires = {}
        self.params = {}
        self.wires['weight'], self.params['weight'] = get_wires2d(self.weight)
        self.wires['s'], self.params['s'] = get_wires1d(self.s)
        self.wires['b'], self.params['b'] = get_wires1d(self.b, bit_length)

        wires = [y for x in self.wires.values() for y in x]
        params = [y for x in self.params.values() for y in x]
        return wires, params

    def build_circuit(self, circuit: Circuit, x: List[Wire]):
        bit_length = 16
        ret = [Wire() for _ in range(self.out_c)]
        for _ in ret:
            circuit.add_wire(_)

        for i in range(self.out_c):
            carry = [Wire() for _ in range(bit_length)]
            circuit.add_wire(carry)
            for j in range(self.in_c):
                tmp = Wire()
                circuit.add_wire(tmp)
                circuit.add_gate(
                    Xor(x[j], self.wires['weight'][i * self.in_c + j], tmp)
                )
                # TODO
                # tmp1 = carry + tmp
                carry = tmp1

            # ret[i] = ret[i] + self.b[i]
            tmp = [Wire() for _ in range(bit_length)]
            circuit.add_wire(tmp)
            circuit.add_gate(
                Add(carry, self.wires['b'][i * bit_length : (i + 1) * bit_length], tmp)
            )
            carry = tmp

            ret[i] = 1 if (ret[i] > 0) ^ self.s[i] else -1
        return ret


class BNN:
    def __init__(self) -> None:
        self.infl_ratio = 1
        self.block1 = Block(784, 2048 * self.infl_ratio)
        self.block2 = Block(2048 * self.infl_ratio, 2048 * self.infl_ratio)
        self.block3 = Block(2048 * self.infl_ratio, 2048 * self.infl_ratio)
        self.fc = Fc(2048 * self.infl_ratio, 10)

    def load(self, c):
        self.block1.load(
            c['fc1.weight'],
            c['fc1.bias'],
            c['bn1.weight'],
            c['bn1.bias'],
            c['bn1.running_mean'],
            c['bn1.running_var'],
        )
        self.block2.load(
            c['fc2.weight'],
            c['fc2.bias'],
            c['bn2.weight'],
            c['bn2.bias'],
            c['bn2.running_mean'],
            c['bn2.running_var'],
        )
        self.block3.load(
            c['fc3.weight'],
            c['fc3.bias'],
            c['bn3.weight'],
            c['bn3.bias'],
            c['bn3.running_mean'],
            c['bn3.running_var'],
        )
        self.fc.load(
            c['fc4.weight'],
            c['fc4.bias'],
        )

    def forward(self, x):
        x = self.block1.forward(x)
        x = self.block2.forward(x)
        x = self.block3.forward(x)
        x = self.fc.forward(x)
        return x

    def parameters(self):
        modules = ['block1', 'block2', 'block3', 'fc']
        wires = []
        params = []
        for module in modules:
            _wires, _params = getattr(self, module).parameters()
            wires.extend(_wires)
            params.extend(_params)
        return wires, params

    def build_circuit(self, circuit):
        pass


class BinarizeTransform:
    def __init__(self, th=0.5) -> None:
        self.th = th

    def __call__(self, x):
        return (x > self.th).float() * 2 - 1


class Transform:
    def __init__(self) -> None:
        self.t = transforms.Compose(
            [
                transforms.ToTensor(),
                BinarizeTransform()
                #    transforms.Normalize((0.1307,), (0.3081,))
            ]
        )

    def forward(self, x):
        x = self.t(x)
        x = x.view(-1)
        return x


def build_circuit(load_path):
    checkpoint = torch.load(load_path, map_location='cpu')
    model = BNN()
    model.load(checkpoint)
    circuit = Circuit()
    input = [Wire() for _ in range(28 * 28)]
    parameters = model.parameters()
    output = [Wire() for _ in range(10)]


def eval():
    checkpoint = torch.load('bnn/checkpoint.pt', map_location='cpu')
    model = BNN()
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
    # build_circuit('bnn/checkpoint.pt')
    eval()
