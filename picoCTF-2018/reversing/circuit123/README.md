circuit123
==========


Problem
-------

**Category:** Reversing
**Description:** “Can you crack the key to decrypt map2 for us? The key to map1
is 11443513758266689915.”
**Hint:** “Have you heard of z3?”


Investigation
-------------

First, we went through map2.txt, and organized it in a more human-readable
format to be able to understand better. The array that is loaded by decrypt.py
as “gates” has the following structure:

```python
gates = [('true', []),
         ('xor', [(0, False), (64, False)]),
         {...}
         ('or', [(1076, False), (1139, False)])]
```

The first part of verify() in decrypt.py looks something like this:

```python
b = [(key >> i) & 1 for i in range(length)]
```

This populates an array of bits, “b,” with “length” (128) bits of the key.
Lastly, we can see that the first part of verify() loads the following variable
from map2.txt:

```python
check = (1140, True)
```

Which is then checked by the following:

```python
return b[check[0]] ^ check[1]
```

Thus, we need the 1140th element of the array b[] to not evaluate to “1.” In
verify(), that gate (the final one shown above in the “gates” array) is
evaluated thusly:

1. the variable “u1” is stored as the xor of gate 1076 and “False”; the
   variable “u2” is similarly stored as the xor of gate 1139 and “False.”
2. the program appends to the array b[] the evaluation of the operation
   specified as the string in the beginning of the gate&#8212;called “name” and
   in this case it is “or”&#8212;applied to u1 and u2; for example, in the case
   of this last gate the bit appended is the evaluation of “u1 or u2.”
3. This is where the headache comes in&#8212;we want the final gate to evaluate
   to “0,” but the value of that final gate is dependent on the evaluation of
   two other gates! As such, we have an awfully long dependency chain that all
   sorts down to the first 128 bits of b[]&#8212;our original key. In other
   words, we need to solve for the original 128 bits of b[] such that when each
   gate is evaluated in turn, the final one will evaluate to “0.”


First attempt
-------------

At first, our plan was to forget about the problem hint and ditch z3, writing
a Python script to attempt traversing down each possibility of the dependency
tree and moving on to the next possibility when a contradiction is reached.
Essentially, at each gate, it would create an array named “try_lst” with all of
the possible evaluations of the gates&#8212;for example, a “xor” gate could
have the combinations of (1, 0) or (0, 1) but not (0, 0) or (1, 1). So
first, the script just guesses that it’s (1, 0), and continues to call itself
down the dependency chain. However, if somewhere along the line we find out
that, say, we want the first gate (which we know is true) to be false, it’s
obvious that it won’t happen and thus we’ve guessed wrong somewhere along the
line. So a contradiction is raised and we guess another option. Our initial
attempt is thus rendered below, with the gates collapsed:

```python
#!/usr/bin/python3

length = 128
# I hope you have folding by indent turned on in your editor >:)
gates = [('true', []),
#+---1012 lines: (‘xor’, [(0, False), (64, False)]),

# gate used by check is ('or', [(1076, False), (1139, False)]), which
# must not work out to the value of 1; thus the check continues all the
# way down


class Contradiction(Exception):
    pass


def solve_gate(idx, val, b):
    name, args = gates[idx - length]
    if b[idx] is not None:
        if b[idx] == val:
            return b
        else:
            raise Contradiction
    if idx < length:
        return b[:idx] + [val] + b[idx + 1:]
    if name == "true":
        if val:
            return b[:idx] + [1] + b[idx + 1:]
        else:
            raise Contradiction
    elif name == "or":
        if val:
            try_lst = ([1, 1], [0, 1], [1, 0])
        else:
            try_lst = ([0, 0],)
    elif name == "xor":
        if val:
            try_lst = ([1, 0], [0, 1])
        else:
            try_lst = ([1, 1], [0, 0])
    else:
        raise ValueError
    for u in try_lst:
        u[0] ^= args[0][1]
        u[1] ^= args[1][1]
        try:
            new_b = solve_gate(args[0][0], u[0], b)
            new_b = solve_gate(args[1][0], u[1], new_b)
            return new_b[:idx] + [val] + new_b[idx + 1:]
        except Contradiction:
            continue
    raise Contradiction


def main():
    print(solve_gate(check[0], check[1] ^ 1,
                     [None] * (len(gates) + length)))


if __name__ == "__main__":
    for i in range(len(gates)):
    print("{}\t{}".format(i + length, gates[i]))
    main()
```

This .&#8239;.&#8239;. didn’t really work, as it returned the incorrect key for
map1 and could not solve map2. We’re still not really sure why, to this moment,
but working with this script at least helped us solidify our knowledge of how
this problem is really structured.


Second attempt
--------------

Luckily, while @imyxh and @nog642 were struggling to debug the first solution,
@jespiron succeeded with a different technique with z3, essentially rewriting
procedures from verify() as a z3 constraint.

```python
def solve(chalbox):
    length, gates, check = chalbox

    b = [z3.Bool(str(i)) for i in range(length)]
    for name, args in gates:
        if name == 'true':
            b.append(True)
        else:
            u1 = z3.Xor(b[args[0][0]], args[0][1])
            u2 = z3.Xor(b[args[1][0]], args[1][1])
            if name == 'or':
                b.append(z3.Or(u1, u2))
            elif name == 'xor':
                b.append(z3.Xor(u1, u2))

    solver = z3.Solver()
    solver.add(z3.Xor(b[check[0]], check[1]))
    if solver.check():
        result = solver.model()
        result_int = 0
        for val in result:
            bit = int(val.name())
            if result[val]:
                result_int = result_int + (1 << bit)
        return result_int
    else:
        exit(1)
```

First, this creates an array of z3 boolean objects similar to the bit array
that was created in the original function; the first gate is appended as the
129th bit of b[]&#8212;“True”; the evaluation of each consecutive gate is
rewritten to use z3 Xor() and Or() functions and is appended to the boolean
array; a z3 constraint is created based on the fact that we want the function
to return 1 (`b[check[0]] ^ check[1]`), but written with a z3.Xor(); we model the
solver and let z3 do the heavy lifting, then convert the boolean array that z3
returns as the model into a string of bits and then convert that to decimal,
yielding the key. That’s about it! The key, when fed to the original Python
code, will decrypt the ciphertext at the beginning of the map file.

