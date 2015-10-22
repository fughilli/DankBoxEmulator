#!/usr/bin/python

import sys

FLASH_OFFSET = 0x1000000
FLASH_LENGTH = 256 * 1024

## OPCODE, RA?, RB?, RC?, IMM

##
##  Flags for specifying the kinds of immediates that instructions accept.
##
IMMFLAG_LABEL = 4
IMMFLAG_UNSIGNED = 2
IMMFLAG_SIGNED = 1

##
##  Instruction lookup table.
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
"BI"    : (0x0C, (0, 0, 0, 5)),
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
"BZI"   : (0x17, (1, 0, 0, 5)),
"JLT"   : (0x18, (1, 1, 0, 0)),
"JLTI"  : (0x19, (1, 1, 0, 1)),
"BLT"   : (0x1A, (1, 1, 0, 0)),
"BLTI"  : (0x1B, (1, 0, 0, 5)),
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

    ret = 0
    try:
        ret = {
                "0x" : lambda : int(suffix, 16),
                "0b" : lambda : int(suffix, 2),
                "0o" : lambda : int(suffix, 8)
        }[prefix]()
    except Exception:
        ret = int(numberstr)
    return -ret if negative else ret
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
##  Check if the passed value can be represented as a 16-bit two's-complement
##  signed integer.
##
def check_imm_signed_range(imm):
    return (-32768 <= imm and imm <= 32767)

##
##  Convert a signed immediate value to an unsigned bitmask.
##
def convert_s_imm_u(imm):
    return (65536-abs(imm)) if (imm < 0) else imm

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

    return convert_s_imm_u(ret)

##
##  Returns the word that corresponds to the supplied instruction string.
##
##  @arg pcaddr The PC address of the instruction being parsed.
##  @arg get_region_address A function which maps symbols to addresses.
##
def parse_instr(line, pcaddr, get_region_address):
    # Break the line on spaces to get the lineparts
    lineparts = line.strip().split(' ')

    # Extract the opcode and argument specification from the instruction
    # dictionary.
    opcode, args = instr_dict[lineparts[0]]

    # If there are not as many operands to the instruction as expected
    # (according to the instruction dictionary), then throw out.
    if not sum(map(lambda x : 1 if x else 0, args)) == len(lineparts[1:]):
        raise Exception(("Incorrect number of arguments for instruction %s;" +
                        " expects %d, given %d") % (lineparts[0], sum(args),
                        len(lineparts[1:])))

    # Save the opcode to the instr_val (the output machine code word).
    instr_val = opcode << 24

    # Cut out the opcode part of the line.
    lineparts = lineparts[1:]

    # For each of the potential register symbols, compute and store the
    # register numbers into instr_val.
    for i in range(3):
        if(args[i]):
            instr_val = instr_val | (get_reg_num(lineparts[0]) << (20 - 4*i))
            lineparts = lineparts[1:]

    # If the immediate field is present, try to parse it as each of the
    # following (in that order) if the flag for that interpretation is set in
    # the instruction dictionary:
    #   1) An unsigned immediate
    #   2) A signed immediate
    #   3) A branch address (for this interpretation, compute the offset from
    #      pcaddr to store as the immediate. If the branch length exceeds the
    #      immediate representation, throw out.
    def _parse_immfield(immfield, immflags):
        if immflags & IMMFLAG_UNSIGNED:
            try:
                return get_immediate(immfield) << 0
            except Exception:
                pass
        if immflags & IMMFLAG_SIGNED:
            try:
                return get_immediate_signed(immfield) << 0
            except Exception:
                pass
        if immflags & IMMFLAG_LABEL:
            try:
                immval = get_region_address(immfield) - pcaddr
                if check_imm_signed_range(immval):
                    return convert_s_imm_u(immval)
            except Exception:
                pass
        raise Exception("Immediate \"%s\" could not be parsed." % immfield)

    ##    instr_val = instr_val | (
    ##            (get_immediate(lineparts[0]) << 0) if (args[3] == 2) else
    ##            (get_immediate_signed(lineparts[0]) << 0))

    if(args[3]):
        instr_val |= _parse_immfield(lineparts[0], args[3])

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
##  Parses a symbol line of the form <_[symbol]@[address]:>. Returns a tuple of
##  the form (symbol, address). If no address is provided, then None is
##  returned in its place.
##
def parse_symbol(line):
    # Get everything up to the ':'
    line = line[:line.find(':')].strip()

    # If the line contains '@', the symbol has an absolute address specified
    if '@' in line:
        # Split the symbol and address
        ret = line.split('@')

        # Parse the address
        ret[1] = parse_num(ret[1])

        return tuple(ret)

    # No address was specified. Return (line, None)
    return (line, None)

##
##  Region class. Allows checking intersections between regions.
##
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

    def contains(self, rother):
        if((self.offset <= rother.offset) and
           ((rother.offset + rother.length) <= (self.offset + self.length))):
            return True

        return False

##
##  Declare a flash region to be used in checking for valid placement.
##
flash_region = Region([], 'flash', FLASH_OFFSET, FLASH_LENGTH)

##
##  Converts the stored data into Region object instances.
##
def convert_to_regions(code_regions, regions):
    for data,sym in code_regions:
        addr = region_symbols[sym]

        if (addr % 4):
            raise Exception("Region %s is not aligned on a word boundary (%08x)" %
                            (sym, addr))

        region_length = len(data)*4

        regions.append(Region(data, sym, addr, region_length))

##
##  Checks for intersecting regions.
##
def check_intersections(regions):
    for region in regions:
        for region2 in regions:
            if region is region2:
                continue
            elif region.intersects(region2):
                raise Exception("Region %s intersects %s." %
                                (region.sym, region2.sym))

##
##  Check that a region is in the flash region.
##
def check_in_flash(regions):
    for region in regions:
        if not flash_region.intersects(region):
            raise Exception("Region %s does not lie in flash." % region.sym)

##
##  Places a region into memory.
##
def place_memory(region, memory):
    new_end_mem_byte_addr = ((region.offset + region.length) - FLASH_OFFSET)
    end_mem_byte_addr = len(memory)*4;
    if(end_mem_byte_addr < new_end_mem_byte_addr):
        memory.extend([0]*((new_end_mem_byte_addr - end_mem_byte_addr)/4))

    for i,word in enumerate(region.data):
        memory[((region.offset - FLASH_OFFSET)/4) + i] = word

##
##  If this is being run as a script, assemble the provided assembly file.
##
if __name__ == '__main__':

    if len(sys.argv) != 3:
        print (
"""USAGE:
    %s [ASM FILE] [OUT FILE]""" % (sys.argv[0]))
        exit(1)

    filelines = open(sys.argv[1]).readlines()
    outfile = open(sys.argv[2], 'w')

    # Declare lists for Region objects and memory contents.
    regions = []
    memory = []

    # A list of code regions.
    code_regions = []

    # One code region datum. Contains an array of words, and a symbol that
    # represents the start address of the array.
    code_region_data = ([], None)

    # A dictionary that maps symbols to addresses.
    region_symbols = dict()

    # For each line in the input assembly file, determine if the line is one of
    # the following:
    #   1) A region tag
    #   2) A blank line
    #   3) An instruction
    #   4) A raw data word/byte
    for line in filelines:
        ## Returns the address for a given symbol.
        def get_address_of_symbol(symbol):
            return region_symbols[symbol]

        ## Returns the PC of the instruction currently being parsed.
        def get_current_pc():
            return get_address_of_symbol(code_region_data[1]) + \
                   (len(code_region_data[0])*4)


        ## Parse a line beginning with _ as a region tag (with address).
        if line[0] == '_':
            # Parse the symbol and address
            sym,addr = parse_symbol(line)

            # If there was an address, this is a new region
            if addr:
                if code_region_data[1]:
                    code_regions.append(code_region_data)

                region_symbols[sym] = addr

                code_region_data = ([], sym)
            # If there was no address, this symbol is relatively placed
            else:
                # Compute the address by looking up the size of the instructions
                # currently in the parent region and adding it to the parent
                # region's address
                region_symbols[sym] = get_current_pc()

        ## Parse a line beginning with $: as a raw word value.
        elif line[:2] == '$:':
            code_region_data[0].append(parse_num(line[2:]))

        ## Skip empty lines.
        elif line.strip() == '' or line[0] == '#':
            continue

        ## Anything else is an instruction.
        else:
            code_region_data[0].append(parse_instr(line, get_current_pc(),
                                       get_address_of_symbol))

    if code_region_data[1]:
        code_regions.append(code_region_data)

    ## print "Region symbols: ", \
    ##       map(lambda i : (i[0],hex(i[1])), region_symbols.iteritems())

    convert_to_regions(code_regions, regions)

    # Check that regions do not intersect one another, and that they lie in
    # flash.
    check_intersections(regions)
    check_in_flash(regions)

    # Place regions into memory.
    for region in regions:
        place_memory(region, memory)

    # Write the memory contents to the output file.
    for w in memory:
        outfile.write(word_to_str(w))

    outfile.close()
