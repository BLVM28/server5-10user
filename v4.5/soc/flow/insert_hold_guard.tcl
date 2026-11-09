set list_file [file normalize $env(SOC_HOLD_CANDIDATES)]
set source_hash [exec sha256sum -- $list_file]
set inverter $MAX_LIB_NAME/INV1_12TH40
if {[sizeof_collection [get_lib_cells $inverter]] != 1} {error "Hold cell not available"}
set f [open $list_file r]
gets $f header
if {$header ne "endpoint\tslack_ns"} {error "Invalid hold list"}
set log [open reports/hold_guard.tsv w]
puts $log "endpoint\tfast_before_ns\tsetup_before_ns\taction"
set count 0
while {[gets $f line] >= 0} {
    lassign [split $line \t] name before
    if {![string is double -strict $before] || $before >= 0.020} {error "Invalid hold candidate: $line"}
    set pin [get_pins -quiet [list $name]]
    set endpoint $pin
    if {[sizeof_collection $pin] == 0} {set endpoint [get_ports -quiet [list $name]]}
    if {[sizeof_collection $endpoint] != 1} {error "Hold endpoint unavailable: $name"}
    if {[sizeof_collection $pin] != 0 &&
        ([get_attribute $pin direction] ne "in" || [file tail $name] ne "D")} {
        puts $log "$name\t$before\t-\tSKIP_NOT_DATA"
        continue
    }
    set path [get_timing_paths -to $endpoint -delay_type max -max_paths 1]
    if {[sizeof_collection $path] != 1} {error "Hold endpoint has no setup check: $name"}
    set setup [get_attribute $path slack]
    if {$setup < 0.200} {
        puts $log "$name\t$before\t$setup\tSKIP_SETUP"
        continue
    }
    insert_buffer -inverter_pair $endpoint $inverter
    puts $log "$name\t$before\t$setup\tINSERT_PAIR"
    incr count
}
close $f
close $log
if {$count == 0} {error "No hold pads inserted"}
if {[exec sha256sum -- $list_file] ne $source_hash} {error "Hold candidates changed"}
require_native_success "Inserted hold guard buffers on data endpoints"
extract_rc -estimate
require_native_success "Hold guard RC extraction"
puts "V45_HOLD_PAD_COMPLETE endpoints=$count $OUT"
