#include "global_config.h"
#include "processor.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

register_map_t proc_regs;
byte_t* real_memory;

/**
 * @brief Initializes the processor.
 */
void proc_init()
{
    /*
     * Initialize the registers to 0.
     */
    memset(&proc_regs, 0, sizeof(proc_regs));
    
    /*
     * Allocate memory for the processor. This includes the RAM and the ROM.
     */
    real_memory = (byte_t*)malloc(sizeof(byte_t) *
                                  (ARCH_RAM_SIZE + ARCH_ROM_SIZE));

    /*
     * Set the PC to the program entry point (beginning of ROM).
     */
    proc_regs.PC = ARCH_ROM_OFFSET;

    /*
     * Set the SP to the top of RAM.
     */
    proc_regs.SP = ARCH_RAM_OFFSET + ARCH_RAM_SIZE - sizeof(word_t);
}

/**
 * @brief Loads a program into ROM from a file.
 */
void proc_load_program(const char* fname)
{
    FILE* fp = fopen(fname, "r");
    
    int readval;

    int i = 0;

    while((readval = fgetc(fp)) != EOF)
    {
        if(global_verbosity)
            printf("Read byte from file: %02x\n", readval);
        //get_mem_byte((ARCH_ROM_OFFSET + i++)) = (byte_t)readval;
        real_memory[i++] = (byte_t)readval;
    }

    fclose(fp);
}

/**
 * @brief Decodes an instruction, passing the opcode, register numbers, and
 *        immediate to the caller via OUT arguments.
 */
void proc_instr_decode(word_t instr, regidx_t* ra, regidx_t* rb, regidx_t* rc,
                  word_t* imm, opcode_t* opcode)
{
    /*
     * Extract the opcode.
     */
    (*opcode) = (instr & ARCH_INSTR_OPC_MASK) >> ARCH_INSTR_OPC_OFFSET;

    /*
     * Extract the register indices.
     */
    (*ra) = (instr & ARCH_INSTR_RA_MASK) >> ARCH_INSTR_RA_OFFSET;
    (*rb) = (instr & ARCH_INSTR_RB_MASK) >> ARCH_INSTR_RB_OFFSET;
    (*rc) = (instr & ARCH_INSTR_RC_MASK) >> ARCH_INSTR_RC_OFFSET;

    /*
     * Extract the immediate.
     */
    (*imm) = (instr & ARCH_INSTR_IMM_MASK) >> ARCH_INSTR_IMM_OFFSET;
}

void proc_dump_regs()
{
    int i;

    printf("Contents of registers at PC=0x%08x:\n", proc_regs.PC);

    for(i = 0; i < 12; i++)
    {
        printf("R%d:\t0x%08x\n", i, proc_reg(i));
    }

    printf("PC:\t0x%08x\nLR:\t0x%08x\nSP:\t0x%08x\nSR:\t0x%08x\n\n",
           proc_regs.PC, proc_regs.LR, proc_regs.SP, proc_regs.SR);
}

/**
 * @brief Executes an instruction.
 */
bool proc_instr_execute(word_t instr)
{
    regidx_t ra, rb, rc;
    word_t imm;
    opcode_t opcode;

    proc_instr_decode(instr, &ra, &rb, &rc, &imm, &opcode);

    if(global_verbosity)
        printf("@0x%08x: Decoded 0x%08x"
               " --> (RA: %d, RB: %d, RC: %d, IMM: %d, OPC: 0x%02x)\n",
               proc_regs.PC, instr, ra, rb, rc, imm, opcode);

    /*
     * This will be used to store any new SR flags generated during this cycle.
     */
    word_t new_sr = 0;

    bool increment_pc = true;

    switch(opcode)
    {
        case PROC_OPCODE_ADD:
            proc_reg(rc) = proc_reg(ra) + proc_reg(rb);

            /*
             * Check for overflow.
             */
            if(proc_reg(ra) & proc_reg(rb) & ~proc_reg(rc) & 0x80000000)
                new_sr |= SR_ALU_O_FLAG;

            /*
             * Check for negative.
             */
            if(proc_reg(rc) & 0x80000000)
                new_sr |= SR_ALU_N_FLAG;

            /*
             * Check for zero.
             */
            if(proc_reg(rc) == 0)
                new_sr |= SR_ALU_Z_FLAG;

            break;

        case PROC_OPCODE_ADDI:
            proc_reg(rb) = proc_reg(ra) + proc_sign_extend_imm(imm);

            /*
             * Check for overflow.
             */
            if((proc_reg(ra) | proc_sign_extend_imm(imm)) & ~proc_reg(rb) &
               0x80000000)
                new_sr |= SR_ALU_O_FLAG;

            /*
             * Check for negative.
             */
            if(proc_reg(rb) & 0x80000000)
                new_sr |= SR_ALU_N_FLAG;

            /*
             * Check for zero.
             */
            if(proc_reg(rb) == 0)
                new_sr |= SR_ALU_Z_FLAG;


            break;

        case PROC_OPCODE_ADDUI:
            proc_reg(rb) = proc_reg(ra) + imm;

            /*
             * Check for overflow.
             */
            if(proc_reg(ra) & ~proc_reg(rb) & 0x80000000)
                new_sr |= SR_ALU_O_FLAG;

            /*
             * Check for negative.
             */
            if(proc_reg(rb) & 0x80000000)
                new_sr |= SR_ALU_N_FLAG;

            /*
             * Check for zero.
             */
            if(proc_reg(rb) == 0)
                new_sr |= SR_ALU_Z_FLAG;


            break;

        case PROC_OPCODE_HALT:
            return false;

        case PROC_OPCODE_DUMP:
            proc_dump_regs();
            break;

        case PROC_OPCODE_LUH:
            proc_reg(ra) &= ~0x0000FFFF;
            proc_reg(ra) |= imm << 16;
            break;

        case PROC_OPCODE_JUMP:
            proc_regs.PC = proc_reg(ra);

            increment_pc = false;
            break;

        case PROC_OPCODE_JUMPI:
            proc_regs.PC = proc_reg(ra) + proc_sign_extend_imm(imm);

            increment_pc = false;
            break;

        case PROC_OPCODE_BR:
            proc_regs.PC = proc_regs.PC + proc_reg(ra);


        case PROC_OPCODE_BI:
            proc_regs.PC = proc_regs.PC + proc_sign_extend_imm(imm);

            increment_pc = false;
            break;

        case PROC_OPCODE_MOV:
            proc_reg(rb) = proc_reg(ra);

            if(rb == 12)
                increment_pc = false;
            break;

        case PROC_OPCODE_LOAD:
            proc_reg(ra) = get_mem_word(proc_reg(rb));

            if(ra == 12)
                increment_pc = false;
            break;

        case PROC_OPCODE_STOR:
            get_mem_word(proc_reg(rb)) = proc_reg(ra);
            break;

        default:
            proc_regs.SR |= SR_FAULT_DECODE_FLAG; 
    } 

    if(increment_pc)
        proc_regs.PC += 4;

    proc_clear_alu_flags();

    proc_regs.SR |= new_sr;

    return true;
}
