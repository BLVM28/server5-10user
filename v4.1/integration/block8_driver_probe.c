#include "kwt_v41_block8.h"
int probe_block8(uint32_t layer,uint32_t x,uint32_t w,uint32_t b,uint32_t y,int16_t *out){
    kwt_descriptor d=kwt_make_block8_descriptor(layer,x,w,b,y);
    uint32_t status=kwt_run(&d);
    return status ? (int)status : kwt_decode_block8((const uint32_t *)(uintptr_t)y,KWT_B8_Y_WORDS,out,KWT_M*KWT_N,1);
}
