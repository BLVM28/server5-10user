set cutoff 0.020
set paths [get_timing_paths -delay_type min -slack_lesser_than $cutoff -max_paths 2000 -nworst 1]
if {[sizeof_collection $paths] >= 2000} {error "Near-critical hold scan reached its limit"}
set rows [dict create]
foreach_in_collection path $paths {
    set endpoint [get_object_name [get_attribute $path endpoint]]
    set slack [get_attribute $path slack]
    if {![dict exists $rows $endpoint] || $slack < [dict get $rows $endpoint]} {
        dict set rows $endpoint $slack
    }
}
set out [open $OUT/reports/hold_candidates.tsv w]
puts $out "endpoint\tslack_ns"
dict for {endpoint slack} $rows {puts $out "$endpoint\t$slack"}
close $out
puts "V45_HOLD_SCAN_COMPLETE endpoints=[dict size $rows] cutoff=$cutoff $OUT"
require_native_success "Fast-corner hold endpoint scan"
