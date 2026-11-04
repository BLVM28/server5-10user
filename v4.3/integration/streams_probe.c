/* Host ABI and transport conformance test. */
#include <stdio.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
#include "kwt_v43_streams.h"
static int16_t x[99*64],w[64*256],decoded[99*256],gold[99*256];
static uint32_t xx[4096],ww[16384],yy[16384],out[16384];
int main(void) {
    unsigned layer,order,n=0;
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY);
#endif
    while(fread(&layer,4,1,stdin)==1) {
        if(layer>=12 || fread(&order,4,1,stdin)!=1 || order>1 ||
           fread(x,sizeof x,1,stdin)!=1 || fread(w,sizeof w,1,stdin)!=1 ||
           fread(xx,sizeof xx,1,stdin)!=1 || fread(ww,sizeof ww,1,stdin)!=1 ||
           fread(yy,sizeof yy,1,stdin)!=1 || fread(gold,sizeof gold,1,stdin)!=1)return 1;
        const kwt_rice_profile *p=&kwt_v42_profiles[layer];
        if(kwt_encode_streams_x(x,99*64,out,4096,p->sx,order) || memcmp(xx,out,sizeof xx))return 2;
        if(kwt_encode_streams_w(w,64*256,out,16384,p,order) || memcmp(ww,out,sizeof ww))return 3;
        if(kwt_decode_streams_y(yy,16384,decoded,99*256,p->sy,order) || memcmp(decoded,gold,sizeof gold))return 4;
        ++n;
    }
    kwt_descriptor d;
    if(!n || ferror(stdin) || kwt_make_streams_descriptor(&d,0,0,0,0,0,&kwt_v42_profiles[0]) ||
       d.format!=0x10004 || d.reserved!=(unsigned)(kwt_v42_profiles[0].sx|kwt_v42_profiles[0].sw<<4|kwt_v42_profiles[0].sy<<8))return 5;
    if(kwt_encode_streams_x(x,99*64,out,4095,0,1)==0 ||
       kwt_decode_streams_y(yy,16383,decoded,99*256,1,1)==0 ||
       kwt_make_streams_descriptor(&d,12,0,0,0,0,&kwt_v42_profiles[0])==0)return 6;
    printf("C STREAMS PASS %u frames\n",n);return 0;
}
