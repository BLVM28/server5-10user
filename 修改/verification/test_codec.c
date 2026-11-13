#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "kwt_v43_streams.h"
static uint32_t src[16384],gold[16384],out[16384];
static int16_t x[99*64],w[64*256],y[99*256];
static void readhex(const char *base,const char *sub,unsigned l,const char *suffix,uint32_t *dst,size_t n) {
    char path[4096]; snprintf(path,sizeof(path),"%s/%s/layer%02u_%s.hex",base,sub,l,suffix);
    FILE *f=fopen(path,"r");if(!f){perror(path);exit(1);}
    for(size_t i=0;i<n;++i)if(fscanf(f,"%x",&dst[i])!=1){fprintf(stderr,"short file %s\n",path);exit(1);}
    fclose(f);
}
static int16_t signed16(uint32_t v) { return (int16_t)((int32_t)((v&65535u)^32768u)-32768); }
static void require(int ok,const char *why){if(!ok){fprintf(stderr,"CODEC_FAIL %s\n",why);exit(1);}}
int main(int argc,char **argv) {
    require(argc==2,"vector root");
    for(unsigned l=0;l<12;++l) {
        const kwt_rice_profile *p=&kwt_v42_profiles[l];
        kwt_descriptor d;
        require(kwt_make_streams_descriptor(&d,l,0x10001000,0x10005000,0x10016000,0x10018000,p)==0,"descriptor");
        require(d.format==0x10005,"new format");
        readhex(argv[1],"raw",l,"x",src,3168);
        for(unsigned i=0;i<6336;++i)x[i]=signed16(src[i/2]>>(16*(i%2)));
        readhex(argv[1],"raw",l,"w",src,8192);
        for(unsigned i=0;i<16384;++i)w[i]=signed16(src[i/2]>>(16*(i%2)));
        for(int pack=0;pack<2;++pack) {
            require(kwt_encode_streams_x(x,6336,out,16384,p->sx,pack)==0,"encode X");
            readhex(argv[1],"worst",l,"x",gold,4096);
            for(unsigned i=0;i<4096;++i)require(out[i]==kwt_v4_word(gold[i],pack),"X mismatch");
            require(kwt_encode_streams_w(w,16384,out,16384,p,pack)==0,"encode W");
            readhex(argv[1],"worst",l,"w",gold,16384);
            for(unsigned i=0;i<16384;++i)require(out[i]==kwt_v4_word(gold[i],pack),"W mismatch");
            readhex(argv[1],"worst",l,"wire",src,12672);
            for(unsigned i=0;i<12672;++i)src[i]=kwt_v4_word(src[i],pack);
            require(kwt_decode_streams_y(src,12672,y,25344,p->sy,pack)==0,"read raw Y");
            readhex(argv[1],"worst",l,"decoded",gold,12672);
            for(unsigned i=0;i<25344;++i)require(y[i]==signed16(gold[i/2]>>(16*(i%2))),"Y mismatch");
        }
    }
    require(kwt_decode_streams_y(src,12671,y,25344,0,1)!=0,"short Y");
    puts("C_CODEC_PASS layers=12 pack_modes=2 raw_y_values=608256");return 0;
}
