#include "devices.h"

#include <stdlib.h>

typedef struct device_mapping_node_t
{
    device_mapping_t* device_mapping;
    struct device_mapping_node_t* next_node;
} device_mapping_node_t;

device_mapping_node_t* device_mappings = NULL;

/**
 * @brief Prepends a device mapping to the device mapping list.
 */
void device_register(device_mapping_t* device_mapping)
{
    device_mapping_node_t* new_node =
            (device_mapping_node_t*)malloc(sizeof(device_mapping_node_t));

    new_node->next_node = device_mappings;
    new_node->device_mapping = device_mapping;
    device_mappings = new_node;
}

/**
 * @brief Walks the list of devices, looking for one whose mapped addresses
 *        contain the provided address.
 */
bool device_get_mapping_for_addr(word_t addr,
                                 device_mapping_t** device_mapping_ptr)
{
    device_mapping_node_t* cur_node = device_mappings;

    while((cur_node != NULL) &&
          (!cur_node->device_mapping->get_addr_in_device_map(addr)))
        cur_node = cur_node->next_node;

    if(cur_node == NULL)
            return false;

    (*device_mapping_ptr) = cur_node->device_mapping;

    return true; 
}

/**
 * @brief Returns an address to a byte for a memory-mapped device.
 */
byte_t* device_get_byte(word_t addr)
{
    device_mapping_t* device_mapping;

    if(!device_get_mapping_for_addr(addr, &device_mapping))
        return 0;

    return device_mapping->get_byte(addr);
}

/**
 * @brief Returns an address to a halfword for a memory-mapped device.
 */
hword_t* device_get_hword(word_t addr)
{
    device_mapping_t* device_mapping;

    if(!device_get_mapping_for_addr(addr, &device_mapping))
        return 0;

    return device_mapping->get_hword(addr);
}

/**
 * @brief Returns an address to a word for a memory-mapped device.
 */
word_t* device_get_word(word_t addr)
{
    device_mapping_t* device_mapping;

    if(!device_get_mapping_for_addr(addr, &device_mapping))
        return 0;

    return device_mapping->get_word(addr);
}

/**
 * @brief Updates all registered devices.
 */
void device_update()
{
     device_mapping_node_t* cur_node = device_mappings;

    while(cur_node != NULL)
    {
        cur_node->device_mapping->update();
        cur_node = cur_node->next_node;
    }
}
