#!/usr/bin/env python3
"""
gen-routing-tests.py — parse tools/routing-scenarios.md and emit per-skill
routing test YAML files.

  skills/<skill>/tests/routing_trigger.yaml  — prompts where this skill is Primary
  skills/<skill>/tests/routing_boundary.yaml — prompts where this skill is Inactive

Usage:
    python tools/gen-routing-tests.py           # generate / overwrite files
    python tools/gen-routing-tests.py --dry-run # report what would be written;
                                                # prints MISSING: for any Primary
                                                # skill that lacks routing_trigger.yaml
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

KNOWN_SKILLS = {
    'dev-workflow', 'ai-hygiene', 'commit-message', 'pr-description',
    'changelog', 'release-prep', 'code-review', 'bug-triage', 'scope-creep',
    'architecture-review', 'test-strategy', 'context-compression', 'docs-audit',
    'security-audit', 'dependency-check', 'observability-audit', 'kill-test',
    'performance-audit', 'infra-review', 'refactor-guide',
}

REPO_ROOT = Path(__file__).parent.parent
SCENARIOS_FILE = REPO_ROOT / 'tools' / 'routing-scenarios.md'
SKILLS_DIR = REPO_ROOT / 'skills'

# Patterns that mark a skill as PRIMARY (fires/owns/handles/proceeds)
_FIRES_RE = re.compile(
    r'\b(\w[\w-]+)\s+(?:fires\b|owns\b|proceeds\b|handles\b|leads\b)'
    r'|\bthen\s+(\w[\w-]+)\b',
    re.IGNORECASE,
)

# Patterns that mark a skill as INACTIVE (stays silent / does not fire / not X)
_SILENT_RE = re.compile(
    r'\b(\w[\w-]+)\s+stays?\s+silent\b'
    r'|\b(\w[\w-]+)\s+does\s+(?:not|\*\*not\*\*)\s+(?:fire|re-)'
    r'|\b(\w[\w-]+)\s+stays\s+out\b'
    r'|(?:,\s*not|—\s*not|;\s*not|,\snot)\s+(?:a\s+(?:full\s+)?)?(\w[\w-]+)',
    re.IGNORECASE,
)

# Pivot words used as fallback to split before/after inactive region
_PIVOTS = ['stays silent', 'does not fire', ', not ', ' — not ', '**not**', 'stays out']


def _find_ordered(text):
    """Return known skill names found in text, ordered by first position."""
    hits = [(text.find(s), s) for s in KNOWN_SKILLS if s in text]
    hits.sort()
    return [s for _, s in hits]


def _parse_expect(expect_text, candidates=None):
    """Determine (primaries, inactives) from an Expect: line.

    Uses explicit regex patterns first; falls back to pivot-split for primaries
    only (never uses fallback to assign inactives — avoids false positives).
    """
    primaries, inactives = set(), set()

    for m in _FIRES_RE.finditer(expect_text):
        skill = m.group(1) or m.group(2)
        if skill and skill in KNOWN_SKILLS:
            primaries.add(skill)

    for m in _SILENT_RE.finditer(expect_text):
        skill = next((g for g in m.groups() if g and g in KNOWN_SKILLS), None)
        if skill:
            inactives.add(skill)

    inactives -= primaries  # don't double-count

    # Fallback: if no primaries found, use pivot split (primaries only)
    if not primaries:
        pivot_pos = len(expect_text)
        for pivot in _PIVOTS:
            pos = expect_text.lower().find(pivot.lower())
            if 0 < pos < pivot_pos:
                pivot_pos = pos
        before = expect_text[:pivot_pos]
        primaries = set(_find_ordered(before))

    # Restrict to declared candidates when provided
    if candidates:
        cands = set(candidates)
        primaries &= cands
        inactives &= cands

    # Sort by order of appearance in the text
    def _pos(s):
        p = expect_text.find(s)
        return p if p != -1 else 9999

    return sorted(primaries, key=_pos), sorted(inactives, key=_pos)


def _extract_prompt(block, header):
    """Try several patterns to extract the user-facing prompt from a scenario block."""
    # 1. Quoted text following closing ** on the header line: **A1. Title.** "prompt"
    m = re.search(r'\.\*\* "([^"]+)"', header)
    if m:
        return m.group(1)
    # 2. Title IS the prompt: **B2. "prompt text"**
    m = re.match(r'\*\*[A-Z]\d+\. "([^"]+)"\*\*', header)
    if m:
        return m.group(1)
    # 3. Explicit Scenario: line: - Scenario: ...text... "prompt."
    m = re.search(r'- Scenario: [^"]*"([^"]+)"', block)
    if m:
        return m.group(1)
    # 4. Fallback: first long quoted string anywhere in block
    m = re.search(r'"([^"]{20,})"', block)
    if m:
        return m.group(1)
    return None


def _parse_block(block):
    """Parse one scenario block. Returns a dict or None."""
    id_m = re.match(r'\*\*([A-Z]\d+)\.', block)
    if not id_m:
        return None
    sid = id_m.group(1)
    header = block.split('\n')[0]

    prompt = _extract_prompt(block, header)
    if not prompt:
        return {'id': sid, 'error': 'no prompt', 'primary': [], 'inactive': []}

    primaries, inactives = [], []

    # A-section: explicit Primary: / Inactive: fields on one line
    pm = re.search(r'\n- Primary: ([^\n]+)', block)
    im = re.search(r'Inactive: ([^\n]+)', block)

    if pm:
        # Take only the part before ' ·' (which introduces Supporting, Inactive)
        primary_part = pm.group(1).split('·')[0].strip()
        primaries = _find_ordered(primary_part)
        if im:
            inactives = [s for s in _find_ordered(im.group(1)) if s not in primaries]
    else:
        # B/C section: use Skill(s) involved + Expect line
        inv_m = re.search(r'Skill\(s\) involved: ([^\n]+)', block)
        exp_m = re.search(r'- Expect: (.+?)(?=\n-|\Z)', block, re.DOTALL)

        candidates = _find_ordered(inv_m.group(1)) if inv_m else None
        expect_text = exp_m.group(1).strip() if exp_m else ''

        if expect_text:
            primaries, inactives = _parse_expect(expect_text, candidates)
        elif candidates:
            primaries = candidates[:1]
            inactives = candidates[1:]

    guard_m = re.search(r'- Guard: ([^\n]+)', block)
    guard = guard_m.group(1).strip() if guard_m else ''

    return {'id': sid, 'prompt': prompt, 'primary': primaries, 'inactive': inactives, 'guard': guard}


def _yaml_entry(sid, prompt, should_trigger, notes=''):
    prompt_esc = prompt.replace('\\', '\\\\').replace('"', '\\"')
    lines = [
        f'- scenario: {sid}',
        f'  prompt: "{prompt_esc}"',
        f'  should_trigger: {"true" if should_trigger else "false"}',
    ]
    if notes:
        short = (notes[:117] + '...') if len(notes) > 120 else notes
        lines.append(f'  notes: "{short.replace(chr(34), chr(92)+chr(34))}"')
    return '\n'.join(lines)


def main():
    dry_run = '--dry-run' in sys.argv

    if not SCENARIOS_FILE.exists():
        print(f'ERROR: {SCENARIOS_FILE} not found', file=sys.stderr)
        sys.exit(1)

    text = SCENARIOS_FILE.read_text(encoding='utf-8')

    # Split at scenario headers (**A1., **B1., **C1., …)
    raw_blocks = re.split(r'(?=\n\*\*[A-Z]\d+\.)', '\n' + text)
    blocks = [b.strip() for b in raw_blocks if re.match(r'\*\*[A-Z]\d+\.', b.strip())]

    # skill -> [(sid, prompt, should_trigger, notes), ...]
    skill_tests = defaultdict(list)
    warnings = []

    for block in blocks:
        parsed = _parse_block(block)
        if not parsed:
            continue

        sid = parsed['id']
        if 'error' in parsed:
            warnings.append(f'{sid}: {parsed["error"]}')
            continue

        prompt = parsed['prompt']
        primaries = parsed['primary']
        inactives = parsed['inactive']
        guard = parsed.get('guard', '')

        if not primaries:
            warnings.append(f'{sid}: no primary skill identified — prompt: "{prompt[:60]}"')
            continue

        note_t = f'{sid} Primary. Guard: {guard}' if guard else f'{sid} Primary.'
        note_b = f'{sid} Inactive. Guard: {guard}' if guard else f'{sid} Inactive.'

        for skill in primaries:
            skill_tests[skill].append((sid, prompt, True, note_t))
        for skill in inactives:
            skill_tests[skill].append((sid, prompt, False, note_b))

    for w in warnings:
        print(f'WARNING: {w}')

    HEADER = '# Generated from tools/routing-scenarios.md — do not edit; re-run gen-routing-tests.py to update'

    if dry_run:
        for skill in sorted(skill_tests):
            trigger_entries = [e for e in skill_tests[skill] if e[2]]
            tfile = SKILLS_DIR / skill / 'tests' / 'routing_trigger.yaml'
            if trigger_entries and not tfile.exists():
                print(f'MISSING: skills/{skill}/tests/routing_trigger.yaml')
        print(f'\nDry run: {len(skill_tests)} skills with routing tests, '
              f'{sum(len(v) for v in skill_tests.values())} total entries')
        return

    written = 0
    for skill in sorted(skill_tests):
        skill_dir = SKILLS_DIR / skill
        if not skill_dir.exists():
            print(f'WARNING: skills/{skill}/ not found — skipping')
            continue

        tests_dir = skill_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)

        triggers = [e for e in skill_tests[skill] if e[2]]
        boundaries = [e for e in skill_tests[skill] if not e[2]]

        if triggers:
            path = tests_dir / 'routing_trigger.yaml'
            content = HEADER + '\n' + '\n'.join(_yaml_entry(*e) for e in triggers) + '\n'
            path.write_text(content, encoding='utf-8')
            print(f'  wrote {path.relative_to(REPO_ROOT)} ({len(triggers)} entries)')
            written += 1

        if boundaries:
            path = tests_dir / 'routing_boundary.yaml'
            content = HEADER + '\n' + '\n'.join(_yaml_entry(*e) for e in boundaries) + '\n'
            path.write_text(content, encoding='utf-8')
            print(f'  wrote {path.relative_to(REPO_ROOT)} ({len(boundaries)} entries)')
            written += 1

    print(f'\nGenerated {written} routing test files across {len(skill_tests)} skills.')


if __name__ == '__main__':
    main()
