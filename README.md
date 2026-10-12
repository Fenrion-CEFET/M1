FENRION · Missão 1 "Bouncing 2.0"

Guia para instalar, testar e aprimorar o código da Missão 1 num notebook com Windows, partindo do zero (sem Python instalado).

Siga os passos na ordem. Cada passo termina com um "Deu certo se...": só avance quando ele acontecer. Se travar, veja a seção Problemas comuns.

O que a missão faz :

O drone decola da base central, procura o gabarito (um marcador ArUco dentro de uma forma geométrica), lê o ID do ArUco e procura a base de pouso que tem a mesma forma do gabarito e um número (3, 4 ou 5) que divide exatamente o ID. Depois pousa com precisão sobre ela e desliga os rotores.

Exemplo: gabarito hexágono com ID 25. Divisores possíveis: só o 5. Base correta: hexágono 5.

Como o sistema está montado:

 Camera ESP32-S3 (aponta para baixo) --Wi-Fi--> NOTEBOOK (este codigo) --Wi-Fi--> ESP8266 --serial--> Pixhawk
        stream de video, porta 81            visao + decisao + controle       MAVLink, porta UDP 14550

O notebook vê a imagem, decide para onde ir e manda comandos de voo para a Pixhawk.

O que vem nesta pasta
Arquivo	Para que serve
0_instalar.bat	Instala tudo (rodar uma vez),
1_testar_visao_exemplos.bat	Testa a visão em imagens prontas
2_simulador_missao.bat	Roda a missão inteira num simulador, sem drone
3_teste_em_lote.bat	Roda várias missões simuladas e dá a taxa de acerto
4_camera_bancada.bat	Visão com a câmera real ou a webcam
5_missao_sitl.bat	Missão no simulador do Mission Planner (SITL)
6_missao_drone_real.bat	Missão no drone real (só com o professor ou capitão)
m1_visao.py	Código da visão (ArUco, formas, números, decisão)
m1_missao.py	Código da missão (máquina de estados, controle, simulador)
teste_lote.py	Script usado pelo teste em lote
requirements.txt	Lista de bibliotecas Python
alvos_teste_A4.pdf	Alvos para imprimir (gabaritos e bases)
exemplos/	Imagens para testar a visão
firmware/	Códigos Arduino da câmera e da ponte de telemetria (referência)
logs/	Onde ficam os registros de cada missão (.csv)

_____________________//////___________________________________________________________________________

Passo 1 · Instalar o Python
Acesse python.org, menu Downloads, e baixe o Python 3.12 para Windows (instalador de 64 bits, "Windows installer (64-bit)").
Abra o instalador. Na primeira tela, marque a caixa "Add python.exe to PATH" (fica embaixo, é fácil passar despercebida).
Clique em Install Now e espere terminar.
Para conferir: 
tecla Windows, digite cmd, Enter. No Prompt de Comando, digite:
   py --version

Deu certo se aparecer Python 3.12.x.

Se aparecer uma mensagem sugerindo a Microsoft Store, desligue os atalhos em Configurações > Aplicativos > Configurações avançadas de aplicativos > Aliases de execução de aplicativo (desative python.exe e python3.exe) e feche e abra o Prompt de Comando.

_____________________//////___________________________________________________________________________

Passo 2 · Copiar a pasta do projeto

Copie a pasta inteira FENRION_M1 para C:\FENRION_M1.

Evite a Área de Trabalho, Documentos ou qualquer pasta dentro do OneDrive: a sincronização costuma travar o ambiente virtual. Evite também nomes de pasta com acento.


_____________________//////___________________________________________________________________________

Passo 3 · Instalar as bibliotecas

Dê dois cliques em 0_instalar.bat. Ele cria um ambiente isolado na pasta .venv e instala o OpenCV, o pymavlink e as demais bibliotecas. Precisa de internet e leva de 2 a 5 minutos.

Deu certo se terminar com OpenCV x.x.x - tudo OK e INSTALACAO CONCLUIDA.

Se o Windows mostrar "O Windows protegeu o computador", clique em Mais informações > Executar assim mesmo. Os .bat são arquivos de texto simples; você pode abri-los no Bloco de Notas para conferir o que fazem.
_____________________//////___________________________________________________________________________


Passo 4 · Testar a visão com imagens prontas

Dê dois cliques em 1_testar_visao_exemplos.bat. Abre uma janela por imagem; aperte qualquer tecla para passar para a próxima.

Na imagem aparecem:

magenta: o ArUco (com o ID) e a forma do gabarito;
amarelo: as bases reconhecidas, com forma e número;
verde: a base correta, com uma linha saindo do centro da imagem.

Deu certo se a figura do regulamento mostrar ID 25 | gabarito hexagono | ... | POUSAR: hexagono 5 no topo.


_____________________//////___________________________________________________________________________

Passo 5 · Rodar a missão no simulador próprio

Dê dois cliques em 2_simulador_missao.bat e aperte Enter (arena sorteada) ou digite um número de arena.

O simulador desenha uma arena virtual, "fotografa" o chão conforme a posição do drone e passa essa imagem pelo mesmo código de visão usado no drone real. Na janela você vê o que a câmera do drone veria; na faixa de baixo, o estado da missão:

DECOLAR -> BUSCA -> IR_ALVO -> ALINHAR -> POUSO -> FIM

Teclas: espaço pausa, q aborta (pousa onde está).

Deu certo se no fim aparecer algo como:

Base escolhida: hexagono 3 (erro de pouso estimado 2 cm)
Resposta esperada: ('hexagono', 3); distancia ate o centro dela: 2 cm

Cada missão gera um arquivo em logs/ (abre no Excel; separador ;) com tempo, estado, posição, altura e mensagens.

_____________________//////___________________________________________________________________________

Passo 6 · Teste em lote (use sempre que mudar o código)

Dê dois cliques em 3_teste_em_lote.bat e aperte Enter duas vezes (arenas 1 a 10). Cada arena leva cerca de 15 segundos.

Deu certo se terminar com RESULTADO: 10/10 pousos corretos (100%).

Este é o seu termômetro. A regra da equipe é: rode o lote antes de mexer no código (anote o resultado), faça a mudança e rode o lote de novo. A mudança só entra se o resultado ficar igual ou melhor. Para um teste mais exigente, use as arenas 1 a 30.

_____________________//////___________________________________________________________________________

Passo 7 · Visão com a câmera real (bancada)
Imprima o alvos_teste_A4.pdf e espalhe as folhas no chão. Deixe um gabarito visível por vez, como na arena.
Ligue a câmera ESP32-S3 e conecte o notebook na mesma rede Wi-Fi dela. Peça o IP da câmera à equipe (aparece no Serial Monitor da placa ao ligar).
Confira no navegador: http://IP_DA_CAMERA/ deve mostrar a imagem. Feche essa aba depois, porque a câmera atende um stream por vez.
Dê dois cliques em 4_camera_bancada.bat, digite o IP e aperte Enter (nas próximas vezes, só Enter repete o último IP). Digite w para usar a webcam do notebook.

Teclas na janela: q sai, s salva o quadro em arquivo, d mostra a imagem binarizada (preto e branco), útil para ver o efeito da iluminação.

Para o vídeo ficar fluido, deixe a câmera em VGA ou SVGA, abrindo no navegador: http://IP_DA_CAMERA/control?var=framesize&val=11

Deu certo se, segurando a câmera a 1 a 3 m de altura, a base correta aparecer em verde.


_____________________//////___________________________________________________________________________

Passo 8 · Missão no SITL do Mission Planner (opcional)

O SITL roda o firmware real do ArduPilot no computador. É o teste mais próximo do voo de verdade, porque usa o mesmo protocolo e os mesmos modos de voo do drone.

Instale o Mission Planner (ardupilot.org, seção Mission Planner).
Abra o Mission Planner, vá na aba SIMULATION, clique em Multirotor e aceite a versão estável. Espere o drone aparecer no mapa e o GPS ficar verde (cerca de 1 minuto).
Dê dois cliques em 5_missao_sitl.bat e aperte Enter (porta 5762).

A câmera continua virtual (arena desenhada), mas o voo é do ArduPilot. O Mission Planner continua mostrando o drone no mapa durante a missão.

Deu certo se o drone decolar no Mission Planner, percorrer a arena e pousar. Se não conectar, tente a porta 5763.

_____________________//////___________________________________________________________________________

Passo 9 · Drone real

Só com o professor ou o capitão técnico presentes. Leia a seção Segurança antes.

Pré-requisitos (já feitos pela equipe de hardware):

Pixhawk com SERIAL2_PROTOCOL = 2 e SERIAL2_BAUD = 115 (telemetria pela ESP8266).
MTF-01 instalado e configurado (fluxo óptico e distância), com o drone segurando posição em Loiter.
Câmera ESP32-S3 presa apontando para baixo, com o topo da imagem voltado para a frente do drone.
ESP8266 e câmera na mesma rede do notebook.

Execução:

Feche o Mission Planner (ele ocupa a porta 14550 e o código não consegue conectar).
Dê dois cliques em 6_missao_drone_real.bat, informe o IP da câmera e responda se o voo é sem GPS (s = usa o MTF-01).
O programa pede para digitar VOAR. Só digite com a área livre e o piloto pronto.

Durante o voo, q na janela da imagem manda pousar. O piloto de segurança pode a qualquer momento trocar o modo no rádio (Loiter ou Land), e isso tem prioridade sobre o código.

Como o código está organizado
m1_visao.py (visão)
Função	O que faz
ArucoFinder	Acha o ArUco e lê o ID (testa vários dicionários)
find_shapes	Acha triângulos, hexágonos e estrelas pelos contornos
read_digit	Lê o número 3, 4 ou 5 dentro de cada forma (testando rotações)
decide	Aplica a regra: mesma forma do gabarito e número que divide o ID
process	Junta tudo para um quadro e devolve a imagem anotada e o estado

Ajustes no topo do arquivo: ARUCO_DICTS (coloque primeiro o dicionário definido no regulamento), MIN_AREA_FRAC, ADAPT_BLOCK e ADAPT_C (sensibilidade à iluminação).

m1_missao.py (missão)
Parte	O que faz
Missao	Máquina de estados: DECOLAR, BUSCA, IR_ALVO, ALINHAR, POUSO, FIM
Mapa	Guarda a posição das bases vistas e vota para evitar leituras erradas
SimDrone	Drone simulado (simples, com vento leve)
ArenaVirtual	Desenha a arena e gera a imagem da câmera virtual
MavDrone	Fala com a Pixhawk real ou SITL via MAVLink (modo GUIDED)

Parâmetros no topo do arquivo:

Parâmetro	Valor	Efeito
ALT_BUSCA	3,0 m	Altura da varredura
ALT_FINAL	1,0 m	Altura em que, alinhado, manda o comando de pouso
V_MAX	0,6 m/s	Velocidade máxima no alinhamento
KP_ALINHA, KI_ALINHA	0,8 e 0,25	Ganhos do controle de alinhamento sobre a base
V_DESCIDA	0,35 m/s	Velocidade de descida enquanto alinha
TOL_ALINHA	0,12 m	Erro máximo para continuar descendo
VOTOS_MIN	3	Quantas leituras iguais para confiar numa base
VARREDURA	lista	Pontos (leste, norte) em metros percorridos na busca
CAM_HFOV_DEG	60°	Campo de visão da câmera (precisa ser medido)
Sugestões de aprimoramento

Escolha uma, faça e valide com o teste em lote:

Medir o campo de visão real da câmera. Fixe a câmera a uma altura h conhecida sobre uma trena e anote a largura L que aparece na imagem. Então CAM_HFOV_DEG = 2 × atan(L / (2h)). Valor errado faz o drone errar a posição das bases.
Robustez à iluminação. Teste a câmera real com luz forte, sombra e contraluz; ajuste ADAPT_BLOCK e ADAPT_C olhando a imagem binarizada (tecla d).
Altura máxima de leitura. Descubra até que altura os números ainda são lidos e ajuste ALT_BUSCA.
Tempo de missão. Reduza o tempo médio sem perder acertos (rota de varredura mais curta, velocidades maiores).
IDs ambíguos (12, 15, 20...). Hoje o código escolhe a base mais vista e avisa "ID AMBIGUO". Confirme no regulamento como a organização trata esse caso e ajuste a regra em decide e Mapa.decidir.
Simulador mais realista. Aumente o vento em SimDrone ou o atraso de resposta e veja se o pouso continua preciso.

Para testar uma arena específica com um ID escolhido, use o Prompt de Comando dentro da pasta:

.venv\Scripts\python.exe m1_missao.py --sim --seed 5 --id 20
Como entregar sua melhoria
Antes de começar, faça uma cópia dos arquivos .py originais.
Anote o resultado do teste em lote antes e depois da mudança.
Envie para o capitão técnico: os arquivos alterados, o que mudou (2 ou 3 linhas) e os dois resultados do lote.
Problemas comuns
Sintoma	Causa e solução
Janela abre e fecha ao clicar num .py	Não abra os .py direto; use sempre os .bat
Python nao encontrado no 0_instalar.bat	Refaça o Passo 1 marcando "Add python.exe to PATH"
Ambiente nao instalado	Rode o 0_instalar.bat primeiro
Erro de pip, SSL ou timeout na instalação	Sem internet ou rede bloqueada; tente outra rede (por exemplo, roteador do celular)
Nao consegui abrir a fonte de video	IP errado, câmera desligada, notebook em outra rede ou stream aberto no navegador
Vídeo muito lento ou atrasado	Câmera em resolução alta; use framesize&val=11 (Passo 7)
ArUco não detectado	Dicionário diferente: coloque o do regulamento no topo de ARUCO_DICTS
Números lidos errado na câmera real	Iluminação ou altura; veja a imagem binarizada (tecla d)
SITL: Sem LOCAL_POSITION_NED	O simulador ainda não tem posição; espere o GPS ficar verde e rode de novo
SITL: não conecta	Tente a porta 5763 no 5_missao_sitl.bat
Real: fica conectando e não passa	Mission Planner aberto (feche) ou ESP8266 fora da rede
Real: Nao armou	Veja as linhas [Pixhawk] no console: são os motivos do pré-arm
Segurança
Nunca rode o modo real sozinho. Sempre com piloto de segurança no rádio, pronto para trocar o modo.
Hélices conferidas, bateria carregada e área livre de pessoas antes de digitar VOAR.
Primeiro voo de cada mudança no código: sempre no simulador e no teste em lote antes.
Em qualquer comportamento estranho: piloto assume no rádio, depois analise o arquivo de logs/.
