#!/usr/bin/env python3
"""Import the complete public-domain editions used by this library.

Sources: Project Gutenberg #40409 (Os Maias) and the 1934 edition of
Mensagem transcribed at Portuguese Wikisource. The latter is CC BY-SA 4.0.
"""

import json
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "data" / "books"
USER_AGENT = "Livros-de-Portugal/1.0 (public-domain text importer)"

MESSAGE_POEMS = [
    ("O dos Castellos", "A Europa jaz, posta nos cotovellos:", "A Europa é representada como uma figura reclinada; Portugal ocupa o rosto voltado para o Ocidente, imagem que abre a construção simbólica do livro."),
    ("O das Quinas", "Os Deuses vendem o que dão.", "As cinco quinas do escudo português tornam-se uma meditação sobre sacrifício, sofrimento e glória."),
    ("Ulysses", "O mytho é o nada que é tudo.", "Ulisses surge como fundador lendário de Lisboa. O poema explora como o mito, mesmo sem prova histórica, pode dar forma à identidade coletiva."),
    ("Viriato", "Se a alma que sente e faz conhece", "Viriato representa a resistência lusitana a Roma e uma memória anterior à fundação do reino português."),
    ("O Conde D. Henrique", "Todo começo é involuntário.", "Henrique de Borgonha recebe o condado portucalense; o poema apresenta a origem política de Portugal como parte de um desígnio ainda por cumprir."),
    ("D. Tareja", "As nações todas são mysterios.", "Teresa de Leão, mãe de Afonso Henriques, é retratada no limiar entre a herança leonesa e a formação de um reino próprio."),
    ("D. Affonso Henriques", "Pai, foste cavalleiro.", "Afonso Henriques é lembrado como fundador do reino e primeiro rei de Portugal."),
    ("D. Diniz", "Na noite escreve um seu Cantar de Amigo", "D. Dinis reúne as figuras do rei e do poeta. O pinhal de Leiria liga a cultura à preparação marítima do país."),
    ("D. João O Primeiro", "O homem e a hora são um só", "O poema evoca a crise de 1383–1385 e a ascensão de D. João I, associando o seu reinado à consolidação da independência."),
    ("D. Philippa de Lencastre", "Que enigma havia em teu seio", "Filipa de Lencastre é apresentada como mãe da geração régia ligada à expansão portuguesa, conhecida como Ínclita Geração."),
    ("D. Duarte Rei de Portugal", "Meu dever fez-me, como Deus ao mundo.", "D. Duarte é lembrado pelo sentido de dever e pela reflexão moral que marcou a sua imagem de rei-filósofo."),
    ("D. Fernando Infante de Portugal", "Deu-me Deus o seu gladio, porque eu faça", "O Infante D. Fernando, capturado em Tânger e morto em cativeiro, torna-se símbolo de sacrifício e fidelidade à missão régia."),
    ("D. Pedro Regente de Portugal", "Claro em pensar, e claro no sentir", "D. Pedro, duque de Coimbra e regente, representa a tensão entre lucidez política e o conflito que terminou na batalha de Alfarrobeira."),
    ("D. João, Infante de Portugal", "Não fui alguém. Minha alma estava estreita", "O poema transforma a figura do Infante D. João numa presença discreta, cuja importância se mede pelo destino que não chegou a realizar."),
    ("D. Sebastião, Rei de Portugal", "Louco, sim, louco, porque quiz grandeza", "A voz do rei desaparecido em Alcácer-Quibir assume a loucura como preço de desejar uma grandeza para além do possível."),
    ("Nunalvares Pereira", "Que auréola te cerca?", "Nuno Álvares Pereira, condestável decisivo na crise de 1383–1385, é convertido em figura de santidade e proteção nacional."),
    ("O Infante D. Henrique", "Em seu throno entre o brilho das espheras", "O Infante D. Henrique aparece como cabeça do grifo heráldico e impulsionador simbólico da expansão marítima."),
    ("D. João o Segundo", "Braços cruzados, fita além do mar.", "D. João II é associado à visão estratégica que preparou a passagem do reconhecimento costeiro à rota para a Índia."),
    ("Affonso de Albuquerque", "De pé, sobre os paizes conquistados", "Afonso de Albuquerque, governador da Índia portuguesa, completa o grifo como figura da expansão imperial no Oriente."),
    ("O Infante", "Deus quer, o homem sonha, a obra nasce.", "O poema condensa a ideia de que a vontade humana, quando encontra um propósito maior, transforma o sonho em ação histórica."),
    ("Horizonte", "Ó mar anterior a nós, teus medos", "A travessia do mar surge como passagem do medo para o conhecimento, sem apagar o custo humano da expansão."),
    ("Padrão", "O esforço é grande e o homem é pequeno.", "O padrão de pedra deixado pelos navegadores marca a presença portuguesa e a distância entre a fragilidade humana e a ambição histórica."),
    ("O Mostrengo", "O mostrengo que está no fim do mar", "O Mostrengo dramatiza o medo do desconhecido no Cabo das Tormentas, enfrentado por um marinheiro que fala em nome do rei."),
    ("Epitaphio de Bartholomeu Dias", "Jaz aqui, na pequena praia extrema", "Bartolomeu Dias dobrou o Cabo da Boa Esperança em 1488; o epitáfio liga a descoberta à morte no mar."),
    ("Os Colombos", "Outros haverão de ter", "O título plural amplia a figura de Colombo para falar dos que sonham e descobrem, mas não chegam a possuir plenamente a própria descoberta."),
    ("Occidente", "Com duas mãos — o Acto e o Destino", "O poema associa o Ocidente a Portugal por meio de uma imagem de criação em que ação humana e destino se cruzam."),
    ("Fernão de Magalhães", "No valle «Afundam, como os navios»,", "Magalhães, navegador português ao serviço de Castela, comandou a expedição que iniciou a primeira circum-navegação do globo."),
    ("Ascensão de Vasco da Gama", "Os Deuses da tormenta e os gigantes da terra", "Vasco da Gama é elevado a figura mítica; a viagem marítima converte-se numa ascensão de alcance espiritual."),
    ("Mar Portuguez", "Ó mar salgado, quanto do teu sal", "A expansão marítima é apresentada pelo seu custo humano: lágrimas, perdas e sofrimento acompanham cada descoberta."),
    ("A Ultima Nau", "Levando a bordo El-Rei D. Sebastião", "A nau de D. Sebastião parte para Alcácer-Quibir e regressa como lenda; o poema aproxima a derrota do mito do Encoberto."),
    ("Prece (Fernando Pessoa)", "Senhor, a noite veio e a alma é vil.", "A oração pede um novo impulso coletivo depois do declínio, retomando a imagem da espera por uma manhã portuguesa."),
    ("D. Sebastião", "'Sperai! Cahí no areal e na hora adversa", "A figura de D. Sebastião passa da derrota histórica à esperança messiânica do seu regresso."),
    ("O Quinto Império", "Triste de quem vive em casa", "O Quinto Império é apresentado como renovação espiritual e cultural, não apenas como domínio territorial."),
    ("O Desejado (Fernando Pessoa)", "Onde quer que, entre sombras e dizeres", "O Desejado representa a esperança projetada numa figura ainda ausente, ligada à expectativa sebastianista."),
    ("As Ilhas Afortunadas", "Que voz vem no som das ondas", "As ilhas afortunadas pertencem à geografia mítica do Ocidente e simbolizam um lugar de espera e revelação."),
    ("O Encoberto", "Que symbolo fecundo", "O rei oculto torna-se símbolo de uma promessa nacional por cumprir e de uma identidade ainda em transformação."),
    ("O Bandarra", "Sonhava, anonymo e disperso", "Gonçalo Anes Bandarra, sapateiro e autor de trovas proféticas, tornou-se uma das fontes do sebastianismo."),
    ("António Vieira (Mensagem)", "O céu strella o azul e tem grandeza.", "O padre António Vieira é lembrado pela força da palavra e pela expectativa profética do Quinto Império."),
    ("Screvo meu livro à beira-magoa", "Screvo meu livro à beira-magoa.", "A voz do poema transforma a escrita numa forma de espera, entre a perda do passado e a possibilidade de um futuro."),
    ("Noite", "Não sei a hora, mas sei que ha a hora", "A noite representa o período de suspensão anterior a uma mudança, mantendo viva a expectativa de uma hora decisiva."),
    ("Tormenta", "Que jaz no abysmo sob o mar que se ergue?", "A tormenta é uma crise coletiva que pode preceder a mudança; o poema pergunta que força profunda ainda move Portugal."),
    ("Calma", "Que Voz vem no som das ondas", "A calma depois da tormenta é uma pausa de escuta e preparação, não a resolução definitiva da espera."),
    ("Antemanhã", "O DESEJADO", "A antemanhã é o instante incerto antes do amanhecer, imagem de um futuro que ainda não se revelou."),
    ("Nevoeiro", "Nem rei nem lei, nem paz nem guerra", "O nevoeiro traduz a indefinição de Portugal e culmina no apelo 'É a Hora!', fecho aberto à possibilidade de renovação."),
]

MESSAGE_GROUPS = {
    "O dos Castellos": "Brasão — Os Campos",
    "O das Quinas": "Brasão — Os Campos",
    "Ulysses": "Brasão — Os Castelos",
    "Viriato": "Brasão — Os Castelos",
    "O Conde D. Henrique": "Brasão — Os Castelos",
    "D. Tareja": "Brasão — Os Castelos",
    "D. Affonso Henriques": "Brasão — Os Castelos",
    "D. Diniz": "Brasão — Os Castelos",
    "D. João O Primeiro": "Brasão — Os Castelos",
    "D. Philippa de Lencastre": "Brasão — Os Castelos",
    "D. Duarte Rei de Portugal": "Brasão — As Quinas",
    "D. Fernando Infante de Portugal": "Brasão — As Quinas",
    "D. Pedro Regente de Portugal": "Brasão — As Quinas",
    "D. João, Infante de Portugal": "Brasão — As Quinas",
    "D. Sebastião, Rei de Portugal": "Brasão — As Quinas",
    "Nunalvares Pereira": "Brasão — A Coroa",
    "O Infante D. Henrique": "Brasão — O Timbre",
    "D. João o Segundo": "Brasão — O Timbre",
    "Affonso de Albuquerque": "Brasão — O Timbre",
    "O Infante": "Mar Portuguez",
    "Horizonte": "Mar Portuguez",
    "Padrão": "Mar Portuguez",
    "O Mostrengo": "Mar Portuguez",
    "Epitaphio de Bartholomeu Dias": "Mar Portuguez",
    "Os Colombos": "Mar Portuguez",
    "Occidente": "Mar Portuguez",
    "Fernão de Magalhães": "Mar Portuguez",
    "Ascensão de Vasco da Gama": "Mar Portuguez",
    "Mar Portuguez": "Mar Portuguez",
    "A Ultima Nau": "Mar Portuguez",
    "Prece (Fernando Pessoa)": "Mar Portuguez",
    "D. Sebastião": "O Encoberto — Os Símbolos",
    "O Quinto Império": "O Encoberto — Os Símbolos",
    "O Desejado (Fernando Pessoa)": "O Encoberto — Os Símbolos",
    "As Ilhas Afortunadas": "O Encoberto — Os Símbolos",
    "O Encoberto": "O Encoberto — Os Símbolos",
    "O Bandarra": "O Encoberto — Os Avisos",
    "António Vieira (Mensagem)": "O Encoberto — Os Avisos",
    "Screvo meu livro à beira-magoa": "O Encoberto — Os Avisos",
    "Noite": "O Encoberto — Os Tempos",
    "Tormenta": "O Encoberto — Os Tempos",
    "Calma": "O Encoberto — Os Tempos",
    "Antemanhã": "O Encoberto — Os Tempos",
    "Nevoeiro": "O Encoberto — Os Tempos",
}

MESSAGE_SECTION_CONTEXTS = {
    "Brasão — Os Campos": "A abertura de Brasão apresenta Portugal por meio da geografia e dos símbolos do escudo nacional.",
    "Brasão — Os Castelos": "Esta secção reúne figuras lendárias e históricas associadas às origens e à formação do reino.",
    "Brasão — As Quinas": "As Quinas evocam membros da família real e os sacrifícios ligados à história portuguesa.",
    "Brasão — A Coroa": "A Coroa destaca Nuno Álvares Pereira como figura militar e espiritual da memória nacional.",
    "Brasão — O Timbre": "O Timbre organiza três figuras da expansão portuguesa segundo as partes do grifo heráldico.",
    "Mar Portuguez": "Mar Portuguez desloca o foco dos símbolos e governantes para as viagens, os navegadores e o custo humano da expansão marítima.",
    "O Encoberto — Os Símbolos": "Os Símbolos retomam o sebastianismo e a ideia de uma missão colectiva ainda por realizar.",
    "O Encoberto — Os Avisos": "Os Avisos reúnem vozes proféticas e a reflexão do poeta sobre a escrita e o destino de Portugal.",
    "O Encoberto — Os Tempos": "Os Tempos descreve uma passagem alegórica da noite e da tormenta para a expectativa de uma nova manhã.",
}

MAIAS_CONTEXTS = [
    "A abertura apresenta o Ramalhete e a situação da família Maia em Lisboa, combinando descrição minuciosa, memória familiar e presságios de ruína.",
    "A narrativa acompanha Pedro e Maria Monforte numa viagem pela Itália e reconstrói as circunstâncias que conduzem à separação da família.",
    "A visita de Villaça a Santa Olávia retoma a história dos Maias e mostra a infância de Carlos sob a educação do avô.",
    "Carlos prepara-se para concluir Medicina em Coimbra; o capítulo observa a sua formação e os primeiros planos para a vida adulta.",
    "Carlos regressa ao Ramalhete e encontra a casa e os amigos de Afonso, num capítulo que apresenta a sociabilidade da geração mais velha.",
    "Carlos visita a casa de Ega e percorre os círculos literários e mundanos que cercam o seu amigo em Lisboa.",
    "Afonso e Craft conversam no Ramalhete; a discussão sobre a vida social e os projectos de Carlos dá lugar a novos planos de convívio.",
    "A procura de Cruges leva Carlos e os seus amigos pela cidade; o episódio acompanha os preparativos e os encontros que antecedem a soirée dos Cohens.",
    "A soirée dos Cohens reúne a sociedade lisboeta e aproxima Carlos de Maria Eduarda, enquanto a relação de Ega com Raquel Cohen ganha relevo.",
    "Carlos volta a encontrar Maria Eduarda e inicia uma aproximação marcada pelo segredo, pela curiosidade e pela vida social da cidade.",
    "Carlos visita Maria Eduarda e começa a conhecer o espaço doméstico e a história que ela partilha com a família Gomes.",
    "Ega regressa inesperadamente a Lisboa e procura Carlos; a sua chegada reabre a história de Raquel Cohen e a ligação ao círculo dos Maias.",
    "Ega conta a Carlos o que sabe sobre a relação de Maria Cohen e sobre o passado de Maria Eduarda, preparando a revelação central do romance.",
    "Afonso parte para Santa Olávia e Carlos fica em Lisboa; a narrativa acompanha a relação com Maria Eduarda e a mudança para os Olivais.",
    "A vida de Carlos e Maria Eduarda nos Olivais aprofunda o idílio amoroso e aproxima a narrativa da verdade sobre as suas origens.",
    "Os compromissos sociais e o sarau da Trindade contrastam com a relação privada de Carlos e Maria Eduarda e com o segredo que a ameaça.",
    "A revelação do parentesco entre Carlos e Maria Eduarda transforma a paixão em tragédia; Ega e Afonso enfrentam as consequências da verdade.",
    "O epílogo passa alguns anos e mostra Carlos e Ega de regresso a Lisboa, confrontados com a memória e com a passagem do tempo.",
]

MAIAS_NOTES = [
    ("Ramalhete", "A casa da família em Lisboa funciona como cenário e símbolo da história dos Maias; a sua decadência acompanha a dos seus moradores."),
    ("Santa Olavia", "A quinta dos Maias no Douro representa o retiro familiar e contrasta com a vida social de Lisboa."),
    ("Santa Olávia", "A quinta dos Maias no Douro representa o retiro familiar e contrasta com a vida social de Lisboa."),
    ("Regeneração", "Período político iniciado em 1851, associado a reformas e obras públicas; é um dos temas das conversas satirizadas no romance."),
    ("Coimbra", "Cidade universitária onde Carlos estuda Medicina; o romance contrapõe a formação académica à vida prática e social de Lisboa."),
    ("Maria Monforte", "Mãe de Carlos e de Maria Eduarda; a sua fuga com Tancredo desencadeia a separação da família Maia."),
    ("Tancredo", "O príncipe italiano por quem Maria Monforte abandona Pedro, abrindo a primeira grande ruptura familiar do romance."),
    ("Affonso da Maia", "Patriarca dos Maias, liberal e avô de Carlos; representa a continuidade familiar e um ideal de rigor moral."),
    ("Afonso da Maia", "Patriarca dos Maias, liberal e avô de Carlos; representa a continuidade familiar e um ideal de rigor moral."),
    ("Carlos da Maia", "Protagonista do romance, médico formado em Coimbra, cuja educação e projectos entram em conflito com a inércia social que o rodeia."),
    ("Pedro da Maia", "Filho de Afonso e pai de Carlos; a sua sensibilidade e dependência afectiva antecedem a tragédia da família."),
    ("Villaça", "Administrador da família Maia e testemunha das mudanças na casa e na fortuna dos seus proprietários."),
    ("Vilaça", "Administrador da família Maia e testemunha das mudanças na casa e na fortuna dos seus proprietários."),
    ("João da Ega", "Amigo íntimo de Carlos, estudante e escritor; as suas ideias ambiciosas contrastam muitas vezes com a sua dificuldade em agir."),
    ("Ega", "João da Ega, amigo de Carlos e figura central nas conversas literárias e políticas do romance."),
    ("Dâmaso", "Dâmaso Salcede encarna o novo-rico superficial e a dependência de modelos sociais importados."),
    ("Alencar", "Poeta romântico cuja presença permite ao romance satirizar a sobrevivência de estilos e poses literárias do século XIX."),
    ("Cruges", "Músico talentoso e reservado, cuja sensibilidade artística contrasta com a conversa mundana dos salões lisboetas."),
    ("Gouvarinho", "O conde e a condessa de Gouvarinho pertencem à elite política e social que o romance observa com ironia."),
    ("Maria Eduarda", "A mulher por quem Carlos se apaixona; a sua identidade e história familiar reorientam toda a tragédia do romance."),
    ("Castro Gomes", "Apresentado como marido de Maria Eduarda, é uma peça decisiva na revelação da identidade dela."),
    ("Hotel Central", "Espaço de encontro da elite lisboeta, onde o convívio social e o debate público se tornam matéria de observação satírica."),
    ("Chiado", "Zona central de Lisboa associada ao passeio, à sociabilidade urbana e à observação dos costumes contemporâneos."),
    ("Avenida da Liberdade", "A grande avenida aberta em Lisboa na década de 1880 simboliza a modernização urbana e a imitação de modelos europeus."),
    ("Jockey Club", "Clube ligado às corridas de cavalos e à sociabilidade elegante da elite lisboeta oitocentista."),
]


def fetch(url):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            time.sleep(2 ** attempt)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(value):
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


class PoemText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.lines = []
        self.current = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.depth and tag == "div" and "poem" in attrs.get("class", "").split():
            self.depth = 1
            return
        if self.depth:
            if tag == "div":
                self.depth += 1
            elif tag == "br":
                self._newline()
            elif tag in {"p", "blockquote"}:
                self._newline()

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "div":
            self.depth -= 1
            if not self.depth:
                self._newline()
        elif tag in {"p", "blockquote"}:
            self._newline()

    def handle_data(self, data):
        if self.depth:
            value = data.replace("\xa0", " ")
            if value.strip():
                self.current.append(value)

    def _newline(self):
        line = re.sub(r"\s+", " ", "".join(self.current)).strip()
        if line:
            self.lines.append(line)
        self.current = []

    def text(self):
        self._newline()
        return "\n".join(self.lines).strip()


def import_mensagem():
    book_dir = BOOKS_DIR / "mensagem"
    chapters = []
    for position, (title, target, note) in enumerate(MESSAGE_POEMS, start=1):
        query = urlencode({"action": "parse", "page": title, "prop": "text", "format": "json"})
        payload = json.loads(fetch("https://pt.wikisource.org/w/api.php?" + query))
        html = payload.get("parse", {}).get("text", {}).get("*")
        if not html:
            raise RuntimeError(f"Wikisource não devolveu o poema: {title}")
        parser = PoemText()
        parser.feed(html)
        content = parser.text()
        if not content:
            raise RuntimeError(f"Não foi possível extrair o poema: {title}")
        safe_title = slugify(title)
        actual_target = target if target in content else content.splitlines()[0]
        chapter = {
            "slug": safe_title,
            "title": title,
            "section": MESSAGE_GROUPS[title],
            "context": MESSAGE_SECTION_CONTEXTS[MESSAGE_GROUPS[title]],
            "content": content,
            "audioUrl": "",
            "audioDuration": "",
            "annotations": [{"target": actual_target, "text": note}],
        }
        write_json(book_dir / "chapters" / f"{safe_title}.json", chapter)
        chapters.append(safe_title)
        print(f"Mensagem {position:02d}/44: {title} ({len(content)} caracteres)")
        # Wikisource applies conservative per-client request limits.
        time.sleep(7)

    book = json.loads((book_dir / "book.json").read_text(encoding="utf-8"))
    book.update({
        "chapterOrder": chapters,
        "source": {
            "title": "Mensagem (edição de 1934)",
            "url": "https://pt.wikisource.org/wiki/Mensagem_(Fernando_Pessoa)",
            "transcription": "Wikisource lusófona; licença CC BY-SA 4.0",
            "editorialNote": "Texto transcrito segundo a edição de 1934; grafia original preservada.",
        },
    })
    write_json(book_dir / "book.json", book)
    for path in (book_dir / "chapters").glob("*.json"):
        if path.stem not in chapters:
            path.unlink()


ROMAN = r"(?:I|II|III|IV|V|VI|VII|VIII|IX|X)"


def normalize_prose(lines):
    blocks = []
    current = []
    for raw in lines:
        line = raw.strip()
        if not line:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"\s+", " ", line)
        if current and current[-1].endswith("-") and not current[-1].endswith("--"):
            current[-1] = current[-1][:-1] + line
        else:
            current.append(line)
    if current:
        blocks.append(" ".join(current))
    text = "\n\n".join(blocks)
    text = text.replace("_", "")
    return text.strip()


def import_os_maias():
    raw = fetch("https://www.gutenberg.org/cache/epub/40409/pg40409.txt").decode("utf-8-sig")
    lines = raw.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "OS MAIAS" and i > 90)
    heading_re = re.compile(rf"^\s*({ROMAN})\s*$")
    headings = []
    for index in range(start + 1, len(lines)):
        if "*** END OF THE PROJECT GUTENBERG EBOOK" in lines[index]:
            break
        match = heading_re.match(lines[index])
        if match:
            headings.append((index, match.group(1)))
    if len(headings) != 18:
        raise RuntimeError(f"Esperava 18 capítulos em Os Maias; encontrei {len(headings)}.")

    book_dir = BOOKS_DIR / "os-maias"
    chapters = []
    for index, (heading_index, roman) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else next(
            i for i in range(heading_index, len(lines)) if "*** END OF THE PROJECT GUTENBERG EBOOK" in lines[i]
        )
        content = normalize_prose(lines[heading_index + 1:end])
        if len(content) < 1000:
            raise RuntimeError(f"Capítulo {index + 1} de Os Maias parece incompleto ({len(content)} caracteres).")
        volume = 1 if index < 10 else 2
        chapter_number = index + 1 if volume == 1 else index - 9
        slug = f"volume-{volume}-capitulo-{chapter_number:02d}"
        chapter = {
            "slug": slug,
            "title": f"Volume {volume} · Capítulo {chapter_number}",
            "section": f"Volume {volume}",
            "context": MAIAS_CONTEXTS[index],
            "content": content,
            "audioUrl": "",
            "audioDuration": "",
            "annotations": [],
        }
        chapter["annotations"] = [
            {"target": target, "text": text}
            for target, text in MAIAS_NOTES
            if target.casefold() in content.casefold()
        ][:5]
        write_json(book_dir / "chapters" / f"{slug}.json", chapter)
        chapters.append(slug)
        print(f"Os Maias volume {volume}, capítulo {chapter_number:02d}: {len(content)} caracteres")

    book = json.loads((book_dir / "book.json").read_text(encoding="utf-8"))
    book.update({
        "chapterOrder": chapters,
        "source": {
            "title": "Os Maias: episódios da vida romântica (1888)",
            "url": "https://www.gutenberg.org/ebooks/40409",
            "transcription": "Project Gutenberg e Biblioteca Nacional de Portugal",
            "editorialNote": "Transcrição da edição de 1888; ortografia original preservada. Os dois volumes originais foram reunidos numa sequência de 16 capítulos.",
        },
    })
    write_json(book_dir / "book.json", book)
    for path in (book_dir / "chapters").glob("*.json"):
        if path.stem not in chapters:
            path.unlink()


def main():
    try:
        import_mensagem()
        import_os_maias()
        print("Importação concluída. Execute scripts/build_books.py para compilar a biblioteca.")
    except Exception as exc:
        print(f"Erro de importação: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
