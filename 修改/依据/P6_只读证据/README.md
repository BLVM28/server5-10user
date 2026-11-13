# P6 旁路直接证据

来源Git对象5530ae66d132c73af3dac3683a995a456bd53afa，文件原路径soc/p6/rtl/kwt_e203_soc_top.v、soc/p6/tb/tb_soc_boot.sv。

顶层149行实例化两主仲裁器，151行把load_cmd_valid和sysmem_icb_cmd_valid并联；149–176行为完整接线，178行接共享SRAM。TB 39–41行连接load接口，172行起通过该接口装载。该旁路被答复第16问禁止。保留证据，不编译，不把删除几根线后不能工作的系统称为已修复。
