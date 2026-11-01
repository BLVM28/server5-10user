# Explicit 150 MHz exploration budget; no false/multicycle paths.
set_units -time ns -capacitance pF
create_clock -name core_clock -period 6.666667 [get_ports clk]
set_clock_uncertainty 0.100 [get_clocks core_clock]
set inputs [remove_from_collection [all_inputs] [get_ports clk]]
set_input_delay -clock core_clock -max 1.000 $inputs
set_input_delay -clock core_clock -min 0.100 $inputs
set_output_delay -clock core_clock -max 1.000 [all_outputs]
set_output_delay -clock core_clock -min 0.100 [all_outputs]
set_input_transition 0.100 $inputs
set_load 0.002852 [all_outputs]
