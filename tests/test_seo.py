"""Validate crawlable editions and the actual Pages publication artifact."""
import json
import os
from pathlib import Path
import sys
import unittest
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_seo import book_url, load_site, safe_json

OUTPUT = Path(os.environ.get('SITE_OUTPUT_DIR', str(ROOT)))
if not OUTPUT.is_absolute():
    OUTPUT = ROOT / OUTPUT


class SearchableSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = load_site()
        cls.catalog = json.loads((ROOT / 'data/books.json').read_text())

    def soup(self, relative):
        return BeautifulSoup((OUTPUT / relative).read_text(encoding='utf-8'), 'html.parser')

    def test_home_catalog_is_crawlable_without_javascript(self):
        page = self.soup('index.html')
        links = page.select('#book-grid > a[href]')
        self.assertEqual(len(links), len(self.catalog))
        self.assertEqual({a['href'] for a in links}, {f'./livros/{b["slug"]}/' for b in self.catalog})
        self.assertEqual(page.find('link', rel='canonical')['href'], self.site['url'])
        self.assertNotIn('noindex', page.find('meta', attrs={'name': 'robots'})['content'])
        self.assertEqual(page.select_one('#home-view h2').get_text(' ', strip=True), 'Literatura lusófona, para todos.')

    def test_each_book_has_complete_text_and_unique_search_metadata(self):
        titles, descriptions = [], []
        for meta in self.catalog:
            with self.subTest(book=meta['slug']):
                book = json.loads((ROOT / 'data/books' / meta['slug'] / 'compiled.json').read_text())
                page = self.soup(f'livros/{meta["slug"]}/index.html')
                self.assertEqual(page.html['lang'], self.site['language'])
                self.assertEqual(page.h1.get_text(), book['title'])
                self.assertEqual(len(page.find_all('link', rel='canonical')), 1)
                self.assertEqual(page.find('link', rel='canonical')['href'], book_url(self.site, book['slug']))
                self.assertNotIn('noindex', page.find('meta', attrs={'name': 'robots'})['content'])
                content = page.select('.chapter-text')
                self.assertEqual(len(content), len(book['chapters']))
                for element, chapter in zip(content, book['chapters']):
                    self.assertEqual(element.get_text(), chapter['content'])
                schema = json.loads(page.find('script', type='application/ld+json').string)
                self.assertEqual(schema['@type'], 'Book')
                self.assertEqual(schema['name'], book['title'])
                self.assertTrue(schema['isAccessibleForFree'])
                self.assertEqual(schema['url'], book_url(self.site, book['slug']))
                titles.append(page.title.string)
                descriptions.append(page.find('meta', attrs={'name': 'description'})['content'])
        self.assertEqual(len(titles), len(set(titles)))
        self.assertEqual(len(descriptions), len(set(descriptions)))

    def test_sitemap_contains_only_public_canonical_pages(self):
        root = ET.parse(OUTPUT / 'sitemap.xml').getroot()
        urls = [element.text for element in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        expected = {self.site['url'], urljoin(self.site['url'], 'autores/')} | {book_url(self.site, b['slug']) for b in self.catalog}
        self.assertEqual(set(urls), expected)
        self.assertEqual(len(urls), len(expected))
        self.assertTrue(all(not urlparse(url).query for url in urls))
        self.assertIn(self.site['url'] + 'sitemap.xml', (OUTPUT / 'robots.txt').read_text())

    def test_native_author_links_and_sharing_images_exist(self):
        page = self.soup('autores/index.html')
        urls = {a['href'] for a in page.select('.author-card a')}
        self.assertEqual(urls, {f'../livros/{b["slug"]}/' for b in self.catalog})
        for book in self.catalog:
            with Image.open(OUTPUT / 'assets/share' / f'{book["slug"]}.jpg') as image:
                self.assertEqual(image.format, 'JPEG')
                self.assertGreaterEqual(min(image.size), 200)

    def test_generated_links_and_images_resolve_inside_the_project(self):
        pages = ['index.html', 'autores/index.html'] + [f'livros/{b["slug"]}/index.html' for b in self.catalog]
        for relative in pages:
            page = self.soup(relative)
            for node in page.select('a[href], img[src]'):
                href = node.get('href') or node.get('src')
                if href.startswith(('https://', 'http://', '#')):
                    continue
                absolute = urlparse(urljoin('https://preview.invalid/' + relative, href)).path.lstrip('/')
                target = OUTPUT / absolute
                if target.is_dir():
                    target /= 'index.html'
                self.assertTrue(target.is_file(), f'{relative}: {href}')

    def test_schema_encoding_does_not_close_its_script_element(self):
        text = safe_json({'name': '</script><script>bad()</script>'})
        self.assertNotIn('</script>', text)
        self.assertEqual(json.loads(text)['name'], '</script><script>bad()</script>')

    def test_book_urls_keep_github_pages_project_prefix(self):
        self.assertEqual(book_url(self.site, 'um livro'), self.site['url'] + 'livros/um%20livro/')

    def test_publication_artifact_excludes_project_tools(self):
        if OUTPUT.resolve() == ROOT:
            self.skipTest('Applies to the staged production artifact')
        for name in ['.git', 'node_modules', 'scripts', 'tests', 'design', 'site.json']:
            self.assertFalse((OUTPUT / name).exists(), name)
        self.assertTrue((OUTPUT / '.nojekyll').exists())


if __name__ == '__main__':
    unittest.main()
