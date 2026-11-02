# Incremental physical-cell repair. Read a previously hold/reset-repaired DDC.
# Final STA always rebuilds the original constraints independently.
set root $env(KWT_ROOT)
set top $env(KWT_TOP)
set_app_var target_library [list $env(KWT_STD_DB)]
set_app_var link_library [concat [list *] $target_library [split $env(KWT_SRAM_DBS) |] [list dw_foundation.sldb]]
set_min_library $env(KWT_STD_DB) -min_version $env(KWT_MIN_STD_DB)
foreach maxdb [split $env(KWT_SRAM_DBS) |] mindb [split $env(KWT_MIN_SRAM_DBS) |] {set_min_library $maxdb -min_version $mindb}
read_ddc $env(KWT_DDC)
current_design $top
if {![link]} {error "Unresolved design"}
source [file join $root server_eda constraints.tcl]
puts "CONSTRAINT_OUTPUT_LOAD reference=v1 four_pin_cap=0.002852"
# Two observed SS cap violations plus three setup/hold delay-balancing cells.
# Pin functions were checked against the real SS library.
# Preserve all other mapped cells; do not run a global incremental remap.
foreach {instance oldref newref} {master/U381 INV2_12TH40 INV3_12TH40 U1770 BUFV2RD_12TH40 BUFV3RD_12TH40 core/mac/lane_4__dot/U8 DEL4V0_12TH40 DEL2V0_12TH40 core/mac/lane_5__dot/U15 DEL4V0_12TH40 DEL2V0_12TH40 core/mac/lane_5__dot/U17 DEL4V0_12TH40 DEL2V0_12TH40} {
 set cell [get_cells $instance]
 if {[sizeof_collection $cell] != 1 || [get_attribute $cell ref_name] ne $oldref} {error "ECO source mismatch: $instance"}
 # Both SS and FF are loaded; resize against the SS target library only.
 set target [get_lib_cells *ss*/$newref]
 if {[sizeof_collection $target] != 1} {error "ECO library mismatch: $newref"}
 size_cell $cell [get_object_name $target]
 puts "ECO_SIZED $instance $oldref -> $newref"
}
change_names -rules verilog -hierarchy
redirect -file units.rpt {report_units}
redirect -file check_design.rpt {check_design}
redirect -file area.rpt {report_area -hierarchy}
redirect -file references.rpt {report_reference -hierarchy}
redirect -file qor.rpt {report_qor}
redirect -file violations.rpt {report_constraint -all_violators -significant_digits 6}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
write_sdf mapped.sdf
write_sdc constraints.sdc
puts "ECO_REPAIR_COMPLETE $top"
exit
