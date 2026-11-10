# Loaded after mapping by the P6 deck. The same circuit is checked in place.
proc select_kwt_endpoints {} {
    global kwt_from kwt_to
    set macros [get_cells -hierarchical -filter {full_name =~ */u_kwt/* && ref_name =~ RAMSP*}]
    if {[sizeof_collection $macros] != 72} {error "Expected 72 accelerator SRAM macros"}
    set inputs [get_pins -of_objects $macros -filter {direction == in}]
    set clocks [filter_collection $inputs {full_name =~ */CLK}]
    set registers [filter_collection [all_registers -cells] {full_name =~ */u_kwt/*}]
    set register_clocks [filter_collection [all_registers -clock_pins] {full_name =~ */u_kwt/*}]
    set register_inputs [get_pins -of_objects $registers -filter {direction == in}]
    set kwt_from [add_to_collection $register_clocks $clocks]
    set kwt_to [add_to_collection [remove_from_collection $register_inputs $register_clocks] \
        [remove_from_collection $inputs $clocks]]
    if {[sizeof_collection $kwt_from] <= 72 || [sizeof_collection $kwt_to] == 0} {
        error "Accelerator timing endpoints did not resolve"
    }
}

proc electrical_row {label report table} {
    set rules {max_transition max_capacitance max_fanout}
    foreach rule $rules {
        dict set counts kwt $rule 0
        dict set counts soc $rule 0
    }
    set f [open $report r]
    set section {}
    set preceding {}
    while {[gets $f line] >= 0} {
        set name [string trim $line]
        if {[regexp {^(max|min)_[a-z_]+$} $name]} {set section $name}
        if {$section in $rules && [string first "(VIOLATED)" $line] >= 0} {
            dict set counts soc $section [expr {[dict get $counts soc $section] + 1}]
            if {[regexp {^\s*[-+]?[0-9]} $line]} {set line "$preceding $line"}
            if {[string first /u_kwt/ $line] >= 0} {
                dict set counts kwt $section [expr {[dict get $counts kwt $section] + 1}]
            }
        }
        set preceding $line
    }
    close $f
    foreach scope {kwt soc} {
        foreach rule $rules {puts $table [join [list $label $scope $rule [dict get $counts $scope $rule]] "\t"]}
    }
    flush $table
    puts "KWT_ELECTRICAL $label $counts"
    return $counts
}

proc raw_coverage_ok {report} {
    set stream [open $report r]
    set text [read $stream]
    close $stream
    foreach line [split $text \n] {
        set line [string trimleft $line]
        if {[string match {Warning:*} $line] &&
            ![string match {Warning: The following input ports have no clock_relative delay specified*} $line]} {
            return 0
        }
    }
    return 1
}

proc timing_row {label table} {
    global kwt_from kwt_to
    set values {}
    foreach delay {max min} {
        set worst 100000
        foreach side {internal to from soc} {
            set selector {}
            if {$side eq "to"} {set selector [list -to $kwt_to]}
            if {$side eq "from"} {set selector [list -from $kwt_from]}
            if {$side eq "internal"} {set selector [list -from $kwt_from -to $kwt_to]}
            set paths [get_timing_paths -delay_type $delay -max_paths 1 {*}$selector]
            if {[sizeof_collection $paths] == 0} {error "Missing path: $label/$side/$delay"}
            set slack 100000
            foreach_in_collection path $paths {
                set path_slack [get_attribute $path slack]
                if {$path_slack < $slack} {
                    set slack $path_slack
                    set start [get_object_name [get_attribute $path startpoint]]
                    set stop [get_object_name [get_attribute $path endpoint]]
                }
            }
            puts $table [join [list $label $side $delay $slack $start $stop] "\t"]
            if {$side in {soc internal}} {dict set values ${side}_$delay $slack} \
            elseif {$slack < $worst} {set worst $slack}
        }
        dict set values kwt_$delay $worst
    }
    flush $table
    puts "KWT_TIMING $label $values"
    flush stdout
    return $values
}

# Use the same clock-redefinition and full SDC comparison as the measured
# v4.5 period probe. Only the core period and its waveform may differ.
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
    get_timing_paths -group core_clk -delay_type max -max_paths 1
    foreach name {core_clk sys_clk_out} {
        set actual [get_attribute [get_clocks $name] period]
        if {![string is double -strict $actual] || abs($actual - $period) > 0.00002} {
            error "Target clock period disagrees: $name $actual expected $period"
        }
    }
    require_native_success "Redefine the core clock period"
}

if {[info exists kwt_define_procs_only] && $kwt_define_procs_only} {return}

set table [open reports/kwt_paths.tsv w]
puts $table "case\tscope\tcheck\tslack_ns\tstartpoint\tendpoint"
set electrical [open reports/electrical.tsv w]
puts $electrical "case\tscope\trule\trecords"
select_kwt_endpoints
set periods [dict create 160 6.25 150 6.666666667]
# A repeated native check can print a warning without incrementing the
# message counter. The raw report is also required for platform coverage.
set coverage [dict create 160 [expr {$timing_coverage_ok && [raw_coverage_ok reports/check_timing.rpt]}]]
dict set primary 160 [timing_row 160/primary $table]
set primary_electrical [electrical_row 160/primary reports/violations.rpt $electrical]
set coverage_file [open reports/check_timing.rpt r]
set kwt_coverage_ok [expr {[string first /u_kwt/ [read $coverage_file]] < 0}]
close $coverage_file
set base_sdc [sdc_without_core_period reports/period160.sdc]
if {[regexp -all {(?m)^set_clock_groups[ \t]} $base_sdc] != 1 ||
    ![regexp {(?m)^set_clock_groups[^\n]*-asynchronous[^\n]*-name[ \t]+([^ \t\n]+)} $base_sdc -> async_group]} {
    error "Cannot identify the original asynchronous clock group"
}
define_core_period [dict get $periods 150] $async_group
if {[sdc_without_core_period reports/period150.sdc] ne $base_sdc} {
    error "Changing the period also changed other exported timing constraints"
}
set coverage_native_150 [expr {![catch {check_mapped_timing reports/check_timing_150.rpt} coverage_message]}]
if {!$coverage_native_150} {puts "KWT_COVERAGE_FAILED_150 $coverage_message"}
dict set coverage 150 [expr {$coverage_native_150 && [dict get $coverage 160] && [raw_coverage_ok reports/check_timing_150.rpt]}]
dict set primary 150 [timing_row 150/primary $table]
define_core_period [dict get $periods 160] $async_group
set restored [timing_row 160/restored $table]
dict for {name slack} $restored {
    if {abs($slack - [dict get $primary 160 $name]) > 0.0002} {
        error "Restored 160 MHz slack changed for $name"
    }
}
set report [open reports/primary_acceptance.txt w]
foreach mhz {150 160} {
    puts $report "PRIMARY_$mhz [dict get $primary $mhz]"
    puts $report "COVERAGE_${mhz}_PASS=[dict get $coverage $mhz]"
}
close $report

set worst [dict get $primary 160]
set where {}
dict for {name slack} $worst {dict set where $name primary}
set checked 0
set most_violations $primary_electrical
set electrical_ok $kwt_coverage_ok
dict for {rule count} [dict get $primary_electrical kwt] {if {$count != 0} {set electrical_ok 0}}
# A negative primary slack already establishes a failure at that period.
if {$electrical_ok && [dict get $worst kwt_max] >= 0 && [dict get $worst kwt_min] >= 0} {
    foreach library [concat [list $STD_MAX] $SRAM_MAX] {set_min_library $library -none}
    foreach specification $CORNER_SPECS {
        set corner [lindex $specification 0]
        bind_single_corner $corner reports/${corner}_bound_libraries.txt
        select_kwt_endpoints
        foreach rc $RC_CORNERS {
            set_tlu_plus_files -max_tluplus $RC_DIRECTORY/$rc.tluplus \
                -min_tluplus $RC_DIRECTORY/$rc.tluplus -tech2itf_map $TECH_MAP
            extract_rc -estimate
            require_native_success "RC extraction $corner/$rc"
            set row [timing_row 160/$corner/$rc $table]
            dict for {name slack} $row {
                if {$slack < [dict get $worst $name]} {
                    dict set worst $name $slack
                    dict set where $name $corner/$rc
                }
            }
            set detail reports/${corner}_${rc}_violations.rpt
            redirect -file $detail {report_constraint -all_violators}
            set counts [electrical_row 160/$corner/$rc $detail $electrical]
            foreach scope {kwt soc} {
                dict for {rule count} [dict get $counts $scope] {
                    if {$count > [dict get $most_violations $scope $rule]} {
                        dict set most_violations $scope $rule $count
                    }
                }
            }
            incr checked
        }
    }
}

close $table
close $electrical
set report [open reports/acceptance.txt w]
foreach mhz {150 160} {
    puts $report "PERIOD_${mhz}_NS=[dict get $periods $mhz]"
    puts $report "COVERAGE_${mhz}_PASS=[dict get $coverage $mhz]"
    puts $report "PRIMARY_$mhz [dict get $primary $mhz]"
}
puts $report "CORNER_CHECKS_160=$checked"
puts $report "WORST_160 $worst"
puts $report "WORST_CORNERS_160 $where"
puts $report "MAX_ELECTRICAL_RECORDS_160 $most_violations"
puts $report "KWT_ENDPOINT_COVERAGE_PASS=$kwt_coverage_ok"
foreach scope {kwt soc} {
    set timing_ok [expr {$checked == 35 && [dict get $worst ${scope}_max] >= 0 && [dict get $worst ${scope}_min] >= 0}]
    set electrical_ok [expr {$checked == 35}]
    dict for {rule count} [dict get $most_violations $scope] {
        if {$count != 0} {set electrical_ok 0}
    }
    set cover [expr {$scope eq "kwt" ? $kwt_coverage_ok : [dict get $coverage 160]}]
    set name [string toupper $scope]
    puts $report "${name}_TIMING_160_PASS=$timing_ok"
    puts $report "${name}_ELECTRICAL_160_PASS=$electrical_ok"
    puts $report "${name}_160_PASS=[expr {$timing_ok && $electrical_ok && $cover}]"
}
close $report
puts "KWT_TIMING_DONE $OUT"
