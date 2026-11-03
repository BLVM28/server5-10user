#include <stdio.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
#include "kwt_v41_block8.h"
static int16_t x[99*64],w[64*256],actual[99*256],expected[99*256];
static uint32_t xwire[1683],wwire[4128],ywire[6752],out[4128];
int main(void){
    unsigned order,frames=0;
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY);
#endif
    while(fread(&order,4,1,stdin)==1){
        if(fread(x,sizeof x,1,stdin)!=1||fread(w,sizeof w,1,stdin)!=1||
           fread(xwire,sizeof xwire,1,stdin)!=1||fread(wwire,sizeof wwire,1,stdin)!=1||
           fread(ywire,sizeof ywire,1,stdin)!=1||fread(expected,sizeof expected,1,stdin)!=1)return 1;
        if(kwt_encode_block8_x(x,99*64,out,1683,order)||memcmp(out,xwire,sizeof xwire))return 2;
        if(kwt_encode_block8_w(w,64*256,out,4128,order)||memcmp(out,wwire,sizeof wwire))return 3;
        if(kwt_decode_block8(ywire,6752,actual,99*256,order)||memcmp(actual,expected,sizeof expected))return 4;
        ++frames;
    }
    if(ferror(stdin)||!frames)return 5;
    if(kwt_decode_block8(ywire,6751,actual,99*256,1)==0)return 6;
    ywire[6336]=15;
    if(kwt_decode_block8(ywire,6752,actual,99*256,1)==0)return 7;
    printf("C BLOCK8 PASS %u frames\n",frames);
    return 0;
}
