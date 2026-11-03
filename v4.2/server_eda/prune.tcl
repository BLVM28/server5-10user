# Remove only proved-unloaded mapped cells, then revisit their upstream drivers.
set_app_var target_library [list $env(KWT_STD_DB)]
set_app_var link_library [concat [list *] $target_library [split $env(KWT_SRAM_DBS) |] [list dw_foundation.sldb]]
read_ddc $env(KWT_DDC)
current_design $env(KWT_TOP)
if {![link]} {error "Unresolved pre-cleanup DDC"}
proc leaf_connected {pin} {
    set net [get_nets -quiet -of_objects $pin]
    if {![sizeof_collection $net]} {return ""}
    return [all_connected -leaf $net]
}
proc has_sinks {cell} {
    foreach_in_collection p [get_pins -quiet -of_objects $cell -filter {direction != in}] {
        foreach_in_collection n [leaf_connected $p] {
            set cls [get_attribute $n object_class]
            set dir [get_attribute $n direction]
            if {($cls eq "port" && $dir ne "in") || ($cls eq "pin" && $dir ne "out")} {return 1}
        }
    }
    return 0
}
set todo {}
set f [open $env(KWT_PRUNE_TARGETS) r]
foreach name [split [string trim [read $f]] \n] {
    set p [get_pins -quiet $name]
    if {[sizeof_collection $p]!=1} {error "Unknown min-cap pin $name"}
    set c [get_cells -of_objects $p]
    if {[has_sinks $c]} {error "Refusing to remove a cell with a leaf consumer: $name"}
    lappend todo [get_object_name $c]
}
close $f
set proof [open pruned.txt w]
set total 0
while {[llength $todo]} {
    set old [lsort -unique $todo]
    set todo {}
    foreach name $old {
        set c [get_cells -quiet $name]
        if {[sizeof_collection $c]==0 || [has_sinks $c]} {continue}
        if {[get_attribute $c is_hierarchical]} {error "Refusing to remove hierarchy $name"}
        foreach_in_collection pin [get_pins -of_objects $c -filter {direction == in}] {
            foreach_in_collection related [leaf_connected $pin] {
                if {[get_attribute $related object_class] eq "pin" && [get_attribute $related direction] eq "out"} {
                    lappend todo [get_object_name [get_cells -of_objects $related]]
                }
            }
        }
        puts $proof "$name [get_attribute $c ref_name]"
        remove_cell $c
        incr total
        if {$total>512} {error "Unexpected cleanup size"}
    }
}
close $proof
if {$total<1} {error "No cells removed"}
redirect -file area.rpt {report_area -hierarchy}
redirect -file check_design.rpt {check_design}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
puts "DEAD_OUTPUT_CLEANUP_PASS $total"
exit
