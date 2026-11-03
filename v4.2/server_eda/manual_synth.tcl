set root $env(KWT_ROOT)
set rtlroot $env(KWT_RTL_ROOT)
set top $env(KWT_TOP)
set scripts [file join $root server_eda]
set_app_var search_path [concat $search_path [list [file join $rtlroot rtl]]]
set_app_var target_library [list $env(KWT_STD_DB)]
set_app_var link_library [concat [list *] $target_library [split $env(KWT_SRAM_DBS) |] [list dw_foundation.sldb]]
set_app_var synthetic_library [list dw_foundation.sldb]
if {$env(KWT_HOLD_FIX)} {
  set_min_library $env(KWT_STD_DB) -min_version $env(KWT_MIN_STD_DB)
  foreach maxdb [split $env(KWT_SRAM_DBS) |] mindb [split $env(KWT_MIN_SRAM_DBS) |] {
    set_min_library $maxdb -min_version $mindb
  }
}
define_design_lib WORK -path ./work
if {$top eq "kwt_dot64"} {
  set names {kwt_quantize.sv kwt_mul16_pipe.sv kwt_dot64.sv}
  set sources {}
  foreach n $names {lappend sources [file join $rtlroot rtl $n]}
} else {
  set f [open [file join $rtlroot rtl.f] r]
  set sources {}
  foreach line [split [string trim [read $f]] \n] {lappend sources [file join $rtlroot [string trim $line]]}
  close $f
}
analyze -format sverilog -define {KWT_USE_FOUNDRY_SRAM SYNTHESIS} $sources
if {$top eq "kwt_nice_core"} {
  # Explicit test-only region; default disabled window would optimize the core.
  elaborate $top -parameters {MEM_BASE=268435456,MEM_BYTES=524288}
} else {elaborate $top}
set actual [get_object_name [current_design]]
if {$actual ne $top} {rename_design $actual $top}
current_design $top
if {![link]} {error "Unresolved design references"}
uniquify
set_fix_multiple_port_nets -all -buffer_constants [get_designs *]
redirect -file check_design_before.rpt {check_design}
source [file join $scripts constraints.tcl]
if {$env(KWT_HOLD_FIX)} {
  # Optimization margin only; restore the original 0.1 ns for reported checks.
  # SS library hold requirements may exceed FF even when FF data is faster.
  set_clock_uncertainty -hold 0.180 [get_clocks core_clock]
  set_fix_hold [get_clocks core_clock]
}
redirect -file units.rpt {report_units}
redirect -file libraries.rpt {list_libs}
compile -map_effort medium
if {$env(KWT_HOLD_FIX)} {compile -incremental_mapping -only_hold_time}
set_clock_uncertainty -hold 0.100 [get_clocks core_clock]
change_names -rules verilog -hierarchy
redirect -file check_design.rpt {check_design}
redirect -file check_timing.rpt {check_timing}
redirect -file area.rpt {report_area -hierarchy}
redirect -file references.rpt {report_reference -hierarchy}
redirect -file qor.rpt {report_qor}
redirect -file setup.rpt {report_timing -delay_type max -max_paths 10 -transition_time -capacitance}
redirect -file hold.rpt {report_timing -delay_type min -max_paths 10 -transition_time -capacitance}
redirect -file violations.rpt {report_constraint -all_violators}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
write_sdf mapped.sdf
write_sdc constraints.sdc
puts "SYNTHESIS_COMPLETED $top"
exit
