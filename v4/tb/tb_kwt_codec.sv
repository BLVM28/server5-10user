 `timescale 1ns/1ps
module tb_kwt_codec;
  reg clk=0,capture=0,compact=0;
  reg [127:0] current,previous;
  wire [127:0] payload;wire [1:0] mode;
  kwt_row_pack dut(.*);
  always #5 clk=~clk;
  integer prev[0:7],nowv[0:7],n,l,delta,width,required,encoded,decoded,mask,count;
  integer limits[0:15];reg [31:0] rng=32'h35c104ad;
  initial begin
    limits[0]=-32768;limits[1]=32767;limits[2]=-2049;limits[3]=-2048;limits[4]=2047;limits[5]=2048;
    limits[6]=-129;limits[7]=-128;limits[8]=127;limits[9]=128;limits[10]=-9;limits[11]=-8;
    limits[12]=7;limits[13]=8;limits[14]=0;limits[15]=1;count=0;
    for(n=0;n<4096;n=n+1)begin
      @(negedge clk);compact=(n%17!=16);required=4;
      for(l=0;l<8;l=l+1)begin
        rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
        if(n<16)begin prev[l]=0;nowv[l]=(l==7)?limits[n]:0;end
        else if(n==17 || n==18)begin prev[l]=n==17?-32768:32767;nowv[l]=n==17?32767:-32768;end
        else begin
          prev[l]=$signed(rng[15:0]);
          case(n%4)
            0: delta=$signed(rng[3:0]);1: delta=$signed(rng[7:0]);2: delta=$signed(rng[11:0]);default:delta=$signed(rng[31:16]);endcase
          nowv[l]=prev[l]+delta;
          if(nowv[l]<-32768)nowv[l]=-32768;if(nowv[l]>32767)nowv[l]=32767;
        end
        previous[16*l+:16]=prev[l];current[16*l+:16]=nowv[l];
        delta=nowv[l]-prev[l];width=delta>=-8 && delta<=7 ? 4 : delta>=-128 && delta<=127 ? 8 :
                                     delta>=-2048 && delta<=2047 ? 12 : 16;
        if(width>required)required=width;
      end
      if(!compact)required=16;
      capture=1;@(posedge clk);#1;capture=0;
      width=4*(1+int'(mode));if(width!=required)$fatal(1,"wrong width %0d != %0d",width,required);
      mask=(1<<width)-1;
      for(l=0;l<8;l=l+1)begin
        encoded=(payload>>(width*l))&mask;
        decoded=(encoded & (1<<(width-1))) ? encoded-(1<<width) : encoded;
        if(width!=16)decoded=decoded+prev[l];
        if(decoded!=nowv[l])$fatal(1,"codec mismatch sample=%0d lane=%0d",n,l);
      end
      count=count+1;
    end
    $display("ALL PASS, %0d/4096 exact pack boundary/random cases",count);$finish;
  end
endmodule
