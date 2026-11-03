# Resize only named, measured cap violations in a repaired, mapped full core.
set root $env(KWT_ROOT)
set top $env(KWT_TOP)
set_app_var target_library [list $env(KWT_STD_DB)]
set_app_var link_library [concat [list *] $target_library [split $env(KWT_SRAM_DBS) |] [list dw_foundation.sldb]]
set_min_library $env(KWT_STD_DB) -min_version $env(KWT_MIN_STD_DB)
foreach maxdb [split $env(KWT_SRAM_DBS) |] mindb [split $env(KWT_MIN_SRAM_DBS) |] {set_min_library $maxdb -min_version $mindb}
read_ddc $env(KWT_DDC)
current_design $top
if {![link]} {error "Unresolved pre-ECO netlist"}
source [file join $root server_eda constraints.tcl]
set plan [open $env(KWT_ECO_PLAN) r]
set changes 0
while {[gets $plan row] >= 0} {
    set row [string trim $row]
    if {$row eq "" || [string index $row 0] eq "#"} {continue}
    if {[llength $row] != 5} {error "Expected instance oldref newref output_pin measured_cap"}
    lassign $row inst oldref newref output measured
    set cell [get_cells $inst]
    if {[sizeof_collection $cell] != 1 || [get_attribute $cell ref_name] ne $oldref} {error "Unexpected ECO source: $inst"}
    set old [get_lib_cells *ss*/$oldref]
    set new [get_lib_cells *ss*/$newref]
    if {[sizeof_collection $new] != 1 || [sizeof_collection $old] != 1} {error "No unique SS library cells"}
    foreach lib [list $old $new] {
        set pin_names {}
        foreach_in_collection pin [get_lib_pins -of_objects $lib] {
            lappend pin_names [list [lindex [split [get_object_name $pin] /] end] [get_attribute $pin direction]]
        }
        set ref [lindex [split [get_object_name $lib] /] end]
        set pins($ref) [lsort $pin_names]
    }
    if {$pins($oldref) ne $pins($newref)} {error "ECO pinout differs"}
    set oldpin [get_lib_pins *ss*/$oldref/$output]
    set newpin [get_lib_pins *ss*/$newref/$output]
    set func [get_attribute $oldpin function]
    if {$func eq "" || $func ne [get_attribute $newpin function]} {error "ECO Boolean function differs"}
    if {[get_attribute $newpin max_capacitance] <= $measured} {error "New cell cannot drive measured load"}
    size_cell $cell [get_object_name $new]
    incr changes
    puts "ECO_CELL $inst $oldref => $newref function=$func"
}
close $plan
if {$changes == 0} {error "Empty cap repair plan"}
redirect -file area.rpt {report_area -hierarchy}
redirect -file check_design.rpt {check_design}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
puts "ECO_COMPLETE $top changes=$changes"
exit
