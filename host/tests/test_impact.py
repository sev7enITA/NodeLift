import copy
import http.client
import json
import threading
import unittest
from nodelift.impact import analyze, digest, energy, estimate, VERSION, SCOPE_KEYS
from nodelift.host import Server


def fixture(sessions=1, kind='physical'):
    scope = {k: digest(k) for k in SCOPE_KEYS}
    scope.update(candidate='remote_draft', warmup_policy='one pair')
    data = dict(schema_version=1, runner=VERSION, scope=scope, evidence_kind=kind, sessions=[])
    for s in range(sessions):
        plan = [dict(id=str(i), prompt_sha256=digest(str(i)), order='AB' if i%2 == 0 else 'BA', max_tokens=32) for i in range(3)]
        session = dict(id=str(s), plan=plan, plan_sha256=digest(plan), scope_sha256=digest(scope), attempts=[])
        for p in plan:
            for arm in ('host', 'candidate'):
                session['attempts'].append(dict(pair_id=p['id'], arm=arm, run_id=f'{s}/{p["id"]}/{arm}',
                    status='completed', scope_sha256=digest(scope), prompt_sha256=p['prompt_sha256'],
                    max_tokens=32, fallback=False, duration_ms=1000 if arm=='host' else 700,
                    ttft_ms=100 if arm=='host' else 80, token_count=32, tokens_sha256=digest([1,2]), finish_reason='length'))
        data['sessions'].append(session)
    return data


def meter(duration, watts=10):
    return dict(source='test-meter', scope='whole-system', components=['host','phone','router'],
                clock='run_relative_monotonic_ms', unit='W', max_gap_ms=2000,
                calibration_relative_uncertainty=.01, samples=[[0,watts],[duration,watts]])


class ImpactTests(unittest.TestCase):
    def test_direction_units_and_small_sample(self):
        r=analyze(fixture())
        self.assertEqual(r['time_saved_ms']['estimate'],300)
        self.assertEqual(r['time_saved_percent']['estimate'],30)
        self.assertEqual(r['ttft_change_ms']['estimate'],-20)
        self.assertIsNone(r['time_saved_ms']['ci95'])
        self.assertEqual(r['verdict'],'insufficient_evidence')
        self.assertFalse(r['qualified_recommendation'])

    def test_cluster_bootstrap_does_not_count_repetitions_as_sessions(self):
        r=estimate([('one',i) for i in range(100)])
        self.assertEqual(r['clusters'],1)
        self.assertIsNone(r['ci95'])
        data=fixture(10)
        r=analyze(data)
        self.assertEqual(r,analyze(data))
        self.assertEqual(r['verdict'],'insufficient_evidence')
        self.assertIsNone(r['time_saved_ms']['ci95'])
        self.assertTrue(r['time_saved_ms']['degenerate_interval'])
        self.assertFalse(r['qualified_recommendation'])

    def test_correlated_clusters_produce_interval_without_qualification(self):
        rows=[(str(s),float(s*100)) for s in range(10) for _ in range(10)]
        r=estimate(rows)
        self.assertIsNotNone(r['ci95'])
        self.assertGreater(r['ci95'][1]-r['ci95'][0],100)
        self.assertEqual(r,estimate(rows))

    def test_realized_order_and_clock_faults_excluded(self):
        d=fixture();a,b=d['sessions'][0]['attempts'][:2]
        a.update(start_monotonic_ns=2000000000,end_monotonic_ns=3000000000)
        b.update(start_monotonic_ns=1000000000,end_monotonic_ns=1700000000)
        r=analyze(d)
        self.assertEqual(r['counts']['eligible_pairs'],2)
        self.assertEqual(r['service_time_saved_ms']['n'],2)
        d=fixture();d['sessions'][0]['attempts'][1]['clock_discontinuity_ms']=2000
        self.assertEqual(analyze(d)['counts']['eligible_pairs'],2)

    def test_control_and_synthetic_never_promoted(self):
        for kind in ('synthetic','control'):
            self.assertEqual(analyze(fixture(10,kind))['verdict'],'control_only')

    def test_missing_failed_cancelled_fallback_all_retained(self):
        d=fixture(); a=d['sessions'][0]['attempts']; a.pop()
        a[1]['fallback']=True; a[2]['status']='failed'; a[3]['status']='cancelled'
        r=analyze(d)
        self.assertEqual(r['counts']['planned_pairs'],3)
        self.assertEqual(r['counts']['missing_runs'],1)
        self.assertEqual(r['reliability']['candidate']['planned'],3)
        self.assertEqual(r['reliability']['candidate']['fallback'],1)
        self.assertEqual(r['reliability']['candidate']['cancelled'],1)
        self.assertEqual(r['counts']['eligible_pairs'],0)

    def test_mismatch_cannot_be_hidden_as_clean_speedup(self):
        d=fixture(10);d['sessions'][0]['attempts'][1]['tokens_sha256']=digest('different')
        r=analyze(d)
        self.assertEqual(r['verdict'],'invalid_comparison')
        self.assertEqual(r['counts']['mismatched_pairs'],1)
        self.assertEqual(r['reliability']['candidate']['correct'],29)
        self.assertEqual(r['reliability']['host']['correct'],29)

    def test_scope_drift_excludes_but_retains_denominator(self):
        d=fixture();d['sessions'][0]['attempts'][1]['scope_sha256']='different'
        r=analyze(d)
        self.assertEqual(r['counts']['eligible_pairs'],2)
        self.assertEqual(r['reliability']['candidate']['planned'],3)

    def test_duplicate_sessions_runs_slots_and_plan_rejected(self):
        for change in ('session','run','slot','plan','legacy'):
            d=fixture()
            if change=='session':d['sessions'].append(copy.deepcopy(d['sessions'][0]))
            if change=='run':d['sessions'][0]['attempts'][1]['run_id']=d['sessions'][0]['attempts'][0]['run_id']
            if change=='slot':d['sessions'][0]['attempts'][1]=copy.deepcopy(d['sessions'][0]['attempts'][0])
            if change=='plan':d['sessions'][0]['plan'][0]['max_tokens']=12
            if change=='legacy':d['runner']='old'
            with self.subTest(change=change),self.assertRaises(ValueError):analyze(d)

    def test_invalid_and_nonfinite_timing_never_zero_or_gain(self):
        for value in (None,0,-1,float('nan'),float('inf'),True):
            d=fixture();d['sessions'][0]['attempts'][1]['duration_ms']=value
            r=analyze(d)
            self.assertEqual(r['counts']['eligible_pairs'],2)
            json.dumps(r,allow_nan=False)

    def test_energy_integral_clips_and_requires_full_coverage(self):
        e=meter(1000);self.assertEqual(energy(e,1000)[0]['joules'],10)
        e['samples']=[[-100,10],[500,20],[1100,30]]
        self.assertAlmostEqual(energy(e,1000)[0]['joules'],20)
        for mutate in ('unit','gap','coverage','negative','unordered'):
            e=meter(1000)
            if mutate=='unit':e['unit']='battery_percent'
            if mutate=='gap':e['max_gap_ms']=100
            if mutate=='coverage':e['samples'][-1][0]=999
            if mutate=='negative':e['samples'][0][1]=-1
            if mutate=='unordered':e['samples'].reverse()
            self.assertIsNone(energy(e,1000)[0])

    def test_energy_missing_partial_and_scope_mismatch(self):
        d=fixture();r=analyze(d);self.assertIsNone(r['energy_saved_joules'])
        for a in d['sessions'][0]['attempts']:a['energy']=meter(a['duration_ms'])
        r=analyze(d);self.assertEqual(r['energy_saved_joules']['estimate'],3)
        self.assertEqual(r['energy']['status'],'measured')
        d['sessions'][0]['attempts'][0]['energy']['components']=['host']
        r=analyze(d);self.assertEqual(r['energy']['status'],'partial')
        self.assertEqual(r['energy']['valid_pairs'],2)

    def test_regression_is_distinct_from_missing_evidence(self):
        d=fixture(10)
        for s in d['sessions']:
            for a in s['attempts']:
                if a['arm']=='candidate':a['duration_ms']=1300
        self.assertEqual(analyze(d)['verdict'],'insufficient_evidence')
        self.assertEqual(analyze(d)['gates']['execution_attestation'],'blocked')


class ImpactAPITests(unittest.TestCase):
    def test_analysis_requires_same_origin_admin_and_valid_schema(self):
        server=Server(('127.0.0.1',0),None,admin_token='test')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def request(token,origin,body):
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            try:
                c.request('POST','/admin/impact/analyze',json.dumps(body),{'Authorization':'Bearer '+token,'Origin':origin,'Content-Type':'application/json'})
                r=c.getresponse(); r.read();return r.status
            finally:c.close()
        origin='http://127.0.0.1:'+str(server.server_port)
        try:
            self.assertEqual(request('',origin,fixture()),401)
            self.assertEqual(request('test','https://example.org',fixture()),401)
            self.assertEqual(request('test',origin,{}),400)
            self.assertEqual(request('test',origin,fixture()),200)
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
