import json
import tempfile
import unittest
from pathlib import Path
from evaluation.export_prompts import export
from evaluation.score_reviews import score
from contract_check import ingest


class EvaluationTest(unittest.TestCase):
    def test_prompts_withhold_expected_findings_and_traps(self):
        cases = json.loads((Path(__file__).parents[1] / 'evaluation' / 'cases.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(export(d), len(cases))
            for case in cases:
                prompt = (Path(d) / (case['id'] + '.md')).read_text()
                self.assertIn(case['contract'], prompt)
                self.assertNotIn('expected_issue', prompt)
                self.assertNotIn('concept', prompt)
                if 'trap' in case:
                    self.assertNotIn(case['trap'], prompt)

    def test_scorer_distinguishes_missing_from_valid_evidence(self):
        cases = json.loads((Path(__file__).parents[1] / 'evaluation' / 'cases.json').read_text())
        case = cases[0]
        project = ingest(case['contract'])
        bid = next(b['id'] for b in project['blocks'] if case['expected_issue']['evidence'] in b['text'])
        review = {'source_sha256': project['source_sha256'], 'project_version': 0,
                  'context': {'contract_type': 'services', 'represented_party': 'consultant',
                              'objective': 'bonus threshold', 'jurisdiction': 'unknown'},
                  'findings': [{'id': 'F-1', 'lens': 'deal', 'status': 'proposed',
                                'evidence': [{'block_id': bid, 'quote': case['expected_issue']['evidence']}],
                                'affected_blocks': [bid],
                                **{k: 'needs review' for k in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed')}}]}
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            (folder / (case['id'] + '.project.json')).write_text(json.dumps(project))
            (folder / (case['id'] + '.review.json')).write_text(json.dumps(review))
            result = score(folder)
        self.assertTrue(result['cases'][0]['expected_passage_cited'])
        self.assertEqual(result['cases'][0]['human_assessment'], 'pending')
        self.assertEqual(result['cases'][1]['status'], 'not tested')
