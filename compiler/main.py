from typing import Dict, List, Union
import sys
import ast
from circuit import Circuit, Wire
from circuit_utils import int2bits, bits2int
from circuit_utils.modules import Add, Subtract, Lt, ToBool, Select


class ASTCompiler:
    vars: Dict[str, List[Wire]]
    zero: Wire
    one: Wire
    circuit: Circuit

    def __init__(self):
        self.vars = {}
        self.default_bit_length = 64

    def create_variable(self, bit_length: int) -> List[Wire]:
        result = []
        for _ in range(bit_length):
            w = Wire()
            self.circuit.add_wire(w)
            result.append(w)
        return result

    def compile_constant(self, stmt: ast.Constant) -> List[Wire]:
        assert isinstance(stmt.value, int)
        bits = int2bits(stmt.value, self.default_bit_length)
        return [[self.zero, self.one][bit] for bit in bits]

    def compile_bin_op(self, stmt: Union[ast.BinOp, ast.Compare]):
        if isinstance(stmt, ast.Compare):
            assert len(stmt.ops) == 1
            stmt.right = stmt.comparators[0]
            stmt.op = ast.Lt()
        operands: List[List[Wire]] = []
        for expr in [stmt.left, stmt.right]:
            if isinstance(expr, ast.Constant):
                operands.append(self.compile_constant(expr))
            elif isinstance(expr, ast.Name):
                assert (
                    expr.id in self.vars
                ), f'line {expr.lineno}: variable {expr.id} used before declaration'
                operands.append(self.vars[expr.id])
            elif isinstance(expr, ast.BinOp):
                operands.append(self.compile_bin_op(expr))
            else:
                assert False, f'line {expr.lineno}: unsupported expression'
        assert len(operands[0]) == len(
            operands[1]
        ), f'line {expr.lineno}: operands should have the same bit length. got: {len(operands[0])} {len(operands[1])}'
        bit_length = len(operands[0])
        if isinstance(stmt.op, ast.Add):
            adder = Add(self.circuit, bit_length, operands[0], operands[1])
            return adder.out
        elif isinstance(stmt.op, ast.Sub):
            subtract = Subtract(
                self.circuit, bit_length, self.one, operands[0], operands[1]
            )
            return subtract.out
        elif isinstance(stmt.op, ast.Lt):
            lt = Lt(self.circuit, bit_length, self.one, operands[0], operands[1])
            return lt.out
        else:
            assert False, f'line {stmt.op.lineno}: unsupported operation {stmt.op}'

    def compile_if_expr(self, stmt: ast.IfExp) -> List[Wire]:
        test = self.compile_expr(stmt.test)
        to_bool = ToBool(self.circuit, len(test), test)
        test = to_bool.out
        body = self.compile_expr(stmt.body)
        orelse = self.compile_expr(stmt.orelse)

        assert len(body) == len(orelse)
        bit_length = len(body)
        result = []
        for i in range(bit_length):
            select = Select(self.circuit, orelse[i], body[i], test[0])
            result.append(select.out)
        return result

    def compile_expr(self, stmt):
        if isinstance(stmt, ast.Name):
            assert (
                stmt.id in self.vars
            ), f'line {stmt.lineno}: variable {stmt.id} used before declaration'
            return self.vars[stmt.id]
        elif isinstance(stmt, ast.Constant):
            return self.compile_constant(stmt)
        elif isinstance(stmt, ast.BinOp) or isinstance(stmt, ast.Compare):
            return self.compile_bin_op(stmt)
        elif isinstance(stmt, ast.IfExp):
            return self.compile_if_expr(stmt)
        else:
            assert False, f'line {stmt.lineno}: unsupported value {stmt}'

    def compile_assign(self, stmt: Union[ast.Assign, ast.AnnAssign]):
        if isinstance(stmt, ast.Assign):
            assert len(stmt.targets) == 1 and isinstance(
                stmt.targets[0], ast.Name
            ), f'line {stmt.lineno}: assignment should have exactly one target'
            targets = stmt.targets
        elif isinstance(stmt, ast.AnnAssign):
            targets: List[ast.Name] = [stmt.target]
        if targets[0].id in self.vars:
            bit_length = len(self.vars[targets[0].id])
        else:
            bit_length = None
        self.vars[targets[0].id] = self.compile_expr(stmt.value)
        if bit_length is not None:
            # implicit type conversion
            tmp = len(self.vars[targets[0].id])
            if tmp > bit_length:
                self.vars[targets[0].id] = self.vars[targets[0].id][:bit_length]
            elif tmp < bit_length:
                self.vars[targets[0].id] = self.vars[targets[0].id].copy()
                self.vars[targets[0].id].extend(
                    self.zero for _ in range(bit_length - tmp)
                )

    def compile(self, m: ast.Module) -> Circuit:
        circuit = Circuit()
        self.circuit = circuit
        zero = Wire()
        self.zero = zero
        circuit.add_wire(zero)
        circuit.inputs.append(zero)
        one = Wire()
        self.one = one
        circuit.add_wire(one)
        circuit.inputs.append(one)
        for stmt in m.body:
            if isinstance(stmt, ast.AnnAssign):
                assert isinstance(
                    stmt.target, ast.Name
                ), f'line {stmt.lineno}: assignment should have exactly one target'
                if isinstance(stmt.annotation, ast.Subscript):
                    assert isinstance(stmt.annotation.value, ast.Name)
                    if stmt.annotation.value.id == 'Bits':
                        assert isinstance(stmt.annotation.slice, ast.Constant)
                        assert isinstance(stmt.annotation.slice.value, int)
                        self.vars[stmt.target.id] = self.create_variable(
                            stmt.annotation.slice.value
                        )
                    elif stmt.annotation.value.id == 'Input':
                        assert stmt.value is None
                        assert isinstance(stmt.annotation.slice, ast.Constant)
                        assert isinstance(stmt.annotation.slice.value, int)
                        self.vars[stmt.target.id] = self.create_variable(
                            stmt.annotation.slice.value
                        )
                        circuit.inputs.extend(self.vars[stmt.target.id])
                if stmt.value is not None:
                    self.compile_assign(stmt)
                if isinstance(stmt.annotation, ast.Name):
                    if stmt.annotation.id == 'Output':
                        assert (
                            stmt.target.id in self.vars
                        ), f'line {stmt.target.lineno}: variable {stmt.target.id} used before declaration'
                        circuit.outputs.extend(self.vars[stmt.target.id])
                    elif stmt.annotation.id == 'Input':
                        print(
                            f'(warning) line {stmt.annotation.lineno}: do you mean Input[SOME_BIT_LENGTH]?',
                            file=sys.stderr,
                        )
            elif isinstance(stmt, ast.Assign):
                self.compile_assign(stmt)
            else:
                assert False, f'line {stmt.lineno}: unsupported statement'
        return circuit


if __name__ == '__main__':
    bit_length = 64
    with open('tests/demos/billionaire.py', 'r') as f:
        code = f.read()
    compiler = ASTCompiler()
    circuit = compiler.compile(ast.parse(code))
    print(circuit.evaluate([0, 1] + int2bits(12, 64) + int2bits(11, 64)))
