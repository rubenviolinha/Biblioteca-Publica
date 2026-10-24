# Biblioteca Pública — Livros de Portugal

Uma biblioteca digital gratuita para ler clássicos da literatura portuguesa. O leitor funciona como um site estático, sem conta, servidor ou base de dados. Os livros são guardados em JSON simples, com contexto, notas de leitura e edições de referência.

## Conteúdo

- **Os Lusíadas**, Luís de Camões — os dez cantos, com introduções e notas.
- **Mensagem**, Fernando Pessoa — os 44 poemas, organizados pelas três partes e secções do livro.
- **Os Maias**, Eça de Queirós — os 18 capítulos dos dois volumes, com a ortografia da edição de 1888.
- **Viagens na Minha Terra**, Almeida Garrett — os 49 capítulos da edição de 1846, entre viagem, romance e comentário político.
- **Amor de Perdição**, Camilo Castelo Branco — prólogo e os 20 capítulos das duas partes, na grafia da edição de 1862.
- **O Primo Basílio**, Eça de Queirós — o texto da segunda edição de 1878, organizado segundo os 16 títulos de capítulo explícitos na transcrição de referência.
- **A Cidade e as Serras**, Eça de Queirós — os 16 capítulos da edição póstuma de 1901, organizados entre Paris e Tormes.
- **Frei Luís de Sousa**, Almeida Garrett — a peça completa de 1843, organizada pelos seus três actos.
- **A Correspondência de Fradique Mendes**, Eça de Queirós — oito secções de memórias e as 16 cartas da edição de 1900.
- **O Mandarim**, Eça de Queirós — prólogo e oito capítulos da novela publicada em 1880, com notas de leitura.
- **O Mistério da Estrada de Sintra**, Eça de Queirós e Ramalho Ortigão — oito partes do romance epistolar publicado em 1870.
- **A Harpa do Crente**, Alexandre Herculano — as três séries de poemas da edição de 1838.
- **A Velhice do Padre Eterno**, Guerra Junqueiro — 28 poemas da edição de 1885, incluindo o posfácio.
- **O Livro de Cesário Verde**, Cesário Verde — 22 poemas na compilação de Silva Pinto publicada em 1887.


- **Eurico, o Presbítero**, Alexandre Herculano — prefácio, 19 capítulos e notas históricas da quinta edição de 1864.
- **A Queda d’um Anjo**, Camilo Castelo Branco — dedicatória, 36 capítulos e notas da edição de 1866.
- **O Crime do Padre Amaro**, Eça de Queirós — nota do autor e 25 divisões da transcrição da edição de 1889, que passa de X a XII sem cabeçalho XI.
- **A Relíquia**, Eça de Queirós — abertura do narrador e cinco capítulos da edição impressa no Porto em 1887.
- **A Ilustre Casa de Ramires**, Eça de Queirós — os 12 capítulos da edição de 1900, com a novela histórica intercalada.
- **Só**, António Nobre — poema de dedicatória e 29 poemas da primeira edição de 1892, com versos e estrofes preservados.
- **Os Sonetos Completos de Antero de Quental**, Antero de Quental — prefácio de Oliveira Martins e 99 unidades poéticas da edição de 1886, mantendo os ciclos e os períodos cronológicos.

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

Os estilos estão incluídos no repositório. Se alterar as classes do leitor, actualize-os com:

```bash
npm ci
npm run build:css
```

Os importadores consultam as fontes online e recriam as edições de referência. Instale primeiro as dependências com `python3 -m pip install -r requirements.txt`:

```bash
python3 scripts/import_public_domain.py
python3 scripts/import_additional_classics.py
python3 scripts/import_more_classics.py
python3 scripts/build_books.py
```

Para actualizar também todos os PDFs, instale a dependência e execute `python3 scripts/build_pdfs.py`. O Project Gutenberg identifica o estatuto de direitos das suas edições nos Estados Unidos e recomenda que leitores de outros países confirmem a lei local; os metadados de cada livro identificam a edição consultada e a fonte da transcrição.

Os testes de importação verificam os limites das secções, a remoção das páginas de origem e a preservação dos versos:

```bash
python3 -m unittest discover -s tests -v
```

## Capas e catálogo

As capas da colecção seguem o desenho a grafite sobre papel claro usado em **Mensagem**. Cada obra tem uma ilustração própria; os títulos e autores são apresentados como texto sob a imagem para manter a leitura nítida. As novas imagens estão em `data/books/<slug>/cover-sketch.webp`, com os prompts e a referência de estilo em `design/cover-sketches.json`.

O campo `coverImage` de `book.json` e do catálogo identifica a imagem utilizada. Os importadores preservam a capa já escolhida quando actualizam o texto de uma obra.

## Administração local

O painel ADMIN só aparece quando o site é aberto em `localhost` ou `127.0.0.1`. Para guardar alterações nos ficheiros do projecto, inicie a API local noutro terminal:

```bash
python3 scripts/admin_api.py
```

O painel envia as alterações à API em `http://127.0.0.1:8765`. Esta API destina-se apenas à gestão local; não é necessária para publicar ou ler o site.

## Publicar com GitHub Pages

O workflow em `.github/workflows/pages.yml` compila os estilos, prepara os livros e publica automaticamente o site depois de activar **GitHub Actions** e **GitHub Pages → Build and deployment → GitHub Actions** nas definições do repositório. Também pode iniciar a publicação manualmente no separador **Actions**. O leitor não precisa de um processo de build JavaScript.

O leitor suporta pesquisa no catálogo, ligações directas para livros e capítulos, PDFs, tamanho de letra ajustável e anotações activáveis. Os estilos são compilados para um ficheiro local; as fontes tipográficas usam Google Fonts com alternativas do sistema.

## Estrutura

```text
index.html                      Leitor estático
assets/tailwind.css             Estilos compilados para produção
styles/tailwind.css             Entrada dos estilos Tailwind CSS
package.json                    Dependências e comando de compilação dos estilos
data/books.json                 Catálogo
data/books/<slug>/book.json     Metadados e ordem dos capítulos
data/books/<slug>/chapters/     Conteúdo-fonte, notas e contexto
data/books/<slug>/compiled.json Dados carregados pelo leitor
data/books/<slug>/compiled.pdf  Edição PDF para descarregar
scripts/build_books.py          Compilador do catálogo de leitura
scripts/build_pdfs.py           Gerador de PDFs
scripts/import_public_domain.py Importador de edições de referência
scripts/import_more_classics.py Importador de sete novas edições de referência
scripts/admin_api.py            API para edição local
```

## Licença

O código do site e os scripts estão cobertos pela licença MIT em `LICENSE`. As obras incluídas, as transcrições e os materiais editoriais mantêm as condições próprias descritas nos respectivos ficheiros de metadados e nas fontes.
