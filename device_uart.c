#include "device_uart.h"

#include "architecture.h"
#include "devices.h"
#include "global_config.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define UART_DEVICE_ADDR_OFFSET (0x50000000)
#define UART_DEVICE_MAP_SIZE (4 * 3)

typedef struct
{
    word_t txbuf;
    word_t rxbuf;
    word_t control;
} uart_regs_t;

uart_regs_t uart_regs;

byte_t* uart_get_byte(word_t addr)
{
    if(global_verbosity)
        printf("UART GET BYTE @0x%08x\n", addr);

    return ((byte_t*)(((byte_t*)&uart_regs) +
                      (addr - UART_DEVICE_ADDR_OFFSET)));
}

hword_t* uart_get_hword(word_t addr)
{
    if(global_verbosity)
        printf("UART GET HWORD @0x%08x\n", addr);

    return ((hword_t*)(((byte_t*)&uart_regs) +
                       (addr - UART_DEVICE_ADDR_OFFSET)));
}

word_t* uart_get_word(word_t addr)
{
    if(global_verbosity)
        printf("UART GET WORD @0x%08x\n", addr);

    return ((word_t*)(((byte_t*)&uart_regs) +
                      (addr - UART_DEVICE_ADDR_OFFSET)));
}

bool uart_get_addr_in_map(word_t addr)
{
    return (addr >= UART_DEVICE_ADDR_OFFSET) && 
           (addr < UART_DEVICE_ADDR_OFFSET + UART_DEVICE_MAP_SIZE);
}

void uart_update()
{
    if(global_verbosity)
        printf("UART UPDATE\n");
    /*
     * Write the rxbuf to stdout if the transmit flag is set.
     */
    if (uart_regs.control & 0x1)
    {
        if(global_verbosity)
            printf("UART WRITING CHARACTER: %c\n", (char)uart_regs.txbuf);
        else
            printf("%c", (char)uart_regs.txbuf);


        /*
         * Clear the flag.
         */
        uart_regs.control &= ~0x1;
    }
}

static device_mapping_t uart_device_mapping =
{
    .get_byte = uart_get_byte,
    .get_hword = uart_get_hword,
    .get_word = uart_get_word,
    .get_addr_in_device_map = uart_get_addr_in_map,
    .update = uart_update
};

void uart_init()
{
    device_register(&uart_device_mapping);
}

