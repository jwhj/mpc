from typing import List, Any
from agent import Agent
from circuit import Circuit, Wire
from circuit_utils.gates import Xor
from oblivious_transfer import H, ObliviousTransferProtocol
import queue, csprng


def gen_binary_string(len):
    ret = ''.join([csprng.choice(['0', '1']) for i in range(len)])
    return ret


def int2str(x, length=None):
    ret = bin(x)[2:]
    if length is not None:
        return ''.join(['0'] * (length - len(ret)) + [ret])
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

    def __init__(
        self,
        circuit,
        n_Alice_bits,
        n_Bob_bits,
        alice_id,
        bob_id,
        security_param=128,
        enable_GRR=True,
        enable_freeXOR=True,
    ) -> None:
        self.circuit = circuit
        self.n_Alice_bits = n_Alice_bits
        self.n_Bob_bits = n_Bob_bits
        self.OT = ObliviousTransferProtocol(1 << (security_param + 1))
        self.alice_id, self.bob_id = alice_id, bob_id
        self.OT.alice_id, self.OT.bob_id = alice_id, bob_id
        self.security_param = security_param
        self.enable_GRR = enable_GRR
        self.enable_freeXOR = enable_freeXOR

    def alice(
        self,
        agent: Agent,
        input_bits: List[int],
    ):

        n = len(self.circuit.gates)
        m = len(self.circuit.wires)

        if self.enable_freeXOR:
            Delta = str2int(gen_binary_string(self.security_param))
        wire_labels = []
        for i in range(m):
            k0, p0 = (
                str2int(gen_binary_string(self.security_param)),
                csprng.randint(0, 1),
            )
            if self.enable_freeXOR:
                k1, p1 = (k0 ^ Delta, p0 ^ 1)
            else:
                k1, p1 = (str2int(gen_binary_string(self.security_param)), p0 ^ 1)
            wire_labels.append([k0 << 1 | p0, k1 << 1 | p1])

        garbled_tables_for_gates = []

        for gate in self.circuit.gates:
            assert len(gate.inputs) == 2
            w_a, w_b = gate.inputs
            w_c = gate.output

            if self.enable_freeXOR and isinstance(gate, Xor):
                wire_labels[w_c.index][0] = (
                    wire_labels[w_a.index][0] ^ wire_labels[w_b.index][0]
                )
                wire_labels[w_c.index][1] = wire_labels[w_c.index][0] ^ (Delta << 1 | 1)
                garbled_tables_for_gates.append(None)
            elif self.enable_GRR:
                for v_a, v_b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    k_a, p_a = (
                        wire_labels[w_a.index][v_a] >> 1,
                        wire_labels[w_a.index][v_a] & 1,
                    )

                    k_b, p_b = (
                        wire_labels[w_b.index][v_b] >> 1,
                        wire_labels[w_b.index][v_b] & 1,
                    )
                    if p_a == 1 and p_b == 1:
                        ret = gate.evaluate([v_a, v_b])
                        wire_labels[w_c.index][ret] = H(
                            int2str(k_a, self.security_param)
                            + int2str(k_b, self.security_param)
                            + int2str(gate.index)
                        )
                        wire_labels[w_c.index][ret ^ 1] = wire_labels[w_c.index][
                            ret
                        ] ^ (Delta << 1 | 1)
                        break

                table_e = [-1] * 4
                for v_a, v_b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    k_a, p_a = (
                        wire_labels[w_a.index][v_a] >> 1,
                        wire_labels[w_a.index][v_a] & 1,
                    )

                    k_b, p_b = (
                        wire_labels[w_b.index][v_b] >> 1,
                        wire_labels[w_b.index][v_b] & 1,
                    )

                    e = (
                        H(
                            int2str(k_a, self.security_param)
                            + int2str(k_b, self.security_param)
                            + int2str(gate.index)
                        )
                        ^ wire_labels[w_c.index][gate.evaluate([v_a, v_b])]
                    )
                    table_e[p_a << 1 | p_b] = e
                    if p_a == 1 and p_b == 1:
                        assert e == 0
                garbled_tables_for_gates.append(table_e[:-1])

            else:
                table_e = [-1] * 4
                for v_a, v_b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    k_a, p_a = (
                        wire_labels[w_a.index][v_a] >> 1,
                        wire_labels[w_a.index][v_a] & 1,
                    )

                    k_b, p_b = (
                        wire_labels[w_b.index][v_b] >> 1,
                        wire_labels[w_b.index][v_b] & 1,
                    )

                    e = (
                        H(
                            int2str(k_a, self.security_param)
                            + int2str(k_b, self.security_param)
                            + int2str(gate.index)
                        )
                        ^ wire_labels[w_c.index][gate.evaluate([v_a, v_b])]
                    )
                    table_e[p_a << 1 | p_b] = e

                garbled_tables_for_gates.append(table_e)

        garbled_tables_for_outputs = []
        for output_wire in self.circuit.outputs:
            table_e = [-1] * 2
            for v in [0, 1]:
                k_v, p_v = (
                    wire_labels[output_wire.index][v] >> 1,
                    wire_labels[output_wire.index][v] & 1,
                )
                assert output_wire.input is not None
                gate = output_wire.input
                e = (
                    H(int2str(k_v, self.security_param) + 'out' + int2str(gate.index))
                    & 1
                ) ^ v
                table_e[p_v] = e
            garbled_tables_for_outputs.append(table_e)

        inputs_labels = []
        for i in range(self.n_Alice_bits):
            wire, bit = self.circuit.inputs[i], input_bits[i]
            inputs_labels.append(wire_labels[wire.index][bit])

        agent.sender.send(self.bob_id, garbled_tables_for_gates)
        agent.sender.send(self.bob_id, garbled_tables_for_outputs)
        agent.sender.send(self.bob_id, inputs_labels)

        # print('garbled_gates:', garbled_tables_for_gates)
        # print('garbled_outputs', garbled_tables_for_outputs)
        # print('labelsA:', inputs_labels)

        for i in range(self.n_Bob_bits):
            wire = self.circuit.inputs[self.n_Alice_bits + i]
            self.OT.alice(
                agent,
                [
                    wire_labels[wire.index][0],
                    wire_labels[wire.index][1],
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
        # print('_garbled_gates:', garbled_tables_for_gates)
        # print('_garbled_outputs', garbled_tables_for_outputs)
        # print('_labelsA:', inputs_labels_A)

        if self.enable_GRR:
            for table_e in garbled_tables_for_gates:
                if table_e is not None:
                    table_e.append(0)
        inputs_labels_B = []
        for i in range(self.n_Bob_bits):
            inputs_labels_B.append(self.OT.bob(agent, input_bits[i]))

        inputs_labels = inputs_labels_A + inputs_labels_B
        assert len(inputs_labels) == self.n_Alice_bits + self.n_Bob_bits
        # print(inputs_labels)
        n = len(self.circuit.gates)
        m = len(self.circuit.wires)
        in_deg: List[int] = [0] * n
        wire_ret: List[int] = [-1] * m
        for wire in self.circuit.wires:
            for out_gate in wire.outputs:
                if out_gate is not None:
                    in_deg[out_gate.index] += 1
        q = queue.Queue()
        for i in range(len(self.circuit.inputs)):
            # print('hhhhhh', inputs_labels[i])
            wire_ret[self.circuit.inputs[i].index] = inputs_labels[i]
            q.put(self.circuit.inputs[i])

        while not q.empty():
            wire = q.get()
            for out_gate in wire.outputs:
                if out_gate is not None:
                    in_deg[out_gate.index] -= 1
                    if in_deg[out_gate.index] == 0:
                        assert len(out_gate.inputs) == 2
                        w_a, w_b = out_gate.inputs
                        w_c = out_gate.output
                        # print('wtf', wire_ret[w_a.index], wire_ret[w_b.index])
                        k_a, p_a = wire_ret[w_a.index] >> 1, wire_ret[w_a.index] & 1
                        k_b, p_b = wire_ret[w_b.index] >> 1, wire_ret[w_b.index] & 1

                        if self.enable_freeXOR and isinstance(out_gate, Xor):
                            wire_ret[w_c.index] = (
                                wire_ret[w_a.index] ^ wire_ret[w_b.index]
                            )

                        else:

                            wire_ret[w_c.index] = (
                                H(
                                    int2str(k_a, self.security_param)
                                    + int2str(k_b, self.security_param)
                                    + int2str(out_gate.index)
                                )
                                ^ garbled_tables_for_gates[out_gate.index][
                                    p_a << 1 | p_b
                                ]
                            )

                        q.put(w_c)

        # for output_wire in self.circuit.outputs:
        #     print('index=', output_wire.index)
        # print('start', flush=True)
        # print(len(self.circuit.outputs))
        output_bits = [
            (
                H(
                    int2str(wire_ret[output_wire.index] >> 1, self.security_param)
                    + 'out'
                    + int2str(output_wire.input.index)
                )
                & 1
            )
            ^ garbled_tables_for_outputs[i][wire_ret[output_wire.index] & 1]
            for i, output_wire in enumerate(self.circuit.outputs)
        ]
        # output_bits = [0] * len(self.circuit.outputs)
        # print('hello', flush=True)
        agent.sender.send(self.alice_id, output_bits)
        # print('end', flush=True)
        return output_bits
