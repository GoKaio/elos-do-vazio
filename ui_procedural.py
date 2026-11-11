# -*- coding: utf-8 -*-
"""Biblioteca procedural modular de UI Dark Fantasy Gótica (Elos do Vazio)."""

import math
import pygame

# Paleta Gótica Padronizada
COR_EBANO_FUNDO        = (15, 15, 26)       # #0F0F1A
COR_EBANO_HUD          = (11, 15, 25)       # #0B0F19
COR_EBANO_PAINEL       = (22, 22, 36)       # #161624
COR_LATAO_BORDA        = (217, 119, 6)      # #D97706
COR_OURO_BRILHO        = (245, 158, 11)     # #F59E0B
COR_OURO_VIVO          = (253, 230, 138)    # #FDE68A
COR_OURO_DIVISOR       = (180, 83, 9)       # #B45309
COR_OURO_ESCURO        = (120, 53, 15)      # #78350F

COR_METAL_NEUTRO       = (34, 31, 45)       # #221F2D
COR_METAL_NEUTRO_ALT   = (30, 27, 38)       # #1E1B26
COR_METAL_BORDA        = (63, 57, 81)       # #3F3951
COR_VINHO_ESC          = (42, 14, 26)       # #2A0E1A
COR_VINHO_VIVO         = (59, 13, 31)       # #3B0D1F

COR_MARFIM_CRANIO      = (241, 245, 249)    # #F1F5F9
COR_BRANCO_PEROLA      = (248, 250, 252)    # #F8FAFC
COR_CINZA_TEXTO        = (148, 163, 184)    # #94A3B8
COR_REBITE             = (148, 163, 184)
COR_REBITE_LUZ         = (226, 232, 240)

COR_AZUL_ETER          = (56, 189, 248)     # #38BDF8
COR_AZUL_ETER_CLARO    = (224, 242, 254)    # #E0F2FE
COR_AZUL_ETER_GLOW     = (14, 165, 233)     # #0EA5E9
COR_ESMERALDA_VIDA     = (34, 197, 94)      # #22C55E
COR_ESMERALDA_SOMB     = (21, 128, 61)      # #15803D
COR_ARDOSIA_PERDIDA    = (30, 41, 59)       # #1E293B
COR_CONTORNO_BLOCO     = (15, 23, 42)       # #0F172A
COR_VERMELHO_DANO      = (220, 38, 38)      # #DC2626
COR_VERMELHO_SOMB      = (153, 27, 27)      # #991B1B
COR_ROXO_ARCANO        = (147, 51, 234)     # #9333EA

_FONTES_CACHE = {}
_BOSS_DELAY_CACHE = {}
_ICONES_CACHE = {}

_MATRIZ_CRANIO_12 = (
    "...######...",
    "..#WWWWWW#..",
    ".#WWWWWWWW#.",
    ".#WWWWWWWW#.",
    ".#W##WW##W#.",
    ".#W##WW##W#.",
    ".#WSW##WSW#.",
    "..#SSSSSS#..",
    "..#W#WW#W#..",
    "..#S#SS#S#..",
    "...######...",
    "............",
)

_MATRIZES_ICONES = {
    "espada": (
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
    ),
    "grade": (
        ".#...#....#...#.",
        "#M#.#M#..#M#.#M#",
        "################",
        "#MW..MW..MW..MW#",
        "#MW..MW..MW..MW#",
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
    ),
    "frasco": (
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
    ),
    "escudo": (
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
    ),
    "coroa": (
        "................",
        ".##....##....##.",
        "#GG#..#GG#..#GG#",
        "#GG#.#GGGG#.#GG#",
        "#GGG#GGGGGG#GGG#",
        "#GGGGGGGGGGGGGG#",
        ".#GGGGGGGGGGGG#.",
        ".#GG#C#GG#C#GG#.",
        ".#GGGGGGGGGGGG#.",
        ".#GGdddddddddd#.",
        "..############..",
        "................",
        "................",
        "................",
        "................",
        "................",
    ),
    "relogio": (
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
    ),
}
_MATRIZES_ICONES["portao"] = _MATRIZES_ICONES["grade"]
_MATRIZES_ICONES["pocao"] = _MATRIZES_ICONES["frasco"]


def obter_fonte_serif(tamanho, bold=True, italic=False):
    chave = (int(tamanho), bool(bold), bool(italic))
    if chave in _FONTES_CACHE:
        return _FONTES_CACHE[chave]
    for nome in ("Cinzel", "Constantia", "Georgia", "Cardo", "EB Garamond", "DejaVu Serif", "serif"):
        try:
            if nome == "serif" or pygame.font.match_font(nome):
                f = pygame.font.SysFont(nome, int(tamanho), bold=bold, italic=italic)
                _FONTES_CACHE[chave] = f
                return f
        except Exception:
            pass
    f = pygame.font.Font(None, int(tamanho))
    _FONTES_CACHE[chave] = f
    return f


def _resolver_rect(x_ou_rect, y, largura, altura):
    if isinstance(x_ou_rect, pygame.Rect):
        return x_ou_rect
    if isinstance(x_ou_rect, (tuple, list)):
        return pygame.Rect(x_ou_rect)
    return pygame.Rect(int(x_ou_rect), int(y or 0), int(largura or 0), int(altura or 0))


def _pontos_octogono(x, y, w, h, c):
    return [
        (x + c, y), (x + w - c, y),
        (x + w, y + c), (x + w, y + h - c),
        (x + w - c, y + h), (x + c, y + h),
        (x, y + h - c), (x, y + c),
    ]


def desenhar_cranio_gotico(superficie, cx, cy, tamanho=12, apagado=False):
    """Crânio gótico em pixel art (12x12 px base) em osso marfim (#F1F5F9)."""
    tam = max(8, int(tamanho))
    chave = ("cranio", tam, bool(apagado))
    if chave not in _ICONES_CACHE:
        base = pygame.Surface((12, 12), pygame.SRCALPHA)
        pal = {
            "#": (8, 6, 12, 255),
            "W": (71, 85, 105, 220) if apagado else (*COR_MARFIM_CRANIO, 255),
            "S": (51, 65, 85, 220) if apagado else (175, 185, 200, 255),
        }
        for py, linha in enumerate(_MATRIZ_CRANIO_12):
            for px, ch in enumerate(linha):
                if ch in pal:
                    base.set_at((px, py), pal[ch])
        _ICONES_CACHE[chave] = pygame.transform.scale(base, (tam, tam)) if tam != 12 else base
    surf = _ICONES_CACHE[chave]
    superficie.blit(surf, (int(cx - tam // 2), int(cy - tam // 2)))


def desenhar_icone_tematico(superficie, tipo, cx, cy, tamanho=16, aceso=False):
    """Renderiza ícones góticos procedurais (espada, grade, frasco, cristal, escudo, coroa, relogio)."""
    t_norm = str(tipo or "").lower()
    if t_norm in ("cristal", "cristal_ap", "eter"):
        desenhar_cristal_eter(superficie, int(cx), int(cy), tamanho=max(5, int(tamanho // 2)), ativo=aceso)
        return
    if t_norm == "caveira":
        desenhar_cranio_gotico(superficie, cx, cy, tamanho=max(12, int(tamanho)), apagado=not aceso)
        return

    tam = max(12, int(tamanho))
    chave = ("icone", t_norm, tam, bool(aceso))
    if chave not in _ICONES_CACHE:
        matriz = _MATRIZES_ICONES.get(t_norm, _MATRIZES_ICONES["espada"])
        base = pygame.Surface((16, 16), pygame.SRCALPHA)
        if aceso:
            pal = {
                "#": (8, 6, 12, 255),
                "W": (*COR_BRANCO_PEROLA, 255),
                "S": (203, 213, 225, 255),
                "G": (*COR_OURO_VIVO, 255),
                "g": (*COR_OURO_BRILHO, 255),
                "d": (*COR_LATAO_BORDA, 255),
                "B": (180, 120, 65, 255),
                "b": (110, 68, 30, 255),
                "M": (203, 213, 225, 255),
                "E": (*COR_ESMERALDA_VIDA, 255),
                "e": (*COR_ESMERALDA_SOMB, 255),
                "C": (*COR_AZUL_ETER, 255),
                "s": (148, 163, 184, 255),
            }
        else:
            pal = {
                "#": (10, 9, 16, 255),
                "W": (180, 190, 205, 255),
                "S": (120, 130, 148, 255),
                "G": (180, 130, 45, 255),
                "g": (130, 90, 28, 255),
                "d": (80, 50, 15, 255),
                "B": (125, 85, 50, 255),
                "b": (75, 48, 25, 255),
                "M": (130, 140, 158, 255),
                "E": (45, 140, 85, 255),
                "e": (22, 75, 42, 255),
                "C": (56, 155, 205, 255),
                "s": (95, 105, 125, 255),
            }
        for py, linha in enumerate(matriz):
            for px, ch in enumerate(linha[:16]):
                if ch in pal:
                    base.set_at((px, py), pal[ch])
        _ICONES_CACHE[chave] = pygame.transform.scale(base, (tam, tam)) if tam != 16 else base
    surf = _ICONES_CACHE[chave]
    superficie.blit(surf, (int(cx - tam // 2), int(cy - tam // 2)))


def desenhar_divisor_dourado(superficie, x, y, largura):
    """Linha horizontal fina (1px) em ouro envelhecido (#78350F -> #B45309) com desvanecimento nas pontas."""
    w = int(largura)
    if w <= 12:
        return
    s_div = pygame.Surface((w, 7), pygame.SRCALPHA)
    meio = w // 2
    for px in range(w):
        dist = abs(px - meio) / float(max(1, meio))
        fade = max(0.0, 1.0 - (dist ** 1.7))
        alfa = int(225 * fade)
        r = int(COR_OURO_ESCURO[0] + (COR_OURO_BRILHO[0] - COR_OURO_ESCURO[0]) * fade)
        g = int(COR_OURO_ESCURO[1] + (COR_OURO_BRILHO[1] - COR_OURO_ESCURO[1]) * fade)
        b = int(COR_OURO_ESCURO[2] + (COR_OURO_BRILHO[2] - COR_OURO_ESCURO[2]) * fade)
        s_div.set_at((px, 3), (r, g, b, alfa))
    superficie.blit(s_div, (int(x), int(y) - 3))
    cx = int(x + meio)
    pygame.draw.polygon(superficie, COR_OURO_VIVO, [(cx, int(y) - 3), (cx + 4, int(y)), (cx, int(y) + 3), (cx - 4, int(y))])


def desenhar_moldura_gotica(
    superficie, x_ou_rect, y=None, largura=None, altura=None,
    chanfro=8, destacado=False, alpha=245, borda_ouro=True,
    ativo=None, cantoneiras=True, cranios=False, variante="padrao"
):
    """Painel mestre gótico em ardósia/ébano (#0F0F1A), borda dupla em latão/ouro, abas em 'L' e crânios."""
    r = _resolver_rect(x_ou_rect, y, largura, altura)
    x, ry, w, h = int(r.x), int(r.y), int(r.width), int(r.height)
    if w <= 8 or h <= 8:
        return

    is_dest = bool(ativo) if ativo is not None else bool(destacado)
    c = max(3, min(int(chanfro), w // 5, h // 5))
    pontos = _pontos_octogono(x, ry, w, h, c)

    a_val = max(210, min(255, int(alpha)))
    cor_bg = (26, 14, 22) if variante == "carmesim" else COR_EBANO_FUNDO
    s_painel = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    pygame.draw.polygon(s_painel, (*cor_bg, a_val), [(px - x, py - ry) for px, py in pontos])
    superficie.blit(s_painel, (x, ry))

    cor_borda_ext = COR_OURO_BRILHO if is_dest else (COR_LATAO_BORDA if borda_ouro else COR_METAL_BORDA)
    pygame.draw.polygon(superficie, cor_borda_ext, pontos, 2)

    c_in = max(2, c - 2)
    pontos_in = _pontos_octogono(x + 3, ry + 3, w - 6, h - 6, c_in)
    cor_borda_int = COR_OURO_VIVO if is_dest else (COR_OURO_ESCURO if borda_ouro else (42, 46, 66))
    pygame.draw.polygon(superficie, cor_borda_int, pontos_in, 1)

    if cantoneiras and w >= 48 and h >= 34:
        braco = min(14, max(8, min(w, h) // 7))
        cor_l = COR_OURO_VIVO if is_dest else COR_OURO_BRILHO
        cor_l_somb = COR_OURO_DIVISOR
        cantos = [
            ((x - 1, ry + braco), (x - 1, ry - 1), (x + braco, ry - 1), (x + 2, ry + 2)),
            ((x + w - braco, ry - 1), (x + w, ry - 1), (x + w, ry + braco), (x + w - 3, ry + 2)),
            ((x - 1, ry + h - braco), (x - 1, ry + h), (x + braco, ry + h), (x + 2, ry + h - 3)),
            ((x + w - braco, ry + h), (x + w, ry + h), (x + w, ry + h - braco), (x + w - 3, ry + h - 3)),
        ]
        for p1, p2, p3, reb in cantos:
            pygame.draw.lines(superficie, cor_l_somb, False, [p1, p2, p3], 3)
            pygame.draw.lines(superficie, cor_l, False, [p1, p2, p3], 1)
            pygame.draw.rect(superficie, COR_OURO_VIVO, (reb[0], reb[1], 2, 2))

    if cranios and w >= 120 and h >= 64:
        desenhar_cranio_gotico(superficie, x + 20, ry + 18, tamanho=14, apagado=False)
        desenhar_cranio_gotico(superficie, x + w - 20, ry + 18, tamanho=14, apagado=False)


def desenhar_painel_gotico(
    superficie, x_ou_rect, y=None, largura=None, altura=None,
    chanfro=8, destacado=False, alpha=244, borda_ouro=True, ativo=None, cantoneiras=True, cranios=False, variante="padrao"
):
    desenhar_moldura_gotica(
        superficie, x_ou_rect, y=y, largura=largura, altura=altura,
        chanfro=chanfro, destacado=destacado, alpha=alpha, borda_ouro=borda_ouro,
        ativo=ativo, cantoneiras=cantoneiras, cranios=cranios, variante=variante,
    )


def desenhar_painel_elegante(surface, rect, cor_fundo=COR_EBANO_FUNDO, cor_borda=COR_LATAO_BORDA, alpha=244, borda=1, chanfro=6):
    desenhar_moldura_gotica(
        surface, rect, chanfro=chanfro, destacado=(borda >= 2),
        alpha=alpha, borda_ouro=(cor_borda is not None), cantoneiras=False,
    )


def desenhar_botao_gotico(
    surface, rect, texto, fonte, selecionado=False, icone=None,
    custo_ap=None, atalho=None, subtexto=None, desabilitado=False, font_sub=None
):
    """Botão metálico chanfrado com rebites internos, destaque vinho/ouro e ponteiros laterais."""
    r = _resolver_rect(rect, None, None, None)
    x, y, w, h = int(r.x), int(r.y), int(r.width), int(r.height)
    if w <= 12 or h <= 10:
        return

    chanfro = max(3, min(6, h // 5))
    pts = _pontos_octogono(x, y, w, h, chanfro)

    if desabilitado:
        cor_top, cor_bot = (20, 18, 28), (15, 14, 22)
    elif selecionado:
        cor_top, cor_bot = COR_VINHO_VIVO, COR_VINHO_ESC
    else:
        cor_top, cor_bot = COR_METAL_NEUTRO, COR_METAL_NEUTRO_ALT

    # Preenchimento metálico com gradiente sutil superior/inferior
    pygame.draw.polygon(surface, cor_bot, pts)
    pts_top = [
        (x + chanfro, y), (x + w - chanfro, y),
        (x + w, y + chanfro), (x + w, y + h // 2),
        (x, y + h // 2), (x, y + chanfro),
    ]
    pygame.draw.polygon(surface, cor_top, pts_top)

    # Bordas
    if desabilitado:
        pygame.draw.polygon(surface, (48, 45, 62), pts, 1)
    elif selecionado:
        pygame.draw.polygon(surface, COR_OURO_BRILHO, pts, 2)
        pts_in = _pontos_octogono(x + 2, y + 2, w - 4, h - 4, max(2, chanfro - 2))
        pygame.draw.polygon(surface, COR_OURO_VIVO, pts_in, 1)
    else:
        pygame.draw.polygon(surface, COR_METAL_BORDA, pts, 1)
        pygame.draw.line(surface, (78, 71, 99), (x + chanfro + 2, y + 1), (x + w - chanfro - 2, y + 1), 1)

    # Rebites metálicos nos 4 cantos internos
    off_r = 5 if h >= 28 else 3
    cor_reb = COR_OURO_VIVO if selecionado else COR_REBITE
    for rx, ry_p in (
        (x + off_r, y + off_r),
        (x + w - off_r - 2, y + off_r),
        (x + off_r, y + h - off_r - 2),
        (x + w - off_r - 2, y + h - off_r - 2),
    ):
        pygame.draw.rect(surface, (8, 6, 12), (rx + 1, ry_p + 1, 2, 2))
        pygame.draw.rect(surface, cor_reb, (rx, ry_p, 2, 2))

    # Marcadores pontiagudos dourados (> e <) flanqueando o botão selecionado
    if selecionado and not desabilitado:
        cy = y + h // 2
        pts_esq = [(x - 5, cy - 5), (x + 3, cy), (x - 5, cy + 5), (x - 2, cy)]
        pts_dir = [(x + w + 5, cy - 5), (x + w - 3, cy), (x + w + 5, cy + 5), (x + w + 2, cy)]
        pygame.draw.polygon(surface, COR_OURO_VIVO, pts_esq)
        pygame.draw.polygon(surface, COR_OURO_ESCURO, pts_esq, 1)
        pygame.draw.polygon(surface, COR_OURO_VIVO, pts_dir)
        pygame.draw.polygon(surface, COR_OURO_ESCURO, pts_dir, 1)

    # Ícone temático à esquerda
    pad_esq = 12 if w >= 48 else 4
    if icone:
        ico_tam = 18 if h >= 42 else (14 if h >= 26 else 12)
        desenhar_icone_tematico(surface, icone, x + 16 + ico_tam // 2, y + h // 2, tamanho=ico_tam, aceso=selecionado)
        pad_esq = 20 + ico_tam

    # Área disponível de texto
    pad_dir = 12 if w >= 48 else 4
    if custo_ap is not None:
        pad_dir = 48
    elif atalho:
        pad_dir = 68

    area_x = x + pad_esq
    area_w = max(4, (x + w - pad_dir) - area_x)

    if desabilitado:
        cor_txt = (110, 114, 128)
    elif selecionado:
        cor_txt = COR_OURO_VIVO
    else:
        cor_txt = COR_BRANCO_PEROLA

    if fonte and texto:
        s_txt = fonte.render(texto, True, cor_txt)
        s_sh = fonte.render(texto, True, (6, 8, 14))
        if subtexto and h >= 42:
            f_sub = font_sub or obter_fonte_serif(11, bold=False)
            cor_sub = COR_OURO_VIVO if selecionado else COR_CINZA_TEXTO
            s_sub = f_sub.render(subtexto, True, cor_sub)
            bloco_h = s_txt.get_height() + s_sub.get_height() + 2
            top_bloco = y + (h - bloco_h) // 2
            tx = area_x + max(0, (area_w - s_txt.get_width()) // 2) if (icone and w >= 180) else (x + (w - s_txt.get_width()) // 2 + (pad_esq // 3 if icone else 0))
            sx = area_x + max(0, (area_w - s_sub.get_width()) // 2) if (icone and w >= 180) else (x + (w - s_sub.get_width()) // 2 + (pad_esq // 3 if icone else 0))
            surface.blit(s_sh, (tx + 1, top_bloco + 1))
            surface.blit(s_txt, (tx, top_bloco))
            surface.blit(s_sub, (sx, top_bloco + s_txt.get_height() + 2))
        else:
            ty = y + (h - s_txt.get_height()) // 2
            if custo_ap is not None or atalho:
                tx = area_x
            elif icone:
                tx = area_x + max(0, (area_w - s_txt.get_width()) // 2)
            else:
                tx = x + (w - s_txt.get_width()) // 2
            surface.blit(s_sh, (tx + 1, ty + 1))
            surface.blit(s_txt, (tx, ty))

    if custo_ap is not None and fonte:
        bx, by = x + w - 42, y + h // 2
        desenhar_cristal_eter(surface, bx + 8, by, tamanho=5, ativo=(custo_ap > 0))
        txt_c = fonte.render(f"{custo_ap}", True, COR_AZUL_ETER if custo_ap > 0 else COR_CINZA_TEXTO)
        surface.blit(txt_c, (bx + 18, by - txt_c.get_height() // 2))
    elif atalho and fonte:
        f_at = font_sub or obter_fonte_serif(11, bold=False)
        txt_at = f_at.render(atalho, True, COR_OURO_VIVO if selecionado else COR_CINZA_TEXTO)
        surface.blit(txt_at, (x + w - txt_at.get_width() - 12, y + (h - txt_at.get_height()) // 2))


def desenhar_botao_elegante(surface, rect, texto, fonte, selecionado=False, icone=None, atalho=None, custo_ap=None, subtexto=None, desabilitado=False):
    desenhar_botao_gotico(
        surface, rect, texto, fonte, selecionado=selecionado,
        icone=icone, custo_ap=custo_ap, atalho=atalho, subtexto=subtexto, desabilitado=desabilitado,
    )


def desenhar_barra_segmentada(
    superficie, x_ou_rect, y=None, largura=None, altura=None,
    atual=None, maximo=None, segmentos=10,
    valor_atual=None, valor_max=None, num_blocos=None, margem_interna=2,
    cor_ativo=None, cor_vazio=None, texto_central=None, fonte=None, tipo="hp"
):
    """Barra modular segmentada em blocos individuais com contorno escuro."""
    if isinstance(x_ou_rect, (pygame.Rect, tuple, list)):
        r = _resolver_rect(x_ou_rect, None, None, None)
        v_at = y if valor_atual is None and y is not None else (valor_atual if valor_atual is not None else 0)
        v_mx = largura if valor_max is None and largura is not None else (valor_max if valor_max is not None else 1)
    else:
        r = _resolver_rect(x_ou_rect, y, largura, altura)
        v_at = atual if atual is not None else (valor_atual if valor_atual is not None else 0)
        v_mx = maximo if maximo is not None else (valor_max if valor_max is not None else 1)

    x, ry, w, h = int(r.x), int(r.y), int(r.width), int(r.height)
    if w <= 6 or h <= 4 or v_mx <= 0:
        return

    n_seg = max(2, min(24, int(num_blocos if num_blocos is not None else segmentos)))
    razao = max(0.0, min(1.0, float(v_at) / float(v_mx)))

    pygame.draw.rect(superficie, (10, 12, 20), (x, ry, w, h), border_radius=2)
    pygame.draw.rect(superficie, COR_METAL_BORDA, (x, ry, w, h), 1, border_radius=2)

    if cor_ativo is None:
        if tipo == "boss":
            cor_ativo, cor_somb = COR_VERMELHO_DANO, COR_VERMELHO_SOMB
        elif tipo in ("ap", "eter"):
            cor_ativo, cor_somb = COR_AZUL_ETER, (3, 105, 161)
        elif razao <= 0.25:
            cor_ativo, cor_somb = COR_VERMELHO_DANO, COR_VERMELHO_SOMB
        elif razao <= 0.50:
            cor_ativo, cor_somb = COR_OURO_BRILHO, COR_OURO_ESCURO
        else:
            cor_ativo, cor_somb = COR_ESMERALDA_VIDA, COR_ESMERALDA_SOMB
    else:
        cor_somb = (max(0, cor_ativo[0] - 45), max(0, cor_ativo[1] - 45), max(0, cor_ativo[2] - 45))

    cor_vazio = cor_vazio or COR_ARDOSIA_PERDIDA
    ix, iy, iw, ih = x + 2, ry + 2, w - 4, h - 4
    larg_bloco = max(2.0, (iw - (n_seg - 1) * margem_interna) / float(n_seg))

    for i in range(n_seg):
        bx = int(ix + i * (larg_bloco + margem_interna))
        bw = min(int(larg_bloco), (ix + iw) - bx)
        if bw <= 0:
            continue
        ativo = ((i + 0.5) / float(n_seg)) <= razao
        r_b = pygame.Rect(bx, iy, bw, ih)
        if ativo:
            pygame.draw.rect(superficie, cor_ativo, r_b)
            pygame.draw.line(superficie, tuple(min(255, c + 45) for c in cor_ativo[:3]), (bx, iy), (bx + bw - 1, iy), 1)
            pygame.draw.line(superficie, cor_somb, (bx, iy + ih - 1), (bx + bw - 1, iy + ih - 1), 1)
        else:
            pygame.draw.rect(superficie, cor_vazio, r_b)
        pygame.draw.rect(superficie, COR_CONTORNO_BLOCO, r_b, 1)

    if texto_central and fonte:
        txt_s = fonte.render(texto_central, True, COR_BRANCO_PEROLA)
        txt_sh = fonte.render(texto_central, True, (6, 9, 14))
        tx = x + (w - txt_s.get_width()) // 2
        ty = ry + (h - txt_s.get_height()) // 2
        superficie.blit(txt_sh, (tx + 1, ty + 1))
        superficie.blit(txt_s, (tx, ty))


def desenhar_barra_boss_monumental(
    superficie, x, y, largura, altura, atual, maximo, nome_boss,
    fase_atual=1, fases_totais=2, delay_ratio=None, tempo=0.0,
    cor_tema=None, fonte_nome=None, fonte_info=None
):
    """Barra monumental do Chefe no topo central com moldura dupla dourada e marcadores de fase."""
    if maximo <= 0:
        maximo = 1
    razao = max(0.0, min(1.0, float(atual) / float(maximo)))

    if delay_ratio is None:
        chave = str(nome_boss)
        prev = _BOSS_DELAY_CACHE.get(chave, razao)
        prev = razao if razao > prev else max(razao, prev - 0.008)
        _BOSS_DELAY_CACHE[chave] = prev
        delay_ratio = prev
    else:
        delay_ratio = max(razao, min(1.0, float(delay_ratio)))

    f_nome = fonte_nome or obter_fonte_serif(17, bold=True)
    f_info = fonte_info or obter_fonte_serif(12, bold=True)

    nome_limpo = str(nome_boss).replace("BOSS: ", "").replace("CHEFE: ", "").replace("CHEFE FINAL: ", "").strip().upper()
    txt_nome = f_nome.render(nome_limpo, True, COR_OURO_VIVO)
    somb_nome = f_nome.render(nome_limpo, True, (6, 8, 14))
    nx = x + (largura - txt_nome.get_width()) // 2
    ny = y - txt_nome.get_height() - 6
    superficie.blit(somb_nome, (nx + 1, ny + 1))
    superficie.blit(txt_nome, (nx, ny))

    lin_esq_x1 = max(x, nx - 14)
    lin_dir_x0 = min(x + largura, nx + txt_nome.get_width() + 14)
    ly_mid = ny + txt_nome.get_height() // 2 + 1
    if lin_esq_x1 - x >= 16:
        pygame.draw.line(superficie, COR_LATAO_BORDA, (x + 6, ly_mid), (lin_esq_x1, ly_mid), 1)
    if (x + largura) - lin_dir_x0 >= 16:
        pygame.draw.line(superficie, COR_LATAO_BORDA, (lin_dir_x0, ly_mid), (x + largura - 6, ly_mid), 1)

    pad = 4
    mx, my, mw, mh = x - pad, y - pad, largura + pad * 2, altura + pad * 2
    pts_ext = _pontos_octogono(mx, my, mw, mh, 6)
    s_fundo = pygame.Surface((mw + 2, mh + 2), pygame.SRCALPHA)
    pygame.draw.polygon(s_fundo, (*COR_EBANO_FUNDO, 245), [(px - mx, py - my) for px, py in pts_ext])
    superficie.blit(s_fundo, (mx, my))
    pygame.draw.polygon(superficie, COR_LATAO_BORDA, pts_ext, 2)
    pygame.draw.rect(superficie, COR_OURO_BRILHO, (x - 1, y - 1, largura + 2, altura + 2), 1)

    pygame.draw.rect(superficie, (14, 10, 18), (x, y, largura, altura))

    larg_delay = int(largura * delay_ratio)
    larg_hp = int(largura * razao)
    if larg_delay > larg_hp:
        pygame.draw.rect(superficie, (253, 224, 150), (x + larg_hp, y, larg_delay - larg_hp, altura))

    cor_fill = cor_tema or (COR_ROXO_ARCANO if ("VAZIO" in nome_limpo or "BIBLIOTEC" in nome_limpo) else COR_VERMELHO_DANO)
    cor_luz = tuple(min(255, cc + 50) for cc in cor_fill)
    if larg_hp > 0:
        pygame.draw.rect(superficie, cor_fill, (x, y, larg_hp, altura))
        pygame.draw.line(superficie, cor_luz, (x, y + 1), (x + larg_hp - 1, y + 1), 2)

    total_f = max(1, int(fases_totais))
    if total_f > 1:
        for fi in range(1, total_f):
            fx = x + int(largura * (fi / float(total_f)))
            pygame.draw.line(superficie, COR_EBANO_FUNDO, (fx, y), (fx, y + altura), 2)
            cy_d = y + altura // 2
            ativo_d = razao > (fi / float(total_f))
            cor_d = COR_OURO_VIVO if ativo_d else COR_OURO_ESCURO
            pts_d = [(fx, cy_d - 5), (fx + 4, cy_d), (fx, cy_d + 5), (fx - 4, cy_d)]
            pygame.draw.polygon(superficie, cor_d, pts_d)
            pygame.draw.polygon(superficie, COR_EBANO_FUNDO, pts_d, 1)

    lbl_hp = f"{int(atual)} / {int(maximo)}"
    txt_hp = f_info.render(lbl_hp, True, COR_CINZA_TEXTO)
    superficie.blit(txt_hp, (x + largura - txt_hp.get_width(), y + altura + 4))


def desenhar_cristal_eter(superficie, cx, cy, tamanho=7, ativo=True):
    """Gema de Éter em losango ciano (#38BDF8) com núcleo luminoso."""
    t = int(tamanho)
    if t <= 10:
        w_meio = max(4, t)
        h_meio = max(6, int(t * 1.4))
    else:
        w_meio = t // 2
        h_meio = int(t * 0.72)

    pontos = [(cx, cy - h_meio), (cx + w_meio, cy), (cx, cy + h_meio), (cx - w_meio, cy)]
    if ativo:
        raio_glow = int(max(w_meio, h_meio) * 1.45)
        s_glow = pygame.Surface((raio_glow * 2 + 4, raio_glow * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s_glow, (*COR_AZUL_ETER_GLOW, 65), (raio_glow + 2, raio_glow + 2), raio_glow)
        superficie.blit(s_glow, (cx - raio_glow - 2, cy - raio_glow - 2))
        pygame.draw.polygon(superficie, COR_AZUL_ETER, pontos)
        pygame.draw.polygon(superficie, COR_AZUL_ETER_CLARO, [(cx, cy - h_meio), (cx - w_meio, cy), (cx, cy + h_meio // 3)])
        pygame.draw.polygon(superficie, COR_AZUL_ETER_CLARO, pontos, 1)
    else:
        pygame.draw.polygon(superficie, COR_ARDOSIA_PERDIDA, pontos)
        pygame.draw.polygon(superficie, (71, 85, 105), pontos, 1)


def desenhar_hud_boss_rush(superficie, boss_atual, total_bosses, tempo_str):
    """HUD limpo exclusivo do modo Boss Rush."""
    f_hud = obter_fonte_serif(14, bold=True)
    sw = superficie.get_width()

    txt_prog = f"CHEFE [ {int(boss_atual):02d} / {int(total_bosses):02d} ]"
    surf_prog = f_hud.render(txt_prog, True, COR_OURO_VIVO)
    pw_e = surf_prog.get_width() + 24
    desenhar_moldura_gotica(superficie, 14, 14, pw_e, 30, chanfro=5, destacado=True, alpha=244, cantoneiras=False)
    superficie.blit(surf_prog, (26, 14 + (30 - surf_prog.get_height()) // 2))

    surf_tmp = f_hud.render(str(tempo_str), True, COR_BRANCO_PEROLA)
    pw_d = surf_tmp.get_width() + 38
    rx = sw - pw_d - 14
    desenhar_moldura_gotica(superficie, rx, 14, pw_d, 30, chanfro=5, destacado=False, alpha=244, cantoneiras=False)
    icx, icy = rx + 15, 29
    pygame.draw.circle(superficie, COR_OURO_BRILHO, (icx, icy), 6, 1)
    pygame.draw.line(superficie, COR_OURO_VIVO, (icx, icy), (icx, icy - 4), 1)
    pygame.draw.line(superficie, COR_OURO_VIVO, (icx, icy), (icx + 3, icy), 1)
    superficie.blit(surf_tmp, (rx + 28, 14 + (30 - surf_tmp.get_height()) // 2))


def desenhar_painel_eter_completo(surface, x, y, ap_atual, ap_max=6, tamanho=14, espacamento=20):
    for i in range(ap_max):
        cx = x + i * espacamento + tamanho // 2
        cy = y + tamanho // 2
        desenhar_cristal_eter(surface, cx, cy, tamanho=max(5, tamanho // 2), ativo=(i < ap_atual))


def desenhar_reticulo_mira(surface, rect, tempo=0.0, cor=None, estilo="unitario"):
    x, y, w, h = int(rect.x), int(rect.y), int(rect.width), int(rect.height)
    pulso = 0.5 + 0.5 * math.sin(tempo * 6.5)
    folga = int(6 + 4 * pulso)
    rx, ry, rw, rh = x - folga, y - folga, w + folga * 2, h + folga * 2
    cor = cor or (COR_VERMELHO_DANO if estilo == "aoe" else COR_OURO_VIVO)
    tam_l = max(8, min(18, min(rw, rh) // 4))

    for (x1, y1, x2, y2) in (
        (rx, ry, rx + tam_l, ry), (rx, ry, rx, ry + tam_l),
        (rx + rw, ry, rx + rw - tam_l, ry), (rx + rw, ry, rx + rw, ry + tam_l),
        (rx, ry + rh, rx + tam_l, ry + rh), (rx, ry + rh, rx, ry + rh - tam_l),
        (rx + rw, ry + rh, rx + rw - tam_l, ry + rh), (rx + rw, ry + rh, rx + rw, ry + rh - tam_l),
    ):
        pygame.draw.line(surface, cor, (x1, y1), (x2, y2), 2)


def desenhar_prompt_interacao(surface, x, y, texto="[E] INTERAGIR", fonte=None, tempo=0.0):
    f_use = fonte or obter_fonte_serif(12, bold=True)
    py = int(y + math.sin(tempo * 4.0) * 2.5)
    acao_ic, texto_lbl = _interpretar_item_rodape(texto)
    txt_surf = f_use.render(texto_lbl or texto, True, COR_OURO_VIVO)
    w_ic = (26 if not INPUT_MANAGER.usar_controle() else 20) if acao_ic else 0
    gap = 6 if (acao_ic and texto_lbl) else 0
    pw = w_ic + gap + (txt_surf.get_width() if texto_lbl else 0) + 20
    ph = max(28, txt_surf.get_height() + 10)
    px = int(x - pw // 2)
    desenhar_moldura_gotica(surface, px, py, pw, ph, chanfro=4, destacado=True, alpha=244, cantoneiras=False)
    cur_x = px + 10
    if acao_ic:
        ic_r = desenhar_icone_botao(surface, cur_x + w_ic // 2, py + ph // 2, acao_ic, escala=0.88)
        cur_x = ic_r.right + gap
    if texto_lbl:
        somb_s = f_use.render(texto_lbl, True, (8, 6, 12))
        ty = py + (ph - txt_surf.get_height()) // 2
        surface.blit(somb_s, (cur_x + 1, ty + 1))
        surface.blit(txt_surf, (cur_x, ty))


def desenhar_barra_elegante(surface, rect, valor, max_valor, cor_cheio=None, cor_vazio=None, tipo="hp", label=None, fonte=None):
    x, y, w, h = int(rect.x), int(rect.y), int(rect.width), int(rect.height)
    if w <= 4 or h <= 2 or max_valor <= 0:
        return
    razao = max(0.0, min(1.0, float(valor) / float(max_valor)))
    cor_vazio = cor_vazio or (18, 22, 32)
    if cor_cheio is None:
        if tipo == "boss":
            cor_cheio = COR_VERMELHO_DANO
        elif tipo in ("ap", "eter"):
            cor_cheio = COR_AZUL_ETER
        elif razao <= 0.25:
            cor_cheio = COR_VERMELHO_DANO
        elif razao <= 0.5:
            cor_cheio = COR_OURO_BRILHO
        else:
            cor_cheio = COR_ESMERALDA_VIDA

    pygame.draw.rect(surface, cor_vazio, (x, y, w, h), border_radius=2)
    larg_ativa = int(w * razao)
    if larg_ativa > 0:
        pygame.draw.rect(surface, cor_cheio, (x, y, larg_ativa, h), border_radius=2)
    pygame.draw.rect(surface, COR_METAL_BORDA, (x, y, w, h), 1, border_radius=2)
    if label and fonte:
        txt_s = fonte.render(label, True, COR_BRANCO_PEROLA)
        surface.blit(txt_s, (x + (w - txt_s.get_width()) // 2, y + (h - txt_s.get_height()) // 2))


def desenhar_badge_status(surface, rect, texto, fonte, cor_texto, cor_bg=None, cor_borda=None):
    x, y, w, h = int(rect.x), int(rect.y), int(rect.width), int(rect.height)
    pygame.draw.rect(surface, cor_bg or COR_EBANO_FUNDO, (x, y, w, h), border_radius=2)
    pygame.draw.rect(surface, cor_borda or cor_texto, (x, y, w, h), 1, border_radius=2)
    if fonte and texto:
        txt_surf = fonte.render(texto, True, cor_texto)
        surface.blit(txt_surf, (x + (w - txt_surf.get_width()) // 2, y + (h - txt_surf.get_height()) // 2))


def desenhar_card_sala(surface, rect, idx, nome_sala, ativo=False, derrotado=False, hp=100, max_hp=100, visitada=True, miniatura_surf=None, fontes=None):
    desenhar_moldura_gotica(surface, rect, chanfro=6, destacado=ativo, alpha=244, borda_ouro=True, cantoneiras=False)
    f_peq = fontes[0] if isinstance(fontes, (list, tuple)) else None
    f_tit = fontes[1] if isinstance(fontes, (list, tuple)) and len(fontes) > 1 else f_peq
    if f_peq:
        surface.blit(f_peq.render(f"SALA {idx + 1}", True, COR_OURO_VIVO if ativo else COR_LATAO_BORDA), (rect.x + 14, rect.y + 10))
    if f_tit:
        surface.blit(f_tit.render(nome_sala, True, COR_BRANCO_PEROLA), (rect.x + 14, rect.y + 30))


def desenhar_painel_hud_compacto(superficie, rect, alpha=240, borda_ouro=True, destacado=False, chanfro=5):
    """Caixa chanfrada única leve (#0B0F19, alpha 240) com borda fina de 1px sem poluição."""
    r = _resolver_rect(rect, None, None, None)
    x, y, w, h = int(r.x), int(r.y), int(r.width), int(r.height)
    if w <= 8 or h <= 8:
        return
    c = max(3, min(int(chanfro), w // 5, h // 5))
    pontos = _pontos_octogono(x, y, w, h, c)
    s_bg = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    pygame.draw.polygon(s_bg, (*COR_EBANO_HUD, max(180, min(255, int(alpha)))), [(px - x, py - y) for px, py in pontos])
    superficie.blit(s_bg, (x, y))
    cor_b = COR_OURO_BRILHO if destacado else (COR_LATAO_BORDA if borda_ouro else COR_METAL_BORDA)
    pygame.draw.polygon(superficie, cor_b, pontos, 1)


def _truncar_texto(fonte, texto, largura_max):
    s = str(texto or "")
    if fonte.size(s)[0] <= largura_max:
        return s
    while len(s) > 1 and fonte.size(s + "…")[0] > largura_max:
        s = s[:-1]
    return s + "…" if len(s) > 0 else ""


def desenhar_hud_mapa_compacto(surface, nome_heroi, hp, max_hp, eter_cristais, pocoes, vidas, vidas_max=3, margin=16):
    """Painel único de status do jogador (260x60 px) no canto superior esquerdo dentro da Safe Area (16px)."""
    px, py, pw, ph = int(margin), int(margin), 260, 60
    desenhar_painel_hud_compacto(surface, (px, py, pw, ph), alpha=240, borda_ouro=True, destacado=False, chanfro=5)

    f_nome = obter_fonte_serif(12, bold=True)
    f_info = obter_fonte_serif(11, bold=True)

    # Linha 1: Nome à esquerda + barra segmentada (12 blocos verdes limpos) + "42 / 120" legível
    nome_limpo = _truncar_texto(f_nome, str(nome_heroi or "Viajante"), 72)
    s_nome = f_nome.render(nome_limpo, True, COR_OURO_VIVO)
    surface.blit(s_nome, (px + 10, py + 7))

    hp_v = max(0, int(hp))
    max_hp_v = max(1, int(max_hp))
    bar_rect = pygame.Rect(px + 86, py + 10, 104, 10)
    desenhar_barra_segmentada(
        surface, bar_rect.x, bar_rect.y, bar_rect.width, bar_rect.height,
        hp_v, max_hp_v, num_blocos=12, margem_interna=1,
        cor_ativo=COR_ESMERALDA_VIDA, cor_vazio=(18, 26, 38),
    )

    hp_str = f"{hp_v} / {max_hp_v}"
    cor_hp = (255, 190, 190) if hp_v <= max_hp_v * 0.25 else COR_BRANCO_PEROLA
    s_hp = f_info.render(hp_str, True, cor_hp)
    surface.blit(s_hp, (px + pw - s_hp.get_width() - 9, py + 8))

    # Divisória discreta entre linhas
    pygame.draw.line(surface, (92, 62, 24), (px + 10, py + 30), (px + pw - 10, py + 30), 1)

    # Linha 2: Gemas de Éter em losangos azuis ciano alinhadas + contadores compactos (Poções x3, Vidas 1/3)
    qtd_eter = max(0, int(eter_cristais))
    for i in range(5):
        desenhar_cristal_eter(surface, px + 17 + i * 13, py + 45, tamanho=4, ativo=(i < qtd_eter))

    s_poc = f_info.render(f"Poções x{max(0, int(pocoes))}", True, (110, 231, 183))
    surface.blit(s_poc, (px + 90, py + 38))

    cor_v = COR_VERMELHO_DANO if vidas <= 1 else COR_OURO_VIVO
    s_vid = f_info.render(f"Vidas {max(0, int(vidas))}/{max(1, int(vidas_max))}", True, cor_v)
    surface.blit(s_vid, (px + pw - s_vid.get_width() - 10, py + 38))


def desenhar_placa_missao_topo(surface, texto_missao, concl=False, margin_top=16):
    """Placa chanfrada única no centro superior (340x28 px) para sub-região e objetivo sem poluição."""
    pw, ph = 340, 28
    px = (surface.get_width() - pw) // 2
    py = int(margin_top)
    desenhar_painel_hud_compacto(surface, (px, py, pw, ph), alpha=238, borda_ouro=True, destacado=concl, chanfro=5)

    f_miss = obter_fonte_serif(12, bold=True)
    msg = _truncar_texto(f_miss, str(texto_missao or ""), pw - 24)
    cor = COR_ESMERALDA_VIDA if concl else COR_OURO_VIVO
    s_txt = f_miss.render(msg, True, cor)
    s_sh = f_miss.render(msg, True, (6, 8, 12))
    tx = px + (pw - s_txt.get_width()) // 2
    ty = py + (ph - s_txt.get_height()) // 2
    surface.blit(s_sh, (tx + 1, ty + 1))
    surface.blit(s_txt, (tx, ty))


def desenhar_relogio_inferior_esquerdo(surface, tempo_texto, rotulo=None, urgente=False, margin=16):
    """Caixa minimalista travada no rodapé inferior esquerdo (deixa topo direito livre para a lua)."""
    f_cron = obter_fonte_serif(12, bold=True)
    pw = 152 if rotulo else 104
    ph = 28
    px = int(margin)
    py = surface.get_height() - int(margin) - ph
    desenhar_painel_hud_compacto(surface, (px, py, pw, ph), alpha=240, borda_ouro=True, destacado=False, chanfro=5)
    if urgente:
        pygame.draw.polygon(surface, COR_VERMELHO_DANO, _pontos_octogono(px, py, pw, ph, 5), 1)

    icx, icy = px + 14, py + ph // 2
    pygame.draw.circle(surface, COR_VERMELHO_DANO if urgente else COR_LATAO_BORDA, (icx, icy), 6, 1)
    pygame.draw.line(surface, COR_OURO_VIVO, (icx, icy), (icx, icy - 4), 1)
    pygame.draw.line(surface, COR_OURO_VIVO, (icx, icy), (icx + 3, icy), 1)

    if rotulo:
        s_rot = f_cron.render(str(rotulo), True, COR_OURO_BRILHO)
        surface.blit(s_rot, (px + 25, py + (ph - s_rot.get_height()) // 2))

    cor_num = COR_VERMELHO_DANO if urgente else COR_BRANCO_PEROLA
    s_num = f_cron.render(str(tempo_texto), True, cor_num)
    nx = px + pw - s_num.get_width() - 11
    surface.blit(s_num, (nx, py + (ph - s_num.get_height()) // 2))


# =============================================================================
# 9. GERENCIADOR DE INPUT (HOT-SWAP), GLIFOS DE BOTÕES E BRASÃO DE RANK
# =============================================================================

PALETA_RANKS = {
    "S": {"cor": (253, 230, 138), "borda": (217, 155, 38), "fundo": (42, 30, 14), "titulo": "Execução Impecável"},
    "A": {"cor": (147, 197, 253), "borda": (59, 130, 246), "fundo": (18, 28, 48), "titulo": "Maestria Arcana"},
    "B": {"cor": (245, 158, 11),  "borda": (180, 95, 12),  "fundo": (38, 24, 14), "titulo": "Honra de Combate"},
    "C": {"cor": (148, 163, 184), "borda": (100, 116, 139),"fundo": (24, 28, 36), "titulo": "Sobrevivente"},
}


class InputManager:
    """Gerenciador unificado de dispositivos de entrada com hot-swap em tempo real."""

    MODO_TECLADO = "TECLADO"
    MODO_CONTROLE = "CONTROLE"
    TIPO_XBOX = "XBOX"
    TIPO_PLAYSTATION = "PLAYSTATION"

    def __init__(self):
        self.modo_input = self.MODO_TECLADO
        self.tipo_controle = self.TIPO_XBOX
        self.controle_conectado = False
        self.nome_controle = ""
        self._ultimo_mouse_pos = None

    @staticmethod
    def detectar_tipo_controle(nome):
        n = str(nome or "").lower()
        if any(k in n for k in ("playstation", "ps5", "ps4", "ps3", "dualsense", "dualshock", "sony", "wireless controller")):
            return InputManager.TIPO_PLAYSTATION
        return InputManager.TIPO_XBOX

    def registrar_teclado(self):
        self.modo_input = self.MODO_TECLADO

    def registrar_controle(self, nome=""):
        self.modo_input = self.MODO_CONTROLE
        self.controle_conectado = True
        if nome:
            self.nome_controle = str(nome)
            self.tipo_controle = self.detectar_tipo_controle(nome)

    def atualizar_dispositivo_joystick(self, conectado, nome=""):
        self.controle_conectado = bool(conectado)
        if conectado:
            if nome:
                self.nome_controle = str(nome)
                self.tipo_controle = self.detectar_tipo_controle(nome)
        else:
            self.nome_controle = ""
            self.modo_input = self.MODO_TECLADO

    def usar_controle(self):
        return self.modo_input == self.MODO_CONTROLE

    def processar_evento(self, event, nome_joystick="", limiar_eixo=0.25, limiar_mouse=8):
        """Atualiza `modo_input` dinamicamente para TECLADO ou CONTROLE com base no último evento real."""
        if event is None:
            return self.modo_input
        if getattr(event, "simulado_controle", False) or getattr(event, "origem", None) == "CONTROLE":
            return self.modo_input

        etype = getattr(event, "type", None)
        if etype in (pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.registrar_teclado()
        elif etype == pygame.MOUSEMOTION:
            pos = getattr(event, "pos", None)
            if pos is not None:
                if self._ultimo_mouse_pos is None:
                    self._ultimo_mouse_pos = pos
                elif (abs(pos[0] - self._ultimo_mouse_pos[0]) + abs(pos[1] - self._ultimo_mouse_pos[1])) >= limiar_mouse:
                    self._ultimo_mouse_pos = pos
                    self.registrar_teclado()
        elif etype in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION):
            self.registrar_controle(nome_joystick)
        elif etype == pygame.JOYAXISMOTION:
            if abs(getattr(event, "value", 0.0)) > limiar_eixo:
                self.registrar_controle(nome_joystick)
        elif etype == pygame.JOYDEVICEADDED:
            self.controle_conectado = True
            if nome_joystick:
                self.nome_controle = str(nome_joystick)
                self.tipo_controle = self.detectar_tipo_controle(nome_joystick)
            self.modo_input = self.MODO_CONTROLE
        elif etype == pygame.JOYDEVICEREMOVED:
            if nome_joystick:
                self.controle_conectado = True
                self.nome_controle = str(nome_joystick)
                self.tipo_controle = self.detectar_tipo_controle(nome_joystick)
            else:
                self.atualizar_dispositivo_joystick(False)
        return self.modo_input


INPUT_MANAGER = InputManager()


def _desenhar_keycap(surface, cx, cy, texto, f_key=None, escala=1.0):
    """Desenha uma tecla cinza chanfrada gótica centralizada em (cx, cy) e retorna o rect."""
    f_use = f_key or obter_fonte_serif(max(9, int(10 * escala)), bold=True)
    lbl = f_use.render(texto, True, (242, 245, 252))
    somb = f_use.render(texto, True, (10, 12, 18))
    w = max(int(20 * escala), lbl.get_width() + int(12 * escala))
    h = max(int(18 * escala), lbl.get_height() + int(5 * escala))
    r = pygame.Rect(int(cx - w // 2), int(cy - h // 2), w, h)
    c = max(2, int(3 * escala))

    pts = [
        (r.left + c, r.top), (r.right - c, r.top),
        (r.right, r.top + c), (r.right, r.bottom - c),
        (r.right - c, r.bottom), (r.left + c, r.bottom),
        (r.left, r.bottom - c), (r.left, r.top + c),
    ]
    pygame.draw.polygon(surface, (42, 48, 62), pts)
    pygame.draw.line(surface, (118, 130, 154), (r.left + c, r.top + 1), (r.right - c, r.top + 1), 1)
    pygame.draw.line(surface, (24, 28, 38), (r.left + c, r.bottom - 1), (r.right - c, r.bottom - 1), 2)
    pygame.draw.polygon(surface, (96, 108, 128), pts, 1)

    tx = r.centerx - lbl.get_width() // 2
    ty = r.centery - lbl.get_height() // 2
    surface.blit(somb, (tx + 1, ty + 1))
    surface.blit(lbl, (tx, ty))
    return r


def _desenhar_bumper(surface, cx, cy, texto, escala=1.0):
    """Desenha gatilho/ombro metálico chanfrado [LB] / [RB] para gamepad."""
    f_use = obter_fonte_serif(max(9, int(10 * escala)), bold=True)
    lbl = f_use.render(texto, True, (238, 242, 250))
    w = max(int(24 * escala), lbl.get_width() + int(12 * escala))
    h = max(int(17 * escala), lbl.get_height() + int(4 * escala))
    r = pygame.Rect(int(cx - w // 2), int(cy - h // 2), w, h)
    pygame.draw.rect(surface, (36, 40, 54), r, border_radius=max(3, int(5 * escala)))
    pygame.draw.line(surface, (160, 174, 200), (r.left + 4, r.top + 1), (r.right - 4, r.top + 1), 1)
    pygame.draw.rect(surface, (124, 138, 165), r, 1, border_radius=max(3, int(5 * escala)))
    surface.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))
    return r


def _desenhar_face_gamepad(surface, cx, cy, forma, cor_fill, cor_rim, texto_ps_ou_xbox="", escala=1.0):
    """Desenha botão circular de gamepad (Xbox letra ou símbolo geométrico PlayStation)."""
    r_btn = max(8, int(9 * escala))
    icx, icy = int(cx), int(cy)
    pygame.draw.circle(surface, (10, 10, 16), (icx + 1, icy + 1), r_btn)
    pygame.draw.circle(surface, cor_fill, (icx, icy), r_btn)
    pygame.draw.circle(surface, cor_rim, (icx, icy), r_btn, 1)

    if forma == "PS_CRUZ":
        d = max(3, int(4 * escala))
        c_s = (147, 197, 253)
        pygame.draw.line(surface, c_s, (icx - d, icy - d), (icx + d, icy + d), 2)
        pygame.draw.line(surface, c_s, (icx - d, icy + d), (icx + d, icy - d), 2)
    elif forma == "PS_CIRCULO":
        pygame.draw.circle(surface, (252, 165, 165), (icx, icy), max(3, int(4 * escala)), 2)
    elif forma == "PS_QUADRADO":
        d = max(3, int(4 * escala))
        pygame.draw.rect(surface, (249, 168, 212), (icx - d, icy - d, d * 2 + 1, d * 2 + 1), 2)
    elif forma == "PS_TRIANGULO":
        d = max(3, int(4 * escala))
        pts = [(icx, icy - d - 1), (icx - d - 1, icy + d), (icx + d + 1, icy + d)]
        pygame.draw.polygon(surface, (110, 231, 183), pts, 2)
    else:
        f_btn = obter_fonte_serif(max(9, int(10 * escala)), bold=True)
        cor_txt = (20, 18, 12) if sum(cor_fill) > 490 else (248, 250, 252)
        s = f_btn.render(texto_ps_ou_xbox, True, cor_txt)
        surface.blit(s, (icx - s.get_width() // 2, icy - s.get_height() // 2))

    return pygame.Rect(icx - r_btn, icy - r_btn, r_btn * 2, r_btn * 2)


def desenhar_icone_botao(surface, cx, cy, acao, modo_input=None, tipo_controle=None, escala=1.0):
    """
    Renderiza proceduralmente o glifo de comando correspondente ao dispositivo ativo.
    Retorna o pygame.Rect delimitador do ícone desenhado.
    """
    modo = str(modo_input or INPUT_MANAGER.modo_input).upper()
    tipo = str(tipo_controle or INPUT_MANAGER.tipo_controle).upper()
    act = str(acao or "CONFIRMAR").strip().upper()
    eh_ps = ("PLAYSTATION" in tipo or tipo.startswith("PS"))

    if modo != "CONTROLE":
        mapa_teclado = {
            "CONFIRMAR": "ENTER", "ACEITAR": "ENTER", "ENTER": "ENTER", "OK": "ENTER", "CONFIRMAR_COMBATE": "ENTER",
            "ESPACO": "ESPAÇO", "ESPAÇO": "ESPAÇO", "PULO": "ESPAÇO", "SALTAR": "ESPAÇO", "RENASCER": "ESPAÇO", "QTE": "ESPAÇO",
            "ATAQUE": "ESPAÇO", "ATIRAR": "Z", "ATACAR": "Z",
            "CANCELAR": "ESC", "VOLTAR": "ESC", "ESC": "ESC", "FECHAR": "ESC",
            "DESVIO": "C",
            "INTERAGIR": "E", "ACAO_SECUNDARIA": "E", "ABRIR": "E",
            "PARRY": "X",
            "DEFESA": "Q", "ITENS": "Q", "POCAO": "Q", "CURA": "Q", "USAR_ITEM": "Q",
            "REINICIAR": "R", "NOVA_JORNADA": "R", "RECOMEÇAR": "R", "RECOMECAR": "R",
            "RANQUE": "T", "RANK": "T",
            "ALVOS": "A / D", "TROCAR_ALVO": "A / D", "LB_RB": "A / D",
            "NAVEGAR": "A / D", "NAVEGAR_H": "A / D", "NAVEGAR_V": "W / S", "MOVER": "A / D",
            "F2": "F2", "AUTO": "F2", "F5": "F5", "F11": "F11",
        }
        rotulo = mapa_teclado.get(act, act[:10])
        return _desenhar_keycap(surface, cx, cy, rotulo, escala=escala)

    # Modo CONTROLE (Xbox padrão ou PlayStation)
    if act in ("CONFIRMAR", "ACEITAR", "ENTER", "OK", "CONFIRMAR_COMBATE", "ESPACO", "ESPAÇO", "PULO", "SALTAR", "RENASCER", "QTE", "ATAQUE"):
        if eh_ps:
            return _desenhar_face_gamepad(surface, cx, cy, "PS_CRUZ", (29, 78, 216), (147, 197, 253), escala=escala)
        return _desenhar_face_gamepad(surface, cx, cy, "XBOX", (34, 197, 94), (134, 239, 172), "A", escala=escala)

    if act in ("CANCELAR", "VOLTAR", "ESC", "FECHAR", "DESVIO"):
        if eh_ps:
            return _desenhar_face_gamepad(surface, cx, cy, "PS_CIRCULO", (127, 29, 29), (248, 113, 113), escala=escala)
        return _desenhar_face_gamepad(surface, cx, cy, "XBOX", (220, 38, 38), (252, 165, 165), "B", escala=escala)

    if act in ("INTERAGIR", "ACAO_SECUNDARIA", "ABRIR", "ATIRAR", "ATACAR", "PARRY", "REINICIAR", "NOVA_JORNADA", "RECOMEÇAR", "RECOMECAR"):
        if eh_ps:
            return _desenhar_face_gamepad(surface, cx, cy, "PS_QUADRADO", (88, 28, 135), (244, 114, 182), escala=escala)
        return _desenhar_face_gamepad(surface, cx, cy, "XBOX", (37, 99, 235), (147, 197, 253), "X", escala=escala)

    if act in ("DEFESA", "ITENS", "POCAO", "CURA", "USAR_ITEM", "RANQUE", "RANK"):
        if eh_ps:
            return _desenhar_face_gamepad(surface, cx, cy, "PS_TRIANGULO", (17, 94, 89), (110, 231, 183), escala=escala)
        return _desenhar_face_gamepad(surface, cx, cy, "XBOX", (234, 179, 8), (253, 230, 138), "Y", escala=escala)

    if act in ("ALVOS", "TROCAR_ALVO", "LB_RB", "GATILHOS"):
        return _desenhar_bumper(surface, cx, cy, "L1/R1" if eh_ps else "LB/RB", escala=escala)

    if act in ("NAVEGAR", "NAVEGAR_H", "NAVEGAR_V", "MOVER"):
        return _desenhar_bumper(surface, cx, cy, "D-PAD", escala=escala)

    if act in ("F2", "AUTO", "F11"):
        return _desenhar_bumper(surface, cx, cy, "VIEW" if act == "F11" else "MENU", escala=escala)

    return _desenhar_bumper(surface, cx, cy, act[:6], escala=escala)


def desenhar_brasao_rank(surface, cx, cy, rank_letra, pontuacao=None, tamanho=64, sem_avaria=False, titulo=None, anim_t=0.0):
    """
    Desenha o brasão gótico chanfrado com letra monumental S/A/B/C centralizada,
    sem sobreposição de texto e com sub-placa opcional de pontuação e 'Sem Avaria'.
    """
    letra = str(rank_letra or "C").upper()[:1]
    cfg = PALETA_RANKS.get(letra, PALETA_RANKS["C"])
    cor = cfg["cor"]
    borda = cfg["borda"]
    fundo = cfg["fundo"]

    icx, icy = int(cx), int(cy)
    tam = max(36, int(tamanho))
    r_half = tam // 2
    chanfro = max(8, int(tam * 0.22))

    # Brilho pulsante para Rank S e A
    pulso = 0.5 + 0.5 * math.sin(anim_t * 3.8)
    if letra in ("S", "A"):
        glow = pygame.Surface((tam + 28, tam + 28), pygame.SRCALPHA)
        alpha_g = int((34 + 28 * pulso) if letra == "S" else (22 + 16 * pulso))
        pygame.draw.circle(glow, (*cor, alpha_g), (glow.get_width() // 2, glow.get_height() // 2), r_half + 12)
        surface.blit(glow, (icx - glow.get_width() // 2, icy - glow.get_height() // 2))

    rect_b = pygame.Rect(icx - r_half, icy - r_half, tam, tam)
    pts_ext = [
        (rect_b.left + chanfro, rect_b.top), (rect_b.right - chanfro, rect_b.top),
        (rect_b.right, rect_b.top + chanfro), (rect_b.right, rect_b.bottom - chanfro),
        (rect_b.right - chanfro, rect_b.bottom), (rect_b.left + chanfro, rect_b.bottom),
        (rect_b.left, rect_b.bottom - chanfro), (rect_b.left, rect_b.top + chanfro),
    ]
    pygame.draw.polygon(surface, fundo, pts_ext)
    pygame.draw.polygon(surface, cor, pts_ext, 2)

    # Moldura metálica interna chanfrada
    rect_in = rect_b.inflate(-8, -8)
    c_in = max(5, chanfro - 3)
    pts_in = [
        (rect_in.left + c_in, rect_in.top), (rect_in.right - c_in, rect_in.top),
        (rect_in.right, rect_in.top + c_in), (rect_in.right, rect_in.bottom - c_in),
        (rect_in.right - c_in, rect_in.bottom), (rect_in.left + c_in, rect_in.bottom),
        (rect_in.left, rect_in.bottom - c_in), (rect_in.left, rect_in.top + c_in),
    ]
    pygame.draw.polygon(surface, borda, pts_in, 1)

    # Letra gótica monumental estritamente centralizada
    f_rank = obter_fonte_serif(max(20, int(tam * 0.54)), bold=True)
    somb_l = f_rank.render(letra, True, (8, 6, 12))
    txt_l = f_rank.render(letra, True, cor)
    lx = icx - txt_l.get_width() // 2
    ly = icy - txt_l.get_height() // 2 - 1
    surface.blit(somb_l, (lx + 2, ly + 2))
    surface.blit(txt_l, (lx, ly))

    cur_y = rect_b.bottom + 8
    f_sub = obter_fonte_serif(11, bold=True)
    if titulo:
        t_surf = f_sub.render(str(titulo), True, COR_BRANCO_PEROLA)
        surface.blit(t_surf, (icx - t_surf.get_width() // 2, cur_y))
        cur_y += t_surf.get_height() + 3

    detalhes = []
    if pontuacao is not None:
        detalhes.append(f"{int(pontuacao)} PTS")
    if sem_avaria:
        detalhes.append("SEM AVARIA")
    if detalhes:
        txt_det = " · ".join(detalhes)
        d_surf = f_sub.render(txt_det, True, cor if sem_avaria else COR_CINZA_TEXTO)
        surface.blit(d_surf, (icx - d_surf.get_width() // 2, cur_y))

    return rect_b


def _interpretar_item_rodape(item):
    """Converte item de rodapé em (acao_icone_ou_None, rotulo_texto)."""
    if isinstance(item, (tuple, list)) and len(item) >= 2:
        return str(item[0]).upper(), str(item[1])

    s = str(item or "").strip()
    if s.startswith("[") and "]" in s:
        fim = s.index("]")
        chave = s[1:fim].strip().upper()
        resto = s[fim + 1:].strip()
        mapa = {
            "ENTER": "CONFIRMAR",
            "ENTER/ESPAÇO": "CONFIRMAR",
            "ENTER / ESPAÇO": "CONFIRMAR",
            "ESPAÇO": "ESPACO",
            "SPACE": "ESPACO",
            "ESC": "CANCELAR",
            "E": "INTERAGIR",
            "Q": "ITENS",
            "R": "REINICIAR",
            "T": "RANQUE",
            "X": "PARRY",
            "C": "DESVIO",
            "A/D": "NAVEGAR_H",
            "A / D": "NAVEGAR_H",
            "W/S": "NAVEGAR_V",
            "W / S": "NAVEGAR_V",
            "↑/↓": "NAVEGAR_V",
            "↑ / ↓": "NAVEGAR_V",
            "←/→": "NAVEGAR_H",
            "← / →": "NAVEGAR_H",
            "← →": "NAVEGAR_H",
            "F2": "F2",
            "F5": "F5",
            "F11": "F11",
        }
        if chave in mapa:
            return mapa[chave], resto
    return None, s


def desenhar_rodape_comandos(surface, y_pos, comandos, fonte=None, largura=None, cor=None):
    """Legenda de rodapé centralizada com glifos procedurais sincronizados com o InputManager."""
    if not comandos:
        return
    f_use = fonte or obter_fonte_serif(12, bold=False)
    w_ref = largura or surface.get_width()
    cor_txt = cor or COR_CINZA_TEXTO

    if isinstance(comandos, str):
        itens_raw = [p.strip() for p in comandos.split("|") if p.strip()]
    else:
        itens_raw = list(comandos)

    # Medição prévia para centralização perfeita sem cortes nem sobreposições
    blocos = []
    largura_total = 0
    sep_w = f_use.render("  |  ", True, cor_txt).get_width()

    for idx, raw in enumerate(itens_raw):
        acao_ic, texto_lbl = _interpretar_item_rodape(raw)
        surf_lbl = f_use.render(texto_lbl, True, cor_txt) if texto_lbl else None
        # Calcula largura aproximada do ícone sem poluir a tela final
        if acao_ic:
            if not INPUT_MANAGER.usar_controle():
                tmp_key = {
                    "CONFIRMAR": "ENTER", "ESPACO": "ESPAÇO", "CANCELAR": "ESC",
                    "INTERAGIR": "E", "ITENS": "Q", "REINICIAR": "R", "RANQUE": "T",
                    "PARRY": "X", "DESVIO": "C", "NAVEGAR_H": "A / D", "NAVEGAR_V": "W / S",
                    "ALVOS": "A / D", "F2": "F2", "F5": "F5", "F11": "F11",
                }.get(acao_ic, acao_ic[:6])
                w_ic = max(20, obter_fonte_serif(10, bold=True).render(tmp_key, True, cor_txt).get_width() + 12)
            elif acao_ic in ("ALVOS", "LB_RB", "NAVEGAR_H", "NAVEGAR_V", "F2", "F11"):
                tmp_pad = "L1/R1" if (acao_ic in ("ALVOS", "LB_RB") and INPUT_MANAGER.tipo_controle == InputManager.TIPO_PLAYSTATION) else ("LB/RB" if acao_ic in ("ALVOS", "LB_RB") else "D-PAD")
                w_ic = max(24, obter_fonte_serif(10, bold=True).render(tmp_pad, True, cor_txt).get_width() + 12)
            else:
                w_ic = 19
        else:
            w_ic = 0

        w_bloco = (w_ic + (6 if (w_ic and surf_lbl) else 0)) + (surf_lbl.get_width() if surf_lbl else 0)
        blocos.append((acao_ic, texto_lbl, surf_lbl, w_ic, w_bloco))
        largura_total += w_bloco
        if idx < len(itens_raw) - 1:
            largura_total += sep_w

    cur_x = max(8, (w_ref - largura_total) // 2)
    cy = int(y_pos) + f_use.get_height() // 2

    for idx, (acao_ic, texto_lbl, surf_lbl, w_ic, _wb) in enumerate(blocos):
        if acao_ic:
            ic_rect = desenhar_icone_botao(surface, cur_x + w_ic // 2, cy, acao_ic, escala=0.92)
            cur_x = ic_rect.right + (6 if surf_lbl else 0)
        if surf_lbl:
            somb = f_use.render(texto_lbl, True, (6, 8, 14))
            ty = int(y_pos)
            surface.blit(somb, (cur_x + 1, ty + 1))
            surface.blit(surf_lbl, (cur_x, ty))
            cur_x += surf_lbl.get_width()
        if idx < len(blocos) - 1:
            sep_s = f_use.render("  |  ", True, (90, 96, 114))
            surface.blit(sep_s, (cur_x, int(y_pos)))
            cur_x += sep_s.get_width()

