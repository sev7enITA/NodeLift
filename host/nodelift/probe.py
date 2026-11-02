"""Portable, local-only node inventory and explicitly requested LLM kernel probes.

No enrollment, network scan, driver install, elevated command or report upload.
Detected hardware is never promoted to executed-backend or acceleration evidence.
"""
import argparse
import copy
import threading
import csv
from datetime import datetime, timezone
import hashlib
import io
from importlib import metadata
import json
import math
import os
from pathlib import Path
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

SCHEMA = 'nodelift.node-probe.v1'
WINDOWS_QUERY = r'''
$ErrorActionPreference='Stop'
$c=Get-CimInstance Win32_ComputerSystem
$o=Get-CimInstance Win32_OperatingSystem
$p=@(Get-CimInstance Win32_Processor | Select-Object Name,Architecture,NumberOfCores,NumberOfLogicalProcessors)
$g=@(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,VideoProcessor)
$a=@(Get-CimInstance Win32_PnPEntity | Where-Object {$_.Name -match '(?i)\bNPU\b|Neural|AI Boost|Hexagon'} | Select-Object Name,Status)
@{manufacturer=$c.Manufacturer;model=$c.Model;ram_bytes=$c.TotalPhysicalMemory;available_kib=$o.FreePhysicalMemory;os_version=$o.Version;os_build=$o.BuildNumber;processors=$p;gpus=$g;npus=$a} | ConvertTo-Json -Depth 5 -Compress
'''


def positive(value):
    try:
        if isinstance(value, bool):
            return None
        number = float(value)
        return number if math.isfinite(number) and number > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def text(value):
    return str(value).replace('\x00', '').strip()[:160] if value is not None else None


def number(value, factor=1):
    value = positive(value)
    return int(value * factor) if value is not None else None


def run_command(argv, timeout=5, output_limit=2 * 1024 * 1024):
    # Temp files avoid unbounded pipe buffering; no raw stderr or local paths in exports.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            result = subprocess.run(argv, stdout=out, stderr=err, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'stdout': None}
        except OSError:
            return {'status': 'unavailable', 'stdout': None}
        out.seek(0, 2)
        if out.tell() > output_limit:
            return {'status': 'output_limit', 'stdout': None}
        out.seek(0)
        return {'status': 'ok' if result.returncode == 0 else 'failed',
                'stdout': out.read().decode('utf-8-sig', errors='replace') if result.returncode == 0 else None}


def architecture(raw):
    raw = str(raw or '').lower()
    return {'amd64': 'x86_64', 'x64': 'x86_64', 'aarch64': 'arm64',
            'arm64': 'arm64', 'x86_64': 'x86_64', 'i386': 'x86',
            'i686': 'x86', 'armv7l': 'arm32'}.get(raw, raw or 'unknown')


def windows_fields(data):
    cpus = data.get('processors') or []
    if isinstance(cpus, dict):
        cpus = [cpus]
    gpus = data.get('gpus') or []
    if isinstance(gpus, dict):
        gpus = [gpus]
    archs = {str(p.get('Architecture')) for p in cpus}
    native = {'12': 'arm64', '9': 'x86_64', '0': 'x86', '5': 'arm32'}.get(next(iter(archs))) if len(archs) == 1 else None
    npus = data.get('npus') or []
    if isinstance(npus, dict):
        npus = [npus]
    return {
        'model': text(data.get('model')), 'manufacturer': text(data.get('manufacturer')),
        'native_architecture': native,
        'cpu_name': ', '.join(filter(None, (text(p.get('Name')) for p in cpus))) or None,
        'physical_cores': sum(number(p.get('NumberOfCores')) or 0 for p in cpus) or None,
        'logical_cores': sum(number(p.get('NumberOfLogicalProcessors')) or 0 for p in cpus) or None,
        'ram_bytes': number(data.get('ram_bytes')),
        'available_ram_bytes': number(data.get('available_kib'), 1024),
        'os_version': text(data.get('os_version')), 'os_build': text(data.get('os_build')),
        'accelerators': [{'name': text(g.get('Name')), 'driver_version': text(g.get('DriverVersion')),
                          'kind': 'display_adapter', 'memory_bytes': None, 'memory_kind': 'unknown',
                          'source': 'Win32_VideoController', 'execution_verified': False} for g in gpus] +
                        [{'name': text(g.get('Name')), 'kind': 'npu_candidate', 'memory_bytes': None,
                          'memory_kind': 'unknown', 'driver_version': None, 'os_device_status': text(g.get('Status')),
                          'source': 'Win32_PnPEntity_name_match', 'execution_verified': False} for g in npus],
    }


def linux_fields(cpuinfo, meminfo, model=None):
    fields = {}
    for line in cpuinfo.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            fields.setdefault(key.strip(), value.strip())
    mem = {}
    for line in meminfo.splitlines():
        bits = line.split()
        if len(bits) >= 2 and bits[0] in ('MemTotal:', 'MemAvailable:'):
            mem[bits[0][:-1]] = number(bits[1], 1024)
    flags = (fields.get('flags') or fields.get('Features') or '').split()
    return {'cpu_name': text(fields.get('model name') or fields.get('Hardware') or model),
            'model': text(model), 'ram_bytes': mem.get('MemTotal'),
            'available_ram_bytes': mem.get('MemAvailable'),
            'cpu_features': sorted({f for f in flags if f.replace('_', '').isalnum()})[:256]}


def pci_accelerators(output):
    rows = []
    for line in output.splitlines():
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        if len(parts) < 4:
            continue
        cls = parts[1].lower()
        if not any(s in cls for s in ('vga', '3d controller', 'display controller', 'processing accelerator')):
            continue
        rows.append({'name': text(parts[2] + ' ' + parts[3]),
                     'kind': 'compute_accelerator' if 'processing' in cls else 'display_adapter',
                     'memory_bytes': None, 'memory_kind': 'unknown', 'source': 'lspci',
                     'driver_version': None, 'execution_verified': False})
    return rows


def nvidia_accelerators(output):
    rows = []
    for row in csv.reader(io.StringIO(output)):
        if len(row) != 4:
            continue
        name, total, free, driver = (v.strip() for v in row)
        total_bytes = number(total, 1024**2)
        free_bytes = number(free, 1024**2)
        # nvidia-smi can report 0 free memory. It is observed zero, not unknown.
        if free == '0':
            free_bytes = 0
        if total_bytes is not None and free_bytes is not None and free_bytes > total_bytes:
            free_bytes = None
        rows.append({'name': text(name), 'kind': 'gpu', 'memory_bytes': total_bytes,
                     'available_memory_bytes': free_bytes, 'memory_kind': 'device_reported',
                     'driver_version': text(driver), 'source': 'nvidia-smi', 'execution_verified': False})
    return rows


def collect_probe(runner=run_command):
    system = platform.system()
    report = {'schema': SCHEMA, 'observed_at': datetime.now(timezone.utc).isoformat(),
              'system': system, 'os_version': platform.release(),
              'process_architecture': architecture(platform.machine()),
              'native_architecture': None, 'cpu_name': None, 'physical_cores': None,
              'logical_cores': os.cpu_count(), 'cpu_features': [], 'model': None,
              'ram_bytes': None, 'available_ram_bytes': None, 'accelerators': [],
              'python_version': platform.python_version(), 'sources': [],
              'hardware_status': 'partial', 'runtime_execution': 'not_tested',
              'llm_speedup_qualified': False, 'energy': None, 'connection': None}

    def command(label, args):
        result = runner(args)
        report['sources'].append({'name': label, 'status': result['status']})
        return result.get('stdout') or ''

    def read(name):
        try:
            return Path(name).read_text(errors='replace')[:262144]
        except OSError:
            return ''

    if system == 'Windows':
        raw = command('windows_cim', ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', WINDOWS_QUERY])
        try:
            report.update(windows_fields(json.loads(raw)))
        except (ValueError, TypeError, AttributeError):
            report['sources'].append({'name': 'windows_cim_parse', 'status': 'failed'})
    elif system == 'Darwin':
        for key, dest in [('hw.model', 'model'), ('machdep.cpu.brand_string', 'cpu_name'),
                          ('hw.memsize', 'ram_bytes'), ('hw.physicalcpu', 'physical_cores')]:
            raw = command(key, ['/usr/sbin/sysctl', '-n', key]).strip()
            report[dest] = number(raw) if dest.endswith('bytes') or dest.endswith('cores') else text(raw) or None
        arm = command('hw.optional.arm64', ['/usr/sbin/sysctl', '-n', 'hw.optional.arm64']).strip()
        report['native_architecture'] = 'arm64' if arm == '1' else report['process_architecture']
        raw = command('display_inventory', ['/usr/sbin/system_profiler', 'SPDisplaysDataType', '-json'])
        try:
            for gpu in json.loads(raw).get('SPDisplaysDataType', []):
                report['accelerators'].append({'name': text(gpu.get('sppci_model') or gpu.get('_name')),
                    'kind': 'gpu', 'memory_bytes': None,
                    'memory_kind': 'shared_system' if arm == '1' else 'unknown',
                    'driver_version': None, 'source': 'system_profiler', 'execution_verified': False})
        except (ValueError, TypeError, AttributeError):
            report['sources'].append({'name': 'display_parse', 'status': 'failed'})
    elif system == 'Linux':
        cpu, mem = read('/proc/cpuinfo'), read('/proc/meminfo')
        report.update(linux_fields(cpu, mem, read('/sys/firmware/devicetree/base/model') or None))
        report['native_architecture'] = report['process_architecture']
        report['sources'].append({'name': 'proc_inventory', 'status': 'ok' if cpu and mem else 'partial'})
        report['accelerators'] = pci_accelerators(command('pci_accelerators', ['lspci', '-mm']))
    if system in ('Windows', 'Linux'):
        raw = command('nvidia_smi', ['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version', '--format=csv,noheader,nounits'])
        nvidia = nvidia_accelerators(raw)
        if nvidia:
            report['accelerators'] = [g for g in report['accelerators'] if 'nvidia' not in (g['name'] or '').lower()] + nvidia
    report['tools'] = {name: {'found': shutil.which(name) is not None, 'execution_verified': False}
                       for name in ('llama-bench', 'nvidia-smi', 'vulkaninfo', 'rocminfo', 'sycl-ls')}
    report['python_packages'] = {}
    for package in ('mlx', 'mlx-lm', 'llama-cpp-python', 'onnxruntime', 'onnxruntime-qnn'):
        try:
            version = metadata.version(package)
        except metadata.PackageNotFoundError:
            version = None
        report['python_packages'][package] = {'version': version, 'execution_verified': False}
    report['limitations'] = ['Inventory does not attest backend execution, allocatable memory or LLM speed.',
                            'Accelerator enumeration may be incomplete, especially non-PCI SoCs. Absence is not proof of no accelerator.',
                            'NPU support must be tested with a compatible runtime; chip branding is insufficient.',
                            'No network benchmark, thermal endurance, power measurement or remote enrollment performed.']
    report['hardware_status'] = 'observed' if report['cpu_name'] and report['ram_bytes'] and report['native_architecture'] else 'partial'
    report['assessment'] = {'state': 'needs_model_benchmark', 'eligible_roles': [],
                            'next_step': 'Run an explicit local model benchmark, then a matched connection-specific impact session.'}
    # Dynamic available memory and timestamps are deliberately outside static identity.
    identity = {k: report[k] for k in ('system', 'os_version', 'native_architecture', 'process_architecture', 'cpu_name', 'ram_bytes')}
    identity['accelerators'] = [{k: g.get(k) for k in ('name', 'memory_bytes', 'memory_kind', 'driver_version')} for g in report['accelerators']]
    report['configuration_sha256'] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return report


_cache_lock = threading.Lock()
_cache_value = None
_cache_at = 0.0


def cached_inventory():
    global _cache_value, _cache_at
    with _cache_lock:
        if _cache_value is None or time.monotonic() - _cache_at >= 60:
            _cache_value = collect_probe()
            _cache_at = time.monotonic()
        return {**copy.deepcopy(_cache_value), 'cache_age_seconds': time.monotonic() - _cache_at}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def summarize_bench(rows, prompt_tokens, generated_tokens, repetitions):
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError('expected separate prefill and decode records')
    output = {}
    for kind, expected in [('prefill', (prompt_tokens, 0)), ('decode', (0, generated_tokens))]:
        matches = [r for r in rows if isinstance(r, dict) and (r.get('n_prompt'), r.get('n_gen')) == expected]
        if len(matches) != 1:
            raise ValueError('benchmark workload does not match request')
        row = matches[0]
        samples = row.get('samples_ns')
        if not isinstance(samples, list) or len(samples) != repetitions or any(positive(v) is None for v in samples):
            raise ValueError('missing or invalid repetition timings')
        tokens = sum(expected)
        rates = [tokens * 1e9 / v for v in samples]
        output[kind] = {'tokens': tokens, 'samples_ns': samples,
                        'tokens_per_second_median': statistics.median(rates),
                        'tokens_per_second_min': min(rates), 'tokens_per_second_max': max(rates),
                        'build_commit': text(row.get('build_commit')), 'backends': text(row.get('backends')),
                        'gpu_layers_requested': row.get('n_gpu_layers'),
                        'n_threads': row.get('n_threads'), 'model_type': text(row.get('model_type'))}
    return output


def benchmark(executable, model, prompt_tokens=128, generated_tokens=32, repetitions=3,
              threads=4, gpu_layers=0, timeout=120, runner=run_command):
    limits = [(prompt_tokens, 1, 4096), (generated_tokens, 1, 512), (repetitions, 1, 10),
              (threads, 1, 256), (gpu_layers, 0, 999), (timeout, 1, 1800)]
    if any(type(v) is not int or not low <= v <= high for v, low, high in limits):
        raise ValueError('benchmark option outside bounded range')
    executable, model = Path(executable).resolve(strict=True), Path(model).resolve(strict=True)
    if not executable.is_file() or not model.is_file():
        raise ValueError('explicit executable and model files required')
    config = dict(prompt_tokens=prompt_tokens, generated_tokens=generated_tokens, repetitions=repetitions,
                  threads=threads, gpu_layers_requested=gpu_layers)
    report = {'schema': 'nodelift.node-benchmark.v1', 'kind': 'llama_bench_kernels',
              'observed_at': datetime.now(timezone.utc).isoformat(),
              'model_sha256': sha256_file(model), 'executable_sha256': sha256_file(executable),
              'node_profile': collect_probe(),
              'configuration': config, 'status': 'pending', 'metrics': None,
              'ttft_ms': None, 'energy_joules': None, 'connection': None,
              'accelerator_allocation_verified': False, 'llm_speedup_qualified': False,
              'limitations': ['Kernel timings exclude loading, request queue, client streaming and network.',
                              'Separate decode test is not generation after the prefill test context.',
                              'No output-equivalence or distributed acceleration conclusion.',
                              'Executable hash does not include every dynamic driver/runtime dependency.']}
    args = [str(executable), '-m', str(model), '-p', str(prompt_tokens), '-n', str(generated_tokens),
            '-r', str(repetitions), '-t', str(threads), '-ngl', str(gpu_layers), '-o', 'json']
    start = time.monotonic()
    result = runner(args, timeout=timeout)
    report['process_wall_ms'] = (time.monotonic() - start) * 1000
    report['status'] = result['status']
    if result['status'] == 'ok':
        try:
            rows = json.loads(result['stdout'])
            report['metrics'] = summarize_bench(rows, prompt_tokens, generated_tokens, repetitions)
            if any(v['n_threads'] != threads or v['gpu_layers_requested'] != gpu_layers for v in report['metrics'].values()):
                raise ValueError('backend did not report the requested execution configuration')
            report['status'] = 'completed'
        except (ValueError, TypeError, KeyError, OverflowError):
            report['status'] = 'invalid_result'
            report['metrics'] = None
    # Detect an artifact changing during the probe instead of trusting a stale scope.
    try:
        changed = sha256_file(model) != report['model_sha256'] or sha256_file(executable) != report['executable_sha256']
    except OSError:
        changed = True
    if changed:
        report['status'] = 'artifact_changed'
        report['metrics'] = None
    return report


def compare(baseline, candidate):
    for record in (baseline, candidate):
        if record.get('schema') != 'nodelift.node-benchmark.v1' or record.get('status') != 'completed':
            raise ValueError('two completed node benchmark reports required')
    if baseline['model_sha256'] != candidate['model_sha256']:
        raise ValueError('different model artifacts cannot establish same-model potential')
    for field in ('prompt_tokens', 'generated_tokens', 'threads', 'repetitions'):
        if baseline['configuration'][field] != candidate['configuration'][field]:
            raise ValueError('benchmark configuration mismatch: ' + field)
    ratios = {}
    for kind in ('prefill', 'decode'):
        b = positive(baseline['metrics'][kind]['tokens_per_second_median'])
        c = positive(candidate['metrics'][kind]['tokens_per_second_median'])
        if b is None or c is None:
            raise ValueError('positive finite rates required')
        ratios[kind + '_rate_ratio'] = c / b
    return {'schema': 'nodelift.node-potential.v1', 'kernel_ratios': ratios,
            'same_executable': baseline['executable_sha256'] == candidate['executable_sha256'],
            'baseline_configuration': baseline['configuration'], 'candidate_configuration': candidate['configuration'],
            'classification': 'requires_paired_end_to_end_assessment',
            'distributed_speedup': None, 'qualified_recommendation': False,
            'reason': 'Standalone kernel comparison only; link, acceptance, verification, TTFT, reliability, energy and uncertainty are not measured here.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    inventory = sub.add_parser('inventory')
    inventory.add_argument('--output', type=Path, required=True)
    bench = sub.add_parser('benchmark')
    bench.add_argument('--executable', type=Path, required=True)
    bench.add_argument('--model', type=Path, required=True)
    bench.add_argument('--output', type=Path, required=True)
    for flag, default in [('prompt-tokens', 128), ('generated-tokens', 32), ('repetitions', 3), ('threads', 4), ('gpu-layers', 0), ('timeout', 120)]:
        bench.add_argument('--'+flag, type=int, default=default)
    comparison = sub.add_parser('compare')
    comparison.add_argument('--baseline', type=Path, required=True)
    comparison.add_argument('--candidate', type=Path, required=True)
    comparison.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('output exists; choose a new path to retain previous evidence')
    try:
        if args.action == 'inventory':
            result = collect_probe()
        elif args.action == 'benchmark':
            result = benchmark(args.executable, args.model, args.prompt_tokens, args.generated_tokens,
                               args.repetitions, args.threads, args.gpu_layers, args.timeout)
        else:
            result = compare(json.loads(args.baseline.read_text()), json.loads(args.candidate.read_text()))
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    except (OSError, ValueError, TypeError, KeyError):
        parser.exit(2, 'Probe input/output failed. Check files and report schema; no automatic upload occurred.\n')
    print(json.dumps({'written': True, 'schema': result['schema'], 'status': result.get('status', 'recorded')}))
    return 0 if result.get('status') in (None, 'completed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
