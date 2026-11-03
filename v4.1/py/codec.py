"""Reference storage encoder and decoder. Inputs are final quantized int16 values."""
ROWS,COLS=99,256
WORDS=12896
def signed(value,width):
    value&=(1<<width)-1
    return value-(1<<width) if value&(1<<(width-1)) else value

def wire(word,low_first):
    return word if low_first else ((word>>16)|(word<<16))&0xffffffff

def encode(values,low_first=True):
    if len(values)!=ROWS*COLS or any(x < -32768 or x>32767 for x in values):
        raise ValueError("Expected a 99x256 signed16 matrix")
    memory=[0x5a5aa5a5]*12672+[0]*224
    histogram=[0]*4
    for g in range(32):
        previous=[0]*8
        for row in range(ROWS):
            start=row*COLS+8*g
            current=values[start:start+8]
            delta=[a-b for a,b in zip(current,previous)]
            mode=next((i for i,n in enumerate((4,8,12)) if all(-(1<<(n-1))<=v<(1<<(n-1)) for v in delta)),3)
            width=4*(mode+1);mask=(1<<width)-1
            bits=sum((v&mask)<<(i*width) for i,v in enumerate(current if mode==3 else delta))
            for i in range(mode+1):memory[row*128+g*4+i]=(bits>>(32*i))&0xffffffff
            memory[12672+g*7+row//16]|=mode<<(2*(row%16))
            histogram[mode]+=1
            previous=current
    return [wire(x,low_first) for x in memory],histogram

def decode(memory,low_first=True):
    if len(memory)<WORDS:raise ValueError("Short packed matrix")
    result=[0]*(ROWS*COLS)
    for g in range(32):
        previous=[0]*8
        for row in range(ROWS):
            tag=wire(memory[12672+7*g+row//16],low_first)
            if row==98 and tag>>6:raise ValueError("Invalid padding")
            mode=(tag>>(2*(row%16)))&3;width=(mode+1)*4
            slot=row*128+g*4
            bits=sum(wire(memory[slot+i],low_first)<<(32*i) for i in range(mode+1))
            for l in range(8):
                value=signed(bits>>(l*width),width)+(previous[l] if mode!=3 else 0)
                if not -32768<=value<=32767:raise ValueError("Invalid delta")
                result[row*COLS+8*g+l]=previous[l]=value
    return result
