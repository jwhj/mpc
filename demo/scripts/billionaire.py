a: Input[64]
flag: Input[1]
b: Input[64]
t1 = a < b
t2 = a <= b
result: Output = t2 if flag else t1
