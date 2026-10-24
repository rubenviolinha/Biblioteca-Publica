# Biblioteca Pública — Livros de Portugal

Uma biblioteca digital gratuita para ler clássicos da literatura portuguesa. O leitor funciona como um site estático, sem conta, servidor ou base de dados. Os livros são guardados em JSON simples, com contexto, notas de leitura e edições de referência.

## Conteúdo

- **Os Lusíadas**, Luís de Camões — os dez cantos, com introduções e notas.
- **Mensagem**, Fernando Pessoa — os 44 poemas, organizados pelas três partes e secções do livro.
- **Os Maias**, Eça de Queirós — os 18 capítulos dos dois volumes, com a ortografia da edição de 1888.

As obras e os ficheiros do site têm termos de utilização diferentes. Consulte `data/books/*/book.json` para a edição e a fonte de cada texto. A transcrição de *Mensagem* vem da Wikisource e é disponibilizada sob CC BY-SA 4.0; *Os Maias* usa uma transcrição do Project Gutenberg preparada a partir de digitalizações da Biblioteca Nacional de Portugal. As notas editoriais são conteúdo do projecto.

## Ver o site no computador

Na pasta do projecto, execute:

```bash
python3 -m http.server 8000
```

Abra [http://localhost:8000](http://localhost:8000). Servir os ficheiros por HTTP permite ao navegador carregar o catálogo e os textos JSON.

## Gerar os livros e os PDFs

Os ficheiros-fonte estão em `data/books/<slug>/book.json` e `data/books/<slug>/chapters/`. Para reconstruir os ficheiros de leitura:

```bash
python3 scripts/build_books.py
```

Para actualizar os PDFs, instale a dependência e execute:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build_pdfs.py
```

O importador que recria as edições completas de *Mensagem* e *Os Maias* consulta as fontes online e pode ser executado com:

```bash
python3 scripts/import_public_domain.py
python3 scripts/build_books.py
```

## Administração local

O painel ADMIN só aparece quando o site é aberto em `localhost` ou `127.0.0.1`. Para guardar alterações nos ficheiros do projecto, inicie a API local noutro terminal:

```bash
python3 scripts/admin_api.py
```

O painel envia as alterações à API em `http://127.0.0.1:8765`. Esta API destina-se apenas à gestão local; não é necessária para publicar ou ler o site.

## Publicar com GitHub Pages

O workflow em `.github/workflows/pages.yml` prepara e publica automaticamente o site depois de activar **GitHub Actions** e **GitHub Pages → Build and deployment → GitHub Actions** nas definições do repositório. Também pode iniciar a publicação manualmente no separador **Actions**. O site não precisa de um processo de build JavaScript.

O leitor suporta pesquisa no catálogo, ligações directas para livros e capítulos, PDFs, tamanho de letra ajustável e anotações activáveis. As capas, tipos de letra e Tailwind CSS são carregados de serviços externos.

## Estrutura

```text
index.html                      Leitor estático
data/books.json                 Catálogo
data/books/<slug>/book.json     Metadados e ordem dos capítulos
data/books/<slug>/chapters/     Conteúdo-fonte, notas e contexto
data/books/<slug>/compiled.json Dados carregados pelo leitor
data/books/<slug>/compiled.pdf  Edição PDF para descarregar
scripts/build_books.py          Compilador do catálogo de leitura
scripts/build_pdfs.py           Gerador de PDFs
scripts/import_public_domain.py Importador de edições de referência
scripts/admin_api.py            API para edição local
```

## Licença

O código do site e os scripts estão cobertos pela licença MIT em `LICENSE`. As obras incluídas, as transcrições e os materiais editoriais mantêm as condições próprias descritas nos respectivos ficheiros de metadados e nas fontes.
