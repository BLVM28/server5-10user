/* A native-host test of the exact decoder exported to RV32 software. */
#include "kwt_v4_output.h"
#include <stdio.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
static uint32_t frame[KWT_PACKED_WORDS];
static int16_t decoded[KWT_M*KWT_N], golden[KWT_M*KWT_N];
int main(void) {
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY);
#endif
    unsigned frames=0;
    uint32_t packing;
    while (fread(&packing,sizeof(packing),1,stdin)==1) {
        if (fread(frame,sizeof(*frame),KWT_PACKED_WORDS,stdin)!=KWT_PACKED_WORDS ||
            fread(golden,sizeof(*golden),KWT_M*KWT_N,stdin)!=KWT_M*KWT_N ||
            kwt_decode_packed(frame,KWT_PACKED_WORDS,decoded,KWT_M*KWT_N,(int)packing)!=0) return 1;
        for (unsigned i=0; i<KWT_M*KWT_N; ++i) if(decoded[i]!=golden[i]) return 2;
        ++frames;
    }
    printf("C DECODE PASS %u frames\n",frames);
    return frames ? 0 : 3;
}
