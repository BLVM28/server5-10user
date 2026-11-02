"""Run the existing adversarial NICE/ICB system TB on every exported suite.

Every run retains the unchanged TB checks, including full 40-bit accumulators,
16-bit writeback, guards, saturation, handshake backpressure, errors and reset.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--tag', default='real_speech_20261102')
    a = p.parse_args()
    assert 1 <= a.jobs <= 3
    a.capture = a.capture.resolve()
    capture = json.loads((a.capture / 'report.json').read_text())
    assert capture['precision_pass'] and capture['all_individual_cases_pass']
    logs = a.capture / 'logs'
    logs.mkdir(exist_ok=True)
    # Refuse to compare captures from another RTL revision silently.
    for path, expected in capture['source_sha256'].items():
        if path.startswith('v2/rtl/'):
            assert hashlib.sha256((ROOT.parent / path).read_bytes()).hexdigest() == expected

    def run(suite):
        name = suite['name']
        assert re.fullmatch(r'(class_[0-9]{2}|worst)', name)
        tag = a.tag + '_' + name
        command = [sys.executable, str(ROOT / 'py/run_xsim.py'), '--tops', 'tb_kwt_system',
                   '--tag', tag, '--vectors', str(a.capture / 'rtl' / name)]
        start = time.monotonic()
        result = subprocess.run(command, cwd=str(ROOT.parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1200)
        (logs / (name + '_driver.log')).write_bytes(result.stdout)
        if result.returncode:
            raise RuntimeError(name + ' failed: ' + result.stdout.decode('utf-8', errors='replace')[-4000:])
        build = ROOT / 'build' / tag
        evidence = json.loads((build / 'results.json').read_text())
        tb_log = (build / 'tb_kwt_system.log').read_text(encoding='utf-8', errors='replace')
        assert 'ALL PASS, 29/29' in tb_log
        matrices = re.findall(r'matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+)', tb_log)
        assert len(matrices) == 14 and all(int(m[2]) == 12672 for m in matrices)
        for path in build.glob('*.log'):
            (logs / (name + '_' + path.name)).write_bytes(path.read_bytes())
        (logs / (name + '_results.json')).write_text(json.dumps(evidence, indent=2) + '\n')
        # Generated TB is the original except for the default vector directory;
        # preserve it beside logs for independent inspection.
        (logs / (name + '_tb_kwt_system.sv')).write_bytes((build / 'tb_kwt_system.sv').read_bytes())
        print('%s ALL PASS, 29/29; 14 full matrices; %.1fs' % (name, time.monotonic() - start), flush=True)
        return dict(suite=name, tests=29, full_matrices=14, matrix_results=matrices,
                    elapsed_seconds=time.monotonic() - start, source_sha256=evidence['source_sha256'])

    started = time.monotonic()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures = {pool.submit(run, suite): suite['name'] for suite in capture['rtl_suites']}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r['suite'])
    tests = sum(r['tests'] for r in results)
    matrices = sum(r['full_matrices'] for r in results)
    report = dict(tool='Vivado XSim 2023.2', scope='v2 NICE/ICB behavioral-memory BFM; not E203 CPU or STA',
                  suites=results, tests_passed=tests, full_matrix_executions=matrices,
                  output_int16_elements_checked=matrices * 99 * 256,
                  accumulator_int40_elements_checked=matrices * 99 * 256,
                  elapsed_seconds=time.monotonic() - started)
    (a.capture / 'rtl_results.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ALL PASS, %d/%d scenarios; %d full matrix executions' % (tests, tests, matrices), flush=True)


if __name__ == '__main__':
    main()
