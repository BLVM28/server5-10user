# PrimeTime PX average power from the measured cold-task VCD.
set_app_var power_enable_analysis true
set_app_var power_analysis_mode averaged
set root $env(KWT_ROOT)
set top kwt_nice_core
set_app_var link_path [concat [list * $env(KWT_STD_DB)] [split $env(KWT_SRAM_DBS) |]]
read_verilog $env(KWT_NETLIST)
if {![link_design $top]} {error "Unresolved power netlist"}
source [file join $root server_eda constraints.tcl]
redirect -file units.rpt {report_units}
redirect -file operating_conditions.rpt {report_design}
read_vcd -strip_path $env(KWT_STRIP_PATH) $env(KWT_VCD)
update_timing
update_power
redirect -file power.rpt {report_power -verbose}
redirect -file power_hierarchy.rpt {report_power -hierarchy}
redirect -file switching.rpt {report_switching_activity}
redirect -file unannotated.rpt {report_switching_activity -list_not_annotated}
set f [open power_attributes.txt w]
foreach a {internal_power switching_power leakage_power dynamic_power total_power} {
  if {![catch {get_attribute [current_design] $a} v]} {puts $f "$a $v"}
}
close $f
puts "POWER_COMPLETED kwt_nice_core"
exit
