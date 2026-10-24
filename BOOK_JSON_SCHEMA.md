# Formato dos livros

Cada obra tem uma pasta em `data/books/<slug>/`. O ficheiro `book.json` contém os metadados e a ordem de leitura; cada capítulo vive num ficheiro em `chapters/`. `scripts/build_books.py` combina esses ficheiros em `compiled.json`, que o site carrega.

## Metadados da obra

```json
{
  "id": 4,
  "slug": "o-primo-bazilio",
  "title": "O Primo Basílio",
  "author": "Eça de Queirós",
  "authorId": "eca-de-queiros",
  "authorBio": "Romancista português (1845–1900).",
  "description": "Romance publicado em 1878.",
  "year": "1878",
  "language": "pt",
  "coverImage": "./data/books/o-primo-bazilio/cover.png",
  "tags": ["romance", "realismo"],
  "source": {
    "title": "Edição de referência",
    "url": "https://example.org/edicao",
    "transcription": "Identificação da transcrição ou licença",
    "editorialNote": "Nota sobre a edição usada"
  },
  "chapterOrder": ["capitulo-i"]
}
```

`slug` deve usar apenas letras minúsculas sem acentos, números e hífenes. `chapterOrder` é obrigatório, não pode ter repetições e determina a ordem do leitor. O catálogo `data/books.json` contém a lista pública de metadados e é actualizado pelo painel local.

## Capítulo

```json
{
  "slug": "capitulo-i",
  "title": "Capítulo I",
  "section": "Volume I",
  "context": "Enquadramento histórico e literário deste capítulo.",
  "content": "Texto integral do capítulo, preservando as quebras de linha.",
  "audioUrl": "",
  "audioDuration": "",
  "annotations": [
    {
      "target": "Ramalhete",
      "text": "A casa da família em Lisboa também funciona como símbolo da sua história."
    }
  ]
}
```

Cada anotação deve apontar para uma expressão que apareça no texto. O leitor destaca essa expressão quando as notas estão activadas. `section` é opcional e permite agrupar secções maiores, por exemplo, partes ou volumes.

## Importar ou editar

1. Crie `data/books/<slug>/book.json` e `data/books/<slug>/chapters/<chapter-slug>.json`.
2. Inclua todos os capítulos em `chapterOrder`, pela ordem de leitura.
3. Execute `python3 scripts/build_books.py` para validar e criar os ficheiros de leitura.
4. Execute `python3 scripts/build_pdfs.py` para gerar os PDFs.

O importador das edições actuais está em `scripts/import_public_domain.py`. Ao adicionar uma obra, registe sempre a edição, a origem da transcrição e os termos de utilização em `book.json`.
