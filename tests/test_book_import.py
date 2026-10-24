"""Offline regression checks for edition boundaries and faithful text layout."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_more_classics as importer
from build_pdfs import format_block


class EditionImportTests(unittest.TestCase):
    def test_nested_chapters_exclude_index_and_legacy_footer(self):
        html = '''<body><header>catalog header</header><div>
        <h2>I</h2>Primeiro capítulo.<br/><br/>Última frase do primeiro.
        <div><h2>II</h2>Segundo capítulo.<br/><br/>Fim da narrativa.</div>
        End of Project Gutenberg's Example
        <footer id="pg-footer">Modern licence</footer></div></body>'''
        soup = BeautifulSoup(html, 'html.parser')
        _, chapters = importer.pieces(soup, soup.find_all('h2'), soup.find(id='pg-footer'))
        self.assertEqual(len(chapters), 2)
        self.assertIn('Última frase do primeiro.', chapters[0])
        self.assertNotIn('Segundo capítulo', chapters[0])
        self.assertTrue(chapters[1].endswith('Fim da narrativa.'))
        self.assertNotIn('Gutenberg', ''.join(chapters))
        self.assertNotIn('catalog header', ''.join(chapters))

    def test_prose_reflows_wrapping_without_dropping_numbered_sections(self):
        soup = BeautifulSoup('<body><h3>1</h3>Primeira linha<br/>continua aqui.<br/><br/><h3>2</h3>Outro parágrafo.</body>', 'html.parser')
        text = importer.prose(importer.serialise(soup))
        self.assertIn('Primeira linha continua aqui.', text)
        self.assertIn('1\n\n', text)
        self.assertIn('\n\n2\n\n', text)

    def test_embedded_verse_keeps_line_and_stanza_breaks(self):
        soup = BeautifulSoup('<body><p>Prosa que não<br/>deve perder a quebra.</p><div class="poetry">Verso A<br/>Verso B<br/><br/>Verso C</div></body>', 'html.parser')
        text = importer.prose(importer.serialise(soup))
        self.assertIn('Prosa que não\ndeve perder a quebra.', text)
        self.assertIn('Verso A\nVerso B\n\nVerso C', text)
        self.assertFalse(any(0xe000 <= ord(char) <= 0xf8ff for char in text))

    def test_inline_emphasis_does_not_split_words(self):
        soup = BeautifulSoup('<body><p>servo de <em>Deus</em> e servi<strong>ço</strong>.</p></body>', 'html.parser')
        self.assertEqual(importer.prose(importer.serialise(soup)), 'servo de Deus e serviço.')

    def test_source_removes_printed_page_numbers(self):
        with TemporaryDirectory() as directory:
            Path(directory, 'example.html').write_text('<body><h2>I</h2>Uma <span class="pagenum">[12]</span>frase.</body>')
            with patch.object(importer, 'SOURCE_DIR', Path(directory)):
                soup = importer.source('example')
        self.assertEqual(importer.prose(importer.serialise(soup)), 'I\n\nUma frase.')

    def test_poetry_book_keeps_all_verse_breaks(self):
        soup = BeautifulSoup('<body><p>Um verso,<br/>outro verso.</p><p>Outra estrofe.</p></body>', 'html.parser')
        text = importer.poetry_text(importer.serialise(soup))
        self.assertEqual(text, 'Um verso,\noutro verso.\n\nOutra estrofe.')

    def test_source_title_markup_is_cleaned_before_punctuation(self):
        tag = BeautifulSoup('<p>*Pobre Tysica*!</p>', 'html.parser').p
        self.assertEqual(importer.title_text(tag), 'Pobre Tysica!')

    def test_transcription_superscripts_become_readable_inline_text(self):
        soup = BeautifulSoup('<body><p>S.^{ta} Iria e V. Ex.^{a}</p></body>', 'html.parser')
        self.assertEqual(importer.serialise(soup), 'S.ta Iria e V. Ex.a')

    def test_pdf_dialogue_bar_uses_supported_glyph(self):
        self.assertEqual(format_block('― Olá!\nA & B'), '— Olá!<br/>A &amp; B')


if __name__ == '__main__':
    unittest.main()
