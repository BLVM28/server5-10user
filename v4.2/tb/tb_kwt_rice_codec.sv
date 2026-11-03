// Independent token/word scoreboard with full-range residuals and cross-word tails.
`timescale 1ns/1ps
module tb_kwt_rice_codec;
  localparam N=257;
  reg clk=0,rst_n=0,clear=0,tv=0,flush=0,pop=0,push=0,consume=0;
  reg [19:0] tok;reg [4:0] width;reg [31:0] input_word;
  reg [3:0] key,shift;
  wire room,empty,wv,space,valid,absolute,tail;wire [31:0] word;wire signed [16:0] value;
  kwt_rice_pack p(.clk(clk),.rst_n(rst_n),.clear(clear),.token_valid(tv),.token(tok),.width(width),
      .flush(flush),.room(room),.empty(empty),.word_valid(wv),.pop(pop),.word(word));
  kwt_rice_unpack u(.clk(clk),.rst_n(rst_n),.clear(clear),.push(push),.word(input_word),
      .key(key),.shift(shift),.consume(consume),.room(space),.valid(valid),.absolute(absolute),.tail_clean(tail),.value(value));
  always #5 clk=~clk;
  integer widths[0:N-1],keys[0:N-1],values[0:N-1],esc[0:N-1];
  reg [19:0] tokens[0:N-1];reg [31:0] gold[0:N-1];
  integer i,j,s,k,d,z,v,q,t,b,n,at,nn,wr,rd,c,checks=0,shorts=0,escapes=0,crossings=0;
  initial begin
    repeat(3)@(negedge clk);rst_n=1;
    // In a fresh FIFO the second RAM word has never been initialized. Cross a
    // prefix at bit 31 on the same cycle as the next word arrives.
    key=0;shift=0;push=1;input_word=32'h80000000;@(negedge clk);push=0;
    for(i=0;i<31;i=i+1)begin consume=1;@(negedge clk);end
    consume=0;#1;if(valid!==1'b0)$fatal(1,"undefined prefix before refill");
    push=1;input_word=0;@(negedge clk);push=0;#1;
    if(valid!==1'b1 || $signed(value)!==-1 || u.count!==2)$fatal(1,"refill lost at cross-word prefix");
    $display("RICE FIRST REFILL PASS 1/1");
    for(s=0;s<=5;s=s+1)begin
      clear=1;@(negedge clk);clear=0;shift=s;
      at=0;for(i=0;i<N;i=i+1)gold[i]=0;
      for(i=0;i<N;i=i+1)begin
        k=i%16;keys[i]=k;
        case((i/16)%8)
          0:d=0;1:d=-1;2:d=(1<<k)-1;3:d=-(1<<k);4:d=65535;5:d=-65535;6:d=17;default:d=-73;
        endcase
        v=i%2 ? -(32768>>s) : (32767>>s);
        z=d<0?-2*d-1:2*d;q=z>>k;
        if(q<4)begin n=q+1+k;t=((1<<q)-1)|((z&((1<<k)-1))<<(q+1));values[i]=d;esc[i]=0;shorts=shorts+1;end
        else begin n=20-s;t=15|((v&((1<<(16-s))-1))<<4);values[i]=v;esc[i]=1;escapes=escapes+1;end
        tokens[i]=t;widths[i]=n;if(at%32+n>32)crossings=crossings+1;
        for(j=0;j<n;j=j+1)gold[(at+j)/32][(at+j)%32]=(t>>j)&1;
        at=at+n;
      end
      nn=(at+31)/32;wr=0;rd=0;c=0;
      while(wr<N || !empty)begin
        tv=wr<N && room && c%7!=0;flush=wr==N;
        tok=wr<N?tokens[wr]:0;width=wr<N?widths[wr]:0;pop=wv&&c%5!=0;
        if(pop)begin if(word!==gold[rd])$fatal(1,"pack word %0d",rd);rd=rd+1;end
        if(tv)wr=wr+1;
        @(negedge clk);c=c+1;
      end
      if(rd!=nn)$fatal(1,"pack word count");flush=0;tv=0;pop=0;
      wr=0;rd=0;c=0;
      while(rd<N)begin
        key=keys[rd];#1;
        push=wr<nn && space && c%4!=0;input_word=wr<nn?gold[wr]:0;
        consume=valid && c%6!=0;
        if(consume)begin
          if($signed(value)!==values[rd] || absolute!==esc[rd][0])$fatal(1,"unpack symbol %0d scale=%0d k=%0d",rd,s,key);
          if(rd==N-1 && !tail)$fatal(1,"clean tail rejected");
          rd=rd+1;checks=checks+1;
        end
        if(push)wr=wr+1;
        @(negedge clk);c=c+1;
      end
      if(wr!=nn)$fatal(1,"incorrect consumption");
      push=0;consume=0;
    end
    // Independent malformed tails: set unused high bit, truncated unary prefix,
    // and a token finishing exactly at the 32-bit boundary.
    for(s=0;s<3;s=s+1)begin
      clear=1;@(negedge clk);clear=0;key=0;shift=0;
      push=1;input_word=(s==2)?0:32'h80000000;
      @(negedge clk);push=0;
      if(s==0)begin if(!valid || tail)$fatal(1,"nonzero padding accepted");end
      else begin
        for(i=0;i<31;i=i+1)begin consume=1;@(negedge clk);end
        consume=0;#1;
        if(s==1 && valid)$fatal(1,"truncated final prefix accepted");
        if(s==2 && (!valid || !tail))$fatal(1,"aligned final word rejected");
      end
    end
    $display("RICE TAIL PASS 3/3");
    if(shorts==0 || escapes==0 || crossings<100)$fatal(1,"missing prefix coverage");
    $display("ALL PASS, %0d/1542 Rice symbols, short=%0d escape=%0d crossing=%0d",checks,shorts,escapes,crossings);$finish;
  end
  initial begin #10000000;$fatal(1,"codec timeout");end
endmodule
