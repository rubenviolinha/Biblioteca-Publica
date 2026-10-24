#!/usr/bin/env python3
"""Import seven further classics from documented Gutenberg transcriptions.

Source-specific chapter boundaries are checked before writing. Poems retain
verse and stanza breaks; source page furniture and proofreading errata are
excluded. Historical authorial introductions and notes are retained separately.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.error import HTTPError

from bs4 import BeautifulSoup, NavigableString, Tag
from import_public_domain import fetch, write_json
from import_additional_classics import chapter_record, normalized_heading, roman_number, save_book

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / 'data' / 'books'
ROMAN = re.compile(r'^[IVXL]+$')
SOURCE_DIR = None


def source(book_id):
    path = SOURCE_DIR / f'{book_id}.html' if SOURCE_DIR else None
    if path and path.exists():
        html = path.read_text(encoding='utf-8-sig')
    else:
        try:
            html = fetch(f'https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.html').decode('utf-8-sig')
        except HTTPError as exc:
            if exc.code != 404:
                raise
            html = fetch(f'https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}-images.html').decode('utf-8-sig')
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.select('.pagenum, .pagenumber, script, style'):
        tag.decompose()
    return soup


def flatten(node):
    """Distinguish explicit verse breaks from HTML source-code wrapping."""
    if isinstance(node, NavigableString):
        return re.sub(r'\s+', ' ', str(node).replace('\xa0', ' '))
    if not isinstance(node, Tag):
        return ''
    if node.name == 'br':
        return '\ue001'
    if node.name in {'img', 'hr'}:
        return '\ue002'
    text = ''.join(flatten(child) for child in node.children)
    if (node.name == 'div' and any(c.startswith('poetry') for c in node.get('class', []))) or (node.name == 'p' and node.find('br')):
        text = '\ue010' + text + '\ue011'
    if node.name in {'p', 'div', 'blockquote', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'header', 'footer'}:
        return '\ue002' + text + '\ue002'
    return text


def serialise(soup):
    text = flatten(soup.body or soup)
    text = text.replace('\ue002', '\n\n').replace('\ue001', '\n')
    text = '\n'.join(line.strip() for line in text.splitlines())
    text = re.sub(r'\^\{([^}]+)\}', r'\1', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def title_text(tag):
    return tag.get_text(' ', strip=True).replace('*', '').strip().replace('  ', ' ')


def pieces(soup, headings, stop):
    """Mark actual DOM boundaries, including headings inside nested divs."""
    for index, heading in enumerate(headings):
        heading.insert_before(NavigableString(f'\ue100PART{index:03d}\ue101'))
    stop.insert_before(NavigableString('\ue100STOP\ue101'))
    text = serialise(soup).split('\ue100STOP\ue101', 1)[0]
    text = re.split(r'(?im)^End of (?:the )?Project Gutenberg', text, maxsplit=1)[0]
    result = []
    for index in range(len(headings)):
        content = text.split(f'\ue100PART{index:03d}\ue101', 1)[1]
        content = content.split(f'\ue100PART{index+1:03d}\ue101', 1)[0]
        result.append(content.strip())
    return text.split('\ue100PART000\ue101')[0], result


def without_heading(content, heading):
    """The original heading is represented by the chapter title, not repeated."""
    original = serialise(BeautifulSoup(str(heading), 'html.parser'))
    if not content.startswith(original):
        raise ValueError(f'Não foi possível separar o título da fonte: {title_text(heading)}')
    return content[len(original):].lstrip()


def prose(text):
    blocks = []
    for part in re.split(r'(\ue010.*?\ue011)', text, flags=re.S):
        if part.startswith('\ue010'):
            blocks.append(part.replace('\ue010', '').replace('\ue011', '').strip())
        else:
            for block in re.split(r'\n\s*\n', part):
                block = re.sub(r'(?<=\w)-\n(?=\w)', '', block)
                value = re.sub(r'\s+', ' ', block).strip()
                if value:
                    blocks.append(value)
    return '\n\n'.join(blocks)


def book_meta(id, slug, title, author, author_id, bio, year, description, tags,
              source_id, edition, transcription, editorial):
    return dict(id=id, slug=slug, title=title, author=author, authorId=author_id,
                authorBio=bio, year=str(year), description=description, tags=tags,
                language='pt', coverImage=f'./data/books/{slug}/cover.svg',
                source=dict(title=edition, url=f'https://www.gutenberg.org/ebooks/{source_id}',
                            transcription=transcription,
                            editorialNote=editorial + ' As marcas tipográficas de sobrescrito da transcrição são apresentadas em linha. As obras originais estão no domínio público em Portugal: os autores morreram há mais de 70 anos. O Project Gutenberg identifica o estatuto nos Estados Unidos; a transcrição e a edição devem ser distinguidas do texto original.'))

ECA_BIO = 'Escritor português (1845–1900), figura central do Realismo, conhecido pela ironia e pela crítica dos costumes e das instituições.'
BNP = 'Project Gutenberg e Distributed Proofreaders; transcrição a partir de imagens disponibilizadas pela Biblioteca Nacional de Portugal.'

EURICO_NOTES = [
 ('wisigodos', 'Os Visigodos governaram grande parte da Península Ibérica antes da conquista islâmica iniciada em 711; o romance recria esse mundo pela imaginação histórica do século XIX.'),
 ('Carteia', 'Carteia, cidade antiga junto à baía de Algeciras, é o lugar associado ao sacerdócio de Eurico.'),
 ('Hermengarda', 'Hermengarda é a mulher amada por Eurico; o vínculo amoroso entra em conflito com o compromisso religioso do protagonista.'),
 ('Pelagio', 'Pelágio é associado à resistência cristã nas Astúrias e à batalha de Covadonga; a sua representação mistura história e construção literária.'),
 ('Roderico', 'Rodrigo, último rei visigodo, é designado por Roderico nesta grafia histórica.'),
 ('Tarik', 'Tárique ibn Ziyad comandou as forças que atravessaram o estreito em 711; o nome surge na reconstrução histórica da conquista.'),
 ('Chryssus', 'Nome histórico usado no romance para o rio junto do qual se confrontam as forças visigodas e invasoras; a localização da batalha de 711 é discutida pelos historiadores.'),
 ('Covadonga', 'Lugar asturiano associado à vitória de Pelágio e à memória da resistência cristã no início do século VIII.'),
 ('presbytero', 'Presbítero é um sacerdote. O celibato e a renúncia aos afectos familiares são questões centrais do prefácio de Herculano.'),
 ('Amir', 'Forma do título árabe emir, aplicado a um comandante ou governante.'),
 ('Dies irae', 'Expressão latina que significa «dia da ira»; evoca o julgamento e a catástrofe.'),
 ('godo', 'A palavra designa aqui a sociedade visigótica. A oposição entre povos e crenças é apresentada através da perspectiva romântica do narrador.'),
]
EURICO_CONTEXTS = [
 'O capítulo apresenta a sociedade visigótica e as tensões políticas que antecedem a invasão da Península Ibérica.',
 'A apresentação do presbítero de Carteia aproxima a vida religiosa da solidão e da memória amorosa.',
 'A figura de Eurico é observada através da criação poética e da maneira como os outros interpretam a sua vida retirada.',
 'As recordações de Eurico recuperam a experiência amorosa e a ferida que acompanha a sua escolha religiosa.',
 'A meditação torna explícito o conflito entre a consciência, a fé e os sentimentos que a renúncia não extinguiu.',
 'A saudade organiza uma escrita lírica em que o passado é vivido como presença e perda.',
 'A visão amplia o mundo interior de Eurico e aproxima a linguagem do romance da profecia e do poema.',
 'O desembarque das forças invasoras muda a escala da narrativa; as cartas articulam a experiência individual e a ameaça colectiva.',
 'A aproximação ao Chryssus prepara o confronto militar e põe em relevo a fragilidade do poder visigótico.',
 'A traição converte as divisões internas do reino numa causa decisiva da catástrofe militar.',
 'O título latino «Dies irae» enquadra o combate através de imagens de julgamento, destruição e sacrifício.',
 'O mosteiro introduz um espaço de refúgio e clausura no percurso de guerra, memória e perseguição.',
 'Covadonga desloca a narrativa para a paisagem montanhosa associada à resistência de Pelágio.',
 'A noite do amir concentra a tensão entre a violência da guerra e o destino dos que se encontram em poder do inimigo.',
 'O luar acompanha uma mudança do cenário militar para uma experiência nocturna de perigo e aproximação.',
 'O castro romano reaproveita um vestígio antigo como cenário das decisões e dos riscos do presente narrativo.',
 'A imagem da aurora associa a resistência a uma expectativa de libertação, sem resolver o conflito íntimo de Eurico.',
 'O título «Impossivel!» concentra o impasse entre o reencontro amoroso e a condição sacerdotal.',
 'A conclusão fecha os percursos de Eurico e Hermengarda e retoma o custo humano da renúncia e da guerra.',
]

QUEDA_NOTES = [
 ('Calisto', 'Calisto Elói é o morgado provinciano cuja chegada à política lisboeta permite a Camilo satirizar tanto o conservadorismo como a modernidade mundana.'),
 ('morgado', 'Herdeiro ou administrador de um morgadio, vínculo que concentrava bens familiares; a instituição foi abolida em Portugal em 1863.'),
 ('Miranda', 'A região de Miranda situa o mundo de origem do protagonista no nordeste de Portugal, em contraste com a capital.'),
 ('Theodora', 'Teodora é a mulher de Calisto; o seu percurso também participa na transformação dos valores domésticos apresentada pelo romance.'),
 ('Iphigenia', 'Ifigénia é a viúva brasileira que ocupa um lugar decisivo na vida sentimental e social de Calisto.'),
 ('parlamento', 'O parlamento é representado como espaço de retórica, alianças e ambição; a sátira põe em causa a distância entre discurso e conduta.'),
 ('Benevides', 'Benevides é um dos apelidos de Calisto; a acumulação de nomes participa na caracterização cómica da sua pretensão genealógica.'),
 ('constitutional', 'A vida política do romance decorre no quadro da monarquia constitucional portuguesa do século XIX.'),
 ('Camões', 'A referência ao poeta pode servir à erudição das personagens ou à ironia do narrador; convém observar o contexto de cada citação.'),
 ('S. Carlos', 'O Teatro de São Carlos, em Lisboa, é um lugar de espectáculo e de exibição pública das hierarquias sociais.'),
 ('Cíntra', 'Grafia antiga de Sintra, local de veraneio e sociabilidade das elites representadas no romance.'),
 ('brazileira', 'No contexto do romance, a palavra pode referir-se à origem brasileira ou à ligação ao Brasil, parte importante das relações económicas e sociais portuguesas.'),
]

CRIME_NOTES = [
 ('Leiria', 'A cidade de Leiria é o centro da acção; a proximidade entre casas, igreja, botica e espaços de convívio torna visível o controlo social.'),
 ('Amelia', 'Amélia vive com a mãe num meio devoto. A sua relação com Amaro expõe relações de poder, desejo e dependência.'),
 ('Amaro', 'O padre Amaro é o protagonista; o narrador observa a sua formação, os seus desejos e o uso da autoridade sacerdotal.'),
 ('conego', 'Cónego é um membro do cabido de uma catedral. No romance, o título religioso também assinala posição social e influência.'),
 ('Joanneira', 'A S. Joaneira é a mãe de Amélia; a sua casa é um ponto de encontro da sociabilidade religiosa local.'),
 ('Natario', 'O padre Natário participa nas conversas e nos mecanismos de influência do clero local.'),
 ('João Eduardo', 'João Eduardo é o pretendente de Amélia e uma voz crítica do meio clerical.'),
 ('Libaninho', 'Libaninho integra o círculo devoto e participa na circulação de notícias, rumores e juízos sobre os outros.'),
 ('Ferrão', 'O abade Ferrão oferece uma maneira de exercer a religião que pode ser comparada com a dos outros sacerdotes da narrativa.'),
 ('confissão', 'A confissão aproxima intimidade e autoridade; o acesso à consciência alheia é um dos problemas éticos do romance.'),
 ('Zola', 'Émile Zola, escritor francês associado ao Naturalismo. Na nota inicial, Eça responde à acusação de imitar La Faute de l’Abbé Mouret.'),
 ('botica', 'A botica, ou farmácia, funciona como lugar de encontro, conversa política e circulação de rumores.'),
 ('beata', 'A palavra designa uma mulher muito devota; o seu uso pelo narrador pode carregar uma intenção satírica.'),
 ('Dionysia', 'Dionísia intervém no mundo doméstico e nos expedientes que rodeiam a relação dos protagonistas.'),
]

RELIQUIA_NOTES = [
 ('Theodorico', 'Teodorico Raposo, narrador destas memórias, procura controlar a imagem que os leitores formam da sua vida; a distância entre o que conta e o que revela sustenta a ironia.'),
 ('titi', 'Tratamento familiar da tia D. Patrocínio das Neves, de quem Teodorico espera receber uma herança.'),
 ('Topsius', 'O erudito alemão Topsius acompanha a viagem e permite satirizar a autoridade académica e a representação europeia do Oriente.'),
 ('Jerusalem', 'Jerusalém é simultaneamente destino de peregrinação e cenário de expectativas religiosas, interesses materiais e fantasias do narrador.'),
 ('reliquia', 'Uma relíquia é um vestígio material associado a uma figura ou acontecimento sagrado; o romance explora o contraste entre devoção, objecto e interesse.'),
 ('Raposão', 'Alcunha de Teodorico Raposo; acompanha a sua identidade mundana e a comicidade do relato.'),
 ('Mary', 'Mary pertence aos encontros de Teodorico durante a viagem; o objecto que lhe fica associado ganha importância na construção do equívoco narrativo.'),
 ('Alexandria', 'Cidade portuária egípcia que integra o itinerário de Teodorico para a Terra Santa.'),
 ('Burguezia Liberal', 'A expressão surge na autojustificação do narrador e liga prestígio social, dinheiro e respeitabilidade pública.'),
 ('Golgotha', 'Gólgota é o lugar associado à crucificação de Jesus; a sua evocação participa na reconstrução imaginária da narrativa bíblica.'),
]

RAMIRES_NOTES = [
 ('Gonçalo', 'Gonçalo Mendes Ramires, o Fidalgo da Torre, procura conciliar o prestígio da linhagem com as ambições do seu presente.'),
 ('Torre', 'A torre familiar é um vestígio material da linhagem e um motivo que liga o espaço doméstico à novela histórica escrita pelo protagonista.'),
 ('Gracinha', 'Gracinha é a irmã de Gonçalo; a vida familiar cruza-se com as relações de influência e a carreira política.'),
 ('Cavaleiro', 'André Cavaleiro é uma figura de influência política; as relações pessoais com ele expõem a ligação entre ambição, memória e conveniência.'),
 ('Castanheiro', 'José Lúcio Castanheiro promove a revista para a qual Gonçalo escreve a novela histórica.'),
 ('Titó', 'Titó pertence ao círculo de convivência de Gonçalo e participa na representação dos costumes provincianos.'),
 ('Bacoco', 'Alcunha que integra o registo familiar e cómico com que o romance apresenta a sociedade local.'),
 ('Annaes', 'Os Annaes de Litteratura e de Historia são a revista ficcional que oferece a Gonçalo uma oportunidade de afirmação literária.'),
 ('Walter Scott', 'Romancista escocês associado à consolidação do romance histórico; a referência ajuda a enquadrar os modelos literários de Gonçalo.'),
 ('África', 'O horizonte africano deve ser lido no contexto da expansão colonial portuguesa do fim do século XIX, que o romance relaciona com projectos pessoais e nacionais.'),
 ('Santa Ireneia', 'A aldeia de Santa Ireneia é um dos lugares ficcionais que organizam o mundo provincial da casa de Ramires.'),
]

ANTERO_NOTES = [
 ('Nirvâna', 'Termo de origem budista ligado à libertação do sofrimento e do desejo; na poesia de Antero é apropriado num diálogo europeu entre filosofia, religião e consciência.'),
 ('Inconsciente', 'O inconsciente surge como força que ultrapassa a vontade individual, num horizonte de reflexão filosófica do século XIX.'),
 ('Razão', 'A razão pode aparecer como guia, tribunal ou força de desengano; observe a tensão entre conhecimento e desejo de consolação.'),
 ('Deus', 'A procura de Deus e a dúvida convivem nesta poesia; a linguagem religiosa não deve ser reduzida a uma única conclusão doutrinal.'),
 ('morte', 'A morte assume sentidos diferentes ao longo do livro: ameaça, libertação, enigma ou possibilidade de repouso.'),
 ('Ideal', 'O ideal designa uma aspiração que a experiência concreta pode contrariar; esta distância alimenta o movimento interrogativo dos poemas.'),
 ('Mors', 'Palavra latina para «morte»; nos títulos, aproxima a tradição clássica dos problemas modernos de consciência e sofrimento.'),
 ('Nox', 'Palavra latina para «noite», associada à escuridão, ao silêncio e à interrogação metafísica.'),
 ('Solemnia Verba', 'A expressão latina Solemnia Verba significa «palavras solenes» e enquadra o tom de uma meditação final.'),
 ('Justitia', 'O título latino Justitia Mater aproxima a justiça de uma figura materna.'),
 ('Oliveira Martins', 'Joaquim Pedro de Oliveira Martins (1845–1894) apresenta a edição de 1886; o seu prefácio é identificado como texto de outro autor.'),
 ('João de Deus', 'João de Deus (1830–1896), poeta português a quem Antero dedica um dos sonetos.'),
]

SO_NOTES = [
 ('Carlota', 'Carlota é uma figura de cuidado e memória afectiva que reaparece no universo poético de António Nobre.'),
 ('Coimbra', 'Coimbra é um espaço de juventude, estudo e recordação; a sua evocação participa na construção da memória do sujeito poético.'),
 ('Pariz', 'Paris é o lugar de escrita e de distância em relação a Portugal em vários poemas; esta grafia corresponde à edição de 1892.'),
 ('Luzitania', 'Grafia usada no título para evocar Portugal através de um nome antigo e literário; a distância geográfica intensifica a recordação do país.'),
 ('Bairro-Latino', 'O Quartier Latin de Paris é tradicionalmente associado às universidades, aos estudantes e à vida intelectual.'),
 ('tysica', 'Designação antiga da tuberculose; a doença é um motivo recorrente na poesia finissecular.'),
 ('Ophelia', 'Ofélia, personagem de Hamlet, de Shakespeare, é retomada pela poesia europeia como figura de perda, fragilidade e morte.'),
 ('Anto', 'Forma familiar de António, usada na construção de uma identidade poética que aproxima autobiografia e encenação.'),
 ('sinos', 'Os sinos ligam o som à vida comunitária, ao ritual religioso, à passagem do tempo e à memória.'),
 ('saudade', 'A saudade aproxima a experiência da ausência de uma reconstrução afectiva de pessoas, paisagens e tempos perdidos.'),
 ('Manoel', 'O poema Carta a Manoel usa a forma de uma mensagem dirigida a um interlocutor, aproximando verso, conversa e memória.'),
 ('Coveiro', 'A figura do coveiro participa no diálogo dramático do poema final, em que a morte é imaginada através de uma linguagem quotidiana.'),
]


def import_eurico():
    soup = source('45966')
    headings = [h for h in soup.find_all('h3') if re.match(r'^[IVXL]+\s+\S', title_text(h))]
    assert len(headings) == 19, f'Eurico: estrutura inesperada: {len(headings)} capítulos'
    author_notes = next(h for h in soup.find_all('h3') if normalized_heading(title_text(h)) == 'notas')
    stop = next(h for h in soup.find_all('h2') if normalized_heading(title_text(h)) == 'lista de erros corrigidos')
    front, blocks = pieces(soup, headings + [author_notes], stop)
    intro = front[front.index('Para as almas,'):].rsplit('EURICO O PRESBYTERO', 1)[0]
    chapters = [chapter_record('prefacio', 'Prefácio do autor', 'Prefácio',
                'Herculano explica a relação entre o celibato, a solidão e a concepção do romance; o texto está datado de Novembro de 1843.', prose(intro), EURICO_NOTES)]
    for index, (heading, content) in enumerate(zip(headings, blocks)):
        number, subtitle = title_text(heading).split(' ', 1)
        chapters.append(chapter_record(f'capitulo-{index+1:02d}', f'Capítulo {number} — {subtitle.capitalize()}',
                        'Romance histórico', EURICO_CONTEXTS[index], prose(without_heading(content, heading)), EURICO_NOTES))
    chapters.append(chapter_record('notas-do-autor', 'Notas do autor', 'Aparato histórico',
                    'As notas históricas da edição explicam referências, fontes e escolhas de Herculano. As remissões de página dizem respeito à edição impressa de 1864.', prose(without_heading(blocks[-1], author_notes)), EURICO_NOTES))
    book = book_meta(15, 'eurico-o-presbitero', 'Eurico, o Presbítero', 'Alexandre Herculano', 'alexandre-herculano',
         'Escritor e historiador português (1810–1877), figura central do Romantismo e do romance histórico.', 1844,
         'Amor, renúncia e guerra no fim do reino visigótico, num romance histórico que acompanha o sacerdote e guerreiro Eurico.',
         ['romance histórico', 'Romantismo', 'Península Ibérica'], '45966', 'Eurico o Presbytero — quinta edição, Imprensa Nacional, 1864',
         'Project Gutenberg e Distributed Proofreaders; transcrição a partir de imagens do Google Print.',
         'Inclui o prefácio, os 19 capítulos e as notas históricas do autor; exclui a nota moderna de transcrição e a tabela de erratas. Preserva a grafia da edição de 1864 e as subdivisões internas. Alexandre Herculano morreu em 1877.')
    save_book(book['slug'], book, chapters)
    return book


def import_queda():
    soup = source('17927')
    dedication = soup.find(id='id00011')
    headings = [h for h in soup.find_all('h2') if ROMAN.fullmatch(title_text(h))]
    assert len(headings) == 36, f'A Queda: esperava 36 capítulos, encontrei {len(headings)}'
    index = soup.find(id='id01400')
    author_notes = soup.find(id='id01402')
    _, blocks = pieces(soup, [dedication] + headings + [index, author_notes], soup.find(id='pg-footer'))
    chapters = [chapter_record('dedicatoria', 'Dedicatória', 'Dedicatória',
                'Camilo dedica o romance a António Rodrigues Sampaio. A amizade, a gratidão e a falsa modéstia já anunciam o jogo irónico da narrativa.', prose(blocks[0]), QUEDA_NOTES)]
    for position, (h, content) in enumerate(zip(headings, blocks[1:37]), 1):
        subtitle_tag = h.find_next('p')
        subtitle = title_text(subtitle_tag)
        content = without_heading(without_heading(content, h), subtitle_tag)
        context = f'O título original desta etapa é «{subtitle}». Na sátira de Camilo, a passagem entre o mundo provincial e a sociedade lisboeta permite confrontar princípios declarados, interesses e comportamentos.'
        chapters.append(chapter_record(f'capitulo-{position:02d}', f'Capítulo {title_text(h)} — {subtitle}',
                        'Romance satírico', context, prose(content), QUEDA_NOTES))
    chapters.append(chapter_record('notas-do-autor', 'Notas do autor', 'Notas da edição',
                    'As notas numeradas da edição esclarecem citações e referências presentes nos capítulos; a numeração original é mantida.', prose(without_heading(blocks[-1], author_notes)), QUEDA_NOTES))
    book = book_meta(16, 'a-queda-dum-anjo', 'A Queda d’um Anjo', 'Camilo Castelo Branco', 'camilo-castelo-branco',
         'Romancista português (1825–1890), autor de uma vasta obra de ficção, polémica e crítica dos costumes.', 1866,
         'A chegada de um morgado provinciano ao parlamento lisboeta desencadeia uma sátira à política, à respeitabilidade e à transformação dos costumes.',
         ['romance', 'sátira', 'política', 'Lisboa'], '17927', 'A Queda d’um Anjo: Romance — Livraria de Campos Junior, 1866', BNP,
         'Dedicatória, 36 capítulos com os seus subtítulos originais e notas numeradas da edição de 1866. Exclui o índice, mantendo a grafia de época. Camilo Castelo Branco morreu em 1890.')
    save_book(book['slug'], book, chapters)
    return book


def import_crime():
    soup = source('31971')
    headings = [h for h in soup.find_all('h3') if ROMAN.fullmatch(title_text(h))]
    numbers = [roman_number(title_text(h)) for h in headings]
    assert numbers == list(range(1, 11)) + list(range(12, 27)), f'Amaro: numeração inesperada: {numbers}'
    note = next(h for h in soup.find_all('h3') if title_text(h) == 'NOTA')
    stop = next(h for h in soup.find_all('h2') if normalized_heading(title_text(h)) == 'lista de erros corrigidos')
    _, blocks = pieces(soup, [note] + headings, stop)
    introduction = re.sub(r'O\s+CRIME\s+DO\s+PADRE\s+AMARO\s*$', '', blocks[0])
    chapters = [chapter_record('nota-do-autor', 'Nota do autor', 'Nota da segunda edição',
                'Eça responde à comparação com La Faute de l’Abbé Mouret, de Zola, e discute as datas, as personagens e os propósitos dos dois romances.', prose(introduction), CRIME_NOTES)]
    contexts = {
        1: 'A morte do pároco de Leiria abre o romance e introduz o meio clerical e doméstico onde chegará Amaro.',
        2: 'A chegada de Amaro à cidade é acompanhada pelo cónego Dias e pela instalação na casa da S. Joanneira.',
        3: 'O narrador recua à infância de Amaro, à sua educação e ao seminário, interrogando a origem da sua condição de sacerdote.',
        4: 'A notícia da chegada do novo pároco circula pela cidade. As visitas e conversas mostram como a reputação se forma no espaço doméstico.',
        5: 'A inquietação de Amélia é aproximada do ambiente do quarto e das imagens de devoção que a rodeiam.',
        6: 'O conforto da casa e a atenção da S. Joanneira consolidam a presença de Amaro; a convivência aproxima o desejo da intimidade quotidiana.',
        7: 'O jantar na Cortegassa oferece um retrato das relações entre os sacerdotes, onde a conversa e os prazeres da mesa tornam visíveis os costumes do grupo.',
        8: 'O medo de Amaro põe em causa a sua permanência na casa. A preocupação com o escândalo revela a distância entre autoridade religiosa e responsabilidade moral.',
        9: 'A intimidade na rua da Misericórdia retoma o seu ritmo de visitas e encontros, enquanto se acumulam tensões entre as personagens.',
        10: 'A redacção da Voz do Districto aproxima o conflito pessoal da polémica pública e da sátira ao clero. A divisão seguinte da fonte é XII; não há cabeçalho XI na transcrição consultada.',
        12: 'A aproximação entre o padre Natário e o doutor Godinho altera os equilíbrios do meio local. Observe as alianças e os interesses que se escondem na conversa pública.',
        13: 'A visita matinal de Amaro aos Dias desloca o conflito para outro espaço doméstico e evidencia a circulação de notícias e juízos no círculo devoto.',
        14: 'João Eduardo procura Amélia num momento em que as expectativas de casamento se confrontam com rumores, vigilância e autoridade religiosa.',
        15: 'O percurso de João Eduardo pela cidade expõe o desgaste de uma noite de inquietação e a dificuldade de encontrar apoio fora do círculo dominante.',
        16: 'A missa cantada na Sé reúne as personagens num ritual público; os gestos de devoção convivem com tensões sociais e afectivas.',
        17: 'O despertar satisfeito de Amaro permite observar a relação entre prazer privado e a linguagem religiosa com que ele interpreta os seus actos.',
        18: 'Amaro apresenta a felicidade pessoal como sinal da graça divina, num dos contrastes mais explícitos entre a consciência da personagem e a ironia narrativa.',
        19: 'A presença de Tótó perturba os encontros na casa do sineiro. A vulnerabilidade e a hostilidade entram no espaço que os protagonistas pretendiam controlar.',
        20: 'Amaro procura o cónego com urgência. A dependência dos conselhos e das soluções do seu círculo põe em relevo os mecanismos de protecção mútua.',
        21: 'A notícia recebida por Amélia ameaça os projectos com que tentava conciliar honra, vida doméstica e felicidade.',
        22: 'O afastamento recomendado pelo cónego torna a vida de Amaro mais vazia, enquanto a distância é usada para evitar suspeitas.',
        23: 'A espera de Amaro e as visitas à sua casa prolongam o clima de inquietação e aproximam a narrativa das consequências das decisões anteriores.',
        24: 'A intervenção de Dionísia introduz negociações e expedientes em torno da situação de Amélia, acentuando a desigualdade de poder entre as personagens.',
        25: 'A espera ansiosa por Dionísia concentra o desenlace dos acontecimentos e a reacção de Amaro às suas consequências.',
        26: 'O último capítulo desloca-se para Lisboa, em 1871. O encontro público permite confrontar o destino das personagens com uma imagem irónica da ordem e da prosperidade nacionais.',
    }
    for h, content in zip(headings, blocks[1:]):
        number = title_text(h)
        chapters.append(chapter_record(f'capitulo-{roman_number(number):02d}', f'Capítulo {number}', 'Romance',
                        contexts[roman_number(number)], prose(without_heading(content, h)), CRIME_NOTES))
    book = book_meta(17, 'o-crime-do-padre-amaro', 'O Crime do Padre Amaro', 'Eça de Queirós', 'eca-de-queiros', ECA_BIO, 1875,
         'Em Leiria, a relação entre o padre Amaro e Amélia expõe os mecanismos de desejo, autoridade e hipocrisia de um meio devoto.',
         ['romance', 'Realismo', 'Leiria', 'religião'], '31971', 'O Crime do Padre Amaro — terceira edição, Livraria Internacional de Ernesto Chardron, 1889', BNP,
         'A primeira versão foi publicada em 1875 na Revista Ocidental; a edição-fonte de 1889 contém a nota da segunda edição e 25 divisões de capítulo explícitas: I–X e XII–XXVI. A transcrição não apresenta um cabeçalho XI; mantém-se essa numeração sem fabricar uma divisão. Excluem-se publicidade, nota moderna de transcrição e tabela de erratas. Eça de Queirós morreu em 1900.')
    save_book(book['slug'], book, chapters)
    return book


def import_reliquia():
    soup = source('17515')
    headings = [h for h in soup.find_all('h2') if ROMAN.fullmatch(title_text(h))]
    assert len(headings) == 5, f'A Relíquia: encontrei {len(headings)} capítulos'
    intro = soup.find(id='id00004')
    _, blocks = pieces(soup, [intro] + headings, soup.find(id='pg-footer'))
    contexts = [
        'Teodorico apresenta a sua vida e a dependência da tia, entre a educação religiosa, o cálculo da herança e os desejos que procura esconder.',
        'A viagem ao Egipto e à Terra Santa cruza a peregrinação declarada com o olhar interessado e mundano do narrador.',
        'A reconstrução visionária do mundo bíblico ocupa o centro do romance e transforma a peregrinação numa experiência de imaginação histórica.',
        'O regresso aproxima a experiência da viagem das expectativas da tia e prepara o confronto entre aparência devota e interesse material.',
        'O desfecho acompanha as consequências do equívoco e a maneira como Teodorico procura explicar a sua mudança de fortuna.',
    ]
    chapters = [chapter_record('abertura', 'Abertura do narrador', 'Memórias de Teodorico',
                'O narrador apresenta o projecto das suas memórias e disputa a versão da viagem atribuída ao companheiro Topsius. A sua autojustificação convida a uma leitura atenta da ironia.', prose(blocks[0]), RELIQUIA_NOTES)]
    for index, content in enumerate(blocks[1:]):
        chapters.append(chapter_record(f'capitulo-{index+1:02d}', f'Capítulo {title_text(headings[index])}',
                        'Romance', contexts[index], prose(without_heading(re.split(r'(?m)^Porto:\s*1887', content)[0], headings[index])), RELIQUIA_NOTES))
    book = book_meta(18, 'a-reliquia', 'A Relíquia', 'Eça de Queirós', 'eca-de-queiros', ECA_BIO, 1887,
         'Teodorico Raposo conta a sua peregrinação à Terra Santa numa sátira em que devoção, herança e desejo se cruzam.',
         ['romance', 'sátira', 'viagem', 'religião'], '17515', 'A Reliquia — Porto, Typ. de A. J. da Silva Teixeira, 1887', BNP,
         'Texto integral organizado pela abertura do narrador e pelos cinco capítulos. O colofão da fonte identifica Porto e a tipografia de A. J. da Silva Teixeira, em 1887; estas linhas de impressão são excluídas do texto de leitura. A grafia da fonte é preservada. Eça de Queirós morreu em 1900.')
    save_book(book['slug'], book, chapters)
    return book


def import_ramires():
    soup = source('23145')
    headings = [h for h in soup.find_all('h2') if ROMAN.fullmatch(title_text(h))]
    assert len(headings) == 12, f'Ramires: encontrei {len(headings)} capítulos'
    _, blocks = pieces(soup, headings, soup.find(id='pg-footer'))
    blocks[-1] = re.split(r'(?m)^FIM\s*$', blocks[-1], maxsplit=1)[0].rstrip()
    contexts = [
        'Gonçalo escreve uma novela sobre os antepassados na biblioteca da casa familiar. A torre e a genealogia introduzem a distância entre grandeza herdada e acção presente.',
        'A escrita da novela histórica cruza-se com a convivência provincial. Observe como os modelos literários e a memória familiar alimentam a imagem que Gonçalo pretende construir.',
        'A narrativa articula a vida de Gonçalo com a história que ele escreve; os projectos literários e as relações sociais dependem uns dos outros.',
        'A vida provincial aproxima as questões familiares das ambições públicas. A ironia permite avaliar o que Gonçalo pensa de si e o que os seus actos mostram.',
        'O romance alterna a grandeza evocada dos antepassados com as dificuldades concretas do seu descendente, tornando a escrita um lugar de comparação e de conflito.',
        'A carreira pública e os vínculos privados expõem os compromissos do protagonista. Observe como a reputação se constrói nas conversas e nos pequenos gestos.',
        'A novela histórica e o presente de Gonçalo oferecem duas escalas de coragem e de conveniência; o contraste orienta a leitura das suas decisões.',
        'As relações pessoais e a ambição política intensificam a tensão entre lealdade familiar e interesse individual.',
        'As escolhas de Gonçalo são avaliadas no interior da rede de amizades, favores e expectativas que sustenta a vida provincial.',
        'O contraste entre o herói imaginado e o homem do presente regressa através da novela e das relações que rodeiam o Fidalgo da Torre.',
        'A narrativa aproxima-se do desfecho, convidando a rever a distância entre os projectos iniciais de Gonçalo e o percurso que efectivamente seguiu.',
        'O capítulo final reavalia o percurso de Gonçalo e abre a leitura da personagem a uma reflexão mais ampla sobre Portugal e o seu futuro.',
    ]
    chapters = [chapter_record(f'capitulo-{i+1:02d}', f'Capítulo {title_text(headings[i])}', 'Romance', contexts[i], prose(without_heading(content, headings[i])), RAMIRES_NOTES) for i, content in enumerate(blocks)]
    book = book_meta(19, 'a-ilustre-casa-de-ramires', 'A Ilustre Casa de Ramires', 'Eça de Queirós', 'eca-de-queiros', ECA_BIO, 1900,
         'Gonçalo Mendes Ramires escreve a história heroica dos antepassados enquanto procura o seu lugar na sociedade e na política do presente.',
         ['romance', 'Realismo', 'história', 'política'], '23145', 'A Illustre Casa de Ramires — Livraria Chardron, 1900', BNP,
         'Os 12 capítulos da edição de 1900 são preservados, incluindo a novela histórica intercalada e a grafia de época. Excluem-se publicidade e páginas de impressão; a nota final dos editores informa que as provas desde a página 417 até ao fim não foram revistas pelo autor, tendo os editores seguido o original. Essa nota é registada aqui em vez de integrar a narrativa. Eça de Queirós morreu em 1900.')
    save_book(book['slug'], book, chapters)
    return book


def poetry_text(content):
    return content.replace('\ue010', '').replace('\ue011', '').strip()



SO_CONTEXTS = [
    'A voz de António reconstrói a própria origem e convoca Carlota e o passado familiar a partir de uma noite de frio e solidão.',
    'A infância é figurada como uma flor perdida; o poema acompanha a passagem da expectativa juvenil à experiência do desencanto.',
    'O diálogo com o vento dá forma à viagem nocturna dos cavaleiros. A repetição aproxima o poema da balada e da narrativa oral.',
    'A amada desejada aparece entre figura concreta e criação ideal; observe a acumulação de imagens de leveza, véu e distância.',
    'A distância de França intensifica a recordação da terra e de uma figura familiar ausente, aproximando saudade e luto.',
    'O som dos sinos organiza um ciclo de imagens da vida e da morte; os refrães transformam a paisagem sonora em memória colectiva.',
    'A dedicatória a Alberto abre uma sequência dividida em partes; o tratamento familiar aproxima a evocação afectiva da linguagem religiosa.',
    'A forma epistolar permite conversar com Manoel sobre Coimbra, os passeios e as lembranças, dando ao verso um ritmo próximo da fala.',
    'Os pequenos quadros numerados aproximam paisagem, canção, intimidade e juventude; cada fragmento mantém a sua forma breve.',
    'A solidão em Paris faz regressar imagens de Portugal. O sujeito poético alterna a experiência do exílio e a evocação de um mundo colectivo.',
    'As figueiras são interpeladas num diálogo que mobiliza uma memória cultural de maldição e a experiência sensorial da paisagem.',
    'As rosas são associadas ao vinho, ao sangue e à intensidade do desejo; a cor vermelha organiza a progressão das imagens.',
    'O poente francês é observado através de imagens de vinho e sangue, cruzando a paisagem presente com outras memórias visuais e literárias.',
    'A passagem de uma mulher doente junto à porta desencadeia uma linguagem de compaixão, fragilidade física e pressentimento de morte.',
    'O anoitecer e o Outono oferecem imagens de declínio; o poema aproxima a paisagem exterior do acto de imaginar e escrever.',
    'A figura de Santa Iria é evocada sobre as águas, numa composição que aproxima a imagem religiosa, o corpo e a paisagem.',
    'A morte de Ofélia, personagem de Hamlet, é transposta para um cortejo de árvores, água e silêncio.',
    'O fabrico de caixões é tratado através de imagens de costura e vestuário; a familiaridade do ofício convive com a ironia e a morte.',
    'As vozes do primeiro homem e dos elementos naturais transformam a solidão inicial num diálogo dramático com a paisagem.',
    'A interpelação de uns olhos abre uma meditação em que amor, dor e morte são aproximados por uma linguagem de grande intensidade visual.',
    'O sono de João é descrito numa fala de cuidado e protecção. Observe como a linguagem de embalo convive com imagens de fragilidade.',
    'A solidão junto do lume convoca o tédio e as horas demoradas; o espaço doméstico torna-se lugar de interrogação e recordação.',
    'A espera de uma sombra desejada transforma a noite num espaço de escuta, sinal e aproximação.',
    'O cachimbo é tratado como objecto ritual e veículo de lembrança; fumar torna presente um tempo familiar já desaparecido.',
    'A dedicatória memorial enquadra uma meditação sobre o corpo e a morte. A decomposição gráfica do título evoca uma fórmula latina associada ao cadáver.',
    'A fala dirigida ao abade imagina os preparativos do próprio enterro, usando detalhes concretos para aproximar humor e mortalidade.',
    'A caminhada nocturna de uma velha é acompanhada pelos sons da natureza e pela interpelação da voz poética.',
    'A estadia numa aldeia, à procura de saúde, torna-se relato de sofrimento físico e espiritual, entre a atenção dos outros e a solidão íntima.',
    'O poema final distribui a fala por várias personagens. O Hotel da Cova aproxima a morte de uma hospedagem e encerra o livro com o desejo de dormir.',
]
ANTERO_TITLE_CONTEXTS = {
    'ignoto deo': 'O título latino, «ao deus desconhecido», enquadra a procura de uma beleza que ultrapassa a experiência imediata.',
    'ad amicos': 'O título latino dirige o poema «aos amigos», aproximando a reflexão da forma de uma interpelação.',
    'amaritudo': 'Amaritudo significa «amargura» em latim; a palavra dá um enquadramento afectivo à leitura.',
    'mea culpa': 'A fórmula latina «minha culpa» introduz um gesto de autoavaliação através da linguagem religiosa.',
    'despondency': 'O título inglês significa abatimento ou desânimo, nomeando o estado de espírito interrogado pelo poema.',
    'justitia mater': 'O título latino apresenta a justiça como mãe, cruzando uma ideia abstracta com uma imagem de acolhimento.',
    'mors amor': 'O título aproxima duas palavras latinas, morte e amor, cuja relação orienta a leitura.',
    'mors liberatrix': 'A expressão latina significa «morte libertadora» e apresenta a morte sob uma perspectiva paradoxal de libertação.',
    'anima mea': 'A expressão latina significa «minha alma» e enquadra a voz de uma interrogação interior.',
    'nox': 'Nox significa «noite» em latim; a imagem nocturna acompanha o movimento de interrogação metafísica.',
    'nirvana': 'O título toma um termo budista ligado à libertação do sofrimento e reinterpreta-o no horizonte filosófico do poema.',
    'solemnia verba': 'A expressão latina significa «palavras solenes»; o título assinala o tom meditativo da composição.',
    'na mao de deus': 'O poema aproxima a imagem da mão divina do repouso da consciência; o último verso repete uma formulação citada no prefácio.',
    'a ideia': 'Os oito sonetos do ciclo mantêm a numeração original, permitindo acompanhar as mudanças de uma mesma interrogação filosófica.',
    'elogio da morte': 'Os seis sonetos permanecem reunidos como um ciclo; observe como uma mesma figura é interrogada através de imagens sucessivas.',
}

def import_so():
    soup = source('17193')
    dedication = soup.find(id='id00012')
    stop = soup.find(id='id00759')
    headings = [p for p in soup.find_all('p') if 'id00014' <= p.get('id', '') < 'id00759'
                and re.search(r'margin-top:\s*[45]em', p.get('style', ''))]
    assert len(headings) == len(SO_CONTEXTS) == 29, f'Só: esperava 29 poemas, encontrei {len(headings)}'
    _, blocks = pieces(soup, [dedication] + headings, stop)
    chapters = []
    for index, (heading, content) in enumerate(zip([dedication] + headings, blocks)):
        title = title_text(heading).replace('S.^{ta} Iria', 'Santa Iria')
        if index == 0:
            title = 'Memória à minha mãe, ao meu pai'
        chapters.append(chapter_record(f'poema-{index:02d}', title, 'Dedicatória' if index == 0 else 'Poesia',
                        'O poema de dedicatória apresenta os vínculos familiares e a origem da voz que atravessa o livro.' if index == 0 else
                        SO_CONTEXTS[index - 1],
                        poetry_text(without_heading(content, heading)), SO_NOTES, minimum_length=30))
    book = book_meta(20, 'so', 'Só', 'António Nobre', 'antonio-nobre',
         'Poeta português (1867–1900), cuja escrita aproxima a memória de infância, a saudade, a linguagem familiar e a experiência do exílio.', 1892,
         'A primeira edição da colectânea de António Nobre, entre memória familiar, paisagens portuguesas, doença, viagem e saudade.',
         ['poesia', 'saudade', 'memória', 'Paris'], '17193', 'Só — Léon Vanier, Paris, 1892', BNP,
         'Poema de dedicatória e os 29 poemas listados na tábua da primeira edição de 1892. Não incorpora poemas acrescentados em edições posteriores. Preserva versos, estrofes, datas, dedicatórias e a grafia da fonte; exclui índice e colofão. António Nobre morreu em 1900.')
    save_book(book['slug'], book, chapters)
    return book


def import_antero():
    soup = source('20142')
    stop = soup.find(id='id00790')
    headings, sections = [], []
    section = 'Poemas de abertura'
    period_tags = []
    for tag in soup.find_all(['h2', 'p']):
        if not ('id00105' <= tag.get('id', '') < 'id00790'):
            continue
        if tag.name != 'h2' and 'margin-top: 4em' not in tag.get('style', ''):
            continue
        title = title_text(tag)
        if re.fullmatch(r'\d{4}\s*[—–-]\s*\d{4}', title):
            section = title
            period_tags.append(tag)
            continue
        headings.append(tag)
        sections.append(section)
    assert len(headings) == 99, f'Antero: esperava 99 unidades poéticas, encontrei {len(headings)}'
    for tag in period_tags:
        tag.decompose()
    intro = soup.find(id='id00017')
    _, blocks = pieces(soup, [intro] + headings, stop)
    chapters = [chapter_record('prefacio-oliveira-martins', 'Prefácio de Oliveira Martins', 'Prefácio',
                'Oliveira Martins apresenta a personalidade e a poesia de Antero, numa leitura crítica datada do século XIX. Este prefácio é distinguido dos poemas do autor.', prose(blocks[0]), ANTERO_NOTES)]
    totals = Counter(normalized_heading(title_text(h)) for h in headings)
    seen = Counter()
    for index, (heading, content, section) in enumerate(zip(headings, blocks[1:], sections), 1):
        title = title_text(heading)
        key = normalized_heading(title)
        seen[key] += 1
        if totals[key] > 1:
            title += f' ({seen[key]})'
        context = ('Este poema precede a organização cronológica dos sonetos na edição de 1886.' if section == 'Poemas de abertura' else
                   f'Esta unidade integra o período {section} da edição de 1886. Os ciclos de vários sonetos mantêm a numeração interna da fonte.')
        focus = ANTERO_TITLE_CONTEXTS.get(key)
        context += ' ' + (focus or 'Observe a relação entre a forma poética, a dúvida, o desejo de conhecimento e a procura de repouso.')
        chapters.append(chapter_record(f'poema-{index:03d}', title, section, context, poetry_text(without_heading(content, heading)).replace('Dorme na não de Deus eternamente!', 'Dorme na mão de Deus eternamente!'), ANTERO_NOTES, minimum_length=100))
    book = book_meta(21, 'os-sonetos-completos-de-antero-de-quental', 'Os Sonetos Completos de Antero de Quental', 'Antero de Quental', 'antero-de-quental',
         'Poeta e pensador português (1842–1891), figura da Geração de 70, cuja poesia interroga a consciência, o ideal, a fé e o sofrimento.', 1886,
         'A edição de 1886 apresentada por Oliveira Martins, com poemas de abertura e sonetos organizados por períodos da vida do poeta.',
         ['poesia', 'sonetos', 'filosofia', 'Geração de 70'], '20142', 'Os Sonetos Completos de Anthero de Quental — Livraria Portuense, 1886',
         'Project Gutenberg; transcrição de Pedro Saborano, Ricardo Diogo e Tiago Tejo, editada por Rita Farinha, com referência à Biblioteca Nacional Digital.',
         'Inclui o prefácio de Oliveira Martins e 99 unidades tituladas de poesia: os poemas de abertura e os sonetos ou ciclos da edição de 1886. Ciclos com vários sonetos permanecem reunidos e títulos repetidos recebem um número apenas na navegação. Mantém versos, estrofes, períodos cronológicos e grafia da fonte; exclui o índice por primeiros versos. No último poema, corrige-se a gralha «Dorme na não de Deus» para «Dorme na mão de Deus», leitura confirmada pela citação do mesmo verso no prefácio da própria edição. Antero morreu em 1891 e Oliveira Martins em 1894.')
    save_book(book['slug'], book, chapters)
    return book


def update_catalog(books):
    path = ROOT / 'data' / 'books.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    additions = {book['slug']: {k: v for k, v in book.items() if k not in {'source', 'chapterOrder'}} for book in books}
    catalog = [additions.pop(item['slug'], item) for item in catalog]
    catalog.extend(additions.values())
    assert len({item['id'] for item in catalog}) == len(catalog), 'IDs duplicados no catálogo'
    assert len({item['slug'] for item in catalog}) == len(catalog), 'Slugs duplicados no catálogo'
    write_json(path, catalog)


def main():
    global SOURCE_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, help='Cache local opcional de HTMLs Gutenberg <id>.html')
    args = parser.parse_args()
    SOURCE_DIR = args.source_dir
    books = [import_eurico(), import_queda(), import_crime(), import_reliquia(), import_ramires(), import_so(), import_antero()]
    update_catalog(books)
    print('Sete obras importadas; execute build_books.py e build_pdfs.py para compilar as edições.')


if __name__ == '__main__':
    main()
