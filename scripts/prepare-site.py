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
notes = [p for p in ROOT.glob('*.md') if re.match(r'^\d+\s*-', p.name) or p.name == 'INDEX.md']
numbers = {int(p.name.split('-')[0]) for p in notes if re.match(r'^\d+\s*-', p.name)}
if numbers != set(range(1, 101)) or not (ROOT / 'INDEX.md').is_file():
    raise SystemExit('Expected source documents 1–100 and INDEX.md; refusing to publish incomplete content.')
names = {p.stem for p in notes}
index_entries = []
notes.sort(key=lambda p: int(p.name.split('-')[0]) if p.name != 'INDEX.md' else 101)
for source in notes:
    text = source.read_text()
    targets = [re.split(r'[|#]', m, maxsplit=1)[0] for m in re.findall(r'\[\[([^\]]+)\]\]', text)]
    missing = set(targets) - names - {''}
    if missing:
        raise SystemExit(f'{source.name}: unresolved links: {sorted(missing)}')
    destination = 'source-index.md' if source.name == 'INDEX.md' else source.name
    legacy_name = source.stem.replace(' - ', '-').replace(' ', '-')
    redirect = f'---\naliases:\n  - {legacy_name}\n---\n\n' if source.name != 'INDEX.md' else ''
    (content / destination).write_text(redirect + text.strip() + footer)
    if source.name != 'INDEX.md':
        number = int(source.name.split('-')[0])
        heading = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        title = heading.group(1).strip() if heading else source.stem.split('-', 1)[1].strip()
        title = re.sub(r'^Proof\s+\d+:\s*', '', title)
        index_entries.append(f'{number}. [[{source.stem}|{title}]]')
(content / 'index.md').write_text(
    '---\ntitle: 100 Proofs Index\n---\n\n' +
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
