# Run from v4.3/build/structure. FPGA synthesis is a structural check, NOT ASIC PPA.
set root [file normalize ../..]
set f [open [file join $root rtl.f] r]
set sources [split [string trim [read $f]] "\n"]
close $f
foreach s $sources {
  read_verilog -sv [file join $root [string trim $s]]
}
set_property verilog_define {KWT_USE_FOUNDRY_SRAM} [current_fileset]
read_verilog -sv [file join $root integration sram_blackboxes.sv]
# Test-only legal region; defaults would intentionally reject every task.
synth_design -top kwt_nice_core -part xc7a35tcpg236-1 -flatten_hierarchy none -mode out_of_context -generic {MEM_BASE=268435456 MEM_BYTES=524288}
report_utilization -file utilization.txt
set s1024 [get_cells -hier -filter {REF_NAME == RAMSP1024X16}]
set s128 [get_cells -hier -filter {REF_NAME == RAMSP128X16}]
set latches [get_cells -hier -filter {REF_NAME =~ LD*}]
if {[llength $s1024]!=8 || [llength $s128]!=64 || [llength $latches]!=0} {
  error "Unexpected memory count or inferred latch"
}
write_checkpoint -force structure.dcp
puts "ALL PASS, 3/3 structure checks: SP1024=8 SP128=64 latches=0; NOT ASIC timing/area"
exit
