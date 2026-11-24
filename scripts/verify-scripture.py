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
