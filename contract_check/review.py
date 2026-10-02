"""Evidence provenance validation; no automatic legal judgment."""
from .core import validate

LENSES = {'deal', 'linguistic', 'philosophical', 'operational', 'structural', 'definitions', 'termination', 'legal'}
STATUSES = {'proposed', 'accepted', 'rejected', 'deferred', 'resolved'}
CHOICES = {'adopt', 'retain', 'defer', 'custom'}


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
        if not isinstance(evidence, list) or (not evidence and not f.get('absence_basis')):
            raise ValueError('finding needs source evidence or an absence basis')
        for row in evidence:
            if row.get('block_id') not in blocks or not isinstance(row.get('quote'), str) or not row['quote'] or row['quote'] not in blocks[row['block_id']]:
                raise ValueError('quote does not occur in cited block')
        for key in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed'):
            if not isinstance(f.get(key), str):
                raise ValueError(f'missing {key}; use unknown explicitly')
        if not isinstance(f.get('affected_blocks'), list) or any(x not in blocks for x in f['affected_blocks']):
            raise ValueError('invalid affected blocks')
    return {'valid': True, 'finding_count': len(findings)}


def choice_template(project, review):
    validate_review(project, review)
    return {'source_sha256': project['source_sha256'], 'project_version': project['version'],
            'selections': [{'finding_id': f['id'], 'choice': None, 'reason': '', 'custom_instruction': ''}
                           for f in review['findings']]}


def validate_choices(project, review, choices):
    validate_review(project, review)
    if choices.get('source_sha256') != project['source_sha256'] or choices.get('project_version') != project['version']:
        raise ValueError('choices are stale or unrelated')
    findings = {f['id'] for f in review['findings']}
    selections = choices.get('selections')
    if not isinstance(selections, list):
        raise ValueError('selections must be an array')
    ids = [s.get('finding_id') for s in selections]
    if len(ids) != len(set(ids)) or set(ids) != findings:
        raise ValueError('each finding needs exactly one selection')
    for selection in selections:
        if selection.get('choice') not in CHOICES or not isinstance(selection.get('reason'), str) or not selection['reason'].strip():
            raise ValueError('selection needs a choice and reason')
        if selection['choice'] == 'custom' and not selection.get('custom_instruction'):
            raise ValueError('custom choice needs an instruction')
    return {'valid': True, 'selection_count': len(selections)}
