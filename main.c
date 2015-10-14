#include <stdio.h>
#include "processor.h"

int main(int argc, char** argv)
{
    if(argc != 2)
    {
        printf("USAGE:\n\t%s:\t[BINFILE]\n", argv[0]);
        return 1;
    }
    proc_init();

    proc_load_program(argv[1]);

    while(proc_instr_execute(get_mem_word(proc_regs.PC)))
    {
//        fgetc(stdin);
    }

    return 0;
}
