/**
 * @brief The main routine of the DankBoxEmulator. Reads in a binary file and
 *        starts executing.
 * @author Kevin Balke
 */

#include "global_config.h"
#include "device_uart.h"
#include "devices.h"
#include "processor.h"

#include <stdio.h>

uint32_t global_verbosity;

int main(int argc, char** argv)
{
    /*
     * If the user does not provide a binary to run, print the usage and exit.
     */
    if(argc < 2)
    {
        printf("USAGE:\n\t%s:\t[-v]\t[BINFILE]\n", argv[0]);
        return 1;
    }

    /*
     * Initialize the global flags.
     */
    global_verbosity = 0;

    /*
     * We don't care about the program invocation name at this point.
     */
    argc--;
    argv++;

    while(argc > 1)
    {
        if(strcmp(argv[0], "-v") == 0)
        {
            global_verbosity = 1;
        }

        argc--;
        argv++;
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
     * Load the program binary from the provided binary file. The filename
     * should be the last argument after parsing the flags.
     */
    proc_load_program(argv[0]);

    /*
     * Execute the program in a loop.
     */
    while(proc_instr_execute(get_mem_word(proc_regs.PC)))
    {
        device_update();
    }

    return 0;
}
