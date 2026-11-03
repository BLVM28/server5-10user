/* Compile/disassemble on RV32; the actual platform supplies and owns memory. */
#include "kwt_v4_output.h"
uint32_t probe(const volatile kwt_descriptor *descriptor) {
    return kwt_run(descriptor);
}
int probe_packed(uint32_t layer,uint32_t x,uint32_t w,uint32_t b,uint32_t y,int16_t *dense) {
    kwt_descriptor descriptor=kwt_make_packed_descriptor(layer,x,w,b,y);
    uint32_t status=kwt_run(&descriptor);
    if(status!=KWT_OK)return (int)status;
    return kwt_decode_packed((const uint32_t *)(uintptr_t)y,KWT_PACKED_WORDS,dense,99*256,1);
}
