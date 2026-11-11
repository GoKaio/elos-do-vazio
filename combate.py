# -*- coding: utf-8 -*-
"""
ELOS DO VAZIO - MÓDULO DE COMBATE TÁTICO 2.5D (combate.py)
Inspirado na arquitetura tática de Clair Obscur: Expedition 33.
- Câmera dinâmica cinematográfica com lerp (CameraCombateRig).
- Cenário de arena em perspectiva cônica tridimensional (trapézio de lajes góticas).
- Fluxo de turnos sequenciais individuais para cada criatura.
- Seleção de alvo unitário com retículo respiratório dourado.
- Habilidade em área 'Dança do Éter' atingindo todos os inimigos simultaneamente.
- Pausa tática entre ataques de inimigos diferentes.
- UI gótica Dark Fantasy integrada ao sistema modular (ui.py).
"""

import sys
import os
import math
import random
import unicodedata
from types import SimpleNamespace
import pygame

from config import CONFIG
import caminhos
import audio
import sprites
from sprites import (Animador, criar_animador, NovoCombatente, projetar_ponto_25d,
                     criar_heroi_modular)
import cenarios
from cenarios import LARGURA_TELA, ALTURA_TELA, desenhar_fundo_combate
from cenario_combate_25d import CameraCombate25D, CenarioCombate25D
import dados_combatentes
import ui
import ui_procedural
import combate_ui
import ui_medieval
import ranking
import ui_configurador
from bot_autonomo import BOT

# -----------------------------------------------------------------------------
# FONTES DO COMBATE
# -----------------------------------------------------------------------------
def _fonte_med(nomes, tamanho, bold=False):
    if not pygame.font.get_init():
        try:
            pygame.font.init()
        except Exception:
            pass
    for n in nomes:
        try:
            if pygame.font.match_font(n):
                return pygame.font.SysFont(n, tamanho, bold=bold)
        except Exception:
            pass
    try:
        return pygame.font.SysFont("serif", tamanho, bold=bold)
    except Exception:
        return pygame.font.Font(None, tamanho)

fonte_micro = _fonte_med(["Cardo", "EB Garamond", "DejaVu Serif"], 12, True)
fonte_pequena = _fonte_med(["Cardo", "EB Garamond", "Cormorant Garamond", "DejaVu Serif"], 15, True)
fonte = _fonte_med(["Cardo", "EB Garamond", "Cormorant Garamond", "DejaVu Serif"], 18, True)
fonte_menu = _fonte_med(["Cinzel", "Cormorant SC", "Alegreya SC", "DejaVu Serif"], 20, True)
fonte_grande = _fonte_med(["Cinzel", "Cinzel Decorative", "Alfa Slab One", "DejaVu Serif"], 30, True)
fonte_titulo = _fonte_med(["Cinzel Decorative", "Cinzel", "IM FELL English SC", "Alfa Slab One"], 42, True)

fontes_ui = {
    "normal": fonte,
    "pequena": fonte_pequena,
    "micro": fonte_micro,
    "menu": fonte_menu,
    "grande": fonte_grande,
    "titulo": fonte_titulo
}

# -----------------------------------------------------------------------------
# PALETA DE CORES E CONSTANTES DO COMBATE
# -----------------------------------------------------------------------------
COR_PERGAMINHO = (212, 190, 150)
COR_PERGAMINHO_ESC = (168, 140, 100)
COR_MADEIRA = (62, 38, 22)
COR_MADEIRA_CLARA = (98, 62, 36)
COR_OURO = (212, 175, 55)
COR_OURO_ESCURO = (150, 115, 30)
COR_FERRO = (55, 50, 48)
COR_FERRO_CLARO = (95, 88, 82)
COR_SANGUE = (140, 28, 28)
COR_SANGUE_CLARO = (180, 50, 45)
COR_MUSGO = (55, 95, 50)
COR_TEXTO = (35, 25, 15)
COR_TEXTO_CLARO = (235, 220, 185)
COR_TEXTO_OURO = (240, 210, 120)

GOLPES_SO_PULO = ("RASTEIRA", "ONDA_CHOQUE", "INVESTIDA", "TERREMOTO")
GOLPES_SO_PARRY = ("ESMAGAMENTO", "GOLPE_TITANICO", "QUEBRA_GUARDA", "RODOPIO")
GOLPES_SO_DESVIO = ("VENENO", "RUGIDO", "GOLPE_ARCANO", "GARRAS")
GOLPES_PADRAO = ("CORTE",)

POOL_GOLPES_COMUNS = ["CORTE", "ESMAGAMENTO", "RASTEIRA", "GARRAS", "VENENO"]
POOL_GOLPES_MEDIOS = POOL_GOLPES_COMUNS + ["RODOPIO", "GOLPE_ARCANO", "QUEBRA_GUARDA"]
POOL_GOLPES_BOSS = POOL_GOLPES_MEDIOS + ["ONDA_CHOQUE", "INVESTIDA", "RUGIDO", "GOLPE_TITANICO", "TERREMOTO"]

DESCRICAO_GOLPE = {
    "CORTE": "Lâmina rápida!",
    "ESMAGAMENTO": "Golpe esmagador!",
    "RASTEIRA": "Ataque rasteiro!",
    "ONDA_CHOQUE": "Onda destruidora!",
    "INVESTIDA": "Investida colossal!",
    "TERREMOTO": "Fissura sísmica!",
    "GOLPE_TITANICO": "Clava titânica!",
    "QUEBRA_GUARDA": "Golpe pesado!",
    "RODOPIO": "Giro devastador!",
    "GARRAS": "Garras dilacerantes!",
    "VENENO": "Névoa venenosa!",
    "GOLPE_ARCANO": "Energia arcana!",
    "RUGIDO": "Rugido sônico!",
}

DANO_GOLPE = {
    "CORTE": CONFIG["inimigo_dano_corte"],
    "ESMAGAMENTO": CONFIG["inimigo_dano_esmagamento"],
    "RASTEIRA": CONFIG["inimigo_dano_rastria"],
    "GARRAS": int(CONFIG["inimigo_dano_corte"] * 0.85),
    "VENENO": int(CONFIG["inimigo_dano_corte"] * 0.70),
    "GOLPE_ARCANO": int(CONFIG["inimigo_dano_esmagamento"] * 0.90),
    "RODOPIO": int(CONFIG["inimigo_dano_esmagamento"] * 1.10),
    "INVESTIDA": int(CONFIG["inimigo_dano_esmagamento"] * 1.05),
    "RUGIDO": int(CONFIG["inimigo_dano_corte"] * 0.60),
    "ONDA_CHOQUE": CONFIG.get("boss_dano_onda_choque", 30),
    "GOLPE_TITANICO": int(CONFIG["inimigo_dano_esmagamento"] * 1.15),
    "QUEBRA_GUARDA": int(CONFIG["inimigo_dano_esmagamento"] * 1.0),
    "TERREMOTO": CONFIG.get("boss_dano_onda_choque", 30),
}

DEBUFFS_INFO = {
    "VENENO": {
        "nome": "Veneno",
        "icone": "[TOX]",
        "cor": (90, 225, 75),
        "cor_bg": (22, 54, 18),
        "desc": "Sofre dano tóxico a cada turno",
    },
    "SANGRANDO": {
        "nome": "Sangria",
        "icone": "[SANG]",
        "cor": (255, 80, 80),
        "cor_bg": (60, 18, 18),
        "desc": "+30% de dano sofrido em ataques",
    },
    "LENTIDAO": {
        "nome": "Lentidão",
        "icone": "[LENT]",
        "cor": (210, 180, 255),
        "cor_bg": (45, 30, 65),
        "desc": "Inimigo realiza 1 golpe a menos nos combos",
    },
    "VULNERAVEL": {
        "nome": "Vulnerável",
        "icone": "[VULN]",
        "cor": (255, 215, 60),
        "cor_bg": (65, 55, 15),
        "desc": "+40% de dano sofrido em todos os ataques",
    },
    "FRAQUEZA": {
        "nome": "Fraqueza",
        "icone": "[FRAQ]",
        "cor": (140, 185, 255),
        "cor_bg": (20, 35, 60),
        "desc": "Inimigo causa -30% de dano nos ataques",
    },
    "QUEIMADURA": {
        "nome": "Queimadura",
        "icone": "[FOGO]",
        "cor": (255, 140, 40),
        "cor_bg": (65, 25, 10),
        "desc": "Sofre dano de fogo solar a cada turno",
    },
}

def _retrato_sprite(frame, tamanho):
    """Recorta o personagem e amplia bem para o retrato (sprites 100x100 tem personagem pequeno)."""
    try:
        rect = frame.get_bounding_rect(min_alpha=5)
        if rect.width < 4 or rect.height < 4:
            return pygame.transform.scale(frame, (tamanho, tamanho))
        pad = max(6, max(rect.width, rect.height) // 3)
        x = max(0, rect.x - pad)
        y = max(0, rect.y - pad)
        w = min(frame.get_width() - x, rect.width + pad * 2)
        h = min(frame.get_height() - y, rect.height + pad * 2)
        cortado = frame.subsurface(pygame.Rect(x, y, w, h)).copy()
        escala = max(tamanho / max(1, cortado.get_width()), tamanho / max(1, cortado.get_height()))
        nw = max(1, int(cortado.get_width() * escala))
        nh = max(1, int(cortado.get_height() * escala))
        scaled = pygame.transform.scale(cortado, (nw, nh))
        out = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        out.blit(scaled, ((tamanho - nw) // 2, (tamanho - nh) // 2))
        return out
    except Exception:
        return pygame.transform.scale(frame, (tamanho, tamanho))

def desenhar_painel_medieval(surface, rect, preenchimento=None, borda=None, espessura=3, variante="pedra", ativo=False, borda_ouro=False, alpha=255):
    is_ouro = borda_ouro or (borda == COR_OURO) or ativo
    ui_medieval.desenhar_painel_medieval(surface, rect, variante=variante, ativo=ativo or is_ouro, borda_ouro=is_ouro, alpha=alpha)

def desenhar_barra_medieval(surface, rect, valor, maximo=1.0, cor_cheia=None, cor_fundo=None, tipo="hp"):
    if isinstance(maximo, (tuple, list)):
        ui_medieval.desenhar_barra_medieval(surface, rect, valor, 1.0, tipo=tipo)
    else:
        ui_medieval.desenhar_barra_medieval(surface, rect, valor, maximo, tipo=tipo)


class CameraCombateRig:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.tilt = 0.0

        self.alvo_x = 0.0
        self.alvo_y = 0.0
        self.alvo_zoom = 1.0
        self.alvo_tilt = 0.0

        self.shake_timer = 0.0
        self.shake_forca = 0

    def definir_pose(self, x, y, zoom=1.0, tilt=0.0):
        self.alvo_x = x
        self.alvo_y = y
        self.alvo_zoom = zoom
        self.alvo_tilt = tilt

    def tremer(self, duracao=0.2, forca=12):
        self.shake_timer = duracao
        self.shake_forca = forca

    def update(self, dt):
        vel = 7.5 * dt
        self.x += (self.alvo_x - self.x) * vel
        self.y += (self.alvo_y - self.y) * vel
        self.zoom += (self.alvo_zoom - self.zoom) * vel
        self.tilt += (self.alvo_tilt - self.tilt) * vel

        if self.shake_timer > 0:
            self.shake_timer -= dt

    def transformar_ponto(self, px, py):
        cx, cy = LARGURA_TELA // 2, ALTURA_TELA // 2
        dx = (px - cx - self.x) * self.zoom
        dy = (py - cy - self.y) * self.zoom

        rad = math.radians(self.tilt)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

        sx = random.randint(-self.shake_forca, self.shake_forca) if self.shake_timer > 0 else 0
        sy = random.randint(-self.shake_forca, self.shake_forca) if self.shake_timer > 0 else 0

        return int(cx + rx + sx), int(cy + ry + sy)

    def projetar(self, x, y, z):
        px, py, _ = projetar_ponto_25d(x, y, z, cam_x=self.x, cam_y=self.y)
        return int(px), int(py)


def desenhar_chao_combate_simples(surface, sala_idx=0):
    """
    Desenha um chão medieval simples, elegante e perfeitamente ancorado na arena de combate.
    Elimina grades poligonais artificiais e proporciona uma plataforma gótica natural
    com lajes de pedra escura (dungeon/castelo) ou terra e musgo suave (florestas/pântano).
    """
    w, h = surface.get_size()
    y_inicio = 210
    altura_chao = h - y_inicio

    surf_chao = pygame.Surface((w, altura_chao), pygame.SRCALPHA)
    e_floresta = sala_idx in (1, 4, 5)

    # Cores orgânicas medievais
    cor_base_topo = (16, 14, 20) if not e_floresta else (18, 16, 14)
    cor_base_meio = (22, 18, 28) if not e_floresta else (24, 20, 16)
    cor_base_fim  = (14, 11, 18) if not e_floresta else (15, 12, 10)
    cor_junta     = (10, 8, 14)  if not e_floresta else (11, 9, 8)
    cor_brilho    = (36, 30, 44) if not e_floresta else (34, 30, 22)

    # Gradiente suave com transição gradual (fade-in) nos primeiros 32px
    for y_rel in range(altura_chao):
        prog = y_rel / float(altura_chao)
        alpha = int(min(225, y_rel * 7.0)) if y_rel < 32 else 225

        if prog < 0.5:
            f = prog / 0.5
            r = int(cor_base_topo[0] + (cor_base_meio[0] - cor_base_topo[0]) * f)
            g = int(cor_base_topo[1] + (cor_base_meio[1] - cor_base_topo[1]) * f)
            b = int(cor_base_topo[2] + (cor_base_meio[2] - cor_base_topo[2]) * f)
        else:
            f = (prog - 0.5) / 0.5
            r = int(cor_base_meio[0] + (cor_base_fim[0] - cor_base_meio[0]) * f)
            g = int(cor_base_meio[1] + (cor_base_fim[1] - cor_base_meio[1]) * f)
            b = int(cor_base_meio[2] + (cor_base_fim[2] - cor_base_meio[2]) * f)

        pygame.draw.line(surf_chao, (r, g, b, alpha), (0, y_rel), (w, y_rel))

    # Lajes de pedra horizontais em perspectiva clássica de 2.5D RPG
    faixas_y = [24, 56, 96, 148, 210, 280]
    for idx_f, fy in enumerate(faixas_y):
        if fy < altura_chao:
            alpha_l = min(120, int(35 + idx_f * 14))
            pygame.draw.line(surf_chao, (*cor_junta, alpha_l), (0, fy), (w, fy), 2)
            if fy + 2 < altura_chao:
                pygame.draw.line(surf_chao, (*cor_brilho, int(alpha_l * 0.55)), (0, fy + 2), (w, fy + 2), 1)

            # Juntas verticais alternadas entre os blocos de pedra
            larg_bloco = 110 + idx_f * 36
            deslocamento = (idx_f * 67) % larg_bloco
            alt_junta = faixas_y[idx_f + 1] - fy if idx_f + 1 < len(faixas_y) else altura_chao - fy
            for bx in range(deslocamento, w, larg_bloco):
                pygame.draw.line(surf_chao, (*cor_junta, int(alpha_l * 0.45)), (bx, fy), (bx, min(altura_chao, fy + alt_junta)), 1)

    # Detalhes sutis de cascalho/musgo medieval
    random.seed(sala_idx * 137 + 42)
    for _ in range(30):
        rx = random.randint(20, w - 20)
        ry_rel = random.randint(35, altura_chao - 15)
        tam = random.randint(2, 4)
        c_det = cor_brilho if not e_floresta else (22, 38, 20)
        pygame.draw.rect(surf_chao, (*c_det, 85), (rx, ry_rel, tam, max(1, tam // 2)))

    surface.blit(surf_chao, (0, y_inicio))


# ==============================================================================
# 4. COMBATE COMPLETO COM OPÇÃO DE ATAQUE OU ITENS (ESTILO EXPEDITION 33)
# ==============================================================================
class CombateExpedition33:
    def __init__(self, jogador_mapa, inimigo_ref, vantagem="NEUTRO", sala_idx=0, alvos_disponiveis=None, modo_boss_rush=False, sala_atual=None):
        self.modo_boss_rush = modo_boss_rush
        self.sala_atual = dados_combatentes.normalizar_indice_sala(sala_idx if sala_atual is None else sala_atual)
        self.sala_idx = self.sala_atual
        self.alvos_disponiveis = [a for a in (alvos_disponiveis or [inimigo_ref]) if getattr(a, "vivo", True)]
        if inimigo_ref not in self.alvos_disponiveis:
            self.alvos_disponiveis.insert(0, inimigo_ref)
        self.alvo_index = self.alvos_disponiveis.index(inimigo_ref)
        self.turnos_inimigo_decorridos = 0
        self.esqueleto_invocado = False
        self.alvo_esqueleto = False
        self.cam = CameraCombate25D(largura_tela=LARGURA_TELA, altura_tela=ALTURA_TELA)
        self.cenario_25d = CenarioCombate25D(largura=LARGURA_TELA, altura=ALTURA_TELA, sala_idx=self.sala_idx, sala_atual=self.sala_atual)
        self.bioma_combate = self.cenario_25d.bioma
        self.jogador_mapa = jogador_mapa
        self.inimigo_ref = inimigo_ref

        self.jogador_hp = jogador_mapa.hp
        self.jogador_max_hp = jogador_mapa.max_hp

        self.inimigo_nome = inimigo_ref.nome
        self.inimigo_hp = inimigo_ref.hp
        self.inimigo_max_hp = max(1, getattr(inimigo_ref, "max_hp", inimigo_ref.hp))
        self.inimigo_cor = inimigo_ref.cor
        self.is_boss = inimigo_ref.is_boss
        self.num_combos_inimigo = inimigo_ref.num_combos

        self.jogador_ap = CONFIG["jogador_ap_inicial"] if vantagem != "JOGADOR" else CONFIG["jogador_ap_inicial"] + 2
        self.max_ap = CONFIG["jogador_max_ap"]

        self.progresso = getattr(jogador_mapa, "progresso_ref", None)
        # Inventário de Itens do Jogador (+1 poção e +1 cristal de éter por nível)
        if self.progresso:
            self.qtd_pocao = self.progresso.total_pocoes_cura()
            self.qtd_cristal_ap = self.progresso.total_cristais_eter()
        else:
            self.qtd_pocao = CONFIG["pocoes_cura_inicial"]
            self.qtd_cristal_ap = CONFIG["cristais_ap_inicial"]
        if self.progresso:
            for alvo in self.alvos_disponiveis:
                base = getattr(alvo, "_hp_base", getattr(alvo, "max_hp", alvo.hp))
                hp_escalado = self.progresso.escalar_hp_inimigo(base)
                if hp_escalado > alvo.max_hp:
                    diff = hp_escalado - alvo.max_hp
                    alvo.max_hp = hp_escalado
                    alvo.hp = max(1, alvo.hp + diff)
            self.inimigo_hp = inimigo_ref.hp
            self.inimigo_max_hp = max(1, getattr(inimigo_ref, "max_hp", inimigo_ref.hp))

        # Nas batalhas de chefe, o chefe SEMPRE ataca primeiro mesmo que o jogador tenha desferido golpe preventivo
        if self.is_boss:
            audio.tocar_musica("boss_theme")
            self.banner_msg = "O CHEFE ATACA PRIMEIRO! DEFENDA-SE!"
            self.banner_cor = (255, 75, 75)
            self.jogador_ap = CONFIG["jogador_ap_inicial"]
        elif vantagem == "JOGADOR":
            audio.tocar_musica("battle_theme")
            self.banner_msg = "ATAQUE PREVENTIVO! (+2 AP & Turno Duplo)"
            self.banner_cor = (80, 250, 195)
        elif vantagem == "INIMIGO":
            audio.tocar_musica("battle_theme")
            self.banner_msg = "EMBOSCADA! Defenda-se imediatamente!"
            self.banner_cor = (255, 85, 85)
        else:
            audio.tocar_musica("battle_theme")
            self.banner_msg = dados_combatentes.obter_titulo_arena(self.sala_atual, is_boss=self.is_boss).upper()
            self.banner_cor = (220, 225, 240)

        # Menus principais do Turno do Jogador: "PRINCIPAL", "ATAQUES", "ITENS"
        self.menu_categoria = "PRINCIPAL"
        self.opcao_principal = 0  # 0: Atacar, 1: Usar Item, 2: Fugir
        self.opcao_ataque = 0
        self.opcao_item = 0
        self.fugiu = False
        self.rects_botoes_menu = []

        bonus_dano = self.progresso.bonus_dano() if self.progresso else 0
        mult_poder = self.progresso.multiplicador_poder() if self.progresso else 1.0

        self.acoes_ataque = [
            {"nome": "Assalto Rápido", "custo": 0, "ganho_ap": 1, "dano": int((CONFIG["habilidade_assalto_dano"] + bonus_dano) * mult_poder), "golpes": 1, "debuff": "SANGRANDO", "badge": "+1 AP • SANGUE", "desc": "Golpe veloz (+1 AP). Aplica Sangria (+25% de dano sofrido por 2 turnos).", "anim": "attack", "aoe": False},
            {"nome": "Corte Lumina", "custo": 2, "ganho_ap": 0, "dano": int((CONFIG["habilidade_corte_dano"] + bonus_dano) * mult_poder), "golpes": 2, "debuff": "QUEIMADURA", "badge": "FOGO (DoT)", "desc": "Lâmina solar (2x). Inflige Queimadura periódica (DoT solar por 2 turnos).", "anim": "attack2", "aoe": False},
            {"nome": "Dança do Éter", "custo": 6, "ganho_ap": 0, "dano": int((CONFIG["habilidade_danca_dano"] + bonus_dano * 2) * mult_poder), "golpes": 3, "debuff": "VULNERAVEL", "badge": "FENDA (+35%)", "desc": "Combo cósmico (3x AoE). Fenda Temporal (+35% dano sofrido). Atinge TODOS os inimigos!", "anim": "attack3", "aoe": True},
            {"nome": "Lâmina Tóxica", "custo": 1, "ganho_ap": 0, "dano": int((int(CONFIG["habilidade_assalto_dano"] * 1.15) + bonus_dano) * mult_poder), "golpes": 1, "debuff": "VENENO", "badge": "VENENO", "desc": "Golpe envenenado. Causa dano tóxico a cada turno do alvo (3 turnos).", "anim": "attack", "aoe": False},
            {"nome": "Foco Absoluto", "custo": 0, "ganho_ap": 2, "dano": 0, "golpes": 0, "debuff": None, "badge": "+2 AP • PURIF", "desc": "Postura tática. Gera +2 AP e purifica 1 debuff (ou intimida o alvo com Fraqueza -30%).", "anim": "magic", "aoe": False},
        ]

        # Debuffs de combate
        self.debuffs_jogador = []
        self.debuffs_inimigo = getattr(inimigo_ref, "debuffs", [])
        inimigo_ref.debuffs = self.debuffs_inimigo
        for alvo in self.alvos_disponiveis:
            if not hasattr(alvo, "debuffs"):
                alvo.debuffs = []

        self.golpes_restantes_qte = 0
        self.qte_timer = 0.0
        self.qte_duracao = 0.95

        self.combo_inimigo = []
        self.golpe_inimigo_atual = 0
        self.inimigo_timer = 0.0
        self.pausa_tatica_timer = 0.0
        self.tempo_impacto_base = 1.25 if self.is_boss else 1.38
        self.tempo_impacto = self.tempo_impacto_base
        self.retomar_combo_apos_contra = False
        self.dano_contra_atual = 0
        self.contra_golpeou = False
        self.todos_aparados_com_parry = True

        self.janela_parry_ativa = 0.0
        self.janela_desvio_ativa = 0.0
        self.cooldown_reacao = 0.0
        self.reacao_executada_neste_golpe = False

        # Métricas de desempenho para cálculo de Rank S/A/B/C
        self.dano_recebido_combate = 0
        self.qtes_perfeitos = 0
        self.parries_perfeitos = 0
        self.desvios_perfeitos = 0
        self.resultado_rank = None

        self.jog_avanco = 0.0
        self.inim_avanco = 0.0
        self.desvio_offset_x = 0.0
        self.pulo_offset_y = 0.0
        self.pulo_vy = 0.0
        self.pulando = False
        self.pulo_perfeito = False

        self.textos_flutuantes = []
        self.flash_cor = None
        self.flash_alpha = 0
        self.hitstop_timer = 0.0
        self.contra_ataque_timer = 0.0
        self.tempo_combate = 0.0

        # Inicialização 2.5D dos Combatentes Modulares (Perspectiva Tridimensional X, Y, Z)
        # Herói posicionado em primeiro plano à esquerda (projetado em ~300px, 340px)
        self.combatente_jogador = criar_heroi_modular(x=-220.0, y=140.0, z=70.0, progresso=self.progresso)

        # Mapeamento e formação espacial 2.5D de cada inimigo presente (Posições Vermelhas da imagem)
        self.combatentes_inimigos = []
        if len(self.alvos_disponiveis) == 1:
            posicoes_formacao = [
                [180.0, 140.0, 100.0],  # Alvo único / Chefe centralizado na arena
            ]
        else:
            posicoes_formacao = [
                [-24.0, 140.0, 70.0],   # Alvo 0: Vanguarda esquerda (Marca vermelha 1 ~ 460px)
                [197.0, 140.0, 100.0],  # Alvo 1: Centro intermediário (Marca vermelha 2 ~ 630px)
                [450.0, 140.0, 130.0],  # Alvo 2: Flanco direito (Marca vermelha 3 ~ 800px)
                [680.0, 140.0, 160.0],  # Alvo 3: Retaguarda extrema (~900px)
            ]
        for idx_alvo, inim in enumerate(self.alvos_disponiveis):
            pos_3d = posicoes_formacao[idx_alvo % len(posicoes_formacao)]
            sprite_in = (getattr(inim, "anim", None) and getattr(inim.anim, "personagem", None) and inim.anim.personagem.nome) or getattr(inim, "sprite", inim.nome)
            is_b = getattr(inim, "is_boss", False)
            arq = dados_combatentes.inferir_arquetipo_sprite(sprite_in, is_boss=is_b)

            cb_inim = NovoCombatente(
                nome=inim.nome,
                hp_max=getattr(inim, "max_hp", inim.hp),
                ap_max=8 if is_b else 6,
                arquetipo=arq,
                sprite_nome=sprite_in,
                pos_mundo=list(pos_3d),
                is_boss=is_b
            )
            cb_inim.hp_atual = inim.hp
            cb_inim.pos_base = list(pos_3d)
            cb_inim.pos_alvo = list(pos_3d)
            self.combatentes_inimigos.append((inim, cb_inim))

        self.mapa_combatentes = {id(inim): cb for inim, cb in self.combatentes_inimigos}
        self.combatente_inimigo = self.mapa_combatentes.get(id(inimigo_ref), self.combatentes_inimigos[0][1])
        self.combatentes_equipe = [pair for pair in self.combatentes_inimigos if pair[0] is not self.inimigo_ref]

        if self.combatente_jogador.animador and self.combatente_jogador.animador.ativo:
            self.anim_jog = self.combatente_jogador.animador
        else:
            self.anim_jog = Animador(getattr(getattr(jogador_mapa, "anim", None), "personagem", None))

        if self.combatente_inimigo.animador and self.combatente_inimigo.animador.ativo:
            self.anim_inim = self.combatente_inimigo.animador
        else:
            self.anim_inim = Animador(getattr(getattr(inimigo_ref, "anim", None), "personagem", None))

        # Construção da Linha do Tempo Expedition 33 (Turno Individual por Combatente)
        self.timeline = []
        self.indice_proximo_inimigo_turno = 0
        inimigos_vivos = [pair for pair in self.combatentes_inimigos if getattr(pair[0], "vivo", True) and getattr(pair[0], "hp", 0) > 0]

        if self.is_boss or vantagem == "INIMIGO":
            if inimigos_vivos:
                r0, c0 = inimigos_vivos[0]
                self.timeline.append({"tipo": "INIMIGO", "ref": r0, "cb": c0, "nome": r0.nome})
                self.indice_proximo_inimigo_turno = 1 % len(inimigos_vivos)
        elif vantagem == "JOGADOR":
            self.timeline.append({"tipo": "JOGADOR", "ref": self.jogador_mapa, "cb": self.combatente_jogador, "nome": "Viajante"})
            self.timeline.append({"tipo": "JOGADOR", "ref": self.jogador_mapa, "cb": self.combatente_jogador, "nome": "Viajante"})
        else:
            self.timeline.append({"tipo": "JOGADOR", "ref": self.jogador_mapa, "cb": self.combatente_jogador, "nome": "Viajante"})

        self.garantir_tamanho_timeline(min_turnos=6)
        self.golpe_anim_iniciado = False
        self.timer_fim = 0.0
        self.fim_concluido = False

        self.estado = ""
        self.iniciar_turno()

    def adicionar_texto_flutuante(self, texto, x, y, cor):
        cur_y = float(y)
        # Limita para evitar sobrecarga e poluição visual
        if len(self.textos_flutuantes) >= 7:
            self.textos_flutuantes.pop(0)
        # Empilhamento vertical estrito sem sobreposição de textos flutuantes
        colidiu = True
        tentativas = 0
        while colidiu and tentativas < 12:
            colidiu = False
            for tf in self.textos_flutuantes:
                if abs(tf["x"] - float(x)) < 140 and abs(tf["y"] - cur_y) < 24:
                    cur_y = tf["y"] - 24.0
                    colidiu = True
                    tentativas += 1
                    break
        self.textos_flutuantes.append({"txt": texto, "x": float(x), "y": cur_y, "cor": cor, "tempo": 1.15})

    def disparar_flash(self, cor, alpha=140):
        self.flash_cor = cor
        self.flash_alpha = alpha

    def aplicar_debuff(self, alvo, tipo, turnos=2, valor=0):
        """Aplica ou renova um debuff no jogador ('JOGADOR') ou no inimigo ('INIMIGO')."""
        lista = self.debuffs_jogador if alvo == "JOGADOR" else self.debuffs_inimigo
        info = DEBUFFS_INFO.get(tipo, {"nome": tipo, "icone": "⚠", "cor": (255, 200, 80), "cor_bg": (40, 30, 20)})
        existente = next((d for d in lista if d.get("tipo") == tipo), None)
        if existente:
            existente["turnos"] = max(existente.get("turnos", 0), turnos)
            if valor > 0:
                existente["valor"] = max(existente.get("valor", 0), valor)
            msg = f"{info['icone']} {info['nome']} RENOVADO ({existente['turnos']}t)!"
        else:
            novo_d = {
                "tipo": tipo,
                "nome": info["nome"],
                "icone": info["icone"],
                "cor": info["cor"],
                "cor_bg": info["cor_bg"],
                "turnos": turnos,
                "valor": valor
            }
            lista.append(novo_d)
            msg = f"{info['icone']} DEBUFF: {info['nome']} ({turnos}t)!"

        pos_x = 220 if alvo == "JOGADOR" else 620
        pos_y = 200 if alvo == "JOGADOR" else 150
        self.adicionar_texto_flutuante(msg, pos_x, pos_y, info["cor"])
        self.disparar_flash(info["cor"], 75)

    def desenhar_aura_debuffs(self, surface, rect, debuffs, tempo):
        """Renderiza auras místicas e partículas dinâmicas nos combatentes sob efeito de debuffs."""
        if not debuffs:
            return
        cx, cy = rect.centerx, rect.centery
        for d in debuffs:
            tipo = d.get("tipo")
            if tipo == "VENENO":
                # Vapores tóxicos esmeralda subindo em espiral
                for i in range(4):
                    fase = (tempo * 2.4 + i * 0.28) % 1.0
                    bx = cx - 18 + i * 12 + int(math.sin(tempo * 4.0 + i * 1.5) * 6)
                    by = rect.bottom - int(fase * (rect.height + 15))
                    raio = max(2, int(4 * (1.0 - fase * 0.5)))
                    alpha = int(190 * (1.0 - fase))
                    surf_b = pygame.Surface((raio * 2 + 2, raio * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf_b, (90, 225, 75, alpha), (raio + 1, raio + 1), raio)
                    surface.blit(surf_b, (bx - raio, by - raio))
            elif tipo == "QUEIMADURA":
                # Fagulhas e brasas ardentes subindo
                for i in range(5):
                    fase = (tempo * 3.5 + i * 0.22) % 1.0
                    fx = cx - 20 + i * 10 + int(math.sin(tempo * 6.0 + i * 2) * 8)
                    fy = rect.bottom - int(fase * (rect.height + 20))
                    tam = max(2, int(4 * (1.0 - fase)))
                    cor_f = (255, int(130 + 80 * (1.0 - fase)), 30, int(210 * (1.0 - fase)))
                    surf_f = pygame.Surface((tam * 2 + 2, tam * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf_f, cor_f, (tam + 1, tam + 1), tam)
                    surface.blit(surf_f, (fx - tam, fy - tam))
            elif tipo == "SANGRANDO":
                # Gotas de sangue carmesim pingando
                for i in range(3):
                    fase = (tempo * 2.6 + i * 0.35) % 1.0
                    sx = cx - 14 + i * 14
                    sy = rect.top + int(fase * (rect.height + 10))
                    tam = max(2, int(3.5 * (1.0 - fase * 0.3)))
                    surf_s = pygame.Surface((tam * 2 + 2, tam * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf_s, (225, 40, 40, int(200 * (1.0 - fase * 0.5))), (tam + 1, tam + 1), tam)
                    surface.blit(surf_s, (sx - tam, sy - tam))
            elif tipo == "VULNERAVEL":
                # Anel de fenda temporal cósmica pulsando
                pulso = 0.5 + 0.5 * math.sin(tempo * 5.0)
                rw = int(rect.width * (1.1 + 0.12 * pulso))
                rh = int(rect.height * (1.05 + 0.10 * pulso))
                surf_v = pygame.Surface((rw, rh), pygame.SRCALPHA)
                pygame.draw.ellipse(surf_v, (90, 230, 255, int(50 + 45 * pulso)), surf_v.get_rect(), 2)
                surface.blit(surf_v, (cx - rw // 2, cy - rh // 2))
            elif tipo == "FRAQUEZA":
                # Bruma arroxeada descendente
                pulso = 0.5 + 0.5 * math.sin(tempo * 3.5)
                rw = int(rect.width * 1.05)
                rh = int(rect.height * 1.05)
                surf_w = pygame.Surface((rw, rh), pygame.SRCALPHA)
                pygame.draw.rect(surf_w, (140, 90, 220, int(35 + 30 * pulso)), surf_w.get_rect(), border_radius=8)
                surface.blit(surf_w, (cx - rw // 2, cy - rh // 2))
            elif tipo == "LENTIDAO":
                # Cristais de geada e lentidão orbitando lentamente
                pulso = 0.5 + 0.5 * math.sin(tempo * 2.8)
                for ang in [0, 90, 180, 270]:
                    rad = math.radians(ang + tempo * 45.0)
                    dist = 28 + 6 * pulso
                    px = int(cx + math.cos(rad) * dist)
                    py = int(cy + math.sin(rad) * dist * 0.7)
                    pygame.draw.circle(surface, (180, 215, 255), (px, py), 3)

    def processar_inicio_turno(self, combatente):
        """Processa efeitos periódicos (DoT, AP, debuffs) e decrementa duração no início de cada turno."""
        tipo_combatente = combatente["tipo"] if isinstance(combatente, dict) else combatente
        if tipo_combatente == "JOGADOR":
            for d in self.debuffs_jogador[:]:
                tipo = d["tipo"]
                if tipo == "VENENO":
                    dano_dot = d.get("valor", 4)
                    if any(deb["tipo"] == "VULNERAVEL" for deb in self.debuffs_jogador):
                        dano_dot = int(dano_dot * 1.35)
                    if any(deb["tipo"] == "SANGRANDO" for deb in self.debuffs_jogador):
                        dano_dot = int(dano_dot * 1.30)
                    dano_dot = max(1, dano_dot)
                    self.dano_recebido_combate += dano_dot
                    self.jogador_hp = max(0, self.jogador_hp - dano_dot)
                    self.jogador_mapa.hp = self.jogador_hp
                    audio.tocar_sfx("freeze", 0.65)
                    self.cam.tremer(0.12, 6)
                    self.disparar_flash((90, 225, 75), 70)
                    self.adicionar_texto_flutuante(f"[TOX] VENENO -{dano_dot} HP!", 220, 230, (90, 225, 75))
                    if self.jogador_hp <= 0:
                        self.iniciar_fim()
                        return
                elif tipo == "QUEIMADURA":
                    dano_dot = d.get("valor", 5)
                    if any(deb["tipo"] == "VULNERAVEL" for deb in self.debuffs_jogador):
                        dano_dot = int(dano_dot * 1.35)
                    if any(deb["tipo"] == "SANGRANDO" for deb in self.debuffs_jogador):
                        dano_dot = int(dano_dot * 1.30)
                    dano_dot = max(1, dano_dot)
                    self.dano_recebido_combate += dano_dot
                    self.jogador_hp = max(0, self.jogador_hp - dano_dot)
                    self.jogador_mapa.hp = self.jogador_hp
                    audio.tocar_sfx("burn", 0.75)
                    self.cam.tremer(0.12, 6)
                    self.disparar_flash((255, 140, 40), 70)
                    self.adicionar_texto_flutuante(f"[FOGO] QUEIMADURA -{dano_dot} HP!", 220, 230, (255, 175, 45))
                    if self.jogador_hp <= 0:
                        self.iniciar_fim()
                        return
                elif tipo == "LENTIDAO":
                    if self.jogador_ap > 0:
                        self.jogador_ap = max(0, self.jogador_ap - 1)
                        self.adicionar_texto_flutuante("[LENTO] LENTIDÃO: -1 AP!", 220, 255, (210, 180, 255))
                elif tipo == "SANGRANDO":
                    dano_dot = max(1, d.get("valor", 2))
                    self.dano_recebido_combate += dano_dot
                    self.jogador_hp = max(0, self.jogador_hp - dano_dot)
                    self.jogador_mapa.hp = self.jogador_hp
                    audio.tocar_sfx("hit_player", 0.55)
                    self.adicionar_texto_flutuante(f"[SANGUE] SANGRIA -{dano_dot} HP!", 220, 210, (255, 80, 80))
                    if self.jogador_hp <= 0:
                        self.iniciar_fim()
                        return

                t_rest = max(0, d.get("turnos", d.get("duracao", 1)) - 1)
                d["turnos"] = t_rest
                if t_rest <= 0:
                    if d in self.debuffs_jogador:
                        self.debuffs_jogador.remove(d)
                    self.adicionar_texto_flutuante(f"{d.get('nome', 'Efeito')} dissipado", 220, 205, (170, 200, 210))

        elif tipo_combatente == "INIMIGO":
            ref_at = (combatente.get("ref") if isinstance(combatente, dict) else None) or self.inimigo_ref
            cb_at = (combatente.get("cb") if isinstance(combatente, dict) else None) or self.mapa_combatentes.get(id(ref_at), self.combatente_inimigo)
            if not getattr(ref_at, "vivo", True) or getattr(ref_at, "hp", 0) <= 0:
                return
            debs_at = getattr(ref_at, "debuffs", [])
            pt_txt = (620, 175)
            if cb_at and hasattr(cb_at, "pos_mundo"):
                pt_proj = self.cam.projetar(cb_at.pos_mundo[0], cb_at.pos_mundo[1] - 75, cb_at.pos_mundo[2])
                pt_txt = (pt_proj[0], pt_proj[1])

            for d in debs_at[:]:
                tipo = d.get("tipo", "")
                dano_dot = 0
                if tipo == "QUEIMADURA":
                    dano_dot = d.get("valor", 6)
                    if any(deb.get("tipo") == "VULNERAVEL" for deb in debs_at):
                        dano_dot = int(dano_dot * 1.35)
                    if any(deb.get("tipo") == "SANGRANDO" for deb in debs_at):
                        dano_dot = int(dano_dot * 1.25)
                    dano_dot = max(1, dano_dot)
                    audio.tocar_sfx("burn", 0.75)
                    self.cam.tremer(0.12, 6)
                    self.disparar_flash((255, 140, 40), 70)
                    self.adicionar_texto_flutuante(f"[FOGO] QUEIMADURA -{dano_dot} HP!", pt_txt[0], pt_txt[1], (255, 175, 45))
                elif tipo == "VENENO":
                    dano_dot = d.get("valor", 5)
                    if any(deb.get("tipo") == "VULNERAVEL" for deb in debs_at):
                        dano_dot = int(dano_dot * 1.35)
                    if any(deb.get("tipo") == "SANGRANDO" for deb in debs_at):
                        dano_dot = int(dano_dot * 1.25)
                    dano_dot = max(1, dano_dot)
                    audio.tocar_sfx("freeze", 0.65)
                    self.cam.tremer(0.10, 5)
                    self.disparar_flash((90, 225, 75), 70)
                    self.adicionar_texto_flutuante(f"[TOX] VENENO -{dano_dot} HP!", pt_txt[0], pt_txt[1] + 18, (90, 225, 75))
                elif tipo == "SANGRANDO":
                    dano_dot = max(1, d.get("valor", 3))
                    self.adicionar_texto_flutuante(f"[SANGUE] HEMORRAGIA -{dano_dot} HP!", pt_txt[0], pt_txt[1] - 18, (255, 80, 80))

                if dano_dot > 0:
                    ref_at.hp = max(0, int(getattr(ref_at, "hp", 0)) - dano_dot)
                    if cb_at and hasattr(cb_at, "hp_atual"):
                        cb_at.hp_atual = ref_at.hp
                    if ref_at is self.inimigo_ref:
                        self.inimigo_hp = ref_at.hp
                    if ref_at.hp <= 0:
                        ref_at.vivo = False
                        if cb_at and getattr(cb_at, "animador", None):
                            cb_at.animador.tocar("death", loop=False, duracao=0.75, forcar=True, retorno=None)
                        vivos_rest = self._inimigos_vivos_lista()
                        if not vivos_rest:
                            self.iniciar_fim()
                        elif ref_at is self.inimigo_ref:
                            self.selecionar_alvo_direto(vivos_rest[0][0])
                        return

                t_rest = max(0, d.get("turnos", d.get("duracao", 1)) - 1)
                d["turnos"] = t_rest
                if t_rest <= 0:
                    if d in debs_at:
                        debs_at.remove(d)
                    self.adicionar_texto_flutuante(f"{d.get('nome', 'Efeito')} expirou", pt_txt[0], pt_txt[1] - 20, (170, 200, 210))

    def _inimigos_vivos_lista(self):
        return [
            pair for pair in getattr(self, "combatentes_inimigos", [])
            if getattr(pair[0], "vivo", True) and getattr(pair[0], "hp", 0) > 0
        ]

    def garantir_tamanho_timeline(self, min_turnos=6):
        """Mantém a timeline de iniciativa com pelo menos min_turnos futuros planejados."""
        inimigos_vivos = self._inimigos_vivos_lista()
        if not inimigos_vivos:
            return
        while len(self.timeline) < min_turnos:
            ultimo_tipo = self.timeline[-1]["tipo"] if self.timeline else "INIMIGO"
            if ultimo_tipo == "INIMIGO":
                self.timeline.append({"tipo": "JOGADOR", "ref": self.jogador_mapa, "cb": self.combatente_jogador, "nome": "Viajante"})
            else:
                idx = self.indice_proximo_inimigo_turno % len(inimigos_vivos)
                r_at, c_at = inimigos_vivos[idx]
                self.timeline.append({"tipo": "INIMIGO", "ref": r_at, "cb": c_at, "nome": r_at.nome})
                self.indice_proximo_inimigo_turno = (self.indice_proximo_inimigo_turno + 1) % len(inimigos_vivos)

    def iniciar_turno(self):
        self.jog_avanco = 0.0
        self.inim_avanco = 0.0
        self.pulando = False
        self.pulo_offset_y = 0.0
        self.desvio_offset_x = 0.0

        # Filtra combatentes mortos da timeline
        self.timeline = [t for t in self.timeline if t["tipo"] == "JOGADOR" or (getattr(t["ref"], "vivo", True) and getattr(t["ref"], "hp", 0) > 0)]
        inimigos_vivos = self._inimigos_vivos_lista()
        if not inimigos_vivos or self.jogador_hp <= 0:
            self.iniciar_fim()
            return

        if not getattr(self.inimigo_ref, "vivo", True) or getattr(self.inimigo_ref, "hp", 0) <= 0:
            self.selecionar_alvo_direto(inimigos_vivos[0][0])

        self.garantir_tamanho_timeline(min_turnos=6)
        atual = self.timeline[0]
        self.processar_inicio_turno(atual)

        inimigos_vivos = self._inimigos_vivos_lista()
        if not inimigos_vivos or self.jogador_hp <= 0:
            self.iniciar_fim()
            return

        if not getattr(self.inimigo_ref, "vivo", True) or getattr(self.inimigo_ref, "hp", 0) <= 0:
            self.selecionar_alvo_direto(inimigos_vivos[0][0])

        if atual["tipo"] == "INIMIGO" and (not getattr(atual["ref"], "vivo", True) or getattr(atual["ref"], "hp", 0) <= 0):
            self.avancar_timeline()
            return

        if atual["tipo"] == "JOGADOR":
            self.estado = "MENU_JOGADOR"
            self.menu_categoria = "PRINCIPAL"
            self.cam.definir_pose(x=-40, y=15, zoom=1.0, tilt=0.0)
            for _, cb in self.combatentes_inimigos:
                cb.pos_alvo = list(cb.pos_base)
                cb.pos_mundo = list(cb.pos_base)
            self.banner_msg = ""
        else:
            self.iniciar_combo_inimigo()

    def avancar_timeline(self):
        self.timeline = [t for t in self.timeline if t["tipo"] == "JOGADOR" or (getattr(t["ref"], "vivo", True) and getattr(t["ref"], "hp", 0) > 0)]
        inimigos_vivos = [pair for pair in getattr(self, "combatentes_inimigos", []) if getattr(pair[0], "vivo", True) and getattr(pair[0], "hp", 0) > 0]
        if not inimigos_vivos or self.jogador_hp <= 0:
            self.iniciar_fim()
            return
        if self.timeline:
            self.timeline.pop(0)
        self.garantir_tamanho_timeline(min_turnos=6)
        self.iniciar_turno()

    def iniciar_qte_jogador(self, acao):
        self.estado = "QTE_JOGADOR"
        self.acao_selecionada = acao
        self.golpes_restantes_qte = acao["golpes"]
        self.qte_timer = 0.0
        self.jog_avanco = 1.0

        is_aoe = acao.get("aoe", False)
        if is_aoe:
            self.cam.definir_pose(x=60, y=-20, zoom=1.18, tilt=0.0)
        else:
            alvo_cb = getattr(self, "combatente_inimigo", None)
            alvo_x = alvo_cb.pos_base[0] if (alvo_cb and hasattr(alvo_cb, "pos_base")) else 160.0
            cam_foco_x = int(alvo_x * 0.42)
            self.cam.definir_pose(x=cam_foco_x, y=-25, zoom=1.35, tilt=3.5)

        tag_atk = ui_medieval.tag_comando("atacar")
        self.banner_msg = f"QTE ATIVO! Pressione {tag_atk} no losango dourado! ({self.golpes_restantes_qte}x)"
        self.banner_cor = (255, 235, 110)

    def resolver_golpe_qte(self, apertou_botao):
        acao = getattr(self, "acao_selecionada", self.acoes_ataque[self.opcao_ataque])
        progresso = self.qte_timer / self.qte_duracao
        perfeito = apertou_botao and (0.74 <= progresso <= 1.05)

        if perfeito:
            self.qtes_perfeitos += 1
            audio.tocar_sfx("timestop", 0.9)
            audio.tocar_sfx("sword_crit", 0.95)
            dano = int(acao["dano"] * 1.45)
            ganho = acao["ganho_ap"] + (1 if acao["ganho_ap"] > 0 else 0)
            self.hitstop_timer = 0.09
            self.cam.tremer(0.20, 14)
            self.disparar_flash((80, 255, 210), 110)
        else:
            audio.tocar_sfx("hit_enemy", 0.85)
            dano = int(acao["dano"] * 0.75)
            ganho = acao["ganho_ap"]
            self.cam.tremer(0.10, 5)

        # Modificadores de Debuffs no dano causado pelo jogador
        mensagens_mod = []
        if any(d["tipo"] == "FRAQUEZA" for d in self.debuffs_jogador):
            dano = int(dano * 0.70)
            mensagens_mod.append(("FRAQUEZA -30%!", (175, 140, 255)))

        debuff_tipo = acao.get("debuff")
        is_aoe = acao.get("aoe", False)

        if is_aoe:
            # Dano em área simultâneo em todos os inimigos vivos
            inimigos_vivos = [pair for pair in getattr(self, "combatentes_inimigos", []) if getattr(pair[0], "vivo", True) and getattr(pair[0], "hp", 0) > 0]
            if not inimigos_vivos and getattr(self.inimigo_ref, "vivo", True):
                inimigos_vivos = [(self.inimigo_ref, self.combatente_inimigo)]

            for idx_alvo, (alvo_ref, alvo_cb) in enumerate(inimigos_vivos):
                dano_alvo = dano
                debs_alvo = getattr(alvo_ref, "debuffs", [])
                if any(d["tipo"] == "VULNERAVEL" for d in debs_alvo):
                    dano_alvo = int(dano_alvo * 1.35)
                if any(d["tipo"] == "SANGRANDO" for d in debs_alvo):
                    dano_alvo = int(dano_alvo * 1.25)
                dano_alvo = max(1, dano_alvo)

                alvo_ref.hp = max(0, alvo_ref.hp - dano_alvo)
                if hasattr(alvo_cb, "hp_atual"):
                    alvo_cb.hp_atual = alvo_ref.hp
                if alvo_ref.hp <= 0:
                    alvo_ref.vivo = False
                    if hasattr(alvo_cb, "animador") and alvo_cb.animador:
                        alvo_cb.animador.tocar("death", loop=False, duracao=0.75, forcar=True, retorno=None)

                pos_tx = 450 + idx_alvo * 150
                pos_ty = 160 + (idx_alvo % 2) * 35
                if hasattr(alvo_cb, "pos_mundo"):
                    pt = self.cam.projetar(alvo_cb.pos_mundo[0], alvo_cb.pos_mundo[1] - 70, alvo_cb.pos_mundo[2])
                    pos_tx, pos_ty = pt[0], pt[1]

                if perfeito:
                    self.adicionar_texto_flutuante(f"CRÍTICO AOE! -{dano_alvo}", pos_tx, pos_ty, (90, 240, 255))
                else:
                    self.adicionar_texto_flutuante(f"AOE -{dano_alvo}", pos_tx, pos_ty, (180, 220, 255))

                if debuff_tipo == "VULNERAVEL":
                    if not any(d["tipo"] == "VULNERAVEL" for d in debs_alvo):
                        debs_alvo.append({"tipo": "VULNERAVEL", "nome": "Fenda Temporal", "turnos": 2 if perfeito else 1, "origem": "JOGADOR"})

                if hasattr(alvo_cb, "animador") and alvo_cb.animador:
                    alvo_cb.animador.tocar("hurt", loop=False, duracao=0.35, forcar=True)

            self.inimigo_hp = max(0, self.inimigo_ref.hp)
            if self.inimigo_hp <= 0:
                self.inimigo_ref.vivo = False
        else:
            # Dano unitário no alvo focado
            if any(d["tipo"] == "VULNERAVEL" for d in self.debuffs_inimigo):
                dano = int(dano * 1.35)
                mensagens_mod.append(("VULNERAVEL +35%!", (90, 230, 255)))
            if any(d["tipo"] == "SANGRANDO" for d in self.debuffs_inimigo):
                dano = int(dano * 1.25)
                mensagens_mod.append(("SANGRIA +25%!", (255, 80, 80)))
            dano = max(1, dano)

            if perfeito:
                self.adicionar_texto_flutuante(f"PERFEITO! -{dano}", 620, 160, (80, 255, 200))
            else:
                self.adicionar_texto_flutuante(f"NORMAL -{dano}", 620, 180, (200, 200, 215))

            for msg_txt, cor_txt in mensagens_mod:
                self.adicionar_texto_flutuante(msg_txt, 620, 135, cor_txt)

            if debuff_tipo == "QUEIMADURA":
                self.aplicar_debuff("INIMIGO", "QUEIMADURA", turnos=2, valor=6 if perfeito else 4)
            elif debuff_tipo == "VULNERAVEL":
                self.aplicar_debuff("INIMIGO", "VULNERAVEL", turnos=2 if perfeito else 1)
            elif debuff_tipo == "VENENO":
                self.aplicar_debuff("INIMIGO", "VENENO", turnos=3 if perfeito else 2, valor=5 if perfeito else 4)
            elif debuff_tipo == "SANGRANDO":
                self.aplicar_debuff("INIMIGO", "SANGRANDO", turnos=2 if perfeito else 1)

            self.inimigo_hp = max(0, self.inimigo_hp - dano)
            self.inimigo_ref.hp = self.inimigo_hp
            if hasattr(self.combatente_inimigo, "hp_atual"):
                self.combatente_inimigo.hp_atual = self.inimigo_hp
            if self.inimigo_hp <= 0:
                self.inimigo_ref.vivo = False
                if self.anim_inim:
                    self.anim_inim.tocar("death", loop=False, duracao=0.75, forcar=True, retorno=None)
            else:
                self.anim_inim.tocar("hurt", loop=False, duracao=0.35, forcar=True)

        self.jogador_ap = min(self.max_ap, self.jogador_ap + ganho)
        # Variar animações de ataque do herói para não repetir sempre a mesma
        anims_combo = ["attack", "attack2", "attack3"]
        anim_base = acao.get("anim", "attack")
        if anim_base in anims_combo:
            idx_anim = (acao["golpes"] - self.golpes_restantes_qte) % len(anims_combo)
            anim_usar = anims_combo[idx_anim]
        else:
            anim_usar = anim_base
        self.anim_jog.tocar(anim_usar, loop=False, duracao=0.32, forcar=True)

        self.golpes_restantes_qte -= 1
        inimigos_restantes = self._inimigos_vivos_lista()
        if inimigos_restantes and (not getattr(self.inimigo_ref, "vivo", True) or getattr(self.inimigo_ref, "hp", 0) <= 0):
            self.selecionar_alvo_direto(inimigos_restantes[0][0])

        if self.golpes_restantes_qte > 0 and inimigos_restantes:
            self.qte_timer = 0.0
            inclinacao = -4.0 if self.golpes_restantes_qte % 2 == 0 else 4.0
            is_aoe = acao.get("aoe", False)
            if is_aoe:
                self.cam.definir_pose(x=60, y=-20, zoom=1.18, tilt=inclinacao)
            else:
                alvo_cb = getattr(self, "combatente_inimigo", None)
                alvo_x = alvo_cb.pos_base[0] if (alvo_cb and hasattr(alvo_cb, "pos_base")) else 160.0
                cam_foco_x = int(alvo_x * 0.42)
                self.cam.definir_pose(x=cam_foco_x, y=-25, zoom=1.35, tilt=inclinacao)
        else:
            self.avancar_timeline()

    def iniciar_combo_inimigo(self):
        self.estado = "TURNO_INIMIGO"
        atual = self.timeline[0]
        ref_at = atual["ref"]
        cb_at = atual["cb"]

        if not getattr(ref_at, "vivo", True) or getattr(ref_at, "hp", 0) <= 0:
            self.avancar_timeline()
            return

        self.atacante_atual_ref = ref_at
        self.atacante_atual_cb = cb_at
        self.atacante_atual_is_boss = getattr(ref_at, "is_boss", False)

        # Todos os outros combatentes inimigos permanecem em suas posições base
        for ali, cb in getattr(self, "combatentes_inimigos", []):
            if cb is not cb_at:
                cb.pos_alvo = list(cb.pos_base)

        # O combatente ativo avança para a frente do herói em perspectiva 3D
        cb_at.pos_alvo = [-170.0, 140.0, -20.0]

        # Determina o golpe específico deste combatente de acordo com seu arquétipo
        pool_usar = []
        if getattr(cb_at, "move_pool", None):
            for m in cb_at.move_pool:
                pool_usar.append(m.get("id", "").upper())
        if not pool_usar:
            if self.atacante_atual_is_boss:
                pool_usar = list(POOL_GOLPES_BOSS)
            elif getattr(ref_at, "num_combos", 2) >= 3:
                pool_usar = list(POOL_GOLPES_MEDIOS)
            else:
                pool_usar = list(POOL_GOLPES_COMUNS)

        golpe = random.choice(pool_usar)
        total_golpes = 2 if (self.atacante_atual_is_boss or golpe == "COMBO_DUPLO") else 1
        self.combo_inimigo = [golpe]
        if total_golpes == 2 and len(pool_usar) > 1:
            g2 = random.choice(pool_usar)
            self.combo_inimigo.append(g2)

        self.combo_atacantes = [{
            "ref": ref_at,
            "cb": cb_at,
            "tipo": g,
            "is_boss": self.atacante_atual_is_boss
        } for g in self.combo_inimigo]

        # Se sofrer LENTIDÃO e tiver mais de 1 golpe, perde 1 golpe do combo
        deb_at = getattr(ref_at, "debuffs", [])
        if any(d["tipo"] == "LENTIDAO" for d in deb_at) and len(self.combo_inimigo) > 1:
            self.combo_inimigo.pop()
            self.combo_atacantes.pop()
            self.adicionar_texto_flutuante("LENTIDÃO CANCELOU 1 GOLPE DO COMBO!", 620, 130, (210, 180, 255))

        self.golpe_inimigo_atual = 0
        self.todos_aparados_com_parry = True
        self.preparar_golpe_inimigo()

    def todos_inimigos_mortos(self):
        """Verifica confiavelmente se todos os inimigos do confronto foram eliminados."""
        for par in getattr(self, "combatentes_inimigos", []):
            inim_ent = par[0]
            if getattr(inim_ent, "vivo", True) and getattr(inim_ent, "hp", 0) > 0:
                return False
        for alvo in getattr(self, "alvos_disponiveis", []):
            if getattr(alvo, "vivo", True) and getattr(alvo, "hp", 0) > 0:
                return False
        if getattr(self.inimigo_ref, "vivo", True) and getattr(self.inimigo_ref, "hp", 0) > 0:
            return False
        return True

    def iniciar_fim(self):
        if self.estado in ("VITORIA", "FIM_VITORIA", "FIM_DERROTA", "FIM_FUGA"):
            return

        # Guarda contra término prematuro em combates de grupo: se ainda há inimigos vivos
        # (exceto lacaios invocados quando um Chefe já caiu), troca o foco e continua o combate.
        if self.jogador_hp > 0:
            vivos_rest = self._inimigos_vivos_lista()
            havia_boss = any(getattr(p[0], "is_boss", False) for p in getattr(self, "combatentes_inimigos", []))
            boss_vivo = any(getattr(p, "is_boss", False) for p, _ in vivos_rest)
            vivos_nao_lacaios = [p for p, _ in vivos_rest if not (havia_boss and not boss_vivo and getattr(p, "esqueleto_invocado", False))]
            if vivos_nao_lacaios:
                self.selecionar_alvo_direto(vivos_nao_lacaios[0])
                self.avancar_timeline()
                return

        # Zera imediatamente travas temporais e offsets de reação
        self.hitstop_timer = 0.0
        self.pausa_tatica_timer = 0.0
        self.janela_parry_ativa = 0.0
        self.janela_desvio_ativa = 0.0
        self.pulando = False
        self.pulo_offset_y = 0.0
        self.pulo_vy = 0.0
        self.jog_avanco = 0.0
        self.desvio_offset_x = 0.0

        # A vitória é definida pelo fato do herói estar vivo (jogador_hp > 0)
        if self.jogador_hp > 0:
            self.estado = "VITORIA"
            self.inimigo_hp = 0
            if self.inimigo_ref:
                self.inimigo_ref.hp = 0
                self.inimigo_ref.vivo = False
            for pair in getattr(self, "combatentes_inimigos", []):
                if hasattr(pair[0], "hp"):
                    pair[0].hp = 0
                    pair[0].vivo = False
            for alvo in getattr(self, "alvos_disponiveis", []):
                alvo.hp = 0
                alvo.vivo = False
            audio.tocar_sfx("death_enemy", 0.95)

            # Animação de morte exclusivamente nos inimigos
            if hasattr(self, "anim_inim") and self.anim_inim:
                self.anim_inim.tocar("death", loop=False, duracao=0.85, forcar=True, retorno=None)
            for _, cb in getattr(self, "combatentes_inimigos", []):
                if cb and getattr(cb, "animador", None):
                    cb.animador.tocar("death", loop=False, duracao=0.85, forcar=True, retorno=None)

            # O HERÓI NUNCA CAI NA VITÓRIA: força guarda neutra (idle) e posição padrão
            self.combatente_jogador.y_offset = 0.0
            self.combatente_jogador.pos_alvo = [-220.0, 140.0, 70.0]
            self.combatente_jogador.pos_mundo = [-220.0, 140.0, 70.0]
            if hasattr(self, "anim_jog") and self.anim_jog:
                self.anim_jog.tocar("idle", loop=True, duracao=None, forcar=True, retorno="idle")
            if self.combatente_jogador and getattr(self.combatente_jogador, "animador", None):
                self.combatente_jogador.animador.tocar("idle", loop=True, duracao=None, forcar=True, retorno="idle")

            tempo_meta_comb = 95.0 if self.is_boss else 55.0
            self.resultado_rank = ranking.calcular_rank_desempenho(
                dano_recebido=getattr(self, "dano_recebido_combate", 0),
                tempo_segundos=getattr(self, "tempo_combate", 0.0),
                tempo_meta=tempo_meta_comb,
                qtes_perfeitos=getattr(self, "qtes_perfeitos", 0),
                parries_perfeitos=getattr(self, "parries_perfeitos", 0),
                venceu=True,
            )
            if self.progresso:
                chave_r = "boss_rush" if getattr(self, "modo_boss_rush", False) else self.sala_idx
                self.progresso.registrar_rank_sala(
                    chave_r,
                    self.resultado_rank["rank"],
                    self.resultado_rank["pontuacao"],
                    sem_avaria=self.resultado_rank["sem_avaria"],
                )

            self.banner_msg = "VITÓRIA ALCANÇADA"
            self.banner_cor = (253, 230, 138)
            self.cam.definir_pose(x=40, y=-10, zoom=1.18, tilt=0.0)
            self.timer_fim = 2.0
        else:
            self.estado = "FIM_DERROTA"
            audio.tocar_sfx("death_player", 1.0)
            if hasattr(self, "anim_jog") and self.anim_jog:
                self.anim_jog.tocar("death", loop=False, duracao=0.8, forcar=True, retorno=None)
            self.banner_msg = "VOCÊ CAIU..."
            self.banner_cor = (255, 90, 90)
            self.cam.definir_pose(x=-100, y=20, zoom=1.2, tilt=0.0)
            self.timer_fim = 1.0

    def tipo_golpe_atual(self):
        if self.estado == "TURNO_INIMIGO" and 0 <= self.golpe_inimigo_atual < len(self.combo_inimigo):
            return self.combo_inimigo[self.golpe_inimigo_atual]
        return None

    def preparar_golpe_inimigo(self):
        self.inimigo_timer = 0.0
        self.golpe_anim_iniciado = False
        self.reacao_executada_neste_golpe = False
        self.pulo_perfeito = False

        if hasattr(self, "combo_atacantes") and self.combo_atacantes and self.golpe_inimigo_atual < len(self.combo_atacantes):
            dados_golpe = self.combo_atacantes[self.golpe_inimigo_atual]
            self.atacante_atual_ref = dados_golpe["ref"]
            self.atacante_atual_cb = dados_golpe["cb"]
            self.atacante_atual_is_boss = dados_golpe["is_boss"]
            tipo = dados_golpe["tipo"]
        else:
            self.atacante_atual_ref = self.inimigo_ref
            self.atacante_atual_cb = self.combatente_inimigo
            self.atacante_atual_is_boss = self.is_boss
            tipo = self.combo_inimigo[self.golpe_inimigo_atual]

        num = self.golpe_inimigo_atual + 1
        total = len(self.combo_inimigo)
        desc = DESCRICAO_GOLPE.get(tipo, tipo)
        nome_at = self.atacante_atual_ref.nome

        # O combatente ativo avança em perspectiva 3D para a frente do herói!
        self.atacante_atual_cb.pos_alvo = [-170.0, 140.0, -20.0]

        self.cam.definir_pose(x=-25, y=10, zoom=1.12, tilt=2.5 if num % 2 == 1 else -2.5)
        # Golpes especiais têm telegrafias mais longas
        tempo_extra = 0.0
        if tipo in ("ONDA_CHOQUE", "INVESTIDA"):
            tempo_extra = 0.30
        elif tipo in ("RUGIDO", "RODOPIO"):
            tempo_extra = 0.15
        mult_lentidao = 1.35 if any(d["tipo"] == "LENTIDAO" for d in self.debuffs_inimigo) else 1.0
        self.tempo_impacto = (self.tempo_impacto_base + tempo_extra) * mult_lentidao
        if mult_lentidao > 1.0:
            self.adicionar_texto_flutuante("INIMIGO LENTO (+35% TEMPO REAÇÃO)!", 620, 140, (210, 180, 255))

        tag_p = ui_medieval.tag_comando("pulo")
        tag_x = ui_medieval.tag_comando("parry")
        tag_c = ui_medieval.tag_comando("desvio")

        prefixo_at = f"[!] {num}/{total} • {nome_at.upper()}"
        if tipo in GOLPES_SO_PULO:
            if tipo == "ONDA_CHOQUE":
                self.banner_msg = f"{prefixo_at}: ONDA DE CHOQUE! → {tag_p} PULE!"
                self.banner_cor = (255, 150, 40)
            elif tipo == "INVESTIDA":
                self.banner_msg = f"{prefixo_at}: MERGULHO RASANTE! → {tag_p} PULE!"
                self.banner_cor = (255, 100, 50)
            else:
                self.banner_msg = f"{prefixo_at}: IMPACTO NO SOLO! → {tag_p} PULAR!"
                self.banner_cor = (255, 210, 90)
        elif tipo in GOLPES_SO_PARRY:
            if tipo == "ESMAGAMENTO":
                self.banner_msg = f"{prefixo_at}: ESMAGAMENTO! → {tag_x} PARRY OBRIGATÓRIO!"
                self.banner_cor = (90, 210, 255)
            elif tipo == "GOLPE_TITANICO":
                self.banner_msg = f"{prefixo_at}: GOLPE TITÂNICO! → {tag_x} PARRY OBRIGATÓRIO!"
                self.banner_cor = (80, 240, 255)
            elif tipo == "QUEBRA_GUARDA":
                self.banner_msg = f"{prefixo_at}: QUEBRA GUARDA! → {tag_x} PARRY OBRIGATÓRIO!"
                self.banner_cor = (100, 200, 255)
            else:
                self.banner_msg = f"{prefixo_at}: {desc}! → {tag_x} PARRY OBRIGATÓRIO!"
                self.banner_cor = (90, 220, 255)
        elif tipo in GOLPES_SO_DESVIO:
            if tipo == "VENENO":
                self.banner_msg = f"{prefixo_at}: NÉVOA VENENOSA! → {tag_c} DESVIE!"
                self.banner_cor = (120, 255, 80)
            elif tipo == "RUGIDO":
                self.banner_msg = f"{prefixo_at}: RUGIDO SÔNICO! → {tag_c} DESVIE!"
                self.banner_cor = (200, 180, 255)
            else:
                self.banner_msg = f"{prefixo_at}: {desc}! → {tag_c} DESVIE!"
                self.banner_cor = (140, 255, 180)
        elif tipo == "GARRAS":
            self.banner_msg = f"{prefixo_at}: GARRAS! → {tag_x} PARRY ou {tag_c} DESVIO!"
            self.banner_cor = (255, 130, 70)
        elif tipo == "GOLPE_ARCANO":
            self.banner_msg = f"{prefixo_at}: GOLPE ARCANO! → {tag_x} PARRY ou {tag_c} DESVIO!"
            self.banner_cor = (180, 130, 255)
        elif tipo == "RODOPIO":
            self.banner_msg = f"{prefixo_at}: RODOPIO! → {tag_x} PARRY ou {tag_c} DESVIO!"
            self.banner_cor = (255, 200, 100)
        else:
            self.banner_msg = f"{prefixo_at}: {desc}! → {tag_x} PARRY ou {tag_c} DESVIO!"
            self.banner_cor = (255, 100, 90)

    def resolver_impacto_inimigo(self):
        tipo = self.combo_inimigo[self.golpe_inimigo_atual]
        mult_boss = 1.25 if self.is_boss else 1.0
        contra_por_pulo = False

        if tipo in GOLPES_SO_PULO:
            # Golpes que nao podem ser aparados nem desviados no chao: so pulando no timing exato.
            pulou = self.pulando and (self.pulo_offset_y < -25 or getattr(self, "pulo_perfeito", False))
            if pulou:
                pulo_perfeito = getattr(self, "pulo_perfeito", False)
                if pulo_perfeito or tipo in ("ONDA_CHOQUE", "INVESTIDA"):
                    contra_por_pulo = True
                    self.adicionar_texto_flutuante("SALTO PERFEITO! CONTRA-ATAQUE!", 180, 190, (255, 235, 110))
                    self.disparar_flash((255, 220, 90), 120)
                    self.cam.tremer(0.20, 10)
                    self.jogador_ap = min(self.max_ap, self.jogador_ap + (2 if pulo_perfeito else 1))
                else:
                    self.adicionar_texto_flutuante("SALTOU! +1 AP", 240, 210, (120, 255, 160))
                    self.jogador_ap = min(self.max_ap, self.jogador_ap + 1)
            else:
                self.todos_aparados_com_parry = False
                dano_base = DANO_GOLPE.get(tipo, CONFIG["inimigo_dano_rastria"])
                self.aplicar_dano_no_jogador(int(dano_base * mult_boss))
                self.aplicar_debuff("JOGADOR", "LENTIDAO", turnos=1, valor=1)
                self.adicionar_texto_flutuante("NÃO SALTOU A TEMPO!", 220, 220, (255, 90, 80))

        elif tipo in GOLPES_SO_PARRY:
            # Golpes esmagadores que SÓ podem ser defendidos com PARRY [X]
            if self.janela_parry_ativa > 0:
                self.parries_perfeitos += 1
                audio.tocar_sfx("parry", 1.0)
                self.hitstop_timer = 0.14
                self.cam.tremer(0.24, 16)
                self.disparar_flash((80, 240, 255), 140)
                self.jogador_ap = min(self.max_ap, self.jogador_ap + 2)
                self.adicionar_texto_flutuante("PARRY TITÂNICO! +2 AP", 250, 210, (80, 240, 255))
                self.cam.definir_pose(x=-65, y=20, zoom=1.30, tilt=-5.0)
            elif self.janela_desvio_ativa > 0:
                # Esquiva falha contra o impacto massivo no chão
                self.todos_aparados_com_parry = False
                dano_base = DANO_GOLPE.get(tipo, 18)
                tag_x = ui_medieval.tag_comando("parry")
                self.adicionar_texto_flutuante(f"DESVIO FALHOU! SÓ PARRY {tag_x}!", 180, 220, (255, 120, 80))
                self.aplicar_dano_no_jogador(int(dano_base * mult_boss * 0.65))
                self.aplicar_debuff("JOGADOR", "LENTIDAO", turnos=1, valor=1)
            else:
                self.todos_aparados_com_parry = False
                dano_base = DANO_GOLPE.get(tipo, 18)
                self.aplicar_dano_no_jogador(int(dano_base * mult_boss))
                self.aplicar_debuff("JOGADOR", "FRAQUEZA", turnos=2)

        elif tipo in GOLPES_SO_DESVIO:
            # Golpes que SÓ podem ser desviados (C), não aparados (X)
            if self.janela_desvio_ativa > 0:
                self.desvios_perfeitos += 1
                self.adicionar_texto_flutuante("DESVIO PERFEITO!", 190, 210, (130, 255, 180))
                self.jogador_ap = min(self.max_ap, self.jogador_ap + 1)
                self.cam.tremer(0.15, 8)
                self.disparar_flash((130, 255, 180), 90)
            elif self.janela_parry_ativa > 0:
                # Tentou parry num golpe que só aceita desvio — dano reduzido
                self.todos_aparados_com_parry = False
                dano_base = DANO_GOLPE.get(tipo, 15)
                tag_c = ui_medieval.tag_comando("desvio")
                self.adicionar_texto_flutuante(f"PARRY FALHOU! SÓ DESVIO {tag_c}!", 180, 220, (255, 180, 80))
                self.aplicar_dano_no_jogador(int(dano_base * mult_boss * 0.5))
                if tipo == "VENENO":
                    self.aplicar_debuff("JOGADOR", "VENENO", turnos=2, valor=10)
                elif tipo == "RUGIDO":
                    self.aplicar_debuff("JOGADOR", "LENTIDAO", turnos=1, valor=1)
            else:
                self.todos_aparados_com_parry = False
                dano_base = DANO_GOLPE.get(tipo, 15)
                self.aplicar_dano_no_jogador(int(dano_base * mult_boss))
                if tipo == "VENENO":
                    self.aplicar_debuff("JOGADOR", "VENENO", turnos=2, valor=10)
                elif tipo == "RUGIDO":
                    self.aplicar_debuff("JOGADOR", "LENTIDAO", turnos=1, valor=1)

        else:
            # Golpes padrão: podem ser aparados (X) ou desviados (C)
            if self.janela_parry_ativa > 0:
                self.parries_perfeitos += 1
                audio.tocar_sfx("parry", 1.0)
                self.hitstop_timer = 0.12
                self.cam.tremer(0.22, 14)
                self.disparar_flash((80, 255, 230), 130)
                ganho_ap = 2 if tipo == "RODOPIO" else 1  # Rodopio dá AP extra no parry
                self.jogador_ap = min(self.max_ap, self.jogador_ap + ganho_ap)
                self.adicionar_texto_flutuante(f"PARRY! +{ganho_ap} AP", 250, 210, (60, 255, 220))
                self.cam.definir_pose(x=-65, y=20, zoom=1.28, tilt=-5.0)

            elif self.janela_desvio_ativa > 0:
                audio.tocar_sfx("teleport", 0.75)
                self.todos_aparados_com_parry = False
                self.adicionar_texto_flutuante("DESVIO!", 190, 230, (130, 210, 255))

            else:
                self.todos_aparados_com_parry = False
                dano_base = DANO_GOLPE.get(tipo, CONFIG["inimigo_dano_corte"])
                self.aplicar_dano_no_jogador(int(dano_base * mult_boss))
                if tipo == "GARRAS":
                    self.aplicar_debuff("JOGADOR", "SANGRANDO", turnos=2)
                elif tipo == "GOLPE_ARCANO":
                    self.aplicar_debuff("JOGADOR", "FRAQUEZA", turnos=2)
                elif tipo == "RODOPIO":
                    self.aplicar_debuff("JOGADOR", "LENTIDAO", turnos=1, valor=1)

        # O atacante retorna suavemente para sua posição base na formação
        cb_at = getattr(self, "atacante_atual_cb", self.combatente_inimigo)
        if cb_at:
            cb_at.pos_alvo = list(cb_at.pos_base)

        self.golpe_inimigo_atual += 1
        restam_golpes = self.golpe_inimigo_atual < len(self.combo_inimigo) and self.jogador_hp > 0
        if not restam_golpes:
            self.turnos_inimigo_decorridos += 1
            if self.sala_idx >= 3 and self.turnos_inimigo_decorridos >= 2 and not self.esqueleto_invocado and self.jogador_hp > 0:
                self.invocar_esqueleto()

        if contra_por_pulo and self.jogador_hp > 0:
            # Pulou a Onda de Choque/Investida: contra-ataque imediato; depois o combo do boss continua
            self.iniciar_contra_ataque_cinematico(retomar_combo=restam_golpes, por_pulo=True)
        elif restam_golpes:
            self.preparar_golpe_inimigo()
        else:
            if self.todos_aparados_com_parry and self.jogador_hp > 0:
                self.iniciar_contra_ataque_cinematico()
            else:
                self.avancar_timeline()

    def invocar_esqueleto(self):
        """Invoca um alvo extra durante a batalha nas salas dos Necromantes."""
        self.esqueleto_invocado = True
        anim_esq = criar_animador("Esqueleto")
        hp_esq_base = 95
        hp_esq = self.progresso.escalar_hp_inimigo(hp_esq_base) if self.progresso else hp_esq_base
        esq = SimpleNamespace(
            nome="Esqueleto Invocado", hp=hp_esq, max_hp=hp_esq, cor=(205, 220, 190),
            is_boss=False, num_combos=1, vivo=True, esqueleto_invocado=True, debuffs=[],
            rect=pygame.Rect(0, 0, 42, 60), anim=anim_esq, _hp_base=hp_esq_base
        )
        self.alvos_disponiveis.append(esq)
        pos_esq = [420.0, 140.0, 130.0]
        cb_esq = NovoCombatente(
            nome=esq.nome, hp_max=hp_esq, ap_max=6, arquetipo="ASSASSINO",
            sprite_nome="Esqueleto", pos_mundo=list(pos_esq), is_boss=False
        )
        cb_esq.pos_base = list(pos_esq)
        cb_esq.pos_alvo = list(pos_esq)
        self.combatentes_inimigos.append((esq, cb_esq))
        self.mapa_combatentes[id(esq)] = cb_esq
        tag_mira = ui_medieval.tag_comando("alvos")
        self.adicionar_texto_flutuante(f"O NECROMANTE INVOCA UM ESQUELETO! {tag_mira} PARA MIRAR", 230, 120, (205, 225, 190))
        self.banner_msg = f"ESQUELETO INVOCADO! TROQUE O ALVO COM {tag_mira}"
        self.banner_cor = (205, 225, 190)

    def aplicar_dano_no_jogador(self, dano):
        # 1. Se o inimigo atacante tiver FRAQUEZA, dano é reduzido em 30%
        if any(d["tipo"] == "FRAQUEZA" for d in self.debuffs_inimigo):
            dano = int(dano * 0.70)
            self.adicionar_texto_flutuante("INIMIGO ENFRAQUECIDO -30%!", 220, 190, (175, 140, 255))
        # 2. Se o jogador tiver VULNERÁVEL, dano sofrido aumenta em 35%
        if any(d["tipo"] == "VULNERAVEL" for d in self.debuffs_jogador):
            dano = int(dano * 1.35)
            self.adicionar_texto_flutuante("VULNERÁVEL +35%!", 220, 205, (90, 230, 255))
        # 3. Se o jogador tiver SANGRANDO, dano sofrido aumenta em 30%
        if any(d["tipo"] == "SANGRANDO" for d in self.debuffs_jogador):
            dano = int(dano * 1.30)
            self.adicionar_texto_flutuante("SANGRIA +30%!", 220, 220, (255, 80, 80))

        dano = max(1, dano)
        self.dano_recebido_combate += dano
        self.jogador_hp = max(0, self.jogador_hp - dano)
        self.jogador_mapa.hp = self.jogador_hp
        audio.tocar_sfx("hit_player", 0.95)
        self.cam.tremer(0.25, 15)
        self.anim_jog.tocar("hurt", loop=False, duracao=0.40, forcar=True)
        self.disparar_flash((255, 40, 40), 140)
        self.adicionar_texto_flutuante(f"-{dano} HP", 240, 240, (255, 70, 70))
        if self.jogador_hp <= 0:
            self.iniciar_fim()

    def iniciar_contra_ataque_cinematico(self, retomar_combo=False, por_pulo=False):
        self.estado = "CONTRA_ATAQUE"
        self.contra_ataque_timer = 1.15
        self.contra_golpeou = False
        self.retomar_combo_apos_contra = retomar_combo
        self.jog_avanco = 1.0
        bonus_dano = self.progresso.bonus_dano() if self.progresso else 0
        mult_poder = self.progresso.multiplicador_poder() if self.progresso else 1.0
        if por_pulo:
            self.dano_contra_atual = int((CONFIG.get("boss_contra_ataque_pulo_dano", 26.4) + bonus_dano) * mult_poder)
            self.cam.definir_pose(x=140, y=-25, zoom=1.48, tilt=8.0)
            self.banner_msg = "PULOU A ONDA! CONTRA-ATAQUE!"
            self.banner_cor = (255, 235, 110)
        else:
            self.dano_contra_atual = int(((23 if self.is_boss else 19) + bonus_dano) * mult_poder)
            self.cam.definir_pose(x=140, y=-25, zoom=1.48, tilt=-8.0)
            self.banner_msg = "CONTRA-ATAQUE DE LUMINA DEVASTADOR!"
            self.banner_cor = (60, 255, 220)

    def continuar_luta_em_equipe(self):
        """Continua o mesmo combate quando ainda restam inimigos do grupo."""
        vivos = [a for a in self.alvos_disponiveis
                 if getattr(a, "vivo", True) and getattr(a, "hp", 1) > 0]
        if not vivos:
            return False
        # Escolhe automaticamente o próximo inimigo vivo, mas o jogador pode
        # mudar de alvo com A/D durante os turnos seguintes.
        novo = vivos[0]
        self.inimigo_ref = novo
        self.inimigo_nome = novo.nome
        self.inimigo_hp = max(0, novo.hp)
        self.inimigo_max_hp = max(1, getattr(novo, "max_hp", novo.hp))
        self.inimigo_cor = novo.cor
        self.is_boss = bool(getattr(novo, "is_boss", False))
        self.num_combos_inimigo = getattr(novo, "num_combos", 1)
        self.alvo_esqueleto = bool(getattr(novo, "esqueleto_invocado", False))
        self.anim_inim = Animador(getattr(getattr(novo, "anim", None), "personagem", None))
        self.estado = "MENU_JOGADOR"
        self.menu_categoria = "PRINCIPAL"
        self.opcao_principal = 0
        cb_novo = self.mapa_combatentes.get(id(novo), self.combatente_inimigo)
        self.combatente_inimigo = cb_novo
        self.timeline = [
            {"tipo": "JOGADOR", "ref": self.jogador_mapa, "cb": self.combatente_jogador, "nome": "Viajante"},
            {"tipo": "INIMIGO", "ref": novo, "cb": cb_novo, "nome": novo.nome},
        ]
        self.garantir_tamanho_timeline(min_turnos=6)
        self.fim_concluido = False
        self.timer_fim = 0.0
        self.inimigo_timer = 0.0
        self.debuffs_inimigo = getattr(novo, "debuffs", [])
        novo.debuffs = self.debuffs_inimigo
        tag_mira = ui_medieval.tag_comando("alvos")
        self.banner_msg = f"OUTRO INIMIGO! ALVO: {self.inimigo_nome} {tag_mira}"
        self.banner_cor = (255, 205, 110)
        self.cam.definir_pose(x=-40, y=15, zoom=1.0, tilt=0.0)
        self.adicionar_texto_flutuante(f"Restam {len(vivos)} inimigo(s)!", 230, 120, (255, 205, 110))
        return True

    def selecionar_alvo(self, delta):
        vivos = [pair[0] for pair in getattr(self, "combatentes_inimigos", []) if getattr(pair[0], "vivo", True) and getattr(pair[0], "hp", 0) > 0]
        if not vivos:
            return
        atual = self.inimigo_ref
        try:
            idx = vivos.index(atual)
        except ValueError:
            idx = 0
        novo = vivos[(idx + delta) % len(vivos)]
        if novo is atual:
            return
        self.selecionar_alvo_direto(novo)

    def selecionar_alvo_direto(self, novo):
        self.inimigo_ref = novo
        self.debuffs_inimigo = getattr(novo, "debuffs", [])
        novo.debuffs = self.debuffs_inimigo
        if novo in self.alvos_disponiveis:
            self.alvo_index = self.alvos_disponiveis.index(novo)
        self.inimigo_nome = novo.nome
        self.inimigo_hp = max(0, novo.hp)
        self.inimigo_max_hp = max(1, getattr(novo, "max_hp", novo.hp))
        self.inimigo_cor = novo.cor
        self.is_boss = bool(getattr(novo, "is_boss", False))
        self.num_combos_inimigo = getattr(novo, "num_combos", 1)
        self.alvo_esqueleto = bool(getattr(novo, "esqueleto_invocado", False))
        self.combatente_inimigo = self.mapa_combatentes.get(id(novo), self.combatente_inimigo)
        if self.combatente_inimigo and self.combatente_inimigo.animador:
            self.anim_inim = self.combatente_inimigo.animador
        self.cam.definir_pose(x=-40, y=15, zoom=1.0, tilt=0.0)
        if len(self.alvos_disponiveis) > 1:
            self.adicionar_texto_flutuante(f"Alvo: {self.inimigo_nome}", 620, 140, (190, 150, 255) if self.alvo_esqueleto else (100, 230, 210))
        self.banner_msg = ""

    def tentar_fugir(self):
        """Tenta fugir do combate atual e retornar ao mapa de exploração."""
        if self.is_boss:
            audio.tocar_sfx("shield", 0.8)
            self.adicionar_texto_flutuante("O CHEFE BLOQUEIA A FUGA!", 260, 260, (255, 90, 90))
        else:
            audio.tocar_sfx("dodge", 1.0)
            self.adicionar_texto_flutuante("FUGINDO DA BATALHA...", 260, 260, (140, 230, 255))
            self.estado = "FIM_FUGA"
            self.timer_fim = 0.5
            self.fugiu = True

    def handle_mouse_click(self, pos):
        """Permite selecionar e acionar os botões do menu de combate com o mouse."""
        mx, my = pos
        r_auto = pygame.Rect(14, 508, 92, 22)
        if r_auto.collidepoint(mx, my):
            BOT.alternar()
            self.adicionar_texto_flutuante("MODO AUTO: ATIVADO" if BOT.ativo else "MODO AUTO: DESATIVADO", 200, 100, (120, 255, 180) if BOT.ativo else (255, 140, 140))
            return
        if self.estado != "MENU_JOGADOR":
            return
        for i, caixa in getattr(self, "rects_botoes_menu", []):
            if caixa.collidepoint(pos):
                if self.menu_categoria == "PRINCIPAL":
                    self.opcao_principal = i
                    self.handle_keydown(pygame.K_RETURN)
                elif self.menu_categoria == "ATAQUES":
                    self.opcao_ataque = i
                    self.handle_keydown(pygame.K_RETURN)
                elif self.menu_categoria == "ITENS":
                    self.opcao_item = i
                    self.handle_keydown(pygame.K_RETURN)
                break

    def pular(self):
        """Dispara reação defensiva de salto (equivalente a ESPAÇO)."""
        self.handle_keydown(pygame.K_SPACE)

    def desviar(self):
        """Dispara reação defensiva de esquiva (equivalente a C)."""
        self.handle_keydown(pygame.K_c)

    def parry(self):
        """Dispara reação defensiva de parry (equivalente a X)."""
        self.handle_keydown(pygame.K_x)

    def handle_keydown(self, key):
        if key == pygame.K_F2:
            BOT.alternar()
            self.adicionar_texto_flutuante("MODO AUTO: ATIVADO" if BOT.ativo else "MODO AUTO: DESATIVADO", 200, 100, (120, 255, 180) if BOT.ativo else (255, 140, 140))
            return
        # A/D alternam entre inimigos vivos durante o turno do jogador (no menu principal, ataques e selecao de alvo).
        if self.estado == "MENU_JOGADOR" and self.menu_categoria in ("PRINCIPAL", "ATAQUES", "SELECAO_ALVO") and key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
            self.selecionar_alvo(-1 if key in (pygame.K_a, pygame.K_LEFT) else 1)
            return
        # 1. MENU PRINCIPAL (ATACAR, ITENS OU FUGIR)
        if self.estado == "MENU_JOGADOR":
            if self.menu_categoria == "PRINCIPAL":
                if key in (pygame.K_w, pygame.K_UP):
                    self.opcao_principal = (self.opcao_principal - 1) % 3
                elif key in (pygame.K_s, pygame.K_DOWN):
                    self.opcao_principal = (self.opcao_principal + 1) % 3
                elif key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
                    if self.opcao_principal == 0:
                        self.menu_categoria = "ATAQUES"
                    elif self.opcao_principal == 1:
                        self.menu_categoria = "ITENS"
                    else:
                        self.tentar_fugir()
                elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.tentar_fugir()

            # 2. SUBMENU DE ATAQUES
            elif self.menu_categoria == "ATAQUES":
                if key in (pygame.K_w, pygame.K_UP):
                    self.opcao_ataque = (self.opcao_ataque - 1) % len(self.acoes_ataque)
                elif key in (pygame.K_s, pygame.K_DOWN):
                    self.opcao_ataque = (self.opcao_ataque + 1) % len(self.acoes_ataque)
                elif key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
                    acao = self.acoes_ataque[self.opcao_ataque]
                    if self.jogador_ap < acao["custo"]:
                        self.adicionar_texto_flutuante("AP INSUFICIENTE!", 260, 260, (255, 80, 80))
                        return

                    if acao["golpes"] == 0:
                        # Foco absoluto / Buff
                        self.jogador_ap -= acao["custo"]
                        audio.tocar_sfx("shield", 0.9)
                        self.anim_jog.tocar("magic", loop=False, duracao=0.50, forcar=True)
                        self.jogador_ap = min(self.max_ap, self.jogador_ap + acao["ganho_ap"])
                        self.adicionar_texto_flutuante(f"+{acao['ganho_ap']} AP", 250, 230, (100, 255, 220))
                        # Efeito ativo do Foco Absoluto: Purifica 1 debuff do herói ou intimida o alvo com Fraqueza
                        if self.debuffs_jogador:
                            removido = self.debuffs_jogador.pop(0)
                            self.adicionar_texto_flutuante(f"FOCO PURIFICOU: {removido['nome']}!", 220, 200, (120, 255, 200))
                            self.disparar_flash((120, 255, 200), 100)
                        else:
                            self.aplicar_debuff("INIMIGO", "FRAQUEZA", turnos=2)
                        self.avancar_timeline()
                    elif acao.get("aoe", False):
                        # Dano em área (AoE) - Dança do Éter: atinge todos os alvos simultaneamente
                        self.jogador_ap -= acao["custo"]
                        audio.tocar_sfx("shock", 0.95)
                        self.acao_selecionada = acao
                        self.iniciar_qte_jogador(acao)
                    else:
                        # Habilidade de alvo único -> transita para SELECAO_ALVO sem gastar AP
                        self.acao_selecionada = acao
                        self.menu_categoria = "SELECAO_ALVO"
                        audio.tocar_sfx("ui_select", 0.5)
                        self.cam.definir_pose(x=-40, y=15, zoom=1.0, tilt=0.0)
                elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    audio.tocar_sfx("ui_select", 0.4)
                    self.menu_categoria = "PRINCIPAL"

            # 2.5 SUBMENU DE SELEÇÃO DE ALVO UNITÁRIO
            elif self.menu_categoria == "SELECAO_ALVO":
                if key in (pygame.K_a, pygame.K_LEFT, pygame.K_w, pygame.K_UP):
                    self.selecionar_alvo(-1)
                    audio.tocar_sfx("ui_select", 0.5)
                elif key in (pygame.K_d, pygame.K_RIGHT, pygame.K_s, pygame.K_DOWN):
                    self.selecionar_alvo(1)
                    audio.tocar_sfx("ui_select", 0.5)
                elif key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
                    acao = getattr(self, "acao_selecionada", self.acoes_ataque[self.opcao_ataque])
                    if self.jogador_ap < acao["custo"]:
                        self.adicionar_texto_flutuante("AP INSUFICIENTE!", 260, 260, (255, 80, 80))
                        self.menu_categoria = "ATAQUES"
                        return

                    self.jogador_ap -= acao["custo"]
                    if "Lumina" in acao["nome"] or "Corte" in acao["nome"]:
                        audio.tocar_sfx("fireball", 0.9)
                    elif "Tóxica" in acao["nome"]:
                        audio.tocar_sfx("sword_crit", 0.85)
                    else:
                        audio.tocar_sfx("sword", 0.8)
                    self.iniciar_qte_jogador(acao)
                elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_b):
                    audio.tocar_sfx("ui_select", 0.4)
                    self.menu_categoria = "ATAQUES"
                    self.cam.definir_pose(x=-20, y=0, zoom=1.0, tilt=0.0)

            # 3. SUBMENU DE ITENS (CURA E CRISTAL DE AP COM ZOOM DE CÂMERA NO PERSONAGEM)
            elif self.menu_categoria == "ITENS":
                if key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                    self.opcao_item = 1 - self.opcao_item
                    audio.tocar_sfx("ui_select", 0.5)
                elif key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
                    if self.opcao_item == 0:
                        # Usar Poção de Cura
                        if self.qtd_pocao > 0:
                            self.qtd_pocao -= 1
                            audio.tocar_sfx("potion", 0.85)
                            audio.tocar_sfx("heal", 0.9)
                            self.anim_jog.tocar("magic", loop=False, duracao=0.45, forcar=True)
                            cura_val = CONFIG["cura_pocao_valor"]
                            self.jogador_hp = min(self.jogador_max_hp, self.jogador_hp + cura_val)
                            self.jogador_mapa.hp = self.jogador_hp
                            # Câmera dá zoom focado no personagem ao usar o item
                            self.cam.definir_pose(x=-150, y=50, zoom=1.45, tilt=0.0)
                            self.disparar_flash((80, 255, 160), 120)
                            self.adicionar_texto_flutuante(f"CURA +{cura_val} HP!", 220, 200, (80, 255, 160))
                            self.avancar_timeline()
                        else:
                            self.adicionar_texto_flutuante("SEM POÇÕES!", 260, 260, (255, 80, 80))
                    else:
                        # Usar Cristal de AP
                        if self.qtd_cristal_ap > 0:
                            self.qtd_cristal_ap -= 1
                            audio.tocar_sfx("teleport", 0.85)
                            self.anim_jog.tocar("magic", loop=False, duracao=0.45, forcar=True)
                            ap_val = CONFIG["ap_cristal_valor"]
                            self.jogador_ap = min(self.max_ap, self.jogador_ap + ap_val)
                            self.cam.definir_pose(x=-150, y=50, zoom=1.45, tilt=0.0)
                            self.disparar_flash((80, 220, 255), 120)
                            self.adicionar_texto_flutuante(f"CRISTAL +{ap_val} AP!", 220, 200, (80, 220, 255))
                            self.avancar_timeline()
                        else:
                            self.adicionar_texto_flutuante("SEM CRISTAIS!", 260, 260, (255, 80, 80))
                elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    audio.tocar_sfx("ui_select", 0.4)
                    self.menu_categoria = "PRINCIPAL"

        elif self.estado == "QTE_JOGADOR":
            if key in (pygame.K_z, pygame.K_x, pygame.K_SPACE, pygame.K_RETURN):
                self.resolver_golpe_qte(apertou_botao=True)

        elif self.estado == "TURNO_INIMIGO":
            tipo = self.tipo_golpe_atual()
            if key == pygame.K_SPACE:
                # Click Time Event de Salto no Combate
                if not self.pulando:
                    self.pulando = True
                    tempo_restante = self.tempo_impacto - self.inimigo_timer
                    na_janela_pulo = abs(tempo_restante) <= 0.28
                    pulo_muito_cedo = tempo_restante > 0.45

                    if tipo in GOLPES_SO_PULO:
                        if na_janela_pulo:
                            self.pulo_perfeito = True
                            self.pulo_vy = -620.0  # Salto alto e acrobático de contra-ataque
                            audio.tocar_sfx("jump", 0.95)
                            self.anim_jog.tocar("jump", loop=False, duracao=0.55, forcar=True)
                            self.adicionar_texto_flutuante("★ SALTO PERFEITO! ★", 240, 200, (80, 255, 180))
                            self.disparar_flash((90, 255, 190), 110)
                            self.cam.definir_pose(x=-50, y=-25, zoom=1.35, tilt=4.5)
                        elif pulo_muito_cedo:
                            self.pulo_perfeito = False
                            self.pulo_vy = -450.0  # Salto curto prematuro
                            audio.tocar_sfx("jump", 0.70)
                            self.anim_jog.tocar("jump", loop=False, duracao=0.40, forcar=True)
                            self.adicionar_texto_flutuante("PULOU CEDO DEMAIS!", 220, 220, (255, 180, 80))
                        else:
                            self.pulo_perfeito = False
                            self.pulo_vy = -540.0
                            audio.tocar_sfx("jump", 0.80)
                            self.anim_jog.tocar("jump", loop=False, duracao=0.45, forcar=True)
                    else:
                        self.pulo_perfeito = False
                        self.pulo_vy = -540.0
                        audio.tocar_sfx("jump", 0.80)
                        self.anim_jog.tocar("jump", loop=False, duracao=0.45, forcar=True)
            elif tipo in GOLPES_SO_PULO:
                if key in (pygame.K_x, pygame.K_c):
                    if self.cooldown_reacao <= 0:
                        self.cooldown_reacao = 0.30
                        tag_p = ui_medieval.tag_comando("pulo")
                        self.adicionar_texto_flutuante(f"SÓ PULANDO {tag_p}!", 190, 250, (255, 190, 80))
            elif tipo in GOLPES_SO_PARRY:
                if key == pygame.K_c:
                    if self.cooldown_reacao <= 0:
                        self.cooldown_reacao = 0.30
                        tag_x = ui_medieval.tag_comando("parry")
                        self.adicionar_texto_flutuante(f"SÓ PARRY {tag_x}!", 190, 250, (255, 120, 80))
                elif key == pygame.K_x and self.cooldown_reacao <= 0 and not self.reacao_executada_neste_golpe:
                    self.janela_parry_ativa = 0.26
                    self.anim_jog.tocar("block", loop=False, duracao=0.32, forcar=True)
                    self.cooldown_reacao = 0.32
                    self.reacao_executada_neste_golpe = True
                    self.cam.definir_pose(x=-45, y=15, zoom=1.22, tilt=-4.0)
            elif tipo in GOLPES_SO_DESVIO:
                if key == pygame.K_x:
                    if self.cooldown_reacao <= 0:
                        self.cooldown_reacao = 0.30
                        tag_c = ui_medieval.tag_comando("desvio")
                        self.adicionar_texto_flutuante(f"SÓ DESVIO {tag_c}!", 190, 250, (255, 190, 80))
                elif key == pygame.K_c and self.cooldown_reacao <= 0 and not self.reacao_executada_neste_golpe:
                    self.janela_desvio_ativa = 0.36
                    self.desvio_offset_x = -85.0
                    self.anim_jog.tocar("dodge", loop=False, duracao=0.36, forcar=True)
                    self.cooldown_reacao = 0.32
                    self.reacao_executada_neste_golpe = True
                    self.cam.definir_pose(x=-70, y=10, zoom=1.15, tilt=4.0)
            elif self.cooldown_reacao <= 0 and not self.reacao_executada_neste_golpe:
                if key == pygame.K_x:
                    self.janela_parry_ativa = 0.23
                    self.anim_jog.tocar("block", loop=False, duracao=0.30, forcar=True)
                    self.cooldown_reacao = 0.32
                    self.reacao_executada_neste_golpe = True
                    self.cam.definir_pose(x=-45, y=15, zoom=1.20, tilt=-4.0)

                elif key == pygame.K_c:
                    self.janela_desvio_ativa = 0.36
                    self.desvio_offset_x = -85.0
                    self.anim_jog.tocar("dodge", loop=False, duracao=0.36, forcar=True)
                    self.cooldown_reacao = 0.32
                    self.reacao_executada_neste_golpe = True
                    self.cam.definir_pose(x=-70, y=10, zoom=1.15, tilt=4.0)

    def update(self, dt):
        self.tempo_combate += dt
        for tf in self.textos_flutuantes[:]:
            tf["y"] -= 45.0 * dt
            tf["tempo"] -= dt
            if tf["tempo"] <= 0:
                self.textos_flutuantes.remove(tf)

        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - int(450 * dt))

        # Estados finais de combate têm prioridade absoluta (não podem ser bloqueados por hitstop/pausa)
        if self.estado in ("VITORIA", "FIM_VITORIA", "FIM_DERROTA", "FIM_FUGA"):
            self.cam.update(dt)
            if hasattr(self, "cenario_25d") and self.cenario_25d:
                self.cenario_25d.atualizar(dt)
            if self.estado in ("VITORIA", "FIM_VITORIA"):
                self.combatente_jogador.pos_alvo = [-220.0, 140.0, 70.0]
                self.combatente_jogador.y_offset = 0.0
                if self.anim_jog and self.anim_jog.anim != "idle":
                    self.anim_jog.tocar("idle", loop=True, duracao=None, forcar=True, retorno="idle")
            self.combatente_jogador.update(dt)
            for _, cb_in in getattr(self, "combatentes_inimigos", []):
                cb_in.update(dt)
            if self.anim_jog:
                self.anim_jog.update(dt)
            if self.anim_inim:
                self.anim_inim.update(dt)
            self.timer_fim -= dt
            if self.timer_fim <= 0:
                self.fim_concluido = True
            return

        if self.pausa_tatica_timer > 0:
            self.pausa_tatica_timer -= dt
            self.cam.update(dt)
            if hasattr(self, "cenario_25d") and self.cenario_25d:
                self.cenario_25d.atualizar(dt)
            if self.pausa_tatica_timer <= 0:
                self.pausa_tatica_timer = 0.0
                self.avancar_timeline()
            return

        if self.hitstop_timer > 0:
            self.hitstop_timer -= dt
            return

        self.cam.update(dt)
        if hasattr(self, "cenario_25d") and self.cenario_25d:
            self.cenario_25d.atualizar(dt)

        # Atualização tridimensional dos combatentes modulares 2.5D
        av_j = 0.0 if self.estado == "MENU_JOGADOR" else self.jog_avanco
        
        # O herói avança exatamente na direção do inimigo escolhido (ou centro em AoE)
        x_base = -280.0
        z_base = -50.0
        is_aoe = (self.estado == "QTE_JOGADOR" and getattr(self, "acao_selecionada", {}).get("aoe", False))
        
        if is_aoe:
            x_dest = 40.0
            z_dest = 40.0
        else:
            alvo_cb = getattr(self, "atacante_atual_cb", None) if self.estado == "CONTRA_ATAQUE" else getattr(self, "combatente_inimigo", None)
            if alvo_cb and hasattr(alvo_cb, "pos_base"):
                ex = alvo_cb.pos_base[0]
                ez = alvo_cb.pos_base[2]
            elif alvo_cb and hasattr(alvo_cb, "pos_mundo"):
                ex = alvo_cb.pos_mundo[0]
                ez = alvo_cb.pos_mundo[2]
            else:
                ex = 160.0
                ez = 110.0
            x_dest = ex - 75.0
            z_dest = ez - 15.0

        self.combatente_jogador.pos_alvo[0] = x_base + (av_j * (x_dest - x_base)) + self.desvio_offset_x
        self.combatente_jogador.pos_alvo[1] = 140.0
        self.combatente_jogador.pos_alvo[2] = z_base + (av_j * (z_dest - z_base))

        self.combatente_jogador.update(dt)
        for _, cb_in in getattr(self, "combatentes_inimigos", []):
            cb_in.update(dt)

        self.anim_jog.update(dt)
        self.anim_inim.update(dt)

        inimigos_vivos = [pair for pair in getattr(self, "combatentes_inimigos", []) if getattr(pair[0], "vivo", True) and getattr(pair[0], "hp", 0) > 0]
        if (not inimigos_vivos) or self.jogador_hp <= 0:
            self.iniciar_fim()
            return

        self.janela_parry_ativa = max(0.0, self.janela_parry_ativa - dt)
        self.janela_desvio_ativa = max(0.0, self.janela_desvio_ativa - dt)
        self.cooldown_reacao = max(0.0, self.cooldown_reacao - dt)

        if self.janela_desvio_ativa <= 0:
            self.desvio_offset_x += (0.0 - self.desvio_offset_x) * 10.0 * dt

        if self.pulando:
            self.pulo_vy += 1450.0 * dt
            self.pulo_offset_y += self.pulo_vy * dt
            if self.pulo_offset_y >= 0.0:
                self.pulo_offset_y = 0.0
                self.pulo_vy = 0.0
                self.pulando = False

        if self.estado == "QTE_JOGADOR":
            self.qte_timer += dt
            if self.qte_timer >= self.qte_duracao + 0.14:
                self.resolver_golpe_qte(apertou_botao=False)

        elif self.estado == "TURNO_INIMIGO":
            self.inimigo_timer += dt
            prog_golpe = min(1.0, self.inimigo_timer / self.tempo_impacto)
            cb_at = getattr(self, "atacante_atual_cb", self.combatente_inimigo)
            if cb_at:
                if not hasattr(cb_at, "pos_base"):
                    cb_at.pos_base = list(cb_at.pos_mundo)
                # O atacante se aproxima em perspectiva 3D
                t_cub = prog_golpe ** 2
                cb_at.pos_mundo[0] = cb_at.pos_base[0] + (-170.0 - cb_at.pos_base[0]) * (t_cub * 0.75)
                cb_at.pos_mundo[2] = cb_at.pos_base[2] + (-20.0 - cb_at.pos_base[2]) * (t_cub * 0.75)

            if not self.golpe_anim_iniciado and self.inimigo_timer >= self.tempo_impacto - 0.45:
                self.golpe_anim_iniciado = True
                tipo_golpe = self.tipo_golpe_atual()
                anim_target = cb_at.animador if (cb_at and cb_at.animador) else self.anim_inim
                if tipo_golpe in GOLPES_SO_PULO:
                    anim_target.tocar("attack_pulo", loop=False, duracao=0.60, forcar=True)
                elif tipo_golpe in GOLPES_SO_PARRY:
                    anim_target.tocar("attack_parry", loop=False, duracao=0.60, forcar=True)
                elif tipo_golpe in GOLPES_SO_DESVIO:
                    anim_target.tocar("attack_desvio", loop=False, duracao=0.60, forcar=True)
                else:
                    anim_target.tocar("attack_combo" if "attack_combo" in getattr(anim_target, "personagem", SimpleNamespace(anims={})).anims else "attack", loop=False, duracao=0.60, forcar=True)

            if self.tipo_golpe_atual() == "ONDA_CHOQUE":
                self.inim_avanco = 0.2 * prog_golpe
            else:
                self.inim_avanco = prog_golpe ** 2

            if self.inimigo_timer >= self.tempo_impacto:
                self.resolver_impacto_inimigo()

        elif self.estado == "CONTRA_ATAQUE":
            self.contra_ataque_timer -= dt
            if not self.contra_golpeou and self.contra_ataque_timer <= 0.55 and self.hitstop_timer <= 0:
                self.contra_golpeou = True
                self.anim_jog.tocar("counter", loop=False, duracao=0.45, forcar=True)
                self.anim_inim.tocar("hurt", loop=False, duracao=0.40, forcar=True)
                dano_contra = self.dano_contra_atual
                if any(d["tipo"] == "FRAQUEZA" for d in self.debuffs_jogador):
                    dano_contra = int(dano_contra * 0.70)
                    self.adicionar_texto_flutuante("FRAQUEZA -30%!", 220, 170, (175, 140, 255))
                if any(d["tipo"] == "VULNERAVEL" for d in self.debuffs_inimigo):
                    dano_contra = int(dano_contra * 1.35)
                    self.adicionar_texto_flutuante("VULNERÁVEL +35%!", 580, 115, (90, 230, 255))
                if any(d["tipo"] == "SANGRANDO" for d in self.debuffs_inimigo):
                    dano_contra = int(dano_contra * 1.25)
                    self.adicionar_texto_flutuante("SANGRIA +25%!", 580, 130, (255, 80, 80))
                dano_contra = max(1, dano_contra)
                at_ref = getattr(self, "atacante_atual_ref", self.inimigo_ref)
                at_cb = getattr(self, "atacante_atual_cb", self.combatente_inimigo)
                if at_ref is self.inimigo_ref:
                    self.inimigo_hp = max(0, self.inimigo_hp - dano_contra)
                    self.inimigo_ref.hp = self.inimigo_hp
                    self.combatente_inimigo.hp_atual = self.inimigo_hp
                    if self.inimigo_hp <= 0:
                        self.inimigo_ref.vivo = False
                        if self.anim_inim:
                            self.anim_inim.tocar("death", loop=False, duracao=0.8, forcar=True, retorno=None)
                        vivos_ca = self._inimigos_vivos_lista()
                        if vivos_ca:
                            self.selecionar_alvo_direto(vivos_ca[0][0])
                else:
                    at_ref.hp = max(0, at_ref.hp - dano_contra)
                    if at_cb:
                        at_cb.hp_atual = at_ref.hp
                    if at_ref.hp <= 0:
                        at_ref.vivo = False
                        if at_cb and at_cb.animador:
                            at_cb.animador.tocar("death", loop=False, duracao=0.8, forcar=True, retorno=None)
                self.hitstop_timer = 0.15
                self.cam.tremer(0.35, 20)
                self.disparar_flash((60, 255, 220), 180)
                self.adicionar_texto_flutuante(f"CONTRA-ATAQUE! -{dano_contra}", 580, 140, (60, 255, 220))
                self.contra_ataque_timer = 0.40
            elif self.contra_ataque_timer <= 0:
                if (self.retomar_combo_apos_contra and self.inimigo_hp > 0 and self.jogador_hp > 0
                        and self.golpe_inimigo_atual < len(self.combo_inimigo)):
                    # Contra-ataque por pulo no meio do combo do boss: ele continua o combo
                    self.retomar_combo_apos_contra = False
                    self.estado = "TURNO_INIMIGO"
                    self.jog_avanco = 0.0
                    self.inim_avanco = 0.0
                    self.preparar_golpe_inimigo()
                else:
                    self.avancar_timeline()

    def desenhar_sinal_especial(self, surface, tipo, rect_inim, rect_jog, pe_y, progresso):
        """Efeito de aviso visual para golpes especiais (pulo, desvio, etc)."""
        t = self.inimigo_timer
        pulso = 0.5 + 0.5 * math.sin(t * 18.0)
        restante = self.tempo_impacto - t
        no_ar = self.pulando and self.pulo_offset_y < -35
        cx = rect_jog.centerx

        tag_p = ui_medieval.tag_comando("pulo")
        tag_x = ui_medieval.tag_comando("parry")
        tag_c = ui_medieval.tag_comando("desvio")

        # Determinar cor e texto baseado no tipo de golpe
        if tipo in GOLPES_SO_PULO:
            if no_ar:
                cor, texto = (110, 255, 150), "NO AR!"
            elif 0.10 <= restante <= 0.62 and not self.pulando:
                cor, texto = (255, 255, 120), f"PULE {tag_p} AGORA!"
            else:
                cor, texto = (255, int(90 + 90 * pulso), 50), f"PULE {tag_p}!"
        elif tipo in GOLPES_SO_PARRY:
            if self.janela_parry_ativa > 0:
                cor, texto = (80, 240, 255), "DEFENDENDO!"
            elif 0.10 <= restante <= 0.62:
                cor, texto = (255, 255, 120), f"PARRY {tag_x} AGORA!"
            else:
                cor, texto = (90, 210, 255), f"SÓ PARRY {tag_x}!"
        elif tipo in GOLPES_SO_DESVIO:
            if self.janela_desvio_ativa > 0:
                cor, texto = (130, 255, 180), "DESVIANDO!"
            elif 0.10 <= restante <= 0.62:
                cor, texto = (255, 255, 120), f"DESVIE {tag_c}!"
            else:
                cor, texto = (120, 255, 80) if tipo == "VENENO" else (200, 180, 255), f"DESVIE {tag_c}!"
        else:
            return  # Golpes normais não precisam de sinal especial

        # 1) Borda da tela pulsando
        borda = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        if tipo in GOLPES_SO_PULO:
            cor_borda = (255, 60, 40, int(50 + 110 * pulso))
        elif tipo in GOLPES_SO_PARRY:
            cor_borda = (80, 210, 255, int(45 + 105 * pulso))
        elif tipo == "VENENO":
            cor_borda = (60, 200, 40, int(40 + 100 * pulso))
        else:
            cor_borda = (160, 100, 255, int(40 + 100 * pulso))
        pygame.draw.rect(borda, cor_borda, borda.get_rect(), 10)
        surface.blit(borda, (0, 0))

        # 2) Zona de perigo
        larg_zona = int(150 * self.cam.zoom)
        zona = pygame.Rect(0, 0, larg_zona, 28)
        zona.center = (cx, int(pe_y))
        sup = pygame.Surface((zona.width, zona.height), pygame.SRCALPHA)
        if tipo in GOLPES_SO_PARRY:
            pygame.draw.ellipse(sup, (80, 200, 255, int(70 + 110 * pulso)), sup.get_rect())
        elif tipo == "VENENO":
            pygame.draw.ellipse(sup, (60, 200, 40, int(70 + 110 * pulso)), sup.get_rect())
        elif tipo == "RUGIDO":
            pygame.draw.ellipse(sup, (160, 100, 255, int(70 + 110 * pulso)), sup.get_rect())
        else:
            pygame.draw.ellipse(sup, (255, 70, 40, int(70 + 110 * pulso)), sup.get_rect())
        surface.blit(sup, zona.topleft)
        pygame.draw.ellipse(surface, cor, zona, 3)

        # 3) Efeito visual do golpe viajando
        x0, x1 = rect_inim.centerx, cx
        sentido = -1 if x1 < x0 else 1
        inicio = 0.30 if tipo in ("ONDA_CHOQUE", "INVESTIDA") else 0.10
        frac = max(0.0, min(1.0, (progresso - inicio) / (1.0 - inicio)))
        if frac > 0.0:
            fx = int(x0 + (x1 - x0) * frac)
            if tipo == "ONDA_CHOQUE":
                pygame.draw.line(surface, (110, 40, 45), (x0, int(pe_y)), (x1, int(pe_y)), 3)
                altura_onda = 56 * self.cam.zoom * (0.7 + 0.3 * pulso)
                for i in range(6):
                    px = fx - sentido * i * 24
                    h = int(altura_onda * (1.0 - i * 0.15))
                    cor_pico = (255, 200 - i * 18, 60) if i == 0 else (235, 90 - i * 8, 45)
                    pygame.draw.polygon(surface, cor_pico, [(px - 13, int(pe_y)), (px, int(pe_y) - h), (px + 13, int(pe_y))])
            elif tipo == "INVESTIDA":
                # Rastro de poeira / impacto no chão
                for i in range(8):
                    px = fx - sentido * i * 18
                    sz = max(3, int(14 - i * 1.5))
                    alpha_p = max(30, 220 - i * 25)
                    d_surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                    pygame.draw.circle(d_surf, (200, 100, 40, alpha_p), (sz, sz), sz)
                    surface.blit(d_surf, (px - sz, int(pe_y) - sz - 6))
            elif tipo == "VENENO":
                # Nuvem de veneno se espalhando
                for i in range(10):
                    px = fx - sentido * i * 14 + int(math.sin(t * 8 + i) * 8)
                    py_n = int(pe_y) - 20 - i * 4 + int(math.cos(t * 6 + i * 2) * 10)
                    sz = max(6, int(20 - i * 1.5))
                    v_surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                    pygame.draw.circle(v_surf, (90, 200, 50, max(20, 180 - i * 18)), (sz, sz), sz)
                    surface.blit(v_surf, (px - sz, py_n - sz))
            elif tipo == "RUGIDO":
                # Ondas circulares saindo do inimigo
                for i in range(4):
                    raio = int(frac * 250 + i * 30)
                    alpha_r = max(20, 150 - i * 35 - int(frac * 80))
                    r_surf = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                    pygame.draw.circle(r_surf, (180, 150, 255, alpha_r), (raio, raio), raio, 3)
                    surface.blit(r_surf, (x0 - raio, int(pe_y) - raio - 30))
            else:
                pygame.draw.rect(surface, (255, 190, 70), (min(fx, fx - sentido * 110), int(pe_y) - 14, 110, 12), border_radius=4)

        # 4) Setas de aviso laterais suaves no chão
        for lado in (-1, 1):
            ax = cx + lado * int(95 * self.cam.zoom)
            for k in range(3):
                fase = (t * 2.2 + k * 0.33) % 1.0
                ay = int(pe_y) - 24 - k * 26 - int(fase * 14)
                fade = 1.0 - fase * 0.55
                cor_seta = (int(cor[0] * fade), int(cor[1] * fade), int(cor[2] * fade))
                if tipo in GOLPES_SO_PULO:
                    pts = [(ax - 16, ay + 14), (ax, ay), (ax + 16, ay + 14), (ax + 16, ay + 24), (ax, ay + 10), (ax - 16, ay + 24)]
                else:
                    pts = [(ax, ay), (ax + lado * 20, ay + 10), (ax, ay + 20), (ax + lado * 6, ay + 14), (ax + lado * 6, ay + 6)]
                pygame.draw.polygon(surface, cor_seta, pts)

    def draw(self, surface):
        # 1. Pipeline de Cenário 2.5D com céu, muralha, tochas de Éter, chão em trapézio e Z-sorting unificado
        combatentes_cenario = []
        em_vitoria = self.estado in ("VITORIA", "FIM_VITORIA")
        for ali, cb in getattr(self, "combatentes_inimigos", []):
            if em_vitoria or (getattr(ali, "vivo", True) and getattr(ali, "hp", 0) > 0):
                cb.y_offset = 0.0
                combatentes_cenario.append(cb)

        self.combatente_jogador.y_offset = self.pulo_offset_y
        combatentes_cenario.append(self.combatente_jogador)

        if hasattr(self, "cenario_25d") and self.cenario_25d:
            self.cenario_25d.desenhar_completo(surface, self.cam, combatentes_cenario)
        else:
            cenarios.desenhar_fundo_combate(surface, self.tempo_combate, cam=self.cam, sala_idx=self.sala_idx)
            for cb in combatentes_cenario:
                cb.desenhar_25d(surface, cam_x=self.cam.x, cam_y=self.cam.y)

        # Atualiza retângulos do herói e do inimigo focado para efeitos e QTEs
        rect_jog = getattr(self.combatente_jogador, "ultimo_rect_25d", None) or getattr(self.combatente_jogador, "rect_tela", None)
        if rect_jog is None:
            tx, ty, _ = self.cam.projetar(self.combatente_jogador.x_mundo, 140.0 + self.pulo_offset_y, self.combatente_jogador.z_mundo)
            rect_jog = pygame.Rect(int(tx - 35), int(ty - 90), 70, 90)

        if self.janela_parry_ativa > 0:
            pygame.draw.circle(surface, (80, 255, 220), rect_jog.center, int(rect_jog.width * 0.75), 3)
        elif self.janela_desvio_ativa > 0:
            pygame.draw.circle(surface, (110, 190, 255), rect_jog.center, int(rect_jog.width * 0.70), 2)

        # Inimigo focado / atacante ativo
        alvo_cb = None
        if self.estado == "TURNO_INIMIGO" and hasattr(self, "atacante_atual_ref"):
            for ref, cb in self.combatentes_inimigos:
                if ref is self.atacante_atual_ref:
                    alvo_cb = cb
                    break
        if alvo_cb is None:
            for ref, cb in self.combatentes_inimigos:
                if ref is self.inimigo_ref:
                    alvo_cb = cb
                    break
        if alvo_cb is None and self.combatentes_inimigos:
            alvo_cb = self.combatentes_inimigos[0][1]

        rect_inim = getattr(alvo_cb, "ultimo_rect_25d", None) or getattr(alvo_cb, "rect_tela", None)
        if rect_inim is None:
            if alvo_cb:
                tx, ty, _ = self.cam.projetar(alvo_cb.x_mundo, 140.0, alvo_cb.z_mundo)
                rect_inim = pygame.Rect(int(tx - 35), int(ty - 90), 70, 90)
            else:
                rect_inim = pygame.Rect(600, 240, 120, 180)

        # Efeitos de aura de debuff nos inimigos
        for ali, cb in getattr(self, "combatentes_inimigos", []):
            if getattr(ali, "vivo", True) and getattr(ali, "hp", 0) > 0:
                r_in = getattr(cb, "ultimo_rect_25d", None) or getattr(cb, "rect_tela", None)
                if r_in:
                    self.desenhar_aura_debuffs(surface, r_in, getattr(ali, "debuffs", []), getattr(self, "tempo_combate", 0.0))

        # HUD Individual dos Inimigos (Ancoragem individual no topo, sem sobreposições)
        is_aoe = (self.estado == "QTE_JOGADOR" and getattr(self, "acao_selecionada", {}).get("aoe", False))
        combate_ui.desenhar_hud_inimigos_coletivo(
            surface,
            getattr(self, "combatentes_inimigos", []),
            self.inimigo_ref,
            self.cam,
            getattr(self, "tempo_combate", 0.0),
            is_aoe,
            fontes_ui["pequena"],
            fontes_ui["micro"]
        )

        # Aura e partículas de debuffs no jogador
        self.desenhar_aura_debuffs(surface, rect_jog, self.debuffs_jogador, getattr(self, "tempo_combate", 0.0))

        # QTE visual único por tipo de habilidade
        if self.estado == "QTE_JOGADOR":
            qx, qy = rect_inim.centerx, rect_inim.centery
            progresso = self.qte_timer / self.qte_duracao
            na_zona = 0.74 <= progresso <= 1.05
            acao_qte = self.acoes_ataque[self.opcao_ataque]
            nome_qte = acao_qte.get("nome", "")
            tag_atk = ui_medieval.tag_comando("atacar")
            # Variante visual por habilidade
            if "Dança" in nome_qte or "Éter" in nome_qte:
                # Triplo flash ciano rúnico — 3 golpes cósmicos
                pulso_qte = 0.5 + 0.5 * math.sin(self.qte_timer * 14)
                for off in (-38, 0, 38):
                    qx_off = qx + off
                    raio_c = int(22 + 8 * pulso_qte)
                    cor_c = (int(40 + 80 * pulso_qte), int(210 + 45 * pulso_qte), 255, 180) if na_zona else (60, 180, 255, 120)
                    c_surf = pygame.Surface((raio_c * 2 + 4, raio_c * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(c_surf, cor_c, (raio_c + 2, raio_c + 2), raio_c, 3)
                    surface.blit(c_surf, (qx_off - raio_c - 2, qy - raio_c - 2))
                ui_medieval.desenhar_mira_runica_qte(surface, qx, qy, progresso, tamanho_alvo=32)
                cor_qte = (80, 255, 255) if na_zona else (140, 200, 255)
                inst_txt = fonte_menu.render(f"{tag_atk} COMBO CÓSMICO" if na_zona else f"{tag_atk} TIMING...", True, cor_qte)
            elif "Corte" in nome_qte or "Lumina" in nome_qte:
                # Brilho solar rápido — slash de fogo
                pulso_qte = 0.5 + 0.5 * math.sin(self.qte_timer * 18)
                raio_c = int(28 + 12 * pulso_qte)
                cor_c = (255, int(160 + 60 * pulso_qte), 40, 160) if na_zona else (255, 140, 60, 90)
                c_surf = pygame.Surface((raio_c * 2 + 4, raio_c * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(c_surf, cor_c, (raio_c + 2, raio_c + 2), raio_c, 4)
                surface.blit(c_surf, (qx - raio_c - 2, qy - raio_c - 2))
                pygame.draw.line(surface, (255, 210, 80) if na_zona else (200, 140, 60), (qx - raio_c, qy), (qx + raio_c, qy), 3)
                ui_medieval.desenhar_mira_runica_qte(surface, qx, qy, progresso, tamanho_alvo=36)
                cor_qte = (255, 220, 80) if na_zona else (220, 160, 60)
                inst_txt = fonte_menu.render(f"{tag_atk} CORTE SOLAR!" if na_zona else f"{tag_atk} AGUARDE...", True, cor_qte)
            elif "Tóxica" in nome_qte:
                # Pulso verde veneno
                pulso_qte = 0.5 + 0.5 * math.sin(self.qte_timer * 10)
                raio_c = int(26 + 10 * pulso_qte)
                cor_c = (50, 220, 60, 150) if na_zona else (40, 170, 50, 80)
                c_surf = pygame.Surface((raio_c * 2 + 4, raio_c * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(c_surf, cor_c, (raio_c + 2, raio_c + 2), raio_c, 3)
                surface.blit(c_surf, (qx - raio_c - 2, qy - raio_c - 2))
                ui_medieval.desenhar_mira_runica_qte(surface, qx, qy, progresso, tamanho_alvo=36)
                cor_qte = (80, 255, 100) if na_zona else (60, 180, 80)
                inst_txt = fonte_menu.render(f"{tag_atk} VENENO!" if na_zona else f"{tag_atk} TIMING...", True, cor_qte)
            else:
                # Assalto Rápido / padrão
                ui_medieval.desenhar_mira_runica_qte(surface, qx, qy, progresso, tamanho_alvo=38)
                cor_qte = (255, 235, 120) if na_zona else (215, 190, 150)
                inst_txt = fonte_menu.render(f"{tag_atk} AGORA!" if na_zona else f"{tag_atk} TIMING...", True, cor_qte)
            surface.blit(inst_txt, (qx - inst_txt.get_width() // 2, qy - 14))

        elif self.estado == "TURNO_INIMIGO":
            tipo_atual = self.tipo_golpe_atual()
            golpe_so_pulo = tipo_atual in GOLPES_SO_PULO
            progresso = min(1.0, self.inimigo_timer / self.tempo_impacto)
            # Posição real do chão da arena (Y=140.0) projetada na tela (fixa no solo, mesmo com o herói no ar)
            chao_px, chao_py, _ = self.cam.projetar(self.combatente_jogador.x_mundo, 140.0, self.combatente_jogador.z_mundo)
            cx = chao_px
            cy = rect_jog.centery - 10
            pe_base_y = int(chao_py)
            em_janela = abs(self.tempo_impacto - self.inimigo_timer) <= 0.22

            # ==============================================================
            # ESTILO DEFENSIVO 1: OBRIGADO A PULAR (GOLPES DE CHÃO / SÍSMICOS)
            # ==============================================================
            if golpe_so_pulo:
                chao_y = pe_base_y
                no_ar = self.pulando and (self.pulo_offset_y < -25 or getattr(self, "pulo_perfeito", False))

                # 1. Sweet Spot Rúnico de Salto no Solo (Alvo do QTE)
                raio_sweet_x = 36
                raio_sweet_y = 14
                sweet_surf = pygame.Surface((raio_sweet_x * 2 + 8, raio_sweet_y * 2 + 8), pygame.SRCALPHA)
                cor_sweet = (255, 245, 120) if em_janela else (225, 160, 50)
                pygame.draw.ellipse(sweet_surf, (20, 14, 25), (4, 4, raio_sweet_x * 2, raio_sweet_y * 2))
                pygame.draw.ellipse(sweet_surf, cor_sweet, (4, 4, raio_sweet_x * 2, raio_sweet_y * 2), 2 if not em_janela else 3)
                surface.blit(sweet_surf, (cx - raio_sweet_x - 4, chao_y - raio_sweet_y - 4))

                cmd_pulo_tag = ui_medieval.tag_comando("pulo")
                cmd_pulo = f"{cmd_pulo_tag} SALTAR"
                txt_cmd = fonte_pequena.render(cmd_pulo, True, (255, 255, 255) if em_janela else COR_TEXTO_OURO)
                surface.blit(txt_cmd, (cx - txt_cmd.get_width() // 2, chao_y - txt_cmd.get_height() // 2))

                # 2. Elipse da onda de choque sísmica convergindo para o Sweet Spot
                raio_x_onda = int(140 * (1.0 - progresso) + raio_sweet_x)
                raio_y_onda = int(raio_x_onda * 0.38)
                fenda_surf = pygame.Surface((raio_x_onda * 2 + 8, raio_y_onda * 2 + 8), pygame.SRCALPHA)
                
                # Cores de magma ardente e choque telúrico
                cor_onda = (255, 240, 110, 230) if em_janela else (255, 110, 35, int(120 + 80 * (1.0 - progresso)))
                pygame.draw.ellipse(fenda_surf, cor_onda, (4, 4, raio_x_onda * 2, raio_y_onda * 2), 4 if em_janela else 3)
                pygame.draw.ellipse(fenda_surf, (255, 60, 20, 80), (8, 8, raio_x_onda * 2 - 8, raio_y_onda * 2 - 8))
                surface.blit(fenda_surf, (cx - raio_x_onda - 4, chao_y - raio_y_onda - 4))

                # 3. Setas verticais ascendentes saindo do solo [▲ SALTO ▲]
                for off_x in (-36, 0, 36):
                    sx_seta = cx + off_x
                    fase_s = (self.inimigo_timer * 6.0 + off_x * 0.1) % 1.0
                    sy_seta = chao_y - int(fase_s * 48)
                    cor_s = (255, 245, 120) if em_janela else (255, 140, 40)
                    pts_s = [(sx_seta, sy_seta - 14), (sx_seta - 8, sy_seta), (sx_seta - 3, sy_seta), (sx_seta - 3, sy_seta + 10), (sx_seta + 3, sy_seta + 10), (sx_seta + 3, sy_seta), (sx_seta + 8, sy_seta)]
                    pygame.draw.polygon(surface, cor_s, pts_s)

                # 4. Se estiver no ar, projeta escudo e asas de vento de salto seguro
                if no_ar:
                    pygame.draw.circle(surface, (80, 255, 180), (cx, rect_jog.centery), int(60 * self.cam.zoom), 2)
                    pygame.draw.circle(surface, (120, 255, 210), (cx, rect_jog.centery), int(66 * self.cam.zoom), 1)

                badge_txt = "SALTO PERFEITO (NO AR!)" if no_ar else (f"SALTE AGORA! {cmd_pulo_tag}" if em_janela else f"SALTO OBRIGATÓRIO {cmd_pulo_tag}")
                sub_txt = "HERÓI FORA DE ALCANCE!" if no_ar else "ATAQUE SÍSMICO DE CHÃO — PARRY É INÚTIL!"
                cor_badge_borda = (80, 255, 180) if no_ar else ((255, 245, 120) if em_janela else (255, 140, 40))
                var_badge = "pedra" if no_ar else "carmesim"

            # ==============================================================
            # ESTILO DEFENSIVO 2: OBRIGADO A DESVIAR (GARRAS / VENENO / SOMBRA)
            # ==============================================================
            elif tipo_atual in GOLPES_SO_DESVIO:
                # 1. Núcleo central de névoa e sombra de esquiva
                cor_miasma = (70, 235, 90) if tipo_atual == "VENENO" else (205, 140, 255)
                cor_miasma_luz = (150, 255, 160) if tipo_atual == "VENENO" else (235, 190, 255)
                cmd_desvio_tag = ui_medieval.tag_comando("desvio")
                
                # Runa de esquiva com setas horizontais no torso
                raio_nucleo = 26
                pygame.draw.circle(surface, (20, 15, 30), (cx, cy), raio_nucleo)
                pygame.draw.circle(surface, cor_miasma, (cx, cy), raio_nucleo, 2)
                txt_esq = fonte_pequena.render(cmd_desvio_tag, True, (255, 255, 255) if em_janela else cor_miasma_luz)
                surface.blit(txt_esq, (cx - txt_esq.get_width() // 2, cy - txt_esq.get_height() // 2))

                # 2. Duas presas / lâminas curvadas laterais cortando em direção ao peito
                dist_lat = int(140 * (1.0 - progresso) + 32)
                # Lâmina Esquerda convergindo para a direita
                x_esq = cx - dist_lat
                pts_esq = [(x_esq, cy - 28), (x_esq + 26, cy), (x_esq, cy + 28), (x_esq + 8, cy)]
                pygame.draw.polygon(surface, cor_miasma_luz if em_janela else cor_miasma, pts_esq)
                pygame.draw.polygon(surface, (10, 8, 14), pts_esq, 1)

                # Lâmina Direita convergindo para a esquerda
                x_dir = cx + dist_lat
                pts_dir = [(x_dir, cy - 28), (x_dir - 26, cy), (x_dir, cy + 28), (x_dir - 8, cy)]
                pygame.draw.polygon(surface, cor_miasma_luz if em_janela else cor_miasma, pts_dir)
                pygame.draw.polygon(surface, (10, 8, 14), pts_dir, 1)

                # Indicadores de evasão lateral desenhados como polígonos puros
                pulso_e = 0.5 + 0.5 * math.sin(self.inimigo_timer * 16.0)
                seta_off = int(12 * pulso_e)
                pts_arr_esq = [(cx - 52 - seta_off, cy), (cx - 38 - seta_off, cy - 10), (cx - 38 - seta_off, cy + 10)]
                pygame.draw.polygon(surface, cor_miasma_luz, pts_arr_esq)
                pygame.draw.polygon(surface, (10, 8, 14), pts_arr_esq, 1)
                pts_arr_dir = [(cx + 52 + seta_off, cy), (cx + 38 + seta_off, cy - 10), (cx + 38 + seta_off, cy + 10)]
                pygame.draw.polygon(surface, cor_miasma_luz, pts_arr_dir)
                pygame.draw.polygon(surface, (10, 8, 14), pts_arr_dir, 1)

                badge_txt = f"DESVIO OBRIGATÓRIO {cmd_desvio_tag}"
                sub_txt = "GOLPE IMPARÁVEL — APENAS A ESQUIVA SALVA!"
                cor_badge_borda = (255, 245, 120) if em_janela else cor_miasma
                var_badge = "pedra"

            # ==============================================================
            # ESTILO DEFENSIVO 3: PARRY CLÁSSICO E TITÂNICO (APARAR COM [X])
            # ==============================================================
            else:
                cmd_parry_tag = ui_medieval.tag_comando("parry")
                cmd_desvio_tag = ui_medieval.tag_comando("desvio")

                # 1. Brasão Octogonal de Bloqueio no peito do herói (sweet spot)
                raio_alvo = 32
                pts_octo = []
                for i_oct in range(8):
                    ang_o = i_oct * (math.pi / 4.0) + (math.pi / 8.0)
                    pts_octo.append((cx + int(raio_alvo * math.cos(ang_o)), cy + int(raio_alvo * math.sin(ang_o))))
                
                pygame.draw.polygon(surface, (28, 22, 38), pts_octo)
                pygame.draw.polygon(surface, COR_TEXTO_OURO if em_janela else (80, 95, 125), pts_octo, 3)
                # Rebites nas pontas do octógono
                for px_o, py_o in pts_octo:
                    pygame.draw.circle(surface, COR_TEXTO_OURO if em_janela else (180, 190, 215), (px_o, py_o), 2)
                
                # Símbolo central de bloqueio [X]
                txt_parry_btn = fonte_menu.render(cmd_parry_tag, True, (255, 255, 255) if em_janela else COR_TEXTO_OURO)
                surface.blit(txt_parry_btn, (cx - txt_parry_btn.get_width() // 2, cy - txt_parry_btn.get_height() // 2))

                # 2. Mira de 4 Lâminas / Pontas de Ferro que Convergem
                raio_atual = int(125 * (1.0 - progresso) + raio_alvo)
                if raio_atual > raio_alvo:
                    cor_mira = (255, 245, 120) if em_janela else (90, 220, 255)
                    # Círculo de contenção
                    pygame.draw.circle(surface, cor_mira, (cx, cy), raio_atual, 2)
                    # 4 Pontas de espada apontando para o centro (Topo, Baixo, Esquerda, Direita)
                    for ang_p in (0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0):
                        bx1 = cx + int(raio_atual * math.cos(ang_p))
                        by1 = cy + int(raio_atual * math.sin(ang_p))
                        bx2 = cx + int((raio_atual - 14) * math.cos(ang_p))
                        by2 = cy + int((raio_atual - 14) * math.sin(ang_p))
                        # Asas laterais da ponta
                        perp = ang_p + math.pi / 2.0
                        wx1 = cx + int((raio_atual + 8) * math.cos(ang_p) + 6 * math.cos(perp))
                        wy1 = cy + int((raio_atual + 8) * math.sin(ang_p) + 6 * math.sin(perp))
                        wx2 = cx + int((raio_atual + 8) * math.cos(ang_p) - 6 * math.cos(perp))
                        wy2 = cy + int((raio_atual + 8) * math.sin(ang_p) - 6 * math.sin(perp))
                        pygame.draw.polygon(surface, cor_mira, [(bx2, by2), (wx1, wy1), (bx1, by1), (wx2, wy2)])

                # Quando na janela exata, faíscas de energia ciano conectam ao centro
                if em_janela:
                    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), raio_alvo + 4, 2)
                    pygame.draw.circle(surface, (80, 255, 230), (cx, cy), raio_alvo + 8, 1)

                badge_txt = f"PARRY {cmd_parry_tag}  OU  DESVIO {cmd_desvio_tag}" if tipo_atual not in GOLPES_SO_PARRY else f"PARRY OBRIGATÓRIO {cmd_parry_tag}"
                sub_txt = "BLOQUEIO DE PRECISÃO NO IMPACTO!" if tipo_atual not in GOLPES_SO_PARRY else "GOLPE ESMAGADOR — APENAS PARRY FUNCIONA!"
                cor_badge_borda = (255, 245, 120) if em_janela else (85, 245, 255)
                var_badge = "pedra"

            # 3. Badge de ação reativa flutuante sobre o herói (Expedition 33)
            # Evita sobrepor a barra de vida do inimigo no plano de fundo
            tem_boss_flag = self.is_boss or getattr(self.inimigo_ref, "is_boss", False)
            if rect_jog.top - 54 > (102 if tem_boss_flag else 50) and (rect_jog.top - 54 > rect_inim.bottom + 10 or abs(cx - rect_inim.centerx) > 130):
                badge_y = rect_jog.top - 54
            else:
                badge_y = min(ALTURA_TELA - 52, rect_jog.bottom + 10)
            rend_b = fonte_pequena.render(badge_txt, True, cor_badge_borda)
            rend_sub = fonte_micro.render(sub_txt, True, (240, 240, 250))
            bw = max(rend_b.get_width(), rend_sub.get_width()) + 24
            bh = 40
            rect_b = pygame.Rect(max(10, min(LARGURA_TELA - bw - 10, cx - bw // 2)), badge_y, bw, bh)
            ui_procedural.desenhar_moldura_gotica(surface, rect_b, chanfro=5, destacado=em_janela, alpha=244, cantoneiras=False)
            surface.blit(rend_b, (rect_b.centerx - rend_b.get_width() // 2, rect_b.y + 4))
            surface.blit(rend_sub, (rect_b.centerx - rend_sub.get_width() // 2, rect_b.y + 22))

            if golpe_so_pulo or tipo_atual in GOLPES_SO_DESVIO:
                self.desenhar_sinal_especial(surface, tipo_atual, rect_inim, rect_jog, pe_base_y, progresso)

        # ==============================================================
        # 1. MENU DE AÇÕES DO JOGADOR (CENTRO / INFERIOR ESQUERDO)
        # ==============================================================
        # 1. MENU DE AÇÕES DO JOGADOR (CENTRO / INFERIOR ESQUERDO)
        # ==============================================================
        menu_pos = ui_configurador.obter_posicao("menu_combate") if ui_configurador else (250, 382)
        if self.estado == "MENU_JOGADOR":
            self.rects_botoes_menu = combate_ui.desenhar_menu_comandos(
                surface, menu_pos[0], menu_pos[1], 356, 134,
                self.estado, self.menu_categoria,
                self.opcao_principal, self.opcao_ataque, self.opcao_item,
                self.acoes_ataque, self.jogador_ap, self.inimigo_nome,
                fontes_ui
            )
        else:
            self.rects_botoes_menu = []

        # ==============================================================
        # 2. PAINEL DE STATUS DO VIAJANTE (CANTO INFERIOR DIREITO)
        # ==============================================================
        hud_pos = ui_configurador.obter_posicao("hud_jogador") if ui_configurador else (618, 382)
        combate_ui.desenhar_painel_viajante(
            surface, hud_pos[0], hud_pos[1], 308, 134,
            self.jogador_hp, self.jogador_max_hp, self.jogador_ap, self.max_ap,
            self.qtd_pocao, self.qtd_cristal_ap, self.progresso,
            self.debuffs_jogador, self.anim_jog, fontes_ui
        )

        # 3. LINHA DO TEMPO VERTICAL EXPEDITION 33
        tl_pos = ui_configurador.obter_posicao("timeline") if ui_configurador else (14, 18)
        em_rush = bool(getattr(self, "modo_boss_rush", False))
        combate_ui.desenhar_linha_tempo_vertical(
            surface, tl_pos[0], tl_pos[1], self.timeline,
            getattr(self, "tempo_combate", 0.0), self.anim_jog, fontes_ui,
            deslocar_abaixo_badge=em_rush
        )

        # 4. BARRA MONUMENTAL DO CHEFE E HUD DE BOSS RUSH
        tem_boss = self.is_boss or getattr(self.inimigo_ref, "is_boss", False)
        if tem_boss:
            t_rush_ovr = getattr(self, "tempo_boss_rush_ativo", None)
            if em_rush and t_rush_ovr is not None:
                t_dec = max(0.0, float(t_rush_ovr))
            elif self.progresso:
                t_dec = max(0.0, float(getattr(self.progresso, "tempo_decorrido", 0.0)))
            else:
                t_dec = self.tempo_combate
            mm = int(t_dec // 60)
            ss = int(t_dec % 60)
            cs = int((t_dec - int(t_dec)) * 100)
            tempo_rush_str = f"{mm:02d}:{ss:02d}.{cs:02d}"
            combate_ui.desenhar_barra_boss_combate(
                surface, 200, 26, 560, 12,
                self.inimigo_ref, getattr(self, "tempo_combate", 0.0), fontes_ui,
                modo_boss_rush=em_rush,
                boss_rush_idx=getattr(self, "sala_idx", 0),
                tempo_rush_str=tempo_rush_str
            )

        # 5. BANNER SUPERIOR DE AVISOS E TELEGRAFIAS
        if self.banner_msg:
            combate_ui.desenhar_banner_central(surface, self.banner_msg, self.banner_cor, fontes_ui, com_boss=tem_boss)

        # 5b. BRASÃO DE RANK S/A/B/C NA VITÓRIA DE COMBATE
        if em_vitoria and getattr(self, "resultado_rank", None):
            combate_ui.desenhar_painel_rank_combate(
                surface, self.resultado_rank,
                tempo_combate=getattr(self, "tempo_combate", 0.0),
                eh_boss=tem_boss
            )

        # 6. JANELA DE TELEGRAFIA E DEFESA
        if self.estado == "TURNO_INIMIGO":
            def_pos = ui_configurador.obter_posicao("janela_defesa") if ui_configurador else (166, 451)
            combate_ui.desenhar_reacao_defensiva(
                surface, def_pos[0], def_pos[1], 440, 68,
                self.tipo_golpe_atual(), fontes_ui
            )

        # 7. BADGE DISCRETO DE MODO AUTO (DINÂMICO COM INPUT MANAGER)
        r_auto = pygame.Rect(14, 508, 96, 22)
        ui_procedural.desenhar_moldura_gotica(surface, r_auto, chanfro=4, destacado=BOT.ativo, alpha=244, cantoneiras=False)
        if BOT.ativo:
            txt_auto = fontes_ui["micro"].render("AUTO: ON", True, ui_procedural.COR_OURO_VIVO)
            surface.blit(txt_auto, (r_auto.centerx - txt_auto.get_width() // 2, r_auto.centery - txt_auto.get_height() // 2))
        else:
            txt_auto = fontes_ui["micro"].render("AUTO", True, ui_procedural.COR_CINZA_TEXTO)
            ic_a = ui_procedural.desenhar_icone_botao(surface, r_auto.left + 22, r_auto.centery, "F2", escala=0.72)
            surface.blit(txt_auto, (ic_a.right + 5, r_auto.centery - txt_auto.get_height() // 2))

        # ==============================================================
        # 7. TEXTOS FLUTUANTES DE DANO, CURA E CRÍTICOS
        # ==============================================================
        for tf in self.textos_flutuantes:
            f_use = fontes_ui["menu"] if any(ch in tf["txt"] for ch in ("-", "+", "!", "★", "▲")) else fontes_ui["normal"]
            sombra_tf = f_use.render(tf["txt"], True, (10, 6, 8))
            render_tf = f_use.render(tf["txt"], True, tf["cor"])
            tx = int(tf.get("x", LARGURA_TELA // 2)) - render_tf.get_width() // 2
            ty = int(tf["y"])
            bg_tf = pygame.Surface((render_tf.get_width() + 10, render_tf.get_height() + 4), pygame.SRCALPHA)
            bg_tf.fill((10, 8, 14, 180))
            surface.blit(bg_tf, (tx - 5, ty - 2))
            surface.blit(sombra_tf, (tx + 1, ty + 1))
            surface.blit(render_tf, (tx, ty))

        if self.flash_alpha > 0 and self.flash_cor:
            f_surf = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
            f_surf.fill(self.flash_cor)
            f_surf.set_alpha(self.flash_alpha)
            surface.blit(f_surf, (0, 0))



