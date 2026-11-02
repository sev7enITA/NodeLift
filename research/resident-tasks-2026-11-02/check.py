"""Check the pilot's source-selection and scoring contract without inference."""
import json
from probe import FIXTURES, encoded, payload, score

checks = 0
for fixture in FIXTURES:
    assert score(json.dumps(fixture['expected']), fixture['expected'])['correct']
    checks += 1
    assert fixture['source'] in payload(fixture, 'segment')['sources']
    checks += 1
    assert fixture['source'] in payload(fixture, 'full')['sources']
    checks += 1
    assert len(encoded(payload(fixture, 'segment'))) < len(encoded(payload(fixture, 'full')))
    checks += 1
expected = FIXTURES[0]['expected']
invalid = (
    '{}', 'not json', json.dumps({**expected, 'owner': 'Tomas'}),
    json.dumps({**expected, 'extra': 'field'}), json.dumps({**expected, 'owner': True}),
    '{"record_id":"R101","owner":"Mira","owner":"Mira","due_date":"2026-12-03","status":"open"}',
)
for value in invalid:
    assert not score(value, expected)['correct']
    checks += 1
print(json.dumps({'fixture_and_oracle_checks': checks, 'passed': True}))
