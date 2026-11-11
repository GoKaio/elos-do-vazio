# Changelog — Elos do Vazio

Todas as alterações notáveis deste projeto são registradas neste arquivo.

## [1.1.0] — 2026-11-11

### Alterado / Adicionado
- **Combate Single-Player Reformulado ([player.py](player.py), [inimigos.py](inimigos.py), [combate.py](combate.py), [main.py](main.py)):** sistema estritamente 1 Jogador com **Esquiva Rasteira / Roll Dash** (`14` I-Frames e hurtbox pela metade) e **Salto de Reação / Impulso Aéreo com Pogo**.
- **5 Arquétipos de Inimigos com Ataques Exclusivos ([inimigos.py](inimigos.py)):** máquina de estados `PREPARANDO -> EXECUTANDO -> RECUPERACAO` e padrões dedicados (`BOTE_FENDIDO`, `CLAVA_SISMICA`, `LANCA_DO_VAZIO`, `GUILHOTINA_TRIPLICE`, `FURIA_ELOS_RUNICOS`).
- **Chaves Rúnicas e Puzzle da Sala 7 Funcionais ([main.py](main.py), [gerenciador_salas.py](gerenciador_salas.py), [combate.py](combate.py)):** coleta automática/E de chaves com bolsa persistente (`Chaves`), enfraquecimento de chefes (`-15%` HP) caso o portão já esteja aberto e quebra em 3 estágios do Escudo Arcano do Bibliotecário do Vazio via Relíquias da Sala 7 (dano direto, Éter, vulnerabilidade e turno preventivo).
- **Empacotamento e Instalador ([build_exe.py](build_exe.py), [build_instalador.py](build_instalador.py), [instalador_gui.py](instalador_gui.py)):** inclusão de `player` e `inimigos` nos `--hidden-import`, recompilação garantida do payload atualizado e versão atualizada para **v1.1**.

## [1.0.0] — 2026-11-10

### Adicionado
- **Abertura do Estúdio (`splash_estudio.py`):** tela inicial discreta da **GoZygrid Studios** com entrada/saída suaves ao abrir o jogo.
- **Campanha com 7 Salas em 4 Biomas (`gerenciador_salas.py`, `cenarios.py`):** Ameias e Pátio Superior, Galerias das Torres de Vigia, Catacumbas Subterrâneas e Santuário do Guardião.
- **Combate Tático 2.5D (`combate.py`, `cenario_combate_25d.py`):** turnos com QTE ofensivo (`[Z]`), **Parry Perfeito (`[X]`)** com *hitstop*, **Esquiva (`[C]`)**, **Salto Defensivo (`[ESPAÇO]`)** sobre ondas sísmicas e câmera dinâmica.
- **Modos Especiais:** Campanha Completa, **Boss Rush** contra os 7 chefes, suporte nativo a **Controles Xbox / PlayStation** e **Modo Bot Autônomo (`[F2]`)**.
- **Instalador Gótico Windows (`instalador_gui.py`, `build_instalador.py`):** assistente gráfico em 4 etapas com música tema e criação automática de atalhos `.lnk`.
- **Documentação & Mídia:** manual técnico [elos_do_vazio_guia_github.pdf](elos_do_vazio_guia_github.pdf), pôster [elos_do_vazio_exposicao.pdf](elos_do_vazio_exposicao.pdf), gerador de trailer Full HD (`gerar_trailer.py`) e prévia GIF (`assets/trailer_preview.gif`).
