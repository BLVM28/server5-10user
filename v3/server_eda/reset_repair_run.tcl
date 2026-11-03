set root $env(KWT_ROOT)
set top $env(KWT_TOP)
set_app_var target_library [list $env(KWT_STD_DB)]
set_app_var link_library [concat [list *] $target_library [split $env(KWT_SRAM_DBS) |] [list dw_foundation.sldb]]
set_min_library $env(KWT_STD_DB) -min_version $env(KWT_MIN_STD_DB)
foreach maxdb [split $env(KWT_SRAM_DBS) |] mindb [split $env(KWT_MIN_SRAM_DBS) |] {
  set_min_library $maxdb -min_version $mindb
}
read_ddc $env(KWT_DDC)
current_design $top
if {![link]} {error "Unresolved repaired design"}
source [file join $root server_eda constraints.tcl]
puts "CONSTRAINT_OUTPUT_LOAD reference=v1 four_pin_cap=0.002852"
source [file join $root server_eda reset_repair.tcl]
change_names -rules verilog -hierarchy
redirect -file units.rpt {report_units}
redirect -file check_design.rpt {check_design}
redirect -file check_timing.rpt {check_timing}
redirect -file area.rpt {report_area -hierarchy}
redirect -file references.rpt {report_reference -hierarchy}
redirect -file qor.rpt {report_qor}
redirect -file violations.rpt {report_constraint -all_violators}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
write_sdf mapped.sdf
write_sdc constraints.sdc
puts "RESET_REPAIR_COMPLETE $top"
exit
