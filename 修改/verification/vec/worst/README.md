# 当前格式参考

每层x/w为输入编码槽、b为偏置、acc为40位累加、y为sy舍入前signed16、decoded为sy后完整signed16/F11、wire为实际输出的12672个32位字、groups为16组各792字。wire与decoded相同，无输出压缩。公共matrix_sat/reads/writes/params分别记录饱和计数、读次数、写次数和缩放字段。仅计分板读入黄金结果，DUT没有答案ROM。
