# Preliminary, explicit assumptions. No false paths or multicycle exceptions.
# Time units are reported by each tool and must be ns for the 150 MHz claim.
if {$top eq "kwt_nice_core"} {set clkport nice_clk} else {set clkport clk}
set period 6.666667
if {[info exists env(KWT_PERIOD)]} {set period $env(KWT_PERIOD)}
create_clock -name core_clock -period $period [get_ports $clkport]
set_clock_uncertainty -setup 0.150 [get_clocks core_clock]
set_clock_uncertainty -hold 0.100 [get_clocks core_clock]
set inputs [remove_from_collection [all_inputs] [get_ports $clkport]]
set_input_delay -clock core_clock -max 1.000 $inputs
set_input_delay -clock core_clock -min 0.100 $inputs
set_output_delay -clock core_clock -max 1.000 [all_outputs]
set_output_delay -clock core_clock -min 0.100 [all_outputs]
set_input_transition 0.100 $inputs
# Four real inverter input loads, in the library's native capacitance units.
if {[info exists env(KWT_OUTPUT_CAP)]} {
  # PrimeTime represents lib-pin capacitance as an object in this release.
  # Reuse the exact scalar used by DC, unchanged across SS and FF analysis.
  set output_cap $env(KWT_OUTPUT_CAP)
  puts "CONSTRAINT_OUTPUT_LOAD frozen_from_DC=$output_cap"
} else {
  set inverter [index_collection [get_lib_cells */INV*] 0]
  if {[sizeof_collection $inverter]==0} {error "No inverter cell found for an explicit output load"}
  set inv_inputs [filter_collection [get_lib_pins -of_objects $inverter] "direction == in"]
  set load_pin [index_collection $inv_inputs 0]
  set output_cap [expr 4.0*[get_attribute $load_pin capacitance]]
  puts "CONSTRAINT_OUTPUT_LOAD pin=[get_object_name $load_pin] four_pin_cap=$output_cap"
}
set_load $output_cap [all_outputs]
