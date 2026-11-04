/* SPDX-License-Identifier: MIT
 * Exact v4 Dense1 output transport. Source and destination must not overlap.
 * Read only after a successful NICE completion. Return zero on success.
 */
#ifndef KWT_V4_OUTPUT_H
#define KWT_V4_OUTPUT_H
#include "kwt_driver.h"

enum { KWT_FORMAT_RAW = 0x00010000, KWT_FORMAT_DELTA = 0x00010001,
       KWT_TAG_WORDS = 224, KWT_PACKED_WORDS = 12896, KWT_PACKED_BYTES = 51584 };

static inline kwt_descriptor kwt_make_packed_descriptor(uint32_t layer, uint32_t x,
                            uint32_t w, uint32_t b, uint32_t y) {
    kwt_descriptor d = kwt_make_descriptor(layer,x,w,b,y);
    d.format = KWT_FORMAT_DELTA;
    return d;
}
static inline uint32_t kwt_v4_word(uint32_t word, int low_first) {
    return low_first ? word : (word >> 16) | (word << 16);
}
static inline int kwt_decode_packed(const uint32_t *src, size_t src_words,
                                    int16_t *dst, size_t dst_count, int low_first) {
    if (!src || !dst || src_words < KWT_PACKED_WORDS || dst_count < KWT_M*KWT_N) return -1;
    for (unsigned g=0; g<32; ++g) {
        int32_t previous[8]={0};
        for (unsigned row=0; row<KWT_M; ++row) {
            uint32_t tags=kwt_v4_word(src[12672+7*g+row/16],low_first);
            if (row==98 && (tags>>6)) return -1;
            unsigned mode=(tags>>(2*(row%16)))&3u;
            unsigned width=4*(mode+1), mask=(1u<<width)-1;
            size_t slot=row*128+g*4;
            for (unsigned lane=0; lane<8; ++lane) {
                unsigned bit=lane*width, word=bit/32, shift=bit%32;
                uint32_t field=kwt_v4_word(src[slot+word],low_first)>>shift;
                if (shift+width>32)
                    field|=kwt_v4_word(src[slot+word+1],low_first)<<(32-shift);
                field&=mask;
                int32_t value=(int32_t)field;
                if (field&(1u<<(width-1))) value-=(int32_t)(1u<<width);
                if (mode!=3) value+=previous[lane];
                if (value < -32768 || value > 32767) return -1;
                dst[row*KWT_N+8*g+lane]=(int16_t)value;
                previous[lane]=value;
            }
        }
    }
    return 0;
}
#endif
