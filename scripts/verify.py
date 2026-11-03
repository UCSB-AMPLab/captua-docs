"""Checks the built site in public/. Standard library only.

Run through `npm test` after `npm run build` or `npm run build:preview`.
Results are written to reports/verification.json.
"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
SECRET = re.compile(r'[?&](?:access_)?(?:token|api_?key|apikey|secret|password|sig|signature)=[^&#"\'\s<]+'
                    r'|\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}', re.I)


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = Counter(); self.links = []; self.images = []; self.lang = None
        self.canon = []; self.alternates = {}; self.titles = []; self.robots = []
        self.h1 = 0; self.stack = []; self.in_title = False; self.main = None; self.main_text = []; self.skip = None
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids[a['id']] += 1
        for key in ('href', 'src'):
            if a.get(key) and not (tag == 'link' and a.get('rel') in ('canonical', 'alternate')):
                self.links.append(a[key])
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'title': self.in_title = True; self.titles.append('')
        if tag == 'meta' and a.get('name') == 'robots': self.robots.append(a.get('content', ''))
        if tag == 'link' and a.get('rel') == 'canonical': self.canon.append(a.get('href'))
        if tag == 'link' and a.get('rel') == 'alternate' and a.get('hreflang'): self.alternates[a['hreflang']] = a['href']
        if tag == 'img': self.images.append(a)
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main = len(self.stack)
        # Text that does not count towards a page's content: its title, breadcrumbs and footer.
        if self.skip is None and (tag in ('h1', 'footer') or 'breadcrumbs' in a.get('class', '').split()): self.skip = len(self.stack)
        if tag not in VOID: self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag not in self.stack: return
        depth = len(self.stack) - 1 - self.stack[::-1].index(tag)
        if self.main is not None and self.main >= depth: self.main = None
        if self.skip is not None and self.skip >= depth: self.skip = None
        self.stack = self.stack[:depth]

    def handle_data(self, data):
        if self.in_title: self.titles[-1] += data
        if self.main is not None and self.skip is None: self.main_text.append(data)


def front_matter(path):
    m = re.match(r'---\n(.*?)\n---\n', path.read_text(), re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(':')
            out[k.strip()] = v.strip().strip('"')
    return out


build = json.loads((ROOT / '.build-result.json').read_text())
preview = build['preview']
base = 'http://127.0.0.1:4006' if preview else 'https://captua.org'
errors = []; checks = 0


def check(ok, msg):
    global checks
    checks += 1
    if not ok: errors.append(msg)


pages = {f.resolve(): Page(f) for f in PUBLIC.rglob('*.html') if 'pagefind' not in f.parts}
check(len(pages) > 0, 'No HTML pages in public/')

for file, p in pages.items():
    rel = str(file.relative_to(PUBLIC))
    route = '/' + rel[:-len('index.html')] if rel.endswith('index.html') else '/' + rel
    check(p.lang in ('en', 'es'), 'Missing or unexpected html lang ' + rel)
    check(len(p.titles) == 1 and p.titles[0].strip(), 'Missing or duplicate <title> ' + rel)
    check(p.h1 == 1, f'{p.h1} H1 elements (expected 1) ' + rel)
    check(all(n == 1 for n in p.ids.values()), 'Duplicate IDs ' + rel + ' ' + str([k for k, n in p.ids.items() if n > 1]))
    check(''.join(p.main_text).strip() != '', 'Empty page ' + rel)
    if rel != '404.html':
        check(p.canon == [base + route], f'Wrong canonical {rel}: {p.canon}')
        if preview: check(any('noindex' in v for v in p.robots), 'Preview page is indexable ' + rel)
    for img in p.images:
        check(bool(img.get('alt', '').strip()), 'Image without alt text ' + rel + ' ' + str(img.get('src')))
    for href in p.links:
        u = urlsplit(href)
        if u.scheme in ('mailto', 'tel'): continue
        if u.scheme or u.netloc:
            if not preview: check('127.0.0.1' not in href and 'localhost' not in u.netloc, 'Local URL in production ' + rel + ' -> ' + href)
            continue
        target = file if not u.path else (PUBLIC / unquote(u.path.lstrip('/')) if u.path.startswith('/') else file.parent / unquote(u.path))
        if target.is_dir() or u.path.endswith('/'): target = target / 'index.html'
        check(target.exists(), 'Broken link ' + rel + ' -> ' + href)
        if u.fragment and target.suffix == '.html' and target.exists():
            other = pages.get(target.resolve())
            check(other is not None and unquote(u.fragment) in other.ids, 'Broken fragment ' + rel + ' -> ' + href)
    check(not SECRET.search(file.read_text()), 'Possible credential in URL ' + rel)

# Sources: credentials and translation pairing.
for f in (ROOT / 'content').rglob('*.md'):
    m = SECRET.search(f.read_text())
    check(not m, f'Possible credential in {f.relative_to(ROOT)}: {m.group(0) if m else ""}')

pending = json.loads((ROOT / 'data/translations_pending.json').read_text())['pending']
en_keys = {}; es_keys = {}
for lang, store in (('en', en_keys), ('es', es_keys)):
    for f in (ROOT / 'content' / lang).rglob('*.md'):
        key = front_matter(f).get('translationKey')
        if key:
            check(key not in store, f'translationKey {key} used twice in content/{lang}')
            store[key] = f.relative_to(ROOT)
for key, f in en_keys.items():
    check(key in es_keys or key in pending, f'No Spanish counterpart and not listed as pending: {key} ({f})')
for key in pending:
    check(key in en_keys, f'Pending translationKey {key} has no English page')
    check(key not in es_keys, f'Pending translationKey {key} already has a Spanish page; remove it from data/translations_pending.json')
check(len(set(pending)) == len(pending), 'Duplicate entries in data/translations_pending.json')

check((PUBLIC / '404.html').exists(), '404 page missing')
check((PUBLIC / 'pagefind/pagefind.js').exists(), 'Search index missing')
check((PUBLIC / 'sitemap.xml').exists(), 'Sitemap missing')
check((PUBLIC / 'CNAME').exists() and (PUBLIC / 'CNAME').read_text().strip() == 'captua.org', 'CNAME missing or wrong')
check(('Disallow: /' in (PUBLIC / 'robots.txt').read_text()) == preview, 'Wrong robots policy')

out = {'checks': checks, 'failures': len(errors), 'preview': preview, 'pages': len(pages),
       'translations_pending': len(pending), 'errors': errors}
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports/verification.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'errors'}))
for e in errors[:50]: print(e, file=sys.stderr)
sys.exit(bool(errors))
