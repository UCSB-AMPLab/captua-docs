"""Checks the built site in public/. Standard library only.

Run through `npm test` after `npm run build` or `npm run build:preview`.
Results are written to reports/verification.json.
"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json, re, sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
HEADINGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
# Text inside these does not count as page content.
CHROME = HEADINGS | {'nav', 'aside', 'footer', 'header', 'script', 'style', 'noscript', 'template'}
SECRET = re.compile(r'[?&](?:access_)?(?:token|api_?key|apikey|secret|password|sig|signature)=[^&#"\'\s<]+'
                    r'|\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}', re.I)


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = Counter(); self.links = []; self.images = []; self.lang = None
        self.canon = []; self.alternates = {}; self.titles = []; self.robots = []
        self.h1 = 0; self.stack = []; self.in_title = False; self.main = None; self.article = None
        self.seen_tags = set(); self.main_text = []; self.article_text = []; self.skip = None; self.alt_list = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.seen_tags.add(tag)
        if a.get('id'): self.ids[a['id']] += 1
        for key in ('href', 'src'):
            if a.get(key) and not (tag == 'link' and a.get('rel') in ('canonical', 'alternate')):
                self.links.append(a[key])
        if a.get('srcset'):
            self.links += [c.split()[0] for c in a['srcset'].split(',') if c.strip()]
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'title': self.in_title = True; self.titles.append('')
        if tag == 'meta' and a.get('name') == 'robots': self.robots.append(a.get('content', ''))
        if tag == 'link' and a.get('rel') == 'canonical': self.canon.append(a.get('href'))
        if tag == 'link' and a.get('rel') == 'alternate' and a.get('hreflang'):
            self.alternates[a['hreflang']] = a['href']; self.alt_list.append((a['hreflang'], a['href']))
        if tag == 'img': self.images.append(a)
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main = len(self.stack)
        if tag == 'article' and self.article is None: self.article = len(self.stack)
        # Text that does not count towards a page's content: headings, navigation (breadcrumbs,
        # pagination), the footer, preview labels and anything Pagefind is told to ignore.
        classes = a.get('class', '').split()
        if self.skip is None and (tag in CHROME or 'data-pagefind-ignore' in a
                                  or {'breadcrumbs', 'preview-label', 'guide-pagination'} & set(classes)):
            self.skip = len(self.stack)
        if tag not in VOID: self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag not in self.stack: return
        depth = len(self.stack) - 1 - self.stack[::-1].index(tag)
        if self.main is not None and self.main >= depth: self.main = None
        if self.article is not None and self.article >= depth: self.article = None
        if self.skip is not None and self.skip >= depth: self.skip = None
        self.stack = self.stack[:depth]

    def handle_data(self, data):
        if self.in_title: self.titles[-1] += data
        if self.skip is None:
            if self.main is not None: self.main_text.append(data)
            if self.article is not None: self.article_text.append(data)

    def body_text(self):
        # The article if the page has one, otherwise the whole <main>.
        return ''.join(self.article_text if self.article_seen() else self.main_text)

    def article_seen(self):
        return 'article' in self.seen_tags


def front_matter(path):
    m = re.match(r'---\r?\n(.*?)\r?\n---(?:\r?\n|$)', path.open(encoding='utf-8', newline='').read(), re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(':')
            out[k.strip()] = v.strip().strip('"')
    return out


build = json.loads((ROOT / '.build-result.json').read_text())
preview = build['preview']
base = 'http://127.0.0.1:4006' if preview else 'https://captua.org'
site_url = json.loads((ROOT / 'hugo.json').read_text())['baseURL']
# Hosts whose absolute URLs point at this site and are checked like relative links.
OWN_HOSTS = {urlsplit(site_url).netloc, 'www.' + urlsplit(site_url).netloc, urlsplit(base).netloc}
errors = []; checks = 0


def check(ok, msg):
    global checks
    checks += 1
    if not ok: errors.append(msg)


def to_file(path):
    """The built file a URL path points at."""
    target = PUBLIC / unquote(path.lstrip('/'))
    return target / 'index.html' if target.is_dir() or path.endswith('/') or not path else target


def own_path(href):
    """The path of an own-site URL, or None when the URL is external."""
    u = urlsplit(href)
    return u.path or '/' if u.netloc in OWN_HOSTS and u.scheme in ('http', 'https') else None


pages = {f.resolve(): Page(f) for f in PUBLIC.rglob('*.html') if 'pagefind' not in f.parts}
check(len(pages) > 0, 'No HTML pages in public/')


def route_of(file):
    rel = str(file.relative_to(PUBLIC))
    return '/' + rel[:-len('index.html')] if rel.endswith('index.html') else '/' + rel


routes = {route_of(f): p for f, p in pages.items()}
# Preview builds are noindex throughout, so only production separates indexable pages from the rest.
indexable = {r for r, p in routes.items() if r != '/404.html' and (preview or not any('noindex' in v for v in p.robots))}

for file, p in pages.items():
    rel = str(file.relative_to(PUBLIC))
    route = route_of(file)
    check(p.lang in ('en', 'es'), 'Missing or unexpected html lang ' + rel)
    check(len(p.titles) == 1 and p.titles[0].strip(), 'Missing or duplicate <title> ' + rel)
    check(p.h1 == 1, f'{p.h1} H1 elements (expected 1) ' + rel)
    check(all(n == 1 for n in p.ids.values()), 'Duplicate IDs ' + rel + ' ' + str([k for k, n in p.ids.items() if n > 1]))
    check(re.search(r'\w', p.body_text()) is not None, 'Empty page (no body text besides headings and navigation) ' + rel)
    # The 404 page is the one page that legitimately stays out of the index.
    if not preview and rel != '404.html': check(not any('noindex' in v for v in p.robots), 'Production page carries noindex ' + rel)
    if rel != '404.html':
        check(p.canon == [base + route], f'Wrong canonical {rel}: {p.canon}')
        if preview: check(any('noindex' in v for v in p.robots), 'Preview page is indexable ' + rel)
        # hreflang: a self-reference, every alternate built, and every pair reciprocal.
        check(any(own_path(h) == route for _, h in p.alt_list), 'No self-referencing hreflang alternate ' + rel)
        for lang, href in p.alt_list:
            path = own_path(href)
            target = routes.get(path) if path is not None else None
            check(target is not None, f'hreflang {lang} alternate does not resolve to a built page {rel} -> {href}')
            if target is not None and path != route and lang != 'x-default':
                check(any(own_path(h) == route for _, h in target.alt_list),
                      f'hreflang alternate is not reciprocal {rel} -> {href}')
    for img in p.images:
        check(bool(img.get('alt', '').strip()), 'Image without alt text ' + rel + ' ' + str(img.get('src')))
    for href in p.links:
        u = urlsplit(href)
        if u.scheme in ('mailto', 'tel'): continue
        path = own_path(href)
        if path is None and (u.scheme or u.netloc):
            if not preview: check('127.0.0.1' not in href and 'localhost' not in u.netloc, 'Local URL in production ' + rel + ' -> ' + href)
            continue
        if path is not None: target = to_file(path)
        elif not u.path: target = file
        elif u.path.startswith('/'): target = to_file(u.path)
        else:
            target = file.parent / unquote(u.path)
            if target.is_dir() or u.path.endswith('/'): target = target / 'index.html'
        check(target.exists(), 'Broken link ' + rel + ' -> ' + href)
        if u.fragment and target.suffix == '.html' and target.exists():
            other = pages.get(target.resolve())
            check(other is not None and unquote(u.fragment) in other.ids, 'Broken fragment ' + rel + ' -> ' + href)
    check(not SECRET.search(file.read_text()), 'Possible credential in URL ' + rel)

# Files that built CSS refers to with url(...).
for css in PUBLIC.rglob('*.css'):
    for ref in re.findall(r'url\(\s*([\'"]?)(.*?)\1\s*\)', css.read_text()):
        ref = ref[1].strip()
        u = urlsplit(ref)
        if not ref or u.scheme in ('data', 'about') or (u.scheme or u.netloc) and own_path(ref) is None: continue
        if own_path(ref) is not None: target = to_file(own_path(ref))
        elif ref.startswith('#'): continue
        elif u.path.startswith('/'): target = to_file(u.path)
        else: target = css.parent / unquote(u.path)
        check(target.exists(), f'Missing file referenced from {css.relative_to(PUBLIC)}: {ref}')

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
# Pagefind: the entry file parses and the index files it points to exist.
try:
    entry = json.loads((PUBLIC / 'pagefind/pagefind-entry.json').read_text())
    langs = entry.get('languages') or {}
    check(bool(langs), 'pagefind-entry.json lists no languages')
    for lang, info in langs.items():
        check((PUBLIC / f"pagefind/pagefind.{info.get('hash')}.pf_meta").exists(), f'Pagefind metadata file missing for {lang}')
        for part, ext in (('index', 'pf_index'), ('fragment', 'pf_fragment')):
            check(any((PUBLIC / 'pagefind' / part).glob(f'{lang}_*.{ext}')), f'No Pagefind {part} files for {lang}')
except (OSError, ValueError, AttributeError) as e:
    check(False, f'pagefind-entry.json missing or unreadable: {e}')
# Sitemap: every indexable page is listed and every listed URL is a built page.
check((PUBLIC / 'sitemap.xml').exists(), 'Sitemap missing')
try:
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    locs = [e.text.strip() for e in ET.parse(PUBLIC / 'sitemap.xml').getroot().findall('s:url/s:loc', ns) if e.text]
    check(bool(locs), 'Sitemap lists no URLs')
    listed = set()
    for loc in locs:
        path = own_path(loc)
        check(loc.startswith(base + '/') and path in routes, f'Sitemap URL does not resolve to a built page: {loc}')
        listed.add(path)
    for r in sorted(indexable - listed): check(False, f'Page missing from sitemap: {r}')
    for r in sorted(listed & {'/404.html'}): check(False, 'Sitemap lists the 404 page')
    for r in sorted(listed - indexable - {'/404.html'}): check(r not in routes, f'Sitemap lists a noindex page: {r}')
except (OSError, ET.ParseError) as e:
    check(False, f'sitemap.xml unreadable: {e}')
# Migration manifest: every expected page is built and is not a draft.
drafts = {front_matter(f).get('translationKey') for f in (ROOT / 'content' / 'en').rglob('*.md') if front_matter(f).get('draft') == 'true'}
for entry in json.loads((ROOT / 'migration/sources.json').read_text())['pages']:
    check(entry['url'] in routes, f"Expected page not built: {entry['url']}")
    check(entry.get('translationKey') not in drafts, f"Expected page is a draft: {entry['url']}")
check((PUBLIC / 'CNAME').exists() and (PUBLIC / 'CNAME').read_text().strip() == 'captua.org', 'CNAME missing or wrong')
check(('Disallow: /' in (PUBLIC / 'robots.txt').read_text()) == preview, 'Wrong robots policy')

out = {'checks': checks, 'failures': len(errors), 'preview': preview, 'pages': len(pages),
       'translations_pending': len(pending), 'errors': errors}
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports/verification.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'errors'}))
for e in errors[:50]: print(e, file=sys.stderr)
sys.exit(bool(errors))
