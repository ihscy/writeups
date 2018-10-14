# be-quick-or-be-dead-3
**Category:** Reversing

**Points:** 350

**Description:** 
As the [song](https://www.youtube.com/watch?v=CTt1vk9nM9c) draws closer to the end, another executable [be-quick-or-be-dead-3](https://2018shell2.picoctf.com/static/a1a9b9eded9bae8b99283218ee5bb5b3/be-quick-or-be-dead-3)
suddenly pops up. This one requires even faster machines. Can you run it fast enough too? 
You can also find the executable in /problems/be-quick-or-be-dead-3_1_036263621db6b07c874d55f1e0bba59d.

----------

## Solution

Based on the disassembled output of main, it looks like `get_key` will calculate the key needed to decrypt the flag.

```
 (gdb) disassemble main
Dump of assembler code for function main:
...
   0x00000000004008ce <+40>:    callq  0x400815 <get_key>
   0x00000000004008d3 <+45>:    mov    $0x0,%eax
   0x00000000004008d8 <+50>:    callq  0x400840 <print_flag>
   0x00000000004008dd <+55>:    mov    $0x0,%eax
...
```
`get_key` is a simple wrapper of `calculate_key`. Let's take a look at calculate_key, which calls `calc(0x186b5)`.
 
 ```
    0x0000000000400796 <+4>:     mov    $0x186b5,%edi
   0x000000000040079b <+9>:     callq  0x400706 <calc>
```

Further disassembling of `calc` reveals the following C code equivalent. This part is easy to translate because optimization is disabled when compiling the code.
```
uint32_t calc(uint32_t x)
{
	if (x <= 4) return x * x + 0x2345;
	return calc(x – 1) – calc(x – 2) + calc(x-3) – calc(x-4) + calc(x – 5) * 0x1234;
}
```

Ah, this is slow because of recursion. Thus, we implement a [non-recursive version](https://github.com/jespiron/picoCTF-2018/blob/master/reversing/be-quick-or-be-dead-3/get_key.c) to calculate the value for `x186b5`, of which we get `0x221d8eea`.

We run the program under the debugger

```
(gdb) break main
Breakpoint 1 at 0x4008aa
(gdb) run
...
(gdb) disassemble main
Dump of assembler code for function main:
   0x00000000004008a6 <+0>:     push   %rbp
   0x00000000004008a7 <+1>:     mov    %rsp,%rbp
=> 0x00000000004008aa <+4>:     sub    $0x10,%rsp
```

Let's disable `set_key` and `calc` by changing the instruction to `ret` (opcode `0xc3`).

```
(gdb) set {char}&set_timer=0xc3
(gdb) set {char}&calc=0xc3
```

Add a breakpoint at `calc`. Once we hit the breakpoint, set register `eax` to our calculated value `0x221d8eea`.
```
(gdb) break calc
Breakpoint 2 at 0x400706
(gdb) cont
Continuing.
Be Quick Or Be Dead 3
=====================

Calculating key...

Breakpoint 2, 0x0000000000400706 in calc ()
(gdb) set ($eax)=0x221d8eea
(gdb) cont
...
picoCTF{dynamic_pr0gramming_ftw_a0b0b7f8}
```

Voila!
