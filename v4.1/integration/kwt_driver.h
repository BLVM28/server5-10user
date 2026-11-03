/* SPDX-License-Identifier: MIT
 * Proposed ABI, not an official contest assignment. RV32, uncached shared RAM.
 * Platform trap handling is required: nice_rsp_err may trap, rather than return.
 */
#ifndef KWT_DRIVER_H
#define KWT_DRIVER_H
#include <stdint.h>
#include <stddef.h>

enum { KWT_M=99, KWT_K=64, KWT_N=256, KWT_LAYERS=12 };
enum { KWT_X_BYTES=12672, KWT_W_BYTES=32768, KWT_B_BYTES=1024, KWT_Y_BYTES=50688 };
enum { KWT_OK=0, KWT_BAD_RANGE=1, KWT_READ_ERROR=2, KWT_WRITE_ERROR=3,
       KWT_BAD_LAYER=4, KWT_BAD_INSTRUCTION=0x10, KWT_BAD_DESCRIPTOR_ADDRESS=0x11,
       KWT_BAD_FORMAT=0x12, KWT_DESCRIPTOR_READ_ERROR=0x13 };
typedef struct {
    uint32_t magic,format,layer,x,w,b,y,reserved;
} kwt_descriptor;
_Static_assert(sizeof(kwt_descriptor)==32,"descriptor must be 8 RV32 words");
_Static_assert(offsetof(kwt_descriptor,y)==24,"descriptor ABI mismatch");

/* All addresses are byte addresses in the approved shared memory region.
 * Allocate descriptor/X/W/b/Y with at least 4-byte alignment and no overlap.
 * layer tags the task; the caller must select the corresponding W and b.
 */
static inline kwt_descriptor kwt_make_descriptor(uint32_t layer,uint32_t x,
                                                uint32_t w,uint32_t b,uint32_t y) {
    kwt_descriptor d={0x3154574bu,0x00010000u,layer,x,w,b,y,0};return d;
}
static inline uint32_t kwt_pack16(int16_t first,int16_t second,int low_first) {
    uint32_t a=(uint16_t)first,b=(uint16_t)second;
    return low_first ? a|(b<<16) : (a<<16)|b;
}
#if defined(__riscv) && __riscv_xlen==32
static inline uint32_t kwt_run(const volatile kwt_descriptor *descriptor) {
    uint32_t status;
    __asm__ volatile ("fence rw,rw\n\t"
                      ".insn r 0x7b,6,0x40,%0,%1,x0\n\t"
                      "fence rw,rw"
                      : "=r"(status) : "r"(descriptor) : "memory");
    return status;
}
#endif
#endif
