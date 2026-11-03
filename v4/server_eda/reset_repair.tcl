# A stronger optimization target, never a final STA timing exception.
if {$top eq "kwt_nice_core"} {set reset_port nice_rst_n} else {set reset_port rst_n}
set reset_pins [get_pins -hierarchical -filter "full_name =~ */RDN || full_name =~ */SDN"]
if {[sizeof_collection $reset_pins]==0} {error "No mapped async-reset pins found"}
puts "RESET_REPAIR endpoints=[sizeof_collection $reset_pins] min_delay=0.400"
set_min_delay 0.400 -from [get_ports $reset_port] -to $reset_pins
set_fix_hold [get_clocks core_clock]
compile -incremental_mapping -only_hold_time
# PrimeTime independently creates the original constraints from scratch.
reset_path -from [get_ports $reset_port] -to $reset_pins
