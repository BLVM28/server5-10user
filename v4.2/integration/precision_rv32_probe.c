#include "kwt_v42_profile.h"
/* Example using already prepared X/W and an uncached, approved sharing window. */
uint32_t kwt_precision_call(volatile kwt_descriptor *slot,unsigned layer,
                            uint32_t x,uint32_t w,uint32_t bias,uint32_t y) {
    kwt_descriptor d;
    if(layer>=12 || kwt_make_precision_descriptor(&d,layer,x,w,bias,y,&kwt_v42_profiles[layer]))return KWT_BAD_LAYER;
    *slot=d;
    return kwt_run(slot);
}
int kwt_precision_consume(const uint32_t *wire,int16_t *dst,unsigned layer) {
    if(layer>=12)return -1;
    return kwt_decode_precision_y(wire,KWT_RICE_Y_WORDS,dst,99*256,kwt_v42_profiles[layer].sy,1);
}
