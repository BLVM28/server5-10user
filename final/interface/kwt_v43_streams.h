/* SPDX-License-Identifier: MIT
 * Four-stream transport; numerical precision is frozen at v4.2. */
#ifndef KWT_V43_STREAMS_H
#define KWT_V43_STREAMS_H
#include "kwt_v42_profile.h"
enum { KWT_FORMAT_STREAMS43=0x10004, KWT43_X_WORDS=4096,
       KWT43_W_WORDS=16384,KWT43_Y_WORDS=16384,KWT43_SLOT=256 };
static inline int kwt_make_streams_descriptor(kwt_descriptor *d,unsigned layer,
        uint32_t x,uint32_t w,uint32_t b,uint32_t y,const kwt_rice_profile *p) {
    if(!d||!p||layer>=12||p->sx<1||p->sx>5||p->sw<3||p->sw>5||p->sy>5)return -1;
    *d=kwt_make_descriptor(layer,x,w,b,y);d->format=KWT_FORMAT_STREAMS43;
    d->reserved=p->sx|((uint32_t)p->sw<<4)|((uint32_t)p->sy<<8);return 0;
}
static inline int kwt_encode_streams_x(const int16_t *x,size_t count,uint32_t *out,
                                      size_t words,unsigned sx,int low_first) {
    if(!x||!out||count<99*64||words<KWT43_X_WORDS||sx<1||sx>5)return -1;
    for(unsigned i=0;i<KWT43_X_WORDS;++i)out[i]=0;
    for(unsigned s=0;s<4;++s) {
        unsigned key[64];int16_t column[25];uint32_t *slot=out+s*1024;
        for(unsigned c=0;c<64;++c) {
            for(unsigned r=0;r<25;++r)column[r]=(4*r+s<99)?x[(4*r+s)*64+c]:0;
            key[c]=kwt_rice_key(column,25,1,sx,1);
            slot[1+c/8]|=(uint32_t)key[c]<<(4*(c%8));
        }
        for(unsigned i=1;i<=8;++i)slot[i]=kwt_v4_word(slot[i],low_first);
        kwt_rice_sink sink={slot+9,0,0,0,low_first};
        for(unsigned c=0;c<64;++c) {
            int prev=0;
            for(unsigned r=0;r<25;++r) {
                int v=(4*r+s<99)?x[(4*r+s)*64+c]:0,q=kwt_rice_quant(v,sx);
                kwt_rice_emit(&sink,q,q-prev,key[c],sx);prev=q;
            }
        }
        unsigned n=kwt_rice_flush(&sink);if(n>1015)return -1;
        slot[0]=kwt_v4_word(n,low_first);
    }
    return 0;
}
static inline int kwt_encode_streams_w(const int16_t *w,size_t count,uint32_t *out,
        size_t words,const kwt_rice_profile *p,int low_first) {
    if(!w||!out||!p||count<64*256||words<KWT43_W_WORDS||p->sw<3||p->sw>5)return -1;
    for(unsigned i=0;i<256;++i)if(p->y_key[i]>15)return -1;
    for(unsigned i=0;i<KWT43_W_WORDS;++i)out[i]=0;
    for(unsigned g=0;g<16;++g)for(unsigned s=0;s<4;++s) {
        uint32_t *slot=out+(4*g+s)*256,meta=0;unsigned key[4];
        for(unsigned j=0;j<4;++j) {
            unsigned c=16*g+s+4*j;key[j]=kwt_rice_key(w+c,64,256,p->sw,0);
            meta|=key[j]<<(4*j);meta|=(uint32_t)p->y_key[c]<<(16+4*j);
        }
        slot[1]=kwt_v4_word(meta,low_first);kwt_rice_sink sink={slot+2,0,0,0,low_first};
        for(unsigned k=0;k<64;++k)for(unsigned j=0;j<4;++j) {
            int q=kwt_rice_quant(w[k*256+16*g+s+4*j],p->sw);
            kwt_rice_emit(&sink,q,q,key[j],p->sw);
        }
        unsigned n=kwt_rice_flush(&sink);if(n>254)return -1;slot[0]=kwt_v4_word(n,low_first);
    }
    return 0;
}
static inline int kwt_decode_streams_y(const uint32_t *src,size_t words,int16_t *dst,
        size_t count,unsigned sy,int low_first) {
    if(!src||!dst||words<KWT43_Y_WORDS||count<99*256||sy>5)return -1;
    for(unsigned g=0;g<16;++g)for(unsigned s=0;s<4;++s) {
        const uint32_t *slot=src+(4*g+s)*256;uint32_t keys=kwt_v4_word(slot[0],low_first);
        if(keys>>16)return -1;
        unsigned bit=0;int prev[4]={0};
        for(unsigned r=0;r<99;++r)for(unsigned j=0;j<4;++j) {
            unsigned index=1+bit/32,offset=bit%32,k=(keys>>(4*j))&15;
            if(index>=256)return -1;
            uint64_t window=kwt_v4_word(slot[index],low_first);
            if(index+1<256)window|=(uint64_t)kwt_v4_word(slot[index+1],low_first)<<32;
            window>>=offset;unsigned q=0,n;int v;
            while(q<4&&((window>>q)&1u))++q;
            if(q==4) {
                unsigned width=16-sy;int raw=(int)((window>>4)&((1u<<width)-1));
                v=raw&(1<<(width-1))?raw-(1<<width):raw;n=width+4;
            } else {
                unsigned z=(q<<k)|((unsigned)(window>>(q+1))&((1u<<k)-1));
                v=prev[j]+((z&1)?-1-(int)(z>>1):(int)(z>>1));n=q+1+k;
            }
            bit+=n;if(bit>255*32||v< -32768/(1<<(int)sy)||v>32767/(1<<(int)sy))return -1;
            prev[j]=v;dst[r*256+16*g+s+4*j]=(int16_t)(v*(1<<(int)sy));
        }
        if(bit%32&&(kwt_v4_word(slot[1+bit/32],low_first)>>(bit%32)))return -1;
    }
    return 0;
}
#endif
