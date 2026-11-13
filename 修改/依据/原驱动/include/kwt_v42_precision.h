/* SPDX-License-Identifier: MIT */
#ifndef KWT_V42_PRECISION_H
#define KWT_V42_PRECISION_H
#include "kwt_v41_block8.h"

enum { KWT_FORMAT_PRECISION42=0x10003, KWT_RICE_X_WORDS=4096, KWT_RICE_SLOT=512,
       KWT_RICE_W_WORDS=32*512, KWT_RICE_Y_WORDS=32*512 };
typedef struct { uint8_t sx,sw,sy,y_key[256]; } kwt_rice_profile;

static inline int kwt_make_precision_descriptor(kwt_descriptor *dst,unsigned layer,uint32_t x,
       uint32_t w,uint32_t b,uint32_t y,const kwt_rice_profile *p) {
    if(!dst || !p || layer>=12 || p->sx>5 || p->sw>5 || p->sy>5)return -1;
    *dst=kwt_make_descriptor(layer,x,w,b,y);
    dst->format=KWT_FORMAT_PRECISION42;
    dst->reserved=p->sx|((uint32_t)p->sw<<4)|((uint32_t)p->sy<<8);
    return 0;
}

static inline int kwt_rice_quant(int v,unsigned s) {
    int unit=1<<(int)s,t=v+unit/2;
    int q=t>=0?t/unit:-((-t+unit-1)/unit);
    return q>32767/unit?32767/unit:q;
}
static inline unsigned kwt_rice_zig(int d) {
    return (unsigned)(d<0?-2*d-1:2*d);
}
/* Select the minimum total bit count. Ties go to the smaller k. */
static inline unsigned kwt_rice_key(const int16_t *v,unsigned count,unsigned stride,
                                    unsigned shift,int predict) {
    unsigned cost[16]={0},best=0;int prev=0;
    for(unsigned r=0;r<count;++r) {
        int q=kwt_rice_quant(v[r*stride],shift);
        unsigned z=kwt_rice_zig(q-prev);
        if(predict)prev=q;
        for(unsigned k=0;k<16;++k) {
            unsigned quotient=z>>k;
            cost[k]+=quotient<4?1+k+quotient:20-shift;
        }
    }
    for(unsigned k=1;k<16;++k)if(cost[k]<cost[best])best=k;
    return best;
}

typedef struct { uint32_t *out; uint64_t buf; unsigned used,words; int low_first; } kwt_rice_sink;
static inline void kwt_rice_emit(kwt_rice_sink *s,int value,int diff,unsigned k,unsigned shift) {
    unsigned z=kwt_rice_zig(diff),q=z>>k,n,t;
    if(q>=4) {
        n=20-shift;t=15u|(((uint32_t)value&((1u<<(16-shift))-1))<<4);
    } else {
        n=q+1+k;t=((1u<<q)-1)|((z&((1u<<k)-1))<<(q+1));
    }
    s->buf|=(uint64_t)t<<s->used;s->used+=n;
    if(s->used>=32) {
        s->out[s->words++]=kwt_v4_word((uint32_t)s->buf,s->low_first);
        s->buf>>=32;s->used-=32;
    }
}
static inline unsigned kwt_rice_flush(kwt_rice_sink *s) {
    if(s->used)s->out[s->words++]=kwt_v4_word((uint32_t)s->buf,s->low_first);
    return s->words;
}

static inline int kwt_encode_precision_x(const int16_t *x,size_t count,uint32_t *out,
                             size_t words,unsigned sx,int low_first) {
    if(!x || !out || count<KWT_M*KWT_K || words<KWT_RICE_X_WORDS || sx>5)return -1;
    unsigned keys[64];for(unsigned i=0;i<KWT_RICE_X_WORDS;++i)out[i]=0;
    for(unsigned g=0;g<8;++g) {
        uint32_t hdr=0;
        for(unsigned l=0;l<8;++l) {
            unsigned c=8*g+l;keys[c]=kwt_rice_key(x+c,99,64,sx,1);
            hdr|=(uint32_t)keys[c]<<(4*l);
        }
        out[1+g]=kwt_v4_word(hdr,low_first);
    }
    kwt_rice_sink s={out+9,0,0,0,low_first};
    for(unsigned pair=0;pair<32;++pair) {
        int prev[2]={0,0};
        for(unsigned row=0;row<99;++row)for(unsigned l=0;l<2;++l) {
            unsigned c=2*pair+l;int q=kwt_rice_quant(x[row*64+c],sx);
            kwt_rice_emit(&s,q,q-prev[l],keys[c],sx);prev[l]=q;
        }
    }
    out[0]=kwt_v4_word(kwt_rice_flush(&s),low_first);return 0;
}

static inline int kwt_encode_precision_w(const int16_t *w,size_t count,uint32_t *out,
                              size_t words,const kwt_rice_profile *p,int low_first) {
    if(!w || !out || !p || count<KWT_K*KWT_N || words<KWT_RICE_W_WORDS || p->sw>5)return -1;
    for(unsigned c=0;c<256;++c)if(p->y_key[c]>15)return -1;
    for(unsigned i=0;i<KWT_RICE_W_WORDS;++i)out[i]=0;
    for(unsigned g=0;g<32;++g) {
        unsigned keys[8];uint32_t wk=0,yk=0,*slot=out+g*KWT_RICE_SLOT;
        for(unsigned l=0;l<8;++l) {
            unsigned c=8*g+l;keys[l]=kwt_rice_key(w+c,64,256,p->sw,0);
            wk|=(uint32_t)keys[l]<<(4*l);yk|=(uint32_t)p->y_key[c]<<(4*l);
        }
        slot[1]=kwt_v4_word(wk,low_first);slot[2]=kwt_v4_word(yk,low_first);
        kwt_rice_sink s={slot+3,0,0,0,low_first};
        for(unsigned r=0;r<64;++r)for(unsigned l=0;l<8;++l) {
            int q=kwt_rice_quant(w[r*256+g*8+l],p->sw);
            kwt_rice_emit(&s,q,q,keys[l],p->sw);
        }
        slot[0]=kwt_v4_word(kwt_rice_flush(&s),low_first);
    }
    return 0;
}

static inline int kwt_decode_precision_y(const uint32_t *src,size_t words,int16_t *dst,
                                          size_t count,unsigned sy,int low_first) {
    if(!src || !dst || words<KWT_RICE_Y_WORDS || count<KWT_M*KWT_N || sy>5)return -1;
    for(unsigned g=0;g<32;++g) {
        const uint32_t *slot=src+g*KWT_RICE_SLOT;
        uint32_t keys=kwt_v4_word(slot[0],low_first);unsigned bit=0;int prev[8]={0};
        for(unsigned r=0;r<99;++r)for(unsigned l=0;l<8;++l) {
            unsigned index=1+bit/32,offset=bit%32,k=(keys>>(4*l))&15u;
            if(index>=KWT_RICE_SLOT)return -1;
            uint64_t window=kwt_v4_word(slot[index],low_first);
            if(index+1<KWT_RICE_SLOT)window|=(uint64_t)kwt_v4_word(slot[index+1],low_first)<<32;
            window>>=offset;
            unsigned q=0,n;int v;
            while(q<4 && ((window>>q)&1u))++q;
            if(q==4) {
                unsigned width=16-sy;
                int raw=(int)((window>>4)&((1u<<width)-1));
                v=raw&(1<<(width-1))?raw-(1<<width):raw;n=width+4;
            } else {
                unsigned z=(q<<k)|((unsigned)(window>>(q+1))&((1u<<k)-1));
                int diff=(z&1)?-1-(int)(z>>1):(int)(z>>1);
                v=prev[l]+diff;n=q+1+k;
            }
            bit+=n;if(bit>(KWT_RICE_SLOT-1)*32 || v< -32768/(1<<(int)sy) || v>32767/(1<<(int)sy))return -1;
            prev[l]=v;dst[r*256+8*g+l]=(int16_t)(v*(1<<(int)sy));
        }
        if(bit%32 && (kwt_v4_word(slot[1+bit/32],low_first)>>(bit%32)))return -1;
    }
    return 0;
}
#endif
