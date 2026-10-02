"""Portable Markdown views for decisions and revision review."""
from .review import validate_review
from .core import compare
from .audit import audit
from .inventory import inventory
from .core import render


def _safe(value):
    return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('\n', ' ')


def decision_cards(project, review):
    validate_review(project, review)
    context = review['context']
    rows = ['# Contract decisions', '',
            f"Contract: {_safe(context['contract_type'])} · Party: {_safe(context['represented_party'])} · Jurisdiction: {_safe(context['jurisdiction'])}",
            '', 'Choose an option for each material finding. Record your reason before applying an edit.', '']
    for f in review['findings']:
        rows += [f"## {_safe(f['id'])} · {_safe(f['lens'])}", '',
                 f"**Text:** {'; '.join(_safe(e['block_id'] + ': ' + e['quote']) for e in f['evidence']) or _safe(f.get('absence_basis', ''))}", '',
                 f"**Issue:** {_safe(f['issue'])}", '',
                 f"**Effect:** {_safe(f['consequence'])}", '',
                 f"**Uncertainty:** {_safe(f['uncertainty'])}", '',
                 f"**Choice needed:** {_safe(f['decision_needed'])}", '',
                 f"- [ ] Adopt the proposed change: {_safe(f['proposal'])}",
                 '- [ ] Keep the existing wording',
                 '- [ ] Defer pending more information',
                 '', '**Reason/alternative:** ____________________', '']
    if not review['findings']:
        rows += ['No findings recorded within the stated review scope.']
    return '\n'.join(rows).rstrip() + '\n'


def revision_report(original, revised, style='preserve'):
    changes = compare(original, revised, style)
    flags = audit(original, revised)['flags']
    rows = ['# Revision report', '', f"Source SHA-256: `{revised['source_sha256']}` · Version: {revised['version']}", '',
            '## Decisions', '']
    for key, item in revised['decisions'].items():
        rows.append(f"- **{_safe(key)}:** {_safe(item['status'])} — {_safe(item['reason'])}")
    if not revised['decisions']:
        rows.append('No inclusion decisions recorded.')
    rows += ['', '## Review flags', '']
    for flag in flags:
        rows.append(f"- **{_safe(flag['block_id'])}:** {_safe(flag['changes'])}")
    if not flags:
        rows.append('No lexical flags; review all edits for meaning regardless.')
    rows += ['', '## Text comparison', '', '```diff', changes['unified_diff'].rstrip(), '```', '']
    return '\n'.join(rows)


def structure_preview(project):
    """Show layout choices without treating a menu as required legal content."""
    candidates = inventory(project)['heading_candidates']
    confirmed = [b for b in project['blocks'] if b['kind'] == 'heading']
    rows = ['# Structure choices', '',
            'Existing confirmed headings: ' + (', '.join(_safe(b['title']) for b in confirmed) or 'none'),
            'Unconfirmed heading candidates: ' + (', '.join(_safe(c['title']) for c in candidates) or 'none'), '',
            '| Choice | Effect | Preview |', '| --- | --- | --- |']
    for style, effect in [('preserve', 'Keep source sequence and headings'),
                          ('decimal', 'Number confirmed headings by level'),
                          ('articles', 'Use Article at level 1 and Section below')]:
        try:
            text, _ = render(project, style)
            sample = ' / '.join(t.strip() for t in text.splitlines() if t.strip())[:180]
        except ValueError as exc:
            sample = 'Needs heading correction: ' + str(exc)
        rows.append(f'| {style} | {_safe(effect)} | {_safe(sample)} |')
    rows += ['', '## Candidate section decisions', '',
             'For each candidate, choose include, omit, or defer after considering the transaction. These are prompts, not required clauses.', '',
             '| Candidate | Choice | Reason or condition |', '| --- | --- | --- |']
    for name in ('Background', 'Definitions', 'Performance and deliverables', 'Payment',
                 'Term and termination', 'Notices', 'Risk allocation', 'General provisions',
                 'Signatures and attachments'):
        rows.append(f'| {name} | include / omit / defer |  |')
    rows += ['', 'Definition placement: inline / consolidated before operative terms / consolidated after operative terms / retain current placement.', '']
    return '\n'.join(rows)
