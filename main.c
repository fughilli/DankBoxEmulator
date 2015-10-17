/**
 * @brief The main routine of the DankBoxEmulator. Reads in a binary file and
 *        starts executing.
 * @author Kevin Balke
 */

#include "device_uart.h"
#include "devices.h"
#include "processor.h"

#include <stdio.h>

int main(int argc, char** argv)
{
    /*
     * If the user does not provide a binary to run, print the usage and exit.
     */
    if(argc != 2)
    {
        printf("USAGE:\n\t%s:\t[BINFILE]\n", argv[0]);
        return 1;
    }

    /*
     * Initialize the processor.
     */
    proc_init();

    /*
     * Initialize the UART device.
     */
    uart_init();

    /*
     * Load the program binary from the provided binary file.
     */
    proc_load_program(argv[1]);

    /*
     * Execute the program in a loop.
     */
    while(proc_instr_execute(get_mem_word(proc_regs.PC)));

    return 0;
}
