#!/usr/bin/python

import sys

FLASH_OFFSET = 0x1000000
FLASH_LENGTH = 256 * 1024

## OPCODE, RA?, RB?, RC?, IMM

##
##  Instruction lookup table
##
instr_dict = {
"ADD"   : (0x00, (1, 1, 1, 0)),
"ADDI"  : (0x01, (1, 1, 0, 1)),
"ADDUI" : (0x02, (1, 1, 0, 2)),
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
    negative = 0
    if numberstr[0] == '-':
        numberstr = numberstr[1:]
        negative = 1
    prefix, suffix = numberstr[:2], numberstr[2:]
    try:
        return {
                "0x" : lambda : int(suffix, 16),
                "0b" : lambda : int(suffix, 2),
                "0o" : lambda : int(suffix, 8)
        }[prefix]()
    except Exception:
        return int(numberstr) if not negative else -int(numberstr)

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
    if not (0 <= ret and ret <= 65535):
        raise Exception("Immediate out of range: %s" % immstr)

    return ret

def get_immediate_signed(immstr):
    ret = parse_num(immstr)
    if not (-32768 <= ret and ret <= 65535):
        raise Exception("Immediate out of range: %s" % immstr)

    return (65536-abs(ret)) if (ret < 0) else ret

if len(sys.argv) != 3:
    print (
"""USAGE:
    %s [ASM FILE] [OUT FILE]""" % (sys.argv[0]))
    exit(1)

filelines = open(sys.argv[1]).readlines()
outfile = open(sys.argv[2], 'w')

##
##  Returns the word that corresponds to the supplied instruction string.
##
def parse_instr(line):
    # Break the line on spaces to get the lineparts
    lineparts = line.strip().split(' ')

##    sys.stdout.write(str(lineparts) + ', ')

    opcode, args = instr_dict[lineparts[0]]

    if not sum(map(lambda x : 1 if x else 0, args)) == len(lineparts[1:]):
        raise Exception(("Incorrect number of arguments for instruction %s;" +
                        " expects %d, given %d") % (lineparts[0], sum(args),
                        len(lineparts[1:])))

    instr_val = opcode << 24

    lineparts = lineparts[1:]

    for i in range(3):
        if(args[i]):
            instr_val = instr_val | (get_reg_num(lineparts[0]) << (20 - 4*i))
            lineparts = lineparts[1:]

    if(args[3]):

        instr_val = instr_val | (
                (get_immediate(lineparts[0]) << 0) if (args[3] == 2) else
                (get_immediate_signed(lineparts[0]) << 0))

##    sys.stdout.write("0x%08x\n" % instr_val)

    return instr_val

##
##  Converts a word (32-bit integer) to a string of 4 characters,
##  little-endian.
##
def word_to_str(word):
    word_bytes = map(chr, [
        (word >> 24) & 0xFF,
        (word >> 16) & 0xFF,
        (word >> 8) & 0xFF,
        (word >> 0) & 0xFF
        ])

    return reduce(lambda a,b : a+b, word_bytes[::-1])

##
##  A list of code regions.
##
code_regions = []

##
##  One code region datum. Contains an array of words, and a symbol that
##  represents the start address of the array.
##
code_region_data = ([], None)

##
##  A dictionary that maps symbols to addresses.
##
region_symbols = dict()

##
##  Parses a symbol line of the form <_[symbol]@[address]:>. Returns a tuple of
##  the form (symbol, address).
##
def parse_symbol(line):
    line = line[:line.find(':')].strip()

    ret = line.split('@')

    ret[1] = parse_num(ret[1])

    return ret

##
##  For each line in the input assembly file, determine if the line is one of
##  the following:
##      1) A region tag
##      2) A blank line
##      3) An instruction
##      4) A raw data word/byte
##
for line in filelines:
    ## Parse a line beginning with _ as a region tag (with address).
    if line[0] == '_':
        if code_region_data[1]:
            code_regions.append(code_region_data)

        sym,addr = parse_symbol(line)
        region_symbols[sym] = addr

        code_region_data = ([], sym)

    ## Parse a line beginning with $: as a raw word value.
    elif line[:2] == '$:':
        code_region_data[0].append(parse_num(line[2:]))

    ## Skip empty lines.
    elif line.strip() == '' or line[0] == '#':
        continue

    ## Anything else is an instruction.
    else:
        code_region_data[0].append(parse_instr(line))

if code_region_data[1]:
    code_regions.append(code_region_data)

class Region(object):
    def __init__(self, data, sym, offset, length):
        self.length = length
        self.offset = offset
        self.data = data
        self.sym = sym

    def intersects(self, rother):
        if ((self.offset <= rother.offset) and
            (rother.offset < self.offset + self.length)):
            return True
        if ((rother.offset <= self.offset) and
            (self.offset < rother.offset + rother.length)):
            return True

        return False

regions = []

##
## Convert the stored data into Region object instances.
##
for data,sym in code_regions:
    addr = region_symbols[sym]

    if (addr % 4):
        raise Exception("Region %s is not aligned on a word boundary (%08x)" %
                        (sym, addr))

    region_length = len(data)*4

    regions.append(Region(data, sym, addr, region_length))

flash_region = Region([], 'flash', FLASH_OFFSET, FLASH_LENGTH)

##
##  Check for intersecting regions.
##
for region in regions:
    if not flash_region.intersects(region):
        raise Exception("Region %s does not lie in flash." % region.sym)
    for region2 in regions:
        if region is region2:
            continue
        elif region.intersects(region2):
            raise Exception("Region %s intersects %s." %
                            (region.sym, region2.sym))

memory = []

def place_memory(region, memory):
    new_end_mem_byte_addr = ((region.offset + region.length) - FLASH_OFFSET)
    end_mem_byte_addr = len(memory)*4;
    if(end_mem_byte_addr < new_end_mem_byte_addr):
        memory.extend([0]*((new_end_mem_byte_addr - end_mem_byte_addr)/4))

    for i,word in enumerate(region.data):
        memory[((region.offset - FLASH_OFFSET)/4) + i] = word

for region in regions:
    place_memory(region, memory)

for w in memory:
    outfile.write(word_to_str(w))

outfile.close()
