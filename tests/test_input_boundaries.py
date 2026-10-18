import json
import tempfile
import unittest
from pathlib import Path
from pipeline.brief import validate
from pipeline.observed import ingest


class InputBoundaries(unittest.TestCase):
    def test_invalid_provider_shapes_raise_validation_errors(self):
        valid = dict(headline='Review tracking', observations=[dict(metric_id='registration_rate', interpretation='Check the mapped sessions.')], actions=['Review tags.'])
        invalid = [None, [], 'text', dict(valid, headline=' '), dict(valid, observations=[None]), dict(valid, observations=[dict(metric_id=[], interpretation='Check.')]), dict(valid, actions=[' '])]
        for draft in invalid:
            with self.subTest(draft=draft), self.assertRaises(ValueError):
                validate(draft)

    def test_malformed_journeys_do_not_overwrite_previous_import(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            output = root/'out'
            output.mkdir()
            staged = output/'events-v1.csv'
            staged.write_text('previous verified import', encoding='utf-8')
            for events in [[None], ['bad'], [dict(kind='page_view', provenance='observed_test')], [dict(kind='cta_click', provenance='observed_test')]]:
                source = root/'events.json'
                source.write_text(json.dumps(events), encoding='utf-8')
                with self.subTest(events=events), self.assertRaises(ValueError):
                    ingest(source, output)
                self.assertEqual(staged.read_text(encoding='utf-8'), 'previous verified import')
