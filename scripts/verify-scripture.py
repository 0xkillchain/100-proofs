"""Focused source-integrity and built-link audit. Run after Quartz build."""
from pathlib import Path
from html.parser import HTMLParser
import re
import subprocess
import sys
from scripture import load_books, link_references

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=Path(sys.argv[1]).resolve()
BASE=sys.argv[2] if len(sys.argv)>2 else '28a2569'
books=load_books()
class Anchors(HTMLParser):
    def __init__(self): super().__init__(); self.ids=set(); self.hrefs=[];self.tabs=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.add(a['id'])
        if tag=='a' and a.get('href'):self.hrefs.append(a['href'])
        if a.get('role')=='tab':self.tabs+=1
cache={};total=0;changed=0
for p in sorted(ROOT.glob('[0-9]*.md')):
    text=p.read_text()
    original=subprocess.check_output(['git','show',f'{BASE}:{p.name}'],cwd=ROOT).decode()
    unwrapped=re.sub(r'\[\[Scripture/[^|]+\|([^\]]+)\]\]',r'\1',text)
    assert unwrapped==original, f'Non-link wording changed: {p.name}'
    linked,count=link_references(text,books,int(p.name.split('-')[0]))
    assert linked==text and count==0, f'Unlinked citation: {p.name}'
    slug=p.stem.replace(' ','-')
    page=PUBLIC/(slug+'.html');s=page.read_text();parsed=Anchors();parsed.feed(s)
    assert parsed.tabs==2 and 'explorer-toggle' not in s,p.name
    citations=re.findall(r'\[\[(Scripture/[^|]+)\|([^\]]+)\]\]',text)
    if citations:changed+=1
    article=s.split('<article',1)[1].split('</article>',1)[0]
    article_parser=Anchors();article_parser.feed('<article'+article+'</article>')
    actual=[h for h in article_parser.hrefs if 'Scripture/' in h]
    assert len(actual)==len(citations),(p.name,len(actual),len(citations))
    for target,label in citations:
        doc,_,heading=target.partition('#')
        dest=PUBLIC/(doc+'.html')
        assert dest.exists(),target
        if heading:
            if dest not in cache:
                a=Anchors();a.feed(dest.read_text());cache[dest]=a.ids
            assert heading.lower().replace(' ','-') in cache[dest],target
        total+=1
print(f'PASS: all 100 proofs audited; {total} scripture wikilinks across {changed} proofs; targets and verse anchors exist; two tabs; original wording preserved; conversion idempotent.')
# Relevant-only publishing, graph edges, contents links, and attribution.
import json
index=json.loads((PUBLIC/'static/contentIndex.json').read_text())
expected={'Scripture/index'}
for book,data in books.items():
    bs=book.replace(' ','-')
    expected.add(f'Scripture/{bs}/index')
    expected.update(f'Scripture/{bs}/{c}' for c in data['chapters'])
actual={k for k in index if k.startswith('Scripture/')}
assert actual==expected, ('Unexpected/missing scripture pages', actual ^ expected)
for key in index:
    page=PUBLIC/(key+'.html')
    if not page.exists():continue
    markup=page.read_text()
    assert 'class="page-contents"' in markup, f'Missing top contents: {key}'
    assert markup.index('class="page-contents"') < markup.index('<article'),key
    parsed=Anchors();parsed.feed(markup)
    contents=markup.split('class="page-contents"',1)[1].split('</nav>',1)[0]
    toc=Anchors();toc.feed('<nav '+contents+'</nav>')
    from urllib.parse import unquote
    for href in toc.hrefs:
        assert unquote(href.lstrip('#')) in parsed.ids,(key,href)
for proof in ROOT.glob('[0-9]*.md'):
    key=proof.stem.replace(' ','-')
    references={doc.split('#')[0] for doc in re.findall(r'\[\[(Scripture/[^|]+)\|',proof.read_text())}
    assert references <= set(index[key]['links']), f'Missing scripture graph edges: {key}'
home=(PUBLIC/'index.html').read_text()
assert 'href="https://christogenea.org"' in home
assert '[[42 - Genesis 6|' not in home
assert 'class="graph-window"' in home and 'class="graph-reset"' in home
print(f'PASS: only {len(expected)} relevant scripture library pages; top contents and valid anchors on every content page; scripture graph edges; clickable attribution; graph window controls.')
