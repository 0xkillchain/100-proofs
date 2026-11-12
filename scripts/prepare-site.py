"""Stage research documents in an existing Quartz 4 checkout; originals stay untouched."""
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
quartz = Path(sys.argv[1]).resolve()
content = quartz / 'content'
if content.exists():
    shutil.rmtree(content)
content.mkdir()
notice = ('> [!warning] Research archive — claims under examination\n'
          '> This page preserves extremist source material for critical analysis and refutation. '
          'Its racial and religious claims are not endorsed. Rebuttals are being developed; '
          'the presence of a claim here does not establish its accuracy.\n\n')
aliases = {
    '74-Hebrew-Words-European-Languages': '74-Hebrew-Words-In-European-Languages',
    '75-Ancient-Art': '75-Ancient-Art-Depicts-Europeans',
    '76-The-Magi': '76-The-Magi-Were-Israelites',
    '77-Christ-Depicted-As-European': '77-Christ-And-Apostles-European',
    '78-Early-Christian-Art': '78-Early-Christian-Art-Confirms',
    '81-Additional-Proofs': '81-European-Civilization',
}
notes = [p for p in ROOT.glob('*.md') if re.match(r'^\d+-', p.name) or p.name == 'INDEX.md']
names = {p.stem for p in notes}
# Match legacy shorthand links to the actual numbered document, without changing source text.
for old, target in list(aliases.items()):
    matches = [n for n in names if n.split('-')[0] == old.split('-')[0]]
    if target not in names and len(matches) == 1:
        aliases[old] = matches[0]
for source in notes:
    text = source.read_text()
    def resolve(match):
        raw = match.group(1)
        target = re.split(r'[|#]', raw, maxsplit=1)[0]
        return '[[' + aliases.get(target, target) + raw[len(target):] + ']]'
    text = re.sub(r'\[\[([^\]]+)\]\]', resolve, text)
    targets = [re.split(r'[|#]', m, maxsplit=1)[0] for m in re.findall(r'\[\[([^\]]+)\]\]', text)]
    missing = set(targets) - names - {''}
    if missing:
        raise SystemExit(f'{source.name}: unresolved links: {sorted(missing)}')
    destination = 'source-index.md' if source.name == 'INDEX.md' else source.name
    (content / destination).write_text(notice + text.lstrip())
(content / 'index.md').write_text('# 100 Proofs — Research Archive\n\n' + notice +
    'This archive documents a collection of extremist claims for analysis and evidence-based refutation. '
    'Source documents retain their original wording; critical responses are a work in progress.\n\n'
    'Start with [[source-index|the source claim index]]. Use search or backlinks to explore related pages.\n')
config_path = quartz / 'quartz.config.ts'
config = config_path.read_text()
for old, new in [
    ('pageTitle: "Quartz 4"', 'pageTitle: "100 Proofs — Research Archive"'),
    ('baseUrl: "quartz.jzhao.xyz"', 'baseUrl: "0xkillchain.github.io/100-proofs"'),
    ('analytics: {\n      provider: "plausible",\n    }', 'analytics: null'),
]:
    if old not in config:
        raise SystemExit(f'Unexpected Quartz configuration: missing {old!r}')
    config = config.replace(old, new, 1)
config_path.write_text(config)
print(f'Staged {len(notes)} source documents plus homepage; all wikilinks resolve.')
