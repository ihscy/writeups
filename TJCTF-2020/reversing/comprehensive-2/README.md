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

Now what this program is essentially doing is taking a 7-byte key `n`, and using it to create a 63-byte key `keybytes` by XORing together bytes of `n` in a particular order. Then, it XORs `keybytes` with the 63-byte flag, and prints the output as a list of decimal character codes.

Solution
--------

My first thought was just to brute force the 7-byte key. We know `n` consists of only characters from `a`, meaning lowercase letters. That's 26 possibilities, meaning a search space of 26^7 or around 8 billion. That's... doable. It's a good back-up, but we can do better.

The way `keybytes` is created from `n` is constant. Each byte of `keybytes` is three bytes of `n` XORed together, given by the indices `i`, `j`, and `k`. If two of those indices are the same, we can simplify the expression for that byte of `keybytes`. We can modify the deobfuscated script to print the expression for each byte of `keybytes` in terms of `n`:

```python
keyidxs = []
for k in range(3):
    for j in range(7):
        for i in range(3):
            idxs = sorted((k, j, i))
            for idx in set(idxs):
                if idxs.count(idx) >= 2:
                    idxs.remove(idx)
                    idxs.remove(idx)
            print(' ^ '.join('n[{}]'.format(idx) for idx in idxs))
            keyidxs.append(tuple(idxs))
print(keyidxs)
```

That outputs this:

```
n[0]
n[1]
n[2]
n[1]
n[0]
n[0] ^ n[1] ^ n[2]
n[2]
n[0] ^ n[1] ^ n[2]
n[0]
n[3]
n[0] ^ n[1] ^ n[3]
n[0] ^ n[2] ^ n[3]
n[4]
n[0] ^ n[1] ^ n[4]
n[0] ^ n[2] ^ n[4]
n[5]
n[0] ^ n[1] ^ n[5]
n[0] ^ n[2] ^ n[5]
n[6]
n[0] ^ n[1] ^ n[6]
n[0] ^ n[2] ^ n[6]
n[1]
n[0]
n[0] ^ n[1] ^ n[2]
n[0]
n[1]
n[2]
n[0] ^ n[1] ^ n[2]
n[2]
n[1]
n[0] ^ n[1] ^ n[3]
n[3]
n[1] ^ n[2] ^ n[3]
n[0] ^ n[1] ^ n[4]
n[4]
n[1] ^ n[2] ^ n[4]
n[0] ^ n[1] ^ n[5]
n[5]
n[1] ^ n[2] ^ n[5]
n[0] ^ n[1] ^ n[6]
n[6]
n[1] ^ n[2] ^ n[6]
n[2]
n[0] ^ n[1] ^ n[2]
n[0]
n[0] ^ n[1] ^ n[2]
n[2]
n[1]
n[0]
n[1]
n[2]
n[0] ^ n[2] ^ n[3]
n[1] ^ n[2] ^ n[3]
n[3]
n[0] ^ n[2] ^ n[4]
n[1] ^ n[2] ^ n[4]
n[4]
n[0] ^ n[2] ^ n[5]
n[1] ^ n[2] ^ n[5]
n[5]
n[0] ^ n[2] ^ n[6]
n[1] ^ n[2] ^ n[6]
n[6]
[(0,), (1,), (2,), (1,), (0,), (0, 1, 2), (2,), (0, 1, 2), (0,), (3,), (0, 1, 3), (0, 2, 3), (4,), (0, 1, 4), (0, 2, 4), (5,), (0, 1, 5), (0, 2, 5), (6,), (0, 1, 6), (0, 2, 6), (1,), (0,), (0, 1, 2), (0,), (1,), (2,), (0, 1, 2), (2,), (1,), (0, 1, 3), (3,), (1, 2, 3), (0, 1, 4), (4,), (1, 2, 4), (0, 1, 5), (5,), (1, 2, 5), (0, 1, 6), (6,), (1, 2, 6), (2,), (0, 1, 2), (0,), (0, 1, 2), (2,), (1,), (0,), (1,), (2,), (0, 2, 3), (1, 2, 3), (3,), (0, 2, 4), (1, 2, 4), (4,), (0, 2, 5), (1, 2, 5), (5,), (0, 2, 6), (1, 2, 6), (6,)]
```

Each of the seven bytes in `n` have at least one byte in `keybytes` that is equal to it. We know that the *real* output (given in the problem description) XORed with the *real* 63-byte key gives us the flag. We also know the set of valid characters that can be in the flag. So we can use all the bytes in the 63-byte key that are equal to a byte in the 7-byte key to narrow down, byte-by-byte, which are possible bytes for the 7-byte key.

After we've narrowed down the search space that way, we then have to iterate over the remaning possible 7-byte keys, and try them each. We can check if the flag is valid with the same checks that are at the top of the original script as `assert` statements.

Here is a solve script that does just that:

```python
#!/usr/bin/env python3
from functools import reduce
import itertools
from operator import itemgetter, xor

KEY_IDXS = ((0,), (1,), (2,), (1,), (0,), (0, 1, 2), (2,), (0, 1, 2), (0,), (3,), (0, 1, 3), (0, 2, 3), (4,), (0, 1, 4), (0, 2, 4), (5,), (0, 1, 5), (0, 2, 5), (6,), (0, 1, 6), (0, 2, 6), (1,), (0,), (0, 1, 2), (0,), (1,), (2,), (0, 1, 2), (2,), (1,), (0, 1, 3), (3,), (1, 2, 3), (0, 1, 4), (4,), (1, 2, 4), (0, 1, 5), (5,), (1, 2, 5), (0, 1, 6), (6,), (1, 2, 6), (2,), (0, 1, 2), (0,), (0, 1, 2), (2,), (1,), (0,), (1,), (2,), (0, 2, 3), (1, 2, 3), (3,), (0, 2, 4), (1, 2, 4), (4,), (0, 2, 5), (1, 2, 5), (5,), (0, 2, 6), (1, 2, 6), (6,))
ALPHA = tuple(map(ord, 'abcdefghijklmnopqrstuvwxyz'))
OUTPUT = [1, 18, 21, 18, 73, 20, 65, 8, 8, 4, 24, 24, 9, 18, 29, 21, 3, 21, 14, 6, 18, 83, 2, 26, 86, 83, 5, 20, 27, 28, 85, 67, 5, 17, 2, 7, 12, 11, 17, 0, 2, 20, 12, 26, 26, 30, 15, 44, 15, 31, 0, 12, 46, 8, 28, 23, 0, 11, 3, 25, 14, 0, 65]
FLAG_VALID = set(tuple(map(ord, ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')) + ALPHA)


def main():

    possibilities = []
    for i in range(7):
        possible = set(ALPHA)
        for b in ALPHA:
            for output_byte, key_idxs in zip(OUTPUT, KEY_IDXS):
                if len(key_idxs) != 1:
                    continue
                if key_idxs[0] != i:
                    continue
                if output_byte ^ b not in FLAG_VALID:
                    possible.remove(b)
                    break
        possibilities.append(tuple(possible))

    print(tuple(map(len, possibilities)))

    for i, possible_n in enumerate(itertools.product(*possibilities)):

        if i % 1000000 == 0:
            print('tried {} keys so far'.format(i))

        keybytes = tuple(reduce(xor, (possible_n[key_idx] for key_idx in key_idxs)) for output_byte, key_idxs in zip(OUTPUT, KEY_IDXS))

        flag = tuple(itertools.starmap(xor, zip(keybytes, OUTPUT)))
        if any(c not in FLAG_VALID for c in flag):
            continue

        flagstr = ''.join(map(chr, flag))
        if flagstr.count('tjctf{') != 1:
            continue
        if flagstr.count('}') != 1:
            continue
        if flagstr.count(' ') != 5:
            continue

        keystr = ''.join(map(chr, possible_n))
        print('key {}: {}'.format(keystr, flagstr))


main()
```

This outputs the number of possibilities for each byte in `n`: `(11, 6, 13, 17, 25, 23, 16)`. This means our search space has been narrowed to $`11*6*13*17*25*23*16`$, or around 134 million. That's quite a bit better (a 60x decrease), and brought the runtime down from probably over a day to a couple hours (although I didn't have to check all 134 million before I found the solution, so it actually only took around 20 minutes).

Eventually, this got the key (and the flag):

```
(11, 6, 13, 17, 25, 23, 16)
tried 0 keys so far
tried 1000000 keys so far
tried 2000000 keys so far
tried 3000000 keys so far
tried 4000000 keys so far
tried 5000000 keys so far
tried 6000000 keys so far
tried 7000000 keys so far
tried 8000000 keys so far
tried 9000000 keys so far
tried 10000000 keys so far
tried 11000000 keys so far
tried 12000000 keys so far
tried 13000000 keys so far
tried 14000000 keys so far
tried 15000000 keys so far
tried 16000000 keys so far
tried 17000000 keys so far
tried 18000000 keys so far
tried 19000000 keys so far
tried 20000000 keys so far
key isacapo: hata o sagashiteimasu ka? dozo, tjctf{sumimasen_flag_kudasaii}.
tried 21000000 keys so far
^C
```
