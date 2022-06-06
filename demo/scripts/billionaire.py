a: Input[64]
flag: Input[1]
b: Input[64]
result: Output = a < b
false: Bits[1] = 0
eq: Output = a == b if flag else false
