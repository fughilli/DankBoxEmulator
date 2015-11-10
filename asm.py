#!/usr/bin/python

import sys

def lambda_debug(val, message):
    #print message, val
    return val

ENDIANNESS_LITTLE = 1
ENDIANNESS_BIG = 0

ENDIANNESS = ENDIANNESS_LITTLE

FLASH_OFFSET = 0x1000000
FLASH_LENGTH = 256 * 1024

## OPCODE, RA?, RB?, RC?, IMM

##
##  Flags for specifying the kinds of immediates that instructions accept.
##
IMMFLAG_WORD = 8
IMMFLAG_LABEL = 4
IMMFLAG_UNSIGNED = 2
IMMFLAG_SIGNED = 1

##
##  Instruction lookup table. Each entry is of the form:
##      "<instruction name>" :
##          (<opcode>, (<ra?>, <rb?>, <rc?>, <immtype>), <instr width>)
##
instr_dict = {
"ADD"   : (0x00, (1, 1, 1, 0), 4),
"ADDI"  : (0x01, (1, 1, 0, 1), 4),
"ADDUI" : (0x02, (1, 1, 0, 2), 4),
"LUH"   : (0x03, (1, 0, 0, 1), 4),
"MUL"   : (0x04, (1, 1, 1, 0), 4),
"MULI"  : (0x05, (1, 1, 0, 1), 4),
"PUSH"  : (0x06, (1, 0, 0, 0), 4),
"PUSHI" : (0x07, (0, 0, 0, 1), 4),
"POP"   : (0x08, (1, 0, 0, 0), 4),
"JUMP"  : (0x09, (1, 0, 0, 0), 4),
"JUMPI" : (0x0A, (1, 0, 0, 1), 4),
"BR"    : (0x0B, (1, 0, 0, 0), 4),
"BI"    : (0x0C, (0, 0, 0, 5), 4),
"CALL"  : (0x0D, (1, 0, 0, 0), 4),
"MOV"   : (0x0E, (1, 1, 0, 0), 4),
"HALT"  : (0x0F, (0, 0, 0, 0), 4),
"DUMP"  : (0x10, (0, 0, 0, 0), 4),
"LOAD"  : (0x11, (1, 1, 0, 0), 4),
"STOR"  : (0x12, (1, 1, 0, 0), 4),
"RET"   : (0x13, (0, 0, 0, 0), 4),
"JZ"    : (0x14, (1, 1, 0, 0), 4),
"JZI"   : (0x15, (1, 1, 0, 1), 4),
"BZ"    : (0x16, (1, 1, 0, 0), 4),
"BZI"   : (0x17, (1, 0, 0, 5), 4),
"JLT"   : (0x18, (1, 1, 0, 0), 4),
"JLTI"  : (0x19, (1, 1, 0, 1), 4),
"BLT"   : (0x1A, (1, 1, 0, 0), 4),
"BLTI"  : (0x1B, (1, 0, 0, 5), 4),
"SZ"    : (0x1C, (1, 1, 1, 0), 4),
"SLT"   : (0x1D, (1, 1, 1, 0), 4),
"AND"   : (0x1E, (1, 1, 1, 0), 4),
"ANDI"  : (0x1F, (1, 1, 0, 2), 4),
"OR"    : (0x20, (1, 1, 1, 0), 4),
"ORI"   : (0x21, (1, 1, 0, 2), 4),
"INV"   : (0x22, (1, 1, 0, 0), 4),
"XOR"   : (0x23, (1, 1, 1, 0), 4),
"XORI"  : (0x24, (1, 1, 0, 2), 4),
"LOADH" : (0x25, (1, 1, 0, 0), 4),
"LOADB" : (0x26, (1, 1, 0, 0), 4),
"STORH" : (0x27, (1, 1, 0, 0), 4),
"STORB" : (0x28, (1, 1, 0, 0), 4),
"SAR"   : (0x29, (1, 1, 1, 0), 4),
"SLL"   : (0x3A, (1, 1, 1, 0), 4),
"SLR"   : (0x3B, (1, 1, 1, 0), 4),
"SARI"  : (0x3C, (1, 1, 0, 1), 4),
"SLRI"  : (0x3D, (1, 1, 0, 1), 4),
"DIV"   : (0x3E, (1, 1, 1, 0), 4),
"DIVI"  : (0x3F, (1, 1, 0, 1), 4),
"DIVUI" : (0x40, (1, 1, 0, 1), 4),
"MOVW"  : (0x41, (1, 0, 0, 8), 8),
"BALI"  : (0x42, (0, 0, 0, 5), 4),
"JAL"   : (0x43, (1, 0, 0, 0), 4),
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
##  Returns the bytes for a given integer value, in the specified endianness.
##
def get_bytes(val, num, end=ENDIANNESS_LITTLE):
    if(end == ENDIANNESS_LITTLE):
        ret = []
        for i in range(num):
            ret.append((val >> (i*8)) & 0xFF)
        return ret
    elif(end == ENDIANNESS_BIG):
        return get_bytes(val, num, ENDIANNESS_LITTLE)[::-1]
    else:
        raise Exception("Invalid endianness!")
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
##  Parses a label line of the form <_[label]@[address]:>. Returns a tuple of
##  the form (label, address). If no address is provided, then None is
##  returned in its place.
##
def parse_label(line):
    # Get everything up to the ':'
    line = line[:line.find(':')].strip()

    # If the line contains '@', the label has an absolute address specified
    if '@' in line:
        # Split the label and address
        ret = line.split('@')

        # Parse the address
        ret[1] = parse_num(ret[1])

        return tuple(ret)

    # No address was specified. Return (line, None)
    return (line, None)

##
##  Preparses an assembly instruction string. Returns a tuple of the form:
##      (<opcode>, <raidx>, <rbidx>, <rcidx>, <imm>)
##
##  <imm> can be either a string or an integer. Labels cannot have their
##      addresses resolved until the entire program has been parsed, so they
##      will be returned as strings from this function.
##
def preparse_instr(line):
    # Break the line on spaces to get the lineparts
    lineparts = line.strip().split(' ')

    # Extract the opcode and argument specification from the instruction
    # dictionary.
    opcode, args, width = instr_dict[lineparts[0]]

    # If there are not as many operands to the instruction as expected
    # (according to the instruction dictionary), then throw out.
    if not sum(map(lambda x : 1 if x else 0, args)) == len(lineparts[1:]):
        raise Exception(("Incorrect number of arguments for instruction %s;" +
                        " expects %d, given %d") % (lineparts[0], sum(args),
                        len(lineparts[1:])))

    # Initialize the return list.
    ret = [opcode, ]

    # Cut out the opcode part of the line.
    lineparts = lineparts[1:]

    # For each of the potential register labels, compute and store the
    # register numbers into the return list.
    for i in range(3):
        if(args[i]):
            ret.append(get_reg_num(lineparts[0]))
            lineparts = lineparts[1:]
        else:
            ret.append(0)

    # If the immediate field is present, try to parse it as each of the
    # following (in that order) if the flag for that interpretation is set in
    # the instruction dictionary:
    #   1) An unsigned immediate
    #   2) A signed immediate
    #   3) A branch address (for this interpretation, just return the string of
    #       the branch address in place of an immediate. The actual address
    #       will be resolved in a later step).
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
                return immfield
            except Exception:
                pass
        if immflags & IMMFLAG_WORD:
            try:
                return immfield
            except Exception:
                pass
        raise Exception("Immediate \"%s\" could not be parsed." % immfield)

    ##    instr_val = instr_val | (
    ##            (get_immediate(lineparts[0]) << 0) if (args[3] == 2) else
    ##            (get_immediate_signed(lineparts[0]) << 0))

    if(args[3]):
        ret.append(_parse_immfield(lineparts[0], args[3]))
    else:
        ret.append(0)

    ret.append(width)

    return tuple(ret)

##
##  Region class. Allows checking intersections between regions.
##
class Region(object):
    ##
    ##  Constructor.
    ##
    ##  @arg data An list of bytes in this region. The value reported by
    ##      .length() is equivalent to len(data).
    ##  @arg label The label associated with this region. Used to look up the
    ##      region offset.
    ##  @arg label_lookup A function which maps labels to addresses.
    ##
    def __init__(self, data, label, label_lookup):
        self.data = data
        self.label = label
        self.label_lookup = label_lookup

    def offset(self):
        return self.label_lookup(self.label)

    def length(self):
        retlen = sum(map(lambda x : x.width(), self.data))

        if(retlen % WORD_WIDTH):
            return retlen + (WORD_WIDTH - (retlen % WORD_WIDTH))

        return retlen

    def intersects(self, rother):
        if ((self.offset() <= rother.offset()) and
            (rother.offset() < self.offset() + self.length())):
            return True
        if ((rother.offset() <= self.offset()) and
            (self.offset() < rother.offset() + rother.length())):
            return True

        return False

    def contains(self, rother):
        if((self.offset() <= rother.offset()) and
           ((rother.offset() + rother.length()) <= \
            (self.offset() + self.length()))):
            return True

        return False

    def expandData(self):
        ret = []
        ## print "Expanding data for region ", self.label

        for datum in self.data:
            ## print "\tDatum: ", datum
            ret.extend(datum.value())

        retlen = len(ret)

        if(retlen % WORD_WIDTH):
            ret.extend([0] * (WORD_WIDTH - (retlen % WORD_WIDTH)))

        return ret

##
##  Datum placeholder class to abstract value calculation. Instances of this
##      type are used to populate Region.data.
##
class Datum(object):
    def __init__(self, value):
        self.__value__ = value

    ##
    ##  Returns the value of this datum.
    ##
    def value(self):
        return self.__value__

    ##
    ##  Returns the width (in bytes) of this datum.
    ##
    def width(self):
        return len(self.__value__)

##
##  Overridden Datum for instructions. value() is implemented to call the
##      label_lookup() and pc_lookup() callbacks when calculating the binary
##      instruction value.
##
class InstructionDatum(Datum):
    def __init__(self, opcode, raidx, rbidx, rcidx, imm, width,
                 label_lookup=lambda : 0, pc_lookup=lambda : 0):
        self.__width__ = width
        self.imm = imm
        self.raidx = raidx
        self.rbidx = rbidx
        self.rcidx = rcidx
        self.opcode = opcode
        self.label_lookup = label_lookup
        self.pc_lookup = pc_lookup

    def __value_generic__(self):
        if type(self.imm) == str:
            self.imm = self.label_lookup(self.imm) - self.pc_lookup()

        instr = (self.opcode & 0xFF)
        instr <<= 4
        instr |= (self.raidx & 0xF)
        instr <<= 4
        instr |= (self.rbidx & 0xF)
        instr <<= 4
        instr |= (self.rcidx & 0xF)
        instr <<= 12
        instr |= (self.imm & 0xFFFF)

        return get_bytes(instr, 4)

    def __value_movw__(self):
        try:
            self.imm = parse_num(self.imm)
        except Exception:
            self.imm = self.label_lookup(self.imm)

        instr = [0, 0]
        instr[0] = (instr_dict["LUH"][0] & 0xFF)
        instr[0] <<= 4
        instr[0] |= (self.raidx & 0xF)
        instr[0] <<= 20
        instr[0] |= ((self.imm >> 16) & 0xFFFF)

        instr[1] = (instr_dict["ADDUI"][0] & 0xFF)
        instr[1] <<= 4
        instr[1] |= (self.raidx & 0xF)
        instr[1] <<= 4
        instr[1] |= (self.raidx & 0xF)
        instr[1] <<= 16
        instr[1] |= (self.imm & 0xFFFF)

        return (get_bytes(instr[0], 4) + get_bytes(instr[1], 4))


    def value(self):
        pseudo_opcode_map = { instr_dict["MOVW"][0] : self.__value_movw__ }
        if not self.opcode in pseudo_opcode_map.keys():
            return self.__value_generic__()
        else:
            return pseudo_opcode_map[self.opcode]()

    def width(self):
        return self.__width__

##
##  Places a region into memory.
##
##  @arg region A region object containing data to be placed into memory.
##  @arg memory A list of bytes into which the region will be placed.
##  @arg prog_zero_address The target memory address that serves as the first
##          writable location for instructions.
##
def place_memory(region, memory, prog_zero_address):
    # Determine where the current end of memory is.
    end_mem_byte_addr = len(memory)

    # Determine where the new end of memory will be once the region is added.
    new_end_mem_byte_addr = \
        ((region.offset() + region.length()) - prog_zero_address)

    # If the region extends past the end of the current memory list
    if(end_mem_byte_addr < new_end_mem_byte_addr):
        # Extend the memory list to accomodate the region.
        memory.extend([0]*(new_end_mem_byte_addr - end_mem_byte_addr))

    # Copy the bytes from the region into memory.
    # TODO: do this with a slice assignment.

    # First check that the region is aligned on a word boundary.
    if(region.offset() % 4):
        raise Exception("Region %s is not aligned on a word boundary." %
                        region.label)

    # Expand the region's data into a byte array.
    expandedData = region.expandData()

    # Copy the bytes.
    for i,byte in enumerate(expandedData):
        memory[(region.offset() - prog_zero_address) + i] = byte

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
                                (region.label, region2.label))

##
##  Check that a region is in the flash region.
##
def check_in_flash(regions):
    for region in regions:
        if not ((region.offset() >= FLASH_OFFSET) and \
                (region.offset() + region.length()) <= \
                (FLASH_OFFSET + FLASH_LENGTH)):
            raise Exception("Region %s does not lie in flash." % region.sym)

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

    # A dictionary that maps labels to functions that return addresses.
    region_labels = dict()

    ##
    ##  Returns an address for a label.
    ##
    def _resolve_label(label):
        return region_labels[label]()

    current_region = None

    # For each line in the input assembly file, determine if the line is one of
    # the following:
    #   1) A region tag
    #   2) A blank line
    #   3) An instruction
    #   4) A raw data word/byte
    for line in filelines:

        ## Parse a line beginning with _ as a label (with address).
        if line[0] == '_':
            # Parse the label and address
            label,addr = parse_label(line)

            # If there was an address, this is a new region
            if addr:
                if current_region:
                    regions.append(current_region)

                ## print "Region ", label, " at address ", hex(addr)

                region_labels[label] = lambda x=addr : x

                current_region = Region([], label, _resolve_label)
            # If there was no address, this label is relatively placed
            else:
                # Compute the address by looking up the size of the instructions
                # currently in the parent region and adding it to the parent
                # region's address
                closure_region = current_region
                current_data_len = closure_region.length()

                ## print "Region ", label, " in base region ", \
                ##     current_region.label, " with current length ", \
                ##     current_data_len, " (addr ", hex(current_data_len + \
                ##     current_region.offset()), ")"

                region_labels[label] = \
                        lambda reg=closure_region,length=current_data_len : \
                        reg.offset() + length
                    ##lambda : lambda_debug(closure_region.offset(), \
                    ##                      "%s offset: " % \
                    ##                          closure_region.label) + \
                    ##         lambda_debug(current_data_len, "length: ")

        ## Parse a line beginning with $w: as a raw word value.
        ##                             $h: as a raw halfword value.
        ##                             $b: as a raw byte value.
        elif line[:3] == '$w:' or \
             line[:3] == '$h:' or \
             line[:3] == '$b:' :

            # Split the line
            line_prefix,line_suffix = line[:3],line[3:]

            field_width = ({ '$w:' : 4,
                             '$h:' : 2,
                             '$b:' : 1 }[line_prefix])

            current_region.data.append(
                Datum(get_bytes(parse_num(line_suffix), field_width)))

        ## Skip empty lines.
        elif line.strip() == '' or line[0] == '#':
            continue

        ## Anything else is an instruction.
        else:
            # Construct an InstructionDatum from the preparsed instruction
            instr_args = preparse_instr(line)
            instr_datum = InstructionDatum(*instr_args)

            ## print "Parsed instruction string '%s' as %s" % (line, instr_args)

            # Calculate the current region length (to calculate PC)
            current_region_length = current_region.length()

            # PC lookup for this instruction is based on the region offset +
            #   the current region length
            instr_datum.pc_lookup = lambda reg=current_region, \
                                           length=current_region_length: \
                                           reg.offset() + \
                                           length

            # Pass the toplevel label lookup function
            instr_datum.label_lookup = _resolve_label

            current_region.data.append(instr_datum)

    if current_region:
        regions.append(current_region)

    ## print "Regions: ", regions
    ## print "Region labels: ", region_labels
    ## print "Resolved region labels: ", \
    ##        map(lambda kv : str(kv[0]) + ': ' + hex(kv[1]()), \
    ##        region_labels.iteritems())

    # Check that regions do not intersect one another, and that they lie in
    # flash.
    check_intersections(regions)
    check_in_flash(regions)

    # Place regions into memory.
    for region in regions:
        place_memory(region, memory, FLASH_OFFSET)

    # Write the memory contents to the output file.
    for b in memory:
        outfile.write(chr(b))

    outfile.close()
