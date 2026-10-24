# Biblioteca Pública — Livros de Portugal

Uma biblioteca digital gratuita para ler clássicos da literatura portuguesa. O leitor funciona como um site estático, sem conta, servidor ou base de dados. Os livros são guardados em JSON simples, com contexto, notas de leitura e edições de referência.

## Conteúdo

- **Os Lusíadas**, Luís de Camões — os dez cantos, com introduções e notas.
- **Mensagem**, Fernando Pessoa — os 44 poemas, organizados pelas três partes e secções do livro.
- **Os Maias**, Eça de Queirós — os 18 capítulos dos dois volumes, com a ortografia da edição de 1888.
- **Viagens na Minha Terra**, Almeida Garrett — os 49 capítulos da edição de 1846, entre viagem, romance e comentário político.
- **Amor de Perdição**, Camilo Castelo Branco — prólogo e os 20 capítulos das duas partes, na grafia da edição de 1862.
- **O Primo Basílio**, Eça de Queirós — o texto da segunda edição de 1878, organizado segundo os 16 títulos de capítulo explícitos na transcrição de referência.

As obras e os ficheiros do site têm termos de utilização diferentes. Consulte `data/books/*/book.json` para a edição, a origem da transcrição e a nota editorial de cada texto. As obras originais aqui incluídas estão no domínio público em Portugal; a situação de uma transcrição, edição ou material gráfico pode ser diferente. As notas de leitura e as capas criadas para este projecto são conteúdo editorial do projecto.

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

Os importadores consultam as fontes online e recriam as edições completas:

```bash
python3 scripts/import_public_domain.py
python3 scripts/import_additional_classics.py
python3 scripts/build_books.py
```

Para actualizar também todos os PDFs, instale a dependência e execute `python3 scripts/build_pdfs.py`. O Project Gutenberg identifica o estatuto de direitos das suas edições nos Estados Unidos e recomenda que leitores de outros países confirmem a lei local; os metadados de cada livro identificam a edição consultada e a fonte da transcrição.

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
