# DankBoxEmulator
Soft processor implementation for prototyping the DankCore ISA. Designed to run DankOS (lm4f-BoSS).

Compiling
---------
Compile with `ninja`; this will build DankBoxEmulator into the binary `emu`.

Assembling DankCore ASM
-----------------------
To assemble a binary, use the assembler (`asm.py`). To assemble the hello world program, run `./asm.py programs/hello_world.asm binaries/hello_world.bin`.

Running
-------
Run the assembled hello world binary with `./emu binaries/hello_world.bin`.
