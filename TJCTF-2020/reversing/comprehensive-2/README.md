Comprehensive 2
===============

**Points:** 65

**Description:** 

His power level increased... What do I do now??

[comprehensive_2.py](comprehensive_2.py)

Output: `[1, 18, 21, 18, 73, 20, 65, 8, 8, 4, 24, 24, 9, 18, 29, 21, 3, 21, 14, 6, 18, 83, 2, 26, 86, 83, 5, 20, 27, 28, 85, 67, 5, 17, 2, 7, 12, 11, 17, 0, 2, 20, 12, 26, 26, 30, 15, 44, 15, 31, 0, 12, 46, 8, 28, 23, 0, 11, 3, 25, 14, 0, 65]`

Deobfuscation
-------------

So let's take a look at this source.

```python
m = '[?????]'
n = '[?????]'

a = 'abcdefghijklmnopqrstuvwxyz'
p = ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

assert len(m) == 63 and set(m).issubset(set(a + p))
assert len(n) == 7  and set(n).issubset(set(a))
assert m.count('tjctf{') == 1 and m.count('}') == 1 and m.count(' ') == 5

print(str([x for z in [[[ord(m[i]) ^ ord(n[j // 3]) ^ ord(n[i - j - k]) ^ ord(n[k // 21]) for i in range(j + k, j + k + 3)] for j in range (0, 21, 3)] for k in range(0, len(m), 21)] for y in z for x in y])[1:-1])
```

So clearly there's some deobfuscation to be done here. First off, this current script won't even run. We need some way to verify our deobfuscation is correct. We need to define test values for the variables `m` and `n` at the top.

```python
m = 'tjctf{ejoi ejwe?wpio jgwgjj oj)(u) jwje?? eigh_ahoijwwijfwe_wi}'
n = 'svchars'

a = 'abcdefghijklmnopqrstuvwxyz'
p = ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

assert len(m) == 63 and set(m).issubset(set(a + p))
assert len(n) == 7  and set(n).issubset(set(a))
assert m.count('tjctf{') == 1 and m.count('}') == 1 and m.count(' ') == 5

print(str([x for z in [[[ord(m[i]) ^ ord(n[j // 3]) ^ ord(n[i - j - k]) ^ ord(n[k // 21]) for i in range(j + k, j + k + 3)] for j in range (0, 21, 3)] for k in range(0, len(m), 21)] for y in z for x in y])[1:-1])
```

The values for `m` and `n` had to satisfy the three `assert` lines. This works, but many values could work (including the actual flag).

Now this returns an output: `7, 28, 0, 2, 21, 29, 6, 12, 28, 1, 77, 29, 11, 19, 20, 77, 0, 18, 26, 25, 67, 28, 20, 17, 20, 28, 9, 70, 12, 28, 68, 64, 8, 77, 65, 30, 0, 24, 2, 73, 76, 70, 6, 15, 20, 14, 60, 23, 27, 25, 10, 18, 10, 31, 24, 30, 7, 21, 2, 45, 20, 15, 14`. We can use it to verify, as we deobfuscate, that the program still works the same.

After some deobfuscation, we can find that the program is equivalent to this:

```python
FLAG = 'tjctf{ejoi ejwe?wpio jgwgjj oj)(u) jwje?? eigh_ahoijwwijfwe_wi}'
n = 'svchars'

a = 'abcdefghijklmnopqrstuvwxyz'
p = ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

assert len(FLAG) == 63
assert set(FLAG).issubset(set(a + p))
assert len(n) == 7
assert set(n).issubset(set(a))
assert FLAG.count('tjctf{') == 1
assert FLAG.count('}') == 1
assert FLAG.count(' ') == 5


keychars = list(map(ord, n))
keybytes = []
for k in range(3):
    for j in range(7):
        for i in range(3):
            keybytes.append(keychars[k] ^ keychars[j] ^ keychars[i])

output = []
for i in range(63):
    output.append(ord(FLAG[i]) ^ keybytes[i])
print(str(output)[1:-1])
```

Now what this program is essentially doing is taking a 7-byte key `n`, and using it to create a 63-byte key `keybytes`. Then, it XORs that key with the 63-byte flag, and prints the output as a list of decimal character codes.

Solution
--------

Bruh.
