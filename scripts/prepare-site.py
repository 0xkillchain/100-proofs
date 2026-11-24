"""Stage research documents in an existing Quartz 4 checkout; originals stay untouched."""
from pathlib import Path
import re
import shutil
import sys
import subprocess
import hashlib
from scripture import generate

ROOT = Path(__file__).resolve().parents[1]
quartz = Path(sys.argv[1]).resolve()
# Fail on upstream changes rather than silently dropping graph improvements.
subprocess.run(['git', 'apply', '--check', str(ROOT / 'scripts/quartz-graph.patch')], cwd=quartz, check=True)
subprocess.run(['git', 'apply', str(ROOT / 'scripts/quartz-graph.patch')], cwd=quartz, check=True)
content = quartz / 'content'
if content.exists():
    shutil.rmtree(content)
content.mkdir()
footer = '\n\n<footer><p>Original research performed by <a href="https://christogenea.org">christogenea.org</a></p><a href="https://x.com/0xkillchain">@0xkillchain on X</a></footer>\n'
notes = [p for p in ROOT.glob('*.md') if re.match(r'^\d+\s*-', p.name)]
numbers = {int(p.name.split('-')[0]) for p in notes if re.match(r'^\d+\s*-', p.name)}
if numbers != set(range(1, 101)):
    raise SystemExit('Expected source documents 1–100; refusing to publish incomplete content.')
scripture_names = generate(content)
names = {p.stem for p in notes} | {'index'} | scripture_names
index_entries = []
notes.sort(key=lambda p: int(p.name.split('-')[0]))
for source in notes:
    text = re.sub(r'\[\[(?:INDEX|source-index)(?=[|#\]])', '[[index', source.read_text())
    targets = [re.split(r'[|#]', m, maxsplit=1)[0] for m in re.findall(r'\[\[([^\]]+)\]\]', text)]
    missing = set(targets) - names - {''}
    if missing:
        raise SystemExit(f'{source.name}: unresolved links: {sorted(missing)}')
    destination = source.name
    legacy_name = source.stem.replace(' - ', '-').replace(' ', '-')
    redirect = f'---\naliases:\n  - {legacy_name}\n---\n\n'
    (content / destination).write_text(redirect + text.strip() + footer)
    number = int(source.name.split('-')[0])
    heading = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = heading.group(1).strip() if heading else source.stem.split('-', 1)[1].strip()
    title = re.sub(r'^Proof\s+\d+:\s*', '', title)
    title = re.sub(r'\[\[[^|]+\|([^\]]+)\]\]', r'\1', title)
    index_entries.append(f'{number}. [[{source.stem}|{title}]]')
(content / 'index.md').write_text(
    '---\ntitle: 100 Proofs Index\naliases:\n  - source-index\n---\n\n' +
    '\n'.join(index_entries) + '\n' + footer.replace(
        '</footer>',
        '<p><a href="https://github.com/0xkillchain/100-proofs">View on GitHub</a></p></footer>',
    )
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
config = config.replace('Plugin.TableOfContents()', 'Plugin.TableOfContents({ minEntries: 0 })')
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
    'export default ((_opts?: unknown) => {\n'
    '  const Footer: QuartzComponent = () => <></>\n'
    '  return Footer\n'
    '}) satisfies QuartzComponentConstructor\n'
)
print(f'Staged {len(notes)} source documents plus homepage; all wikilinks resolve.')

# Replace Explorer with persistent Proofs / Scripture tabs.
shutil.copy2(ROOT / 'site/components/Library.tsx', quartz / 'quartz/components/Library.tsx')
shutil.copy2(ROOT / 'site/components/library.inline.ts', quartz / 'quartz/components/scripts/library.inline.ts')
shutil.copy2(ROOT / 'site/components/library.scss', quartz / 'quartz/components/styles/library.scss')
layout = layout_path.read_text()
if 'Component.Explorer()' not in layout:
    raise SystemExit('Expected Quartz Explorer; review library tab integration.')
layout = 'import Library from "./quartz/components/Library"\n' + layout.replace('Component.Explorer()', 'Library()')
shutil.copy2(ROOT / 'site/components/PageContents.tsx', quartz / 'quartz/components/PageContents.tsx')
shutil.copy2(ROOT / 'site/components/graph-window.ts', quartz / 'quartz/components/scripts/graph-window.ts')
layout = 'import PageContents from "./quartz/components/PageContents"\n' + layout
layout = layout.replace('Component.DesktopOnly(Component.TableOfContents()),', '')
layout = layout.replace('Component.TagList(),', 'Component.TagList(), PageContents(),')
layout = layout.replace('beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(),', 'beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), PageContents(),')
layout_path.write_text(layout)
print(f'Staged {len(scripture_names)} scripture library pages with Proofs / Scripture tabs.')

# Give each deployment distinct asset URLs; navigation across builds reloads scripts.
source_files = sorted(p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and p.suffix in {'.py', '.ts', '.tsx', '.scss', '.json', '.patch', '.md', '.yml'})
build_hash = hashlib.sha256()
for path in source_files:
    build_hash.update(str(path.relative_to(ROOT)).encode())
    build_hash.update(path.read_bytes())
revision = build_hash.hexdigest()[:12]
render_path = quartz / 'quartz/components/renderPage.tsx'
render = render_path.read_text()
for asset in ['index.css', 'prescript.js', 'postscript.js', 'static/contentIndex.json']:
    original = f'joinSegments(baseDir, "{asset}")'
    if original not in render:
        raise SystemExit(f'Expected resource URL: {asset}')
    render = render.replace(original, original + f' + "?v={revision}"')
render_path.write_text(render)
head_path = quartz / 'quartz/components/Head.tsx'
head = head_path.read_text()
head = head.replace('<meta name="generator" content="Quartz" />', f'<meta name="generator" content="Quartz" /><meta name="site-build" content="{revision}" />')
head_path.write_text(head)
spa_path = quartz / 'quartz/components/scripts/spa.inline.ts'
spa = spa_path.read_text()
needle = '  const html = p.parseFromString(contents, "text/html")'
if needle not in spa:
    raise SystemExit('Expected Quartz navigation parser; review build reload integration.')
spa = spa.replace(needle, needle + """
  const currentBuild = document.querySelector<HTMLMetaElement>('meta[name="site-build"]')?.content
  const nextBuild = html.querySelector<HTMLMetaElement>('meta[name="site-build"]')?.content
  if (currentBuild && nextBuild && currentBuild !== nextBuild) {
    window.location.assign(url)
    return
  }
""")
spa_path.write_text(spa)
print(f'Versioned assets and graph data: {revision}')
