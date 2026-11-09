# Redefine the existing clock in place to retain the virtual route and all
# timing constraints. Verify the full exported SDC before accepting a probe.
proc sdc_without_core_period {file} {
    write_sdc $file
    set stream [open $file r]
    set sdc [read $stream]
    close $stream
    set sdc [regsub -all {(?m)^#[^\n]*\n} $sdc {}]
    set expression {(?m)^create_clock[^\n]*-name[ \t]+core_clk[ \t][^\n]*$}
    if {[regexp -all $expression $sdc] != 1} {error "Expected one SDC core clock"}
    return [regsub $expression $sdc CORE_CLOCK]
}

proc define_core_period {period async_group} {
    create_clock -name core_clk -period $period -waveform [list 0 [expr {$period / 2.0}]] [get_ports hfextclk]
    create_generated_clock -name sys_clk_out -source [get_ports hfextclk] \
        -master_clock core_clk -divide_by 1 [get_ports sys_clk]
    remove_clock_groups -asynchronous -all
    set_clock_groups -asynchronous -name $async_group -group [get_clocks {core_clk sys_clk_out}] \
        -group [get_clocks aon_clk] -group [get_clocks jtag_clk]
    # DC calculates a newly created generated clock at the next timing update.
    get_timing_paths -group core_clk -delay_type max -max_paths 1
    set actual [get_attribute [get_clocks core_clk] period]
    set generated [get_attribute [get_clocks sys_clk_out] period]
    if {![string is double -strict $generated] ||
        abs($actual - $period) > 0.00002 || abs($generated - $period) > 0.00002} {
        error "Target primary/generated periods disagree: $actual/$generated"
    }
    require_native_success "Redefine the core clock period"
}

proc probe_period {target original_groups label {keep_target 0}} {
    global OUT
    set probe $OUT/period_probe
    file mkdir $probe
    set original [get_attribute [get_clocks core_clk] period]
    set before [group_slacks $original_groups]
    set base_sdc [sdc_without_core_period $probe/exported.sdc]
    if {[regexp -all {(?m)^set_clock_groups[ \t]} $base_sdc] != 1 ||
        ![regexp {(?m)^set_clock_groups[^\n]*-asynchronous[^\n]*-name[ \t]+([^ \t\n]+)} $base_sdc -> async_group]} {
        error "Cannot identify the original asynchronous clock group"
    }
    define_core_period $target $async_group
    if {[sdc_without_core_period $probe/target.sdc] ne $base_sdc} {
        error "Changing the period also changed other exported timing constraints"
    }
    check_mapped_timing $probe/check_timing.rpt
    set result [timing_extrema $label $probe/target]
    set target_groups [group_slacks $probe/target/path_groups.tsv]
    if {[lsort [dict keys $before]] ne [lsort [dict keys $target_groups]]} {error "Probe changed path groups"}
    write_sdf $probe/soc_target.sdf
    define_core_period $original $async_group
    timing_extrema restore_original $probe/restored
    set restored [group_slacks $probe/restored/path_groups.tsv]
    if {[lsort [dict keys $before]] ne [lsort [dict keys $restored]]} {error "Restored path groups changed"}
    dict for {key slack} $before {
        if {abs($slack - [dict get $restored $key]) > 0.0002} {
            error "Restored $key slack from $slack to [dict get $restored $key]"
        }
    }
    if {$keep_target} {
        define_core_period $target $async_group
        if {[sdc_without_core_period $probe/final.sdc] ne $base_sdc} {
            error "The retargeted constraints differ from the checked target"
        }
    }
    puts "V45_PERIOD_PROBE_COMPLETE period=$target setup=[dict get $result max slack_ns] hold=[dict get $result min slack_ns]"
    require_native_success "Target period report"
}
