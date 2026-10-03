"""Command line interface for the host-independent structural engine."""
import argparse
import json
from pathlib import Path
from .core import ingest, apply, render, check, compare
from .review import validate_review, validate_choices, choice_template
from .audit import audit
from .docx import extract_docx
from .presentation import decision_cards, revision_report, structure_preview
from .inventory import inventory
from .enforcement import assess, validate_request, validate_assessment
from .enforcement.issues import request_template
from .enforcement.report import render_assessment
from .enforcement.providers.local_llm import LocalLLMProvider


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main(argv=None):
    p = argparse.ArgumentParser(prog='contract-check')
    sub = p.add_subparsers(dest='command', required=True)
    for name, args in [('ingest', ['input', 'output']), ('apply', ['project', 'plan', 'output']),
                       ('render', ['project', 'output']), ('check', ['project', 'input']),
                       ('compare', ['original', 'revised', 'output']), ('audit', ['original', 'revised', 'output']),
                       ('validate-review', ['project', 'review']),
                       ('extract-docx', ['input', 'output', 'manifest']),
                       ('cards', ['project', 'review', 'output']),
                       ('report', ['original', 'revised', 'output']),
                       ('inventory', ['project', 'output']), ('preview', ['project', 'output']),
                       ('choice-template', ['project', 'review', 'output']),
                       ('validate-choices', ['project', 'review', 'choices']),
                       ('enforcement-template', ['project', 'review', 'output']),
                       ('enforcement-validate', ['project', 'review', 'request']),
                       ('enforcement-assess', ['project', 'review', 'request', 'output']),
                       ('enforcement-report', ['project', 'review', 'request', 'assessment', 'output'])]:
        cmd = sub.add_parser(name)
        for arg in args:
            cmd.add_argument(arg)
        if name in ('render', 'compare', 'report'):
            cmd.add_argument('--style', choices=['preserve', 'decimal', 'articles'], default='preserve')
        if name == 'render':
            cmd.add_argument('--update-refs', action='store_true')
            cmd.add_argument('--map-output')
        if name == 'apply':
            cmd.add_argument('--review')
            cmd.add_argument('--choices')
        if name == 'enforcement-assess':
            cmd.add_argument('--authorities')
            cmd.add_argument('--local-endpoint')
            cmd.add_argument('--model')
        if name == 'enforcement-report':
            cmd.add_argument('--authorities')
    a = p.parse_args(argv)
    try:
        if a.command == 'ingest':
            save(a.output, ingest(Path(a.input).read_text(encoding='utf-8')))
        elif a.command == 'apply':
            save(a.output, apply(load(a.project), load(a.plan),
                                 load(a.review) if a.review else None,
                                 load(a.choices) if a.choices else None))
        elif a.command == 'render':
            text, info = render(load(a.project), a.style, a.update_refs)
            Path(a.output).write_text(text, encoding='utf-8')
            if a.map_output:
                save(a.map_output, info)
        elif a.command == 'check':
            report = check(load(a.project), Path(a.input).read_text(encoding='utf-8'))
            print(json.dumps(report, indent=2))
            return 2 if any(report[k] for k in ('duplicate_labels', 'unresolved_references', 'unsupported_references', 'duplicate_definitions')) else 0
        elif a.command == 'compare':
            save(a.output, compare(load(a.original), load(a.revised), a.style))
        elif a.command == 'audit':
            save(a.output, audit(load(a.original), load(a.revised)))
        elif a.command == 'validate-review':
            print(json.dumps(validate_review(load(a.project), load(a.review)), indent=2))
        elif a.command == 'extract-docx':
            extracted = extract_docx(a.input)
            Path(a.output).write_text(extracted['text'], encoding='utf-8')
            save(a.manifest, extracted['manifest'])
        elif a.command == 'cards':
            Path(a.output).write_text(decision_cards(load(a.project), load(a.review)), encoding='utf-8')
        elif a.command == 'report':
            Path(a.output).write_text(revision_report(load(a.original), load(a.revised), a.style), encoding='utf-8')
        elif a.command == 'inventory':
            save(a.output, inventory(load(a.project)))
        elif a.command == 'preview':
            Path(a.output).write_text(structure_preview(load(a.project)), encoding='utf-8')
        elif a.command == 'choice-template':
            save(a.output, choice_template(load(a.project), load(a.review)))
        elif a.command == 'validate-choices':
            print(json.dumps(validate_choices(load(a.project), load(a.review), load(a.choices)), indent=2))
        elif a.command == 'enforcement-template':
            save(a.output, request_template(load(a.project), load(a.review)))
        elif a.command == 'enforcement-validate':
            print(json.dumps(validate_request(load(a.project), load(a.review), load(a.request)), indent=2))
        elif a.command == 'enforcement-assess':
            if bool(a.local_endpoint) != bool(a.model):
                raise ValueError('--local-endpoint and --model must be supplied together')
            provider = LocalLLMProvider(a.local_endpoint, a.model) if a.local_endpoint else None
            save(a.output, assess(load(a.project), load(a.review), load(a.request),
                                  load(a.authorities) if a.authorities else None, provider))
        elif a.command == 'enforcement-report':
            project, review, request, assessment = load(a.project), load(a.review), load(a.request), load(a.assessment)
            validate_assessment(project, review, request, assessment,
                                load(a.authorities) if a.authorities else None)
            Path(a.output).write_text(render_assessment(assessment), encoding='utf-8')
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        p.exit(1, f'contract-check: {error}\n')
    return 0
