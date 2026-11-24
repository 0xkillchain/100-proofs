"""Build a local scripture library and link citations without changing quoted wording."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'site/data/scripture.json'

def load_books():
    return json.loads(DATA.read_text())

def slug(book):
    return book.replace(' ', '-')

def target(book, chapter=None, verse=None):
    path = f'Scripture/{slug(book)}/' + (str(chapter) if chapter else 'index')
    return path + (f'#Verse {verse}' if verse else '')

def url(book, chapter=None):
    return '/100-proofs/' + target(book, chapter).replace('/index', '/')

def patterns(books):
    aliases = {b: b for b in books}
    aliases.update({'Psalm': 'Psalms', 'Revelation of John': 'Revelation', 'Wisdom of Solomon': 'Wisdom', 'Ecclesiasticus': 'Sirach'})
    names = '|'.join(re.escape(x) for x in sorted(aliases, key=len, reverse=True))
    pattern = re.compile(r'(?<![\w])(?P<book>' + names + r')\s+(?P<chapter>\d{1,3})(?P<tail>(?::\d{1,3}(?:\s*[-–]\s*\d{1,3})?(?:,\s*\d{1,3}(?:\s*[-–]\s*\d{1,3})?)*)|(?:\s*[-–]\s*\d{1,3}))?(?!\d)')
    return aliases, pattern

PROTECTED = re.compile(r'\[\[[\s\S]*?\]\]|```[\s\S]*?```|`[^`\n]+`|\[[^\]\n]*\]\([^\)\n]*\)|https?://[^\s<>]+')

def link_references(text, books, proof_number=None):
    aliases, pattern = patterns(books)
    count = 0
    def convert(match):
        nonlocal count
        label = match[0]
        book = aliases[match['book']]
        chapter = int(match['chapter'])
        tail = match['tail'] or ''
        verse = int(re.match(r':(\d+)', tail)[1]) if tail.startswith(':') else None
        if book in {'Obadiah', 'Philemon', '2 John', '3 John', 'Jude', 'Prayer of Manasses', 'Susanna', 'Bel and the Dragon'} and verse is None:
            verse, chapter = chapter, 1
        chapters = books[book]['chapters']
        if str(chapter) not in chapters:
            raise ValueError(f'Invalid chapter: {label}')
        if not books[book].get('excerpts'):
            nums = [int(n) for n in re.findall(r'\d+', tail)]
            if verse is not None:
                nums = nums if tail.startswith(':') else [verse] + nums
                if any(n < 1 or str(n) not in chapters[str(chapter)] for n in nums):
                    raise ValueError(f'Invalid verse: {label}')
            elif nums and any(str(n) not in chapters for n in nums):
                raise ValueError(f'Invalid chapter range: {label}')
        count += 1
        return '[[' + target(book, chapter, verse) + '|' + label + ']]'
    parts = []; pos = 0
    for match in PROTECTED.finditer(text):
        parts += [pattern.sub(convert, text[pos:match.start()]), match[0]]
        pos = match.end()
    parts.append(pattern.sub(convert, text[pos:]))
    linked = ''.join(parts)
    # These abbreviated references have explicit, unambiguous book context in the proofs.
    shorthand = {2: {49: 'Genesis', 33: 'Deuteronomy'}, 18: {49: 'Genesis'}, 19: {33: 'Deuteronomy'}, 40: {4: 'Genesis'}, 50: {1: 'James', 2: 'James'}}.get(proof_number, {})
    if shorthand:
        def bare(m):
            nonlocal count
            chapter, verse = int(m[1]), int(m[2])
            if chapter not in shorthand: return m[0]
            count += 1
            return f'[[{target(shorthand[chapter], chapter, verse)}|{m[0]}]]'
        parts=[];pos=0
        for match in PROTECTED.finditer(linked):
            parts += [re.sub(r'(?<![\w:])([0-9]+):([0-9]+)(?:[-–][0-9]+)?', bare, linked[pos:match.start()]),match[0]];pos=match.end()
        parts.append(re.sub(r'(?<![\w:])([0-9]+):([0-9]+)(?:[-–][0-9]+)?', bare, linked[pos:]))
        linked=''.join(parts)
    return linked, count

def frontmatter(title, **fields):
    fields={'title':title,'socialImage':'https://0xkillchain.github.io/100-proofs/static/og-image.png',**fields}
    return '---\n'+'\n'.join(f'{k}: {json.dumps(v, ensure_ascii=False)}' for k,v in fields.items())+'\n---\n\n'

def generate(content):
    books=load_books(); root=content/'Scripture';root.mkdir()
    library=[]
    for order,(book,data) in enumerate(books.items()):
        folder=root/slug(book);folder.mkdir()
        chapters=data['chapters']; edition=data['edition']
        library.append(f'- [[{target(book)}|{book}]]')
        links='\n'.join(f'<a href="{url(book,c)}">{c}</a>' for c in chapters)
        (folder/'index.md').write_text(frontmatter(book,scriptureBookIndex=True,book=book,bookOrder=order)+'## Cited chapters\n\nSelect a chapter containing passages cited by the proofs.\n\n'+f'*{edition}*\n\n<div class="scripture-chapters">\n{links}\n</div>\n')
        for chapter,verses in chapters.items():
            chapter=int(chapter)
            options=''.join(f'<option value="{url(b,1 if "1" in d["chapters"] else next(iter(d["chapters"])))}"'+(' selected' if b==book else '')+f'>{html.escape(b)}</option>' for b,d in books.items())
            chapter_options=''.join(f'<option value="{url(book,c)}"'+(' selected' if int(c)==chapter else '')+f'>{c}</option>' for c in chapters)
            controls=f'<nav class="scripture-controls" aria-label="Scripture reader"><label>Book<select aria-label="Book">{options}</select></label><label>Chapter<select aria-label="Chapter">{chapter_options}</select></label></nav>\n\n'
            lines=[]
            groups=[]
            for key in verses:
                first,*last=map(int,key.split('-'))
                end=last[0] if last else first
                if groups and first == groups[-1][1]+1: groups[-1][1]=end
                else: groups.append([first,end])
            group_titles={first: (f'Verse {first}' if first==end else f'Verses {first}–{end}') for first,end in groups}
            for verse,text in verses.items():
                label=verse
                anchor=verse.split('-')[0]
                if int(anchor) in group_titles:
                    lines.append(f'<h2 id="passage-{anchor}">{group_titles[int(anchor)]}</h2>')
                if text is None:
                    lines.append(f'<p id="verse-{anchor}">Verse {label} is referenced in the notes; its text is unavailable in this excerpt collection.</p>')
                else:
                    lines.append(f'<p id="verse-{anchor}"><sup>{label}</sup> {html.escape(text)}</p>')
            nav=[]; keys=list(chapters);i=keys.index(str(chapter))
            if i>0: nav.append(f'[[{target(book,keys[i-1])}|← Previous cited chapter]]')
            if i+1<len(keys):nav.append(f'[[{target(book,keys[i+1])}|Next cited chapter →]]')
            body=frontmatter(f'{book} {chapter}',book=book,chapter=chapter,passageSections=[{'text':title,'slug':f'passage-{first}','depth':0} for first,title in group_titles.items()])+f'*{edition}*\n\n'+controls+'<div class="scripture-verses">\n'+'\n'.join(lines)+'\n</div>\n\n'+' · '.join(nav)+'\n\n'+f'[Text source]({data["source"]})\n'
            (folder/f'{chapter}.md').write_text(body)
    (root/'index.md').write_text(frontmatter('Scripture')+'Only scripture cited by the proofs is included. Bible text uses the King James Version; Apocrypha and source excerpts are labeled separately.\n\n## Cited books\n\n'+'\n'.join(library)+'\n')
    return {str(p.relative_to(content).with_suffix('')) for p in root.rglob('*.md')}

if __name__ == '__main__':
    books=load_books();total=0
    for p in ROOT.glob('[0-9]*.md'):
        linked,count=link_references(p.read_text(),books,int(p.name.split('-')[0]))
        p.write_text(linked);total+=count
    print(f'Linked {total} scripture citations.')
