"""Candidate headings and defined terms, for human confirmation."""
import re
from .core import HEADING, DEFINED, validate


def inventory(project):
    validate(project)
    headings = []
    terms = {}
    full_text = '\n\n'.join(b['text'] for b in project['blocks'])
    for block in project['blocks']:
        match = HEADING.fullmatch(block['text'].strip())
        if match and block['kind'] != 'heading':
            number = match.group(2)
            headings.append({'block_id': block['id'], 'old_label': number,
                             'old_kind': match.group(1) or 'Section',
                             'title': match.group(3), 'suggested_level': number.count('.') + 1,
                             'status': 'candidate; confirm before labeling'})
        for match in DEFINED.finditer(block['text']):
            term = match.group(1)
            terms.setdefault(term, []).append(block['id'])
    return {'heading_candidates': headings,
            'defined_terms': [{'term': term, 'definition_blocks': ids,
                               'case_insensitive_mentions': len(re.findall(r'\b' + re.escape(term) + r'\b', full_text, re.I))}
                              for term, ids in sorted(terms.items())],
            'scope': 'number-prefix heading candidates and quoted means definitions only; confirm manually'}
