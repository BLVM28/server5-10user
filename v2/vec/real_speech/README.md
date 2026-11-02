# 真实语音导出向量

class_00 至 class_11 为各类别代表激活；worst 为逐层选出的较大误差激活。make regress 自动测试所有 13 组。生成来源、样本与哈希见 ../../validation_real_speech_20261102/README.md。每层独立输入，不是将 Dense1 输出直接串给下一层。
