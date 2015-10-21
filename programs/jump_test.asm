_print@0x1000100:
# Caller context save
PUSH R7
PUSH R8

# Store the print character (R0) to TXBUF
LUH R7 0x5000
STOR R0 R7

# Set the transmit flag
ADDUI R7 R7 8
LUH R8 0
ADDUI R8 R8 1
STOR R8 R7

# Caller context restore
POP R8
POP R7

# Jump unconditionally to link register
JUMP LR

_printn@0x1000200:
# Caller context save
PUSH LR
PUSH R0
PUSH R1
PUSH R2
PUSH R3

# Compute the address for _print into R3
LUH R3 0x0100
ADDUI R3 R3 0x0100

# Move the counter to R2
MOV R0 R2

# Load a word from the address given in R1 to R0
LOAD R0 R1

MOV PC LR
ADDUI LR LR 12
JUMP R3

# Increment R1 and decrement R2
ADDUI R1 R1 4
ADDI R2 R2 -1

BZI R2 8
BI -28

POP R3
POP R2
POP R1
POP R0
POP LR

JUMP LR

_data@0x1000500:
$:0x00000048
$:0x00000065
$:0x0000006c
$:0x0000006c
$:0x0000006f
$:0x00000020
$:0x00000077
$:0x0000006f
$:0x00000072
$:0x0000006c
$:0x00000064
$:0x00000021
$:0x0000000a

_main@0x1000000:
# Address 0x50000000 (uart txbuf) > R7
LUH R7 0x5000

# Character value 0x33 (!) > R8
LUH R8 0x0
ADDUI R8 R8 0x33

# Store R8 > MEM(R7)
STOR R8 R7

# Increment to address 0x50000008 (uart control)
ADDUI R7 R7 8

# Value 0x1 (uart transmit flag) > R8
LUH R8 0x0
ADDUI R8 R8 0x1

# Store R8 > MEM(R7)
STOR R8 R7

LUH R7 0xFFFF
LUH R8 0xAAAA

# Dump registers
# DUMP

# Compute jump address for _print
LUH R1 0x0100
ADDUI R1 R1 0x0100

# Save print character to R0
LUH R0 0
ADDUI R0 R0 0x34

# Save PC+12 to LR (skip over next two instructions on return)
MOV PC LR
ADDUI LR LR 12

# Jump to _print
JUMP R1

# DUMP

# Compute jump address for _printn
LUH R2 0x0100
ADDUI R2 R2 0x0200

# Compute the address of the _data section
LUH R1 0x0100
ADDUI R1 R1 0x0500

# Save print counter to R0
LUH R0 0
ADDUI R0 R0 13

# Save PC+12 to LR (skip over next two instructions on return)
MOV PC LR
ADDUI LR LR 12

# Jump to _print
JUMP R2

# DUMP


# Halt
HALT
