set root $env(KWT_VM_ROOT)
read_lib $env(KWT_GPDK)/timing/fast_vdd1v0_basicCells.lib
read_verilog $root/results/$env(KWT_VERSION)/eco_dot/mapped.v
set_top_module kwt_dot64
read_sdc $root/flow/dot_tempus.sdc
report_timing -early -max_paths 10000 -max_slack 0.020 > near_hold.rpt
puts KWT_NEAR_HOLD_COMPLETE
exit
