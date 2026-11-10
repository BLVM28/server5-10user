import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home().resolve()
PROJECT = HOME / 'soc_20261107'
P6 = PROJECT / 'candidate_astra_p6'
P6_RUN = PROJECT / 'astra_runs/astra_p6r1_20261108_180156_138277'
P6_DECK = HOME / 'Desktop/astra_p6_dc_r1/dc_synth.tcl'
P6_DECK_SHA = 'b182e38f151200dfe73acafe31280e85ed25bea6ebf6e5a24d88e1ba3abf151b'
DC = '/eda/synopsys/dc/dc_2022.03-SP5-5/bin/dc_shell'
PASS = 'SOC_EXECUTION_ALL_PASS tasks=12 checked_words=58547 boots=2'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path, expected):
    resolved = path.resolve(strict=True)
    if HOME not in resolved.parents and Path('/storage1/admin_public_dir') not in resolved.parents:
        raise RuntimeError('Input is outside the allowed server directories: ' + str(path))
    if digest(resolved) != expected:
        raise RuntimeError('Input changed: ' + str(path))


def make_deck(deck):
    # Keep the verified P6 library, RC and SDC settings. Replace its
    # source selection with the just-verified simulation source list.
    begin = deck.index('set SOURCES {}')
    end = deck.index('set manifest [open reports/input_sha256.txt w]', begin)
    deck = deck[:begin] + r'''set source_file [open $env(KWT_TIMING_SOURCES) r]
set SOURCES [split [string trim [read $source_file]] \n]
close $source_file
foreach source_path $SOURCES {lappend INC_PATH [file dirname $source_path]}
set INPUTS [lsort -unique [concat $SOURCES $LIBRARIES $PHYSICAL_FILES [list $SCRIPT $env(KWT_TIMING_CHECKS)]]]
''' + deck[end:]
    deck = deck.replace('set VERSION astra_p6r1', 'set VERSION kwt43_timing_r8')
    deck = deck.replace('set OUT $PROJECT/astra_runs/', 'set OUT $env(KWT_TIMING_WORK)/')
    deck = deck.replace('6.666666667 30517.578125', '6.25 30517.578125')
    deck = deck.replace('set_host_options -max_cores 1', 'set_host_options -max_cores 4')
    begin = deck.index('write -format ddc -hierarchy -output netlist/soc_initial_mapping.ddc')
    end = deck.index('change_names -rules verilog -hierarchy', begin)
    # The optimizer can size/buffer the mapping in memory. Restore the
    # original timing and transition budgets before reporting acceptance.
    deck = deck[:begin] + '''redirect -file reports/initial_mapping_violations.rpt {report_constraint -all_violators}
compile_ultra -incremental -only_design_rule -no_autoungroup
require_native_success "Incremental electrical optimization"
set_clock_uncertainty -setup $SETUP_UNCERTAINTY_NS [all_clocks]
set_clock_uncertainty -hold $HOLD_UNCERTAINTY_NS [all_clocks]
set_max_transition $MAX_TRANSITION [current_design]
''' + deck[end:]
    deck = deck.replace('set_fix_hold [all_clocks]\n', '''# Give accelerator register paths their own optimization objective.
set register_clocks [all_registers -clock_pins]
set kwt_register_clocks [filter_collection $register_clocks {full_name =~ */u_kwt/*}]
set kwt_register_data [filter_collection [all_registers -data_pins] {full_name =~ */u_kwt/*}]
if {[sizeof_collection $kwt_register_clocks] == 0 || [sizeof_collection $kwt_register_data] == 0} {
    error "Accelerator register path group is empty"
}
group_path -name KWT_LOGIC -from $kwt_register_clocks -to $kwt_register_data -weight 8 -critical_range 0.800
set platform_register_clocks [remove_from_collection $register_clocks $kwt_register_clocks]
group_path -name KWT_INPUT -from $platform_register_clocks -to $kwt_register_data -weight 8 -critical_range 0.500
set platform_register_data [remove_from_collection [all_registers -data_pins] $kwt_register_data]
group_path -name KWT_OUTPUT -from $kwt_register_clocks -to $platform_register_data -weight 8 -critical_range 0.500
# Preserve the explicit macro input drivers and verify their pins in every PVT.
foreach library $STD_CORNERS {
    set name [file rootname [file tail $library]]
    foreach driver {BUFV4_12TH40 BUFV16_12TH40} {
        foreach pin {I Z} {
            if {[sizeof_collection [get_lib_pins $name/$driver/$pin]] != 1} {
                error "Missing driver pin $name/$driver/$pin"
            }
        }
    }
}
set sram_input_drivers [get_cells -hierarchical -filter {full_name =~ */u_kwt/* && (full_name =~ *drive_addr* || full_name =~ *drive_data*) && (ref_name == BUFV4_12TH40 || ref_name == BUFV16_12TH40)}]
set cross_sign_drivers [get_cells -hierarchical -filter {full_name =~ */u_kwt/* && full_name =~ *cross_sign_driver && ref_name == BUFV4_12TH40}]
if {[sizeof_collection $sram_input_drivers] != 1680 || [sizeof_collection $cross_sign_drivers] != 128} {
    error "Explicit driver counts differ from the 72 SRAMs and 128 MAC lanes"
}
set_dont_touch [add_to_collection $sram_input_drivers $cross_sign_drivers] true
# Margin applies only to mapping. Acceptance uses the original P6 values.
set_clock_uncertainty -setup [expr {$SETUP_UNCERTAINTY_NS + 0.250}] [all_clocks]
set_clock_uncertainty -hold [expr {$HOLD_UNCERTAINTY_NS + 0.100}] [all_clocks]
set_max_transition 0.650 [current_design]
set_fix_hold [all_clocks]
''')
    # Reuse the in-memory mapping if physical extraction reveals a small
    # residual. Each attempt finishes under the original acceptance limits.
    marker = 'extract_rc -estimate\nset_app_var write_sdc_output_lumped_net_capacitance false'
    if deck.count(marker) != 1:
        raise RuntimeError('Cannot locate the final extraction stage')
    deck = deck.replace(marker, '''extract_rc -estimate
set kwt_define_procs_only 1
source $env(KWT_TIMING_CHECKS)
unset kwt_define_procs_only
set drc_log [open reports/driver_repair.tsv w]
puts $drc_log "case\\tscope\\trule\\trecords"
foreach limit {0.600 0.550} {
    set detail reports/before_repair_${limit}.rpt
    redirect -file $detail {report_constraint -all_violators}
    set counts [electrical_row repair/$limit $detail $drc_log]
    set remaining 0
    dict for {rule count} [dict get $counts kwt] {incr remaining $count}
    if {$remaining == 0} {break}
    set_max_transition $limit [current_design]
    set_clock_uncertainty -setup [expr {$SETUP_UNCERTAINTY_NS + 0.250}] [all_clocks]
    set_clock_uncertainty -hold [expr {$HOLD_UNCERTAINTY_NS + 0.100}] [all_clocks]
    compile_ultra -incremental -only_design_rule -no_autoungroup
    require_native_success "Repair remaining electrical violations at $limit ns"
    set_max_transition $MAX_TRANSITION [current_design]
    set_clock_uncertainty -setup $SETUP_UNCERTAINTY_NS [all_clocks]
    set_clock_uncertainty -hold $HOLD_UNCERTAINTY_NS [all_clocks]
    extract_rc -estimate
}
close $drc_log
set_app_var write_sdc_output_lumped_net_capacitance false''')
    deck = deck.replace('check_mapped_timing reports/check_timing.rpt\n', '''set timing_coverage_ok [expr {![catch {check_mapped_timing reports/check_timing.rpt} timing_coverage_result]}]
if {!$timing_coverage_ok} {puts "KWT_COVERAGE_FAILED $timing_coverage_result"}
''')
    deck = re.sub(r'(?m)^(?:set_svf|write_sdf|write_parasitics) .+\n', '', deck)
    deck = re.sub(r'(?m)^write -format (?:ddc|verilog) .+\n', '', deck)
    return deck[:deck.index('# 同一最终网表、同一布局')] + 'source $env(KWT_TIMING_CHECKS)\nexit\n'


def main():
    if HOME not in ROOT.parents:
        raise RuntimeError('Place this project inside the server work directory')
    verify(P6_DECK, P6_DECK_SHA)
    stamp = time.strftime('%Y%m%d_%H%M%S') + '_' + str(os.getpid())
    run = ROOT / 'work' / stamp
    scratch = run / 'scratch'
    scratch.mkdir(parents=True)
    env = dict(os.environ, TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))

    dut = {Path(name).name: ROOT / name for name in (ROOT / 'rtl.f').read_text().splitlines() if name}
    p6_sim = P6 / 'verification/tb_soc_boot'
    sim_hashes = json.loads((p6_sim / 'source_manifest.json').read_text())
    cmd = json.loads((p6_sim / 'command.json').read_text())
    saved_hashes = dict((name, value) for value, name in (line.split(None, 1) for line in
                        (P6_RUN / 'reports/input_sha256.txt').read_text().splitlines()))
    verified_inputs = json.loads((P6 / 'verified_inputs.json').read_text())
    vec = HOME / 'v4.3/vec/streams/worst'
    firmware = P6 / 'firmware/firmware.hex'
    verify(firmware, verified_inputs[str(firmware)])
    for name, expected in json.loads((P6 / 'verified_vectors.json').read_text()).items():
        verify(Path(name), expected)

    active = {}
    for name, value in sim_hashes.items():
        old = Path(name)
        path = dut.get(old.name, old)
        verify(path, digest(path) if old.name in dut else value)
        active[name] = str(path)
    p6_sources = (P6_RUN / 'reports/simulation_checked_sources.txt').read_text().splitlines()
    if set(dut) != {Path(name).name for name in p6_sources if Path(name).name in dut}:
        raise RuntimeError('P6 accelerator source selection differs from rtl.f')
    for name in p6_sources:
        if name not in active or sim_hashes[name] != saved_hashes[name]:
            raise RuntimeError('P6 simulation and DC sources differ: ' + name)
    sources = run / 'sources.txt'
    sources.write_text('\n'.join(active[name] for name in p6_sources) + '\n')
    inputs = {str(path): digest(path) for path in map(Path, active.values())}
    (run / 'source_sha256.json').write_text(json.dumps(inputs, indent=2) + '\n')

    command = [active.get(arg, arg) for arg in cmd]
    if command[-2:] != ['-o', 'simv']:
        raise RuntimeError('Unexpected P6 compile command')
    print('RTL_SIM_START', run, flush=True)
    with (run / 'compile.log').open('w') as log:
        subprocess.run(command, cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (run / 'simulation.log').open('w') as log:
        subprocess.run([str(run / 'simv'), '+FIRMWARE=' + str(firmware), '+VEC_DIR=' + str(vec)],
                       cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = (run / 'simulation.log').read_text(errors='replace')
    if (PASS not in result or result.count('SOC_MATRIX_PASS') != 12 or
            re.search(r'(?im)^\s*(fatal|error)[:\[]', result)):
        raise RuntimeError('P6 platform functional regression failed: ' + str(run))
    for name, value in inputs.items():
        verify(Path(name), value)
    print(PASS, flush=True)
    for line in result.splitlines():
        if line.startswith('SOC_PERFORMANCE_TOTAL '):
            print(line, flush=True)

    deck = run / 'dc.tcl'
    deck.write_text(make_deck(P6_DECK.read_text(encoding='utf-8')), encoding='utf-8')
    env.update(KWT_TIMING_WORK=str(run), KWT_TIMING_SOURCES=str(sources),
               KWT_TIMING_CHECKS=str(ROOT / 'flow/measure.tcl'), SOC_MODE='synth', SOC_CHECK_ONLY='0')
    print('STA_START', run / 'dc.log', flush=True)
    with (run / 'dc.log').open('w') as log:
        subprocess.run([DC, '-topographical_mode', '-f', str(deck)], cwd=run, env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    results = list(run.glob('kwt43_timing_*/reports/acceptance.txt'))
    if len(results) != 1:
        raise RuntimeError('DC did not complete the planned timing checks: ' + str(run))
    report = results[0].read_text()
    print(report, end='', flush=True)
    if 'SOC_160_PASS=1' not in report.splitlines():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
