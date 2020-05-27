Tap Dancing
===========

**Points:** 25

**Description:** 
My friend is trying to teach me to dance, but I am not rhythmically coordinated! They sent me a list of [dance moves](cipher.txt) but they're all numbers! Can you help me figure out what they mean so I can learn the dance?

NOTE: Flag is not in flag format.

Solution
--------

```
1101111102120222020120111110101222022221022202022211
```

At first glance this looks like ternary. But converting that directly to binary/hex does not give us ASCII. Tap dancing might suggest several things. Maybe [tap dancing notation](), but no, that looks nothing like this.

Turns out it's morse code. We can see that there are multiple `1`s in a row, and multiple `2`s in a row, but never multiple `0`s in a row. This tells us `0` is ` `. Now which of `1` and `2` correspond to `.` and `-`, but we can just try them both:

```python
>>> c = '1101111102120222020120111110101222022221022202022211'
>>> c.replace('0', ' ').replace('1', '.').replace('2', '-')
'.. ..... -.- --- - .- ..... . .--- ----. --- - ---..'
>>> c.replace('0', ' ').replace('1', '-').replace('2', '.')
'-- ----- .-. ... . -. ----- - -... ....- ... . ...--'
```

Plugging those into [an online morse code decoder](https://morsecode.world/international/translator.html), we get `I5KOTA5EJ9OT8` and `M0RSEN0TB4SE3`, respectively. I'm pretty sure it's the second one.
