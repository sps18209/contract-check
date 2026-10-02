"""Export reviewer-facing cases without answer keys."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
def export(output):
    cases = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    for case in cases:
        body = '\n'.join(['# ' + case['id'], '', 'Represented party: ' + case['represented_party'],
                          'Transaction: ' + case['domain'], '', 'Instructions:', case['instructions'],
                          '', 'Draft contract:', case['contract'], '',
                          'Use Contract Check to return evidence-linked findings, structural choices, and unresolved questions.'])
        (directory / (case['id'] + '.md')).write_text(body + '\n', encoding='utf-8')
    return len(cases)


if __name__ == '__main__':
    print(export(sys.argv[1]))
