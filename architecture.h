#ifndef ARCH_H
#define ARCH_H

#include <stdint.h>

#define ARCH_WORD_WIDTH_BITS        (32)
#define ARCH_UNALIGNED_ACCESS       (0)
#define ARCH_ACCESS_BOUNDARY        (1)

#define ARCH_RAM_SIZE               (32768ul)
#define ARCH_ROM_SIZE               (256 * 1024ul)

#define ARCH_RAM_OFFSET             (0x2000000)
#define ARCH_ROM_OFFSET             (0x1000000)

#define ARCH_INSTR_OPC_MASK         (0xFF000000)
#define ARCH_INSTR_IMM_MASK         (0x0000FFFF)
#define ARCH_INSTR_RA_MASK          (0x00F00000)
#define ARCH_INSTR_RB_MASK          (0x000F0000)
#define ARCH_INSTR_RC_MASK          (0x0000F000)

#define ARCH_INSTR_OPC_OFFSET       (24)
#define ARCH_INSTR_IMM_OFFSET       (0)
#define ARCH_INSTR_RA_OFFSET        (20)
#define ARCH_INSTR_RB_OFFSET        (16)
#define ARCH_INSTR_RC_OFFSET        (12)

typedef uint32_t word_t;
typedef uint8_t byte_t;
typedef uint16_t hword_t;

typedef uint8_t opcode_t;
typedef uint8_t regidx_t;

typedef struct
{
    uint32_t R0;
    uint32_t R1;
    uint32_t R2;
    uint32_t R3;
    uint32_t R4;
    uint32_t R5;
    uint32_t R6;
    uint32_t R7;
    uint32_t R8;
    uint32_t R9;
    uint32_t R10;
    uint32_t R11;
    uint32_t PC;
    uint32_t LR;
    uint32_t SP;
    uint32_t SR;
} register_map_t;

#define SR_FAULT_DECODE_FLAG        (0x40000000)
#define SR_FAULT_FLAG               (0x80000000)
#define SR_ALU_Z_FLAG               (0x00000001)
#define SR_ALU_O_FLAG               (0x00000002)
#define SR_ALU_N_FLAG               (0x00000004)

#define SR_ALU_FLAG_MASK            (0x00000007)

#endif
