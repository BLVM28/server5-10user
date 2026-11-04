set root $env(KWT_ROOT)
set top $env(KWT_TOP)
set_app_var link_path [concat [list * $env(KWT_STD_DB)] [split $env(KWT_SRAM_DBS) |]]
read_verilog $env(KWT_NETLIST)
if {![link_design $top]} {error "Unresolved netlist references"}
source [file join $root server_eda constraints.tcl]
redirect -file units.rpt {report_units}
redirect -file libraries.rpt {list_libs}
update_timing
redirect -file check_timing.rpt {check_timing -verbose}
redirect -file clocks.rpt {report_clock -attributes}
redirect -file setup.rpt {report_timing -delay_type max -slack_lesser_than 100000 -max_paths 10 -input_pins -nets -transition_time -capacitance}
redirect -file hold.rpt {report_timing -delay_type min -slack_lesser_than 100000 -max_paths 10 -input_pins -nets -transition_time -capacitance}
redirect -file violations.rpt {report_constraint -all_violators -significant_digits 6}
redirect -file coverage.rpt {report_analysis_coverage}
redirect -file untested.rpt {report_analysis_coverage -status_details untested}
redirect -file disabled_arcs.rpt {report_disable_timing [get_cells -hierarchical]}
redirect -file reg_setup.rpt {report_timing -delay_type max -slack_lesser_than 100000 -from [all_registers -output_pins] -to [all_registers -data_pins] -max_paths 3}
redirect -file data_hold.rpt {report_timing -delay_type min -slack_lesser_than 100000 -to [all_registers -data_pins] -max_paths 3}
set topo [open topology.txt w]
foreach ref {RAMSP128X16 RAMSP1024X16} {
  set macro_cells [get_cells -hierarchical -quiet -filter "ref_name == $ref"]
  puts $topo "$ref [sizeof_collection $macro_cells]"
}
close $topo
set f [open metrics.txt w]
foreach delay {max min} {
  set paths [get_timing_paths -delay_type $delay -max_paths 1]
  if {[sizeof_collection $paths]==0} {error "No timing paths for $delay"}
  set p [index_collection $paths 0]
  puts $f "$delay slack=[get_attribute $p slack] start=[get_object_name [get_attribute $p startpoint]] end=[get_object_name [get_attribute $p endpoint]]"
}
close $f
write_sdf -version 3.0 -context verilog -exclude {clock_tree_path_models} mapped.sdf
puts "STA_COMPLETED $top corner=$env(KWT_CORNER)"
exit
