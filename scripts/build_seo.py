#!/usr/bin/env python3
"""Build crawlable book pages, metadata, sitemap, and a Pages artifact.

The interactive reader remains available at the existing query URLs. The
canonical, complete HTML editions also work without JavaScript.
"""
import argparse
from collections import OrderedDict
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import quote, urljoin, urlparse
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def safe_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def load_site():
    site = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
    parsed = urlparse(site['url'])
    if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError('site.json url must be an absolute HTTPS site root.')
    site['url'] = site['url'].rstrip('/') + '/'
    return site


def book_url(site, slug):
    return urljoin(site['url'], f'livros/{quote(slug, safe="")}/')


def author_names(book):
    if book['slug'] == 'o-misterio-da-estrada-de-sintra':
        return ['Eça de Queirós', 'Ramalho Ortigão']
    return [book['author']]


def creator_schema(site):
    creator = site['creator']
    return {
        '@type': 'Person', 'name': creator['name'], 'url': creator['url'],
        'sameAs': creator.get('sameAs', []),
    }


def book_schema(site, book):
    url = book_url(site, book['slug'])
    return {
        '@context': 'https://schema.org', '@type': 'Book', '@id': url + '#livro',
        'url': url, 'name': book['title'], 'description': book['description'],
        'author': [{'@type': 'Person', 'name': name} for name in author_names(book)],
        'inLanguage': site['language'], 'datePublished': str(book['year']),
        'genre': book.get('tags', []), 'isAccessibleForFree': True,
        'bookFormat': 'https://schema.org/EBook',
        'publisher': {'@type': 'Organization', 'name': site['name'], 'url': site['url']},
        'creator': creator_schema(site),
        'image': urljoin(site['url'], book['coverImage'].removeprefix('./')),
        'encoding': {'@type': 'MediaObject', 'encodingFormat': 'application/pdf',
                     'contentUrl': urljoin(site['url'], f'data/books/{book["slug"]}/compiled.pdf')},
        'isBasedOn': book.get('source', {}).get('url'),
    }


def head(site, title, description, canonical, image, schema, *, kind='website', image_size=None):
    attrs = [
        ('name', 'description', description), ('name', 'author', site['creator']['name']),
        ('name', 'creator', site['creator']['name']),
        ('name', 'robots', 'index, follow, max-image-preview:large'),
        ('name', 'theme-color', '#fcfcf9'),
        ('property', 'og:site_name', site['name']), ('property', 'og:title', title),
        ('property', 'og:description', description), ('property', 'og:type', kind),
        ('property', 'og:locale', site['locale']), ('property', 'og:url', canonical),
        ('property', 'og:image', image), ('property', 'og:image:alt', ('Capa ilustrada de ' + title.split(' | ')[0]) if kind == 'book' else 'Capas de Os Lusíadas, Mensagem e Os Maias, em desenho a grafite.'),
        ('name', 'twitter:card', 'summary_large_image' if kind == 'website' else 'summary'),
        ('name', 'twitter:title', title), ('name', 'twitter:description', description),
        ('name', 'twitter:image', image), ('name', 'twitter:image:alt', ('Capa ilustrada de ' + title.split(' | ')[0]) if kind == 'book' else 'Capas de Os Lusíadas, Mensagem e Os Maias, em desenho a grafite.'),
    ]
    if image_size:
        attrs += [('property', 'og:image:width', str(image_size[0])),
                  ('property', 'og:image:height', str(image_size[1]))]
    tags = [f'<title>{escape(title)}</title>']
    tags += [f'<meta {attr}="{key}" content="{escape(value, quote=True)}">' for attr, key, value in attrs]
    tags += [f'<link rel="canonical" href="{escape(canonical, quote=True)}">',
             f'<link rel="sitemap" type="application/xml" href="{site["url"]}sitemap.xml">',
             f'<script type="application/ld+json">{safe_json(schema)}</script>']
    return '\n    '.join(tags)


def catalog_card(book):
    esc = lambda value: escape(str(value), quote=True)
    return f'''<a href="./livros/{quote(book['slug'], safe='')}/" class="book-card block group w-full text-left" onclick="handleBookLink(event, {int(book['id'])})" aria-label="Ler {esc(book['title'])}">
    <div class="aspect-[3/4] relative overflow-hidden border border-gray-100 bg-[#f6f2e9] mb-5 transition-all group-hover:shadow-md group-hover:border-gray-200">
        <img src="{esc(book['coverImage'])}" alt="Capa de {esc(book['title'])}" loading="lazy" decoding="async" class="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]">
    </div>
    <p class="text-[10px] tracking-[0.25em] text-gray-400 uppercase mb-2">{esc(book['year'])}</p>
    <h3 class="serif text-2xl text-gray-900 mb-2">{esc(book['title'])}</h3>
    <p class="text-xs tracking-widest text-gray-500 uppercase mb-3">{esc(book['author'])}</p>
    <p class="text-sm text-gray-500 leading-relaxed">{esc(book['description'])}</p>
</a>'''


STATIC_CSS = '''
:root{color-scheme:light}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fcfcf9;color:#1a1a1a;font:16px/1.65 Inter,system-ui,sans-serif}a{color:inherit;text-underline-offset:.22em}a:hover{color:#555}a:focus-visible,summary:focus-visible{outline:2px solid #555;outline-offset:5px}h1,h2,h3,.brand{font-family:Georgia,serif;font-weight:400;line-height:1.25}h1{font-size:clamp(2rem,5vw,3rem);margin:.35em 0}h2{font-size:1.6rem}h3{font-size:1.2rem}header.site-header{max-width:1152px;margin:auto;padding:32px 24px;display:flex;justify-content:space-between;gap:24px;align-items:center;border-bottom:1px solid #eee}.brand{font-size:24px;text-decoration:none}.site-header nav{display:flex;gap:24px;font-size:13px}main{max-width:1000px;padding:40px 24px 64px;margin:auto}.breadcrumb{font-size:13px;color:#777}.book-heading{display:grid;grid-template-columns:160px 1fr;gap:40px;margin:36px 0}.cover{display:block;width:160px;aspect-ratio:3/4;object-fit:cover;border:1px solid #eee}.author,.muted{color:#666}.actions{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.action{display:inline-block;border:1px solid #ddd;border-radius:30px;padding:10px 18px;font-size:14px;text-decoration:none}.primary{background:#1a1a1a;color:white;border-color:#1a1a1a}.primary:hover{background:#333;color:white}.reading{max-width:720px;margin:48px auto}.contents{padding:24px;background:#f4f4f1}.contents ol{padding-left:22px}.contents li{margin:5px 0}.chapter{border-top:1px solid #e8e8e3;padding:20px 0;scroll-margin-top:24px}.chapter>summary{cursor:pointer;font-family:Georgia,serif;font-size:22px}.chapter-text{font-family:Georgia,serif;font-size:18px;line-height:1.85;white-space:pre-line;overflow-wrap:break-word;margin-top:24px}.context{font-size:14px;background:#f4f4f1;padding:20px;color:#555}.notes{font-size:14px;margin-top:24px}.notes li{margin:12px 0}.source{font-size:14px;color:#666;border-top:1px solid #eee;padding-top:24px;overflow-wrap:anywhere}.author-card{border-top:1px solid #eee;padding:24px 0}.author-card li{margin:14px 0}.author-card small{display:block;color:#777}footer{border-top:1px solid #eee;text-align:center;color:#777;font-size:12px;padding:32px 24px}.skip{position:absolute;left:-10000px}.skip:focus{left:16px;top:16px;background:#fff;padding:8px}@media(max-width:600px){header.site-header{align-items:flex-start;flex-direction:column}.book-heading{grid-template-columns:100px 1fr;gap:20px}.cover{width:100px}.actions{grid-column:1/-1}.chapter-text{font-size:17px}}
'''


def page_shell(site, metadata, body, root_prefix):
    return f'''<!DOCTYPE html>
<html lang="{site['language']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    {metadata}
    <link rel="icon" href="{root_prefix}favicon.svg" type="image/svg+xml">
    <style>{STATIC_CSS}</style>
</head><body><a class="skip" href="#conteudo">Saltar para o conteúdo</a>
<header class="site-header"><a class="brand" href="{root_prefix}">Biblioteca Pública</a><nav aria-label="Navegação principal"><a href="{root_prefix}">Colecção</a><a href="{root_prefix}autores/">Autores</a></nav></header>
<main id="conteudo">{body}</main>
<footer>Literatura lusófona, para todos. · Criado por <a href="{escape(site['creator']['url'], quote=True)}" rel="author me">{escape(site['creator']['name'])}</a> · <a href="{root_prefix}sitemap.xml">Mapa do site</a></footer>
<script>function openChapter(){{if(!location.hash)return;const el=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(el&&el.tagName==='DETAILS')el.open=true;}}openChapter();addEventListener('hashchange',openChapter);</script>
</body></html>'''


def book_page(site, book, share_size):
    url = book_url(site, book['slug'])
    description = f'{book["title"]}, de {book["author"]}: leitura online gratuita, contexto, notas e PDF. {book["description"]}'
    if len(description) > 160:
        description = description[:157].rsplit(' ', 1)[0] + '…'
    metadata = head(site, f'{book["title"]} — {book["author"]} | Biblioteca Pública', description, url,
                    urljoin(site['url'], f'assets/share/{book["slug"]}.jpg'), book_schema(site, book), kind='book', image_size=share_size)
    prefix = '../../'
    title, author = escape(book['title']), escape(book['author'])
    body = f'''<p class="breadcrumb"><a href="../../">Colecção</a> / {title}</p>
<section class="book-heading"><img class="cover" src="{prefix}{escape(book['coverImage'].removeprefix('./'), quote=True)}" alt="Capa ilustrada de {title}" width="160" height="213">
<div><p class="muted">{escape(str(book['year']))} · Literatura em português</p><h1>{title}</h1><p class="author">{author}</p><p>{escape(book['description'])}</p>
<div class="actions"><a class="action primary" href="../../?livro={quote(book['slug'], safe='')}&amp;capitulo=1">Abrir leitor com notas</a><a class="action" href="../../data/books/{book['slug']}/compiled.pdf" download>Descarregar PDF</a></div></div></section>
<div class="reading"><nav class="contents" aria-label="Índice do livro"><details><summary>Índice — {len(book['chapters'])} secções</summary><ol>'''
    for index, chapter in enumerate(book['chapters'], 1):
        body += f'<li><a href="#capitulo-{index}">{escape(chapter["title"])}</a></li>'
    body += '</ol></details></nav><h2>Texto e notas de leitura</h2>'
    for index, chapter in enumerate(book['chapters'], 1):
        body += f'<details class="chapter" id="capitulo-{index}"{" open" if index == 1 else ""}><summary>{escape(chapter["title"])}</summary>'
        if chapter.get('context'):
            body += f'<p class="context">{escape(chapter["context"])}</p>'
        body += f'<div class="chapter-text">{escape(chapter.get("content", ""))}</div>'
        notes = chapter.get('annotations') or []
        if notes:
            body += '<details class="notes" open><summary>Notas de leitura</summary><ul>'
            for note in notes:
                body += f'<li><strong>{escape(note["target"])}</strong>: {escape(note["text"])}</li>'
            body += '</ul></details>'
        body += '</details>'
    source = book.get('source') or {}
    body += '<section class="source"><h2>Edição de referência</h2>'
    source_url = source.get('url', '')
    if urlparse(source_url).scheme == 'https':
        body += f'<p><a href="{escape(source_url, quote=True)}" rel="external">{escape(source.get("title", "Fonte do texto"))}</a></p>'
    for field in ['transcription', 'editorialNote']:
        if source.get(field):
            body += f'<p>{escape(source[field])}</p>'
    if book['slug'] == 'mensagem':
        body += '<p>Transcrição: <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.pt">Creative Commons Atribuição-PartilhaIgual 4.0</a>. A organização e as notas de leitura são editoriais do projecto.</p>'
    body += '</section></div>'
    return page_shell(site, metadata, body, prefix)


def authors_page(site, books, home_image, home_size):
    url = urljoin(site['url'], 'autores/')
    title = 'Autores e obras de literatura lusófona | Biblioteca Pública'
    description = 'Conheça os autores da Biblioteca Pública e encontre os seus clássicos em domínio público, com leitura gratuita, notas e edições PDF.'
    schema = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'url': url, 'name': title,
              'inLanguage': site['language'], 'creator': creator_schema(site),
              'mainEntity': {'@type': 'ItemList', 'itemListElement': [
                  {'@type': 'ListItem', 'position': i, 'url': book_url(site, b['slug']), 'name': b['title']} for i, b in enumerate(books, 1)]}}
    metadata = head(site, title, description, url, home_image, schema, image_size=home_size)
    groups = OrderedDict()
    for book in books:
        groups.setdefault(book.get('authorId') or book['author'], []).append(book)
    body = '<h1>Autores e obras</h1><p>As vozes da literatura lusófona presentes na colecção.</p>'
    for works in groups.values():
        author = works[0]
        body += f'<section class="author-card"><h2>{escape(author["author"])}</h2><p>{escape(author.get("authorBio", ""))}</p><ul>'
        for book in works:
            body += f'<li><a href="../livros/{book["slug"]}/">{escape(book["title"])}</a><small>{escape(str(book["year"]))} · {escape(book["description"])}</small></li>'
        body += '</ul></section>'
    return page_shell(site, metadata, body, '../')


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def build(output):
    site = load_site()
    catalog = json.loads((ROOT / 'data/books.json').read_text(encoding='utf-8'))
    books = [json.loads((ROOT / 'data/books' / b['slug'] / 'compiled.json').read_text(encoding='utf-8')) for b in catalog]
    output.mkdir(parents=True, exist_ok=True)
    if output != ROOT:
        for folder in ['assets', 'data']:
            shutil.copytree(ROOT / folder, output / folder, dirs_exist_ok=True)
        for name in ['favicon.svg', 'LICENSE']:
            shutil.copy2(ROOT / name, output / name)
    share = output / 'assets/share'
    share.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for book in books:
        with Image.open(ROOT / book['coverImage'].removeprefix('./')) as image:
            image = image.convert('RGB')
            image.thumbnail((800, 1067))
            # Keep the Pages build bounded on the macOS/Python image stack;
            # the source covers are already small and the quality setting is
            # sufficient for social previews.
            image.save(share / f'{book["slug"]}.jpg', 'JPEG', quality=85)
            sizes[book['slug']] = image.size
    shutil.copy2(ROOT / 'design/cover-sketch-preview.png', share / 'coleccao.png')
    with Image.open(share / 'coleccao.png') as image:
        home_size = image.size
    home_image = urljoin(site['url'], 'assets/share/coleccao.png')
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', '@id': site['url'] + '#website', 'url': site['url'], 'name': site['name'], 'inLanguage': site['language'],
         'creator': creator_schema(site), 'publisher': creator_schema(site)},
        {'@type': 'CollectionPage', '@id': site['url'] + '#coleccao', 'url': site['url'], 'name': site['title'],
         'description': site['description'], 'inLanguage': site['language'], 'creator': creator_schema(site),
         'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(books), 'itemListElement': [
             {'@type': 'ListItem', 'position': i, 'url': book_url(site, b['slug']), 'name': b['title']} for i, b in enumerate(books, 1)]}}]}
    metadata = head(site, site['title'], site['description'], site['url'], home_image, schema, image_size=home_size)
    # The query-based reader and author view are utility views; canonical HTML
    # editions and the static author catalogue are the searchable entry points.
    metadata += '''\n    <script>if(new URLSearchParams(location.search).has('livro')||new URLSearchParams(location.search).has('book')||new URLSearchParams(location.search).get('view')==='authors'){document.querySelector('meta[name="robots"]').content='noindex, follow';document.querySelector('link[rel="canonical"]').remove();}</script>'''
    template = (ROOT / 'index.html').read_text(encoding='utf-8')
    template, count = re.subn(r'<!-- SEO:START -->.*?<!-- SEO:END -->', lambda _: '<!-- SEO:START -->\n    ' + metadata + '\n    <!-- SEO:END -->', template, flags=re.S)
    if count != 1:
        raise ValueError('index.html must contain one SEO marker pair')
    cards = '\n'.join(catalog_card(book) for book in books)
    template, count = re.subn(r'<!-- CATALOG:START -->.*?<!-- CATALOG:END -->', lambda _: '<!-- CATALOG:START -->\n' + cards + '\n                    <!-- CATALOG:END -->', template, flags=re.S)
    if count != 1:
        raise ValueError('index.html must contain one catalog marker pair')
    write(output / 'index.html', template)
    for book in books:
        write(output / 'livros' / book['slug'] / 'index.html', book_page(site, book, sizes[book['slug']]))
    write(output / 'autores/index.html', authors_page(site, books, home_image, home_size))
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    sitemap = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for url in [site['url'], urljoin(site['url'], 'autores/')] + [book_url(site, book['slug']) for book in books]:
        entry = ET.SubElement(sitemap, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        ET.SubElement(entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text = url
    ET.ElementTree(sitemap).write(output / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    write(output / 'robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {site["url"]}sitemap.xml\n')
    write(output / '.nojekyll', '')
    print(f'Built {len(books)} complete HTML book pages, author catalogue, metadata and sitemap in {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    build(args.output_dir.resolve())


if __name__ == '__main__':
    main()
