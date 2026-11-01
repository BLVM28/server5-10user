set root $env(KWT_VM_ROOT)
set src $root/work/$env(KWT_VERSION)
set_db max_cpus_per_server 2
set_db library [list $env(KWT_GPDK)/timing/slow_vdd1v0_basicCells.lib]
read_hdl -language sv [list $src/rtl/kwt_quantize.sv $src/rtl/kwt_mul16_pipe.sv $src/rtl/kwt_dot64.sv]
elaborate kwt_dot64
read_sdc $root/flow/dot.sdc
check_design > check_design.rpt
syn_generic
syn_map
syn_opt
report_timing -max_paths 10 > timing.rpt
report_area > area.rpt
report_design_rules > design_rules.rpt
write_hdl > mapped.v
write_sdc > exported.sdc
write_sdf -version 3.0 -precision 4 -timescale ns -setuphold merge_always -recrem merge_always > mapped.sdf
puts KWT_GENUS_SYNTH_COMPLETE
exit
