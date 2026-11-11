# -*- coding: utf-8 -*-
"""
Módulo de Interface Medieval Gótica em Pixel Art Procedural para ELOS DO VAZIO.

Gera e faz cache de superfícies de UI em baixa resolução com estética dark fantasy
autêntica (estilo Diablo 1, Castlevania SOTN, Dark Souls retro), escaladas com
Nearest-Neighbor (pygame.transform.scale) para preservar pixels nítidos e crocantes
em grade 2x2 ou 3x3.
"""

import math
import random
import pygame
import ui_procedural

# -----------------------------------------------------------------------------
# PALETAS DE CORES PIXEL ART MEDIEVAL
# -----------------------------------------------------------------------------
# Pedra de Castelo / Cripta
PEDRA_ESCURA   = (22, 19, 30)
PEDRA_GRAO_ESC = (16, 14, 22)
PEDRA_GRAO_CL  = (32, 28, 42)
PEDRA_LUZ      = (95, 88, 115)
PEDRA_SOMBRA   = (38, 32, 50)
BORDA_PRETA    = (8, 6, 12)

# Ouro Velho / Relíquia
OURO_BRILHO    = (255, 235, 120)
OURO_MEDIO     = (215, 175, 55)
OURO_SOMBRA    = (135, 95, 25)
OURO_ESCURO    = (75, 50, 15)

# Ferro Forjado
FERRO_LUZ      = (125, 120, 138)
FERRO_MEDIO    = (68, 64, 76)
FERRO_SOMBRA   = (32, 28, 38)
REBITE_LUZ     = (230, 225, 240)
REBITE_SOMBRA  = (20, 18, 25)

# Tapeçaria Real & Sangue
CARMESIM_FUNDO = (58, 22, 36)
CARMESIM_CLARO = (115, 36, 52)
PURPURA_FUNDO  = (48, 20, 58)
PURPURA_CLARO  = (92, 38, 110)
SANGUE_VIVO    = (215, 38, 48)
SANGUE_ESCURO  = (110, 18, 24)

# Pergaminho Envelhecido
PERG_FUNDO     = (42, 28, 18)
PERG_GRAO      = (55, 36, 22)
PERG_TEXTO     = (225, 205, 165)
PERG_LUZ       = (160, 125, 85)

# Alquimia & Magia
VERDE_ALQ      = (55, 195, 110)
VERDE_ALQ_LUZ  = (140, 245, 175)
VERDE_ALQ_ESC  = (20, 85, 45)
CIANO_RUNA     = (80, 225, 255)
CIANO_RUNA_ESC = (28, 95, 120)
AZUL_ETER      = (65, 140, 245)
AZUL_ETER_LUZ  = (165, 215, 255)

# -----------------------------------------------------------------------------
# DETECÇÃO DINÂMICA DE DISPOSITIVO DE ENTRADA (TECLADO VS CONTROLE XBOX)
# -----------------------------------------------------------------------------
_dispositivo_input = "TECLADO"


def definir_dispositivo_input(disp, nome_controle=""):
    global _dispositivo_input
    if disp == "CONTROLE":
        ui_procedural.INPUT_MANAGER.registrar_controle(nome_controle)
        _dispositivo_input = "CONTROLE"
    else:
        ui_procedural.INPUT_MANAGER.registrar_teclado()
        _dispositivo_input = "TECLADO"


def obter_dispositivo_input():
    return ui_procedural.INPUT_MANAGER.modo_input


def usar_controle():
    return ui_procedural.INPUT_MANAGER.usar_controle()


def tag_comando(acao):
    """
    Retorna o rótulo do comando adequado ao dispositivo ativo.
    Quando o comando estiver em uso, exibe os botões Xbox ou PlayStation automaticamente.
    Quando o teclado estiver em uso, exibe as teclas correspondentes.
    """
    c = usar_controle()
    eh_ps = c and (ui_procedural.INPUT_MANAGER.tipo_controle == ui_procedural.InputManager.TIPO_PLAYSTATION)
    bt_confirm = "(✕)" if eh_ps else "(A)"
    bt_cancel = "(○)" if eh_ps else "(B)"
    bt_sec = "(□)" if eh_ps else "(X)"
    bt_alt = "(△)" if eh_ps else "(Y)"
    bt_sh = "(L1/R1)" if eh_ps else "(LB/RB)"
    tags = {
        "alvos": bt_sh if c else "[A/D]",
        "alvos_alternar": f"{bt_sh} alternar" if c else "[A/D] alternar",
        "confirmar": bt_confirm if c else "[ENTER]",
        "confirmar_opcao": f"{bt_confirm}/{bt_sec} Confirmar" if c else "[ENTER/ESPAÇO] Confirmar",
        "cancelar": bt_cancel if c else "[ESC]",
        "voltar": f"{bt_cancel} Voltar" if c else "[ESC] Voltar",
        "atacar": bt_sec if c else "[Z]",
        "atacar_rotulo": f"{bt_sec} Atacar" if c else "[Z] Atacar",
        "pulo": bt_confirm if c else "[ESPAÇO]",
        "pulo_rotulo": f"{bt_confirm} PULAR" if c else "[ESPAÇO] PULAR",
        "parry": bt_sec if c else "[X]",
        "parry_rotulo": f"{bt_sec} PARRY" if c else "[X] PARRY",
        "desvio": bt_cancel if c else "[C]",
        "desvio_rotulo": f"{bt_cancel} DESVIO" if c else "[C] DESVIO",
        "interagir": bt_sec if c else "[E]",
        "itens": bt_alt if c else "[Q]",
        "defesa": bt_alt if c else "[Q]",
        "tela_cheia": "(SHARE)" if eh_ps else ("(BACK)" if c else "[F11]"),
        "reiniciar": bt_sec if c else "[R]",
        "renascer": bt_confirm if c else "[ESPAÇO]",
        "navegar": "(LS / D-PAD)" if c else "[W/S / SETAS]",
    }
    return tags.get(acao, "")

# -----------------------------------------------------------------------------
# MATRIZES DE ÍCONES PIXEL ART 16x16 (CORRIGIDAS E SIMÉTRICAS)
# -----------------------------------------------------------------------------
PALETA_ICONES = {
    ".": (0, 0, 0, 0),
    "#": (8, 6, 12, 255),
    "W": (245, 248, 255, 255),
    "S": (175, 185, 205, 255),
    "s": (95, 105, 120, 255),
    "G": (245, 215, 75, 255),
    "g": (195, 150, 40, 255),
    "d": (110, 75, 20, 255),
    "R": (225, 45, 55, 255),
    "r": (125, 20, 30, 255),
    "E": (65, 215, 125, 255),
    "e": (25, 95, 50, 255),
    "C": (85, 235, 255, 255),
    "c": (30, 110, 140, 255),
    "K": (235, 230, 210, 255),
    "k": (145, 135, 120, 255),
    "B": (145, 95, 55, 255),
    "b": (80, 48, 26, 255),
    "M": (140, 135, 150, 255),
    "m": (65, 60, 72, 255),
    "P": (205, 115, 255, 255),
    "p": (115, 45, 160, 255),
}

MATRIZES_ICONES = {
    # Espada Longa Diagonal Perfeitamente Simétrica (45 graus reais, sem dentes)
    "espada": [
        ".............###",
        "............#WW#",
        "...........#WSS#",
        "..........#WSS#.",
        ".........#WSS#..",
        "........#WSS#...",
        ".......#WSS#....",
        "..##..#WSS#.....",
        "..#G##WSS#......",
        "...#GGGg#.......",
        "....#bGGG#......",
        "...#Bb#GGG#.....",
        "..#Bb#..#G#.....",
        ".#Gd#....##.....",
        ".###............",
        "................",
    ],
    # Frasco Alquímico de Poção (Borda de vidro contínua e base simétrica)
    "pocao": [
        "......####......",
        ".....#BBBB#.....",
        "......#bb#......",
        ".....######.....",
        "....#WWssWW#....",
        "...#W......s#...",
        "..#W........s#..",
        "..#W..WWWW..s#..",
        "..#W.WEEEEW.s#..",
        "..#W.EEEEEE.s#..",
        "..#W.EEEEEEes#..",
        "..#W.eeeeeees#..",
        "...#Weeeeeees#..",
        "....#eeeeeees#..",
        ".....########...",
        "................",
    ],
    # Poção Vermelha de Vida (Mesma geometria simétrica do frasco alquímico)
    "pocao_vida": [
        "......####......",
        ".....#BBBB#.....",
        "......#bb#......",
        ".....######.....",
        "....#WWssWW#....",
        "...#W......s#...",
        "..#W........s#..",
        "..#W..WWWW..s#..",
        "..#W.WRRRRW.s#..",
        "..#W.RRRRRR.s#..",
        "..#W.RRRRRRrs#..",
        "..#W.rrrrrrrs#..",
        "...#Wrrrrrrrs#..",
        "....#rrrrrrrs#..",
        ".....########...",
        "................",
    ],
    # Cristal / Runa Octogonal de Éter (Facetas centralizadas 16x16)
    "cristal_ap": [
        "......####......",
        ".....#CWWC#.....",
        "....#CWWWWC#....",
        "...#CWWCCCCc#...",
        "..#CWWCCCCccc#..",
        "..#CCCccccccc#..",
        "..#CCCccccccc#..",
        "..#CCCccccccc#..",
        "..#CCCccccccc#..",
        "..#cccccccccc#..",
        "...#cccccccc#...",
        "....#cccccc#....",
        ".....#cccc#.....",
        "......####......",
        "................",
        "................",
    ],
    # Caveira Gótica Medieval (Crânio e dentes perfeitamente centralizados)
    "caveira": [
        "....########....",
        "...#KKKKKKKK#...",
        "..#KKWWKKKKKK#..",
        "..#KKWKKKKKKk#..",
        "..#KKKKKKKKKk#..",
        "..#K###KK###k#..",
        "..#K###KK###k#..",
        "..#KKKK##KKKK#..",
        "...#KKKKKKKK#...",
        "....#kkkkkk#....",
        "....#K#KK#K#....",
        "....#k#kk#k#....",
        ".....######.....",
        "................",
        "................",
        "................",
    ],
    # Escudo Templário com Cruz Centralizada (Eixo simétrico exato)
    "escudo": [
        "..############..",
        ".#GGGGGGGGGGGG#.",
        ".#GWWWW##WWWWG#.",
        ".#GWWWW##WWWsG#.",
        ".#GWWWW##WWWsG#.",
        ".#G##########G#.",
        ".#G##########G#.",
        ".#GWWWW##WWWsG#.",
        ".#GWWWW##WWWsG#.",
        "..#GWWW##WWsG#..",
        "...#GWW##WsG#...",
        "....#GW##sG#....",
        ".....#G##G#.....",
        "......#GG#......",
        ".......##.......",
        "................",
    ],
    # Coroa Dourada Real com Joias (Pontas alinhadas e base reta)
    "coroa": [
        "................",
        ".##....##....##.",
        "#GG#..#RR#..#GG#",
        "#GG#.#GGGG#.#GG#",
        "#GGG#GGGGGG#GGG#",
        "#GGGGGGGGGGGGGG#",
        ".#GGGGGGGGGGGG#.",
        ".#GG#C#GG#E#GG#.",
        ".#GGGGGGGGGGGG#.",
        ".#GGdddddddddd#.",
        "..############..",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Elmo Fechado de Cavaleiro Medieval (Visor em T simétrico)
    "elmo": [
        "....########....",
        "...#SSWWWWSS#...",
        "..#SSWSSSSSSs#..",
        "..#SSSSSSSSSs#..",
        "..#SSSSSSSSSs#..",
        "..#S########s#..",
        "..#S###SS###s#..",
        "..#SSSS##SSSs#..",
        "..#SSSS##SSSs#..",
        "..#SSSS##SSSs#..",
        "...#S#SSSS#s#...",
        "....########....",
        "................",
        "................",
        "................",
        "................",
    ],
    # Relógio de Bolso / Cronómetro Medieval (Círculo perfeito)
    "relogio": [
        "......####......",
        "......#GG#......",
        "....########....",
        "...#GGGGGGGG#...",
        "..#GGWWWWWWGG#..",
        ".#GGW..#...WGG#.",
        ".#GGW..#...WGG#.",
        ".#GGW..###.WGG#.",
        ".#GGW......WGG#.",
        ".#GGW......WGG#.",
        "..#GGWWWWWWGG#..",
        "...#GGGGGGGG#...",
        "....########....",
        "................",
        "................",
        "................",
    ],
    # Portão de Ferro Gótico (Corrigido para exatos 16x16 com lanças alinhadas)
    "portao": [
        ".#...#....#...#.",
        "#M#.#M#..#M#.#M#",
        "################",
        "#MM..MM..MM..MM#",
        "#MM..MM..MM..MM#",
        "################",
        "#MM..MM..MM..MM#",
        "#MM..MM..MM..MM#",
        "################",
        "#MM..MM..MM..MM#",
        "#MM..MM..MM..MM#",
        "################",
        "#M#.#M#..#M#.#M#",
        ".#...#....#...#.",
        "................",
        "................",
    ],
    # Runa de Magia / Necromancia (Chama Ectoplásmica / Éter)
    "magia": [
        ".......##.......",
        "......#PP#......",
        ".....#PWWP#.....",
        "....#PWWWWP#....",
        "...#PWWWWWWP#...",
        "...#PWW..WWP#...",
        "..#PWW....WWP#..",
        "..#PW......WP#..",
        "..#PP......PP#..",
        "...#pp....pp#...",
        "....#pp..pp#....",
        ".....#pppp#.....",
        "......#pp#......",
        ".......##.......",
        "................",
        "................",
    ],
    # Engrenagem / Roda Dentada de Ferro para Configurações (Simétrica 16x16)
    "engrenagem": [
        "......####......",
        ".....#MMMM#.....",
        "..##..#MM#..##..",
        ".#MM##########M#",
        ".#MM#MMWWMM#MMM#",
        "..##MWMGGMW#M##.",
        "...#MMG##GMM#...",
        "####M#G##G#M####",
        "####M#G##G#M####",
        "...#MMG##GMM#...",
        "..##MWMGGMW#M##.",
        ".#MM#MMWWMM#MMM#",
        ".#MM##########M#",
        "..##..#MM#..##..",
        ".....#MMMM#.....",
        "......####......",
    ],
}

# -----------------------------------------------------------------------------
# CACHE GLOBAL DE UI
# -----------------------------------------------------------------------------
_cache_ui = {}
_cache_icones = {}


def limpar_cache_ui():
    """Limpa o cache de texturas se necessário."""
    global _cache_ui, _cache_icones
    _cache_ui.clear()
    _cache_icones.clear()


# -----------------------------------------------------------------------------
# 1. ÍCONES PROCEDURAIS EM PIXEL ART
# -----------------------------------------------------------------------------
def obter_icone_pixel(tipo, escala=2):
    """
    Retorna uma Surface contendo o ícone em Pixel Art na escala especificada.
    Usa Nearest-Neighbor (pygame.transform.scale) para pixels puros.
    """
    chave = (tipo, escala)
    if chave in _cache_icones:
        return _cache_icones[chave]

    matriz = MATRIZES_ICONES.get(tipo, MATRIZES_ICONES["espada"])
    tam_base = 16
    surf_peq = pygame.Surface((tam_base, tam_base), pygame.SRCALPHA)

    for y, linha in enumerate(matriz):
        for x, char in enumerate(linha[:tam_base]):
            if char in PALETA_ICONES:
                cor = PALETA_ICONES[char]
                if cor[3] > 0:
                    surf_peq.set_at((x, y), cor)

    if escala > 1:
        surf_final = pygame.transform.scale(surf_peq, (tam_base * escala, tam_base * escala))
    else:
        surf_final = surf_peq

    _cache_icones[chave] = surf_final
    return surf_final


def desenhar_icone_pixel(surface, tipo, x, y, escala=2):
    """Desenha um ícone medieval em pixel art nas coordenadas dadas."""
    ico = obter_icone_pixel(tipo, escala)
    surface.blit(ico, (x, y))


# -----------------------------------------------------------------------------
# 2. PAINEL MEDIEVAL GÓTICO EM PIXEL ART
# -----------------------------------------------------------------------------
def _gerar_textura_painel_pixel(largura, altura, variante="pedra", ativo=False, borda_ouro=False, escala=2):
    """
    Desenha o painel em baixa resolução (largura // escala, altura // escala)
    com textura de pedra dithered, chanfros 3D e cantoneiras de ferro/ouro com rebites.
    """
    pw = max(8, largura // escala)
    ph = max(8, altura // escala)

    surf_low = pygame.Surface((pw, ph), pygame.SRCALPHA)

    if variante == "pergaminho":
        cor_base = PERG_FUNDO
        cor_grao_esc = (30, 20, 12)
        cor_grao_cl = PERG_GRAO
    elif variante == "carmesim":
        cor_base = CARMESIM_FUNDO if not ativo else PURPURA_FUNDO
        cor_grao_esc = (42, 14, 26)
        cor_grao_cl = CARMESIM_CLARO if not ativo else PURPURA_CLARO
    else:  # "pedra" padrão
        cor_base = PEDRA_ESCURA
        cor_grao_esc = PEDRA_GRAO_ESC
        cor_grao_cl = PEDRA_GRAO_CL

    surf_low.fill(cor_base)

    # Aplica granulação/dithering medieval de pedra talhada
    for gy in range(2, ph - 2):
        for gx in range(2, pw - 2):
            val = (gx * 7 + gy * 13 + (gx ^ gy)) % 11
            if val == 0:
                surf_low.set_at((gx, gy), cor_grao_esc)
            elif val == 5:
                surf_low.set_at((gx, gy), cor_grao_cl)

    # Bordas Chanfradas em Degraus de Pixel Art (Bevel 3D)
    for cy in range(2):
        for cx in range(2 - cy):
            surf_low.set_at((cx, cy), (0, 0, 0, 0))
            surf_low.set_at((pw - 1 - cx, cy), (0, 0, 0, 0))
            surf_low.set_at((cx, ph - 1 - cy), (0, 0, 0, 0))
            surf_low.set_at((pw - 1 - cx, ph - 1 - cy), (0, 0, 0, 0))

    cor_contorno = BORDA_PRETA
    if ativo or borda_ouro:
        cor_luz = OURO_BRILHO
        cor_sombra = OURO_SOMBRA
    else:
        cor_luz = PEDRA_LUZ
        cor_sombra = PEDRA_SOMBRA

    # Linhas de contorno externo preto
    for x in range(2, pw - 2):
        surf_low.set_at((x, 0), cor_contorno)
        surf_low.set_at((x, ph - 1), cor_contorno)
    for y in range(2, ph - 2):
        surf_low.set_at((0, y), cor_contorno)
        surf_low.set_at((pw - 1, y), cor_contorno)

    # Chanfros diagonais pretos nos cantos
    surf_low.set_at((1, 1), cor_contorno)
    surf_low.set_at((pw - 2, 1), cor_contorno)
    surf_low.set_at((1, ph - 2), cor_contorno)
    surf_low.set_at((pw - 2, ph - 2), cor_contorno)

    # Chanfro Interno 3D (Luz no topo/esquerda, Sombra na base/direita)
    for x in range(2, pw - 2):
        surf_low.set_at((x, 1), cor_luz)
        surf_low.set_at((x, ph - 2), cor_sombra)
    for y in range(2, ph - 2):
        surf_low.set_at((1, y), cor_luz)
        surf_low.set_at((pw - 2, y), cor_sombra)

    # Cantoneiras Metálicas em "L" & Rebites nos 4 cantos
    if pw >= 16 and ph >= 16:
        cor_ferro = OURO_MEDIO if (ativo or borda_ouro) else FERRO_MEDIO
        cor_f_luz = OURO_BRILHO if (ativo or borda_ouro) else FERRO_LUZ
        cor_f_som = OURO_SOMBRA if (ativo or borda_ouro) else FERRO_SOMBRA

        braco = min(6, min(pw, ph) // 4)

        # Cantoneira Top-Left
        for i in range(2, 2 + braco):
            surf_low.set_at((i, 2), cor_f_luz)
            surf_low.set_at((2, i), cor_f_luz)
            surf_low.set_at((i, 3), cor_ferro)
            surf_low.set_at((3, i), cor_ferro)
        surf_low.set_at((3, 3), REBITE_LUZ)
        surf_low.set_at((4, 3), REBITE_SOMBRA)
        surf_low.set_at((3, 4), cor_f_som)
        surf_low.set_at((4, 4), BORDA_PRETA)

        # Cantoneira Top-Right
        for i in range(2, 2 + braco):
            surf_low.set_at((pw - 1 - i, 2), cor_f_luz)
            surf_low.set_at((pw - 3, i), cor_ferro)
            surf_low.set_at((pw - 1 - i, 3), cor_ferro)
            surf_low.set_at((pw - 4, i), cor_f_som)
        surf_low.set_at((pw - 4, 3), REBITE_LUZ)
        surf_low.set_at((pw - 5, 3), REBITE_SOMBRA)
        surf_low.set_at((pw - 4, 4), cor_f_som)
        surf_low.set_at((pw - 5, 4), BORDA_PRETA)

        # Cantoneira Bottom-Left
        for i in range(2, 2 + braco):
            surf_low.set_at((i, ph - 3), cor_ferro)
            surf_low.set_at((2, ph - 1 - i), cor_f_luz)
            surf_low.set_at((i, ph - 4), cor_f_som)
            surf_low.set_at((3, ph - 1 - i), cor_ferro)
        surf_low.set_at((3, ph - 4), REBITE_LUZ)
        surf_low.set_at((4, ph - 4), REBITE_SOMBRA)
        surf_low.set_at((3, ph - 5), cor_f_som)
        surf_low.set_at((4, ph - 5), BORDA_PRETA)

        # Cantoneira Bottom-Right
        for i in range(2, 2 + braco):
            surf_low.set_at((pw - 1 - i, ph - 3), cor_f_som)
            surf_low.set_at((pw - 3, ph - 1 - i), cor_f_som)
            surf_low.set_at((pw - 1 - i, ph - 4), cor_ferro)
            surf_low.set_at((pw - 4, ph - 1 - i), cor_ferro)
        surf_low.set_at((pw - 4, ph - 4), REBITE_LUZ)
        surf_low.set_at((pw - 5, ph - 4), REBITE_SOMBRA)
        surf_low.set_at((pw - 4, ph - 5), cor_f_som)
        surf_low.set_at((pw - 5, ph - 5), BORDA_PRETA)

    surf_final = pygame.transform.scale(surf_low, (largura, altura))
    return surf_final


def desenhar_painel_medieval(surface, rect, variante="pedra", ativo=False, borda_ouro=False, alpha=255):
    """
    Desenha um painel medieval gótico procedural em Pixel Art com cantoneiras de metal e chanfros.
    Faz cache da textura pelo tamanho e variante.
    """
    if isinstance(rect, (tuple, list)):
        rect = pygame.Rect(rect)
    w = max(16, int(rect.width))
    h = max(16, int(rect.height))

    chave = ("painel", w, h, variante, ativo, borda_ouro)
    if chave not in _cache_ui:
        _cache_ui[chave] = _gerar_textura_painel_pixel(w, h, variante=variante, ativo=ativo, borda_ouro=borda_ouro, escala=2)

    tex = _cache_ui[chave]
    if alpha < 255:
        tex_a = tex.copy()
        tex_a.set_alpha(alpha)
        surface.blit(tex_a, rect.topleft)
    else:
        surface.blit(tex, rect.topleft)


# -----------------------------------------------------------------------------
# 3. BOTÃO MEDIEVAL EM PIXEL ART COM PONTAS DE ESPADA LATERAIS
# -----------------------------------------------------------------------------
def _gerar_textura_botao_pixel(largura, altura, selecionado=False, desabilitado=False, escala=2):
    """
    Gera a placa de botão com chanfros acentuados em degraus e acabamento medieval.
    """
    pw = max(8, largura // escala)
    ph = max(8, altura // escala)
    surf_low = pygame.Surface((pw, ph), pygame.SRCALPHA)

    if desabilitado:
        cor_base = (24, 20, 24)
        cor_luz = (55, 50, 58)
        cor_sombra = (15, 12, 16)
    elif selecionado:
        cor_base = CARMESIM_FUNDO
        cor_luz = OURO_BRILHO
        cor_sombra = OURO_SOMBRA
    else:
        cor_base = (34, 26, 36)
        cor_luz = (115, 105, 130)
        cor_sombra = (22, 18, 25)

    surf_low.fill(cor_base)

    # Chanfros nos 4 cantos (3 pixels de chanfro em degraus)
    for step in range(3):
        for cut in range(3 - step):
            surf_low.set_at((cut, step), (0, 0, 0, 0))
            surf_low.set_at((pw - 1 - cut, step), (0, 0, 0, 0))
            surf_low.set_at((cut, ph - 1 - step), (0, 0, 0, 0))
            surf_low.set_at((pw - 1 - cut, ph - 1 - step), (0, 0, 0, 0))

    # Borda externa preta
    for x in range(3, pw - 3):
        surf_low.set_at((x, 0), BORDA_PRETA)
        surf_low.set_at((x, ph - 1), BORDA_PRETA)
    for y in range(3, ph - 3):
        surf_low.set_at((0, y), BORDA_PRETA)
        surf_low.set_at((pw - 1, y), BORDA_PRETA)

    # Cantos diagonais pretos
    for step in range(3):
        surf_low.set_at((3 - step, step), BORDA_PRETA)
        surf_low.set_at((pw - 4 + step, step), BORDA_PRETA)
        surf_low.set_at((3 - step, ph - 1 - step), BORDA_PRETA)
        surf_low.set_at((pw - 4 + step, ph - 1 - step), BORDA_PRETA)

    # Bevel metálico iluminado (Top/Left) e Sombreado (Bottom/Right)
    for x in range(3, pw - 3):
        surf_low.set_at((x, 1), cor_luz)
        surf_low.set_at((x, ph - 2), cor_sombra)
    for y in range(3, ph - 3):
        surf_low.set_at((1, y), cor_luz)
        surf_low.set_at((pw - 2, y), cor_sombra)

    # Rebites de ferro nos 4 cantos internos da placa
    for rx, ry in [(4, 3), (pw - 5, 3), (4, ph - 4), (pw - 5, ph - 4)]:
        surf_low.set_at((rx, ry), OURO_BRILHO if selecionado else REBITE_LUZ)
        surf_low.set_at((rx + 1, ry), OURO_SOMBRA if selecionado else REBITE_SOMBRA)

    surf_final = pygame.transform.scale(surf_low, (largura, altura))
    return surf_final


def desenhar_botao_medieval(surface, rect, texto, fonte, selecionado=False, desabilitado=False, icone=None):
    """
    Desenha um botão com placa medieval chanfrada em pixel art.
    Quando selecionado=True, exibe borda de ouro reluzente e manoplas/pontas de espada
    em pixel art apontando para dentro nas laterais.
    """
    if isinstance(rect, (tuple, list)):
        rect = pygame.Rect(rect)
    w = max(32, int(rect.width))
    h = max(20, int(rect.height))

    chave = ("botao", w, h, selecionado, desabilitado)
    if chave not in _cache_ui:
        _cache_ui[chave] = _gerar_textura_botao_pixel(w, h, selecionado=selecionado, desabilitado=desabilitado, escala=2)

    surface.blit(_cache_ui[chave], rect.topleft)

    # Pontas de Espada / Manoplas em Pixel Art apontando para dentro nas laterais
    if selecionado:
        lx = rect.left + 12
        ly = rect.centery
        pts_esq = [(lx - 8, ly - 6), (lx, ly), (lx - 8, ly + 6), (lx - 5, ly)]
        pygame.draw.polygon(surface, OURO_BRILHO, pts_esq)
        pygame.draw.polygon(surface, OURO_SOMBRA, pts_esq, 1)

        rx = rect.right - 12
        pts_dir = [(rx + 8, ly - 6), (rx, ly), (rx + 8, ly + 6), (rx + 5, ly)]
        pygame.draw.polygon(surface, OURO_BRILHO, pts_dir)
        pygame.draw.polygon(surface, OURO_SOMBRA, pts_dir, 1)

    deslocamento_x = 0
    if icone:
        surf_ico = obter_icone_pixel(icone, escala=2)
        surface.blit(surf_ico, (rect.left + 14, rect.centery - surf_ico.get_height() // 2))
        deslocamento_x = 16

    if desabilitado:
        cor_txt = (110, 100, 110)
    elif selecionado:
        cor_txt = (255, 245, 215)
    else:
        cor_txt = PERG_TEXTO

    txt_sombra = fonte.render(texto, True, BORDA_PRETA)
    txt_surf = fonte.render(texto, True, cor_txt)
    tx = rect.centerx - txt_surf.get_width() // 2 + deslocamento_x
    ty = rect.centery - txt_surf.get_height() // 2

    surface.blit(txt_sombra, (tx + 2, ty + 2))
    surface.blit(txt_surf, (tx, ty))


# -----------------------------------------------------------------------------
# 4. BARRA DE STATUS MEDIEVAL COM TUBO ALQUÍMICO E DIVISÓRIAS
# -----------------------------------------------------------------------------
def desenhar_barra_medieval(surface, rect, valor, maximo=1.0, tipo="hp"):
    """
    Desenha uma barra medieval com moldura de ferro/ouro forjado, ponteiras em pixel art,
    fundo de vidro alquímico escuro (14, 10, 20), líquido com faixa de reflexo brilhante no topo,
    e divisórias de metal sobre o tubo.
    """
    if isinstance(rect, (tuple, list)):
        rect = pygame.Rect(rect)
    w = max(24, int(rect.width))
    h = max(10, int(rect.height))

    if maximo <= 0:
        maximo = 1.0
    ratio = max(0.0, min(1.0, float(valor) / float(maximo)))

    if tipo == "boss":
        cor_liq = SANGUE_VIVO
        cor_luz = (255, 110, 120)
        cor_sombra = SANGUE_ESCURO
        cor_moldura = OURO_MEDIO
        cor_moldura_luz = OURO_BRILHO
    elif tipo == "ap" or tipo == "eter":
        cor_liq = AZUL_ETER
        cor_luz = AZUL_ETER_LUZ
        cor_sombra = (24, 60, 140)
        cor_moldura = FERRO_MEDIO
        cor_moldura_luz = FERRO_LUZ
    else:  # "hp" normal
        if ratio > 0.5:
            cor_liq = VERDE_ALQ
            cor_luz = VERDE_ALQ_LUZ
            cor_sombra = VERDE_ALQ_ESC
        elif ratio > 0.25:
            cor_liq = OURO_MEDIO
            cor_luz = OURO_BRILHO
            cor_sombra = OURO_SOMBRA
        else:
            cor_liq = SANGUE_VIVO
            cor_luz = (255, 120, 130)
            cor_sombra = SANGUE_ESCURO
        cor_moldura = FERRO_MEDIO
        cor_moldura_luz = FERRO_LUZ

    # 1. Fundo do tubo de vidro escuro
    fundo_vidro = pygame.Rect(rect.x + 4, rect.y + 2, w - 8, h - 4)
    pygame.draw.rect(surface, (14, 10, 20), fundo_vidro)

    # 2. Líquido com Brilho Superior e Sombra na Base
    larg_liq = int(fundo_vidro.width * ratio)
    if larg_liq > 0:
        liq_rect = pygame.Rect(fundo_vidro.x, fundo_vidro.y, larg_liq, fundo_vidro.height)
        pygame.draw.rect(surface, cor_liq, liq_rect)
        alt_luz = max(2, fundo_vidro.height // 3)
        pygame.draw.rect(surface, cor_luz, (liq_rect.x, liq_rect.y, larg_liq, alt_luz))
        pygame.draw.rect(surface, cor_sombra, (liq_rect.x, liq_rect.bottom - 2, larg_liq, 2))

    # 3. Moldura Externa de Metal Forjado com Cantos Chanfrados
    pygame.draw.rect(surface, BORDA_PRETA, rect, 2)
    pygame.draw.line(surface, cor_moldura_luz, (rect.left + 2, rect.top + 1), (rect.right - 2, rect.top + 1))
    pygame.draw.line(surface, cor_moldura_luz, (rect.left + 1, rect.top + 2), (rect.left + 1, rect.bottom - 2))
    pygame.draw.line(surface, cor_moldura, (rect.left + 2, rect.bottom - 2), (rect.right - 2, rect.bottom - 2))
    pygame.draw.line(surface, cor_moldura, (rect.right - 2, rect.top + 2), (rect.right - 2, rect.bottom - 2))

    # 4. Ponteiras Ornamentadas nos 4 Cantos (Rebites 2x2)
    for px_c, py_c in [(rect.left, rect.top), (rect.right - 4, rect.top),
                       (rect.left, rect.bottom - 4), (rect.right - 4, rect.bottom - 4)]:
        pygame.draw.rect(surface, BORDA_PRETA, (px_c, py_c, 4, 4))
        pygame.draw.rect(surface, OURO_BRILHO if tipo == "boss" else REBITE_LUZ, (px_c + 1, py_c + 1, 2, 2))

    # 5. Divisórias Verticais de Metal Sobre o Tubo
    passo = 10 if (tipo == "boss" or w > 200) else 5
    for seg in range(1, passo):
        dx = fundo_vidro.x + int(fundo_vidro.width * (seg / float(passo)))
        pygame.draw.line(surface, BORDA_PRETA, (dx, rect.top + 1), (dx, rect.bottom - 1), 2)
        pygame.draw.line(surface, cor_moldura, (dx, rect.top + 2), (dx, rect.bottom - 2), 1)

    # 6. Se for barra de Boss, desenha coroa/caveira ornamentada no topo central
    if tipo == "boss" and w >= 180:
        cr_x = rect.centerx - 16
        cr_y = rect.top - 16
        desenhar_icone_pixel(surface, "coroa" if ratio <= 0 else "caveira", cr_x, cr_y, escala=2)


# -----------------------------------------------------------------------------
# 5. BANNER DE PEDRA RACHADA COM CORRENTES VERTICAIS (TÍTULO DO MENU)
# -----------------------------------------------------------------------------
def desenhar_banner_corrente(surface, rect, texto=None, fonte=None, logo_surf=None):
    """
    Desenha uma placa/estandarte de pedra gótica suspensa por duas correntes
    de ferro em pixel art que descem do teto (y=0).
    """
    if isinstance(rect, (tuple, list)):
        rect = pygame.Rect(rect)

    # 1. Correntes de Ferro Verticais em Pixel Art
    for corrente_x in (rect.left + 36, rect.right - 44):
        y_atual = 0
        while y_atual < rect.top + 6:
            pygame.draw.rect(surface, BORDA_PRETA, (corrente_x - 1, y_atual, 8, 10))
            pygame.draw.rect(surface, FERRO_MEDIO, (corrente_x, y_atual + 1, 6, 8))
            pygame.draw.rect(surface, (12, 10, 16), (corrente_x + 2, y_atual + 2, 2, 6))
            surface.set_at((corrente_x + 1, y_atual + 1), FERRO_LUZ)
            y_atual += 8

        # Argola de fixação na placa
        pygame.draw.circle(surface, BORDA_PRETA, (corrente_x + 3, rect.top + 4), 6)
        pygame.draw.circle(surface, OURO_MEDIO, (corrente_x + 3, rect.top + 4), 4, 2)
        pygame.draw.circle(surface, OURO_BRILHO, (corrente_x + 2, rect.top + 3), 1)

    # 2. Placa de Pedra Gótica Rachada
    desenhar_painel_medieval(surface, rect, variante="pedra", ativo=True, borda_ouro=True)

    # 3. Rachaduras Procedurais na Pedra
    pts_rachadura = [
        (rect.left + 60, rect.top + 10),
        (rect.left + 72, rect.top + 24),
        (rect.left + 68, rect.top + 38),
        (rect.left + 84, rect.top + 46),
    ]
    pygame.draw.lines(surface, BORDA_PRETA, False, pts_rachadura, 2)
    pygame.draw.lines(surface, PEDRA_SOMBRA, False, [(x + 1, y + 1) for x, y in pts_rachadura], 1)

    pts_rachadura2 = [
        (rect.right - 90, rect.bottom - 12),
        (rect.right - 105, rect.bottom - 26),
        (rect.right - 98, rect.bottom - 42),
    ]
    pygame.draw.lines(surface, BORDA_PRETA, False, pts_rachadura2, 2)
    pygame.draw.lines(surface, PEDRA_SOMBRA, False, [(x + 1, y + 1) for x, y in pts_rachadura2], 1)

    # 4. Conteúdo (Logo ou Texto)
    if logo_surf:
        surface.blit(logo_surf, (rect.centerx - logo_surf.get_width() // 2,
                                 rect.centery - logo_surf.get_height() // 2))
    elif texto and fonte:
        txt_sombra = fonte.render(texto, True, BORDA_PRETA)
        txt_surf = fonte.render(texto, True, OURO_BRILHO)
        surface.blit(txt_sombra, (rect.centerx - txt_surf.get_width() // 2 + 2,
                                  rect.centery - txt_surf.get_height() // 2 + 2))
        surface.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2,
                                rect.centery - txt_surf.get_height() // 2))


# -----------------------------------------------------------------------------
# 6. MIRA RÚNICA MEDIEVAL DUPLA PARA QTE
# -----------------------------------------------------------------------------
def desenhar_mira_runica_qte(surface, centro_x, centro_y, progresso, tamanho_alvo=38):
    """
    Desenha uma mira rúnica medieval dupla com vértices detalhados e runas nos cantos
    para o QTE de ataque e parry do jogador.
    """
    na_zona = 0.74 <= progresso <= 1.05
    cor_alvo = OURO_BRILHO if na_zona else OURO_MEDIO

    ta = tamanho_alvo
    pts_alvo = [
        (centro_x, centro_y - ta),
        (centro_x + ta // 3, centro_y - ta // 3),
        (centro_x + ta, centro_y),
        (centro_x + ta // 3, centro_y + ta // 3),
        (centro_x, centro_y + ta),
        (centro_x - ta // 3, centro_y + ta // 3),
        (centro_x - ta, centro_y),
        (centro_x - ta // 3, centro_y - ta // 3),
    ]
    pygame.draw.polygon(surface, BORDA_PRETA, pts_alvo, 5)
    pygame.draw.polygon(surface, cor_alvo, pts_alvo, 2)

    for dx, dy in [(0, -ta - 8), (0, ta + 8), (-ta - 8, 0), (ta + 8, 0)]:
        pygame.draw.circle(surface, BORDA_PRETA, (centro_x + dx, centro_y + dy), 4)
        pygame.draw.circle(surface, OURO_BRILHO, (centro_x + dx, centro_y + dy), 2)

    tam_ext = int(120 * (1.0 - min(1.1, progresso)) + ta)
    cor_ext = CIANO_RUNA if na_zona else PERG_LUZ

    pts_ext = [
        (centro_x, centro_y - tam_ext),
        (centro_x + tam_ext, centro_y),
        (centro_x, centro_y + tam_ext),
        (centro_x - tam_ext, centro_y),
    ]
    pygame.draw.polygon(surface, BORDA_PRETA, pts_ext, 4)
    pygame.draw.polygon(surface, cor_ext, pts_ext, 2)


# -----------------------------------------------------------------------------
# 7. CHÃO DE ARENA MEDIEVAL GÓTICA EM LAJES DE PEDRA PIXEL ART (CANTARIA)
# -----------------------------------------------------------------------------
def desenhar_chao_arena_medieval(surface, cam, sala_idx=0, is_boss=False):
    """
    Renderiza um amplo e autêntico pátio de combate gótico em lajes de pedra talhada (Pixel Art).
    """
    if sala_idx in (1, 4):  # Bosque / Floresta (Pedra ancestral com musgo húmido)
        pedra_tons = [(26, 32, 26), (21, 26, 21), (32, 38, 30), (18, 23, 18), (28, 34, 26)]
        cor_luz = (75, 105, 70)
        cor_sombra = (11, 15, 11)
        cor_junta = (7, 10, 7)
        cor_fenda = (90, 150, 80)
        cor_runa = (100, 195, 120)
        cor_borda = (115, 155, 90)
    elif sala_idx == 2:     # Fortaleza de Ferro (Basalto escuro e ferro forjado)
        pedra_tons = [(30, 33, 42), (23, 26, 33), (38, 42, 52), (18, 20, 26), (27, 30, 38)]
        cor_luz = (105, 120, 148)
        cor_sombra = (12, 14, 18)
        cor_junta = (7, 8, 12)
        cor_fenda = (195, 165, 90)
        cor_runa = (135, 185, 235)
        cor_borda = (175, 145, 85)
    elif sala_idx == 5:     # Catedral dos Esquecidos (Mármore negro e veios de ouro divino)
        pedra_tons = [(40, 34, 46), (32, 28, 38), (48, 42, 55), (26, 22, 32), (38, 32, 44)]
        cor_luz = (155, 140, 175)
        cor_sombra = (16, 14, 22)
        cor_junta = (9, 7, 12)
        cor_fenda = (235, 195, 80)
        cor_runa = (245, 215, 105)
        cor_borda = (235, 195, 85)
    elif sala_idx == 6:     # Abismo Carmesim (Obsidiana vulcânica e magma)
        pedra_tons = [(34, 16, 22), (25, 12, 18), (42, 20, 28), (19, 8, 13), (30, 14, 20)]
        cor_luz = (135, 50, 65)
        cor_sombra = (14, 6, 9)
        cor_junta = (8, 3, 5)
        cor_fenda = (245, 50, 75)
        cor_runa = (245, 75, 105)
        cor_borda = (220, 45, 70)
    else:                   # Cripta Gótica Ancestral (Padrão: Salas 0, 3)
        pedra_tons = [(28, 24, 36), (22, 18, 28), (35, 29, 44), (17, 14, 22), (25, 21, 33)]
        cor_luz = (92, 85, 115)
        cor_sombra = (12, 10, 18)
        cor_junta = (7, 5, 10)
        cor_fenda = (175, 135, 245) if is_boss else (80, 105, 145)
        cor_runa = (195, 155, 245) if is_boss else (100, 140, 200)
        cor_borda = (215, 175, 85) if is_boss else (98, 88, 118)

    linhas_y = [215, 246, 286, 336, 396, 464, 532]

    def projetar(x_mundo, wy):
        fator = 0.86 + 0.26 * ((wy - 215) / (532 - 215))
        wx = 480 + (x_mundo - 480) * fator
        if cam and hasattr(cam, "transformar_ponto"):
            return cam.transformar_ponto(wx, wy)
        return (int(wx), int(wy))

    # 1. Base sólida com argamassa escura profunda
    p_tl = projetar(-80, 215)
    p_tr = projetar(1040, 215)
    p_br = projetar(1040, 532)
    p_bl = projetar(-80, 532)
    pygame.draw.polygon(surface, cor_junta, [p_tl, p_tr, p_br, p_bl])

    # 2. Fiadas de lajes de cantaria medieval com running bond
    largura_laje = 92
    num_fiadas = len(linhas_y) - 1

    for r in range(num_fiadas):
        y1 = linhas_y[r]
        y2 = linhas_y[r + 1]

        offset_x = (r % 2) * (largura_laje // 2)
        x_atual = -100 + offset_x
        col = 0

        while x_atual < 1060:
            x1 = x_atual
            x2 = x_atual + largura_laje - 2

            pt_tl = projetar(x1, y1 + 1)
            pt_tr = projetar(x2, y1 + 1)
            pt_br = projetar(x2, y2 - 1)
            pt_bl = projetar(x1, y2 - 1)

            idx_tom = (r * 11 + col * 7) % len(pedra_tons)
            tom_laje = pedra_tons[idx_tom]

            pygame.draw.polygon(surface, tom_laje, [pt_tl, pt_tr, pt_br, pt_bl])

            # Chanfro 3D de luz (topo e esquerda)
            pygame.draw.line(surface, cor_luz, pt_tl, pt_tr, 2)
            pygame.draw.line(surface, cor_luz, pt_tl, pt_bl, 2)

            # Chanfro 3D de sombra (fundo e direita)
            pygame.draw.line(surface, cor_sombra, pt_bl, pt_br, 2)
            pygame.draw.line(surface, cor_sombra, pt_tr, pt_br, 2)

            # Dithering e textura de grãos de granito
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            p_g1 = projetar(cx - 10, cy - 2)
            p_g2 = projetar(cx + 12, cy + 3)
            p_g3 = projetar(cx + 1, cy - 5)
            pygame.draw.circle(surface, cor_luz, p_g1, 1)
            pygame.draw.circle(surface, cor_sombra, p_g2, 1)
            pygame.draw.circle(surface, cor_luz, p_g3, 1)

            # Fissuras e fendas místicas entalhadas pelo combate
            det = (r * 23 + col * 17) % 9
            if det == 1:
                p_r1 = projetar(x1 + 12, y1 + 3)
                p_r2 = projetar(cx - 2, cy)
                p_r3 = projetar(cx + 10, y2 - 4)
                pygame.draw.lines(surface, cor_junta, False, [p_r1, p_r2, p_r3], 2)
                pygame.draw.line(surface, cor_luz, (p_r1[0] + 1, p_r1[1]), (p_r2[0] + 1, p_r2[1]), 1)
            elif det == 3 and r >= 1:
                p_f1 = projetar(x1 + 15, y1 + 4)
                p_f2 = projetar(x2 - 16, y2 - 4)
                pygame.draw.line(surface, cor_fenda, p_f1, p_f2, 1)

            x_atual += largura_laje
            col += 1

    # 3. Grande Círculo de Duelo / Selo Rúnico de Pedra no Centro
    centro_runa_x = 480
    centro_runa_y = 350
    c_proj = projetar(centro_runa_x, centro_runa_y)
    zoom_val = getattr(cam, "zoom", 1.0) if cam else 1.0
    raio_x = int(195 * zoom_val)
    raio_y = int(58 * zoom_val)

    if raio_x > 20 and raio_y > 10:
        s_runa = pygame.Surface((raio_x * 2 + 10, raio_y * 2 + 10), pygame.SRCALPHA)
        pygame.draw.ellipse(s_runa, (*cor_junta, 180), (5, 5, raio_x * 2, raio_y * 2), 4)
        pygame.draw.ellipse(s_runa, (*cor_runa, 120), (5, 5, raio_x * 2, raio_y * 2), 2)
        irx, iry = int(raio_x * 0.72), int(raio_y * 0.72)
        ix, iy = raio_x - irx + 5, raio_y - iry + 5
        pygame.draw.ellipse(s_runa, (*cor_runa, 85), (ix, iy, irx * 2, iry * 2), 1)
        for k in range(8):
            ang = k * (math.pi / 4)
            gx = raio_x + 5 + int(raio_x * 0.86 * math.cos(ang))
            gy = raio_y + 5 + int(raio_y * 0.86 * math.sin(ang))
            pygame.draw.circle(s_runa, (*cor_runa, 145), (gx, gy), 2)
        surface.blit(s_runa, (c_proj[0] - raio_x - 5, c_proj[1] - raio_y - 5))

    # 4. Degrau Frontal 3D (Plinto maciço de cantaria na borda inferior)
    wy_topo = 532
    wy_base = 556
    larg_bloco_frontal = 80
    tilt_val = getattr(cam, "tilt", 0) if cam else 0

    for x in range(-80, 1040, larg_bloco_frontal):
        pt_f_tl = projetar(x + 1, wy_topo)
        pt_f_tr = projetar(x + larg_bloco_frontal - 1, wy_topo)
        if cam and hasattr(cam, "transformar_ponto"):
            pt_f_br = cam.transformar_ponto(pt_f_tr[0] if tilt_val == 0 else x + larg_bloco_frontal, wy_base)
            pt_f_bl = cam.transformar_ponto(pt_f_tl[0] if tilt_val == 0 else x, wy_base)
        else:
            pt_f_br = (pt_f_tr[0], wy_base)
            pt_f_bl = (pt_f_tl[0], wy_base)

        tom_face = (max(7, pedra_tons[0][0] - 12), max(6, pedra_tons[0][1] - 12), max(10, pedra_tons[0][2] - 12))
        pygame.draw.polygon(surface, tom_face, [pt_f_tl, pt_f_tr, pt_f_br, pt_f_bl])
        pygame.draw.polygon(surface, cor_junta, [pt_f_tl, pt_f_tr, pt_f_br, pt_f_bl], 2)
        pygame.draw.line(surface, cor_sombra, pt_f_bl, pt_f_br, 2)
        pygame.draw.line(surface, cor_luz, pt_f_tl, pt_f_tr, 3)

    # 5. Friso e arremate superior da arena
    pt_top_l = projetar(-80, 215)
    pt_top_r = projetar(1040, 215)
    pygame.draw.line(surface, cor_junta, pt_top_l, pt_top_r, 4)
    pygame.draw.line(surface, cor_borda, (pt_top_l[0], pt_top_l[1] + 1), (pt_top_r[0], pt_top_r[1] + 1), 2)

    # 6. Bordas laterais de contenção
    pt_lat_tl = projetar(-80, 215)
    pt_lat_bl = projetar(-80, wy_base)
    pt_lat_tr = projetar(1040, 215)
    pt_lat_br = projetar(1040, wy_base)
    pygame.draw.line(surface, cor_borda, pt_lat_tl, pt_lat_bl, 3)
    pygame.draw.line(surface, cor_borda, pt_lat_tr, pt_lat_br, 3)
