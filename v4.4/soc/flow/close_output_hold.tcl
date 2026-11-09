# Add physical delay only at constrained output endpoints with short paths.
# A non-inverting inverter pair preserves the pin polarity and all RTL cycles.
proc output_hold_paths {} {
    set outputs [remove_from_collection [all_outputs] [get_ports sys_clk]]
    set paths [dict create]
    foreach_in_collection port $outputs {
        foreach_in_collection path [get_timing_paths -to $port -delay_type min -max_paths 1] {
            dict set paths [get_object_name $port] [get_attribute $path slack]
        }
    }
    foreach port {hfxoscen lfxoscen io_pads_qspi0_cs_0_o_oval} {
        if {![dict exists $paths $port]} {error "Missing output hold path for $port"}
    }
    return $paths
}

proc close_output_hold {library report} {
    set target 0.075
    set inverter $library/INV1_12TH40
    if {[sizeof_collection [get_lib_cells $inverter]] != 1} {error "Output hold inverter unavailable"}
    set before [output_hold_paths]
    set after $before
    set pairs [dict create]
    for {set pass 0} {$pass < 4} {incr pass} {
        set changes 0
        dict for {port slack} $after {
            if {$slack >= $target} {continue}
            insert_buffer -inverter_pair [get_ports [list $port]] $inverter
            dict incr pairs $port
            incr changes
        }
        if {$changes == 0} {break}
        require_native_success "Timed output hold buffer insertion"
        extract_rc -estimate
        require_native_success "Timed output hold RC extraction"
        set after [output_hold_paths]
    }
    set table [open $report w]
    puts $table "port\tinverter_pairs\thold_before_ns\thold_after_ns\tsetup_after_ns"
    set worst 0
    dict for {port count} $pairs {
        set slack [dict get $after $port]
        set path [get_timing_paths -to [get_ports [list $port]] -delay_type max -max_paths 1]
        if {[sizeof_collection $path] != 1} {error "Missing setup path for buffered output $port"}
        set setup [get_attribute $path slack]
        puts $table [join [list $port $count [dict get $before $port] $slack $setup] "\t"]
        set worst [expr {min($worst, $slack, $setup)}]
    }
    close $table
    puts "V44_OUTPUT_HOLD_ECO endpoints=[dict size $pairs] pairs=[tcl::mathop::+ 0 {*}[dict values $pairs]]"
    if {$worst < 0} {error "Buffered output still violates timing, see $report"}
}
