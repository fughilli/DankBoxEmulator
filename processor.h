#ifndef PROCESSOR_H
#define PROCESSOR_H

#include "architecture.h"

/*
 * Opcode definitions.
 */
#define PROC_OPCODE_ADD (0x00)
#define PROC_OPCODE_ADDI (0x01)
#define PROC_OPCODE_ADDUI (0x02)
#define PROC_OPCODE_LUH (0x03)
#define PROC_OPCODE_MUL (0x04)
#define PROC_OPCODE_MULI (0x05)
#define PROC_OPCODE_PUSH (0x06)
#define PROC_OPCODE_PUSHI (0x07)
#define PROC_OPCODE_POP (0x08)
#define PROC_OPCODE_JUMP (0x09)
#define PROC_OPCODE_JUMPI (0x0A)
#define PROC_OPCODE_BR (0x0B)
#define PROC_OPCODE_BI (0x0C)
#define PROC_OPCODE_CALL (0x0D)

#define PROC_OPCODE_MOV (0x0E)
#define PROC_OPCODE_HALT (0x0F)
#define PROC_OPCODE_DUMP (0x10)

#define PROC_OPCODE_LOAD (0x11)
#define PROC_OPCODE_STOR (0x12)

#define PROC_OPCODE_RET (0x13)
#define PROC_OPCODE_

extern register_map_t proc_regs;
extern byte_t* real_memory;

#define get_addr_in_ram(__addr__) \
        ((__addr__) >= ARCH_RAM_OFFSET && \
         (__addr__) < (ARCH_RAM_OFFSET + ARCH_RAM_SIZE))

#define get_addr_in_rom(__addr__) \
        ((__addr__) >= ARCH_ROM_OFFSET && \
         (__addr__) < (ARCH_ROM_OFFSET + ARCH_ROM_SIZE))

#define get_addr_in_real_mem(__addr__) \
        (get_addr_in_ram(__addr__) && get_addr_in_rom(__addr__))

/**
 * @brief Computes the real address within real_memory for the given emulated
 *        address.
 */
#define get_real_addr(__addr__) \
        (get_addr_in_ram(__addr__) ? \
         ((__addr__) - ARCH_RAM_OFFSET + ARCH_ROM_SIZE) : \
         get_addr_in_rom(__addr__) ? \
         ((__addr__) - ARCH_ROM_OFFSET) : \
         0)

#define get_mem_word(__addr__) \
        (get_addr_in_real_mem(__addr__) ? \
        (*((word_t*)(real_memory + get_real_addr(__addr__)))) : \
        (get_device_word(__addr__))

#define get_mem_hword(__addr__) \
        (get_addr_in_real_mem(__addr__) ? \
        (*((hword_t*)(real_memory + get_real_addr(__addr__)))) : \
        (get_device_hword(__addr__))

#define get_mem_byte(__addr__) \
        (get_addr_in_real_mem(__addr__) ? \
        (*((byte_t*)(real_memory + get_real_addr(__addr__)))) : \
        (get_device_byte(__addr__))

#define proc_reg(__regidx__) \
        (*(((word_t*)(&proc_regs) + (__regidx__))))

#define proc_clear_alu_flags() \
        proc_regs.SR &= ~SR_ALU_FLAG_MASK

#define proc_sign_extend_imm(__imm__) \
        ((word_t)(((__imm__) & 0x00008000ul) ? \
                  (0xFFFF0000ul | (__imm__)) : (__imm__)))

#endif
