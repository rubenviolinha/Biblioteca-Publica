# Biblioteca-Publica

Biblioteca digital para organizar e servir obras em português, com dados estruturados em `data/` e scripts para compilar os livros em PDF.

## Estrutura

- `index.html` - interface principal
- `data/` - catálogo, metadados e capítulos dos livros
- `scripts/` - ferramentas locais para gerar e compilar conteúdo
- `requirements.txt` - dependências Python

## Desenvolvimento

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar os scripts conforme necessário:

```bash
python scripts/build_books.py
python scripts/build_pdfs.py
python scripts/admin_api.py
```

