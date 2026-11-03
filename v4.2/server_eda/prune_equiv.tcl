# Prove equivalence of the two complete, library-linked accelerator netlists.
set synopsys_auto_setup true
foreach library [concat [list $env(KWT_STD_DB)] [split $env(KWT_SRAM_DBS) |]] {
    read_db -technology_library $library
}
read_verilog -r $env(KWT_REFERENCE_NET)
set_top r:/WORK/kwt_nice_core
read_verilog -i $env(KWT_FINAL_NET)
set_top i:/WORK/kwt_nice_core
match
if {![verify]} {report_failing_points; error "Netlists differ"}
puts "FORMAL_EQUIVALENCE_PASS kwt_nice_core"
exit
