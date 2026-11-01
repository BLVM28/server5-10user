set root $env(KWT_VM_ROOT)
read_lib $env(KWT_GPDK)/timing/$env(KWT_CORNER)_vdd1v0_basicCells.lib
set netdir synth_dot
if {[info exists env(KWT_ECO)] && $env(KWT_ECO) eq "1"} {set netdir eco_dot}
read_verilog $root/results/$env(KWT_VERSION)/$netdir/mapped.v
set_top_module kwt_dot64
read_sdc $root/flow/dot_tempus.sdc
report_timing -late -max_paths 10 > setup.rpt
report_timing -early -max_paths 10 > hold.rpt
report_timing -early -max_paths 10000 -max_slack 0.020 > near_hold.rpt
report_constraint -all_violators > constraints.rpt
report_constraint -all_violators -drv_violation_type {max_capacitance max_transition max_fanout} > drv.rpt
check_timing -verbose > coverage.rpt
# Installed GPDK models use $recovery and reset $hold, not $recrem.
# Native SDF 2.1/remashold preserves checks while matching that model syntax.
write_sdf -recompute_delay_calc -precision 6 -timescale ns -version 2.1 -recrem split -remashold -setuphold merge_always mapped_raw.sdf
# These GPDK Verilog models cannot represent negative single-limit recovery.
# Preserve raw SDF above. Zero negative limits ONLY in the simulation SDF:
# this tightens the timing windows; original Liberty checks remain in STA.
write_sdf -recompute_delay_calc -precision 6 -timescale ns -version 2.1 -recrem split -remashold -setuphold merge_always -nonegchecks mapped.sdf
puts KWT_TEMPUS_STA_COMPLETE
exit
