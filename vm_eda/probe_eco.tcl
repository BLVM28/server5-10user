puts KWT_ECO_PROBE_BEGIN
foreach cmd {eco_add_repeater eco_change_cell write_verilog report_units set_delay_cal_mode set_analysis_mode} {
 catch {help $cmd}
}
puts KWT_ECO_PROBE_END
exit
