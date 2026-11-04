# Template only. SoC integration must preserve its real clock and I/O budget.
# The contest target is 150 MHz. No false or multicycle datapath exceptions.
create_clock -name kwt_clk -period 6.666667 [get_ports nice_clk]
# Do not invent input/output delays, clock uncertainty, SRAM corners or loads.
# Add the platform-approved budgets and analyze reset recovery/removal there.
# A local reset is unsupported while an ICB transaction is outstanding; reset
# the CPU/NICE/interconnect response domain together, or add a drain controller.
