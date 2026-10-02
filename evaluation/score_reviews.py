"""Score machine-checkable evaluation evidence; leave legal judgments to reviewers."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contract_check.core import validate
from contract_check.review import validate_review

ROOT = Path(__file__).resolve().parent


def score(directory):
    cases = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))
    rows = []
    for case in cases:
        prefix = Path(directory) / case['id']
        project_path = prefix.with_suffix('.project.json')
        review_path = prefix.with_suffix('.review.json')
        revised_path = prefix.with_suffix('.revised.txt')
        row = {'case_id': case['id'], 'status': 'not tested', 'human_assessment': 'pending'}
        if not project_path.exists() or not review_path.exists():
            rows.append(row)
            continue
        try:
            project = json.loads(project_path.read_text(encoding='utf-8'))
            review = json.loads(review_path.read_text(encoding='utf-8'))
            validate(project)
            if project['source'].rstrip('\n') != case['contract'].rstrip('\n'):
                raise ValueError('case source does not match fixture (except terminal newlines)')
            validate_review(project, review)
            cited_ids = {e['block_id'] for f in review['findings'] for e in f['evidence']}
            blocks = {b['id']: b['text'] for b in project['blocks']}
            row['expected_passage_cited'] = any(case['expected_issue']['evidence'] in blocks[bid] for bid in cited_ids)
            row['preservation'] = 'not tested'
            if revised_path.exists():
                final = revised_path.read_text(encoding='utf-8')
                row['preservation'] = {phrase: phrase in final for phrase in case['preserve']}
            row['status'] = 'machine checks completed'
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            row['status'] = 'invalid response'
            row['error'] = str(exc)
        rows.append(row)
    return {'scope': 'provenance, expected passage citation and unchanged phrases only; human rubric required',
            'cases': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('responses')
    parser.add_argument('output')
    args = parser.parse_args()
    Path(args.output).write_text(json.dumps(score(args.responses), indent=2) + '\n', encoding='utf-8')
