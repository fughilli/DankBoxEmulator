#!/usr/bin/python

import sys

## OPCODE, RA?, RB?, RC?, IMM

##
##  Instruction lookup table
##
instr_dict = {
"ADD"   : (0x00, (1, 1, 1, 0)),
"ADDI"  : (0x01, (1, 1, 0, 1)),
"ADDUI" : (0x02, (1, 1, 0, 1)),
"LUH"   : (0x03, (1, 0, 0, 1)),
"MUL"   : (0x04, (1, 1, 1, 0)),
"MULI"  : (0x05, (1, 1, 0, 1)),
"PUSH"  : (0x06, (1, 0, 0, 0)),
"PUSHI" : (0x07, (0, 0, 0, 1)),
"POP"   : (0x08, (1, 0, 0, 0)),
"JUMP"  : (0x09, (1, 0, 0, 0)),
"JUMPI" : (0x0A, (1, 0, 0, 1)),
"BR"    : (0x0B, (1, 0, 0, 0)),
"BI"    : (0x0C, (0, 0, 0, 1)),
"CALL"  : (0x0D, (1, 0, 0, 0)),
"MOV"   : (0x0E, (1, 1, 0, 0)),
"HALT"  : (0x0F, (0, 0, 0, 0)),
"DUMP"  : (0x10, (0, 0, 0, 0)),
"LOAD"  : (0x11, (1, 1, 0, 0)),
"STOR"  : (0x12, (1, 1, 0, 0)),
"RET"   : (0x13, (0, 0, 0, 0)),
"JZ"    : (0x14, (1, 1, 0, 0)),
"JZI"   : (0x15, (1, 1, 0, 1)),
"BZ"    : (0x16, (1, 1, 0, 0)),
"BZI"   : (0x17, (1, 0, 0, 1)),
"JLT"   : (0x18, (1, 1, 0, 0)),
"JLTI"  : (0x19, (1, 1, 0, 1)),
"BLT"   : (0x1A, (1, 1, 0, 0)),
"BLTI"  : (0x1B, (1, 0, 0, 1)),
"SZ"    : (0x1C, (1, 1, 1, 0)),
"SLT"   : (0x1D, (1, 1, 1, 0)),
}

##
##  Returns the number corresponding to the supplied string.
##
def parse_num(numberstr):
    prefix, suffix = numberstr[:2], numberstr[2:]
    try:
        return {
                "0x" : lambda : int(suffix, 16),
                "0b" : lambda : int(suffix, 2),
                "0o" : lambda : int(suffix, 8)
        }[prefix]()
    except Exception:
        return int(numberstr)

##
##  Returns the register number that corresponds to the supplied register name.
##
def get_reg_num(regname):
    if regname[0] == 'R':
        ret = int(regname[1:])
        if not 0 <= ret <= 15:
            raise Exception("Unknown register %s" % regname)
        return ret
    try:
        return {'PC' : 12,
                'LR' : 13,
                'SP' : 14,
                'SR' : 15}[regname]
    except Exception:
        raise Exception("Unknown register %s" % regname)

##
##  Returns the immediate value that corresponds to the supplied register name.
##
def get_immediate(immstr):
    ret = parse_num(immstr)
    if not 0 <= ret <= 65535:
        raise Exception("Immediate out of range: %s" % immstr)

    return ret

if len(sys.argv) != 3:
    print (
"""USAGE:
    %s [ASM FILE] [OUT FILE]""" % (sys.argv[0]))
    exit(1)

filelines = open(sys.argv[1]).readlines()
outfile = open(sys.argv[2], 'w')

for line in filelines:
    
    lineparts = line.strip().split(' ')

    sys.stdout.write(str(lineparts) + ', ')

    opcode, args = instr_dict[lineparts[0]]

    if not sum(args) == len(lineparts[1:]):
        raise Exception(("Incorrect number of arguments for instruction %s;" +
                        " expects %d, given %d") % lineparts[0], sum(args), 
                        len(lineparts[1:]))
    
    instr_val = opcode << 24

    lineparts = lineparts[1:]

    for i in range(3):
        if(args[i]):
            instr_val = instr_val | (get_reg_num(lineparts[0]) << (20 - 4*i))
            lineparts = lineparts[1:]

    if(args[3]):
        instr_val = instr_val | (get_immediate(lineparts[0]) << 0)

    sys.stdout.write("0x%08x\n" % instr_val)

    instr_bytes = map(chr, [
        (instr_val >> 24) & 0xFF, 
        (instr_val >> 16) & 0xFF,
        (instr_val >> 8) & 0xFF,
        (instr_val >> 0) & 0xFF
        ])

    outfile.write(reduce(lambda a,b : a+b, instr_bytes[::-1]))

outfile.close()
