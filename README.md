<div align="center">

  <img src="assets/logo_gozygrid.png" alt="GoZygrid Studios" width="230" />

  <br/>

  <img src="assets/ui/logo_elos_do_vazio.png" alt="Elos do Vazio" width="460" />

  <h3>Plataforma 2D &amp; Combate Tático 2.5D Dark Fantasy em Python (<code>pygame-ce</code>)</h3>

  <p>
    <a href="https://github.com/GoKaio/elos-do-vazio/releases/latest/download/Instalador_Elos_do_Vazio.exe">
      <img src="https://img.shields.io/badge/%E2%AC%87%EF%B8%8F_BAIXAR_INSTALADOR_WINDOWS-Instalador__Elos__do__Vazio.exe-D97706?style=for-the-badge&logo=windows&logoColor=F8FAFC&labelColor=0B0F19" alt="Baixar Instalador Windows (.exe)" />
    </a>
    &nbsp;
    <a href="https://github.com/GoKaio/elos-do-vazio/releases">
      <img src="https://img.shields.io/badge/GitHub-Releases-38BDF8?style=for-the-badge&logo=github&logoColor=F8FAFC&labelColor=13192B" alt="Todas as Releases" />
    </a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B_%7C_3.12-38BDF8?style=flat-square&labelColor=0B0F19" alt="Python" />
    <img src="https://img.shields.io/badge/Engine-pygame--ce_%E2%89%A5_2.5.0-D97706?style=flat-square&labelColor=0B0F19" alt="pygame-ce" />
    <img src="https://img.shields.io/badge/Resolu%C3%A7%C3%A3o-960x540_(SCALED_16%3A9)-CBD5E1?style=flat-square&labelColor=0B0F19" alt="Resolução" />
    <img src="https://img.shields.io/badge/Modos-Campanha_%7C_Boss_Rush_%7C_Co--op_Local-94A3B8?style=flat-square&labelColor=0B0F19" alt="Modos de Jogo" />
  </p>

  <br/>

  <img src="assets/trailer_preview.gif" alt="Prévia de Combate, Esquiva e Parry 2.5D — Elos do Vazio" width="640" />

  <br/>
  <sub><i>Trailer oficial de gameplay: combate em catacumbas, esquiva com i-frames e Parry Perfeito na arena 2.5D.</i></sub>

</div>

---

## Sobre o Jogo

**Elos do Vazio** é um jogo de ação, plataforma 2D e combate tático 2.5D desenvolvido pela **GoZygrid Studios**. Ambientado em uma cidadela gótica arruinada pela queda dos selos de Éter, o Viajante deve cruzar **7 salas distribuídas em 4 biomas distintos**, destrancar portões de ferro por alavancas e chaves, dominar reações defensivas em tempo real (*Parry*, *Esquiva* e *Salto* sobre ondas sísmicas) e derrotar o guardião final.

### Principais Características
- **Combate Tático 2.5D com Reações em Tempo Real:** sistema por turnos com câmera dinâmica, golpes com janela de **QTE ofensivo**, **Parry Perfeito (`[X]`)** com *hitstop* de impacto e recuperação de Éter (+AP), **Esquiva (`[C]`)** e **Salto Defensivo (`[ESPAÇO]`)**.
- **7 Salas em 4 Biomas Temáticos (`gerenciador_salas.py`):** progressão de ameias exteriores sob luar, galerias com plataformas suspensas por correntes, catacumbas fechadas com plataformas móveis e a arena final do Guardião.
- **Renderização Procedural Gótica (`cenarios.py` & `cenario_combate_25d.py`):** cantaria autotiled 32x32 via `pygame.PixelArray`, pisos 2.5D com projeção cônica e perspectiva $1/Z$, tochas com halo suave `SRCALPHA` e efeitos de partículas.
- **Modos Especiais:** Campanha Completa, **Boss Rush** contínuo contra os 7 chefes, suporte a **Controles USB/Bluetooth (Xbox / PlayStation)** e **Modo Autônomo (IA) (`[F2]`)**.

---

## Guia das 7 Salas da Masmorra

| Sala | Nome da Câmara | Bioma | Guardião / Chefe | Mecânicas e Elementos |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Pátio das Ameias** | Ameias e Pátio Superior | Guardião do Cemitério | Exterior noturno, lua cheia, mastros com bandeiras e alavanca da guarita. |
| **2** | **Ameias Superiores** | Ameias e Pátio Superior | Ente da Árvore Torta | Patamares em 3 alturas crescentes, vãos de muralha e armadilhas de veneno. |
| **3** | **Galeria da Torre** | Galerias das Torres de Vigia | Carcereiro dos Portões | Torres em paralaxe, degraus rebaixados, chaves e portão ancorado ao pátio leste. |
| **4** | **Torre de Vigia Suspensa** | Galerias das Torres de Vigia | Zelador do Mausoléu | Passarelas suspensas por correntes sobre o fosso e rotas bilaterais de retorno. |
| **5** | **Catacumbas Subterrâneas** | Cripta e Catacumbas | Sentinela de Pedra | Teto fechado em cantaria escura, grades de ferro, lápides, arcos e tochas frias. |
| **6** | **Cripta dos Ossos** | Cripta e Catacumbas | Rei da Lua Sangrenta | Plataformas móveis mecanizadas sobre trilhos e fossos com espinhos estreitos. |
| **7** | **Santuário do Guardião** | Santuário do Guardião | Bibliotecário do Vazio | Arena plana monumental (960 px), gárgulas, 3 glifos de Éter e Portão Titânico Rúnico. |

---

## Como Baixar e Instalar

### Opção 1 — Executável Pronto para Windows (Modo Jogador)

Para jogar diretamente no Windows **sem precisar configurar Python ou bibliotecas externas**:

1. Acesse a aba [**Releases**](https://github.com/GoKaio/elos-do-vazio/releases) (ou clique no botão **Baixar Instalador Windows** no topo deste README).
2. Baixe o arquivo **`Instalador_Elos_do_Vazio.exe`** e execute-o com dois cliques.
3. Siga as **4 etapas do instalador gótico** até a conclusão:

| Etapa | O que faz |
| :--- | :--- |
| **Etapa 1 · Boas-Vindas** | Apresenta a moldura Dark Fantasy, versão e controle de música ambiente em loop; clique em **`AVANÇAR >`**. |
| **Etapa 2 · Diretório & Opções** | Permite editar o caminho padrão (`C:\Jogos\Elos do Vazio`), escolher outra pasta e marcar a criação de atalhos. |
| **Etapa 3 · Instalação Ativa** | Descompacta o jogo em *thread* separada com barra segmentada em ciano de Éter e badalo de sino nos 100%. |
| **Etapa 4 · Conclusão & Atalhos** | Cria atalhos **`.lnk`** automáticos na **Área de Trabalho** e no **Menu Iniciar** e libera o botão **`JOGAR AGORA`**. |

### Opção 2 — Baixar e Rodar via Código-Fonte (Modo Desenvolvedor)

Requer **Python 3.10+** (recomendado **Python 3.12**) e Git instalados no Windows (ou faça o download direto em **`Code → Download ZIP`** nesta página e extraia os arquivos):

```powershell
# 1. Clonar o repositório e entrar na pasta
git clone https://github.com/GoKaio/elos-do-vazio.git
cd elos-do-vazio

# 2. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Iniciar o jogo
python main.py
```

> No Windows, após clonar ou extrair o `.zip`, você também pode simplesmente dar dois cliques em **`INSTALAR_DEPENDENCIAS.bat`** e depois em **`JOGAR.bat`**.

### Documentação em PDF Incluída

- 📄 [**Manual Técnico GitHub & Instalação (`elos_do_vazio_guia_github.pdf`)**](elos_do_vazio_guia_github.pdf) — guia passo a passo com modo jogador e desenvolvedor.
- 📄 [**Painel Editorial de Exposição (`elos_do_vazio_exposicao.pdf`)**](elos_do_vazio_exposicao.pdf) — ficha técnica Dark Fantasy, sinopse e prévia dos 4 biomas.

---

## Instruções de Compilação (`.exe` & Instalador Gótico)

O projeto possui pipeline completo via **PyInstaller** para gerar tanto o executável portátil do jogo quanto o instalador gráfico `Instalador_Elos_do_Vazio.exe`:

### Opção 1 — Automação Completa (Windows `.bat`)
Execute **`build_tudo.bat`** com dois cliques ou pelo terminal:
```powershell
.\build_tudo.bat
```
Esse script instala `pyinstaller`, `pillow` e `pygame-ce`, extrai `Legacy-Dungeon_V0.2_vacaroxa.zip` se presente e executa `python build_instalador.py --all`.

### Opção 2 — Comandos Python Diretos
```powershell
pip install pyinstaller pillow pygame-ce

# Compila dist/Elos_do_Vazio/Elos_do_Vazio.exe + empacota dist_installer/Instalador_Elos_do_Vazio.exe
python build_instalador.py --all

# Alternativa: gerar em --onefile ou apenas o executável / instalador
python build_instalador.py --only-installer
python build_exe.py
```

---

## Controles Essenciais

| Contexto | Ação | Teclado | Controle (Xbox / PS) |
| :--- | :--- | :--- | :--- |
| **Exploração** | Mover / Saltar | `A`/`D` ou Setas • `ESPAÇO` / `W` | Analógico / D-Pad • `A` / Cruz |
| **Exploração** | Interagir / Pausa | `E` / `ENTER` • `ESC` | `X` / Quadrado • `START` |
| **Combate (Turno)** | Menu / Trocar Alvo | Setas • `ENTER` / `Z` • `A`/`D` | D-Pad • `A` • `LB`/`RB` |
| **Combate (Reação)** | **Parry Perfeito** | `X` | `X` / Quadrado |
| **Combate (Reação)** | **Esquivar / Pular Onda** | `C` • `ESPAÇO` | `B` / Círculo • `A` / Cruz |
| **Utilitários** | Bot Autônomo / Tela Cheia | `F2` • `F11` | — |

---

## Ferramentas de Mídia e Documentação Incluídas

| Script | Finalidade | Saída Gerada |
| :--- | :--- | :--- |
| `gerar_trailer.py` | Renderiza trailer cinematográfico 1920x1080 @ 60 FPS com áudio sincronizado | `trailer_elos_do_vazio.mp4` |
| `converter_trailer_gif.py` | Extrai 6s de combate em 640px otimizado para GitHub | `assets/trailer_preview.gif` |
| `gerar_documentos_pdf.py` | Gera pôster Dark Fantasy de exposição e manual técnico GitHub | `elos_do_vazio_exposicao.pdf` / `elos_do_vazio_guia_github.pdf` |

```powershell
# Sequência completa para gerar o trailer MP4 e extrair a prévia GIF deste README:
python gerar_trailer.py
python converter_trailer_gif.py
```

---

## Estrutura do Repositório

```text
elos-do-vazio/
├── main.py                      # Loop principal (960x540 SCALED), física 2D e estados
├── splash_estudio.py            # Animação discreta de abertura (GoZygrid Studios)
├── menu.py                      # Menu principal, seleção de salas, perfil e ranking
├── gerenciador_salas.py         # Construtores das 7 salas, 4 biomas e loader Legacy-Dungeon
├── cenarios.py                  # Tileset autotile 32x32 (PixelArray), paralaxe, tochas e portões
├── combate.py                   # Sistema tático por turnos, QTE, parry, hitstop e câmera
├── cenario_combate_25d.py       # Arena 2.5D com projeção cônica e piso 1/Z
├── sprites.py                   # Loader/animador modular de sprites e combatentes
├── instalador_gui.py            # Instalador gráfico 800x500 com música e atalhos .lnk
├── build_instalador.py          # Orquestrador de payload ZIP + Instalador PyInstaller
├── build_exe.py                 # Gerador de ícone .ico e compilação PyInstaller do jogo
├── build_tudo.bat               # Automação completa Windows (deps + exe + instalador)
├── gerar_trailer.py             # Gerador do trailer oficial Full HD 60 FPS
├── converter_trailer_gif.py     # Extrator de prévia GIF 640px otimizada
├── gerar_documentos_pdf.py      # Gerador de PDFs editoriais (Exposição e Guia GitHub)
├── elos_do_vazio_guia_github.pdf # Manual Técnico GitHub & Instalação (PDF)
├── elos_do_vazio_exposicao.pdf  # Painel Editorial de Exposição (PDF)
├── requirements.txt             # Dependências Python (pygame-ce>=2.5.0)
└── assets/                      # Logos, sprites, áudios (.ogg) e preview GIF
```

<div align="center">
  <sub>Desenvolvido por <b>GoZygrid Studios</b> — Projeto <b>Elos do Vazio</b></sub>
</div>
