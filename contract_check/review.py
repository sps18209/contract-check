"""Evidence provenance validation; no automatic legal judgment."""
from .core import validate

LENSES = {'deal', 'linguistic', 'philosophical', 'operational', 'structural', 'definitions', 'termination', 'legal'}
STATUSES = {'proposed', 'accepted', 'rejected', 'deferred', 'resolved'}


def validate_review(project, review):
    validate(project)
    if review.get('source_sha256') != project['source_sha256'] or review.get('project_version') != project['version']:
        raise ValueError('review is stale or unrelated')
    context = review.get('context', {})
    for key in ('contract_type', 'represented_party', 'objective', 'jurisdiction'):
        if not isinstance(context.get(key), str):
            raise ValueError(f'missing context {key}; use unknown explicitly')
    blocks = {b['id']: b['text'] for b in project['blocks']}
    findings = review.get('findings')
    if not isinstance(findings, list):
        raise ValueError('findings must be a list')
    ids = set()
    for f in findings:
        if not isinstance(f, dict) or not isinstance(f.get('id'), str) or f['id'] in ids:
            raise ValueError('finding needs unique id')
        ids.add(f['id'])
        if f.get('lens') not in LENSES or f.get('status') not in STATUSES:
            raise ValueError('invalid lens or status')
        evidence = f.get('evidence', [])
        if not isinstance(evidence, list) or not evidence:
            raise ValueError('finding needs source evidence')
        for row in evidence:
            if row.get('block_id') not in blocks or not isinstance(row.get('quote'), str) or not row['quote'] or row['quote'] not in blocks[row['block_id']]:
                raise ValueError('quote does not occur in cited block')
        for key in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed'):
            if not isinstance(f.get(key), str):
                raise ValueError(f'missing {key}; use unknown explicitly')
        if not isinstance(f.get('affected_blocks'), list) or any(x not in blocks for x in f['affected_blocks']):
            raise ValueError('invalid affected blocks')
    return {'valid': True, 'finding_count': len(findings)}
