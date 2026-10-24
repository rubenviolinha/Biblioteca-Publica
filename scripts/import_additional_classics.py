#!/usr/bin/env python3
"""Import six Portuguese classics from documented Project Gutenberg editions.

The novels' original authors are long deceased. Project Gutenberg's own
notices describe US status, so each book also records its Portuguese source
edition and cautions readers to distinguish the underlying work from a modern
transcription or edition.
"""

import json
import re
import sys
from pathlib import Path

from import_public_domain import fetch, normalize_prose, write_json


ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "data" / "books"
ROMAN = r"(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXI|XXII|XXIII|XXIV|XXV|XXVI|XXVII|XXVIII|XXIX|XXX|XXXI|XXXII|XXXIII|XXXIV|XXXV|XXXVI|XXXVII|XXXVIII|XXXIX|XL|XLI|XLII|XLIII|XLIV|XLV|XLVI|XLVII|XLVIII|XLIX)"


VIAGENS_CONTEXTS = {
    "I": "A partida de Lisboa transforma uma viagem próxima numa ocasião para pensar a literatura, a política e o próprio acto de narrar.",
    "II": "A viagem pelo Tejo e a chegada a Vila Nova da Rainha põem em contacto o narrador com os passageiros, os costumes e as paisagens da margem.",
    "III": "A contemplação do Tejo e das povoações ribeirinhas leva o narrador a interromper o relato de viagem com reflexões sobre Portugal.",
    "IV": "A passagem por Azambuja e pela estalagem aprofunda o contraste entre a paisagem real e os modelos idealizados da literatura.",
    "V": "A viagem prossegue entre observações sobre os viajantes, a sociedade e as mudanças que o país atravessa.",
    "VI": "O narrador aproxima a paisagem de Santarém da memória histórica e da decadência dos monumentos nacionais.",
    "VII": "O percurso e as conversas abrem espaço a uma reflexão sobre a história política portuguesa e as suas divisões.",
    "VIII": "A entrada em Santarém reúne a experiência concreta da viagem e a procura de vestígios de um passado mais glorioso.",
    "IX": "A cidade e os seus edifícios antigos tornam-se matéria para pensar a distância entre a memória histórica e o presente.",
    "X": "A narrativa muda de plano e apresenta a história de Joaninha, da avó e dos dois homens ligados ao seu destino.",
    "XI": "A história de Joaninha é contada através da vida no Vale de Santarém e da relação entre a jovem e a sua avó.",
    "XII": "A chegada de Carlos altera a rotina do vale e introduz uma tensão entre a vida doméstica e a guerra civil.",
    "XIII": "O passado de Carlos e a sua ligação a Joaninha ganham relevo, enquanto a guerra separa a família.",
    "XIV": "A narrativa aproxima os sentimentos de Joaninha e Carlos do conflito entre os liberais e os absolutistas.",
    "XV": "As cartas e as memórias revelam como a guerra e as escolhas familiares conduziram os protagonistas à separação.",
    "XVI": "O narrador retoma a história de Carlos e confronta as esperanças amorosas com a experiência da guerra.",
    "XVII": "A presença de Frei Dinis liga o passado familiar às consequências políticas e morais do conflito.",
    "XVIII": "O capítulo aprofunda os segredos que explicam a relação entre Frei Dinis, a avó e a família de Joaninha.",
    "XIX": "A história familiar é revista à luz da guerra e das decisões que marcaram a vida de Carlos.",
    "XX": "O percurso de Carlos e Joaninha expõe o custo íntimo da guerra e a fragilidade das promessas de regresso.",
    "XXI": "As personagens enfrentam as consequências de uma guerra que transforma a vida privada e a paisagem do país.",
    "XXII": "O narrador aproxima a experiência de Carlos da história política recente e das mudanças de regime.",
    "XXIII": "O passado dos protagonistas e as divisões entre as famílias tornam-se mais claros à medida que o relato avança.",
    "XXIV": "A narrativa articula a história amorosa com as mudanças políticas que interromperam a vida no vale.",
    "XXV": "O reencontro e a memória dos acontecimentos anteriores preparam uma mudança decisiva no destino das personagens.",
    "XXVI": "A guerra e as escolhas de Carlos conduzem a história para longe da tranquilidade que Joaninha conheceu.",
    "XXVII": "A notícia e as cartas fazem regressar o passado, alterando o modo como as personagens compreendem a sua história.",
    "XXVIII": "As personagens confrontam-se com a distância entre os ideais de juventude e as consequências das suas escolhas.",
    "XXIX": "O desenlace aproxima a história de Joaninha do regresso do narrador à viagem e ao presente.",
    "XXX": "O regresso ao enquadramento da viagem permite ao narrador comparar o vale lembrado com a realidade observada.",
    "XXXI": "O narrador comenta a sociedade contemporânea e o modo como a política molda a vida quotidiana.",
    "XXXII": "A observação dos costumes e das instituições prolonga a crítica à imitação social e à falta de iniciativa.",
    "XXXIII": "A paisagem e a conversa conduzem a novas considerações sobre a identidade portuguesa e o seu futuro.",
    "XXXIV": "O capítulo combina a experiência da viagem com uma análise satírica das convenções sociais.",
    "XXXV": "O narrador explora as contradições da sociedade liberal e a distância entre os seus princípios e a prática.",
    "XXXVI": "A reflexão política regressa à narrativa, relacionando a história recente com as expectativas do país.",
    "XXXVII": "A viagem continua entre paisagens, encontros e comentários sobre os hábitos dos portugueses.",
    "XXXVIII": "O narrador observa a vida local e contrapõe a experiência directa aos discursos grandiosos sobre o país.",
    "XXXIX": "As conversas e os episódios da viagem dão forma à crítica das hierarquias e dos costumes sociais.",
    "XL": "A narrativa aproxima-se do fim enquanto o narrador retoma os contrastes entre passado histórico e presente.",
    "XLI": "O episódio combina a observação da paisagem com a ironia dirigida à vida pública portuguesa.",
    "XLII": "O narrador reflecte sobre o poder, a sociedade e a dificuldade de transformar o país.",
    "XLIII": "A viagem oferece um novo cenário para discutir o modo como os portugueses recordam a sua história.",
    "XLIV": "O capítulo aproxima as imagens da viagem e do romance para pensar as possibilidades de mudança.",
    "XLV": "A narrativa volta à paisagem e aos encontros que acompanham o percurso até Santarém.",
    "XLVI": "O narrador observa os viajantes e os costumes locais com humor e atenção às diferenças sociais.",
    "XLVII": "A chegada e a despedida da viagem levam a uma última avaliação das instituições e da sociedade.",
    "XLVIII": "O narrador aproxima o final da viagem do desfecho sentimental e político da obra.",
    "XLIX": "O último capítulo fecha o percurso e deixa em aberto a relação entre viagem, memória e transformação nacional.",
}

VIAGENS_NOTES = [
    ("Xavier de Maistre", "Autor de Viagem à roda do meu quarto (1794), narrativa que transforma uma viagem imóvel em exercício de observação e ironia; Garrett evoca-a para justificar a sua própria viagem."),
    ("Lord Byron", "Poeta inglês associado ao Romantismo e à figura do viajante inquieto; a sua presença aproxima a viagem de Garrett de uma tradição literária europeia."),
    ("Tejo", "O rio acompanha o percurso entre Lisboa e Santarém e funciona como eixo geográfico e simbólico da narrativa."),
    ("Santarém", "Cidade ribatejana visitada pelo narrador; os seus monumentos e a sua história motivam reflexões sobre a memória nacional."),
    ("Azambuja", "Localidade ribatejana no caminho para Santarém; a passagem pela sua estalagem dá lugar a uma das cenas mais cómicas do início da viagem."),
    ("Terreiro do Paço", "Praça ribeirinha de Lisboa, ponto de partida da viagem fluvial descrita no início do livro."),
    ("Vila Nova da Rainha", "Localidade junto ao Tejo onde os passageiros desembarcam durante a viagem para Santarém."),
    ("Bordas-d'água", "Designação popular associada aos trabalhadores e habitantes das margens do Tejo; Garrett observa os seus costumes durante a viagem."),
    ("ilhavos", "Habitantes da região de Ílhavo, tradicionalmente ligados à pesca e à navegação; surgem entre os passageiros do vapor."),
    ("liberais", "Partidários do constitucionalismo liberal, que combateram os absolutistas nas guerras civis portuguesas do século XIX."),
    ("miguelistas", "Partidários de D. Miguel e da monarquia absolutista durante a guerra civil portuguesa de 1828–1834."),
    ("Frei Dinis", "Frade cuja história se cruza com a família de Joaninha; a personagem concentra segredos e consequências morais da guerra civil."),
    ("Joaninha", "Jovem que vive no Vale de Santarém com a avó; a sua história amorosa constitui o núcleo romanesco do livro."),
    ("Carlos", "Soldado liberal e primo de Joaninha; a sua trajectória liga a narrativa amorosa à guerra civil e às mudanças de regime."),
    ("Georgina", "Mulher inglesa ligada ao passado de Carlos; a sua presença complica a relação entre Carlos e Joaninha."),
    ("D. Francisca", "Avó de Joaninha, cuja história familiar se relaciona com Frei Dinis e com os acontecimentos que precedem o romance."),
    ("barão", "Figura social usada por Garrett para satirizar a ascensão burguesa, a política de favores e a transformação das antigas hierarquias."),
    ("baronesa", "Figura ligada à nova elite social que a sátira de Garrett associa à riqueza, ao prestígio e às convenções públicas."),
    ("Carta Constitucional", "Constituição outorgada por D. Pedro IV em 1826; a disputa em torno dela marcou o conflito entre liberais e absolutistas."),
    ("convento", "Os conventos e edifícios religiosos surgem como vestígios materiais de uma história em mudança e de instituições em declínio."),
    ("romance", "Garrett mistura viagem, comentário político e narrativa amorosa, brincando com as expectativas do leitor sobre o género romanesco."),
    ("Santarém", "A cidade converte a visita turística numa reflexão sobre o abandono dos monumentos e a relação dos portugueses com o passado."),
]

AMOR_CONTEXTS = [
    "O narrador apresenta a família Botelho e a educação de Simão, introduzindo as rivalidades que condicionam os dois jovens.",
    "Simão e Teresa reconhecem o amor que os une, mas a oposição entre as famílias transforma o afecto numa disputa de autoridade.",
    "As cartas e os encontros secretos mostram como Teresa e Simão tentam manter a relação apesar da vigilância familiar.",
    "A intervenção de Mariana aproxima-a de Simão e põe em marcha os actos de auxílio que definirão o seu destino.",
    "A violência entre os jovens e a família de Teresa converte a rivalidade doméstica em conflito aberto.",
    "A partida de Simão para Coimbra não interrompe a correspondência; a distância aumenta a dependência dos amantes das cartas.",
    "A pressão de Tadeu sobre Teresa torna a obediência familiar incompatível com a escolha amorosa.",
    "Os planos de casamento e de fuga revelam os limites impostos às mulheres e aos jovens pelas convenções da família.",
    "A tentativa de reunião conduz a um confronto violento e a consequências legais para Simão.",
    "O fim da primeira parte deixa Simão preso e Teresa afastada, enquanto Mariana assume um papel cada vez mais próximo.",
    "A segunda parte retoma o destino de Simão sob a ameaça do degredo e a expectativa de uma última decisão judicial.",
    "Mariana acompanha Simão e transforma a sua devoção numa presença constante ao lado do condenado.",
    "Teresa procura manter a esperança por meio das cartas, apesar da clausura e da deterioração da sua saúde.",
    "A família e as autoridades disputam o futuro de Simão, que recusa separar a liberdade da fidelidade a Teresa.",
    "A possibilidade de comutação da pena confronta Simão com a escolha entre regressar à vida e permanecer fiel ao amor.",
    "As despedidas aproximam Simão, Teresa e Mariana de um desenlace em que cada gesto de amor implica perda.",
    "O destino de Teresa e a viagem de Simão tornam irreversível a separação dos amantes.",
    "Mariana permanece junto de Simão durante a travessia e cuida dele quando a sua saúde se agrava.",
    "O mar e a viagem transformam o degredo numa última etapa de sofrimento partilhado.",
    "O desfecho fecha a tragédia de Simão e revela a ligação final entre a morte, a memória e a devoção de Mariana.",
]

AMOR_NOTES = [
    ("Simão Botelho", "Estudante de Coimbra e filho de Domingos Botelho; a sua paixão por Teresa leva-o a desafiar a autoridade familiar e a enfrentar o degredo."),
    ("Thereza de Albuquerque", "Filha de Tadeu de Albuquerque e amada de Simão; a família tenta controlar o seu casamento e a sua correspondência."),
    ("Teresa", "Forma abreviada de Thereza, protagonista cuja fidelidade a Simão resiste à pressão do pai e à clausura."),
    ("Mariana", "Filha de João da Cruz; acompanha Simão com uma dedicação que mistura compaixão, amor e sacrifício."),
    ("João da Cruz", "Ferreiro e pai de Mariana; a sua ajuda a Simão contrasta com as disputas de honra entre as famílias aristocráticas."),
    ("Tadeu de Albuquerque", "Pai de Teresa, que procura impor à filha um casamento adequado à sua posição e impedir a relação com Simão."),
    ("Baltasar Coutinho", "Primo de Teresa e pretendente escolhido pela família; a sua presença agrava o conflito entre honra familiar e liberdade amorosa."),
    ("Domingos Botelho", "Pai de Simão e magistrado; a sua posição e o conflito com os Albuquerques moldam o destino do filho."),
    ("Coimbra", "Cidade universitária onde Simão estuda; os seus espaços de sociabilidade e as ruas são cenário do início do conflito."),
    ("Vila Real", "Região de origem das famílias Botelho e Albuquerque, cuja rivalidade sustenta o conflito familiar do romance."),
    ("degredo", "Pena de expulsão para uma colónia ultramarina; no romance, afasta Simão de Portugal e transforma o amor numa separação definitiva."),
    ("Índia", "Destino do degredo de Simão, associado à distância extrema entre ele e Teresa."),
    ("Relação do Porto", "Tribunal de apelação do Porto; o narrador diz ter consultado os seus registos prisionais para enquadrar a história como caso documentado."),
    ("cartas", "A correspondência permite aos amantes manter contacto, mas também mostra como a comunicação privada pode ser vigiada e interrompida."),
    ("honra", "Valor social invocado pelas famílias para justificar a autoridade paterna e a violência, em contraste com a escolha individual dos amantes."),
    ("convento", "Espaço de clausura para Teresa, que limita a sua liberdade e converte a vida religiosa num instrumento de controlo familiar."),
    ("liberdade", "A liberdade individual é restringida pelo poder das famílias, pelas convenções sociais e pela sentença de degredo."),
    ("amor", "A paixão é representada como força que desafia as convenções, mas que também conduz as personagens ao sofrimento e à perda."),
]

PRIMO_CONTEXTS = {
    "I": "A rotina conjugal de Luísa e Jorge é interrompida pela notícia do regresso de Basílio; a partida de Jorge abre espaço à visita do primo.",
    "II": "A conversa dos amigos apresenta o círculo lisboeta de Luísa e Jorge e contrapõe as ambições literárias à vida quotidiana.",
    "III": "O passado de Luísa e as leituras sentimentais ajudam a explicar a imagem romântica que ela projecta sobre Basílio.",
    "IV": "Basílio aproxima-se de Luísa e usa a intimidade antiga para transformar a visita familiar numa sedução calculada.",
    "V": "Os encontros entre Luísa e Basílio avançam enquanto a narrativa observa a cidade e o contraste entre fantasia e realidade.",
    "VI": "A relação clandestina passa a depender de segredos e de cartas, que Juliana descobre e transforma em instrumento de chantagem.",
    "VII": "Luísa tenta preservar as aparências domésticas enquanto Juliana exige vantagens e altera a hierarquia dentro da casa.",
    "VIII": "A pressão de Juliana e as tentativas de Luísa para recuperar as cartas aprofundam o suspense e o desgaste da protagonista.",
    "IX": "A vida social de Lisboa e a relação com Basílio expõem a distância entre as convenções respeitáveis e os desejos privados.",
    "X": "A chantagem torna-se mais difícil de esconder; Luísa procura uma saída sem revelar a Jorge a origem do conflito.",
    "XII": "As consequências da chantagem e as estratégias de Luísa deixam cada vez menos espaço para recuperar o controlo da casa.",
    "XIII": "A ausência de Basílio e o regresso de Jorge alteram o equilíbrio das personagens e aumentam o risco da revelação.",
    "XV": "As tentativas de resolver a situação conduzem Luísa a uma exaustão física e emocional que já não consegue disfarçar.",
    "XVI": "A verdade sobre as cartas e a doença de Luísa chegam ao seu desfecho, seguido pelo regresso tardio e cínico de Basílio.",
    "XVII": "O capítulo acompanha as consequências imediatas da crise e a forma como a sociedade interpreta o sofrimento de Luísa.",
    "XVIII": "O final encerra a história com o regresso de Basílio e expõe o egoísmo que estava escondido sob a sua linguagem romântica.",
}

PRIMO_NOTES = [
    ("Luiza", "Luísa é a protagonista; a sua formação através de romances sentimentais alimenta as fantasias com que interpreta a chegada de Basílio."),
    ("Luísa", "Forma modernizada do nome Luiza usado na edição de 1878; é a protagonista do romance."),
    ("Jorge", "Marido de Luísa e engenheiro; a sua ausência temporária deixa Luísa mais vulnerável à sedução de Basílio e à chantagem de Juliana."),
    ("Bazilio", "Basílio é o primo que regressa a Lisboa e reacende a paixão juvenil de Luísa; a sua pose romântica esconde oportunismo e egoísmo."),
    ("Basílio", "Primo de Luísa e antigo namorado; o seu regresso desencadeia a intriga e revela a diferença entre fantasia amorosa e desejo egoísta."),
    ("Juliana", "Criada de Luísa, ressentida com a dependência económica e a desigualdade social; usa as cartas como meio de chantagem."),
    ("Sebastião", "Amigo leal de Jorge e Luísa; ajuda a família durante a crise provocada pela chantagem."),
    ("Leopoldina", "Amiga de Luísa, cuja vida amorosa e reputação desafiam as convenções morais da burguesia lisboeta."),
    ("Julião", "Médico e conhecido do casal; o seu ressentimento social e as ambições frustradas fazem dele uma voz crítica do meio lisboeta."),
    ("Conselheiro Acácio", "Figura de autoridade pública, caracterizada por frases feitas e moralismo; tornou-se um tipo satírico da retórica vazia."),
    ("Dona Felicidade", "Conhecida do círculo de Luísa, marcada por expectativas românticas e pela dependência de convenções sociais."),
    ("Diário de Noticias", "Jornal lisboeta que aparece na vida quotidiana das personagens e ajuda a situar a obra na cultura urbana do século XIX."),
    ("Alentejo", "Região para onde Jorge viaja em serviço; a sua ausência desencadeia a acção principal do romance."),
    ("carta", "As cartas privadas de Luísa e Basílio tornam-se provas da relação e o principal instrumento de chantagem de Juliana."),
    ("romances", "As leituras sentimentais de Luísa moldam as suas expectativas e contrastam com a análise realista das relações sociais."),
    ("Teatro da Trindade", "Teatro lisboeta associado à vida cultural e mundana da cidade; os espectáculos integram a sociabilidade do romance."),
    ("realismo", "O romance usa a observação de hábitos, relações económicas e desigualdades domésticas para criticar a burguesia lisboeta."),
    ("Lisboa", "A cidade é mais do que cenário: os salões, ruas e casas expõem as hierarquias e os códigos de respeitabilidade da burguesia."),
]

CIDADE_CONTEXTS = [
    "A abertura apresenta a origem e a fortuna de Jacinto, cuja vida em Paris se organiza em torno da ideia de que a civilização traz felicidade.",
    "Zé Fernandes reencontra Jacinto no 202 dos Campos Elísios e descreve a casa, os aparelhos e o modo de vida do amigo.",
    "A rotina tecnológica do 202 revela o contraste entre a abundância de aparelhos e a insatisfação de Jacinto.",
    "Uma festa no 202 reúne a elite de Paris e expõe as convenções, a conversa e o espectáculo da vida mundana.",
    "As avarias dos aparelhos levam Jacinto a tentar dominar a matéria através de soluções ainda mais complicadas.",
    "As visitas, os encontros amorosos e a vida social parisiense mostram uma civilização sofisticada, mas cansada.",
    "Zé Fernandes prepara uma viagem pela Europa, enquanto Jacinto começa a imaginar outra relação com a vida.",
    "Jacinto decide acompanhar o amigo a Portugal e parte para a serra, deixando para trás o conforto acumulado no 202.",
    "Zé Fernandes regressa a Guiães e encontra sinais de que Jacinto está a preparar uma mudança para Tormes.",
    "A chegada de Jacinto a Tormes é marcada pela falta de comodidades e pelo contacto directo com a paisagem e os habitantes.",
    "A vida em Tormes aproxima Jacinto das pessoas da região e dá forma prática à sua mudança de hábitos.",
    "O aniversário de Zé Fernandes reúne a família e os vizinhos, permitindo a Jacinto participar na vida social da serra.",
    "A festa no aniversário de Zé Fernandes contrasta as poses da cidade com a espontaneidade e os costumes locais.",
    "O passeio a cavalo aproxima Jacinto de Joaninha e mostra como ele se integra na paisagem e nas relações de Tormes.",
    "Cinco anos depois, Jacinto construiu uma vida familiar e produtiva na serra, sem abandonar a curiosidade intelectual.",
    "O capítulo final recorda o desejo de Jacinto de regressar a Paris e deixa em aberto a relação entre cidade e campo.",
]

CIDADE_NOTES = [
    ("Jacintho", "Jacinto de Tormes é o protagonista; começa como defensor do progresso técnico em Paris e encontra em Tormes uma vida mais ligada à terra e às pessoas."),
    ("Zé Fernandes", "Narrador e amigo de Jacinto; o seu olhar irónico mede as diferenças entre a vida parisiense e a experiência rural portuguesa."),
    ("Tormes", "Propriedade da família de Jacinto no Douro, ligada à serra e à agricultura; torna-se o cenário da transformação do protagonista."),
    ("202", "Número da residência parisiense de Jacinto nos Campos Elísios, equipada com aparelhos que prometem tornar a vida mais confortável."),
    ("Civilisação", "A grafia de época para 'civilização'; o romance questiona se a acumulação de tecnologia e luxo produz realmente felicidade."),
    ("civilização", "O romance contrapõe o ideal de progresso urbano à experiência de Jacinto na serra, sem reduzir a crítica a uma simples rejeição da modernidade."),
    ("Paris", "Centro da vida cosmopolita de Jacinto e Zé Fernandes; a cidade representa o luxo, a velocidade e o cansaço da modernidade."),
    ("Guiães", "Localidade minhota ligada à família de Zé Fernandes, de onde o narrador parte para visitar Tormes."),
    ("Grillo", "Criado de Jacinto, cuja interpretação das avarias e da mudança do patrão ajuda a revelar a perspectiva prática da casa."),
    ("Madame d'Oriol", "Figura da sociedade parisiense que participa nas visitas e relações mundanas de Jacinto."),
    ("Joanninha", "Prima de Zé Fernandes, também chamada Joaninha; a sua presença aproxima Jacinto da vida familiar e social da serra."),
    ("Flôr da Malva", "Quinta da família de Joaninha, perto de Tormes, associada à vida local e ao futuro doméstico de Jacinto."),
    ("serra", "A serra representa a experiência directa da natureza, do trabalho e das relações locais, em contraste com a vida mecanizada do 202."),
    ("Tormes", "A mudança para Tormes permite a Jacinto trocar o consumo de novidades por uma relação mais concreta com o lugar e os seus habitantes."),
]

FREI_CONTEXTS = [
    "No palácio de Almada, Madalena e Telmo falam do passado e do receio de que D. João de Portugal ainda esteja vivo; a chegada de Manuel altera a casa e conduz a família à decisão de regressar ao palácio de D. João.",
    "No antigo palácio de D. João, as recordações e os sinais do passado intensificam o medo de Madalena; a notícia de um peregrino desconhecido aproxima a família da verdade que todos receiam.",
    "O regresso ao palácio e a identificação do Romeiro destroem a vida familiar; Maria adoece, enquanto Manuel e Madalena escolhem a vida religiosa.",
]

FREI_NOTES = [
    ("Manuel de Sousa Coutinho", "Nobre português e marido de Madalena; depois da revelação do regresso de D. João, toma o hábito e passa a chamar-se Frei Luís de Sousa."),
    ("Frei Luiz", "Nome religioso assumido por Manuel de Sousa Coutinho no final da peça."),
    ("Magdalena", "Madalena de Vilhena, esposa de Manuel e antiga mulher de D. João de Portugal; vive assombrada pela possibilidade de o primeiro marido estar vivo."),
    ("D. João de Portugal", "Primeiro marido de Madalena, dado como desaparecido na batalha de Alcácer-Quibir; o seu regresso desencadeia a catástrofe da peça."),
    ("Romeiro", "Peregrino que regressa à família e se identifica como D. João de Portugal, transformando a suspeita em certeza."),
    ("Maria", "Filha de Madalena e Manuel, jovem de saúde frágil e imaginação intensa; a revelação final precipita a sua morte."),
    ("Telmo", "Antigo aio de D. João e criado fiel da família; a lealdade ao antigo senhor entra em conflito com o afecto por Maria."),
    ("Frei Jorge", "Irmão de Manuel e frade dominicano; acompanha a família nos momentos de crise e na decisão de professar."),
    ("Alcácer-Quibir", "Batalha de 1578 em Marrocos, onde desapareceu o rei D. Sebastião e muitos nobres portugueses, entre eles D. João segundo a narrativa."),
    ("sebastianismo", "Expectativa do regresso de D. Sebastião, que alimenta a esperança de que os desaparecidos em Alcácer-Quibir possam voltar."),
    ("profissão", "Cerimónia em que Manuel e Madalena assumem a vida religiosa, consequência da impossibilidade moral de manter o casamento."),
    ("palácio", "Os dois palácios funcionam como espaços da memória: o primeiro pertence à vida com Manuel; o segundo conserva os vestígios de D. João."),
    ("D. Sebastião", "Rei desaparecido em Alcácer-Quibir; a crença no seu regresso ajuda a manter viva a possibilidade de D. João também estar vivo."),
]

FRADIQUE_MEMOIRS_CONTEXTS = [
    "O narrador recorda o primeiro encontro com Fradique em Paris e a impressão de pose, luxo e originalidade que o poeta lhe causou.",
    "A memória de Fradique reúne episódios da sua vida cosmopolita e a reacção dos amigos à sua personalidade teatral e independente.",
    "O narrador acompanha a distância entre os encontros e constrói o retrato de Fradique através das viagens, das amizades e das ideias que deixou.",
    "Uma nova secção retoma as viagens e a vida intelectual de Fradique, aprofundando a relação entre a sua imagem pública e a sua curiosidade privada.",
    "O narrador descreve a inteligência de Fradique e a maneira como ele observa a sociedade, as artes e as ideias sem se prender a um sistema.",
    "O último encontro com Fradique dá lugar a conversas sobre as viagens, a religião e a possibilidade de transformar as experiências em livro.",
    "O narrador explica como reuniu as cartas e por que considera a correspondência uma forma privilegiada de conhecer Fradique.",
    "A secção final das memórias prepara a passagem do retrato do homem para as cartas que mostram directamente a sua voz.",
]

FRADIQUE_LETTER_CONTEXTS = [
    "Fradique responde a uma pergunta prática sobre alfaiates e aproveita-a para distinguir a roupa escolhida segundo a pessoa e o propósito.",
    "Uma carta a Madame de Jouarre mistura observação social, intimidade e comentário sobre a vida parisiense.",
    "Fradique escreve a Oliveira Martins sobre antiguidades, viagens e a maneira de observar culturas sem as reduzir a fórmulas.",
    "A resposta a Madame S. começa com um conselho sobre a aprendizagem do espanhol e desenvolve uma reflexão sobre educação e experiência.",
    "Fradique discute com Guerra Junqueiro a religião, a Igreja e a força estética dos rituais.",
    "Uma carta a Ramalho Ortigão transforma um encontro inesperado e uma viagem numa sequência de observações irónicas.",
    "A carta de Lisboa a Madame de Jouarre relata o regresso de Fradique e a impressão que a cidade lhe causa.",
    "Fradique responde a um director de revista que lhe pede informação biográfica e reflecte sobre a construção de uma vida pública.",
    "Uma carta a Clara recorda o primeiro encontro e converte a memória amorosa numa narrativa cuidadosamente construída.",
    "Fradique descreve a vida em Lisboa à sua madrinha, com retratos da cidade, das relações sociais e dos seus conhecidos.",
    "A carta a Bertrand B. cruza a Páscoa, a paisagem e uma reflexão sobre a história religiosa e política.",
    "Da quinta de Refaldes, Fradique escreve sobre o Minho, a vida rural e as pessoas que encontra.",
    "A carta a Clara revisita a intimidade amorosa e as imagens de viagem que a memória conserva.",
    "Fradique relata a Madame de Jouarre uma conversa com um padre e expõe a sua curiosidade pela religião e pelas pessoas.",
    "A carta a Bento de S. critica o projecto de fundar um jornal e comenta a imprensa e a vida pública.",
    "A última carta a Clara retoma a distância amorosa e a maneira como Fradique transforma os sentimentos em linguagem.",
]

FRADIQUE_NOTES = [
    ("Fradique Mendes", "Carlos Fradique Mendes é um poeta fictício, cosmopolita e erudito; Eça constrói o seu retrato através das memórias do narrador e das cartas atribuídas a Fradique."),
    ("Oliveira Martins", "Historiador e político português, amigo de Eça de Queirós e correspondente de Fradique na ficção."),
    ("Ramalho Ortigão", "Escritor português e antigo colaborador de Eça; aparece entre os destinatários das cartas de Fradique."),
    ("Guerra Junqueiro", "Poeta português a quem Fradique escreve sobre religião e vida cultural."),
    ("Madame de Jouarre", "Madrinha e confidente de Fradique, destinatária de várias cartas que revelam a sua vida quotidiana e afectiva."),
    ("Clara", "Destinatária de cartas amorosas que mostram uma dimensão íntima e vulnerável de Fradique."),
    ("Paris", "Centro da vida cosmopolita de Fradique e cenário de vários encontros, debates e cartas."),
    ("Lisboa", "Cidade revisitada por Fradique; as cartas observam a sua sociedade, as suas instituições e os seus hábitos."),
    ("Londres", "Cidade onde Fradique vive e escreve sobre a vida social, os costumes e a experiência de viagem."),
    ("Correspondencia", "A grafia de época de 'correspondência'; o livro apresenta as cartas como acesso à personalidade e às ideias de Fradique."),
    ("Torre de Marfim", "Imagem de isolamento intelectual e afectivo, usada por Fradique para descrever uma forma de vida retirada."),
    ("Mazzini", "Giuseppe Mazzini, revolucionário e nacionalista italiano, referido na rede de amizades e interesses políticos de Fradique."),
    ("Garibaldi", "Giuseppe Garibaldi, figura das lutas pela unificação italiana, lembrado entre as relações políticas de Fradique."),
    ("Oliveira Martins", "A correspondência com o historiador mostra o interesse de Fradique pela história, pelas viagens e pela interpretação cultural."),
    ("Junqueiro", "Abreviação de Guerra Junqueiro, poeta a quem Fradique dirige uma carta sobre religião e liturgia."),
    ("Ramalho", "Abreviação de Ramalho Ortigão, escritor e amigo do círculo literário de Eça de Queirós."),
]


def body_lines(book_id):
    raw = fetch(f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt").decode("utf-8-sig")
    lines = raw.splitlines()
    start = next(i for i, line in enumerate(lines) if "*** START OF THE PROJECT GUTENBERG EBOOK" in line)
    end = next(i for i, line in enumerate(lines) if "*** END OF THE PROJECT GUTENBERG EBOOK" in line)
    return lines[start + 1:end]


def roman_number(value):
    values = {"I": 1, "V": 5, "X": 10, "L": 50}
    result = 0
    for index, char in enumerate(value):
        amount = values[char]
        result += -amount if index + 1 < len(value) and amount < values[value[index + 1]] else amount
    return result


def roman_chapter_markers(lines):
    marker = re.compile(rf"^\s*({ROMAN})[.]?\s*$", re.I)
    found = []
    for index, line in enumerate(lines):
        match = marker.fullmatch(line)
        if match and (index == 0 or not lines[index - 1].strip()) and (index + 1 == len(lines) or not lines[index + 1].strip()):
            found.append((index, match.group(1).upper()))
    return found


def matching_notes(content, candidates, limit=5):
    found = []
    occupied = []
    for target, note in sorted(candidates, key=lambda item: len(item[0]), reverse=True):
        if target.casefold() not in content.casefold():
            continue
        if any(target.casefold() in previous or previous in target.casefold() for previous in occupied):
            continue
        found.append({"target": target, "text": note})
        occupied.append(target.casefold())
        if len(found) >= limit:
            break
    return found


def chapter_record(slug, title, section, context, content, notes):
    content = content.strip()
    if len(content) < 250:
        raise RuntimeError(f"{title} parece incompleto ({len(content)} caracteres).")
    return {
        "slug": slug,
        "title": title,
        "section": section,
        "context": context,
        "content": content,
        "audioUrl": "",
        "audioDuration": "",
        "annotations": matching_notes(content, notes),
    }


def save_book(slug, book, chapters):
    book_dir = BOOKS_DIR / slug
    book_dir.mkdir(parents=True, exist_ok=True)
    chapter_slugs = []
    for chapter in chapters:
        write_json(book_dir / "chapters" / f"{chapter['slug']}.json", chapter)
        chapter_slugs.append(chapter["slug"])
    book["chapterOrder"] = chapter_slugs
    write_json(book_dir / "book.json", book)
    for path in (book_dir / "chapters").glob("*.json"):
        if path.stem not in chapter_slugs:
            path.unlink()
    print(f"{book['title']}: {len(chapters)} divisões, {sum(len(c['content']) for c in chapters):,} caracteres, {sum(len(c['annotations']) for c in chapters)} notas")


def import_viagens():
    lines = body_lines("24401")
    marker = re.compile(rf"^\s*CAPITULO\s+({ROMAN})[.]\s*$", re.I)
    headings = [(i, match.group(1).upper()) for i, line in enumerate(lines) if (match := marker.fullmatch(line))]
    if len(headings) != 49:
        raise RuntimeError(f"Esperava 49 capítulos de Viagens na Minha Terra; encontrei {len(headings)}.")
    # The source inserts proofreading errata between the two volumes and
    # again after the final chapter. Keep the narrative, not those tables.
    clean_lines = []
    skipping_errata = False
    for line in lines:
        if line.strip() == "Lista de erros corrigidos":
            skipping_errata = True
            continue
        if skipping_errata and marker.fullmatch(line):
            skipping_errata = False
        if not skipping_errata:
            clean_lines.append(line)
    lines = clean_lines
    headings = [(i, match.group(1).upper()) for i, line in enumerate(lines) if (match := marker.fullmatch(line))]
    if len(headings) != 49:
        raise RuntimeError(f"A remoção das erratas alterou a sequência dos capítulos de Viagens ({len(headings)}).")
    book = {
        "id": 4, "slug": "viagens-na-minha-terra", "title": "Viagens na Minha Terra", "author": "Almeida Garrett",
        "authorId": "almeida-garrett", "authorBio": "Escritor, dramaturgo e político português (1799–1854), figura central do Romantismo e do liberalismo português.",
        "description": "Viagem pelo Tejo e pelo Ribatejo que entrelaça observação, memória, crítica política e a história de Joaninha.",
        "year": "1846", "language": "pt", "coverImage": "./data/books/viagens-na-minha-terra/cover.svg",
        "tags": ["romantismo", "viagem", "Santarém", "guerra civil"],
        "source": {"title": "Viagens na Minha Terra (1846)", "url": "https://www.gutenberg.org/ebooks/24401",
                   "transcription": "Project Gutenberg; transcrição produzida a partir de imagens disponibilizadas pela Biblioteca Nacional de Portugal.",
                   "editorialNote": "Texto integral da edição de 1846, com grafia original. As notas de leitura são editoriais. O Project Gutenberg identifica o seu estatuto nos Estados Unidos; a obra original é de autor falecido em 1854 e está no domínio público em Portugal."},
    }
    chapters = []
    for index, (start, number) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        raw_content = lines[start + 1:end]
        content = normalize_prose(raw_content)
        context = VIAGENS_CONTEXTS.get(number, "A viagem e as digressões do narrador articulam observação da paisagem, memória e comentário sobre a sociedade portuguesa.")
        chapters.append(chapter_record(f"capitulo-{roman_number(number):02d}", f"Capítulo {number}", "Viagem e romance", context, content, VIAGENS_NOTES))
    save_book(book["slug"], book, chapters)


def import_amor():
    lines = body_lines("16425")
    binding = next((i for i, line in enumerate(lines) if line.strip().startswith("Encadernação N.")), len(lines))
    lines = lines[:binding]
    first_part = next(i for i, line in enumerate(lines) if line.strip().upper() == "PRIMEIRA PARTE.")
    second_part = next(i for i, line in enumerate(lines) if line.strip().upper() == "SEGUNDA PARTE.")
    prologue_start = next(i for i, line in enumerate(lines) if line.strip().startswith("Folheando os livros de antigos assentamentos"))
    prologue = normalize_prose(lines[prologue_start:first_part])
    chapters = [chapter_record("prologo", "Prólogo", "Enquadramento", "O narrador apresenta o caso a partir de um registo prisional e reflecte sobre as ideias de amor, honra e justiça que guiarão a história.", prologue, AMOR_NOTES)]
    expected_parts = [(first_part, second_part, "Primeira parte", 1), (second_part, len(lines), "Segunda parte", 2)]
    for start, end, section, part_number in expected_parts:
        segment = lines[start:end]
        markers = roman_chapter_markers(segment)
        if len(markers) != 10:
            raise RuntimeError(f"Esperava 10 capítulos em {section} de Amor de Perdição; encontrei {len(markers)}.")
        for index, (offset, number) in enumerate(markers):
            chapter_end = markers[index + 1][0] if index + 1 < len(markers) else len(segment)
            chapter_text = normalize_prose(segment[offset + 1:chapter_end])
            serial = roman_number(number)
            slug = f"parte-{part_number}-capitulo-{serial:02d}"
            chapters.append(chapter_record(slug, f"Capítulo {number}", section, AMOR_CONTEXTS[(part_number - 1) * 10 + serial - 1], chapter_text, AMOR_NOTES))
    book = {
        "id": 5, "slug": "amor-de-perdicao", "title": "Amor de Perdição", "author": "Camilo Castelo Branco",
        "authorId": "camilo-castelo-branco", "authorBio": "Romancista português (1825–1890), um dos nomes centrais da ficção romântica portuguesa.",
        "description": "A paixão de Simão e Teresa enfrenta a rivalidade das famílias, a clausura e o degredo; Mariana acompanha o destino dos amantes.",
        "year": "1862", "language": "pt", "coverImage": "./data/books/amor-de-perdicao/cover.svg",
        "tags": ["romantismo", "amor", "tragédia", "Coimbra"],
        "source": {"title": "Amor de Perdição: Memórias d'uma família (1862)", "url": "https://www.gutenberg.org/ebooks/16425",
                   "transcription": "Project Gutenberg; créditos de transcrição incluem a Biblioteca Nacional Digital.",
                   "editorialNote": "Texto integral em grafia original, com prólogo e as duas partes. O Project Gutenberg identifica o estatuto nos Estados Unidos; a obra original é de autor falecido em 1890 e está no domínio público em Portugal."},
    }
    save_book(book["slug"], book, chapters)


def import_primo():
    lines = body_lines("42942")
    errata = next((i for i, line in enumerate(lines) if line.strip() == "Lista de erros corrigidos"), len(lines))
    lines = lines[:errata]
    markers = roman_chapter_markers(lines)
    # The Gutenberg transcription contains the complete 1878 text and sixteen
    # explicit chapter headings, preserving the numbering printed in that file.
    if len(markers) != 16 or markers[0][1] != "I":
        raise RuntimeError(f"Esperava 16 divisões numeradas em O Primo Basílio; encontrei {len(markers)}.")
    summaries = PRIMO_CONTEXTS
    chapters = []
    for index, (start, number) in enumerate(markers):
        end = markers[index + 1][0] if index + 1 < len(markers) else len(lines)
        content = normalize_prose(lines[start + 1:end])
        chapters.append(chapter_record(f"capitulo-{roman_number(number):02d}", f"Capítulo {number}", "Romance", summaries[number], content, PRIMO_NOTES))
    book = {
        "id": 6, "slug": "o-primo-bazilio", "title": "O Primo Basílio", "author": "Eça de Queirós",
        "authorId": "eca-de-queiros", "authorBio": "Romancista português (1845–1900), figura central do Realismo e da crítica social oitocentista.",
        "description": "Um romance de adultério, chantagem e convenções sociais na Lisboa burguesa do século XIX.",
        "year": "1878", "language": "pt", "coverImage": "./data/books/o-primo-bazilio/cover.svg",
        "tags": ["realismo", "Lisboa", "romance", "sociedade"],
        "source": {"title": "O Primo Bazilio: Episodio Domestico (segunda edição revista, 1878)", "url": "https://www.gutenberg.org/ebooks/42942",
                   "transcription": "Project Gutenberg; transcrição produzida a partir de imagens disponibilizadas pela Biblioteca Nacional de Portugal.",
                   "editorialNote": "Texto integral da segunda edição de 1878, mantendo a grafia de época e a numeração dos capítulos tal como aparece na transcrição. Esta transcrição digital apresenta dezasseis títulos de capítulo explícitos. O Project Gutenberg identifica o estatuto nos Estados Unidos; a obra original é de autor falecido em 1900 e está no domínio público em Portugal."},
    }
    save_book(book["slug"], book, chapters)


def import_cidade():
    lines = body_lines("18220")
    ending = next(i for i, line in enumerate(lines) if line.strip().casefold() == "fim")
    lines = lines[:ending]
    markers = roman_chapter_markers(lines)
    if len(markers) != 16:
        raise RuntimeError(f"Esperava 16 capítulos em A Cidade e as Serras; encontrei {len(markers)}.")
    chapters = []
    for index, (start, number) in enumerate(markers):
        end = markers[index + 1][0] if index + 1 < len(markers) else len(lines)
        content = normalize_prose(lines[start + 1:end])
        section = "Paris" if index < 8 else "Tormes"
        chapters.append(chapter_record(
            f"capitulo-{roman_number(number):02d}", f"Capítulo {number}", section,
            CIDADE_CONTEXTS[index], content, CIDADE_NOTES))
    book = {
        "id": 7, "slug": "a-cidade-e-as-serras", "title": "A Cidade e as Serras", "author": "Eça de Queirós",
        "authorId": "eca-de-queiros", "authorBio": "Romancista português (1845–1900), figura central do Realismo e da crítica social oitocentista.",
        "description": "Jacinto troca o conforto tecnológico de Paris pela vida em Tormes, numa reflexão irónica sobre progresso, felicidade e pertença.",
        "year": "1901", "language": "pt", "coverImage": "./data/books/a-cidade-e-as-serras/cover.svg",
        "tags": ["realismo", "Paris", "Douro", "modernidade"],
        "source": {"title": "A Cidade e as Serras (1901)", "url": "https://www.gutenberg.org/ebooks/18220",
                   "transcription": "Project Gutenberg; transcrição produzida a partir de imagens disponibilizadas pela Biblioteca Nacional Digital.",
                   "editorialNote": "Edição póstuma, publicada em 1901; o texto integral do romance termina em 'Fim' e exclui anúncios editoriais posteriores. A advertência da edição refere que as provas a partir da página 241 não foram revistas pelo autor. O Project Gutenberg declara o estatuto nos Estados Unidos; Eça de Queirós morreu em 1900 e a obra está no domínio público em Portugal."},
    }
    save_book(book["slug"], book, chapters)


def import_frei():
    lines = body_lines("17591")
    curtain = max(i for i, line in enumerate(lines) if "panno" in line.casefold())
    lines = lines[:curtain + 1]
    headers = [(i, line.strip()) for i, line in enumerate(lines)
               if line.strip().upper() in {"ACTO PRIMEIRO", "ACTO SEGUNDO", "ACTO TERCEIRO"}]
    if len(headers) != 3:
        raise RuntimeError(f"Esperava três actos em Frei Luís de Sousa; encontrei {len(headers)}.")
    contexts = FREI_CONTEXTS
    chapters = []
    for index, (start, title) in enumerate(headers):
        end = headers[index + 1][0] if index + 1 < len(headers) else len(lines)
        content = normalize_prose(lines[start:end])
        chapters.append(chapter_record(f"acto-{index + 1}", title.title(), f"Acto {index + 1}",
                                       contexts[index], content, FREI_NOTES))
    book = {
        "id": 8, "slug": "frei-luis-de-sousa", "title": "Frei Luís de Sousa", "author": "Almeida Garrett",
        "authorId": "almeida-garrett", "authorBio": "Escritor e dramaturgo português (1799–1854), figura decisiva do Romantismo e do teatro nacional.",
        "description": "Uma família vive entre o amor, a honra e a esperança de que um desaparecido na batalha de Alcácer-Quibir possa regressar.",
        "year": "1843", "language": "pt", "coverImage": "./data/books/frei-luis-de-sousa/cover.svg",
        "tags": ["teatro", "Romantismo", "sebastianismo", "tragédia"],
        "source": {"title": "Frei Luiz de Sousa (1843)", "url": "https://www.gutenberg.org/ebooks/17591",
                   "transcription": "Project Gutenberg; transcrição digital da peça em três actos.",
                   "editorialNote": "Texto integral em grafia de época; a edição fonte usa 'Luiz' e 'Magdalena'. O título da biblioteca adopta a grafia actual 'Luís'. O Project Gutenberg declara o estatuto nos Estados Unidos; Almeida Garrett morreu em 1854 e a obra está no domínio público em Portugal."},
    }
    save_book(book["slug"], book, chapters)


def import_fradique():
    lines = body_lines("27637")
    letters_header = next(i for i, line in enumerate(lines) if line.strip().upper() == "AS CARTAS")
    notes_start = next(i for i, line in enumerate(lines[letters_header:], start=letters_header)
                       if line.strip().casefold() == "notas:")
    lines = lines[:notes_start]
    memoir_lines = lines[:letters_header]
    memoir_markers = roman_chapter_markers(memoir_lines)
    expected_memoirs = ["I", "II", "III", "III", "IV", "V", "VI", "VII"]
    if [number for _, number in memoir_markers] != expected_memoirs:
        raise RuntimeError("A estrutura das memórias de A Correspondência de Fradique Mendes mudou.")
    letter_lines = lines[letters_header + 1:]
    letter_markers = roman_chapter_markers(letter_lines)
    if len(letter_markers) != 16:
        raise RuntimeError(f"Esperava 16 cartas de Fradique; encontrei {len(letter_markers)}.")
    chapters = []
    for index, (start, _source_number) in enumerate(memoir_markers):
        end = memoir_markers[index + 1][0] if index + 1 < len(memoir_markers) else len(memoir_lines)
        content = normalize_prose(memoir_lines[start + 1:end])
        source_note = " A transcrição fonte repete o algarismo III nesta secção; a navegação distingue-a como capítulo IV." if index == 3 else ""
        chapter = chapter_record(f"memorias-capitulo-{index + 1:02d}", f"Capítulo {index + 1} — Memórias", "Memórias",
                                 FRADIQUE_MEMOIRS_CONTEXTS[index] + source_note, content, FRADIQUE_NOTES)
        chapters.append(chapter)
    for index, (start, number) in enumerate(letter_markers):
        end = letter_markers[index + 1][0] if index + 1 < len(letter_markers) else len(letter_lines)
        content = normalize_prose(letter_lines[start + 1:end])
        chapters.append(chapter_record(f"carta-{roman_number(number):02d}", f"Carta {number}", "Correspondência",
                                       FRADIQUE_LETTER_CONTEXTS[index], content, FRADIQUE_NOTES))
    book = {
        "id": 9, "slug": "a-correspondencia-de-fradique-mendes", "title": "A Correspondência de Fradique Mendes", "author": "Eça de Queirós",
        "authorId": "eca-de-queiros", "authorBio": "Romancista português (1845–1900), figura central do Realismo e da crítica social oitocentista.",
        "description": "Memórias e cartas compõem o retrato de Fradique Mendes, poeta fictício cosmopolita criado por Eça de Queirós.",
        "year": "1900", "language": "pt", "coverImage": "./data/books/a-correspondencia-de-fradique-mendes/cover.svg",
        "tags": ["epistolar", "memórias", "Lisboa", "Paris"],
        "source": {"title": "A Correspondência de Fradique Mendes (1900)", "url": "https://www.gutenberg.org/ebooks/27637",
                   "transcription": "Project Gutenberg; transcrição baseada em imagens da Biblioteca Nacional Digital.",
                   "editorialNote": "Texto integral com oito secções de memórias e dezasseis cartas. A transcrição fonte repete o número III numa das secções; a biblioteca preserva o texto e distingue as secções na navegação. O Project Gutenberg declara o estatuto nos Estados Unidos; Eça de Queirós morreu em 1900 e a obra está no domínio público em Portugal."},
    }
    save_book(book["slug"], book, chapters)


def main():
    try:
        import_viagens()
        import_amor()
        import_primo()
        import_cidade()
        import_frei()
        import_fradique()
        print("Importação concluída. Execute scripts/build_books.py e scripts/build_pdfs.py para compilar as novas edições.")
    except Exception as exc:
        print(f"Erro de importação: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
