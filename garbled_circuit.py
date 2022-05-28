from typing import List, Any
from agent import Agent
from circuit import Circuit, Wire
from oblivious_transfer import H, ObliviousTransferProtocol
import queue, random


def gen_binary_string(len):
    ret = ''.join([random.choice(['0', '1']) for i in range(len)])
    return ret


def int2str(x):
    return bin(x)[2:]


def str2int(x):
    return int(x, 2)


class GarbledCircuitProtocol:
    alice_id: Any
    bob_id: Any
    circuit: Circuit
    n_Alice_bits: int
    n_Bob_bits: int
    OT: ObliviousTransferProtocol

    def __init__(self, circuit, n_Alice_bits, n_Bob_bits, alice_id, bob_id) -> None:
        self.circuit = circuit
        self.n_Alice_bits = n_Alice_bits
        self.n_Bob_bits = n_Bob_bits
        self.OT = ObliviousTransferProtocol()
        self.alice_id, self.bob_id = alice_id, bob_id
        self.OT.alice_id, self.OT.bob_id = alice_id, bob_id

    def alice(
        self,
        agent: Agent,
        input_bits: List[int],
    ):

        n = len(self.circuit.gates)
        m = len(self.circuit.wires)

        wire_labels = []
        for i in range(m):
            k0, p0 = gen_binary_string(128), random.randint(0, 1)
            k1, p1 = gen_binary_string(128), 1 - p0
            wire_labels.append([k0 + int2str(p0), k1 + int2str(p1)])

        garbled_tables_for_gates = []

        for gate in self.circuit.gates:
            assert len(gate.inputs) == 2
            w_a, w_b = gate.inputs
            w_c = gate.output
            table_e = [''] * 4
            for v_a, v_b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                k_a, p_a = (
                    wire_labels[w_a.index][v_a][:-1],
                    wire_labels[w_a.index][v_a][-1],
                )

                k_b, p_b = (
                    wire_labels[w_b.index][v_b][:-1],
                    wire_labels[w_b.index][v_b][-1],
                )

                e = int2str(
                    str2int(H(k_a + k_b + int2str(gate.index)))
                    ^ str2int(wire_labels[w_c.index][gate.evaluate([v_a, v_b])])
                )
                table_e[str2int(p_a + p_b)] = e

            garbled_tables_for_gates.append(table_e)

        garbled_tables_for_outputs = []
        for output_wire in self.circuit.outputs:
            table_e = [''] * 2
            for v in [0, 1]:
                k_v, p_v = wire_labels[output_wire.index][v][:-1], str2int(
                    wire_labels[output_wire.index][v][-1]
                )
                assert output_wire.input is not None
                gate = output_wire.input
                e = int2str(str2int(H(k_v + 'out' + int2str(gate.index))[-1]) ^ v)
                table_e[v] = e
            garbled_tables_for_outputs.append(table_e)

        inputs_labels = []
        for i in range(self.n_Alice_bits):
            wire, bit = self.circuit.inputs[i], input_bits[i]
            inputs_labels.append(wire_labels[wire.index][bit])

        agent.sender.send(self.bob_id, garbled_tables_for_gates)
        agent.sender.send(self.bob_id, garbled_tables_for_outputs)
        agent.sender.send(self.bob_id, inputs_labels)
        for i in range(self.n_Bob_bits):
            wire = self.circuit.inputs[self.n_Alice_bits + i]
            self.OT.alice(
                agent,
                [
                    str2int(wire_labels[wire.index][0]),
                    str2int(wire_labels[wire.index][1]),
                ],
            )

        _, ret = agent.receiver.receive()
        return ret

    def bob(
        self,
        agent: Agent,
        input_bits: List[int],
    ):
        _, garbled_tables_for_gates = agent.receiver.receive()
        _, garbled_tables_for_outputs = agent.receiver.receive()
        _, inputs_labels_A = agent.receiver.receive()

        inputs_labels_B = []
        for i in range(self.n_Bob_bits):
            wire = self.circuit.inputs[self.n_Alice_bits + i]
            inputs_labels_B.append(self.OT.bob(agent, input_bits[i]))

        inputs_labels = inputs_labels_A + inputs_labels_B
        assert len(inputs_labels) == self.n_Alice_bits + self.n_Bob_bits

        n = len(self.circuit.gates)
        m = len(self.circuit.wires)
        edges: List[List] = [[] for i in range(n)]
        in_deg: List[int] = [0] * n
        wire_ret: List[str] = [''] * m
        for wire in self.circuit.wires:
            if wire.input is not None:
                for out_gate in wire.outputs:
                    if out_gate is not None:
                        edges[wire.input.index].append(out_gate.index)
                        in_deg[out_gate.index] += 1
        q = queue.Queue()
        for i in range(len(self.circuit.inputs)):
            wire_ret[self.circuit.inputs[i].index] = inputs_labels[i]
            q.put(self.circuit.inputs[i])

        while q.not_empty():
            wire = q.get()
            for out_gate in wire.outputs:
                if out_gate is not None:
                    in_deg[out_gate.index] -= 1
                    if in_deg[out_gate.index] == 0:
                        assert len(out_gate.inputs) == 2
                        w_a, w_b = out_gate.inputs
                        w_c = out_gate.output
                        k_a, p_a = wire_ret[w_a.index][:-1], wire_ret[w_a.index][-1]
                        k_b, p_b = wire_ret[w_b.index][:-1], wire_ret[w_b.index][-1]

                        wire_ret[out_gate.output.index] = int2str(
                            str2int(H(k_a + k_b + int2str(out_gate.index)))
                            ^ str2int(
                                garbled_tables_for_gates[out_gate.index][
                                    str2int(p_a + p_b)
                                ]
                            )
                        )
                        q.put(out_gate.output)

        output_bits = [
            str2int(
                H(
                    wire_ret[output_wire.index][:-1]
                    + 'out'
                    + int2str(output_wire.input.index)
                )[-1]
            )
            ^ str2int(
                garbled_tables_for_outputs[output_wire.index][
                    wire_ret[output_wire.index][-1]
                ]
            )
            for output_wire in self.circuit.outputs
        ]
        agent.sender.send(self.alice_id, output_bits)
        return output_bits
