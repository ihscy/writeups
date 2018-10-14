#!/usr/bin/python

from pwn import *
import hashlib

def pad(message):
    if len(message) % 16 == 0:
        message = message + chr(16)*16
    elif len(message) % 16 != 0:
        message = message + chr(16 - len(message)%16)*(16 - len(message)%16)
    return message

conn=remote("2018shell2.picoctf.com", 14263)

conn.recvuntil("Send & verify (S)")

def do_encrypt(prefix, suffix):
    ''' encrypt a report
    Keyword arguments:
    prefix -- situation report part of the message body.
              service inserts this string before the CTF flag
    suffix -- service inserts this string after the CTF flag

    Return -- cipher message
    '''
    conn.send("e\n")
    conn.recvuntil("Please enter your situation report: ")
    conn.send(prefix + "\n")
    conn.recvuntil("Anything else? ")
    conn.send(suffix + "\n")
    conn.recvuntil("encrypted: ")

    # strip the trailing newline
    cipher = conn.recvline()[:-1]

    # 16-bytes block == 32 hex string (2 hex per byte)
    assert 0 == len(cipher) % 32, "Fatal error - cipher message must be multiple of 32"
    assert len(cipher) >= 96, "Fatal error - cipher message must be at least 96 characters long"

    conn.recvuntil("Send & verify (S)")
    return cipher

def do_verify(cipher):
    """ Verify if a cipher can be successfully decrypted
    Keyword arguments:
    cipher -- the cipher message

    Return -- True the message is successfully decrypted and False otherwise
    """

    # 16-bytes block == 32 hex string (2 hex per byte)
    assert 0 == (len(cipher) % 32), "Fatal error length of cipher message must be multiple of 32"

    # cipher message is 96 for zero-length plaintext
    #   1. one 16-byte IV block
    #   2. one 20-byte MAC block
    #   3. one 12-byte padding block
    assert len(cipher) >= 96, "Fatal error - cipher message must be at least 96 characters long"

    conn.send("s\n")
    conn.recvuntil("Please input the encrypted message: ")
    conn.send(cipher + "\n")
    line = conn.recvline()
    conn.recvuntil("Send & verify (S)")
    return line.startswith('Successful decryption.')

def get_EBoP_metrics():
    """ determine the length of shortest message with an EBoP and the associated suffix length
        Note: an EBoP (Entire Block of Padding) is defined as a padding block containing only padding data.

    Return -- two tuple with the fist value being the length of shortest message with EBoP
        and the 2nd value being the required padding length (for both prefix and suffix)
    """

    # cipher message length with zero-length prefix and suffix
    cipher_len = 0
    suffix_len = 0

    while True:
        new_cipher_len = len(do_encrypt("", 'a' * suffix_len)) / 2
        assert new_cipher_len >= 48, "Fatal error"
        assert 0 == new_cipher_len % 16, "Fatal error"

        if new_cipher_len > cipher_len:
            # the new length must be exactly 16-byte longer (or 32-hex digit longer)
            assert(new_cipher_len == cipher_len + 16), "fatal error - block_size incorrect"

            return new_cipher_len, suffix_len
        cipher_len = new_cipher_len
        suffix_len = suffix_len + 1

def get_CTF_metrics(EBoP_len, EBoP_padding):
    """ determine the location of CTF
    Return - the smallest where we can place CTF

    """

    # find the earliest possible (where the prefix is empty) CTF location
    prefix = ''
    ctf = ''
    suffix = 'A' * EBoP_padding

    message = """Agent,
Greetings. My situation report is as follows:
{0}
My agent identifying code is: {1}.
Down with the Soviets,
006
""".format(prefix, ctf)

    h = hashlib.sha1()
    message = message+suffix
    h.update(message)
    message = message+h.digest()
    assert 20 == len(h.digest()), "fatal error"

    substr_to_find = "code is: "
    return message.find(substr_to_find) + len(substr_to_find)

def decode_char(offset, EBoP_padding):
    '''
    decode a character at the specified offset using the given EBoP_padding
    Arguments:
    offset -- the offset of the character to be decoded
    EBoP_padding -- the total amount of padding in order to ensure the cipher
        message contains EBoP (Entire Block of Padding)
    '''

    # determine the required prefix padding in order to place the character at the end of the block
    prefix_len = 15 - (offset % 16)

    # the rest of padding will be absorbed by the suffix padding
    suffix_len = EBoP_padding - prefix_len

    block_start = offset + prefix_len + 1
    assert (0 == (block_start % 16)), "fatal error"

    # the block id containing our target character
    # add 1 to accommodate IV
    bid = block_start / 16 + 1

    attempts = 0
    prefix = 'A' * prefix_len
    suffix = 'B' * suffix_len
    print("decoding offset: %d prefix length %d suffix length %d" %(offset, prefix_len, suffix_len))

    # implements the algorithm published by google
    # https://www.openssl.org/~bodo/ssl-poodle.pdf
    while True:
        try:
            message = do_encrypt(prefix, suffix)
            if 0 == (attempts % 16):
                print("offset %d attempts %d" % (offset, attempts))
            assert len(message) == EBoP_len * 2, "fatal error"

            # substitute last block with block bid
            message = message[:-32] + message[(bid - 1)*32:bid * 32]
            attempts = attempts + 1
            if do_verify(message):
                print("offset=%d attempts=%d done" % (offset, attempts))

                # the plain text is C[bid - 1] ^ C[N - 1] ^ 16
                # we use 16 instead of 15 because of padding differences
                char = int(message[bid * 32 - 34:bid * 32 - 32], 16) ^ int(message[-34:-32], 16) ^ 16
                print("offset=%d attempts=%d char=0x%02x" % (offset, attempts, char))
                return p8(char)
        except EOFError:
            global conn
            conn.close()
            conn=remote("2018shell2.picoctf.com", 14263)
            conn.recvuntil("Send & verify (S)")

# Min_EBoP_len, Min_EBoP_padding = get_EBoP_metrics()
Min_EBoP_len, Min_EBoP_padding = 208, 14
print("Min_EBop_Len %d Min_EBoP_padding %d" % (Min_EBoP_len, Min_EBoP_padding))

# increase the padding by 32 bytes (enough to decode CTF)
EBoP_len = Min_EBoP_len + 32
EBoP_padding = Min_EBoP_padding + 32

CTF_start = get_CTF_metrics(EBoP_len, EBoP_padding)
print("CTF start %d" % (CTF_start))

print("full block size %d padding %d" % (Min_EBoP_len, EBoP_padding))

start_offset = len("picoCTF") + CTF_start
cur_offset = start_offset

ch = ''
ctf = ''
# loop until we get }
while ch != '}':
    ch = decode_char(cur_offset, EBoP_padding)

    # { can only be in first characters
    assert cur_offset != start_offset or ch == '{', "first character must be {"
    assert ch != '{' or cur_offset == start_offset , "first character must be {"

    cur_offset = cur_offset + 1
    ctf = ctf + ch
    print ctf
