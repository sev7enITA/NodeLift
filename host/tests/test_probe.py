import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nodelift.probe import (architecture, windows_fields, linux_fields, pci_accelerators,
                            nvidia_accelerators, collect_probe, summarize_bench, benchmark, compare)

class ProbeTests(unittest.TestCase):
    def rows(self):
        return [{'n_prompt':128,'n_gen':0,'n_threads':4,'n_gpu_layers':0,'samples_ns':[100000000,110000000,120000000]},
                {'n_prompt':0,'n_gen':32,'n_threads':4,'n_gpu_layers':0,'samples_ns':[1000000000,1100000000,1200000000]}]

    def test_windows_arm_and_no_serial_or_fake_vram(self):
        raw = {'model':'Fixture ARM computer','ram_bytes':32*1024**3,'available_kib':1234,
               'processors':[{'Name':'Snapdragon fixture','Architecture':12,'NumberOfCores':12}],
               'gpus':[{'Name':'Adreno fixture','AdapterRAM':4294967295,'SerialNumber':'secret'}],
               'npus':[{'Name':'Hexagon fixture','Status':'OK','DeviceID':'secret'}], 'UserName':'secret'}
        report = windows_fields(raw)
        self.assertEqual(report['native_architecture'], 'arm64')
        self.assertIsNone(report['accelerators'][0]['memory_bytes'])
        self.assertEqual(report['accelerators'][1]['kind'], 'npu_candidate')
        self.assertNotIn('secret', json.dumps(report))
        self.assertFalse(report['accelerators'][1]['execution_verified'])

    def test_linux_arm_fields_drop_identity(self):
        report = linux_fields('Hardware : Kirin fixture\nFeatures : asimd aes\nSerial : private',
                              'MemTotal: 1024 kB\nMemAvailable: 512 kB')
        self.assertEqual(report['ram_bytes'], 1024**2)
        self.assertEqual(report['cpu_name'], 'Kirin fixture')
        self.assertNotIn('private', json.dumps(report))

    def test_architecture_aliases(self):
        self.assertEqual(architecture('AMD64'), 'x86_64')
        self.assertEqual(architecture('aarch64'), 'arm64')
        self.assertEqual(architecture(None), 'unknown')

    def test_missing_linux_memory_not_zero(self):
        self.assertIsNone(linux_fields('', '')['ram_bytes'])

    def test_nvidia_zero_free_and_invalid_values(self):
        rows = nvidia_accelerators('GPU fixture, 24576, 0, 1.0\nGPU other, N/A, NaN, 2.0')
        self.assertEqual(rows[0]['memory_bytes'], 24576*1024**2)
        self.assertEqual(rows[0]['available_memory_bytes'], 0)
        self.assertIsNone(rows[1]['memory_bytes'])
        self.assertIsNone(rows[1]['available_memory_bytes'])

    def test_pci_ignores_network_identity(self):
        rows = pci_accelerators('00:01 "Ethernet controller" "vendor" "network"\n00:02 "Display controller" "vendor" "GPU"')
        self.assertEqual(len(rows), 1)
        self.assertNotIn('00:02', json.dumps(rows))

    def test_macos_unified_memory_not_counted_as_vram(self):
        def runner(args):
            key = args[-1]
            values = {'hw.optional.arm64':'1','hw.memsize':'68719476736',
                      '-json':json.dumps({'SPDisplaysDataType':[{'sppci_model':'Apple fixture','serial':'secret'}]})}
            return {'status':'ok','stdout':values.get(key, '')}
        with patch('nodelift.probe.platform.system',return_value='Darwin'):
            result = collect_probe(runner)
        self.assertEqual(result['accelerators'][0]['memory_kind'], 'shared_system')
        self.assertIsNone(result['accelerators'][0]['memory_bytes'])
        self.assertFalse(result['llm_speedup_qualified'])
        self.assertNotIn('secret', json.dumps(result))

    def test_unavailable_commands_keep_inventory_partial(self):
        with patch('nodelift.probe.platform.system',return_value='Windows'):
            result = collect_probe(lambda _: {'status':'unavailable','stdout':None})
        self.assertIsNone(result['ram_bytes'])
        self.assertEqual(result['assessment']['eligible_roles'], [])

    def test_workload_and_sample_validation(self):
        value = summarize_bench(self.rows(),128,32,3)
        self.assertAlmostEqual(value['decode']['tokens_per_second_median'],32/1.1)
        for value in (0, -1, float('nan'), float('inf'), True):
            rows = self.rows();rows[1]['samples_ns'][0]=value
            with self.assertRaises(ValueError):summarize_bench(rows,128,32,3)
        with self.assertRaises(ValueError):summarize_bench(self.rows(),256,32,3)
        with self.assertRaises(ValueError):summarize_bench(self.rows(),128,32,2)

    def test_timeout_retained_without_paths_or_acceleration(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'private-exe';exe.write_bytes(b'fixture')
            model=Path(d)/'private-model';model.write_bytes(b'fixture')
            r=benchmark(exe,model,runner=lambda *a,**k:{'status':'timeout','stdout':None})
            self.assertEqual(r['status'],'timeout')
            self.assertIsNone(r['metrics'])
            self.assertNotIn(d,json.dumps(r))
            self.assertFalse(r['llm_speedup_qualified'])

    def test_artifact_change_invalidates_completed_result(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'exe';exe.write_bytes(b'exe')
            model=Path(d)/'model';model.write_bytes(b'before')
            def runner(*a,**k):
                model.write_bytes(b'after')
                return {'status':'ok','stdout':json.dumps(self.rows())}
            r=benchmark(exe,model,runner=runner)
            self.assertEqual(r['status'],'artifact_changed')
            self.assertIsNone(r['metrics'])

    def test_compare_rejects_scope_mismatch_and_does_not_claim_network_win(self):
        baseline={'schema':'nodelift.node-benchmark.v1','status':'completed','model_sha256':'a',
                  'executable_sha256':'b','configuration':dict(prompt_tokens=128,generated_tokens=32,threads=4,repetitions=3),
                  'metrics':summarize_bench(self.rows(),128,32,3)}
        candidate=copy.deepcopy(baseline)
        self.assertFalse(compare(baseline,candidate)['qualified_recommendation'])
        candidate['model_sha256']='other'
        with self.assertRaises(ValueError):compare(baseline,candidate)
        candidate=copy.deepcopy(baseline);candidate['configuration']['threads']=8
        with self.assertRaises(ValueError):compare(baseline,candidate)

if __name__ == '__main__':unittest.main()
