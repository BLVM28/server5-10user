#include "kwt_v43_streams.h"
uint32_t kwt_streams_call(volatile kwt_descriptor *slot,unsigned layer,
        uint32_t x,uint32_t w,uint32_t b,uint32_t y) {
    kwt_descriptor d;
    if(layer>=12||kwt_make_streams_descriptor(&d,layer,x,w,b,y,&kwt_v42_profiles[layer]))return KWT_BAD_LAYER;
    *slot=d;return kwt_run(slot);
}
int kwt_streams_consume(const uint32_t *src,int16_t *dst,unsigned layer) {
    if(layer>=12)return -1;
    return kwt_decode_streams_y(src,KWT43_Y_WORDS,dst,99*256,kwt_v42_profiles[layer].sy,1);
}
