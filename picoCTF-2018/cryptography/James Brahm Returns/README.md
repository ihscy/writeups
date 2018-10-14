# James Brahms Returns
**Category:** Cryptography

**Points:** 700

**Description:** 
Dr. Xernon has finally approved an update to James Brahm's spy terminal. (Someone finally told them that ECB isn't secure.) Fortunately, CBC mode is safe! Right? Connect with `nc 2018shell1.picoctf.com 22666`. [Source](https://2018shell1.picoctf.com/static/7858d9aeeba4938ed586cbef2931d6a9/source.py).

**Hint:** What killed SSL3?

----------

## Solution

Based off of the hint, "What killed SSL3?" we do some searching and conveniently come across this [nice Google research paper](https://www.openssl.org/~bodo/ssl-poodle.pdf).

We implement the same exact attack outlined in the paper, except we XOR with `0x10` instead of `0xF` due to a padding difference.

Let's look at how the picoCTF problem can be mapped to the one defined in the Google paper.

| Google Paper       | picoCTF           |
| ------------- |:-------------:|
| cookie     | the flag |
| /path     | the text for "Please enter your situation report:"    |
| /body | the text for "Anything else? "  |

The advantage we have is that we know the exact location of the flag in the message due to access to the source code. We can start right at the correct offset and keep decoding until we receive the closing curly bracket character.

We used pwn tools to interact with the server since it provided many handy dandy functionalities such as "recvuntil".

You can find my implementation [here](https://github.com/jespiron/picoCTF-2018/blob/master/crypto/James%20Brahm%20Returns/crack_jbr.py).
