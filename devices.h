#ifndef DEVICES_H
#define DEVICES_H

#include "architecture.h"

#include <stdbool.h>

typedef struct
{
    byte_t* (*get_byte)(word_t);
    hword_t* (*get_hword)(word_t);
    word_t* (*get_word)(word_t);

    bool (*get_addr_in_device_map)(word_t);
    void (*update)();
} device_mapping_t;


void device_register(device_mapping_t* device_mapping);

byte_t* device_get_byte(word_t);
hword_t* device_get_hword(word_t);
word_t* device_get_word(word_t);
void device_update();

#endif // DEVICES_H
