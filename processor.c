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
        /*
         * ADD instruction.
         *
         * RA + RB --> RC
         *
         * Sets overflow, zero, and negative flags as appropriate.
         *
         * TODO: Check that the flags are set correctly.
         */
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

        /*
         * ADDI instruction (signed immediate add).
         *
         * RA + SignExtend(imm) --> RB
         *
         * Sets overflow, zero, and negative flags as appropriate.
         *
         * TODO: Check that the flags are set correctly.
         */
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

        /*
         * ADDUI instruction (unsigned immediate add).
         *
         * RA + imm --> RB
         *
         * Sets overflow, zero, and negative flags as appropriate.
         *
         * TODO: Check that the flags are set correctly.
         */
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

        /*
         * HALT instruction.
         *
         * Stops the processor (terminates the emulator).
         */
        case PROC_OPCODE_HALT:
            return false;

        /*
         * DUMP meta-instruction.
         *
         * Dumps the contents of the registers (to stdout).
         */
        case PROC_OPCODE_DUMP:
            proc_dump_regs();
            break;

        /*
         * LUH instruction (load upper halfword).
         *
         * {imm[31:16], 16'b0} --> RA
         */
        case PROC_OPCODE_LUH:
            proc_reg(ra) = imm << 16;
            break;

        /*
         * JUMP instruction.
         *
         * RA --> PC
         */
        case PROC_OPCODE_JUMP:
            proc_regs.PC = proc_reg(ra);

            increment_pc = false;
            break;

        /*
         * JUMPI instruction (jump immediate).
         *
         * RA + SignExtend(imm) --> PC
         */
        case PROC_OPCODE_JUMPI:
            proc_regs.PC = proc_reg(ra) + proc_sign_extend_imm(imm);

            increment_pc = false;
            break;

        /*
         * BR instruction (branch).
         *
         * PC + RA --> PC
         */
        case PROC_OPCODE_BR:
            proc_regs.PC = proc_regs.PC + proc_reg(ra);

        /*
         * BI instruction (branch immediate).
         *
         * PC + SignExtend(imm) --> PC
         */
        case PROC_OPCODE_BI:
            proc_regs.PC = proc_regs.PC + proc_sign_extend_imm(imm);

            increment_pc = false;
            break;

        /*
         * MOV instruction (move).
         *
         * RA --> RB
         */
        case PROC_OPCODE_MOV:
            proc_reg(rb) = proc_reg(ra);

            if(rb == 12)
                increment_pc = false;
            break;

        /*
         * LOAD instruction.
         *
         * MEM[RB] --> RA
         */
        case PROC_OPCODE_LOAD:
            proc_reg(ra) = get_mem_word(proc_reg(rb));

            if(ra == 12)
                increment_pc = false;
            break;

        /*
         * STOR instruction.
         *
         * RA --> MEM[RB]
         */
        case PROC_OPCODE_STOR:
            get_mem_word(proc_reg(rb)) = proc_reg(ra);
            break;

        /*
         * JZ instruction (jump zero).
         *
         * if(RA == 0): RB --> PC
         */
        case PROC_OPCODE_JZ:
            if(proc_reg(ra) == 0)
            {
                proc_regs.PC = proc_reg(rb);
                increment_pc = false;
            }
            break;

        /*
         * JZI instruction (jump zero immediate).
         *
         * if(RA == 0): RB + SignExtend(imm) --> PC
         */
        case PROC_OPCODE_JZI:
            if(proc_reg(ra) == 0)
            {
                proc_regs.PC = proc_reg(rb) + proc_sign_extend_imm(imm);
                increment_pc = false;
            }
            break;

        /*
         * BZ instruction (branch zero).
         *
         * if(RA == 0): PC + RB --> PC
         */
        case PROC_OPCODE_BZ:
            if(proc_reg(ra) == 0)
            {
                proc_regs.PC += proc_reg(rb);
                increment_pc = false;
            }
            break;

        /*
         * BZI instruction (branch zero immediate).
         *
         * if(RA == 0): PC + SignExtend(imm) --> PC
         */
        case PROC_OPCODE_BZI:
            if(proc_reg(ra) == 0)
            {
                proc_regs.PC += proc_sign_extend_imm(imm);
                increment_pc = false;
            }
            break;

        /*
         * JLT instruction (jump zero).
         *
         * if(RA < 0): RB --> PC
         */
        case PROC_OPCODE_JLT:
            if(proc_reg(ra) < 0)
            {
                proc_regs.PC = proc_reg(rb);
                increment_pc = false;
            }
            break;

        /*
         * JLTI instruction (jump zero immediate).
         *
         * if(RA < 0): RB + SignExtend(imm) --> PC
         */
        case PROC_OPCODE_JLTI:
            if(proc_reg(ra) < 0)
            {
                proc_regs.PC = proc_reg(rb) + proc_sign_extend_imm(imm);
                increment_pc = false;
            }
            break;

        /*
         * BLT instruction (branch zero).
         *
         * if(RA < 0): PC + RB --> PC
         */
        case PROC_OPCODE_BLT:
            if(proc_reg(ra) < 0)
            {
                proc_regs.PC += proc_reg(rb);
                increment_pc = false;
            }
            break;

        /*
         * BLTI instruction (branch zero immediate).
         *
         * if(RA < 0): PC + SignExtend(imm) --> PC
         */
        case PROC_OPCODE_BLTI:
            if(proc_reg(ra) < 0)
            {
                proc_regs.PC += proc_sign_extend_imm(imm);
                increment_pc = false;
            }
            break;

        /*
         * MOVZ instruction (move zero).
         *
         * if(RA == 0): RB --> RC
         */
        case PROC_OPCODE_MOVZ:
            if(proc_reg(ra) == 0)
            {
                proc_reg(rc) = proc_reg(rb);

                if(rc == 12)
                    increment_pc = false;
            }
            break;

        /*
         * MOVLT instruction (move less than).
         *
         * if(RA == 0): RB --> RC
         */
        case PROC_OPCODE_MOVLT:
            if(proc_reg(ra) < 0)
            {
                proc_reg(rc) = proc_reg(rb);

                if(rc == 12)
                    increment_pc = false;
            }
            break;

        /*
         * PUSH instruction (push to stack).
         *
         * RA --> MEM[SP]; SP -= 4
         */
        case PROC_OPCODE_PUSH:
            get_mem_word(proc_regs.SP) = proc_reg(ra);
            proc_regs.SP -= 4;
            break;

        /*
         * POP instruction (pop from stack).
         *
         * SP += 4; MEM[SP] --> RA
         */
        case PROC_OPCODE_POP:
            proc_regs.SP += 4;
            proc_reg(ra) = get_mem_word(proc_regs.SP);

            if(ra == 12)
                increment_pc = false;
            break;

        /*
         * AND instruction (bitwise).
         *
         * RC = RA & RB
         */
        case PROC_OPCODE_AND:
            proc_reg(rc) = proc_reg(ra) & proc_reg(rb);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * ANDI instruction (bitwise).
         *
         * RC = RA & {16'b0,imm}
         */
        case PROC_OPCODE_ANDI:
            proc_reg(rc) = proc_reg(ra) & ((word_t)imm);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * OR instruction (bitwise).
         *
         * RC = RA | RB
         */
        case PROC_OPCODE_OR:
            proc_reg(rc) = proc_reg(ra) | proc_reg(rb);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * ORI instruction (bitwise).
         *
         * RC = RA | {16'b0,imm}
         */
        case PROC_OPCODE_ORI:
            proc_reg(rc) = proc_reg(ra) | ((word_t)imm);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * INV instruction (bitwise).
         *
         * RB = ~RA
         */
        case PROC_OPCODE_INV:
            proc_reg(rb) = ~proc_reg(ra);

            if(rb == 12)
                increment_pc = false;
            break;

        /*
         * XOR instruction (bitwise).
         *
         * RC = RA ^ RB
         */
        case PROC_OPCODE_XOR:
            proc_reg(rc) = proc_reg(ra) ^ proc_reg(rb);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * XORI instruction (bitwise).
         *
         * RB = RA ^ IMM
         */
        case PROC_OPCODE_XORI:
            proc_reg(rb) = proc_reg(ra) ^ ((word_t)imm);

            if(rb == 12)
                increment_pc = false;
            break;

        /*
         * LOADH instruction (load halfword).
         *
         * RA = MEM[RB]
         */
        case PROC_OPCODE_LOADH:
            proc_reg(ra) = ((word_t)get_mem_hword(proc_reg(rb)));

            if(ra == 12)
                increment_pc = false;
            break;

        /*
         * STORH instruction (store halfword).
         *
         * MEM[RB] = RA
         */
        case PROC_OPCODE_STORH:
            get_mem_hword(proc_reg(rb)) = ((hword_t)(proc_reg(ra) & 0xFFFF));
            break;

        /*
         * LOADB instruction (load byte).
         *
         * RA = {24'b0, MEM[RB]}
         */
        case PROC_OPCODE_LOADB:
            proc_reg(ra) = ((word_t)get_mem_byte(proc_reg(rb)));

            if(ra == 12)
                increment_pc = false;
            break;

        /*
         * STORB instruction (store byte).
         *
         * MEM[RB] = RA[7:0]
         */
        case PROC_OPCODE_STORB:
            get_mem_byte(proc_reg(ra)) = ((byte_t)(proc_reg(rb) & 0xFF));
            break;

        /*
         * SAR instruction (shift arithmetic right).
         *
         * RC = sign_extend(RA >> RB)
         */
        case PROC_OPCODE_SAR:
            proc_reg(rc) = proc_reg(ra) >> proc_reg(rb);
            if(proc_reg(ra) & 0x80000000)
                proc_reg(rc) |= proc_high_ones_mask(proc_reg(rb));

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * SLL instruction (shift logical left).
         *
         * RC = RA << RB
         */
        case PROC_OPCODE_SLL:
            proc_reg(rc) = proc_reg(ra) << proc_reg(rb);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * SLR instruction (shift logical right).
         *
         * RC = RA >> RB
         */
        case PROC_OPCODE_SLR:
            proc_reg(rc) = proc_reg(ra) >> proc_reg(rb);

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * SARI instruction (shift arithmetic right immediate).
         *
         * RC = sign_extend(RA >> sign_extend(IMM))
         */
        case PROC_OPCODE_SARI:
            proc_reg(rc) = proc_reg(ra) >> proc_sign_extend_imm(imm);

            if((proc_sign_extend_imm(imm) > 0) & (proc_reg(ra) & 0x80000000))
                proc_reg(rc) |= proc_high_ones_mask(proc_reg(rb));

            if(rc == 12)
                increment_pc = false;
            break;

        /*
         * BALI instruction (branch and link immediate).
         *
         * LR = PC + 4; PC += sign_extend(IMM)
         */
        case PROC_OPCODE_BALI:
            proc_regs.LR = proc_regs.PC + 4;
            proc_regs.PC += proc_sign_extend_imm(imm);
            increment_pc = false;
            break;

        default:
            if(global_verbosity)
                printf("Unknown instruction @PC=0x%08x: {opc: 0x%02x, ra: 0x%x\
, rb: 0x%x, rc: 0x%x, imm: 0x%04x}\n", proc_regs.PC, opcode, proc_reg(ra),
                       proc_reg(rb), proc_reg(rc), imm);
            proc_regs.SR |= SR_FAULT_DECODE_FLAG;
    }

    if(increment_pc)
        proc_regs.PC += 4;

    proc_clear_alu_flags();

    proc_regs.SR |= new_sr;

    return true;
}
