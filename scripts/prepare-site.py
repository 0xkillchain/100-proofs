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
footer = '\n\n<footer><a href="https://x.com/0xkillchain">@0xkillchain on X</a></footer>\n'
aliases = {
    '74-Hebrew-Words-European-Languages': '74-Hebrew-Words-In-European-Languages',
    '75-Ancient-Art': '75-Ancient-Art-Depicts-Europeans',
    '76-The-Magi': '76-The-Magi-Were-Israelites',
    '77-Christ-Depicted-As-European': '77-Christ-And-Apostles-European',
    '78-Early-Christian-Art': '78-Early-Christian-Art-Confirms',
    '81-Additional-Proofs': '81-European-Civilization',
}
notes = [p for p in ROOT.glob('*.md') if re.match(r'^\d+\s*-', p.name) or p.name == 'INDEX.md']
numbers = {int(p.name.split('-')[0]) for p in notes if re.match(r'^\d+\s*-', p.name)}
if numbers != set(range(1, 101)) or not (ROOT / 'INDEX.md').is_file():
    raise SystemExit('Expected source documents 1–100 and INDEX.md; refusing to publish incomplete content.')
names = {p.stem for p in notes}
# Match legacy shorthand links to the actual numbered document, without changing source text.
for old, target in list(aliases.items()):
    matches = [n for n in names if n.split('-')[0].strip().isdigit() and int(n.split('-')[0]) == int(old.split('-')[0])]
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
    legacy_name = source.stem.replace(' - ', '-').replace(' ', '-')
    redirect = f'---\naliases:\n  - {legacy_name}\n---\n\n' if source.name != 'INDEX.md' else ''
    (content / destination).write_text(redirect + text.lstrip().rstrip() + footer)
index_entries = []
numbered_notes = sorted(
    (p for p in notes if p.name != 'INDEX.md'),
    key=lambda p: int(p.name.split('-')[0]),
)
for source in numbered_notes:
    number = int(source.name.split('-')[0])
    heading = re.search(r'^#\s+(.+)$', source.read_text(), re.MULTILINE)
    title = heading.group(1).strip() if heading else source.stem.split('-', 1)[1].strip()
    title = re.sub(r'^Proof\s+\d+:\s*', '', title)
    index_entries.append(f'{number}. [[{source.stem}|{title}]]')
(content / 'index.md').write_text(
    '# 100 Proofs Index\n\n' +
    '\n'.join(index_entries) + '\n' + footer
)
config_path = quartz / 'quartz.config.ts'
config = config_path.read_text()
for old, new in [
    ('pageTitle: "Quartz 4"', 'pageTitle: "100 Proofs Research Archive"'),
    ('baseUrl: "quartz.jzhao.xyz"', 'baseUrl: "0xkillchain.github.io/100-proofs"'),
    ('analytics: {\n      provider: "plausible",\n    }', 'analytics: null'),
]:
    if old not in config:
        raise SystemExit(f'Unexpected Quartz configuration: missing {old!r}')
    config = config.replace(old, new, 1)
config_path.write_text(config)
# Hide dates and estimated reading time on content pages.
layout_path = quartz / 'quartz.layout.ts'
layout = layout_path.read_text()
layout, removed = re.subn(r'Component\.ContentMeta\(\s*\),?\s*', '', layout)
if removed < 1:
    raise SystemExit('Expected a Quartz ContentMeta component; review layout before publishing.')
layout_path.write_text(layout)
# Keep the page-level X link while suppressing Quartz's built-in attribution/footer.
(quartz / 'quartz/components/Footer.tsx').write_text(
    'import { QuartzComponent, QuartzComponentConstructor } from "./types"\n\n'
    'export default (() => {\n'
    '  const Footer: QuartzComponent = () => <></>\n'
    '  return Footer\n'
    '}) satisfies QuartzComponentConstructor\n'
)
print(f'Staged {len(notes)} source documents plus homepage; all wikilinks resolve.')
