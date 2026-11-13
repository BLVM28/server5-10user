/* SPDX-License-Identifier: MIT */
#ifndef KWT_V41_BLOCK8_H
#define KWT_V41_BLOCK8_H
#include "kwt_v4_output.h"

enum { KWT_FORMAT_BLOCK8=0x00010002, KWT_B8_X_WORDS=1683, KWT_B8_W_WORDS=4128,
       KWT_B8_Y_WORDS=6752, KWT_B8_Y_PAYLOAD=6336 };
static inline kwt_descriptor kwt_make_block8_descriptor(uint32_t layer,uint32_t x,uint32_t w,
                                                        uint32_t b,uint32_t y) {
    kwt_descriptor d=kwt_make_descriptor(layer,x,w,b,y);
    d.format=KWT_FORMAT_BLOCK8;
    return d;
}
static inline unsigned kwt_block8_shift(const int16_t *v,unsigned count,unsigned stride) {
    unsigned magnitude=0,shift=0;
    for(unsigned i=0;i<count;++i) {
        int value=v[i*stride];
        unsigned bits=(unsigned)(value<0 ? -1-value : value);
        magnitude |= bits;
    }
    while(magnitude>127) {magnitude>>=1; ++shift;}
    return shift;
}
static inline uint32_t kwt_block8_byte(int16_t value,unsigned shift) {
    int unit=1<<(int)shift;
    int round=(int)value+unit/2;
    int m=round>=0 ? round/unit : -((-round+unit-1)/unit);
    if(m>127)m=127;
    return (uint32_t)m&255u;
}
static inline int kwt_encode_block8_x(const int16_t *x,size_t count,uint32_t *out,size_t words,int low_first) {
    if(!x||!out||count<KWT_M*KWT_K||words<KWT_B8_X_WORDS)return -1;
    for(unsigned row=0;row<KWT_M;++row) {
        const int16_t *v=x+row*KWT_K;
        unsigned e=kwt_block8_shift(v,KWT_K,1);
        out[17*row]=kwt_v4_word(e,low_first);
        for(unsigned j=0;j<16;++j) {
            uint32_t p=0;
            for(unsigned k=0;k<4;++k)p|=kwt_block8_byte(v[4*j+k],e)<<(8*k);
            out[17*row+1+j]=kwt_v4_word(p,low_first);
        }
    }
    return 0;
}
static inline int kwt_encode_block8_w(const int16_t *w,size_t count,uint32_t *out,size_t words,int low_first) {
    if(!w||!out||count<KWT_K*KWT_N||words<KWT_B8_W_WORDS)return -1;
    for(unsigned g=0;g<32;++g) {
        unsigned e[8];uint32_t header=0;
        for(unsigned l=0;l<8;++l) {
            e[l]=kwt_block8_shift(w+8*g+l,KWT_K,KWT_N);
            header|=(uint32_t)e[l]<<(4*l);
        }
        out[129*g]=kwt_v4_word(header,low_first);
        for(unsigned k=0;k<KWT_K;++k)for(unsigned half=0;half<2;++half) {
            uint32_t p=0;
            for(unsigned j=0;j<4;++j){
                unsigned l=4*half+j;
                p|=kwt_block8_byte(w[k*KWT_N+8*g+l],e[l])<<(8*j);
            }
            out[129*g+1+2*k+half]=kwt_v4_word(p,low_first);
        }
    }
    return 0;
}
static inline int kwt_decode_block8(const uint32_t *src,size_t words,int16_t *dst,size_t count,int low_first) {
    if(!src||!dst||words<KWT_B8_Y_WORDS||count<KWT_M*KWT_N)return -1;
    for(unsigned g=0;g<32;++g)for(unsigned r=0;r<KWT_M;++r) {
        uint32_t tag=kwt_v4_word(src[KWT_B8_Y_PAYLOAD+13*g+r/8],low_first);
        unsigned e=(tag>>(4*(r%8)))&15u;
        if(e>8 || (r==98 && (tag>>12)))return -1;
        for(unsigned half=0;half<2;++half) {
            uint32_t word=kwt_v4_word(src[64*r+2*g+half],low_first);
            for(unsigned j=0;j<4;++j) {
                int m=(int)((word>>(8*j))&255u);
                if(m>=128)m-=256;
                dst[r*KWT_N+8*g+4*half+j]=(int16_t)(m*(1<<(int)e));
            }
        }
    }
    return 0;
}
#endif
