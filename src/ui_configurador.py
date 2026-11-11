# -*- coding: utf-8 -*-
"""
ELOS DO VAZIO - Módulo de Configuração e Editor de Posições da Interface (UI Layout Editor).

Permite aos jogadores customizar manualmente, salvar e restaurar as posições de
todos os 23 elementos de UI do jogo em 5 categorias completas:
1. COMBATE (HUD Jogador, Menu Ações, Linha do Tempo, Barra de Chefe, Banner/QTE, Cronômetro Combate, Alvo)
2. MENU PRINCIPAL (Logo do Jogo, Botões de Ação, Herói no Menu, Rival no Menu, Status/Rodapé)
3. MAPA 2D (HUD de Vida no Mapa, Minimapa/Correntes, Cronômetro Exploração, Faixa de Dicas)
4. BOSS RUSH (Placa Boss Rush, Barra de Chefe do Rush, Mural dos Campeões)
5. OUTRAS TELAS (Altar da Morte, Painel de Vitória Lendária, Janela Nome Herói, Mural de Ranque)

Recursos de Ergonomia e Visual:
- Smart Auto-Docking: A barra de ferramentas se posiciona automaticamente no topo ou na base
  para NUNCA cobrir o elemento que está sendo ajustado!
- Arraste fluido com o Mouse (Drag & Drop)
- Botões de Ajuste Fino [-10] [-1] [+1] [+10] para X e Y com precisão de pixel
- Navegação completa por Teclado (Setas/WASD, Shift para 10px, 1-5 para Abas, Enter/Esc/R)
- Suporte total a Controles USB/Xbox (D-Pad, LB/RB, A, B, X, Y)
- Persistência instantânea em elos_do_vazio_ui_positions.json
"""

import os
import math
import json
import pygame
import caminhos
import ui_medieval
import ui_procedural
from config import CONFIG
import cenarios

try:
    import audio
except Exception:
    audio = None

LARGURA_TELA = 960
ALTURA_TELA = 540

# -----------------------------------------------------------------------------
# CATEGORIAS DE ELEMENTOS
# -----------------------------------------------------------------------------
CATEGORIAS = [
    ("combate",   "1. COMBATE",   "Elementos visuais da arena de batalha e QTE"),
    ("menu",      "2. MENU",      "Layout do menu inicial e vitrine de personagens"),
    ("mapa",      "3. MAPA 2D",   "HUD de exploração das masmorras e minimapa"),
    ("boss_rush", "4. BOSS RUSH", "Placas e interface exclusivas do modo Boss Rush"),
    ("outros",    "5. OUTRAS",    "Telas de Morte, Vitória, Nome do Herói e Ranque"),
]

# -----------------------------------------------------------------------------
# DEFINIÇÃO DAS POSIÇÕES PADRÃO DE CADA ELEMENTO DA UI (TOTAL: 23 ELEMENTOS)
# -----------------------------------------------------------------------------
CONFIG_UI_PADRAO = {
    # === CATEGORIA 1: COMBATE 2.5D (7) ===
    "hud_jogador": {
        "x": 618,
        "y": 382,
        "w": 308,
        "h": 134,
        "nome": "HUD do Jogador (Combate)",
        "desc": "Painel Viajante: HP, Éter/AP, Nível, Vidas e Poções",
        "modo": "combate",
        "icone": "espada",
    },
    "menu_combate": {
        "x": 250,
        "y": 382,
        "w": 356,
        "h": 134,
        "nome": "Menu de Ações (Combate)",
        "desc": "Placas de Atacar/Habilidades, Itens e Fugir",
        "modo": "combate",
        "icone": "espada",
    },
    "timeline": {
        "x": 14,
        "y": 18,
        "w": 56,
        "h": 450,
        "nome": "Linha do Tempo (Combate)",
        "desc": "Ordem dos turnos verticais à esquerda",
        "modo": "combate",
        "icone": "relogio",
    },
    "barra_boss": {
        "x": 200,
        "y": 16,
        "w": 560,
        "h": 48,
        "nome": "Barra de Vida do Chefe",
        "desc": "Barra colossal de vida e nome do Chefe no topo da arena",
        "modo": "combate",
        "icone": "caveira",
    },
    "banner_turno": {
        "x": 270,
        "y": 18,
        "w": 420,
        "h": 36,
        "nome": "Banner de Turno (Combate)",
        "desc": "Banner de impacto, esquiva, parry e avisos de turno",
        "modo": "combate",
        "icone": "coroa",
    },
    "cronometro_combate": {
        "x": 792,
        "y": 16,
        "w": 152,
        "h": 28,
        "nome": "Cronômetro (Combate)",
        "desc": "Contador de tempo contínuo no topo durante a luta",
        "modo": "combate",
        "icone": "relogio",
    },
    "janela_defesa": {
        "x": 166,
        "y": 451,
        "w": 440,
        "h": 68,
        "nome": "Janela de Defesa / QTE",
        "desc": "Indicador de Parry, Pulo e Esquiva durante o ataque inimigo",
        "modo": "combate",
        "icone": "escudo",
    },

    # === CATEGORIA 2: MENU PRINCIPAL (5) ===
    "logo_menu": {
        "x": 75,
        "y": 120,
        "w": 470,
        "h": 248,
        "nome": "Logo do Jogo (Menu)",
        "desc": "Placa gótica de pedra suspensa com a Logo ELOS DO VAZIO",
        "modo": "menu",
        "icone": "coroa",
    },
    "botoes_menu": {
        "x": 615,
        "y": 120,
        "w": 310,
        "h": 250,
        "nome": "Botões de Ação (Menu)",
        "desc": "Menu principal: Jogar, Salas, Ranque, Configurar, Bot, Sair",
        "modo": "menu",
        "icone": "portao",
    },
    "heroi_menu": {
        "x": 70,
        "y": 365,
        "w": 75,
        "h": 115,
        "nome": "Herói no Menu",
        "desc": "Sprite do Guerreiro/Soldado na vitrine inferior esquerda",
        "modo": "menu",
        "icone": "elmo",
    },
    "rival_menu": {
        "x": 770,
        "y": 365,
        "w": 85,
        "h": 115,
        "nome": "Rival / Monstro no Menu",
        "desc": "Sprite do Orc na vitrine inferior direita",
        "modo": "menu",
        "icone": "caveira",
    },
    "rodape_menu": {
        "x": 200,
        "y": 480,
        "w": 560,
        "h": 50,
        "nome": "Status e Rodapé (Menu)",
        "desc": "Placa com nível, sala, vidas e atalhos de controle",
        "modo": "menu",
        "icone": "escudo",
    },

    # === CATEGORIA 3: MAPA 2D (4) ===
    "mapa_hud_vida": {
        "x": 16,
        "y": 16,
        "w": 260,
        "h": 60,
        "nome": "Painel do Herói (Mapa 2D)",
        "desc": "Status unificado (HP, Éter, Poções e Vidas) com margem segura de 16px",
        "modo": "mapa",
        "icone": "escudo",
    },
    "mapa_minimapa": {
        "x": 310,
        "y": 16,
        "w": 340,
        "h": 28,
        "nome": "Placa de Missão (Centro Topo)",
        "desc": "Sub-região e objetivo no topo central deixando a lua livre",
        "modo": "mapa",
        "icone": "portao",
    },
    "cronometro_mapa": {
        "x": 16,
        "y": 496,
        "w": 128,
        "h": 28,
        "nome": "Relógio (Rodapé Esquerdo)",
        "desc": "Tempo contínuo travado no canto inferior esquerdo",
        "modo": "mapa",
        "icone": "relogio",
    },
    "mapa_dicas": {
        "x": 310,
        "y": 54,
        "w": 340,
        "h": 30,
        "nome": "Notificações e Dicas (Mapa 2D)",
        "desc": "Avisos de portão e mecanismos abaixo da placa central",
        "modo": "mapa",
        "icone": "cristal_ap",
    },

    # === CATEGORIA 4: BOSS RUSH (3) ===
    "boss_rush_badge": {
        "x": 14,
        "y": 14,
        "w": 360,
        "h": 32,
        "nome": "Placa Boss Rush (Combate)",
        "desc": "Banner superior com contagem e nome do chefe ativo (Ex: BOSS RUSH 1/7)",
        "modo": "boss_rush",
        "icone": "caveira",
    },
    "boss_rush_barra": {
        "x": 260,
        "y": 8,
        "w": 440,
        "h": 46,
        "nome": "Barra de Chefe (Boss Rush)",
        "desc": "Barra colossal de vida e nome do chefe nos combates do Rush",
        "modo": "boss_rush",
        "icone": "caveira",
    },
    "boss_rush_mural": {
        "x": 25,
        "y": 20,
        "w": 910,
        "h": 500,
        "nome": "Mural dos Campeões (Ranque)",
        "desc": "Tabela de recordes com os melhores tempos no Boss Rush",
        "modo": "boss_rush",
        "icone": "coroa",
    },

    # === CATEGORIA 5: OUTRAS TELAS (4) ===
    "morte_painel": {
        "x": 170,
        "y": 260,
        "w": 620,
        "h": 250,
        "nome": "Altar da Morte (Tela de Queda)",
        "desc": "Painel central com tentativas restantes, recomeço e desistência",
        "modo": "outros",
        "icone": "caveira",
    },
    "vitoria_painel": {
        "x": 150,
        "y": 120,
        "w": 660,
        "h": 320,
        "nome": "Estandarte de Vitória Lendária",
        "desc": "Mural de conquista da campanha com estatísticas finais",
        "modo": "outros",
        "icone": "coroa",
    },
    "nome_heroi_painel": {
        "x": 200,
        "y": 120,
        "w": 560,
        "h": 280,
        "nome": "Janela de Nome do Herói",
        "desc": "Proclamação real para digitar o nome do campeão",
        "modo": "outros",
        "icone": "espada",
    },
    "ranque_tabela": {
        "x": 25,
        "y": 20,
        "w": 910,
        "h": 500,
        "nome": "Mural do Hall da Fama (Ranque)",
        "desc": "Tabela de recordes com abas de Campanha e Boss Rush",
        "modo": "outros",
        "icone": "coroa",
    },
}

_ARQUIVO_CONFIG_UI = "elos_do_vazio_ui_positions.json"
_antigo_config_ui = "endbound_ui_positions.json"
if not os.path.exists(_ARQUIVO_CONFIG_UI) and os.path.exists(_antigo_config_ui):
    try:
        os.replace(_antigo_config_ui, _ARQUIVO_CONFIG_UI)
    except Exception:
        pass
_posicoes_atuais = {}


def carregar_posicoes():
    """Carrega as posições salvas em disco ou inicializa com os padrões."""
    global _posicoes_atuais
    _posicoes_atuais = {}
    for k, v in CONFIG_UI_PADRAO.items():
        _posicoes_atuais[k] = {
            "x": v["x"],
            "y": v["y"],
            "w": v["w"],
            "h": v["h"],
            "nome": v["nome"],
            "desc": v["desc"],
            "modo": v["modo"],
            "icone": v.get("icone", "espada"),
        }

    caminho_dados = os.path.join(caminhos.obter_dir_dados(), _ARQUIVO_CONFIG_UI)
    caminho = caminho_dados if os.path.exists(caminho_dados) else caminhos.obter_caminho_recurso(_ARQUIVO_CONFIG_UI)
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict):
                    for k, v in dados.items():
                        if k in _posicoes_atuais and isinstance(v, dict):
                            if "x" in v and "y" in v:
                                _posicoes_atuais[k]["x"] = int(v["x"])
                                _posicoes_atuais[k]["y"] = int(v["y"])
            caminhos.log_info(f"Posições de UI carregadas de '{_ARQUIVO_CONFIG_UI}'.")
        except Exception as e:
            caminhos.log_aviso(f"Erro ao carregar '{_ARQUIVO_CONFIG_UI}': {e}. Usando padrões.")
    return _posicoes_atuais


def salvar_posicoes():
    """Persiste as posições atuais em disco no formato JSON."""
    caminho = os.path.join(caminhos.obter_dir_dados(), _ARQUIVO_CONFIG_UI)
    dados = {}
    for k, v in _posicoes_atuais.items():
        dados[k] = {"x": v["x"], "y": v["y"]}
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        caminhos.log_info(f"Posições de UI salvas com sucesso em '{caminho}'.")
        return True
    except Exception as e:
        caminhos.log_erro(f"Falha ao salvar '{_ARQUIVO_CONFIG_UI}': {e}")
        return False


def restaurar_padroes(categoria=None):
    """Restaura todas as posições para os valores de fábrica (ou só de uma categoria)."""
    global _posicoes_atuais
    for k, v in CONFIG_UI_PADRAO.items():
        if k in _posicoes_atuais:
            if categoria is None or _posicoes_atuais[k]["modo"] == categoria:
                _posicoes_atuais[k]["x"] = v["x"]
                _posicoes_atuais[k]["y"] = v["y"]
    salvar_posicoes()


def obter_posicao(chave):
    """Retorna uma tupla (x, y) com as coordenadas atuais do elemento."""
    if not _posicoes_atuais:
        carregar_posicoes()
    elem = _posicoes_atuais.get(chave)
    if elem:
        return elem["x"], elem["y"]
    padrao = CONFIG_UI_PADRAO.get(chave)
    if padrao:
        return padrao["x"], padrao["y"]
    return 0, 0


def definir_posicao(chave, x, y):
    """Atualiza a posição de um elemento específico em memória."""
    if not _posicoes_atuais:
        carregar_posicoes()
    if chave in _posicoes_atuais:
        elem = _posicoes_atuais[chave]
        elem["x"] = max(0, min(960 - elem["w"], int(x)))
        elem["y"] = max(0, min(540 - elem["h"], int(y)))


# Inicializa as posições no carregamento do módulo
carregar_posicoes()


def salvar_config_exposicao(modo_ativo, tempo_limite, sala_limite):
    """
    Atualiza as opções do Modo Exposição em memória e salva no config.py em disco.
    """
    CONFIG["modo_exposicao_ativo"] = bool(modo_ativo)
    CONFIG["exposicao_tempo_limite_segundos"] = int(tempo_limite)
    CONFIG["exposicao_sala_limite"] = int(sala_limite)

    caminhos_alvo = [
        os.path.join(os.path.dirname(__file__), "config.py")
    ]
    for c_path in caminhos_alvo:
        if os.path.exists(c_path):
            try:
                with open(c_path, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                import re
                conteudo = re.sub(
                    r'"modo_exposicao_ativo":\s*(True|False)',
                    f'"modo_exposicao_ativo": {str(bool(modo_ativo))}',
                    conteudo
                )
                conteudo = re.sub(
                    r'"exposicao_tempo_limite_segundos":\s*\d+',
                    f'"exposicao_tempo_limite_segundos": {int(tempo_limite)}',
                    conteudo
                )
                conteudo = re.sub(
                    r'"exposicao_sala_limite":\s*\d+',
                    f'"exposicao_sala_limite": {int(sala_limite)}',
                    conteudo
                )
                with open(c_path, "w", encoding="utf-8") as f:
                    f.write(conteudo)
                caminhos.log_info(f"Configuração do modo exposição salva em '{c_path}'.")
            except Exception as e:
                caminhos.log_aviso(f"Erro ao salvar config.py em '{c_path}': {e}")



# =============================================================================
# TELA / EDITOR INTERATIVO DE CONFIGURAÇÃO DE UI (TODOS OS 23 ELEMENTOS)
# =============================================================================
class TelaConfiguradorUI:
    """
    Tela interativa que permite ao jogador visualizar, selecionar e reposicionar
    TODOS os 23 elementos de interface do jogo em tempo real.
    """

    def __init__(self, fonte_pequena=None, fonte_media=None, fonte_grande=None):
        self.chaves_ordenadas = list(CONFIG_UI_PADRAO.keys())
        self.sel_idx = 0
        self.modo_idx = 0  # 0: combate, 1: menu, 2: mapa, 3: boss_rush, 4: outros
        self.arrastando = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.tempo_toast = 0.0
        self.msg_toast = ""
        self.t = 0.0

        # Docking inteligente: "auto", "topo" ou "base"
        self.dock_modo = "auto"
        self.dock_topo_ativo = False

        # Fontes seguras
        self.fonte_peq = fonte_pequena or pygame.font.SysFont("Cardo, EB Garamond, Arial", 14, bold=True)
        self.fonte_med = fonte_media or pygame.font.SysFont("Cinzel, Cormorant SC, Arial", 17, bold=True)
        self.fonte_grd = fonte_grande or pygame.font.SysFont("Cinzel Decorative, Cinzel, Arial", 22, bold=True)

        # Retângulos das 5 Abas Superiores
        self.rects_abas = []

        # Retângulos dos botões de ajuste fino [-10] [-1] [+1] [+10]
        self.rects_ajuste_fino = {}

        # Retângulos dos botões de ação do dock
        self.rect_btn_salvar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_padrao = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_cancelar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_dock_flip = pygame.Rect(0, 0, 0, 0)

    @property
    def modo_visualizacao(self):
        return CATEGORIAS[self.modo_idx][0]

    @property
    def chave_ativa(self):
        chaves_modo = self._elementos_do_modo()
        if not chaves_modo:
            return self.chaves_ordenadas[0]
        if self.sel_idx < len(self.chaves_ordenadas):
            c = self.chaves_ordenadas[self.sel_idx]
            if c in chaves_modo:
                return c
        return chaves_modo[0]

    def _elementos_do_modo(self):
        return [k for k in self.chaves_ordenadas if _posicoes_atuais[k]["modo"] == self.modo_visualizacao]

    def mudar_aba(self, novo_idx):
        self.modo_idx = novo_idx % len(CATEGORIAS)
        chaves_modo = self._elementos_do_modo()
        if chaves_modo:
            self.sel_idx = self.chaves_ordenadas.index(chaves_modo[0])

    def proxima_aba(self):
        self.mudar_aba(self.modo_idx + 1)

    def aba_anterior(self):
        self.mudar_aba(self.modo_idx - 1)

    def alternar_dock(self):
        if self.dock_modo == "auto":
            self.dock_modo = "topo" if not self.dock_topo_ativo else "base"
        elif self.dock_modo == "topo":
            self.dock_modo = "base"
        else:
            self.dock_modo = "auto"

    def selecionar_proximo(self):
        chaves_modo = self._elementos_do_modo()
        if not chaves_modo:
            return
        if self.chave_ativa in chaves_modo:
            idx_no_modo = chaves_modo.index(self.chave_ativa)
            prox_chave = chaves_modo[(idx_no_modo + 1) % len(chaves_modo)]
        else:
            prox_chave = chaves_modo[0]
        self.sel_idx = self.chaves_ordenadas.index(prox_chave)

    def selecionar_anterior(self):
        chaves_modo = self._elementos_do_modo()
        if not chaves_modo:
            return
        if self.chave_ativa in chaves_modo:
            idx_no_modo = chaves_modo.index(self.chave_ativa)
            ant_chave = chaves_modo[(idx_no_modo - 1) % len(chaves_modo)]
        else:
            ant_chave = chaves_modo[-1]
        self.sel_idx = self.chaves_ordenadas.index(ant_chave)

    def mover_ativo(self, dx, dy):
        elem = _posicoes_atuais[self.chave_ativa]
        elem["x"] = max(0, min(960 - elem["w"], elem["x"] + dx))
        elem["y"] = max(0, min(540 - elem["h"], elem["y"] + dy))

    def salvar(self):
        if salvar_posicoes():
            self.msg_toast = "Todas as 23 posicoes foram salvas com sucesso!"
            self.tempo_toast = 2.2
            return True
        return False

    def restaurar(self):
        restaurar_padroes(categoria=self.modo_visualizacao)
        cat_nome = CATEGORIAS[self.modo_idx][1]
        self.msg_toast = f"Padroes restaurados para {cat_nome}!"
        self.tempo_toast = 2.2

    def update(self, dt):
        self.t += dt
        if self.tempo_toast > 0:
            self.tempo_toast -= dt

    def handle_event(self, event):
        """
        Processa cliques do mouse, teclas de navegação e botões do controle.
        Retorna 'voltar', 'salvo' ou None.
        """
        # --- TECLADO ---
        if event.type == pygame.KEYDOWN:
            passo = 10 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 2
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.mover_ativo(-passo, 0)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.mover_ativo(passo, 0)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.mover_ativo(0, -passo)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.mover_ativo(0, passo)

            # Troca de abas via teclas 1, 2, 3, 4, 5
            elif event.key == pygame.K_1:
                self.mudar_aba(0)
            elif event.key == pygame.K_2:
                self.mudar_aba(1)
            elif event.key == pygame.K_3:
                self.mudar_aba(2)
            elif event.key == pygame.K_4:
                self.mudar_aba(3)
            elif event.key == pygame.K_5:
                self.mudar_aba(4)

            elif event.key in (pygame.K_TAB, pygame.K_SPACE):
                self.proxima_aba()
            elif event.key == pygame.K_e:
                self.selecionar_proximo()
            elif event.key == pygame.K_q:
                self.selecionar_anterior()
            elif event.key == pygame.K_f:
                self.alternar_dock()
            elif event.key == pygame.K_r:
                self.restaurar()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.salvar()
                return "salvo"
            elif event.key == pygame.K_ESCAPE:
                carregar_posicoes()  # Descarta alterações não salvas
                return "voltar"

        # --- JOYSTICK / CONTROLE ---
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A (Xbox) -> Salvar
                self.salvar()
                return "salvo"
            elif event.button == 1:  # B (Xbox) -> Cancelar/Voltar
                carregar_posicoes()
                return "voltar"
            elif event.button == 2:  # X (Xbox) -> Restaurar
                self.restaurar()
            elif event.button == 3:  # Y (Xbox) -> Alternar Dock / Próxima Aba
                self.proxima_aba()
            elif event.button in (4, 9):  # LB -> Aba Anterior
                self.aba_anterior()
            elif event.button in (5, 10):  # RB -> Próxima Aba
                self.proxima_aba()

        elif event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value
            passo = 4
            if hat_x != 0:
                self.mover_ativo(hat_x * passo, 0)
            if hat_y != 0:
                self.mover_ativo(0, -hat_y * passo)

        # --- MOUSE (ARRASTAR & CLICAR) ---
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # 1. Verifica clique nas 5 abas
            for idx_a, r_aba in enumerate(self.rects_abas):
                if r_aba.collidepoint(mx, my):
                    self.mudar_aba(idx_a)
                    return None

            # 2. Verifica botões de ação do dock
            if self.rect_btn_salvar.collidepoint(mx, my):
                self.salvar()
                return "salvo"
            elif self.rect_btn_padrao.collidepoint(mx, my):
                self.restaurar()
                return None
            elif self.rect_btn_cancelar.collidepoint(mx, my):
                carregar_posicoes()
                return "voltar"
            elif self.rect_btn_dock_flip.collidepoint(mx, my):
                self.alternar_dock()
                return None

            # 3. Verifica botões de ajuste fino [-10], [-1], [+1], [+10]
            for acao, r_fino in self.rects_ajuste_fino.items():
                if r_fino.collidepoint(mx, my):
                    if acao == "x_-10": self.mover_ativo(-10, 0)
                    elif acao == "x_-1":  self.mover_ativo(-1, 0)
                    elif acao == "x_+1":  self.mover_ativo(1, 0)
                    elif acao == "x_+10": self.mover_ativo(10, 0)
                    elif acao == "y_-10": self.mover_ativo(0, -10)
                    elif acao == "y_-1":  self.mover_ativo(0, -1)
                    elif acao == "y_+1":  self.mover_ativo(0, 1)
                    elif acao == "y_+10": self.mover_ativo(0, 10)
                    return None

            # 4. Verifica clique em algum elemento para selecioná-lo e iniciar arraste
            for k in reversed(self._elementos_do_modo()):
                elem = _posicoes_atuais[k]
                r = pygame.Rect(elem["x"], elem["y"], elem["w"], elem["h"])
                if r.collidepoint(mx, my):
                    self.sel_idx = self.chaves_ordenadas.index(k)
                    self.arrastando = True
                    self.drag_offset_x = mx - elem["x"]
                    self.drag_offset_y = my - elem["y"]
                    return None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.arrastando = False

        elif event.type == pygame.MOUSEMOTION:
            if self.arrastando:
                mx, my = event.pos
                elem = _posicoes_atuais[self.chave_ativa]
                novo_x = max(0, min(960 - elem["w"], mx - self.drag_offset_x))
                novo_y = max(0, min(540 - elem["h"], my - self.drag_offset_y))
                elem["x"] = novo_x
                elem["y"] = novo_y

        return None

    def draw(self, surface):
        """Renderiza a interface do editor com o cenário ativo e molduras iluminadas."""
        LARGURA_TELA = 960
        ALTURA_TELA = 540

        # 1. Fundo escuro com vinheta e grade medieval de referência
        surface.fill((16, 13, 20))
        grade_surf = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        for gx in range(0, LARGURA_TELA, 40):
            pygame.draw.line(grade_surf, (35, 28, 48, 55), (gx, 0), (gx, ALTURA_TELA), 1)
        for gy in range(0, ALTURA_TELA, 40):
            pygame.draw.line(grade_surf, (35, 28, 48, 55), (0, gy), (LARGURA_TELA, gy), 1)
        surface.blit(grade_surf, (0, 0))

        # Determina posição inteligente do Dock (Topo vs Base) para NUNCA encobrir o elemento ativo
        elem_ativo = _posicoes_atuais[self.chave_ativa]
        if self.dock_modo == "topo":
            dock_no_topo = True
        elif self.dock_modo == "base":
            dock_no_topo = False
        else:  # "auto"
            dock_no_topo = (elem_ativo["y"] > 240)
        self.dock_topo_ativo = dock_no_topo

        dock_h = 70
        dock_y = 6 if dock_no_topo else (ALTURA_TELA - dock_h - 6)

        # 2. Desenha todos os elementos da categoria ativa
        chaves_modo = self._elementos_do_modo()
        for k in chaves_modo:
            elem = _posicoes_atuais[k]
            x, y, w, h = elem["x"], elem["y"], elem["w"], elem["h"]
            rect = pygame.Rect(x, y, w, h)
            is_ativo = (k == self.chave_ativa)

            # Moldura gótica padronizada em ardósia profunda e latão envelhecido
            ui_procedural.desenhar_moldura_gotica(
                surface, rect, chanfro=6, destacado=is_ativo, alpha=238, cantoneiras=is_ativo
            )

            # Ícone temático no canto superior esquerdo (com fallback seguro para tipos extras)
            ico_raw = elem.get("icone", "espada")
            ico_map = {
                "espada": "espada",
                "portao": "portao",
                "grade": "grade",
                "pocao": "frasco",
                "frasco": "frasco",
                "escudo": "escudo",
                "coroa": "coroa",
                "relogio": "relogio",
                "cristal": "cristal",
                "caveira": "caveira",
                "elmo": "escudo",
            }
            ico_tipo = ico_map.get(ico_raw, "espada")
            ui_procedural.desenhar_icone_tematico(surface, ico_tipo, x + 15, y + 15, tamanho=14, aceso=is_ativo)

            if is_ativo:
                # Efeito pulsante dourado em torno do elemento ativo
                pulso = 0.5 + 0.5 * math.sin(self.t * 5.0)
                alpha_borda = int(175 + 75 * pulso)
                borda_surf = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
                pygame.draw.rect(borda_surf, (*ui_procedural.COR_OURO_VIVO, alpha_borda), (0, 0, w + 8, h + 8), 2)
                surface.blit(borda_surf, (x - 4, y - 4))

            # Rótulo com nome e coordenadas
            cor_txt = ui_procedural.COR_OURO_VIVO if is_ativo else (248, 250, 252)
            lbl = self.fonte_peq.render(elem["nome"], True, cor_txt)
            surface.blit(lbl, (x + 28, y + 7))

            coords_txt = f"X: {x}  Y: {y}  ({w}x{h})"
            lbl_c = self.fonte_peq.render(coords_txt, True, ui_procedural.COR_CINZA_TEXTO)
            surface.blit(lbl_c, (x + 28, y + 25))

            if is_ativo and h >= 56:
                dica_arraste = self.fonte_peq.render("ARRASTE COM O MOUSE OU USE SETAS", True, (120, 245, 175))
                surface.blit(dica_arraste, (x + 8, y + h - 18))

        # 3. DOCK UNIFICADO DE CONTROLE E ABAS (SUPERIOR OU INFERIOR)
        r_dock = pygame.Rect(8, dock_y, LARGURA_TELA - 16, dock_h)
        ui_procedural.desenhar_moldura_gotica(surface, r_dock, chanfro=6, destacado=True, alpha=246, cantoneiras=True)

        # LINHA 1 DO DOCK: 5 Abas de Categorias + Botão de Virar Dock (⇅)
        self.rects_abas = []
        aba_w = 114
        aba_h = 26
        aba_y = r_dock.y + 6
        inicio_aba_x = r_dock.x + 8

        for i_cat, (cat_id, cat_nome, cat_desc) in enumerate(CATEGORIAS):
            r_aba = pygame.Rect(inicio_aba_x + i_cat * (aba_w + 5), aba_y, aba_w, aba_h)
            self.rects_abas.append(r_aba)
            ativa = (i_cat == self.modo_idx)
            ui_procedural.desenhar_botao_gotico(
                surface, r_aba, cat_nome, self.fonte_peq,
                selecionado=ativa, icone=None
            )

        # Botão Flip Dock (Mudar para Topo/Base)
        r_flip_x = inicio_aba_x + len(CATEGORIAS) * (aba_w + 5) + 6
        self.rect_btn_dock_flip = pygame.Rect(r_flip_x, aba_y, 68, aba_h)
        lbl_dock_flip = "⇅ DOCK"
        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_dock_flip, lbl_dock_flip, self.fonte_peq, selecionado=False)

        # Dica rápida de teclado à direita da Linha 1
        dica_keys = self.fonte_peq.render("[1-5] Abas   [F] Dock   [Shift] 10px", True, ui_procedural.COR_CINZA_TEXTO)
        surface.blit(dica_keys, (r_dock.right - dica_keys.get_width() - 10, aba_y + 4))

        # LINHA 2 DO DOCK: Elemento Ativo + Ajuste Fino [-10][-1][+1][+10] + Salvar/Restaurar/Voltar
        pos_y_l2 = r_dock.y + 36
        self.rects_ajuste_fino = {}

        # Rótulo X
        lbl_x = self.fonte_peq.render(f"X: {elem_ativo['x']}", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(lbl_x, (r_dock.x + 10, pos_y_l2 + 4))

        botoes_x = [("-10", "x_-10", 30), ("-1", "x_-1", 24), ("+1", "x_+1", 24), ("+10", "x_+10", 30)]
        cur_bx = r_dock.x + 64
        for texto_b, id_b, bw in botoes_x:
            r_b = pygame.Rect(cur_bx, pos_y_l2, bw, 24)
            self.rects_ajuste_fino[id_b] = r_b
            ui_procedural.desenhar_botao_gotico(surface, r_b, texto_b, self.fonte_peq, selecionado=False)
            cur_bx += bw + 3

        # Rótulo Y
        cur_bx += 8
        lbl_y = self.fonte_peq.render(f"Y: {elem_ativo['y']}", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(lbl_y, (cur_bx, pos_y_l2 + 4))
        cur_bx += 52

        botoes_y = [("-10", "y_-10", 30), ("-1", "y_-1", 24), ("+1", "y_+1", 24), ("+10", "y_+10", 30)]
        for texto_b, id_b, bw in botoes_y:
            r_b = pygame.Rect(cur_bx, pos_y_l2, bw, 24)
            self.rects_ajuste_fino[id_b] = r_b
            ui_procedural.desenhar_botao_gotico(surface, r_b, texto_b, self.fonte_peq, selecionado=False)
            cur_bx += bw + 3

        # Nome do elemento selecionado no centro da Linha 2
        cur_bx += 10
        nome_elem_txt = f"{elem_ativo['nome'][:20]}"
        lbl_elem = self.fonte_peq.render(nome_elem_txt, True, ui_procedural.COR_OURO_VIVO)
        surface.blit(lbl_elem, (cur_bx, pos_y_l2 + 4))

        # Botões de Ação na extremidade direita da Linha 2
        bw_salv = 110
        bw_padr = 104
        bw_canc = 80
        self.rect_btn_salvar = pygame.Rect(r_dock.right - bw_salv - 10, pos_y_l2, bw_salv, 26)
        self.rect_btn_padrao = pygame.Rect(self.rect_btn_salvar.left - bw_padr - 6, pos_y_l2, bw_padr, 26)
        self.rect_btn_cancelar = pygame.Rect(self.rect_btn_padrao.left - bw_canc - 6, pos_y_l2, bw_canc, 26)

        lbl_salvar = "(A) SALVAR" if ui_medieval.usar_controle() else "[ENTER] SALVAR"
        lbl_padrao = "(X) PADRÃO" if ui_medieval.usar_controle() else "[R] PADRÃO"
        lbl_canc = "(B) SAIR" if ui_medieval.usar_controle() else "[ESC] SAIR"

        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_salvar, lbl_salvar, self.fonte_peq, selecionado=True, icone=None)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_padrao, lbl_padrao, self.fonte_peq, selecionado=False, icone=None)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_cancelar, lbl_canc, self.fonte_peq, selecionado=False, icone=None)

        # 4. Notificação Toast de feedback (se ativa)
        if self.tempo_toast > 0 and self.msg_toast:
            tw = 480
            th = 40
            r_toast = pygame.Rect(LARGURA_TELA // 2 - tw // 2, ALTURA_TELA // 2 - th // 2, tw, th)
            ui_procedural.desenhar_moldura_gotica(surface, r_toast, chanfro=6, destacado=True, alpha=248, cantoneiras=True)
            txt_t = self.fonte_med.render(self.msg_toast, True, (120, 255, 180))
            surface.blit(txt_t, (r_toast.centerx - txt_t.get_width() // 2, r_toast.centery - txt_t.get_height() // 2))


# =============================================================================
# TELA INTERATIVA DE AJUSTE DO MODO APRESENTAÇÃO (SHOWCASE / KIOSK)
# =============================================================================
class TelaConfiguracaoExposicao:
    """
    Painel Interativo de Ajuste do Modo Apresentação / Exposição (Showcase & Kiosk Mode).
    Permite ativar/desativar o modo de evento, regular o tempo da sessão (com lista de durações
    e incremento/decremento), selecionar a sala limite da demo e salvar instantaneamente.
    """
    TEMPOS_OPCOES = [60, 120, 180, 240, 300, 360, 420, 480, 600, 900]

    def __init__(self, fonte_peq=None, fonte_med=None, fonte_grd=None):
        self.fonte_peq = fonte_peq or pygame.font.SysFont("Cardo, EB Garamond, Arial", 14, bold=True)
        self.fonte_med = fonte_med or pygame.font.SysFont("Cinzel, Cormorant SC, Arial", 17, bold=True)
        self.fonte_grd = fonte_grd or pygame.font.SysFont("Cinzel Decorative, Cinzel, Arial", 22, bold=True)

        self.t = 0.0
        self.opcao_foco = 0  # 0: Modo Ativo, 1: Tempo Limite, 2: Sala Limite, 3: Salvar, 4: Voltar
        self.toast_msg = ""
        self.toast_tempo = 0.0

        # Carrega valores atuais de CONFIG
        self.carregar_valores()

        # Retângulos interativos de clique
        self.rect_toggle_ativo = pygame.Rect(0, 0, 0, 0)
        self.rect_tempo_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_tempo_mais = pygame.Rect(0, 0, 0, 0)
        self.rect_sala_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_sala_mais = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_salvar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_voltar = pygame.Rect(0, 0, 0, 0)

    def carregar_valores(self):
        self.modo_ativo = bool(CONFIG.get("modo_exposicao_ativo", False))
        self.tempo_limite = int(CONFIG.get("exposicao_tempo_limite_segundos", 300))
        self.sala_limite = int(CONFIG.get("exposicao_sala_limite", 3))

    def salvar(self):
        salvar_config_exposicao(self.modo_ativo, self.tempo_limite, self.sala_limite)
        self.toast_msg = "Configurações de Exposição Salvas com Sucesso!"
        self.toast_tempo = 2.5
        if audio and hasattr(audio, "tocar_sfx"):
            audio.tocar_sfx("ui_select", 0.6)

    def alterar_tempo(self, delta):
        idx_atual = 4
        for i, val in enumerate(self.TEMPOS_OPCOES):
            if val >= self.tempo_limite:
                idx_atual = i
                break
        novo_idx = max(0, min(len(self.TEMPOS_OPCOES) - 1, idx_atual + delta))
        self.tempo_limite = self.TEMPOS_OPCOES[novo_idx]
        if audio and hasattr(audio, "tocar_sfx"):
            audio.tocar_sfx("ui_select", 0.4)

    def alterar_sala(self, delta):
        self.sala_limite = max(1, min(7, self.sala_limite + delta))
        if audio and hasattr(audio, "tocar_sfx"):
            audio.tocar_sfx("ui_select", 0.4)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.opcao_foco = (self.opcao_foco - 1) % 5
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.35)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.opcao_foco = (self.opcao_foco + 1) % 5
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.35)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.opcao_foco == 0:
                    self.modo_ativo = not self.modo_ativo
                    if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.5)
                elif self.opcao_foco == 1:
                    self.alterar_tempo(-1)
                elif self.opcao_foco == 2:
                    self.alterar_sala(-1)
                elif self.opcao_foco in (3, 4):
                    self.opcao_foco = 3 if self.opcao_foco == 4 else 4
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.opcao_foco == 0:
                    self.modo_ativo = not self.modo_ativo
                    if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.5)
                elif self.opcao_foco == 1:
                    self.alterar_tempo(+1)
                elif self.opcao_foco == 2:
                    self.alterar_sala(+1)
                elif self.opcao_foco in (3, 4):
                    self.opcao_foco = 4 if self.opcao_foco == 3 else 3
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.opcao_foco == 0:
                    self.modo_ativo = not self.modo_ativo
                    if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.5)
                elif self.opcao_foco == 1:
                    self.alterar_tempo(+1)
                elif self.opcao_foco == 2:
                    self.alterar_sala(+1)
                elif self.opcao_foco == 3:
                    self.salvar()
                    return "salvo"
                elif self.opcao_foco == 4:
                    self.carregar_valores()
                    return "voltar"
            elif event.key == pygame.K_ESCAPE:
                self.carregar_valores()
                return "voltar"

        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A -> Confirmar
                if self.opcao_foco == 0:
                    self.modo_ativo = not self.modo_ativo
                    if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.5)
                elif self.opcao_foco == 1:
                    self.alterar_tempo(+1)
                elif self.opcao_foco == 2:
                    self.alterar_sala(+1)
                elif self.opcao_foco == 3:
                    self.salvar()
                    return "salvo"
                elif self.opcao_foco == 4:
                    self.carregar_valores()
                    return "voltar"
            elif event.button == 1:  # B -> Voltar
                self.carregar_valores()
                return "voltar"
            elif event.button in (4, 9):  # LB -> Decrementar
                if self.opcao_foco == 1: self.alterar_tempo(-1)
                elif self.opcao_foco == 2: self.alterar_sala(-1)
            elif event.button in (5, 10):  # RB -> Incrementar
                if self.opcao_foco == 1: self.alterar_tempo(+1)
                elif self.opcao_foco == 2: self.alterar_sala(+1)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect_toggle_ativo.collidepoint(mx, my):
                self.opcao_foco = 0
                self.modo_ativo = not self.modo_ativo
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.5)
            elif self.rect_tempo_menos.collidepoint(mx, my):
                self.opcao_foco = 1
                self.alterar_tempo(-1)
            elif self.rect_tempo_mais.collidepoint(mx, my):
                self.opcao_foco = 1
                self.alterar_tempo(+1)
            elif self.rect_sala_menos.collidepoint(mx, my):
                self.opcao_foco = 2
                self.alterar_sala(-1)
            elif self.rect_sala_mais.collidepoint(mx, my):
                self.opcao_foco = 2
                self.alterar_sala(+1)
            elif self.rect_btn_salvar.collidepoint(mx, my):
                self.opcao_foco = 3
                self.salvar()
                return "salvo"
            elif self.rect_btn_voltar.collidepoint(mx, my):
                self.opcao_foco = 4
                self.carregar_valores()
                return "voltar"

        return None

    def update(self, dt):
        self.t += dt
        if self.toast_tempo > 0:
            self.toast_tempo = max(0.0, self.toast_tempo - dt)

    def draw(self, surface):
        cx, cy = LARGURA_TELA // 2, ALTURA_TELA // 2
        pw, ph = 680, 440
        px, py = cx - pw // 2, cy - ph // 2
        painel = pygame.Rect(px, py, pw, ph)
        ui_procedural.desenhar_moldura_gotica(surface, painel, chanfro=8, destacado=True, alpha=246, cantoneiras=True, cranios=True)

        # Cabeçalho
        ui_procedural.desenhar_icone_tematico(surface, "relogio", cx, py + 30, tamanho=24, aceso=True)
        txt_tit = self.fonte_grd.render("CONFIGURAÇÃO DO MODO APRESENTAÇÃO", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(txt_tit, (cx - txt_tit.get_width() // 2, py + 52))
        txt_sub = self.fonte_peq.render("Parâmetros do modo Kiosk para feiras, demonstrações e estandes públicos", True, ui_procedural.COR_CINZA_TEXTO)
        surface.blit(txt_sub, (cx - txt_sub.get_width() // 2, py + 84))

        ui_procedural.desenhar_divisor_dourado(surface, px + 36, py + 104, pw - 72)

        # Opção 0: Ativar/Desativar
        y_opt0 = py + 116
        sel0 = (self.opcao_foco == 0)
        lbl0 = self.fonte_med.render("Modo Exposição / Demonstração:", True, ui_procedural.COR_OURO_VIVO if sel0 else (248, 250, 252))
        surface.blit(lbl0, (px + 45, y_opt0 + 8))

        self.rect_toggle_ativo = pygame.Rect(px + pw - 230, y_opt0, 185, 36)
        texto_ativo = "LIGADO (ATIVO)" if self.modo_ativo else "DESLIGADO"
        ui_procedural.desenhar_moldura_gotica(
            surface, self.rect_toggle_ativo, chanfro=5, destacado=sel0 or self.modo_ativo, alpha=240, cantoneiras=sel0
        )
        surf_badge = self.fonte_peq.render(texto_ativo, True, (120, 255, 180) if self.modo_ativo else ui_procedural.COR_CINZA_TEXTO)
        surface.blit(surf_badge, (self.rect_toggle_ativo.centerx - surf_badge.get_width() // 2, self.rect_toggle_ativo.centery - surf_badge.get_height() // 2))

        # Opção 1: Tempo Limite da Sessão
        y_opt1 = py + 168
        sel1 = (self.opcao_foco == 1)
        lbl1 = self.fonte_med.render("Tempo Limite da Sessão:", True, ui_procedural.COR_OURO_VIVO if sel1 else (248, 250, 252))
        surface.blit(lbl1, (px + 45, y_opt1 + 8))

        self.rect_tempo_menos = pygame.Rect(px + pw - 245, y_opt1, 32, 36)
        self.rect_tempo_mais = pygame.Rect(px + pw - 75, y_opt1, 32, 36)
        rect_tempo_val = pygame.Rect(px + pw - 210, y_opt1, 132, 36)

        ui_procedural.desenhar_botao_gotico(surface, self.rect_tempo_menos, "<", self.fonte_med, selecionado=False)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_tempo_mais, ">", self.fonte_med, selecionado=False)
        ui_procedural.desenhar_moldura_gotica(surface, rect_tempo_val, chanfro=5, destacado=sel1, alpha=240, cantoneiras=sel1)

        m_t, s_t = self.tempo_limite // 60, self.tempo_limite % 60
        txt_t_val = f"{m_t:02d}:{s_t:02d} ({m_t}m)"
        surf_t = self.fonte_med.render(txt_t_val, True, ui_procedural.COR_OURO_VIVO if sel1 else (248, 250, 252))
        surface.blit(surf_t, (rect_tempo_val.centerx - surf_t.get_width() // 2, rect_tempo_val.centery - surf_t.get_height() // 2))

        # Opção 2: Sala Limite da Demonstração
        y_opt2 = py + 220
        sel2 = (self.opcao_foco == 2)
        lbl2 = self.fonte_med.render("Sala Limite da Demo:", True, ui_procedural.COR_OURO_VIVO if sel2 else (248, 250, 252))
        surface.blit(lbl2, (px + 45, y_opt2 + 8))

        self.rect_sala_menos = pygame.Rect(px + pw - 245, y_opt2, 32, 36)
        self.rect_sala_mais = pygame.Rect(px + pw - 75, y_opt2, 32, 36)
        rect_sala_val = pygame.Rect(px + pw - 210, y_opt2, 132, 36)

        ui_procedural.desenhar_botao_gotico(surface, self.rect_sala_menos, "<", self.fonte_med, selecionado=False)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_sala_mais, ">", self.fonte_med, selecionado=False)
        ui_procedural.desenhar_moldura_gotica(surface, rect_sala_val, chanfro=5, destacado=sel2, alpha=240, cantoneiras=sel2)

        txt_s_val = f"Sala {self.sala_limite}"
        surf_s = self.fonte_med.render(txt_s_val, True, ui_procedural.COR_OURO_VIVO if sel2 else (248, 250, 252))
        surface.blit(surf_s, (rect_sala_val.centerx - surf_s.get_width() // 2, rect_sala_val.centery - surf_s.get_height() // 2))

        # Caixa de Explicação / Resumo em Tempo Real
        y_box = py + 272
        rect_expl = pygame.Rect(px + 40, y_box, pw - 80, 72)
        ui_procedural.desenhar_moldura_gotica(surface, rect_expl, chanfro=5, destacado=False, alpha=232, cantoneiras=False)

        if self.modo_ativo:
            nome_s = cenarios.DADOS_MAPAS.get(self.sala_limite - 1, {}).get("nome", f"Sala {self.sala_limite}")
            msg1 = f"• O jogador terá {m_t}m ({self.tempo_limite}s) com cronômetro regressivo no HUD."
            msg2 = f"• A sessão se encerra ao derrotar o chefe da Sala {self.sala_limite} ({nome_s}) ou se o tempo zerar."
            cor_expl = (140, 240, 190)
        else:
            msg1 = "• Modo Campanha Padrão: Sem limitação de tempo ou de avanço de salas."
            msg2 = "• O cronômetro superior contará continuamente como indicador de velocidade."
            cor_expl = (226, 232, 240)

        s_m1 = self.fonte_peq.render(msg1, True, cor_expl)
        s_m2 = self.fonte_peq.render(msg2, True, ui_procedural.COR_CINZA_TEXTO)
        surface.blit(s_m1, (rect_expl.left + 16, rect_expl.top + 14))
        surface.blit(s_m2, (rect_expl.left + 16, rect_expl.top + 40))

        # Botões Salvar e Voltar
        y_btns = py + 360
        self.rect_btn_salvar = pygame.Rect(cx - 245, y_btns, 225, 44)
        self.rect_btn_voltar = pygame.Rect(cx + 20, y_btns, 225, 44)

        sel_salv = (self.opcao_foco == 3)
        sel_volt = (self.opcao_foco == 4)

        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_salvar, "SALVAR E APLICAR", self.fonte_med, selecionado=sel_salv, icone="espada")
        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_voltar, "VOLTAR", self.fonte_med, selecionado=sel_volt, icone="portao")

        # Toast de Confirmação
        if self.toast_tempo > 0:
            surf_tst = self.fonte_med.render(self.toast_msg, True, (130, 255, 180))
            box_tst = pygame.Rect(0, 0, surf_tst.get_width() + 32, 34)
            box_tst.center = (cx, py + ph - 24)
            ui_procedural.desenhar_moldura_gotica(surface, box_tst, chanfro=5, destacado=True, alpha=248, cantoneiras=True)
            surface.blit(surf_tst, (box_tst.centerx - surf_tst.get_width() // 2, box_tst.centery - surf_tst.get_height() // 2))


# =============================================================================
# CENTRAL DE CONFIGURAÇÕES (HUB COM ESCOLHA DE MODO APRESENTAÇÃO E UI)
# =============================================================================
class TelaMenuConfiguracoes:
    """
    Central de Configurações de ELOS DO VAZIO.
    Permite escolher entre:
      1. MODO APRESENTAÇÃO / EVENTO (Showcase Kiosk)
      2. CONFIGURAÇÕES DE INTERFACE (UI Layout Editor)
      3. VOLTAR AO MENU
    """
    def __init__(self, fonte_peq=None, fonte_med=None, fonte_grd=None):
        self.fonte_peq = fonte_peq or pygame.font.SysFont("Cardo, EB Garamond, Arial", 14, bold=True)
        self.fonte_med = fonte_med or pygame.font.SysFont("Cinzel, Cormorant SC, Arial", 17, bold=True)
        self.fonte_grd = fonte_grd or pygame.font.SysFont("Cinzel Decorative, Cinzel, Arial", 22, bold=True)

        self.t = 0.0
        self.estado = "HUB"  # "HUB" | "EXPOSICAO" | "UI_LAYOUT"
        self.sel_idx = 0     # 0: Modo Apresentação, 1: Configurar UI, 2: Voltar

        self.tela_exposicao = TelaConfiguracaoExposicao(self.fonte_peq, self.fonte_med, self.fonte_grd)
        self.tela_ui = TelaConfiguradorUI(self.fonte_peq, self.fonte_med, self.fonte_grd)

        self.rects_cards = []

    def abrir_hub(self):
        self.estado = "HUB"
        self.tela_exposicao.carregar_valores()

    def handle_event(self, event):
        if self.estado == "EXPOSICAO":
            res = self.tela_exposicao.handle_event(event)
            if res in ("voltar", "salvo"):
                self.estado = "HUB"
            return None

        elif self.estado == "UI_LAYOUT":
            res = self.tela_ui.handle_event(event)
            if res in ("voltar", "salvo"):
                self.estado = "HUB"
            return None

        # --- ESTADO "HUB" ---
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.sel_idx = (self.sel_idx - 1) % 3
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.4)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel_idx = (self.sel_idx + 1) % 3
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.4)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self._ativar_opcao(self.sel_idx)
            elif event.key == pygame.K_ESCAPE:
                return "voltar"

        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A (Xbox)
                return self._ativar_opcao(self.sel_idx)
            elif event.button == 1:  # B (Xbox)
                return "voltar"

        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] > 0:
                self.sel_idx = (self.sel_idx - 1) % 3
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.4)
            elif event.value[1] < 0:
                self.sel_idx = (self.sel_idx + 1) % 3
                if audio and hasattr(audio, "tocar_sfx"): audio.tocar_sfx("ui_select", 0.4)

        elif event.type == pygame.MOUSEMOTION:
            for idx, r in enumerate(self.rects_cards):
                if r.collidepoint(event.pos):
                    self.sel_idx = idx

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, r in enumerate(self.rects_cards):
                if r.collidepoint(event.pos):
                    self.sel_idx = idx
                    return self._ativar_opcao(idx)

        return None

    def _ativar_opcao(self, idx):
        if audio and hasattr(audio, "tocar_sfx"):
            audio.tocar_sfx("door_open", 0.7)
        if idx == 0:
            self.tela_exposicao.carregar_valores()
            self.estado = "EXPOSICAO"
            return None
        elif idx == 1:
            self.estado = "UI_LAYOUT"
            return None
        elif idx == 2:
            return "voltar"
        return None

    def update(self, dt):
        self.t += dt
        if self.estado == "EXPOSICAO":
            self.tela_exposicao.update(dt)
        elif self.estado == "UI_LAYOUT":
            self.tela_ui.update(dt)

    def draw(self, surface):
        if self.estado == "EXPOSICAO":
            self.tela_exposicao.draw(surface)
            return
        elif self.estado == "UI_LAYOUT":
            self.tela_ui.draw(surface)
            return

        # Desenha a Central de Configurações (HUB)
        cx, cy = LARGURA_TELA // 2, ALTURA_TELA // 2
        pw, ph = 680, 440
        px, py = cx - pw // 2, cy - ph // 2
        painel = pygame.Rect(px, py, pw, ph)
        ui_procedural.desenhar_moldura_gotica(surface, painel, chanfro=8, destacado=True, alpha=246, cantoneiras=True, cranios=True)

        # Cabeçalho Nobre
        ui_procedural.desenhar_icone_tematico(surface, "escudo", cx, py + 30, tamanho=24, aceso=True)
        txt_tit = self.fonte_grd.render("CENTRAL DE CONFIGURAÇÕES", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(txt_tit, (cx - txt_tit.get_width() // 2, py + 52))
        txt_sub = self.fonte_peq.render("Personalize a interface do jogo ou as restrições para demonstrações públicas", True, ui_procedural.COR_CINZA_TEXTO)
        surface.blit(txt_sub, (cx - txt_sub.get_width() // 2, py + 84))

        ui_procedural.desenhar_divisor_dourado(surface, px + 36, py + 106, pw - 72)

        self.rects_cards = []

        # Card 1: Modo Apresentação / Evento
        r_c1 = pygame.Rect(px + 45, py + 120, pw - 90, 84)
        self.rects_cards.append(r_c1)
        sel1 = (self.sel_idx == 0)
        ui_procedural.desenhar_moldura_gotica(surface, r_c1, chanfro=6, destacado=sel1, alpha=242, cantoneiras=sel1)
        ui_procedural.desenhar_icone_tematico(surface, "relogio", r_c1.left + 32, r_c1.centery, tamanho=22, aceso=sel1)

        tit_c1 = self.fonte_med.render("MODO APRESENTAÇÃO (DEMO / EVENTO)", True, ui_procedural.COR_OURO_VIVO if sel1 else (248, 250, 252))
        desc_c1 = self.fonte_peq.render("Limite o tempo por partida e a quantidade de salas acessíveis para feiras e eventos.", True, ui_procedural.COR_CINZA_TEXTO)

        ativo_expo = CONFIG.get("modo_exposicao_ativo", False)
        t_lim = CONFIG.get("exposicao_tempo_limite_segundos", 300)
        s_lim = CONFIG.get("exposicao_sala_limite", 3)
        m_t, s_t = t_lim // 60, t_lim % 60
        status_txt = f"Status: [ ATIVO ] • {m_t:02d}:{s_t:02d} • Até Sala {s_lim}" if ativo_expo else "Status: [ DESATIVADO ] • Campanha Normal"
        cor_st = (120, 255, 180) if ativo_expo else ui_procedural.COR_CINZA_TEXTO
        st_c1 = self.fonte_peq.render(status_txt, True, cor_st)

        surface.blit(tit_c1, (r_c1.left + 60, r_c1.top + 10))
        surface.blit(desc_c1, (r_c1.left + 60, r_c1.top + 34))
        surface.blit(st_c1, (r_c1.left + 60, r_c1.top + 56))

        # Card 2: Configuração de Interface (UI)
        r_c2 = pygame.Rect(px + 45, py + 220, pw - 90, 84)
        self.rects_cards.append(r_c2)
        sel2 = (self.sel_idx == 1)
        ui_procedural.desenhar_moldura_gotica(surface, r_c2, chanfro=6, destacado=sel2, alpha=242, cantoneiras=sel2)
        ui_procedural.desenhar_icone_tematico(surface, "espada", r_c2.left + 32, r_c2.centery, tamanho=22, aceso=sel2)

        tit_c2 = self.fonte_med.render("CONFIGURAÇÕES DE INTERFACE (UI)", True, ui_procedural.COR_OURO_VIVO if sel2 else (248, 250, 252))
        desc_c2 = self.fonte_peq.render("Editor visual interativo: reposicione manualmente todos os 23 elementos do jogo.", True, ui_procedural.COR_CINZA_TEXTO)
        st_c2 = self.fonte_peq.render("5 Categorias: Combate, Menu, Mapa 2D, Boss Rush e Telas Especiais", True, ui_procedural.COR_OURO_VIVO)

        surface.blit(tit_c2, (r_c2.left + 60, r_c2.top + 10))
        surface.blit(desc_c2, (r_c2.left + 60, r_c2.top + 34))
        surface.blit(st_c2, (r_c2.left + 60, r_c2.top + 56))

        # Card 3 / Botão: Voltar ao Menu
        r_c3 = pygame.Rect(cx - 165, py + 325, 330, 44)
        self.rects_cards.append(r_c3)
        sel3 = (self.sel_idx == 2)
        ui_procedural.desenhar_botao_gotico(surface, r_c3, "VOLTAR AO MENU", self.fonte_med, selecionado=sel3, icone="portao")

        # Dica de Navegação no Rodapé
        c = ui_medieval.usar_controle()
        dica_str = "(LS / D-PAD) Navegar   |   (A) Confirmar   |   (B) Voltar" if c else "[W / S / SETAS] Navegar   |   [ENTER / ESPAÇO] Confirmar   |   [ESC] Voltar"
        ui_procedural.desenhar_rodape_comandos(surface, py + ph - 24, dica_str, self.fonte_peq, largura=LARGURA_TELA)

