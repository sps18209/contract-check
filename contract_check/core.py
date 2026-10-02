"""Auditable, deterministic structural operations. Legal interpretation remains human/model work."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from difflib import unified_diff
from typing import Any

SCHEMA = 1
STYLES = ('preserve', 'decimal', 'articles')
HEADING = re.compile(r'^(?:(Article|Section)\s+)?(\d+(?:\.\d+)*)(?:\.)?\s+(.+)$', re.I)
REF = re.compile(r'\b(Article|Section)\s+(\d+(?:\.\d+)*)\b', re.I)
UNSUPPORTED_REF = re.compile(r'\bSections\s+\d|\b(?:Section|Article)\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\)|\s*(?:-|–|through|to)\s*\d)|§\s*\d|\b(?:Clause|Paragraph|Schedule|Exhibit)\s+[A-Z0-9]', re.I)
DEFINED = re.compile(r'[“"]([^“”"]+)[”"]\s+(?:means|shall mean)\b', re.I)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def ingest(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError('input must contain text')
    # Split only at blank lines. No inference about whether a block is a clause.
    chunks = re.split(r'(?<=\n)\s*\n', text)
    blocks = [{'id': f'b{i:05}', 'text': t, 'kind': 'body', 'origin': [f'b{i:05}']}
              for i, t in enumerate(chunks, 1) if t]
    return {'schema': SCHEMA, 'source': text, 'source_sha256': digest(text),
            'version': 0, 'blocks': blocks, 'decisions': {}, 'ledger': []}


def validate(project: dict[str, Any]) -> None:
    if project.get('schema') != SCHEMA or project.get('source_sha256') != digest(project.get('source', '')):
        raise ValueError('invalid project schema or source hash')
    if type(project.get('version')) is not int or project['version'] < 0:
        raise ValueError('invalid version')
    blocks = project.get('blocks')
    if not isinstance(blocks, list) or not all(isinstance(b, dict) for b in blocks):
        raise ValueError('invalid blocks')
    ids = [b.get('id') for b in blocks]
    if len(set(ids)) != len(ids) or not all(isinstance(x, str) and x for x in ids):
        raise ValueError('duplicate or invalid block ids')
    for b in blocks:
        if not isinstance(b.get('text'), str) or b.get('kind') not in ('body', 'heading'):
            raise ValueError('invalid block text or kind')
        if b['kind'] == 'heading':
            if type(b.get('level')) is not int or not 1 <= b['level'] <= 6 or not isinstance(b.get('title'), str) or not b['title'].strip():
                raise ValueError('invalid heading')
            if b.get('old_label') is not None and not re.fullmatch(r'\d+(?:\.\d+)*', b['old_label']):
                raise ValueError('invalid old_label')
            if b.get('old_kind') is not None and b['old_kind'] not in ('Article', 'Section'):
                raise ValueError('invalid old_kind')
            raw = b['text'].strip()
            parsed = HEADING.fullmatch(raw)
            if '\n' in raw or (raw != b['title'] and (not parsed or parsed.group(3) != b['title'])):
                raise ValueError('heading text contains content beyond the confirmed title')
        if not isinstance(b.get('origin'), list) or not all(isinstance(x, str) for x in b['origin']):
            raise ValueError('invalid origin')
    if not isinstance(project.get('decisions'), dict) or not isinstance(project.get('ledger'), list):
        raise ValueError('invalid decisions or ledger')


def _approval(op: dict[str, Any]) -> None:
    if op.get('approved') is not True or not isinstance(op.get('reason'), str) or not op['reason'].strip():
        raise ValueError('each operation requires approval and reason')


def apply(project: dict[str, Any], plan: dict[str, Any], review=None, choices=None) -> dict[str, Any]:
    validate(project)
    if plan.get('base_version') != project['version'] or plan.get('source_sha256') != project['source_sha256']:
        raise ValueError('stale or unrelated plan')
    if (review is None) != (choices is None):
        raise ValueError('provide both review and choices')
    selected = {}
    if review is not None:
        from .review import validate_choices
        validate_choices(project, review, choices)
        selected = {s['finding_id']: s['choice'] for s in choices['selections']}
    result = copy.deepcopy(project)
    blocks = {b['id']: b for b in result['blocks']}
    seen = set()
    for op in plan.get('operations', []):
        _approval(op)
        action, bid = op.get('action'), op.get('id')
        if op.get('finding_id'):
            if selected.get(op['finding_id']) not in ('adopt', 'custom'):
                raise ValueError('edit is not linked to an adopted finding')
        elif op.get('classification') == 'substantive':
            raise ValueError('substantive edit needs an adopted finding')
        if action not in ('replace', 'delete', 'insert', 'label') or not isinstance(bid, str) or bid in seen:
            raise ValueError('invalid or repeated operation')
        seen.add(bid)
        if action == 'insert':
            if bid in blocks or not bid.startswith('n') or not isinstance(op.get('text'), str) or not op['text'].strip():
                raise ValueError('insert needs a new n-prefixed ID and text')
            block = {'id': bid, 'text': op['text'], 'kind': 'body', 'origin': []}
            blocks[bid] = block
        else:
            if bid not in blocks or blocks[bid]['text'] != op.get('before'):
                raise ValueError('unknown target or source mismatch')
            block = blocks[bid]
            if action == 'replace':
                if not isinstance(op.get('after'), str):
                    raise ValueError('invalid replacement')
                block['text'] = op['after']
                if block['kind'] == 'heading' and 'title' not in op:
                    raise ValueError('replacing a heading requires an explicit title')
            elif action == 'delete':
                del blocks[bid]
            elif action == 'label':
                pass
        if action in ('label', 'insert', 'replace') and 'kind' in op:
            block['kind'] = op['kind']
        if action in ('label', 'insert', 'replace') and block['kind'] == 'heading':
            for field in ('title', 'level', 'old_label', 'old_kind'):
                if field in op:
                    block[field] = op[field]
        result['ledger'].append({'version': project['version'] + 1, **copy.deepcopy(op)})
    order = plan.get('order')
    if order is None:
        if any(op.get('action') == 'insert' for op in plan.get('operations', [])):
            raise ValueError('insertions require explicit complete order')
        order = [b['id'] for b in result['blocks'] if b['id'] in blocks]
    if not isinstance(order, list) or len(order) != len(blocks) or len(set(order)) != len(order) or set(order) != set(blocks):
        raise ValueError('order must contain every remaining block exactly once')
    existing_order = [b['id'] for b in result['blocks'] if b['id'] in blocks]
    if [bid for bid in order if bid in existing_order] != existing_order:
        if plan.get('order_approved') is not True or not plan.get('order_reason'):
            raise ValueError('reordering requires approval and reason')
    result['blocks'] = [blocks[bid] for bid in order]
    decisions = plan.get('decisions', {})
    if not isinstance(decisions, dict):
        raise ValueError('decisions must be an object')
    for key, value in decisions.items():
        if not isinstance(key, str) or not isinstance(value, dict) or value.get('status') not in ('include', 'omit', 'defer') or not value.get('reason'):
            raise ValueError('invalid decision')
    result['decisions'].update(copy.deepcopy(decisions))
    result['version'] += 1
    validate(result)
    return result


def _numbered(project: dict[str, Any], style: str) -> tuple[dict[str, str], list[str]]:
    counters: list[int] = []
    labels: dict[str, str] = {}
    output: list[str] = []
    for b in project['blocks']:
        if b['kind'] != 'heading' or style == 'preserve':
            output.append(b['text'])
            continue
        level = b['level']
        if level > len(counters) + 1:
            raise ValueError('heading hierarchy skips a level')
        counters = counters[:level]
        if level > len(counters):
            counters.append(0)
        counters[-1] += 1
        number = '.'.join(map(str, counters))
        prefix = 'Article ' if style == 'articles' and level == 1 else 'Section ' if style == 'articles' else ''
        labels[b['id']] = number
        output.append(prefix + number + ' ' + b['title'])
    return labels, output


def render(project: dict[str, Any], style: str = 'preserve', update_refs: bool = False) -> tuple[str, dict[str, Any]]:
    validate(project)
    if style not in STYLES:
        raise ValueError('unknown style')
    labels, output = _numbered(project, style)
    mapping: dict[tuple[str, str], tuple[str, str]] = {}
    ambiguous: set[tuple[str, str]] = set()
    for b in project['blocks']:
        if b['kind'] == 'heading' and b.get('old_label') and b['id'] in labels:
            # Caller records the source reference kind explicitly where an article/section ambiguity exists.
            kind = b.get('old_kind') or 'Section'
            key = (kind.lower(), b['old_label'])
            if key in mapping:
                ambiguous.add(key)
            mapping[key] = ('Article' if style == 'articles' and b['level'] == 1 else 'Section', labels[b['id']])
    if update_refs:
        if style == 'preserve':
            raise ValueError('reference updates require a new numbering style')
        for i, b in enumerate(project['blocks']):
            if b['kind'] == 'heading':
                continue
            if UNSUPPORTED_REF.search(output[i]):
                raise ValueError('unsupported compound or subclause reference; review manually')
            def sub(match: re.Match[str]) -> str:
                key = (match.group(1).lower(), match.group(2))
                if key in ambiguous:
                    raise ValueError(f'ambiguous reference {match.group(0)}')
                if key not in mapping:
                    raise ValueError(f'unmapped reference {match.group(0)}')
                return mapping[key][0] + ' ' + mapping[key][1]
            output[i] = REF.sub(sub, output[i])
    return '\n\n'.join(t for t in output if t) + '\n', {'labels': labels, 'reference_map': {f'{k[0]} {k[1]}': f'{v[0]} {v[1]}' for k,v in mapping.items()}, 'ambiguous': [f'{k[0]} {k[1]}' for k in sorted(ambiguous)]}


def check(project: dict[str, Any], text: str) -> dict[str, Any]:
    validate(project)
    headings = [b for b in project['blocks'] if b['kind'] == 'heading']
    declared = {}
    candidates = {}
    for line in text.splitlines():
        match = HEADING.fullmatch(line.strip())
        if match:
            candidates.setdefault(match.group(3), []).append(match)
    for b in headings:
        for match in candidates.get(b['title'], []):
            key = ((match.group(1) or 'Section').lower(), match.group(2))
            declared[key] = declared.get(key, 0) + 1
    refs = {(m.group(1).lower(), m.group(2)) for m in REF.finditer(text)}
    unsupported = sorted(set(m.group(0) for m in UNSUPPORTED_REF.finditer(text)))
    definitions: dict[str, int] = {}
    for term in DEFINED.findall(text):
        definitions[term] = definitions.get(term, 0) + 1
    return {'scope': 'numbered headings, explicit Article/Section references, quoted means definitions; semantic review required',
            'heading_count': len(headings),
            'duplicate_labels': [f'{k[0]} {k[1]}' for k,v in declared.items() if v > 1],
            'unresolved_references': [f'{k[0]} {k[1]}' for k in sorted(refs - declared.keys())],
            'unsupported_references': unsupported,
            'duplicate_definitions': sorted(k for k,v in definitions.items() if v > 1)}


def compare(old: dict[str, Any], new: dict[str, Any], style: str = 'preserve') -> dict[str, Any]:
    validate(old); validate(new)
    if old['source_sha256'] != new['source_sha256']:
        raise ValueError('unrelated projects')
    a, b = {x['id']: x for x in old['blocks']}, {x['id']: x for x in new['blocks']}
    old_common = [bid for bid in a if bid in b]
    new_common = [bid for bid in b if bid in a]
    changes = [{'id': bid, 'change': 'insert' if bid not in a else 'replace' if a[bid]['text'] != block['text'] else 'move',
                'before': a.get(bid, {}).get('text'), 'after': block['text']}
               for pos, (bid, block) in enumerate(b.items())
               if bid not in a or a[bid]['text'] != block['text'] or old_common.index(bid) != new_common.index(bid)]
    changes += [{'id': bid, 'change': 'delete', 'before': block['text'], 'after': None} for bid, block in a.items() if bid not in b]
    old_text, _ = render(old, style)
    new_text, _ = render(new, style)
    diff = ''.join(unified_diff(old_text.splitlines(True), new_text.splitlines(True), fromfile='original', tofile='revised'))
    return {'changes': changes, 'unified_diff': diff, 'decisions': new['decisions'], 'version': new['version']}
