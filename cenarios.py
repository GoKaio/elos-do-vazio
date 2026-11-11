# -*- coding: utf-8 -*-
"""Cenários orgânicos em 3 camadas (Aérea, Térrea BSP e Subterrânea via Autômatos Celulares)."""

import os
import random
import math
import pygame

from config import CONFIG
from caminhos import obter_caminho_recurso
from procedural_gen import gerar_camaras_bsp, gerar_caverna_automato_celular, RuidoSimplex
from cenario_combate_25d import CameraCombate25D, CenarioCombate25D
from gerenciador_salas import GerenciadorSalas, ASSETS_DUNGEON
import ui_procedural

LARGURA_TELA = 960
ALTURA_TELA = 540
LARGURA_MUNDO = 2600
ALTURA_MUNDO = 1400
NUM_SALAS = 7

# Três zonas verticais coesas (exatamente como especificado)
LIMITE_AEREO = 400     # Y: 0 a 400   -> Camada Superior / Aérea
LIMITE_SUBSOLO = 850   # Y: 400 a 850 -> Camada Central / Térrea Fechada | Y: 850 a 1400 -> Subterrânea

SUB_REGIOES = {
    0: [(0, LIMITE_AEREO, "Ameias da Muralha"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Capela da Guarita"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Criptas de Drenagem")],
    1: [(0, LIMITE_AEREO, "Passarelas da Copa"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Santuário do Bosque"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Esgotos das Raízes")],
    2: [(0, LIMITE_AEREO, "Torres de Vigia"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Bastilha de Ferro"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Masmorras Úmidas")],
    3: [(0, LIMITE_AEREO, "Telhados do Mausoléu"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Nave Funerária"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Ossuário Subterrâneo")],
    4: [(0, LIMITE_AEREO, "Pináculos Sagrados"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Catedral Fechada"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Cisterna Antiga")],
    5: [(0, LIMITE_AEREO, "Passarelas Rubras"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Salão do Trono"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Fendas Subterrâneas")],
    6: [(0, LIMITE_AEREO, "Zênite Astral"), (LIMITE_AEREO, LIMITE_SUBSOLO, "Arquivo Central"), (LIMITE_SUBSOLO, ALTURA_MUNDO, "Cripta do Vazio")],
}

POS_RUNAS_SALA7 = [(1120, 240), (860, 850), (1040, 1240)]

HP_BASE = CONFIG["inimigo_hp_padrao"]


def _pasta_final():
    pasta = CONFIG.get("pasta_assets", "assets")
    return obter_caminho_recurso(os.path.join(pasta, "final_pack"))


RECORTES = {
    "grama":          ("Tiles.png", (128, 17, 96, 47)),
    "caminho":        ("Tiles.png", (160, 84, 64, 44)),
    "banco":          ("Tiles.png", (65, 249, 126, 25)),
    "coluna":         ("Tiles.png", (259, 32, 27, 61)),
    "cerca":          ("Tiles.png", (0, 243, 64, 78)),
    "torre":          ("Tiles.png", (3, 23, 156, 201)),
    "colina":         ("Tiles.png", (160, 146, 160, 78)),
    "estatua":        ("Salt.png",  (7, 23, 98, 201)),
    "arbusto":        ("brush.png", (4, 0, 216, 96)),
    "arbusto_escuro": ("brush.png", (4, 100, 216, 92)),
}
LIMPAR = {"torre": [(118, 0, 40, 48)]}


def _rects(lista, altura=18):
    return [pygame.Rect(x, y, w, altura) for (x, y, w) in lista]


def _altura_suporte_ate_solo(x_centro, y_inicio, paredes, chao, limite_padrao=600):
    """Calcula a distância vertical até a primeira superfície sólida (parede ou chão) abaixo de (x_centro, y_inicio)."""
    melhor_y = chao.top if (chao.left <= x_centro <= chao.right and chao.top >= y_inicio) else (y_inicio + limite_padrao)
    for par in paredes:
        if par.left <= x_centro <= par.right and par.top >= y_inicio:
            if par.top < melhor_y:
                melhor_y = par.top
    return max(8, int(melhor_y - y_inicio))


def _adicionar_suportes_plataforma(suportes, plat, modo, paredes, chao, anchor_x=None):
    """Registra colunas verticais de cantaria, vigas diagonais ou escadarias de sustentação."""
    y_bot = plat.bottom
    if modo == "coluna_dupla" and plat.width >= 110:
        xs = (plat.left + 16, plat.right - 34)
        for cx in xs:
            h_col = _altura_suporte_ate_solo(cx + 9, y_bot, paredes, chao)
            suportes.append({"tipo": "coluna", "plat": plat, "rect": pygame.Rect(cx, y_bot, 18, h_col)})
    elif modo == "coluna_central":
        cx = plat.centerx - 11
        h_col = _altura_suporte_ate_solo(plat.centerx, y_bot, paredes, chao)
        suportes.append({"tipo": "coluna", "plat": plat, "rect": pygame.Rect(cx, y_bot, 22, h_col)})
    elif modo == "viga_esq":
        wall_x = int(anchor_x) if anchor_x is not None else max(0, plat.left - 78)
        suportes.append({
            "tipo": "viga",
            "plat": plat,
            "p1": (wall_x, min(chao.top - 4, y_bot + 54)),
            "p2": (min(plat.right - 16, plat.left + 64), y_bot),
        })
        cx = plat.right - 32
        h_col = _altura_suporte_ate_solo(cx + 9, y_bot, paredes, chao)
        suportes.append({"tipo": "coluna", "plat": plat, "rect": pygame.Rect(cx, y_bot, 18, h_col)})
    elif modo == "viga_dir":
        wall_x = int(anchor_x) if anchor_x is not None else (plat.right + 78)
        suportes.append({
            "tipo": "viga",
            "plat": plat,
            "p1": (wall_x, min(chao.top - 4, y_bot + 54)),
            "p2": (max(plat.left + 16, plat.right - 64), y_bot),
        })
        cx = plat.left + 14
        h_col = _altura_suporte_ate_solo(cx + 9, y_bot, paredes, chao)
        suportes.append({"tipo": "coluna", "plat": plat, "rect": pygame.Rect(cx, y_bot, 18, h_col)})
    elif modo == "escadaria":
        h_esc = _altura_suporte_ate_solo(plat.centerx, y_bot, paredes, chao)
        suportes.append({"tipo": "escadaria", "plat": plat, "rect": pygame.Rect(plat.left + 4, y_bot, max(16, plat.width - 8), h_esc)})


def _recalcular_altura_suportes(suportes, paredes, chao):
    """Sincroniza colunas, vigas e escadarias caso alguma plataforma tenha sido ajustada no headroom."""
    if not suportes:
        return
    for sup in suportes:
        plat = sup.get("plat")
        if plat is None:
            continue
        y_bot = plat.bottom
        if sup["tipo"] in ("coluna", "escadaria"):
            r = sup["rect"]
            r.y = y_bot
            r.height = _altura_suporte_ate_solo(r.centerx, y_bot, paredes, chao)
        elif sup["tipo"] == "viga":
            x1, _ = sup["p1"]
            x2, _ = sup["p2"]
            sup["p1"] = (x1, min(chao.top - 4, y_bot + 54))
            sup["p2"] = (x2, y_bot)


def _limpar_obstaculos_headroom(plataformas, paredes, chao, headroom_min=90, suportes=None):
    """
    Garante pelo menos `headroom_min` px de altura livre vertical acima de toda superfície
    pisável onde haja sobreposição horizontal superior, ajustando/deslocando se necessário.
    """
    solidos = list(paredes)
    for plat in plataformas:
        for par in solidos:
            sobrep_x = min(plat.right, par.right) - max(plat.left, par.left)
            if sobrep_x >= 12 and par.bottom <= plat.top:
                folga = plat.top - par.bottom
                if 0 <= folga < headroom_min:
                    plat.y = par.bottom + headroom_min
        if chao.left < plat.right and chao.right > plat.left and chao.top > plat.top:
            folga_chao = chao.top - plat.bottom
            if 0 < folga_chao < headroom_min and plat.width > 120 and folga_chao >= 62:
                plat.y = chao.top - headroom_min - plat.height

    ordenadas = sorted(plataformas, key=lambda p: p.top)
    for idx_a, sup in enumerate(ordenadas):
        for inf in ordenadas[idx_a + 1:]:
            sobrep_x = min(sup.right, inf.right) - max(sup.left, inf.left)
            if sobrep_x >= 12:
                folga = inf.top - sup.bottom
                if 0 <= folga < headroom_min:
                    nova_y = sup.bottom + headroom_min
                    if nova_y + inf.height <= chao.top - 40:
                        inf.y = nova_y

    _recalcular_altura_suportes(suportes, paredes, chao)


def _escolher_superficie_segura(x_desejado, y_alvo, superficies, spawn_x, usados, dist_min_heroi=320):
    """Encontra a superfície caminhável válida mais próxima respeitando distância do herói e alinhamento."""
    candidatos = []
    for sup in superficies:
        if sup.width < 90:
            continue
        x_clamped = max(sup.left + 24, min(sup.right - 74, int(x_desejado)))
        if abs(x_clamped - spawn_x) < dist_min_heroi:
            if sup.right - 74 >= spawn_x + dist_min_heroi:
                x_clamped = max(sup.left + 24, spawn_x + dist_min_heroi)
            else:
                continue
        colide_entidade = False
        for ux, uy in usados:
            if abs(uy - sup.top) < 85 and abs(x_clamped - ux) < 150:
                colide_entidade = True
                break
            if abs(uy - sup.top) < 260 and abs(x_clamped - ux) < 85:
                colide_entidade = True
                break
        if colide_entidade:
            continue
        score = abs(sup.top - y_alvo) * 1.4 + abs(x_clamped - x_desejado) * 0.4
        candidatos.append((score, x_clamped, sup.top))

    if candidatos:
        candidatos.sort(key=lambda item: item[0])
        _, rx, rtop = candidatos[0]
        return rx, rtop
    return max(spawn_x + dist_min_heroi + 20, int(x_desejado)), y_alvo


def _construir_tipologia_A(sala_idx, cfg, rng):
    """Tipo A — A Grande Torre / Ascensão Vertical (escadarias em espiral e pontes cruzadas até o campanário)."""
    larg_m = rng.choice((1280, 1340, 1400))
    alt_m = 1640
    chao_y = 1570
    chao = pygame.Rect(0, chao_y, larg_m, 70)
    y_camp = rng.choice((354, 364))

    paredes = [
        # Parede oeste (deixa passagem aberta na base 1440..1570)
        pygame.Rect(0, 120, 42, chao_y - 120 - 130),
        # Parede leste maciça da torre
        pygame.Rect(larg_m - 42, 120, 42, chao_y - 120),
        # Campanário: varanda oeste após poço aberto (42..220 livre) e arena leste após portão
        pygame.Rect(220, y_camp, 340, 24),
        pygame.Rect(560, y_camp, larg_m - 602, 26),
        pygame.Rect(548, 0, 48, max(32, y_camp - 180)),
    ]

    plataformas = []
    suportes = []

    def _add_p(x, y, w, modo, anchor_x=None):
        p = pygame.Rect(int(x), int(y), int(w), 18)
        plataformas.append(p)
        _adicionar_suportes_plataforma(suportes, p, modo, paredes, chao, anchor_x=anchor_x)
        return p

    # Subida em espiral com degraus <= 98px e vãos horizontais <= 95px (sem plataformas sobre a cabeça do herói)
    p_s1 = _add_p(420, 1462, 175, "escadaria")
    p_s2 = _add_p(675, 1368, 175, "escadaria")
    p_t1 = _add_p(935, 1272, 290, "viga_dir", anchor_x=larg_m - 42)
    p_b2 = _add_p(550, 1176, 300, "coluna_dupla")
    p_g3 = _add_p(140, 1080, 325, "viga_esq", anchor_x=42)
    p_b4 = _add_p(550, 984, 300, "coluna_dupla")
    p_g5 = _add_p(935, 888, 300, "viga_dir", anchor_x=larg_m - 42)
    p_b6 = _add_p(550, 792, 300, "coluna_dupla")
    p_g7 = _add_p(140, 696, 325, "viga_esq", anchor_x=42)
    p_b8 = _add_p(550, 598, 300, "coluna_dupla")
    p_s9 = _add_p(295, 506, 175, "coluna_central")
    p_s10 = _add_p(66, 446, 134, "viga_esq", anchor_x=42)

    _limpar_obstaculos_headroom(plataformas, paredes, chao, headroom_min=90, suportes=suportes)

    spawn_x = rng.randint(85, 130)
    spawn_heroi = (spawn_x, chao_y - 56)

    portoes = [{
        "id": f"gate_sala{sala_idx + 1}",
        "rect": pygame.Rect(554, y_camp - 180, 36, 180),
        "aberto": False,
        "tipo": cfg.get("gate_tipo", "grade_ferro"),
        "nome": "Portão do Campanário",
    }]

    alav_loc = rng.choice((p_g7, p_g5, p_g3))
    alavancas = [{
        "id": f"alav_s{sala_idx + 1}",
        "x": alav_loc.centerx,
        "y": alav_loc.top,
        "alvo": portoes[0]["id"],
        "acionada": False,
        "texto": "Alavanca do Campanário",
        "msg_destrancado": "Portão do Campanário Destrancado!",
    }]
    chave_loc = rng.choice((p_b6, p_b2))
    chaves = [{
        "id": f"chave_s{sala_idx + 1}",
        "x": chave_loc.centerx,
        "y": chave_loc.top,
        "alvo": portoes[0]["id"],
        "coletada": False,
        "nome": "Chave do Sino",
    }]
    bau_loc = rng.choice((p_g3, p_t1)) if chave_loc is not p_b2 else p_t1
    baus = [{
        "id": f"bau_s{sala_idx + 1}",
        "x": bau_loc.left + 58,
        "y": bau_loc.top,
        "aberto": False,
        "tipo": cfg["bau_tipo"],
        "quantidade": 1 if cfg["bau_tipo"] == "pocao" else 2,
        "nome": "Baú da Torre",
    }]

    superficies = [chao, p_t1, p_b2, p_g3, p_b4, p_g5, p_b6, p_g7, p_b8, paredes[2]]
    alvos_inim = [
        (740, chao_y), (p_t1.centerx, p_t1.top), (p_b4.centerx, p_b4.top),
        (p_g5.centerx, p_g5.top), (p_b8.centerx, p_b8.top), (380, y_camp),
    ]
    usados = [(spawn_x, chao_y)]
    inimigos_spec = []
    for i_idx, spec in enumerate(cfg["inimigos"]):
        ax, ay = alvos_inim[i_idx % len(alvos_inim)]
        ix, itop = _escolher_superficie_segura(ax, ay, superficies, spawn_x, usados, dist_min_heroi=320)
        usados.append((ix, itop))
        inimigos_spec.append({
            "x": ix, "y": itop - 52, "patrulha": spec["patrulha"],
            "nome": spec["nome"], "hp": spec["hp"], "cor": spec["cor"],
            "sprite": spec["sprite"], "combos": spec["combos"],
        })

    boss_x = max(spawn_x + 560, rng.randint(larg_m - 490, larg_m - 390))
    boss = _boss(cfg["boss"]["nome"], cfg["boss"]["hp"], cfg["boss"]["cor"], cfg["boss"]["combos"], cfg["boss"]["sprite"], patrulha=95, x=boss_x, y=y_camp - 88)

    armadilhas = [(pygame.Rect(larg_m - 380, chao_y - 18, 110, 18), cfg["armadilha"])]
    runas = [(p_g3.centerx, p_g3.top), (p_g5.centerx, p_g5.top), (350, y_camp)]

    return {
        "tipologia": "A",
        "nome_tipologia": "Grande Torre",
        "ceu_aberto": True,
        "largura": larg_m,
        "altura": alt_m,
        "chao": chao,
        "paredes": paredes,
        "plataformas": plataformas,
        "suportes": suportes,
        "portoes": portoes,
        "alavancas": alavancas,
        "chaves": chaves,
        "baus": baus,
        "armadilhas": armadilhas,
        "spawn_heroi": spawn_heroi,
        "portal_saida": (larg_m - 190, y_camp - 180),
        "inimigos_spec": inimigos_spec,
        "boss": boss,
        "runas_pos": runas,
        "sub_regioes": [(0, 620, "Campanário da Torre"), (620, 1180, "Escadarias Espirais"), (1180, alt_m, "Átrio da Torre")],
    }


def _construir_tipologia_B(sala_idx, cfg, rng):
    """Tipo B — O Pátio de Ruínas e Abismo (abismo central, descida pelas ruínas para ativar ponte levadiça)."""
    larg_m = rng.choice((2420, 2520, 2620))
    alt_m = 1400
    chao_y = 1340
    chao = pygame.Rect(0, chao_y, larg_m, 60)
    y_patio = rng.choice((850, 870))

    gate_x = 1790
    paredes = [
        # Pátio Oeste (entrada) e Pátio Leste (arena do Chefe) divididos pelo abismo central
        pygame.Rect(0, y_patio, 760, 26),
        pygame.Rect(1640, y_patio, larg_m - 1640, 26),
        # Pilares maciços das escarpas do abismo até o solo profundo
        pygame.Rect(700, y_patio + 26, 60, chao_y - (y_patio + 26)),
        pygame.Rect(1640, y_patio + 26, 60, chao_y - (y_patio + 26)),
        # Muralha maciça do Portão da Bastilha Leste estendendo-se do chão até o topo da tela
        pygame.Rect(gate_x - 10, 0, 58, y_patio - 180),
        pygame.Rect(gate_x - 10, y_patio + 26, 58, chao_y - (y_patio + 26)),
    ]

    plataformas = []
    suportes = []

    def _add_p(x, y, w, modo, anchor_x=None):
        p = pygame.Rect(int(x), int(y), int(w), 18)
        plataformas.append(p)
        _adicionar_suportes_plataforma(suportes, p, modo, paredes, chao, anchor_x=anchor_x)
        return p

    # Pontes destruídas nas bordas do abismo central (deixa vão livre 835..920 para descer antes do portão)
    p_stub_w = _add_p(760, y_patio, 75, "viga_esq", anchor_x=760)
    p_stub_e = _add_p(1480, y_patio, 160, "viga_dir", anchor_x=1640)

    # Descida lateral oeste pelas ruínas (alinhada sob a abertura 835..920)
    p_dw1 = _add_p(795, y_patio + 110, 170, "coluna_dupla")
    p_dw2 = _add_p(995, 1080, 175, "coluna_dupla")
    p_dw3 = _add_p(795, 1188, 175, "escadaria")

    # Ilhas de alvenaria no fundo da vala evitando o fosso central de armadilhas
    p_f1 = _add_p(985, 1232, 170, "escadaria")
    p_f2 = _add_p(1255, 1232, 170, "escadaria")

    # Subida lateral leste saindo do abismo (degraus <= 108px até p_stub_e)
    p_up1 = _add_p(1445, 1184, 170, "escadaria")
    p_up2 = _add_p(1240, 1072, 175, "coluna_dupla")
    p_up3 = _add_p(1435, y_patio + 104, 170, "coluna_dupla")

    # Ruínas altas opcionais no pátio leste após o portão (suportadas por colunas)
    p_alta1 = _add_p(1895, y_patio - 106, 175, "coluna_dupla")
    p_alta2 = _add_p(2075, y_patio - 208, 175, "coluna_dupla")

    _limpar_obstaculos_headroom(plataformas, paredes, chao, headroom_min=90, suportes=suportes)

    spawn_x = rng.randint(85, 130)
    spawn_heroi = (spawn_x, y_patio - 56)

    # Portão assentado no solo do Pátio Leste + Ponte Levadiça sobre o abismo central
    portoes = [{
        "id": f"gate_sala{sala_idx + 1}",
        "rect": pygame.Rect(gate_x, y_patio - 180, 38, 180),
        "ponte": pygame.Rect(835, y_patio, 805, 22),
        "aberto": False,
        "tipo": "ponte_levadica",
        "nome": "Portão e Ponte das Ruínas",
    }]

    alav_loc = rng.choice((p_f1, p_f2, p_dw3))
    alavancas = [{
        "id": f"alav_s{sala_idx + 1}",
        "x": alav_loc.centerx,
        "y": alav_loc.top,
        "alvo": portoes[0]["id"],
        "acionada": False,
        "texto": "Guincho da Ponte Levadiça",
        "msg_destrancado": "Ponte Levadiça Baixada sobre o Abismo!",
    }]
    chaves = [{
        "id": f"chave_s{sala_idx + 1}",
        "x": p_up1.centerx,
        "y": p_up1.top,
        "alvo": portoes[0]["id"],
        "coletada": False,
        "nome": "Chave das Ruínas",
    }]
    baus = [{
        "id": f"bau_s{sala_idx + 1}",
        "x": p_alta2.centerx,
        "y": p_alta2.top,
        "aberto": False,
        "tipo": cfg["bau_tipo"],
        "quantidade": 1 if cfg["bau_tipo"] == "pocao" else 2,
        "nome": "Baú das Ruínas Altas",
    }]

    superficies = [paredes[0], p_dw1, p_dw2, p_f1, p_f2, p_up2, p_alta1, paredes[1]]
    alvos_inim = [
        (560, y_patio), (p_dw1.centerx, p_dw1.top), (p_f1.centerx, p_f1.top),
        (p_f2.centerx, p_f2.top), (p_up2.centerx, p_up2.top), (1710, y_patio),
    ]
    usados = [(spawn_x, y_patio)]
    inimigos_spec = []
    for i_idx, spec in enumerate(cfg["inimigos"]):
        ax, ay = alvos_inim[i_idx % len(alvos_inim)]
        ix, itop = _escolher_superficie_segura(ax, ay, superficies, spawn_x, usados, dist_min_heroi=320)
        usados.append((ix, itop))
        inimigos_spec.append({
            "x": ix, "y": itop - 52, "patrulha": spec["patrulha"],
            "nome": spec["nome"], "hp": spec["hp"], "cor": spec["cor"],
            "sprite": spec["sprite"], "combos": spec["combos"],
        })

    boss_x = max(gate_x + 190, larg_m - 480)
    boss = _boss(cfg["boss"]["nome"], cfg["boss"]["hp"], cfg["boss"]["cor"], cfg["boss"]["combos"], cfg["boss"]["sprite"], patrulha=110, x=boss_x, y=y_patio - 88)

    armadilhas = [(pygame.Rect(1135, chao_y - 20, 130, 20), cfg["armadilha"])]
    runas = [(p_f1.centerx, p_f1.top), (p_up2.centerx, p_up2.top), (p_alta2.centerx, p_alta2.top)]

    return {
        "tipologia": "B",
        "nome_tipologia": "Pátio e Abismo",
        "ceu_aberto": True,
        "largura": larg_m,
        "altura": alt_m,
        "chao": chao,
        "paredes": paredes,
        "plataformas": plataformas,
        "suportes": suportes,
        "portoes": portoes,
        "alavancas": alavancas,
        "chaves": chaves,
        "baus": baus,
        "armadilhas": armadilhas,
        "spawn_heroi": spawn_heroi,
        "portal_saida": (larg_m - 190, y_patio - 180),
        "inimigos_spec": inimigos_spec,
        "boss": boss,
        "runas_pos": runas,
        "sub_regioes": [(0, y_patio + 60, "Pátio das Ruínas"), (y_patio + 60, alt_m, "Fosso do Abismo")],
    }


def _construir_tipologia_C(sala_idx, cfg, rng):
    """Tipo C — Galeria Subterrânea Fechada / Cripta (sem céu aberto, teto abobadado, colunas e candelabros)."""
    larg_m = rng.choice((2480, 2580, 2680))
    y_mid = rng.choice((840, 860))
    y_sup = y_mid - 294
    chao_y = y_mid + 310
    alt_m = chao_y + 70
    chao = pygame.Rect(0, chao_y, larg_m, 70)

    abertura_sup = rng.choice((540, 620))
    abertura_leste = rng.choice((1380, 1480))
    gate_x = larg_m - 760

    paredes = [
        # Teto contínuo abobadado fechando completamente o céu
        pygame.Rect(0, 0, larg_m, 92),
        # Foyer da entrada (seguro ao herói)
        pygame.Rect(0, y_mid, abertura_sup - 40, 26),
        # Espinha central entre túneis sinuosos (com duas aberturas verticais sorteadas)
        pygame.Rect(abertura_sup + 210, y_mid, abertura_leste - (abertura_sup + 210), 26),
        # Santuário leste da Cripta (Boss)
        pygame.Rect(abertura_leste + 210, y_mid, larg_m - (abertura_leste + 210), 26),
        # Galeria abobadada superior (deixa vão livre amplo à esquerda para subida limpa sem bater a cabeça)
        pygame.Rect(555, y_sup, max(280, abertura_leste - 600), 24),
        # Pilastra superior acima do portão da cripta e alicerce inferior até o subsolo
        pygame.Rect(gate_x - 10, 92, 56, max(40, y_mid - 180 - 92)),
        pygame.Rect(gate_x - 10, y_mid + 26, 56, max(40, chao_y - (y_mid + 26))),
    ]

    plataformas = []
    suportes = []

    def _add_p(x, y, w, modo, anchor_x=None):
        p = pygame.Rect(int(x), int(y), int(w), 18)
        plataformas.append(p)
        _adicionar_suportes_plataforma(suportes, p, modo, paredes, chao, anchor_x=anchor_x)
        return p

    # Escadaria oeste conectando foyer ao túnel superior (degraus uniformes de ~98px sem teto em cima)
    p_s1 = _add_p(195, y_mid - 98, 165, "coluna_dupla")
    p_s2 = _add_p(335, y_mid - 196, 155, "coluna_dupla")
    p_sup_cat = _add_p(570, y_sup - 98, 210, "coluna_dupla")
    p_sup_alav = _add_p(1000, y_sup - 98, 195, "coluna_dupla")

    # Descida sinuosa ao ossuário profundo e retorno pelo poço leste (degraus <= 108px, sem quina obstruindo)
    p_d1 = _add_p(abertura_sup - 20, y_mid + 102, 175, "coluna_dupla")
    p_d2 = _add_p(abertura_sup + 205, y_mid + 202, 185, "escadaria")
    p_d3 = _add_p(abertura_sup + 465, y_mid + 202, 195, "coluna_dupla")
    p_d4 = _add_p(abertura_leste - 25, y_mid + 202, 185, "escadaria")
    p_d5 = _add_p(abertura_leste + 10, y_mid + 102, 175, "coluna_dupla")

    _limpar_obstaculos_headroom(plataformas, paredes, chao, headroom_min=90, suportes=suportes)

    spawn_x = rng.randint(85, 130)
    spawn_heroi = (spawn_x, y_mid - 56)

    portoes = [{
        "id": f"gate_sala{sala_idx + 1}",
        "rect": pygame.Rect(gate_x, y_mid - 180, 36, 180),
        "aberto": False,
        "tipo": cfg.get("gate_tipo", "cripta"),
        "nome": "Portão da Cripta Abobadada",
    }]

    alavancas = [{
        "id": f"alav_s{sala_idx + 1}",
        "x": p_sup_alav.centerx,
        "y": p_sup_alav.top,
        "alvo": portoes[0]["id"],
        "acionada": False,
        "texto": "Selo da Abóbada",
        "msg_destrancado": "Portão da Cripta Abobadada Destrancado!",
    }]
    chaves = [{
        "id": f"chave_s{sala_idx + 1}",
        "x": p_d3.centerx,
        "y": p_d3.top,
        "alvo": portoes[0]["id"],
        "coletada": False,
        "nome": "Chave do Ossuário",
    }]
    baus = [{
        "id": f"bau_s{sala_idx + 1}",
        "x": p_sup_cat.centerx,
        "y": p_sup_cat.top,
        "aberto": False,
        "tipo": cfg["bau_tipo"],
        "quantidade": 1 if cfg["bau_tipo"] == "pocao" else 2,
        "nome": "Baú da Galeria",
    }]

    candelabros = [(cx, 92) for cx in range(260, larg_m - 180, 340)]

    superficies = [paredes[1], paredes[2], paredes[4], p_sup_alav, p_d2, p_d3, paredes[3], chao]
    alvos_inim = [
        (p_sup_cat.centerx, p_sup_cat.top), (paredes[4].centerx + 160, y_sup),
        (paredes[2].centerx, y_mid), (p_d3.centerx, p_d3.top),
        (abertura_leste + 100, chao_y), (gate_x - 160, y_mid),
    ]
    usados = [(spawn_x, y_mid)]
    inimigos_spec = []
    for i_idx, spec in enumerate(cfg["inimigos"]):
        ax, ay = alvos_inim[i_idx % len(alvos_inim)]
        ix, itop = _escolher_superficie_segura(ax, ay, superficies, spawn_x, usados, dist_min_heroi=320)
        usados.append((ix, itop))
        inimigos_spec.append({
            "x": ix, "y": itop - 52, "patrulha": spec["patrulha"],
            "nome": spec["nome"], "hp": spec["hp"], "cor": spec["cor"],
            "sprite": spec["sprite"], "combos": spec["combos"],
        })

    boss_x = max(gate_x + 170, larg_m - 460)
    boss = _boss(cfg["boss"]["nome"], cfg["boss"]["hp"], cfg["boss"]["cor"], cfg["boss"]["combos"], cfg["boss"]["sprite"], patrulha=100, x=boss_x, y=y_mid - 88)

    armadilhas = [
        (pygame.Rect(abertura_sup + 80, chao_y - 20, 120, 20), cfg["armadilha"]),
        (pygame.Rect(abertura_leste - 240, chao_y - 20, 120, 20), cfg["armadilha"]),
    ]
    runas = [(p_sup_alav.centerx, p_sup_alav.top), (p_d3.centerx, p_d3.top), (paredes[2].centerx, y_mid)]

    return {
        "tipologia": "C",
        "nome_tipologia": "Cripta Abobadada",
        "ceu_aberto": False,
        "candelabros": candelabros,
        "largura": larg_m,
        "altura": alt_m,
        "chao": chao,
        "paredes": paredes,
        "plataformas": plataformas,
        "suportes": suportes,
        "portoes": portoes,
        "alavancas": alavancas,
        "chaves": chaves,
        "baus": baus,
        "armadilhas": armadilhas,
        "spawn_heroi": spawn_heroi,
        "portal_saida": (larg_m - 190, y_mid - 180),
        "inimigos_spec": inimigos_spec,
        "boss": boss,
        "runas_pos": runas,
        "sub_regioes": [(0, y_sup + 40, "Abóbada Superior"), (y_sup + 40, y_mid + 40, "Túnel da Cripta"), (y_mid + 40, alt_m, "Ossuário Profundo")],
    }


def _construir_tipologia_D(sala_idx, cfg, rng):
    """Tipo D — Muralha Longa com Bastilhas (fortaleza horizontal com guaritas fechadas transitáveis)."""
    larg_m = rng.choice((2720, 2860, 3000))
    alt_m = 1080
    chao_y = 1010
    chao = pygame.Rect(0, chao_y, larg_m, 70)
    y_muralha = 780

    g1_x = rng.choice((510, 560))
    g1_w = 380
    g1_teto = 480

    g2_x = rng.choice((1320, 1400))
    g2_w = 420
    g2_teto = 460

    gate_x = g2_x + g2_w + 170

    # Duas guaritas fechadas com portas abertas ao nível do piso (122px de vão livre para entrar e sair)
    paredes = [
        # Piso contínuo da muralha externa
        pygame.Rect(0, y_muralha, larg_m, 28),
        # Guarita 1 (Oeste): teto + paredes com vãos de porta 658..780
        pygame.Rect(g1_x - 10, g1_teto, g1_w + 20, 26),
        pygame.Rect(g1_x, g1_teto + 26, 26, (y_muralha - 122) - (g1_teto + 26)),
        pygame.Rect(g1_x + g1_w - 26, g1_teto + 26, 26, (y_muralha - 122) - (g1_teto + 26)),
        # Guarita 2 (Central-Leste): teto + paredes com vãos de porta 658..780
        pygame.Rect(g2_x - 10, g2_teto, g2_w + 20, 26),
        pygame.Rect(g2_x, g2_teto + 26, 26, (y_muralha - 122) - (g2_teto + 26)),
        pygame.Rect(g2_x + g2_w - 26, g2_teto + 26, 26, (y_muralha - 122) - (g2_teto + 26)),
        # Muralha maciça do Portão da Bastilha Leste (do topo ao alicerce)
        pygame.Rect(gate_x - 10, 0, 56, max(40, y_muralha - 180)),
        pygame.Rect(gate_x - 10, y_muralha + 28, 56, max(40, chao_y - (y_muralha + 28))),
    ]

    guaritas = [
        {"rect": pygame.Rect(g1_x, g1_teto + 26, g1_w, y_muralha - (g1_teto + 26))},
        {"rect": pygame.Rect(g2_x, g2_teto + 26, g2_w, y_muralha - (g2_teto + 26))},
    ]

    plataformas = []
    suportes = []

    def _add_p(x, y, w, modo, anchor_x=None):
        p = pygame.Rect(int(x), int(y), int(w), 18)
        plataformas.append(p)
        _adicionar_suportes_plataforma(suportes, p, modo, paredes, chao, anchor_x=anchor_x)
        return p

    # Escada externa para o telhado da Guarita 1 (degraus <= 104px, sem sobreposição baixa na cabeça)
    p_ext1 = _add_p(g1_x - 140, 682, 130, "viga_dir", anchor_x=g1_x)
    p_ext2 = _add_p(g1_x - 235, 578, 135, "coluna_dupla")
    # Passarela entre tetos das duas guaritas
    p_ponte_teto = _add_p(g1_x + g1_w + 35, 470, max(160, g2_x - (g1_x + g1_w) - 70), "coluna_dupla")
    # Balcões internos dentro das guaritas (<= 106px do piso e >= 170px de headroom até o teto)
    p_int1 = _add_p(g1_x + 100, 676, 175, "coluna_dupla")
    p_int2 = _add_p(g2_x + 115, 674, 185, "coluna_dupla")
    # Subida pós-guarita 2 e plataforma tática no pátio do Chefe (alcançáveis com folga)
    p_ext3 = _add_p(g2_x + g2_w + 25, 682, 120, "viga_esq", anchor_x=g2_x + g2_w)
    p_arena = _add_p(gate_x + 140, 680, 190, "coluna_dupla")

    _limpar_obstaculos_headroom(plataformas, paredes, chao, headroom_min=90, suportes=suportes)

    spawn_x = rng.randint(85, 130)
    spawn_heroi = (spawn_x, y_muralha - 56)

    portoes = [{
        "id": f"gate_sala{sala_idx + 1}",
        "rect": pygame.Rect(gate_x, y_muralha - 180, 36, 180),
        "aberto": False,
        "tipo": cfg.get("gate_tipo", "grade_ferro"),
        "nome": "Portão da Bastilha Leste",
    }]

    alav_loc = rng.choice((pygame.Rect(g1_x + g1_w // 2 - 40, g1_teto, 80, 26), pygame.Rect(g2_x + g2_w // 2 - 40, g2_teto, 80, 26), p_int2))
    alavancas = [{
        "id": f"alav_s{sala_idx + 1}",
        "x": alav_loc.centerx,
        "y": alav_loc.top,
        "alvo": portoes[0]["id"],
        "acionada": False,
        "texto": "Alavanca da Guarita",
        "msg_destrancado": "Portão da Bastilha Leste Suspenso!",
    }]
    chaves = [{
        "id": f"chave_s{sala_idx + 1}",
        "x": p_int1.centerx,
        "y": p_int1.top,
        "alvo": portoes[0]["id"],
        "coletada": False,
        "nome": "Chave da Guarda",
    }]
    baus = [{
        "id": f"bau_s{sala_idx + 1}",
        "x": g2_x + 70,
        "y": y_muralha,
        "aberto": False,
        "tipo": cfg["bau_tipo"],
        "quantidade": 1 if cfg["bau_tipo"] == "pocao" else 2,
        "nome": "Baú da Guarita",
    }]

    superficies = [paredes[0], paredes[1], paredes[4], p_ponte_teto, p_int1, p_int2, p_arena]
    alvos_inim = [
        (g1_x + 210, y_muralha), (g1_x + g1_w // 2, g1_teto),
        (p_ponte_teto.centerx, p_ponte_teto.top), (g2_x + 220, y_muralha),
        (g2_x + g2_w // 2, g2_teto), (gate_x - 140, y_muralha),
    ]
    usados = [(spawn_x, y_muralha)]
    inimigos_spec = []
    for i_idx, spec in enumerate(cfg["inimigos"]):
        ax, ay = alvos_inim[i_idx % len(alvos_inim)]
        ix, itop = _escolher_superficie_segura(ax, ay, superficies, spawn_x, usados, dist_min_heroi=320)
        usados.append((ix, itop))
        inimigos_spec.append({
            "x": ix, "y": itop - 52, "patrulha": spec["patrulha"],
            "nome": spec["nome"], "hp": spec["hp"], "cor": spec["cor"],
            "sprite": spec["sprite"], "combos": spec["combos"],
        })

    boss_x = max(gate_x + 200, larg_m - 460)
    boss = _boss(cfg["boss"]["nome"], cfg["boss"]["hp"], cfg["boss"]["cor"], cfg["boss"]["combos"], cfg["boss"]["sprite"], patrulha=100, x=boss_x, y=y_muralha - 88)

    armadilhas = [(pygame.Rect(g1_x + g1_w + 80, y_muralha - 16, 110, 16), cfg["armadilha"])]
    runas = [(p_int1.centerx, p_int1.top), (p_ponte_teto.centerx, p_ponte_teto.top), (p_int2.centerx, p_int2.top)]

    return {
        "tipologia": "D",
        "nome_tipologia": "Muralha e Bastilhas",
        "ceu_aberto": True,
        "guaritas": guaritas,
        "largura": larg_m,
        "altura": alt_m,
        "chao": chao,
        "paredes": paredes,
        "plataformas": plataformas,
        "suportes": suportes,
        "portoes": portoes,
        "alavancas": alavancas,
        "chaves": chaves,
        "baus": baus,
        "armadilhas": armadilhas,
        "spawn_heroi": spawn_heroi,
        "portal_saida": (larg_m - 190, y_muralha - 180),
        "inimigos_spec": inimigos_spec,
        "boss": boss,
        "runas_pos": runas,
        "sub_regioes": [(0, 520, "Ameias das Bastilhas"), (520, y_muralha + 35, "Muralha e Guaritas"), (y_muralha + 35, alt_m, "Alicerces da Muralha")],
    }


def _boss(nome, hp, cor, combos, sprite, patrulha=100, x=2120, y=LIMITE_SUBSOLO - 88):
    return {
        "x": x, "y": y, "patrulha": patrulha, "nome": nome, "hp": hp,
        "cor": cor, "combos": combos, "sprite": sprite,
    }


def _spec_inimigo(nome, hp, cor, sprite, patrulha, combos):
    return {"nome": nome, "hp": hp, "cor": cor, "sprite": sprite, "patrulha": patrulha, "combos": combos}


_CONFIGS_SALAS_TEMATICAS = {
    0: {
        "nome": "Cemitério da Lua Pálida",
        "cor_fundo": (12, 16, 28),
        "visual": {"mid": False, "grama": 1, "tint": (10, 18, 42, 22), "chao": "cripta", "plataforma": "pedra",
                   "vagalumes": (150, 235, 160), "decor": [("coluna", 580, 1.0, 1.0), ("estatua", 1860, 0.85, 1.0)]},
        "inimigos": [
            _spec_inimigo("Coveiro Sombrio", HP_BASE, (200, 50, 65), "Demon Carmesim", 90, 2),
            _spec_inimigo("Corvo da Lápide", HP_BASE - 15, (80, 150, 205), "Orc", 55, 2),
            _spec_inimigo("Sineiro Maldito", HP_BASE + 10, (240, 95, 55), "Demon Carmesim", 65, 2),
            _spec_inimigo("Vigia da Cripta", HP_BASE + 15, (130, 65, 150), "Blood Monster_A", 65, 2),
            _spec_inimigo("Espectro do Esgoto", HP_BASE + 20, (120, 60, 180), "Esqueleto", 95, 2),
            _spec_inimigo("Carrasco da Lua", HP_BASE + 30, (170, 45, 85), "Blood Monster_A", 80, 2),
        ],
        "boss": _boss("BOSS: GUARDIÃO DO CEMITÉRIO", CONFIG["boss_sala1_hp"], (155, 30, 195), 3, "Boss_Guardiao"),
        "gate_tipo": "grade_ferro", "bau_tipo": "pocao", "armadilha": "espinhos", "objetivo_tipo": "alavanca", "semente": 101,
    },
    1: {
        "nome": "Bosque da Árvore Torta",
        "cor_fundo": (10, 20, 18),
        "visual": {"mid": False, "grama": 2, "tint": (12, 36, 18, 30), "chao": "bosque", "plataforma": "madeira",
                   "vagalumes": (190, 245, 90), "decor": [("arbusto", 540, 0.55, 1.0), ("coluna", 1900, 1.0, 1.0)]},
        "inimigos": [
            _spec_inimigo("Lenhador Corrompido", HP_BASE, (210, 70, 55), "Aberração Hemática", 80, 2),
            _spec_inimigo("Druida Corrompido", HP_BASE + 25, (80, 120, 80), "Aberração Hemática", 65, 3),
            _spec_inimigo("Espantalho Faminto", HP_BASE + 20, (125, 75, 145), "Blood Monster_A", 55, 2),
            _spec_inimigo("Guardião da Hera", HP_BASE + 15, (180, 50, 95), "Aberração Hemática", 65, 2),
            _spec_inimigo("Lobo do Pântano", HP_BASE + 20, (210, 55, 65), "Demon Carmesim", 110, 2),
            _spec_inimigo("Ent Apodrecido", HP_BASE + 35, (155, 65, 110), "Aberração Hemática", 80, 2),
        ],
        "boss": _boss("BOSS: ENTE DA ÁRVORE TORTA", CONFIG["boss_sala2_hp"], (215, 130, 30), 3, "Boss_Ente"),
        "gate_tipo": "raizes", "bau_tipo": "eter", "armadilha": "veneno", "objetivo_tipo": "chave", "semente": 202,
    },
    2: {
        "nome": "Portões de Ferro",
        "cor_fundo": (13, 15, 26),
        "visual": {"mid": True, "grama": 1, "tint": (18, 22, 55, 35), "chao": "ferro", "plataforma": "ferro",
                   "vagalumes": (170, 205, 255), "decor": [("cerca", 560, 1.2, 1.0), ("torre", 1820, 0.85, 1.0)]},
        "inimigos": [
            _spec_inimigo("Sentinela de Ferro", HP_BASE + 10, (170, 40, 110), "Blood Monster_A", 90, 2),
            _spec_inimigo("Bruto da Forja", HP_BASE + 15, (190, 40, 80), "Orc", 60, 2),
            _spec_inimigo("Carrasco Corrompido", HP_BASE + 30, (180, 60, 90), "Demon Carmesim", 65, 3),
            _spec_inimigo("Algoz da Grade", HP_BASE + 30, (120, 45, 160), "Esqueleto", 60, 2),
            _spec_inimigo("Cão de Guarda", HP_BASE + 25, (210, 45, 65), "Demon Carmesim", 100, 2),
            _spec_inimigo("Guardião do Baluarte", HP_BASE + 40, (170, 35, 130), "Blood Monster_A", 80, 3),
        ],
        "boss": _boss("BOSS: CARCEREIRO DOS PORTÕES", CONFIG["boss_sala3_hp"], (220, 35, 95), 4, "Boss_Carcereiro"),
        "gate_tipo": "grade_ferro", "bau_tipo": "pocao", "armadilha": "espinhos", "objetivo_tipo": "selos_duplos", "semente": 303,
    },
    3: {
        "nome": "Mausoléu Esquecido",
        "cor_fundo": (16, 10, 28),
        "visual": {"mid": True, "grama": 2, "tint": (42, 16, 70, 40), "chao": "cripta", "plataforma": "cripta",
                   "vagalumes": (215, 140, 255), "decor": [("coluna", 620, 1.1, 1.0), ("estatua", 1900, 0.9, 1.0)]},
        "inimigos": [
            _spec_inimigo("Acólito do Mausoléu", 165, (135, 55, 210), "Necromante", 80, 2),
            _spec_inimigo("Aprendiz da Cripta", 155, (110, 45, 190), "Necromante", 60, 3),
            _spec_inimigo("Mago das Cinzas", 190, (175, 65, 205), "Necromante", 65, 3),
            _spec_inimigo("Lich das Profundezas", 225, (170, 60, 230), "Necromante", 65, 3),
            _spec_inimigo("Necromante Errante", 200, (155, 55, 230), "Necromante", 95, 3),
            _spec_inimigo("Ceifador Antigo", 240, (180, 50, 220), "Blood Monster_A", 80, 3),
        ],
        "boss": _boss("CHEFE: ZELADOR DO MAUSOLÉU", 520, (170, 45, 240), 4, "Boss_Mausoleu"),
        "gate_tipo": "cripta", "bau_tipo": "pocao", "armadilha": "ossos", "objetivo_tipo": "alavanca", "semente": 404,
    },
    4: {
        "nome": "Salão da Estátua Sombria",
        "cor_fundo": (15, 12, 26),
        "visual": {"mid": True, "grama": 1, "tint": (24, 14, 46, 45), "chao": "catedral", "plataforma": "catedral",
                   "vagalumes": (255, 180, 235), "decor": [("estatua", 620, 1.0, 1.0), ("estatua", 1900, 1.0, 1.0)]},
        "inimigos": [
            _spec_inimigo("Esqueleto Reanimado", 180, (155, 65, 195), "Necromante", 80, 2),
            _spec_inimigo("Acólito das Cinzas", 190, (130, 50, 210), "Necromante", 60, 3),
            _spec_inimigo("Invocador de Almas", 215, (190, 70, 230), "Demon_A", 65, 3),
            _spec_inimigo("Lich Menor", 230, (165, 55, 235), "Demon_A", 65, 3),
            _spec_inimigo("Sentinela de Pedra", 210, (95, 55, 170), "Blood Monster_A", 95, 3),
            _spec_inimigo("Golem de Pedra", 245, (100, 90, 80), "Orc", 85, 3),
        ],
        "boss": _boss("CHEFE: SENTINELA DE PEDRA", 620, (190, 55, 255), 4, "Boss_Sentinela"),
        "gate_tipo": "catedral", "bau_tipo": "eter", "armadilha": "vazio", "objetivo_tipo": "selos_duplos", "semente": 505,
    },
    5: {
        "nome": "Trono da Lua Sangrenta",
        "cor_fundo": (24, 8, 16),
        "visual": {"mid": True, "grama": 2, "tint": (85, 12, 24, 50), "chao": "sangue", "plataforma": "sangue",
                   "vagalumes": (255, 95, 95), "decor": [("estatua", 620, 1.0, 1.0), ("coluna", 1900, 1.1, 1.0)]},
        "inimigos": [
            _spec_inimigo("Cavaleiro Reanimado", 215, (130, 50, 210), "Necromante", 85, 2),
            _spec_inimigo("Acólito Real", 225, (160, 60, 225), "Necromante", 60, 3),
            _spec_inimigo("Arauto da Morte", 240, (185, 70, 240), "Demon_A", 65, 3),
            _spec_inimigo("Campeão da Lua", 260, (110, 50, 200), "Blood Monster_A", 65, 3),
            _spec_inimigo("Guardião Real", 235, (100, 45, 185), "Blood Monster_A", 95, 3),
            _spec_inimigo("Pretor Sanguinário", 295, (190, 25, 55), "Blood Monster_A", 85, 3),
        ],
        "boss": _boss("CHEFE FINAL: REI DA LUA SANGRENTA", 780, (205, 65, 255), 5, "Boss_ReiSangrento"),
        "gate_tipo": "sangue", "bau_tipo": "pocao", "armadilha": "sangue", "objetivo_tipo": "selos_duplos", "semente": 606,
    },
    6: {
        "nome": "Arquivo das Almas",
        "cor_fundo": (10, 13, 28),
        "visual": {"mid": True, "grama": 2, "tint": (18, 22, 68, 50), "chao": "arcano", "plataforma": "arcano",
                   "vagalumes": (140, 225, 255), "decor": [("coluna", 620, 1.1, 1.0), ("estatua", 1900, 0.9, 1.0)]},
        "inimigos": [
            _spec_inimigo("Guardião das Páginas", 260, (100, 170, 220), "Orc", 85, 3),
            _spec_inimigo("Oráculo Partido", 285, (175, 75, 235), "Necromante", 60, 3),
            _spec_inimigo("Escriba Imortal", 315, (160, 90, 245), "Necromante", 65, 3),
            _spec_inimigo("Bibliotecário Sombrio", 280, (120, 80, 180), "Demon Carmesim", 65, 3),
            _spec_inimigo("Sentinela de Sal", 265, (190, 205, 220), "Blood Monster_A", 95, 3),
            _spec_inimigo("Curador Profano", 295, (170, 100, 200), "Necromante", 85, 3),
        ],
        "boss": _boss("CHEFE FINAL: BIBLIOTECÁRIO DO VAZIO", 950, (220, 90, 255), 5, "Boss_Bibliotecario"),
        "gate_tipo": "arcano", "bau_tipo": "eter", "armadilha": "arcano", "objetivo_tipo": "runas_vazio", "semente": 707,
    },
}

_CONSTRUTORES_TIPOLOGIA = {
    "A": _construir_tipologia_A,
    "B": _construir_tipologia_B,
    "C": _construir_tipologia_C,
    "D": _construir_tipologia_D,
}

DADOS_MAPAS = {}
ARMADILHAS_SALAS = {}


def validar_mapa_procedural(mapa):
    """Valida spawn desobstruído, espaçamento >= 320px, suportes, não-empilhamento e headroom >= 90px."""
    sx, sy = mapa["spawn_heroi"]
    erros = []
    if not (80 <= sx <= 140):
        erros.append(f"spawn_heroi.x fora da entrada segura: {sx}")

    hero_box = pygame.Rect(int(sx), int(sy), 36, 56)
    paredes = mapa.get("paredes", [])
    for par in paredes:
        if hero_box.colliderect(par):
            erros.append(f"spawn_heroi colide com parede {par}")
    for gate in mapa.get("portoes", []):
        if hero_box.colliderect(gate["rect"]):
            erros.append("spawn_heroi colide com portão")
    for arm, _ in mapa.get("armadilhas", []):
        if hero_box.inflate(24, 0).colliderect(arm):
            erros.append(f"spawn_heroi próximo/sobre armadilha {arm}")

    pe_y = int(sy + 56)
    chao = mapa.get("chao")
    tem_piso = (chao is not None and chao.left <= sx <= chao.right and abs(chao.top - pe_y) <= 4)
    if not tem_piso:
        tem_piso = any(p.left <= sx and (sx + 36) <= p.right and abs(p.top - pe_y) <= 4 for p in paredes)
    if not tem_piso:
        erros.append(f"spawn_heroi sem piso sólido logo abaixo dos pés em y={pe_y}")

    inims = mapa.get("inimigos_spec", [])
    for idx_i, inim in enumerate(inims):
        if abs(inim["x"] - sx) < 320:
            erros.append(f"inimigo {inim['nome']} muito próximo do herói: dx={abs(inim['x'] - sx)}")
        for outro in inims[idx_i + 1:]:
            dx = abs(inim["x"] - outro["x"])
            dy = abs(inim["y"] - outro["y"])
            if (dy < 85 and dx < 150) or (dy < 260 and dx < 85):
                erros.append(f"inimigos empilhados/próximos ({inim['nome']} vs {outro['nome']}): dx={dx}, dy={dy}")
    if abs(mapa["boss"]["x"] - sx) < 320:
        erros.append("chefe muito próximo do herói")

    plats = mapa.get("plataformas", [])
    suportes = mapa.get("suportes", [])
    if len(suportes) < len(plats):
        erros.append(f"plataformas sem suporte arquitetural: suportes={len(suportes)} < plats={len(plats)}")

    paredes = mapa.get("paredes", [])
    ordenadas = sorted(plats, key=lambda p: p.top)
    for p in plats:
        for par in paredes:
            if min(p.right, par.right) - max(p.left, par.left) >= 12 and par.bottom <= p.top:
                if 0 <= (p.top - par.bottom) < 90:
                    erros.append(f"headroom insuficiente sob parede em y={p.top} (folga={p.top - par.bottom})")
    for i_p, sup_p in enumerate(ordenadas):
        for inf_p in ordenadas[i_p + 1:]:
            if min(sup_p.right, inf_p.right) - max(sup_p.left, inf_p.left) >= 12:
                if 0 <= (inf_p.top - sup_p.bottom) < 90:
                    erros.append(f"headroom insuficiente entre plataformas ({sup_p.bottom}->{inf_p.top})")
    return erros


GERENCIADOR_SALAS = GerenciadorSalas()


def _sortear_dicionario_salas(rng=None):
    """Constrói as 7 salas góticas em 4 biomas distintos sem repetição monótona via GerenciadorSalas."""
    semente = rng.randint(1, 999999) if rng is not None else None
    return GERENCIADOR_SALAS.construir_todas_salas(semente_base=semente)


def atualizar_salas(sala_idx, dt, tempo):
    """Atualiza elementos dinâmicos (como plataformas móveis na Cripta dos Ossos)."""
    mapa = DADOS_MAPAS.get(sala_idx)
    if mapa is not None:
        GERENCIADOR_SALAS.atualizar_sala(mapa, dt, tempo)


def regerar_salas_procedurais(semente_base=None):
    """Reconstroi as 7 salas temáticas em seus 4 biomas e reaquece caches gráficos."""
    novas = GERENCIADOR_SALAS.construir_todas_salas(semente_base=semente_base)

    DADOS_MAPAS.clear()
    DADOS_MAPAS.update(novas)
    ARMADILHAS_SALAS.clear()
    ARMADILHAS_SALAS.update({idx: dados.get("armadilhas", []) for idx, dados in DADOS_MAPAS.items()})
    POS_RUNAS_SALA7[:] = DADOS_MAPAS[6].get("runas_pos", POS_RUNAS_SALA7)

    _camadas_cache.clear()
    _CACHE_PAREDES.clear()
    _CACHE_CHAO_STRIPS.clear()
    _CACHE_PLATAFORMAS.clear()

    if _pronto:
        for idx, mapa in DADOS_MAPAS.items():
            _fundos[idx] = _montar_fundo(idx)
            r, g, b, a = mapa["visual"]["tint"]
            sup = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            sup.fill((r, g, b, a))
            _tints[idx] = sup
            _obter_chao_strip(idx)
            est_plat = mapa["visual"].get("plataforma", "pedra")
            for plat in mapa.get("plataformas", []):
                ch_p = (est_plat, plat.width, plat.height)
                if ch_p not in _CACHE_PLATAFORMAS:
                    _CACHE_PLATAFORMAS[ch_p] = _renderizar_textura_plataforma(est_plat, plat.width, plat.height)
            for par in mapa.get("paredes", []):
                _obter_parede_surface(idx, par)
            _construir_arquitetura_3_camadas(idx)


# Gera automaticamente as 7 salas no carregamento via GerenciadorSalas
def _inicializar_salas_iniciais():
    novas = GERENCIADOR_SALAS.construir_todas_salas()
    DADOS_MAPAS.clear()
    DADOS_MAPAS.update(novas)
    ARMADILHAS_SALAS.clear()
    ARMADILHAS_SALAS.update({idx: dados.get("armadilhas", []) for idx, dados in DADOS_MAPAS.items()})
    POS_RUNAS_SALA7[:] = DADOS_MAPAS[6].get("runas_pos", POS_RUNAS_SALA7)


_inicializar_salas_iniciais()

_arquivos = {}
_pecas = {}
_pecas_escala = {}
_fundos = {}
_tints = {}
_miniaturas = {}
_camadas_cache = {}
_pronto = False
COR_TERRA = (21, 24, 36)

# ==============================================================================
# GERADOR PROCEDURAL DE TEXTURAS 32x32 (PixelArray) & AUTOTILING
# ==============================================================================
TAM_TILE = 32

COR_ARGAMASSA_CANTARIA  = (10, 12, 20, 255)    # #0A0C14
COR_LUZ_CANTARIA        = (71, 85, 105, 255)   # #475569
COR_SOMBRA_CANTARIA     = (30, 41, 59, 255)    # #1E293B
COR_MIOLO_CANTARIA      = (
    (39, 48, 67, 255),                         # #273043
    (34, 41, 56, 255),                         # #222938
    (28, 34, 48, 255),                         # #1C2230
)
COR_TRINCA_CANTARIA     = (5, 7, 11, 255)      # #05070B

COR_ARDOSIA_SUBSOLO     = (21, 24, 36, 255)    # #151824
COR_MUSGO_OLIVA         = (20, 83, 45, 255)    # #14532D
COR_MUSGO_VIVO          = (22, 101, 52, 255)   # #166534
COR_BRILHO_ETER         = (56, 189, 248, 255)  # #38BDF8

_ESTILOS_BLOCO = {
    "pedra": {
        "tipo": "cantaria",
        "argamassa": COR_ARGAMASSA_CANTARIA,
        "luz": COR_LUZ_CANTARIA,
        "sombra": COR_SOMBRA_CANTARIA,
        "miolo": COR_MIOLO_CANTARIA,
        "laje_clara": (148, 163, 184, 255),
        "laje_topo": (100, 116, 139, 255),
        "laje_meio": (51, 65, 85, 255),
        "musgo": True,
        "glint": (56, 189, 248, 255),
    },
    "cripta": {
        "tipo": "cantaria",
        "argamassa": COR_ARGAMASSA_CANTARIA,
        "luz": (92, 82, 128, 255),
        "sombra": (26, 24, 44, 255),
        "miolo": ((42, 36, 62, 255), (34, 29, 51, 255), (27, 23, 41, 255)),
        "laje_clara": (148, 134, 188, 255),
        "laje_topo": (108, 92, 148, 255),
        "laje_meio": (54, 46, 78, 255),
        "musgo": True,
        "glint": COR_BRILHO_ETER,
    },
    "ferro": {
        "tipo": "ferro",
        "argamassa": COR_ARGAMASSA_CANTARIA,
        "luz": (110, 124, 148, 255),
        "sombra": (24, 29, 42, 255),
        "miolo": ((54, 62, 78, 255), (44, 51, 66, 255), (36, 42, 55, 255)),
        "laje_clara": (176, 190, 212, 255),
        "laje_topo": (118, 132, 156, 255),
        "laje_meio": (62, 72, 92, 255),
        "musgo": False,
        "glint": (148, 163, 184, 255),
    },
    "madeira": {
        "tipo": "madeira",
        "argamassa": (14, 9, 6, 255),
        "luz": (152, 102, 58, 255),
        "sombra": (36, 22, 14, 255),
        "miolo": ((86, 54, 32, 255), (72, 44, 26, 255), (58, 35, 20, 255)),
        "laje_clara": (182, 128, 76, 255),
        "laje_topo": (136, 90, 48, 255),
        "laje_meio": (78, 48, 28, 255),
        "musgo": True,
        "glint": None,
    },
    "bosque": {
        "tipo": "cantaria",
        "argamassa": COR_ARGAMASSA_CANTARIA,
        "luz": (74, 98, 86, 255),
        "sombra": (24, 36, 32, 255),
        "miolo": ((38, 52, 48, 255), (31, 44, 40, 255), (24, 35, 33, 255)),
        "laje_clara": (132, 176, 122, 255),
        "laje_topo": (74, 128, 82, 255),
        "laje_meio": (42, 68, 52, 255),
        "musgo": True,
        "glint": COR_BRILHO_ETER,
    },
    "catedral": {
        "tipo": "cantaria",
        "argamassa": (22, 19, 26, 255),
        "luz": (206, 198, 184, 255),
        "sombra": (78, 72, 70, 255),
        "miolo": ((142, 136, 128, 255), (124, 118, 112, 255), (106, 100, 96, 255)),
        "laje_clara": (245, 234, 205, 255),
        "laje_topo": (217, 158, 62, 255),
        "laje_meio": (128, 116, 108, 255),
        "musgo": False,
        "glint": (253, 230, 138, 255),
    },
    "sangue": {
        "tipo": "cantaria",
        "argamassa": (10, 5, 8, 255),
        "luz": (138, 46, 58, 255),
        "sombra": (28, 12, 18, 255),
        "miolo": ((54, 22, 30, 255), (44, 17, 24, 255), (34, 13, 19, 255)),
        "laje_clara": (215, 82, 92, 255),
        "laje_topo": (156, 38, 52, 255),
        "laje_meio": (64, 24, 34, 255),
        "musgo": False,
        "glint": (244, 63, 94, 255),
    },
    "arcano": {
        "tipo": "cantaria",
        "argamassa": (6, 10, 20, 255),
        "luz": (78, 126, 176, 255),
        "sombra": (16, 24, 48, 255),
        "miolo": ((28, 40, 72, 255), (22, 32, 58, 255), (18, 25, 46, 255)),
        "laje_clara": (148, 224, 255, 255),
        "laje_topo": (56, 189, 248, 255),
        "laje_meio": (32, 54, 92, 255),
        "musgo": False,
        "glint": COR_BRILHO_ETER,
    },
}

_ATLAS_32 = {}
_CACHE_TILES_AUTOTILE = {}
_CACHE_BORDAS = {}
_CACHE_PLATAFORMAS = {}
_CACHE_PAREDES = {}
_CACHE_CHAO_STRIPS = {}
_CACHE_PINACULOS = {}
_CACHE_AMEIAS = {}
_CACHE_PORTAO_BATENTE = {}
_CACHE_ALAVANCA_BASE = None
_CACHE_BAUS = {}


def _converter_surf(surf):
    if pygame.display.get_surface() is not None:
        try:
            return surf.convert_alpha()
        except pygame.error:
            pass
    return surf


def _escurecer_cor(cor, fator):
    return (
        max(0, min(255, int(cor[0] * fator))),
        max(0, min(255, int(cor[1] * fator))),
        max(0, min(255, int(cor[2] * fator))),
        cor[3] if len(cor) > 3 else 255,
    )


def gerar_textura_cantaria_32x32(semente=0, estilo="pedra", escuro=False):
    """
    Gera tile 32x32 px de Cantaria Gótica via pygame.PixelArray:
    - 3 fileiras de tijolos intercalados em alvenaria clássica contínua
    - Argamassa de 1px (#0A0C14)
    - Volume 3D por tijolo (luz superior/esquerda #475569, sombra chanfrada #1E293B)
    - Miolo com dither estocástico em 3 tons (#273043, #222938, #1C2230)
    - 1 a 2 trincas diagonais aleatórias (#05070B) para aspecto de ruína
    """
    pal = _ESTILOS_BLOCO.get(estilo, _ESTILOS_BLOCO["pedra"])
    tipo = pal.get("tipo", "cantaria")
    fator = 0.68 if escuro else 1.0

    c_arg = _escurecer_cor(pal["argamassa"], fator)
    c_luz = _escurecer_cor(pal["luz"], fator)
    c_somb = _escurecer_cor(pal["sombra"], fator)
    c_miolo = tuple(_escurecer_cor(c, fator) for c in pal["miolo"])
    c_trinca = _escurecer_cor(COR_TRINCA_CANTARIA, fator)

    surf = pygame.Surface((TAM_TILE, TAM_TILE), pygame.SRCALPHA)
    rng = random.Random(int(semente) * 7919 + hash(estilo) & 0xFFFF)
    pa = pygame.PixelArray(surf)
    try:
        m = surf.map_rgb
        m_arg = m(c_arg)
        m_luz = m(c_luz)
        m_somb = m(c_somb)
        m_miolo = [m(c) for c in c_miolo]
        m_trinca = m(c_trinca)

        if tipo == "madeira":
            # Tábuas horizontais intercaladas com veio orgânico e cravos de ferro
            for y in range(TAM_TILE):
                if y in (10, 21, 31):
                    for x in range(TAM_TILE):
                        pa[x, y] = m_arg
                    continue
                if y < 10:
                    y0, y1, off_v = 0, 9, 0
                elif y < 21:
                    y0, y1, off_v = 11, 20, 14
                else:
                    y0, y1, off_v = 22, 30, 6
                ly = y - y0
                hb = y1 - y0
                for x in range(TAM_TILE):
                    lx = (x - off_v) % 32
                    if lx == 31:
                        pa[x, y] = m_arg
                    elif ly == 0 and lx < 30:
                        pa[x, y] = m_luz
                    elif lx == 0 and ly < hb:
                        pa[x, y] = m_luz
                    elif ly == hb or lx == 30:
                        pa[x, y] = m_somb
                    else:
                        veio = int(math.sin((x * 0.35 + y * 1.4 + semente) * 0.9) * 1.4 + rng.uniform(0, 1.8)) % 3
                        pa[x, y] = m_miolo[veio]
            # Cravos de ferro nas junções das tábuas
            m_reb = m(_escurecer_cor((128, 138, 156, 255), fator))
            for cx, cy in ((2, 3), (2, 7), (16, 14), (16, 18), (8, 25)):
                pa[cx, cy] = m_reb
                pa[cx + 1, cy] = m_somb

        elif tipo == "ferro":
            # Placas de ferro forjado com rebites chanfrados nos 4 cantos de cada placa
            for y in range(TAM_TILE):
                if y in (15, 31):
                    for x in range(TAM_TILE):
                        pa[x, y] = m_arg
                    continue
                y0, y1, off = (0, 14, 0) if y < 15 else (16, 30, 8)
                ly = y - y0
                hb = y1 - y0
                for x in range(TAM_TILE):
                    lx = (x - off) % 16
                    if lx == 15:
                        pa[x, y] = m_arg
                    elif (ly == 0 and lx < 14) or (lx == 0 and ly < hb):
                        pa[x, y] = m_luz
                    elif ly == hb or lx == 14:
                        pa[x, y] = m_somb
                    else:
                        idx_d = (x + (y & 1) + (1 if rng.random() < 0.38 else 0)) % 3
                        pa[x, y] = m_miolo[idx_d]
            m_reb_luz = m(_escurecer_cor((175, 190, 212, 255), fator))
            for rx, ry in ((2, 2), (12, 2), (2, 12), (12, 12), (18, 2), (28, 2), (18, 12), (28, 12),
                           (10, 18), (20, 18), (10, 28), (20, 28), (26, 18), (4, 28)):
                pa[rx, ry] = m_reb_luz
                pa[(rx + 1) % TAM_TILE, ry] = m_somb

        else:
            # Alvenaria clássica de Cantaria Gótica em 3 fileiras intercaladas
            vies_bloco = {}
            for y in range(TAM_TILE):
                if y in (10, 21, 31):
                    for x in range(TAM_TILE):
                        pa[x, y] = m_arg
                    continue
                if y < 10:
                    row_idx, y0, y1, off = 0, 0, 9, 0
                elif y < 21:
                    row_idx, y0, y1, off = 1, 11, 20, 8
                else:
                    row_idx, y0, y1, off = 2, 22, 30, 0
                ly = y - y0
                hb = y1 - y0
                for x in range(TAM_TILE):
                    lx = (x - off) % 16
                    if lx == 15:
                        pa[x, y] = m_arg
                    elif (ly == 0 and lx < 14) or (lx == 0 and ly < hb):
                        pa[x, y] = m_luz
                    elif ly == hb or lx == 14:
                        pa[x, y] = m_somb
                    else:
                        b_id = (row_idx, ((x - off) // 16) % 2)
                        if b_id not in vies_bloco:
                            vies_bloco[b_id] = rng.randint(0, 2)
                        base_v = vies_bloco[b_id]
                        padrao = ((x + y) & 1) + (1 if rng.random() < 0.42 else 0)
                        pa[x, y] = m_miolo[(base_v + padrao) % 3]

        # 1 a 2 trincas/fendas diagonais pretas (#05070B) cortando blocos
        n_trincas = 1 + (int(semente) % 2)
        for ti in range(n_trincas):
            row_sel = rng.choice(((1, 4, 0), (12, 15, 8), (23, 25, 0)))
            py = rng.randint(row_sel[0], row_sel[1])
            off_r = row_sel[2]
            px = (off_r + rng.randint(2, 9) + ti * 16) % TAM_TILE
            dir_x = rng.choice((-1, 1))
            comp = rng.randint(4, 7)
            for k in range(comp):
                if not (0 <= px < TAM_TILE and 0 <= py < TAM_TILE):
                    break
                if py in (10, 21, 31) or ((px - off_r) % 16) == 15:
                    break
                pa[px, py] = m_trinca
                # Micro-borda de luz adjacente dando profundidade ao corte da pedra
                adj_x = px - dir_x
                if 0 <= adj_x < TAM_TILE and ((adj_x - off_r) % 16) != 15 and k % 2 == 0:
                    pa[adj_x, py] = m_luz
                py += 1
                px += dir_x if (k % 2 == 0 or rng.random() < 0.72) else 0
    finally:
        pa.close()
    return _converter_surf(surf)


def gerar_textura_rocha_subsolo_32x32(semente=0, topo_exposto=True, com_musgo=True, escuro=False, estilo_musgo="padrao"):
    """
    Gera tile 32x32 px de Rocha Bruta do Subsolo via pygame.PixelArray:
    - Ruído celular toroidal + Simplex com manchas irregulares de ardósia escura (#151824)
    - Agrupamentos de 3 a 5 pixels de musgo (#14532D, #166534) concentrados no topo
    - Pontos de brilho úmido (#38BDF8 de 1px) simulando gotas refletindo Éter
    """
    surf = pygame.Surface((TAM_TILE, TAM_TILE), pygame.SRCALPHA)
    rng = random.Random(int(semente) * 3571 + (17 if topo_exposto else 91))
    ruido = RuidoSimplex(int(semente) + 41)
    fator = 0.54 if escuro else 1.0

    c_ardosia     = _escurecer_cor(COR_ARDOSIA_SUBSOLO, fator)         # #151824
    c_fenda       = _escurecer_cor((10, 12, 18, 255), fator)
    c_sombra_rocha = _escurecer_cor((15, 18, 27, 255), fator)
    c_nodulo      = _escurecer_cor((28, 33, 49, 255), fator)
    c_crista      = _escurecer_cor((41, 48, 68, 255), fator)
    c_oliva       = _escurecer_cor(COR_MUSGO_OLIVA, fator)             # #14532D
    c_musgo       = _escurecer_cor(COR_MUSGO_VIVO, fator)              # #166534
    c_eter        = _escurecer_cor((220, 48, 68, 255) if estilo_musgo == "sangue" else COR_BRILHO_ETER, 0.72 if escuro else 1.0)

    # 7 centros celulares em espaço toroidal 32x32 para junção perfeita entre tiles
    centros = [(rng.uniform(0, 32), rng.uniform(0, 32)) for _ in range(7)]
    campo = [[0.0] * TAM_TILE for _ in range(TAM_TILE)]
    fenda_mapa = [[False] * TAM_TILE for _ in range(TAM_TILE)]

    for y in range(TAM_TILE):
        for x in range(TAM_TILE):
            d1 = 9999.0
            d2 = 9999.0
            for fx, fy in centros:
                dx = min(abs(x - fx), 32.0 - abs(x - fx))
                dy = min(abs(y - fy), 32.0 - abs(y - fy))
                d = math.sqrt(dx * dx + dy * dy)
                if d < d1:
                    d2 = d1
                    d1 = d
                elif d < d2:
                    d2 = d
            borda = d2 - d1
            # Ruído periódico harmonizado + Simplex para veios minerais
            nx = math.cos(x * (math.tau / 32.0)) * 1.6
            ny = math.sin(y * (math.tau / 32.0)) * 1.6
            n_val = ruido.noise2(nx + x * 0.08, ny + y * 0.08)
            campo[y][x] = (n_val * 0.55) + max(0.0, (5.0 - d1) * 0.18)
            fenda_mapa[y][x] = (borda < 1.25)

    pa = pygame.PixelArray(surf)
    try:
        m = surf.map_rgb
        m_ard = m(c_ardosia)
        m_fenda = m(c_fenda)
        m_somb = m(c_sombra_rocha)
        m_nod = m(c_nodulo)
        m_cris = m(c_crista)
        m_oliva = m(c_oliva)
        m_musgo = m(c_musgo)
        m_eter = m(c_eter)

        for y in range(TAM_TILE):
            yn = (y + 1) % TAM_TILE
            for x in range(TAM_TILE):
                if fenda_mapa[y][x]:
                    pa[x, y] = m_fenda
                    continue
                xn = (x + 1) % TAM_TILE
                inclinacao = campo[y][x] - campo[yn][xn]
                val = campo[y][x]
                if inclinacao > 0.24:
                    pa[x, y] = m_cris if val > 0.2 else m_nod
                elif inclinacao < -0.22:
                    pa[x, y] = m_somb
                elif val > 0.16 and ((x + y) & 1 == 0 or rng.random() < 0.5):
                    pa[x, y] = m_nod
                elif val < -0.18:
                    pa[x, y] = m_somb
                else:
                    pa[x, y] = m_ard

        # Detalhes de musgo: agrupamentos de 3 a 5 pixels (#14532D / #166534) concentrados no topo
        if com_musgo:
            n_grupos = rng.randint(4, 6) if topo_exposto else rng.randint(1, 2)
            for _ in range(n_grupos):
                mx = rng.randint(2, TAM_TILE - 3)
                my = rng.randint(1, 9) if topo_exposto else rng.randint(4, TAM_TILE - 4)
                tam_g = rng.randint(3, 5)
                offsets = [(0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
                for idx_p in range(tam_g):
                    ox, oy = offsets[idx_p]
                    tx = max(0, min(TAM_TILE - 1, mx + ox))
                    ty = max(0, min(TAM_TILE - 1, my + oy))
                    pa[tx, ty] = m_musgo if oy == 0 else m_oliva

        # Pontos de brilho úmido (#38BDF8 de 1px) simulando gotas refletindo Éter
        n_gotas = rng.randint(2, 4) if topo_exposto else rng.randint(1, 2)
        for _ in range(n_gotas):
            gx = rng.randint(2, TAM_TILE - 3)
            gy = rng.randint(2, 13 if topo_exposto else TAM_TILE - 3)
            pa[gx, gy] = m_eter
    finally:
        pa.close()
    return _converter_surf(surf)


def _gerar_tira_laje_topo_32(estilo="pedra", semente=0):
    """Pré-renderiza a laje de pedra espessa (32x9 px) com destaque claro e sombra sob a borda."""
    pal = _ESTILOS_BLOCO.get(estilo, _ESTILOS_BLOCO["pedra"])
    surf = pygame.Surface((TAM_TILE, 9), pygame.SRCALPHA)
    rng = random.Random(int(semente) * 193 + (hash(estilo) & 0xFFFF))
    pa = pygame.PixelArray(surf)
    try:
        m = surf.map_rgb
        m_cont = m(COR_TRINCA_CANTARIA)
        m_claro = m(pal["laje_clara"])
        m_topo = m(pal["laje_topo"])
        m_meio = m(pal["laje_meio"])
        m_somb = m(pal["sombra"])
        m_drop1 = m((5, 7, 11, 215))
        m_drop2 = m((5, 7, 11, 105))
        m_transp = m((0, 0, 0, 0))
        m_oliva = m(COR_MUSGO_OLIVA)
        m_musgo = m(COR_MUSGO_VIVO)

        entalhe_x = {rng.randint(4, 11), rng.randint(19, 27)}
        for x in range(TAM_TILE):
            junta = (x in (15, 31))
            entalhe = (x in entalhe_x)
            pa[x, 0] = m_transp if entalhe else m_cont
            pa[x, 1] = m_cont if entalhe else (m_somb if junta else m_claro)
            pa[x, 2] = m_claro if (not junta and ((x + semente) % 3 != 0)) else (m_somb if junta else m_topo)
            for y in (3, 4):
                if junta:
                    pa[x, y] = m_cont
                elif (x - 1) in (15, 31):
                    pa[x, y] = m_claro
                else:
                    pa[x, y] = m_topo if ((x + y) & 1 == 0 and rng.random() < 0.45) else m_meio
            pa[x, 5] = m_cont if junta else m_meio
            pa[x, 6] = m_cont if junta else m_somb
            pa[x, 7] = m_drop1
            pa[x, 8] = m_drop2

        if pal.get("musgo"):
            for _ in range(2):
                mx = rng.randint(2, TAM_TILE - 4)
                for ox, oy in ((0, 1), (1, 1), (0, 2), (1, 2), (2, 2))[:rng.randint(3, 5)]:
                    tx = min(TAM_TILE - 1, mx + ox)
                    pa[tx, oy] = m_musgo if oy == 1 else m_oliva
                if rng.random() < 0.65:
                    pa[mx, 7] = m_oliva

        if pal.get("glint") and rng.random() < 0.8:
            gx = rng.randint(3, TAM_TILE - 4)
            pa[gx, 2] = m(pal["glint"])
    finally:
        pa.close()
    return _converter_surf(surf)


def _aplicar_chanfros_cantos_pixelarray(surf, topo_exp, baixo_exp, esq_exp, dir_exp, cor_luz):
    """Aplica contornos escuros externos chanfrados (45 graus) nas quinas expostas de qualquer bloco."""
    w, h = surf.get_size()
    if w < 8 or h < 8:
        return
    pa = pygame.PixelArray(surf)
    try:
        m = surf.map_rgb
        m_tr = m((0, 0, 0, 0))
        m_ct = m(COR_TRINCA_CANTARIA)
        m_lz = m(cor_luz)
        if topo_exp and esq_exp:
            pa[0, 0] = m_tr; pa[1, 0] = m_tr; pa[0, 1] = m_tr
            pa[2, 0] = m_ct; pa[1, 1] = m_ct; pa[0, 2] = m_ct
            pa[2, 1] = m_lz; pa[1, 2] = m_lz
        if topo_exp and dir_exp:
            pa[w - 1, 0] = m_tr; pa[w - 2, 0] = m_tr; pa[w - 1, 1] = m_tr
            pa[w - 3, 0] = m_ct; pa[w - 2, 1] = m_ct; pa[w - 1, 2] = m_ct
        if baixo_exp and esq_exp:
            pa[0, h - 1] = m_tr; pa[1, h - 1] = m_tr; pa[0, h - 2] = m_tr
            pa[2, h - 1] = m_ct; pa[1, h - 2] = m_ct; pa[0, h - 3] = m_ct
        if baixo_exp and dir_exp:
            pa[w - 1, h - 1] = m_tr; pa[w - 2, h - 1] = m_tr; pa[w - 1, h - 2] = m_tr
            pa[w - 3, h - 1] = m_ct; pa[w - 2, h - 2] = m_ct; pa[w - 1, h - 3] = m_ct
    finally:
        pa.close()


def _obter_tiras_borda(estilo):
    if estilo in _CACHE_BORDAS:
        return _CACHE_BORDAS[estilo]
    pal = _ESTILOS_BLOCO.get(estilo, _ESTILOS_BLOCO["pedra"])

    # Borda esquerda (2x32): contorno #05070B + chanfro de luz interno
    s_esq = pygame.Surface((2, TAM_TILE), pygame.SRCALPHA)
    pa = pygame.PixelArray(s_esq)
    try:
        m = s_esq.map_rgb
        m_ct, m_lz, m_sb = m(COR_TRINCA_CANTARIA), m(pal["luz"]), m(pal["sombra"])
        for y in range(TAM_TILE):
            pa[0, y] = m_ct
            pa[1, y] = m_sb if y in (10, 21, 31) else m_lz
    finally:
        pa.close()

    # Borda direita (2x32): chanfro de sombra interno + contorno #05070B
    s_dir = pygame.Surface((2, TAM_TILE), pygame.SRCALPHA)
    pa = pygame.PixelArray(s_dir)
    try:
        m = s_dir.map_rgb
        m_ct, m_sb, m_ar = m(COR_TRINCA_CANTARIA), m(pal["sombra"]), m(pal["argamassa"])
        for y in range(TAM_TILE):
            pa[0, y] = m_ar if y in (10, 21, 31) else m_sb
            pa[1, y] = m_ct
    finally:
        pa.close()

    # Borda inferior (32x3): sombra chanfrada + contorno #05070B
    s_bx = pygame.Surface((TAM_TILE, 3), pygame.SRCALPHA)
    pa = pygame.PixelArray(s_bx)
    try:
        m = s_bx.map_rgb
        m_ct, m_sb, m_ar = m(COR_TRINCA_CANTARIA), m(pal["sombra"]), m(pal["argamassa"])
        for x in range(TAM_TILE):
            pa[x, 0] = m_sb
            pa[x, 1] = m_ar
            pa[x, 2] = m_ct
    finally:
        pa.close()

    res = (_converter_surf(s_esq), _converter_surf(s_dir), _converter_surf(s_bx))
    _CACHE_BORDAS[estilo] = res
    return res


def _garantir_atlas_32x32():
    """Pré-renderiza os tiles base 32x32 (cantaria, rocha e lajes de topo) em Surfaces otimizadas."""
    if _ATLAS_32:
        return
    for estilo in _ESTILOS_BLOCO:
        _ATLAS_32[(estilo, "norm")] = [gerar_textura_cantaria_32x32(v, estilo=estilo, escuro=False) for v in range(4)]
        _ATLAS_32[(estilo, "escuro")] = [gerar_textura_cantaria_32x32(v, estilo=estilo, escuro=True) for v in range(4)]
        _ATLAS_32[(estilo, "laje")] = [_gerar_tira_laje_topo_32(estilo=estilo, semente=v) for v in range(4)]

    _ATLAS_32[("rocha", "topo")] = [
        gerar_textura_rocha_subsolo_32x32(v, topo_exposto=True, com_musgo=True, escuro=False) for v in range(4)
    ]
    _ATLAS_32[("rocha", "miolo")] = [
        gerar_textura_rocha_subsolo_32x32(v + 10, topo_exposto=False, com_musgo=False, escuro=False) for v in range(4)
    ]
    _ATLAS_32[("rocha", "fundo")] = [
        gerar_textura_rocha_subsolo_32x32(v + 20, topo_exposto=False, com_musgo=False, escuro=True) for v in range(4)
    ]
    _ATLAS_32[("rocha_sangue", "topo")] = [
        gerar_textura_rocha_subsolo_32x32(v, topo_exposto=True, com_musgo=True, escuro=False, estilo_musgo="sangue") for v in range(4)
    ]

    for estilo in _ESTILOS_BLOCO:
        _obter_tiras_borda(estilo)


def gerar_tile_autotile_32x32(base_tipo, mask4, variante=0, estilo="pedra", topo_laje=True):
    """Retorna tile 32x32 pré-renderizado aplicando máscara autotile 4-bit (topo, baixo, esq, dir)."""
    _garantir_atlas_32x32()
    chave = (base_tipo, int(mask4) & 15, int(variante) & 3, estilo, bool(topo_laje))
    if chave in _CACHE_TILES_AUTOTILE:
        return _CACHE_TILES_AUTOTILE[chave]

    topo_exp = bool(mask4 & 8)
    baixo_exp = bool(mask4 & 4)
    esq_exp = bool(mask4 & 2)
    dir_exp = bool(mask4 & 1)
    v = int(variante) & 3

    if base_tipo == "rocha":
        chave_r = ("rocha_sangue", "topo") if (estilo == "sangue" and topo_exp) else ("rocha", "topo" if topo_exp else "miolo")
        base_img = _ATLAS_32[chave_r][v]
    else:
        base_img = _ATLAS_32[(estilo, "norm")][v]

    surf = base_img.copy()
    pal = _ESTILOS_BLOCO.get(estilo, _ESTILOS_BLOCO["pedra"])
    b_esq, b_dir, b_bx = _obter_tiras_borda(estilo)
    if esq_exp:
        surf.blit(b_esq, (0, 0))
    if dir_exp:
        surf.blit(b_dir, (TAM_TILE - 2, 0))
    if baixo_exp:
        surf.blit(b_bx, (0, TAM_TILE - 3))
    if topo_exp and topo_laje:
        surf.blit(_ATLAS_32[(estilo, "laje")][v], (0, 0))
    if mask4:
        _aplicar_chanfros_cantos_pixelarray(surf, topo_exp, baixo_exp, esq_exp, dir_exp, pal["laje_clara"] if topo_exp else pal["luz"])

    surf = _converter_surf(surf)
    _CACHE_TILES_AUTOTILE[chave] = surf
    return surf


def montar_superficie_bloco_autotile(w, h, base_tipo="cantaria", estilo="pedra",
                                     topo_exp=True, baixo_exp=True, esq_exp=True, dir_exp=True, semente=0):
    """Monta Surface otimizada (w x h) com tiling de tiles 32x32, laje espessa no topo e quinas chanfradas."""
    _garantir_atlas_32x32()
    w, h = max(4, int(w)), max(4, int(h))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    tiles = _ATLAS_32[(estilo, "norm")] if base_tipo == "cantaria" else _ATLAS_32[("rocha", "topo" if topo_exp else "miolo")]

    cols = (w + TAM_TILE - 1) // TAM_TILE
    lins = (h + TAM_TILE - 1) // TAM_TILE
    for gy in range(lins):
        for gx in range(cols):
            v = (gx + gy * 3 + int(semente)) & 3
            surf.blit(tiles[v], (gx * TAM_TILE, gy * TAM_TILE))

    b_esq, b_dir, b_bx = _obter_tiras_borda(estilo)
    if esq_exp:
        for gy in range(lins):
            surf.blit(b_esq, (0, gy * TAM_TILE))
    if dir_exp:
        for gy in range(lins):
            surf.blit(b_dir, (w - 2, gy * TAM_TILE))
    if baixo_exp:
        for gx in range(cols):
            surf.blit(b_bx, (gx * TAM_TILE, h - 3))
    if topo_exp:
        lajes = _ATLAS_32[(estilo, "laje")]
        for gx in range(cols):
            surf.blit(lajes[(gx + int(semente)) & 3], (gx * TAM_TILE, 0))

    pal = _ESTILOS_BLOCO.get(estilo, _ESTILOS_BLOCO["pedra"])
    _aplicar_chanfros_cantos_pixelarray(surf, topo_exp, baixo_exp, esq_exp, dir_exp, pal["laje_clara"] if topo_exp else pal["luz"])
    return _converter_surf(surf)


def _obter_pinaculo_gotico(estilo="pedra"):
    if estilo in _CACHE_PINACULOS:
        return _CACHE_PINACULOS[estilo]
    _garantir_atlas_32x32()
    pw, ph = 96, 192
    surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    tiles = _ATLAS_32[(estilo, "escuro")]
    for gy in range(ph // TAM_TILE):
        for gx in range(pw // TAM_TILE):
            surf.blit(tiles[(gx + gy) & 3], (gx * TAM_TILE, gy * TAM_TILE))

    pa = pygame.PixelArray(surf)
    try:
        m = surf.map_rgb
        m_tr = m((0, 0, 0, 0))
        m_ct = m(COR_TRINCA_CANTARIA)
        m_lz = m(_escurecer_cor(COR_LUZ_CANTARIA, 0.78))
        m_sb = m(_escurecer_cor(COR_SOMBRA_CANTARIA, 0.75))
        cx = pw // 2
        for y in range(ph):
            meia_larg = max(1, int((y / float(ph - 1)) * (cx - 2)))
            x_esq = cx - meia_larg
            x_dir = cx + meia_larg
            for x in range(pw):
                if x < x_esq or x > x_dir:
                    pa[x, y] = m_tr
                elif x == x_esq or x == x_dir:
                    pa[x, y] = m_ct
                elif x == x_esq + 1:
                    pa[x, y] = m_lz
                elif x == x_dir - 1:
                    pa[x, y] = m_sb
                elif 72 <= y <= 148 and abs(x - cx) <= 4:
                    # Fenda estreita de janela ogival gótica
                    pa[x, y] = m_ct if abs(x - cx) <= 2 else m_sb
    finally:
        pa.close()
    res = _converter_surf(surf)
    _CACHE_PINACULOS[estilo] = res
    return res


def _obter_chao_strip(idx):
    if idx in _CACHE_CHAO_STRIPS:
        return _CACHE_CHAO_STRIPS[idx]
    _garantir_atlas_32x32()
    mapa = DADOS_MAPAS.get(idx, DADOS_MAPAS[0])
    estilo_p = mapa["visual"].get("plataforma", "pedra")
    estilo_c = mapa["visual"].get("chao", "cripta")
    estilo_r = "sangue" if estilo_c == "sangue" else "padrao"
    sw, sh = 256, 64
    strip = pygame.Surface((sw, sh), pygame.SRCALPHA)

    tiles_m = _ATLAS_32[("rocha", "miolo")]
    for gy in range(2):
        for gx in range(sw // TAM_TILE):
            if gy == 0:
                tile_t = gerar_tile_autotile_32x32("rocha", 8, variante=(gx + idx) & 3, estilo=estilo_p, topo_laje=True)
                strip.blit(tile_t, (gx * TAM_TILE, 0))
                if estilo_r == "sangue":
                    strip.blit(_ATLAS_32[("rocha_sangue", "topo")][(gx + idx) & 3], (gx * TAM_TILE, 10), area=pygame.Rect(0, 10, TAM_TILE, 22))
            else:
                strip.blit(tiles_m[(gx + gy + idx) & 3], (gx * TAM_TILE, gy * TAM_TILE))

    strip = _converter_surf(strip)
    _CACHE_CHAO_STRIPS[idx] = strip
    return strip


def _arquivo(nome):
    img = _arquivos.get(nome)
    if img is None:
        img = ASSETS_DUNGEON.carregar_imagem(nome)
        if img is None:
            caminho = os.path.join(_pasta_final(), nome)
            try:
                img = pygame.image.load(caminho).convert_alpha()
            except (pygame.error, FileNotFoundError):
                img = None
        _arquivos[nome] = img
    return img


def peca(nome, escala=1.0, espelhar=False):
    chave = (nome, round(escala, 3), espelhar)
    if chave in _pecas_escala:
        return _pecas_escala[chave]
    if nome not in _pecas:
        arq, (x, y, w, h) = RECORTES[nome]
        src = _arquivo(arq)
        _pecas[nome] = src.subsurface(pygame.Rect(x, y, w, h)).copy() if src is not None else None
        if _pecas[nome] is not None:
            for area in LIMPAR.get(nome, []):
                _pecas[nome].fill((0, 0, 0, 0), pygame.Rect(*area))
    base = _pecas[nome]
    if base is not None and escala != 1.0:
        base = pygame.transform.scale(base, (max(1, int(base.get_width() * escala)), max(1, int(base.get_height() * escala))))
    if base is not None and espelhar:
        base = pygame.transform.flip(base, True, False)
    _pecas_escala[chave] = base
    return base


def _escalar_altura(img):
    f = ALTURA_TELA / float(img.get_height())
    return pygame.transform.scale(img, (max(1, int(img.get_width() * f)), ALTURA_TELA))


def _juntar_horizontal(imgs):
    largura = sum(i.get_width() for i in imgs)
    saida = pygame.Surface((largura, imgs[0].get_height()), pygame.SRCALPHA)
    x = 0
    for i in imgs:
        saida.blit(i, (x, 0))
        x += i.get_width()
    return saida


def _gerar_fundo_torres_paralaxe():
    """Fallback em pixel art para `Background_2.png` (silhuetas góticas das Torres de Vigia em paralaxe)."""
    w, h = LARGURA_TELA * 2, ALTURA_TELA
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cor_t = (18, 22, 38, 230)
    cor_b = (38, 46, 74, 155)
    cor_jan = (217, 119, 6, 130)
    rng = random.Random(2024)
    px = 20
    while px < w:
        tw = rng.randint(58, 108)
        th = rng.randint(155, 295)
        topo = h - th
        pygame.draw.rect(surf, cor_t, (px, topo, tw, th))
        # Telhado pontiagudo ou ameias alternadas
        if (px // 50) % 2 == 0:
            pygame.draw.polygon(surf, cor_t, [(px - 4, topo), (px + tw // 2, topo - 48), (px + tw + 4, topo)])
        else:
            for ax in range(px, px + tw - 8, 16):
                pygame.draw.rect(surf, cor_t, (ax, topo - 12, 9, 12))
        pygame.draw.line(surf, cor_b, (px, topo), (px, h), 1)
        pygame.draw.line(surf, cor_b, (px, topo), (px + tw, topo), 1)
        # Janelas ogivais tênues nas torres
        if tw >= 68:
            jx = px + tw // 2 - 5
            for jy in range(topo + 28, h - 85, 52):
                pygame.draw.rect(surf, cor_jan, (jx, jy, 10, 20), border_top_left_radius=5, border_top_right_radius=5)
        px += tw + rng.randint(48, 104)
    return surf


def _montar_fundo(idx):
    visual = DADOS_MAPAS[idx]["visual"]
    arq_fundo = visual.get("fundo_arquivo")
    ceu = _arquivo("Background_0.png") or _arquivo("Background_1.png")
    if arq_fundo == "Background_2.png":
        mid = _arquivo("Background_2.png")
        if mid is not None:
            m = _escalar_altura(mid)
            mid_layer = _juntar_horizontal([m, pygame.transform.flip(m, True, False)])
        else:
            mid_layer = _gerar_fundo_torres_paralaxe()
    elif arq_fundo == "Background_1.png":
        img_bg1 = _arquivo("Background_1.png")
        if img_bg1 is not None:
            m = _escalar_altura(img_bg1)
            mid_layer = _juntar_horizontal([m, pygame.transform.flip(m, True, False)])
        else:
            mid_layer = None
    else:
        mid_img = _arquivo("Background_1.png") if visual.get("mid") else None
        if mid_img is not None:
            m = _escalar_altura(mid_img)
            mid_layer = _juntar_horizontal([m, pygame.transform.flip(m, True, False)])
        else:
            mid_layer = None

    gr1, gr2 = _arquivo("Grass_background_1.png"), _arquivo("Grass_background_2.png")

    fundo = {"ceu": None, "mid": mid_layer, "grama": None}
    if ceu is not None:
        c = _escalar_altura(ceu)
        fundo["ceu"] = _juntar_horizontal([c, pygame.transform.flip(c, True, False)])
    tipo = visual.get("grama")
    if tipo == 2 and gr1 is not None and gr2 is not None:
        fundo["grama"] = _juntar_horizontal([_escalar_altura(gr2), _escalar_altura(gr1)])
    elif tipo and gr1 is not None:
        a = _escalar_altura(gr1)
        fundo["grama"] = _juntar_horizontal([a, pygame.transform.flip(a, True, False)])
    return fundo


def _desenhar_suportes_arquiteturais(surf, mapa, idx):
    """Renderiza colunas verticais de cantaria, correntes verticais, pedra lascada e escadarias."""
    estilo_p = mapa["visual"].get("plataforma", "pedra")
    estilo_sup = "pedra" if estilo_p == "madeira" else estilo_p
    for sup in mapa.get("suportes", []):
        tipo = sup.get("tipo")
        if tipo in ("coluna", "escadaria", "pedra_lascada"):
            r = sup["rect"]
            if r.width < 6 or r.height < 6:
                continue
            bloco = montar_superficie_bloco_autotile(
                r.width, r.height, base_tipo="cantaria", estilo=estilo_sup,
                topo_exp=False, baixo_exp=(tipo == "pedra_lascada"), esq_exp=True, dir_exp=True, semente=r.x + r.y + idx
            )
            surf.blit(bloco, r.topleft)
            if tipo == "coluna" and r.height >= 20:
                capitel = montar_superficie_bloco_autotile(
                    r.width + 6, 8, base_tipo="cantaria", estilo=estilo_sup,
                    topo_exp=False, baixo_exp=True, esq_exp=True, dir_exp=True, semente=r.x + 3
                )
                base_p = montar_superficie_bloco_autotile(
                    r.width + 6, 8, base_tipo="cantaria", estilo=estilo_sup,
                    topo_exp=True, baixo_exp=False, esq_exp=True, dir_exp=True, semente=r.y + 5
                )
                surf.blit(capitel, (r.x - 3, r.y))
                surf.blit(base_p, (r.x - 3, r.bottom - 8))
        elif tipo == "corrente":
            cx = int(sup["x"])
            y_topo = int(sup.get("y_topo", 0))
            y_fim = int(sup.get("y_fim", 0))
            # Ancoragem em chapa de ferro + elos verticais até a plataforma suspensa
            pygame.draw.rect(surf, COR_TRINCA_CANTARIA[:3], (cx - 6, y_topo, 12, 8))
            pygame.draw.rect(surf, (100, 116, 139), (cx - 4, y_topo + 1, 8, 6), 1)
            for cy_l in range(y_topo + 6, max(y_topo + 6, y_fim), 8):
                alt_l = min(7, y_fim - cy_l)
                if alt_l >= 2:
                    pygame.draw.rect(surf, COR_TRINCA_CANTARIA[:3], (cx - 3, cy_l, 6, alt_l), 2)
                    pygame.draw.line(surf, (148, 163, 184), (cx - 1, cy_l + 1), (cx - 1, cy_l + alt_l - 1), 1)
            # Argola de fixação na laje da plataforma
            pygame.draw.circle(surf, (100, 116, 139), (cx, y_fim), 4, 2)
        elif tipo == "viga":
            x1, y1 = sup["p1"]
            x2, y2 = sup["p2"]
            cor_viga = (118, 76, 42) if estilo_p == "madeira" else (62, 72, 92)
            cor_luz = (168, 114, 62) if estilo_p == "madeira" else COR_LUZ_CANTARIA[:3]
            pygame.draw.line(surf, COR_TRINCA_CANTARIA[:3], (x1, y1), (x2, y2), 7)
            pygame.draw.line(surf, cor_viga, (x1, y1), (x2, y2), 4)
            pygame.draw.line(surf, cor_luz, (x1, y1 - 1), (x2, y2 - 1), 1)
            for px_a, py_a in ((x1, y1), (x2, y2)):
                pygame.draw.rect(surf, COR_TRINCA_CANTARIA[:3], (px_a - 4, py_a - 4, 8, 8))
                pygame.draw.rect(surf, (100, 116, 139), (px_a - 3, py_a - 3, 6, 6), 1)


def _desenhar_pilar_gargula(surf, gx, gy_chao, virar_esq=False):
    """Pilar monumental de cantaria coroado com estátua de gárgula esculpida (Sala 7 Boss Room)."""
    pw, ph = 52, 224
    bloco = montar_superficie_bloco_autotile(
        pw, ph, base_tipo="cantaria", estilo="catedral",
        topo_exp=True, baixo_exp=True, esq_exp=True, dir_exp=True, semente=gx + 77
    )
    bx = gx - pw // 2
    by = gy_chao - ph
    surf.blit(bloco, (bx, by))
    # Pedestal & Estátua de Gárgula em pixel art esculpida sobre o capitel
    s_g = pygame.Surface((76, 74), pygame.SRCALPHA)
    cor_p = (76, 84, 102, 255)
    cor_l = (148, 163, 184, 255)
    cor_s = (24, 29, 42, 255)
    # Asas dobradas + corpo agachado + chifres + olhos rúnicos
    pygame.draw.polygon(s_g, cor_s, [(14, 58), (2, 18), (28, 30)])
    pygame.draw.polygon(s_g, cor_p, [(16, 56), (6, 22), (28, 34)])
    pygame.draw.polygon(s_g, cor_s, [(62, 58), (74, 18), (48, 30)])
    pygame.draw.polygon(s_g, cor_p, [(60, 56), (70, 22), (48, 34)])
    pygame.draw.rect(s_g, cor_p, (24, 28, 28, 36), border_radius=5)
    pygame.draw.rect(s_g, cor_s, (24, 28, 28, 36), 2, border_radius=5)
    pygame.draw.circle(s_g, cor_p, (38, 22), 11)
    pygame.draw.polygon(s_g, cor_l, [(29, 14), (22, 4), (34, 14)])
    pygame.draw.polygon(s_g, cor_l, [(47, 14), (54, 4), (42, 14)])
    pygame.draw.rect(s_g, (56, 189, 248, 230), (33, 21, 3, 2))
    pygame.draw.rect(s_g, (56, 189, 248, 230), (41, 21, 3, 2))
    pygame.draw.rect(s_g, cor_l, (16, 62, 44, 10))
    if virar_esq:
        s_g = pygame.transform.flip(s_g, True, False)
    surf.blit(s_g, (gx - 38, by - 72))


def _construir_arquitetura_3_camadas(idx):
    """Pré-renderiza a arquitetura detalhada dos 4 biomas (muralhas, correntes, grades, arcos e gárgulas)."""
    if idx in _camadas_cache:
        return _camadas_cache[idx]

    _garantir_atlas_32x32()
    mapa = DADOS_MAPAS[idx]
    w_m, h_m = mapa["largura"], mapa["altura"]
    chao_y = mapa["chao"].top
    tipologia = mapa.get("tipologia", "B")
    estilo_p = mapa["visual"].get("plataforma", "pedra")
    props = mapa.get("props", {})
    surf = pygame.Surface((w_m, h_m), pygame.SRCALPHA)

    tiles_fundo_bsp = _ATLAS_32[("pedra", "escuro")]
    tiles_fundo_rocha = _ATLAS_32[("rocha", "fundo")]

    if tipologia.startswith("BIOMA1_"):
        # Muralhas baixas em cantaria no fundo das ameias + pináculos ocasionais
        pinaculo = _obter_pinaculo_gotico("pedra")
        muro_h = 96
        muro_y = chao_y - muro_h
        muralha_bg = pygame.Surface((w_m, muro_h), pygame.SRCALPHA)
        for gy in range((muro_h + TAM_TILE - 1) // TAM_TILE):
            for gx in range((w_m + TAM_TILE - 1) // TAM_TILE):
                muralha_bg.blit(tiles_fundo_bsp[(gx + gy + idx) & 3], (gx * TAM_TILE, gy * TAM_TILE))
        muralha_bg.set_alpha(195)
        surf.blit(muralha_bg, (0, muro_y))
        for xm in range(0, w_m, 48):
            if (xm // 48) % 2 == 0:
                pygame.draw.rect(surf, (24, 30, 44, 210), (xm, muro_y - 16, 26, 16))
                pygame.draw.line(surf, COR_LUZ_CANTARIA[:3], (xm, muro_y - 16), (xm + 26, muro_y - 16), 2)
        for tx in (310, 1480):
            if tx + 96 < w_m:
                surf.blit(pinaculo, (tx, max(60, chao_y - 192)))

    elif tipologia.startswith("BIOMA2_"):
        # Torres de vigia: fundações sob pátios + silhuetas de torres + vigas superiores para correntes
        y_base_patio = mapa["paredes"][0].top if mapa["paredes"] else chao_y - 240
        pinaculo = _obter_pinaculo_gotico("pedra")
        for tx, ty in props.get("torres_fundo", []):
            if tx + 96 < w_m:
                surf.blit(pinaculo, (tx, max(40, ty - 192)))
        # Fosso rochoso de fundo no vão inferior
        for gy in range(((chao_y - y_base_patio) + TAM_TILE - 1) // TAM_TILE):
            py_a = y_base_patio + gy * TAM_TILE
            if py_a >= chao_y:
                continue
            for gx in range((w_m + TAM_TILE - 1) // TAM_TILE):
                if (gx * TAM_TILE) > 390 and (gx * TAM_TILE) < w_m - 420:
                    surf.blit(tiles_fundo_rocha[(gx + gy * 2) & 3], (gx * TAM_TILE, py_a))

    elif tipologia.startswith("BIOMA3_"):
        # Catacumbas e Cripta dos Ossos: interior fechado em pedra e rocha úmida sem céu exterior
        for gy_f in range((h_m + TAM_TILE - 1) // TAM_TILE):
            py_f = gy_f * TAM_TILE
            tile_set = tiles_fundo_bsp if py_f < 760 else tiles_fundo_rocha
            for gx_f in range((w_m + TAM_TILE - 1) // TAM_TILE):
                surf.blit(tile_set[(gx_f + gy_f * 2 + idx) & 3], (gx_f * TAM_TILE, py_f))
        # Grades de ferro recuadas no fundo
        for gx_r, gy_r, gw_r, gh_r in props.get("grades_fundo", []):
            pygame.draw.rect(surf, (4, 6, 12, 235), (gx_r, gy_r, gw_r, gh_r), border_top_left_radius=gw_r // 2, border_top_right_radius=gw_r // 2)
            for bx in range(gx_r + 12, gx_r + gw_r - 8, 16):
                pygame.draw.line(surf, (71, 85, 105), (bx, gy_r + 8), (bx, gy_r + gh_r), 3)
            for by in range(gy_r + 36, gy_r + gh_r - 12, 34):
                pygame.draw.line(surf, (51, 65, 85), (gx_r + 6, by), (gx_r + gw_r - 6, by), 2)
            pygame.draw.rect(surf, COR_LUZ_CANTARIA[:3], (gx_r, gy_r, gw_r, gh_r), 2, border_top_left_radius=gw_r // 2, border_top_right_radius=gw_r // 2)
        # Arcos de pedra e colunas estruturais das catacumbas
        for ax, ay, aw in props.get("arcos_cripta", []):
            arco = pygame.Surface((aw, 130), pygame.SRCALPHA)
            pygame.draw.arc(arco, COR_LUZ_CANTARIA[:3], (0, 0, aw, 150), 0, math.pi, 4)
            pygame.draw.arc(arco, COR_TRINCA_CANTARIA[:3], (5, 5, aw - 10, 140), 0, math.pi, 3)
            surf.blit(arco, (ax, ay))
            col_a = montar_superficie_bloco_autotile(22, max(160, chao_y - ay - 60), "cantaria", "cripta", False, False, True, True, semente=ax)
            surf.blit(col_a, (ax - 11, ay + 48))

    elif tipologia == "BIOMA4_ARENA":
        # Santuário do Guardião (960x540): catedral escura, vitrais tênues, grades, arcos e pilares com gárgulas
        for gy_f in range((h_m + TAM_TILE - 1) // TAM_TILE):
            for gx_f in range((w_m + TAM_TILE - 1) // TAM_TILE):
                surf.blit(tiles_fundo_bsp[(gx_f + gy_f * 2 + 7) & 3], (gx_f * TAM_TILE, gy_f * TAM_TILE))
        for gx_r, gy_r, gw_r, gh_r in props.get("grades_fundo", []):
            pygame.draw.rect(surf, (6, 8, 16, 235), (gx_r, gy_r, gw_r, gh_r), border_top_left_radius=gw_r // 2, border_top_right_radius=gw_r // 2)
            for bx in range(gx_r + 12, gx_r + gw_r - 8, 15):
                pygame.draw.line(surf, (94, 108, 134), (bx, gy_r + 8), (bx, gy_r + gh_r), 3)
            pygame.draw.rect(surf, (180, 83, 9), (gx_r, gy_r, gw_r, gh_r), 2, border_top_left_radius=gw_r // 2, border_top_right_radius=gw_r // 2)
        for ax, ay, aw in props.get("arcos_cripta", []):
            arco = pygame.Surface((aw, 120), pygame.SRCALPHA)
            pygame.draw.arc(arco, (180, 120, 40), (0, 0, aw, 140), 0, math.pi, 3)
            pygame.draw.arc(arco, COR_LUZ_CANTARIA[:3], (4, 4, aw - 8, 132), 0, math.pi, 2)
            surf.blit(arco, (ax, ay))
        for px_g, py_g, virar_e in props.get("pilares_gargulas", []):
            _desenhar_pilar_gargula(surf, px_g, py_g, virar_esq=virar_e)

    # Renderiza suportes estruturais (colunas, correntes verticais, pedra lascada)
    _desenhar_suportes_arquiteturais(surf, mapa, idx)

    surf = _converter_surf(surf)
    _camadas_cache[idx] = surf
    return surf


def iniciar():
    global _pronto, COR_TERRA
    if _pronto:
        return
    _garantir_atlas_32x32()
    for nome in RECORTES:
        peca(nome)
    grama = peca("grama")
    if grama is not None:
        COR_TERRA = tuple(grama.get_at((grama.get_width() // 2, grama.get_height() - 1))[:3])

    for idx in DADOS_MAPAS:
        _fundos[idx] = _montar_fundo(idx)
        r, g, b, a = DADOS_MAPAS[idx]["visual"]["tint"]
        sup = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        sup.fill((r, g, b, a))
        _tints[idx] = sup

        _obter_chao_strip(idx)
        mapa = DADOS_MAPAS[idx]
        est_plat = mapa["visual"].get("plataforma", "pedra")
        for plat in mapa.get("plataformas", []):
            ch_p = (est_plat, plat.width, plat.height)
            if ch_p not in _CACHE_PLATAFORMAS:
                _CACHE_PLATAFORMAS[ch_p] = _renderizar_textura_plataforma(est_plat, plat.width, plat.height)
        for par in mapa.get("paredes", []):
            _obter_parede_surface(idx, par)
        _construir_arquitetura_3_camadas(idx)
    _pronto = True


def _blit_loop(surface, img, deslocamento_x, deslocamento_y=0):
    w, h = img.get_width(), img.get_height()
    x = -(int(deslocamento_x) % w)
    y = max(surface.get_height() - h, min(0, -int(deslocamento_y)))
    while x < surface.get_width():
        surface.blit(img, (x, y))
        x += w


def desenhar_fundo_sala(surface, sala_idx, offset_x=0, escurecer=0, offset_y=0, forcar_ceu=False):
    fundo = _fundos.get(sala_idx)
    mapa = DADOS_MAPAS.get(sala_idx, DADOS_MAPAS[0])
    ceu_aberto = True if forcar_ceu else mapa.get("ceu_aberto", mapa["visual"].get("ceu_aberto", True))
    surface.fill((8, 10, 18) if not ceu_aberto else mapa.get("cor_fundo", (12, 16, 28)))

    if ceu_aberto and fundo is not None:
        if fundo["ceu"] is not None:
            _blit_loop(surface, fundo["ceu"], offset_x * 0.08, offset_y * 0.05)
        if fundo["mid"] is not None:
            _blit_loop(surface, fundo["mid"], offset_x * 0.22, offset_y * 0.12)
        if fundo["grama"] is not None:
            _blit_loop(surface, fundo["grama"], offset_x * 0.45, offset_y * 0.22)

    # Lua noturna posicionada no canto superior direito livre (sem caixas de HUD por cima)
    if ceu_aberto:
        lua_x = max(700, min(880, int(815 - offset_x * 0.03)))
        lua_y = max(62, min(126, int(82 - offset_y * 0.04)))
        halo = pygame.Surface((84, 84), pygame.SRCALPHA)
        pygame.draw.circle(halo, (226, 232, 240, 26), (42, 42), 40)
        surface.blit(halo, (lua_x - 42, lua_y - 42))
        pygame.draw.circle(surface, (226, 232, 240), (lua_x, lua_y), 24)
        pygame.draw.circle(surface, (186, 200, 224), (lua_x - 7, lua_y - 4), 5)

    tint = _tints.get(sala_idx)
    if tint is not None:
        surface.blit(tint, (0, 0))
    if escurecer:
        sombra = pygame.Surface(surface.get_size())
        sombra.fill((5, 4, 12))
        sombra.set_alpha(escurecer)
        surface.blit(sombra, (0, 0))


def miniatura_sala(idx, tamanho=(150, 84)):
    chave = (idx, tamanho)
    if chave not in _miniaturas:
        _garantir_atlas_32x32()
        grande = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        desenhar_fundo_sala(grande, idx, offset_x=0, offset_y=0)
        _desenhar_faixa_chao(grande, DADOS_MAPAS[idx], 0, pygame.Rect(0, 470, LARGURA_TELA, 70), 0, idx=idx)
        _miniaturas[chave] = pygame.transform.smoothscale(grande, tamanho)
    return _miniaturas[chave]


def _renderizar_textura_plataforma(estilo, w, h):
    return montar_superficie_bloco_autotile(
        w, h, base_tipo="cantaria", estilo=estilo,
        topo_exp=True, baixo_exp=True, esq_exp=True, dir_exp=True,
        semente=w * 7 + h
    )


def _obter_parede_surface(idx, par):
    chave = (idx, par.x, par.y, par.width, par.height)
    if chave in _CACHE_PAREDES:
        return _CACHE_PAREDES[chave]
    estilo_sala = DADOS_MAPAS.get(idx, DADOS_MAPAS[0])["visual"].get("plataforma", "pedra")
    estilo_par = "pedra" if estilo_sala == "madeira" else estilo_sala
    topo_exp = (par.y > 120 and (par.height <= 42 or par.width >= 68))
    surf = montar_superficie_bloco_autotile(
        par.width, par.height, base_tipo="cantaria", estilo=estilo_par,
        topo_exp=topo_exp, baixo_exp=True, esq_exp=True, dir_exp=True,
        semente=par.x + par.y + idx * 17
    )
    _CACHE_PAREDES[chave] = surf
    return surf


def _desenhar_plataforma(surface, rect_tela, estilo, aerea=False):
    chave = (estilo, rect_tela.width, rect_tela.height)
    if chave not in _CACHE_PLATAFORMAS:
        _CACHE_PLATAFORMAS[chave] = _renderizar_textura_plataforma(estilo, rect_tela.width, rect_tela.height)

    if aerea:
        # Correntes forjadas em elos alternados ligando passarelas aéreas às ameias
        y_topo = max(0, rect_tela.top - 90)
        for cx in (rect_tela.left + 12, rect_tela.right - 12):
            for cy_l in range(y_topo, rect_tela.top, 6):
                alt_l = min(5, rect_tela.top - cy_l)
                if alt_l >= 2:
                    pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (cx - 2, cy_l, 4, alt_l), 1)
                    pygame.draw.line(surface, COR_LUZ_CANTARIA[:3], (cx - 1, cy_l + 1), (cx - 1, cy_l + alt_l - 1), 1)
    surface.blit(_CACHE_PLATAFORMAS[chave], rect_tela.topleft)


def _desenhar_faixa_chao(surface, mapa, camera_x, chao_rect, camera_y=0, idx=None):
    topo = int(chao_rect.top - camera_y)
    if topo >= surface.get_height():
        return
    if idx is None:
        idx = next((i for i, d in DADOS_MAPAS.items() if d is mapa), 0)
    strip = _obter_chao_strip(idx)
    sw = strip.get_width()
    x_ini = -(int(camera_x) % sw)
    for x in range(x_ini, surface.get_width(), sw):
        surface.blit(strip, (x, topo))

    sh_rest = surface.get_height() - topo
    if sh_rest > strip.get_height():
        tiles_m = _ATLAS_32[("rocha", "miolo")]
        off_tx = int(camera_x) // TAM_TILE
        x0 = -(int(camera_x) % TAM_TILE)
        for py in range(topo + strip.get_height(), surface.get_height(), TAM_TILE):
            gy = (py - topo) // TAM_TILE
            for col_i, px in enumerate(range(x0, surface.get_width(), TAM_TILE)):
                surface.blit(tiles_m[(off_tx + col_i + gy + idx) & 3], (px, py))


def desenhar_decoracoes(surface, idx, camera_x, camera_y=0):
    mapa = DADOS_MAPAS[idx]
    if mapa.get("tipologia") == "A":
        base_y_m = mapa["chao"].top
    else:
        slabs = [p.top for p in mapa.get("paredes", []) if p.width >= 300 and p.height <= 42 and p.top > 120]
        base_y_m = slabs[0] if slabs else mapa["chao"].top
    base = int(base_y_m + 4 - camera_y)
    larg_m = mapa.get("largura", LARGURA_MUNDO)
    for nome, x, escala, par in mapa["visual"]["decor"]:
        if x >= larg_m - 120:
            continue
        img = peca(nome, escala)
        if img is None:
            continue
        sx = int(x - camera_x * par)
        sy = base - img.get_height()
        if sx > surface.get_width() or sx + img.get_width() < 0 or sy > surface.get_height() or sy + img.get_height() < 0:
            continue
        surface.blit(img, (sx, sy))


def _desenhar_props_dinamicos_sala(surface, mapa, camera_x, camera_y, tempo):
    """Renderiza arandelas de fogo oscilante, tochas frias, mastros com bandeiras e lápides."""
    props = mapa.get("props")
    if not props:
        return
    vw, vh = surface.get_size()

    # 1) Lápides decorativas em primeiro plano / corredor
    for lx_m, ly_m in props.get("lapides", []):
        lx, ly = int(lx_m - camera_x), int(ly_m - camera_y)
        if lx < -40 or lx > vw + 40 or ly < -60 or ly > vh + 40:
            continue
        pygame.draw.rect(surface, (42, 48, 64), (lx - 11, ly - 24, 22, 24), border_top_left_radius=9, border_top_right_radius=9)
        pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (lx - 11, ly - 24, 22, 24), 1, border_top_left_radius=9, border_top_right_radius=9)
        pygame.draw.line(surface, (100, 116, 139), (lx - 6, ly - 15), (lx + 6, ly - 15), 1)
        pygame.draw.line(surface, (100, 116, 139), (lx, ly - 20), (lx, ly - 8), 1)

    # 2) Mastros de ferro com bandeiras góticas tremulantes ao vento
    for mx_m, my_chao, cor_pano, cor_borda in props.get("mastros", []):
        mx, my = int(mx_m - camera_x), int(my_chao - camera_y)
        if mx < -80 or mx > vw + 80 or my < -40 or my > vh + 140:
            continue
        alt_mastro = 96
        pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (mx - 6, my - 8, 12, 8))
        pygame.draw.line(surface, (148, 163, 184), (mx, my - alt_mastro), (mx, my), 3)
        pygame.draw.circle(surface, (245, 158, 11), (mx, my - alt_mastro), 3)
        onda1 = int(math.sin(tempo * 4.2 + mx_m * 0.03) * 4)
        onda2 = int(math.cos(tempo * 5.1 + mx_m * 0.04) * 5)
        pts_band = [
            (mx + 2, my - alt_mastro + 6),
            (mx + 26, my - alt_mastro + 10 + onda1),
            (mx + 46, my - alt_mastro + 16 + onda2),
            (mx + 34, my - alt_mastro + 26 + onda1),
            (mx + 44, my - alt_mastro + 36 + onda2),
            (mx + 2, my - alt_mastro + 32),
        ]
        pygame.draw.polygon(surface, cor_pano, pts_band)
        pygame.draw.polygon(surface, cor_borda, pts_band, 1)

    # 3) Arandelas de parede com chamas oscilantes e halo suave SRCALPHA (zero BLEND_ADD)
    for tx_m, ty_m, estilo_t in props.get("tochas_parede", []):
        tx, ty = int(tx_m - camera_x), int(ty_m - camera_y)
        if tx < -70 or tx > vw + 70 or ty < -70 or ty > vh + 70:
            continue
        osc = math.sin(tempo * 7.5 + tx_m * 0.13)
        if estilo_t == "fria_azul":
            c_halo, c_ext, c_nuc = (56, 189, 248), (14, 165, 233), (224, 242, 254)
        elif estilo_t == "fria_roxa":
            c_halo, c_ext, c_nuc = (168, 85, 247), (126, 34, 206), (243, 232, 255)
        else:
            c_halo, c_ext, c_nuc = (249, 115, 22), (220, 38, 38), (254, 240, 138)

        # Halo suave SRCALPHA sem BLEND_ADD
        s_h = pygame.Surface((88, 88), pygame.SRCALPHA)
        r_var = int(38 + osc * 4)
        pygame.draw.circle(s_h, (*c_halo, 16), (44, 44), r_var)
        pygame.draw.circle(s_h, (*c_halo, 34), (44, 44), int(r_var * 0.52))
        pygame.draw.circle(s_h, (*c_nuc, 55), (44, 44), 9)
        surface.blit(s_h, (tx - 44, ty - 52))

        # Arandela em ferro forjado
        pygame.draw.rect(surface, (30, 41, 59), (tx - 3, ty, 6, 16))
        pygame.draw.rect(surface, (100, 116, 139), (tx - 5, ty - 2, 10, 4))
        # Chama cônica animada
        dx_c = int(osc * 2)
        pygame.draw.polygon(surface, c_ext, [(tx - 5, ty - 2), (tx + dx_c, ty - 17), (tx + 5, ty - 2)])
        pygame.draw.polygon(surface, c_halo, [(tx - 3, ty - 2), (tx + dx_c, ty - 13), (tx + 3, ty - 2)])
        pygame.draw.circle(surface, c_nuc, (tx, ty - 5), 2)


def desenhar_estruturas_organicas(surface, idx, camera_x, camera_y=0, tempo=0.0):
    """Blita a arquitetura cacheada dos biomas e anima tochas de parede, mastros e lápides."""
    camadas = _construir_arquitetura_3_camadas(idx)
    vw, vh = surface.get_size()
    rx = max(0, min(max(0, camadas.get_width() - vw), int(camera_x)))
    ry = max(0, min(max(0, camadas.get_height() - vh), int(camera_y)))
    surface.blit(camadas, (0, 0), area=pygame.Rect(rx, ry, min(vw, camadas.get_width()), min(vh, camadas.get_height())))
    _desenhar_props_dinamicos_sala(surface, DADOS_MAPAS[idx], camera_x, camera_y, tempo)


def desenhar_terreno(surface, idx, camera_x, camera_y=0):
    mapa = DADOS_MAPAS[idx]
    visual = mapa["visual"]
    _desenhar_faixa_chao(surface, mapa, camera_x, mapa["chao"], camera_y, idx=idx)

    # Paredes e lajes maciças de cantaria texturizada (divisórias de camadas e muralha central)
    vw = surface.get_width()
    vh = surface.get_height()
    for par in mapa.get("paredes", []):
        rp = pygame.Rect(int(par.x - camera_x), int(par.y - camera_y), par.width, par.height)
        if rp.right < -20 or rp.left > vw + 20 or rp.bottom < -20 or rp.top > vh + 20:
            continue
        tex_par = _obter_parede_surface(idx, par)
        area_x = max(0, -rp.x)
        area_w = min(rp.width - area_x, vw - max(0, rp.x))
        if area_w > 0:
            surface.blit(tex_par, (max(0, rp.x), rp.y), area=pygame.Rect(area_x, 0, area_w, rp.height))

    # Trilhos mecânicos de ferro para plataformas móveis (Sala 6: Cripta dos Ossos)
    for pm in mapa.get("plataformas_moveis", []):
        p_r = pm["rect"]
        bx_t = int(pm["base_x"] - camera_x)
        by_t = int(pm["base_y"] - camera_y)
        if pm.get("amp_x", 0.0) > 1.0:
            rx0 = int(pm["base_x"] - pm["amp_x"] + p_r.width // 2 - camera_x)
            rx1 = int(pm["base_x"] + pm["amp_x"] + p_r.width // 2 - camera_x)
            ry_c = int(pm["base_y"] + p_r.height // 2 - camera_y)
            pygame.draw.line(surface, (15, 23, 42), (rx0, ry_c), (rx1, ry_c), 5)
            pygame.draw.line(surface, (100, 116, 139), (rx0, ry_c), (rx1, ry_c), 2)
            pygame.draw.circle(surface, (245, 158, 11), (rx0, ry_c), 3)
            pygame.draw.circle(surface, (245, 158, 11), (rx1, ry_c), 3)
        elif pm.get("amp_y", 0.0) > 1.0:
            rx_c = bx_t + p_r.width // 2
            ry0 = int(pm["base_y"] - pm["amp_y"] - camera_y)
            ry1 = int(pm["base_y"] + pm["amp_y"] + p_r.height - camera_y)
            pygame.draw.line(surface, (15, 23, 42), (rx_c, ry0), (rx_c, ry1), 5)
            pygame.draw.line(surface, (100, 116, 139), (rx_c, ry0), (rx_c, ry1), 2)

    for plat in mapa["plataformas"]:
        rt = pygame.Rect(int(plat.x - camera_x), int(plat.y - camera_y), plat.width, plat.height)
        if rt.right < -30 or rt.left > vw + 30 or rt.bottom < -30 or rt.top > vh + 30:
            continue
        _desenhar_plataforma(surface, rt, visual["plataforma"], aerea=False)


def desenhar_armadilhas(surface, idx, camera_x, tempo=0.0, camera_y=0):
    if tempo == 0.0:
        tempo = pygame.time.get_ticks() / 1000.0
    _garantir_atlas_32x32()
    for area, tipo in DADOS_MAPAS[idx].get("armadilhas", []):
        at = pygame.Rect(int(area.x - camera_x), int(area.y - camera_y), area.w, area.h)
        if at.right < -40 or at.left > surface.get_width() + 40 or at.bottom < -40 or at.top > surface.get_height() + 40:
            continue
        if tipo in ("espinhos", "ferro", "ossos"):
            cor_clara = (218, 226, 240) if tipo != "ossos" else (232, 224, 198)
            cor_escura = (105, 116, 138) if tipo != "ossos" else (142, 132, 110)
            # Base de cantaria fixando os espinhos
            pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (at.x, at.bottom - 5, at.w, 5))
            pygame.draw.line(surface, COR_LUZ_CANTARIA[:3], (at.x + 1, at.bottom - 4), (at.right - 2, at.bottom - 4), 1)
            for sx in range(at.x + 2, at.right - 8, 14):
                p_topo = (sx + 7, at.top + 2)
                pygame.draw.polygon(surface, cor_clara, [(sx, at.bottom - 4), p_topo, (sx + 7, at.bottom - 4)])
                pygame.draw.polygon(surface, cor_escura, [(sx + 7, at.bottom - 4), p_topo, (sx + 14, at.bottom - 4)])
                pygame.draw.polygon(surface, COR_TRINCA_CANTARIA[:3], [(sx, at.bottom - 4), p_topo, (sx + 14, at.bottom - 4)], 1)
        else:
            if tipo == "veneno":
                c_fundo, c_meio, c_luz = (12, 48, 24), (20, 83, 45), (74, 222, 128)
            elif tipo == "sangue":
                c_fundo, c_meio, c_luz = (68, 12, 20), (138, 24, 34), (244, 63, 94)
            else:
                c_fundo, c_meio, c_luz = (24, 18, 54), (62, 42, 118), COR_BRILHO_ETER[:3]
            # Bacia em pedra esculpida com líquido ondulado e reflexos
            pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (at.x, at.y + 3, at.w, at.h - 3))
            pygame.draw.rect(surface, c_fundo, (at.x + 2, at.y + 5, at.w - 4, at.h - 6))
            pygame.draw.rect(surface, c_meio, (at.x + 4, at.y + 6, at.w - 8, max(3, (at.h - 8) // 2)))
            pygame.draw.rect(surface, COR_LUZ_CANTARIA[:3], (at.x, at.y + 4, 3, at.h - 4))
            pygame.draw.rect(surface, COR_LUZ_CANTARIA[:3], (at.right - 3, at.y + 4, 3, at.h - 4))
            for bx in range(at.x + 8, at.right - 10, 18):
                desl = int(math.sin(tempo * 3.5 + bx) * 2)
                pygame.draw.line(surface, c_luz, (bx, at.y + 7 + (desl & 1)), (bx + 6, at.y + 7 + (desl & 1)), 1)


_CACHE_PORTAL_SAIDA = None


def _obter_textura_portal():
    global _CACHE_PORTAL_SAIDA
    if _CACHE_PORTAL_SAIDA is None:
        caminho = obter_caminho_recurso(os.path.join("assets", "ui", "portal_saida.png"))
        if os.path.exists(caminho):
            try:
                img = pygame.image.load(caminho).convert_alpha()
                w_p, h_p = 125, int(125 * (img.get_height() / float(img.get_width())))
                _CACHE_PORTAL_SAIDA = pygame.transform.smoothscale(img, (w_p, h_p))
            except Exception:
                _CACHE_PORTAL_SAIDA = False
        else:
            _CACHE_PORTAL_SAIDA = False
    return _CACHE_PORTAL_SAIDA if _CACHE_PORTAL_SAIDA is not False else None


def desenhar_saida(surface, camera_x, boss_vivo, tempo, camera_y=0, portal_pos=None):
    tex_portal = _obter_textura_portal()
    pw, ph = (125, 180) if tex_portal is None else (tex_portal.get_width(), tex_portal.get_height())
    px_m, py_m = portal_pos if portal_pos else (LARGURA_MUNDO - pw - 30, LIMITE_SUBSOLO - ph)
    px, py = int(px_m - camera_x), int(py_m - camera_y)
    if -pw <= px <= surface.get_width() + pw and -ph <= py <= surface.get_height() + ph:
        pulso = 0.5 + 0.5 * math.sin(tempo * 3.2)
        if tex_portal is not None:
            surface.blit(tex_portal, (px, py))
            if boss_vivo:
                pygame.draw.line(surface, (220, 38, 38), (px + 20, py + 30), (px + pw - 20, py + ph - 20), 3)
                pygame.draw.line(surface, (220, 38, 38), (px + pw - 20, py + 30), (px + 20, py + ph - 20), 3)
        else:
            cor = (180, 30, 50) if boss_vivo else (56, 189, 248)
            pygame.draw.rect(surface, cor, (px, py, pw, ph), 2, border_radius=6)


def _obter_bau_surface(aberto=False):
    if aberto in _CACHE_BAUS:
        return _CACHE_BAUS[aberto]
    s = montar_superficie_bloco_autotile(
        32, 24, base_tipo="cantaria", estilo="madeira",
        topo_exp=True, baixo_exp=True, esq_exp=True, dir_exp=True, semente=99
    )
    pa = pygame.PixelArray(s)
    try:
        m = s.map_rgb
        m_ouro = m((245, 158, 11, 255))
        m_ouro_c = m((253, 230, 138, 255))
        m_ouro_s = m((146, 64, 14, 255))
        m_tr = m(COR_TRINCA_CANTARIA)
        # Cintas metálicas verticais e aro de latão
        for x in (6, 7, 24, 25):
            for y in range(2, 22):
                pa[x, y] = m_ouro if x in (6, 24) else m_ouro_s
        for x in range(1, 31):
            pa[x, 9] = m_tr
            pa[x, 10] = m_ouro_c if not aberto else m_ouro_s
        if not aberto:
            for y in range(9, 16):
                for x in range(13, 19):
                    if y in (9, 15) or x in (13, 18):
                        pa[x, y] = m_tr
                    elif y == 10 or x == 14:
                        pa[x, y] = m_ouro_c
                    else:
                        pa[x, y] = m_ouro
        else:
            for y in range(2, 8):
                for x in range(3, 29):
                    pa[x, y] = m_tr
    finally:
        pa.close()
    res = _converter_surf(s)
    _CACHE_BAUS[aberto] = res
    return res


def desenhar_portoes(surface, grupo_sala, camera_x, camera_y, tempo):
    """Renderiza portões em arco de cantaria/ferro forjado ou pontes levadiças das ruínas."""
    global _CACHE_PORTAO_BATENTE
    _garantir_atlas_32x32()
    pulso = 0.5 + 0.5 * math.sin(tempo * 3.8)
    for gate in grupo_sala.get("portoes", []):
        g_rect = gate["rect"]
        gx, gy = int(g_rect.x - camera_x), int(g_rect.y - camera_y)
        gw, gh = g_rect.width, g_rect.height

        # Ponte levadiça horizontal estendida quando destrancada (Tipo B)
        if "ponte" in gate:
            pr = gate["ponte"]
            if gate.get("aberto", False):
                px_b, py_b = int(pr.x - camera_x), int(pr.y - camera_y)
                if px_b + pr.width >= -40 and px_b <= surface.get_width() + 40:
                    ch_ponte = ("madeira", pr.width, pr.height)
                    if ch_ponte not in _CACHE_PLATAFORMAS:
                        _CACHE_PLATAFORMAS[ch_ponte] = _renderizar_textura_plataforma("madeira", pr.width, pr.height)
                    surface.blit(_CACHE_PLATAFORMAS[ch_ponte], (px_b, py_b))
                    pygame.draw.line(surface, (148, 163, 184), (px_b + 8, py_b - 68), (px_b + 96, py_b), 2)
                    pygame.draw.line(surface, (148, 163, 184), (px_b + pr.width - 8, py_b - 68), (px_b + pr.width - 96, py_b), 2)

        if gx + gw < -60 or gx > surface.get_width() + 60 or gy + gh < -40 or gy > surface.get_height() + 40:
            continue

        ch_b = (gw, gh)
        if ch_b not in _CACHE_PORTAO_BATENTE:
            bat_esq = montar_superficie_bloco_autotile(14, gh + 6, "cantaria", "pedra", True, True, True, False, semente=11)
            bat_dir = montar_superficie_bloco_autotile(14, gh + 6, "cantaria", "pedra", True, True, False, True, semente=22)
            arco_sup = montar_superficie_bloco_autotile(gw + 36, 26, "cantaria", "pedra", True, True, True, True, semente=33)
            soleira = montar_superficie_bloco_autotile(gw + 34, 10, "cantaria", "ferro", True, True, True, True, semente=44)
            fundo_vao = pygame.Surface((gw, gh), pygame.SRCALPHA)
            tiles_e = _ATLAS_32[("pedra", "escuro")]
            for gy_v in range((gh + TAM_TILE - 1) // TAM_TILE):
                for gx_v in range((gw + TAM_TILE - 1) // TAM_TILE):
                    fundo_vao.blit(tiles_e[(gx_v + gy_v) & 3], (gx_v * TAM_TILE, gy_v * TAM_TILE))
            veio_somb = pygame.Surface((gw, gh), pygame.SRCALPHA)
            veio_somb.fill((4, 6, 12, 180))
            fundo_vao.blit(veio_somb, (0, 0))
            vao_aberto = pygame.Surface((gw, gh), pygame.SRCALPHA)
            for ty_a in range(0, gh, 4):
                alpha_v = max(25, 110 - int((ty_a / max(1, gh)) * 75))
                pygame.draw.rect(vao_aberto, (6, 8, 16, alpha_v), (0, ty_a, gw, 4))
            _CACHE_PORTAO_BATENTE[ch_b] = (
                bat_esq, bat_dir, arco_sup, soleira,
                _converter_surf(fundo_vao), _converter_surf(vao_aberto)
            )

        bat_esq, bat_dir, arco_sup, soleira, fundo_vao, vao_aberto = _CACHE_PORTAO_BATENTE[ch_b]

        if not gate.get("aberto", False):
            surface.blit(fundo_vao, (gx, gy))
            e_titanico = (gate.get("tipo") == "titanico_runico")
            for bx in range(gx + 5, gx + gw - 4, 10):
                pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (bx - 1, gy + 2, 6, gh - 4))
                pygame.draw.line(surface, (148, 163, 184), (bx, gy + 3), (bx, gy + gh - 5), 1)
                pygame.draw.line(surface, (71, 85, 105), (bx + 1, gy + 3), (bx + 2, gy + gh - 5), 1)
                pygame.draw.line(surface, (30, 41, 59), (bx + 3, gy + 3), (bx + 3, gy + gh - 5), 1)
            cy_s = gy + gh // 2
            if e_titanico:
                # Travas duplas titânicas e fechadura rúnica em ciano/ouro
                for off_y in (-48, 48):
                    pygame.draw.rect(surface, (30, 41, 59), (gx - 2, cy_s + off_y - 4, gw + 4, 8))
                    pygame.draw.line(surface, (180, 83, 9), (gx - 2, cy_s + off_y - 4), (gx + gw + 2, cy_s + off_y - 4), 1)
                r_ext = int(15 + 2 * pulso)
                pygame.draw.circle(surface, COR_TRINCA_CANTARIA[:3], (gx + gw // 2, cy_s), r_ext + 2)
                pygame.draw.circle(surface, (56, 189, 248), (gx + gw // 2, cy_s), r_ext, 2)
                pygame.draw.circle(surface, (245, 158, 11), (gx + gw // 2, cy_s), int(8 + 2 * pulso))
                pygame.draw.circle(surface, (224, 242, 254), (gx + gw // 2, cy_s), 3)
            else:
                pygame.draw.line(surface, COR_TRINCA_CANTARIA[:3], (gx + 2, cy_s - 28), (gx + gw - 2, cy_s + 28), 5)
                pygame.draw.line(surface, (148, 163, 184), (gx + 2, cy_s - 28), (gx + gw - 2, cy_s + 28), 2)
                pygame.draw.line(surface, COR_TRINCA_CANTARIA[:3], (gx + gw - 2, cy_s - 28), (gx + 2, cy_s + 28), 5)
                pygame.draw.line(surface, (148, 163, 184), (gx + gw - 2, cy_s - 28), (gx + 2, cy_s + 28), 2)
                pygame.draw.circle(surface, COR_TRINCA_CANTARIA[:3], (gx + gw // 2, cy_s), int(9 + 2 * pulso))
                pygame.draw.circle(surface, (245, 158, 11), (gx + gw // 2, cy_s), int(7 + 2 * pulso))
                pygame.draw.circle(surface, (253, 230, 138), (gx + gw // 2 - 2, cy_s - 2), 2)
        else:
            # Portão aberto: vão sombreado + pontas da grade de ferro recolhidas no arco de pedra
            surface.blit(vao_aberto, (gx, gy))
            for bx in range(gx + 5, gx + gw - 4, 10):
                pygame.draw.rect(surface, COR_TRINCA_CANTARIA[:3], (bx - 1, gy, 6, 12))
                pygame.draw.line(surface, (148, 163, 184), (bx, gy), (bx, gy + 10), 1)
                pygame.draw.line(surface, (71, 85, 105), (bx + 1, gy), (bx + 2, gy + 11), 1)
                pygame.draw.polygon(surface, (30, 41, 59), [(bx, gy + 11), (bx + 4, gy + 11), (bx + 2, gy + 15)])

        # Batentes verticais, arco esculpido superior e soleira ancorada ao chão
        surface.blit(bat_esq, (gx - 14, gy - 4))
        surface.blit(bat_dir, (gx + gw, gy - 4))
        surface.blit(arco_sup, (gx - 18, gy - 26))
        pygame.draw.line(surface, (180, 83, 9), (gx - 16, gy - 2), (gx + gw + 16, gy - 2), 1)
        surface.blit(soleira, (gx - 17, gy + gh - 2))


def desenhar_alavancas(surface, grupo_sala, camera_x, camera_y, tempo):
    global _CACHE_ALAVANCA_BASE
    if _CACHE_ALAVANCA_BASE is None:
        _CACHE_ALAVANCA_BASE = montar_superficie_bloco_autotile(
            28, 14, base_tipo="cantaria", estilo="pedra",
            topo_exp=True, baixo_exp=True, esq_exp=True, dir_exp=True, semente=55
        )
    for alav in grupo_sala.get("alavancas", []):
        lx, ly = int(alav["x"] - camera_x), int(alav["y"] - camera_y)
        if lx < -40 or lx > surface.get_width() + 40 or ly < -40 or ly > surface.get_height() + 40:
            continue
        acionada = alav.get("acionada", False)
        ponta = (lx + 12, ly - 22) if acionada else (lx - 12, ly - 22)
        cor_gema = (34, 197, 94) if acionada else (220, 38, 38)
        pygame.draw.line(surface, COR_TRINCA_CANTARIA[:3], (lx, ly + 1), ponta, 5)
        pygame.draw.line(surface, (165, 178, 198), (lx, ly + 1), ponta, 2)
        surface.blit(_CACHE_ALAVANCA_BASE, (lx - 14, ly))
        pygame.draw.circle(surface, COR_TRINCA_CANTARIA[:3], ponta, 6)
        pygame.draw.circle(surface, cor_gema, ponta, 4)
        pygame.draw.circle(surface, (241, 245, 249), (ponta[0] - 1, ponta[1] - 1), 1)


def desenhar_chaves(surface, grupo_sala, camera_x, camera_y, tempo):
    for ch in grupo_sala.get("chaves", []):
        if ch.get("coletada", False):
            continue
        cx, cy = int(ch["x"] - camera_x), int(ch["y"] - camera_y)
        if cx < -40 or cx > surface.get_width() + 40 or cy < -40 or cy > surface.get_height() + 40:
            continue
        flutua = cy + int(math.sin(tempo * 3.5) * 4)
        pygame.draw.circle(surface, (253, 230, 138), (cx, flutua - 6), 6, 2)
        pygame.draw.line(surface, (253, 230, 138), (cx, flutua), (cx, flutua + 12), 2)
        pygame.draw.line(surface, (253, 230, 138), (cx, flutua + 9), (cx + 5, flutua + 9), 2)


def desenhar_baus(surface, grupo_sala, camera_x, camera_y, tempo):
    for b in grupo_sala.get("baus", []):
        bx, by = int(b["x"] - camera_x), int(b["y"] - camera_y)
        if bx < -40 or bx > surface.get_width() + 40 or by < -40 or by > surface.get_height() + 40:
            continue
        tex_bau = _obter_bau_surface(bool(b.get("aberto", False)))
        surface.blit(tex_bau, (bx - 16, by - 24))


def desenhar_prompts_interacao(surface, grupo_sala, jogador, camera_x, camera_y, tempo, fonte):
    cj_x, cj_y = jogador.x + jogador.largura / 2, jogador.y + jogador.altura / 2
    candidatos = []
    for alav in grupo_sala.get("alavancas", []):
        if not alav.get("acionada", False):
            d = math.hypot(cj_x - alav["x"], cj_y - alav["y"])
            if d < 85:
                candidatos.append((d, alav["x"], alav["y"] - 32, f"[E] {alav.get('texto', 'Alavanca')}"))
    for ch in grupo_sala.get("chaves", []):
        if not ch.get("coletada", False):
            d = math.hypot(cj_x - ch["x"], cj_y - ch["y"])
            if d < 75:
                candidatos.append((d, ch["x"], ch["y"] - 32, f"[E] {ch.get('nome', 'Chave')}"))
    for b in grupo_sala.get("baus", []):
        if not b.get("aberto", False):
            d = math.hypot(cj_x - b["x"], cj_y - b["y"])
            if d < 75:
                candidatos.append((d, b["x"], b["y"] - 34, "[E] Abrir Baú"))
    for gate in grupo_sala.get("portoes", []):
        if not gate.get("aberto", False):
            g_rect = gate["rect"]
            if abs(cj_x - g_rect.centerx) < 68 and abs(cj_y - g_rect.centery) < g_rect.height // 2 + 40:
                if getattr(jogador, "chaves_bolsa", 0) > 0:
                    msg_g = f"[E] Usar Chave da Bolsa ({jogador.chaves_bolsa})"
                else:
                    msg_g = f"[E] {gate.get('nome', 'Portão Trancado')}"
                candidatos.append((20.0, g_rect.centerx, g_rect.centery - 46, msg_g))
    if not candidatos:
        return
    candidatos.sort(key=lambda item: item[0])
    _, ox, oy, txt = candidatos[0]
    tx, ty = int(ox - camera_x), int(oy - camera_y + math.sin(tempo * 4.5) * 2)
    s_t = fonte.render(txt, True, (253, 230, 138))
    r = pygame.Rect(tx - s_t.get_width() // 2 - 12, ty - s_t.get_height() // 2 - 5, s_t.get_width() + 24, s_t.get_height() + 10)
    ui_procedural.desenhar_moldura_gotica(surface, r, chanfro=5, destacado=True, alpha=244, cantoneiras=False)
    surface.blit(s_t, (r.x + 12, r.y + 5))


def obter_objetivo_sala(mapa_idx, mapa_atual, grupo_sala, jogador=None):
    boss = grupo_sala.get("boss")
    boss_vivo = getattr(boss, "vivo", True)
    gate = next(iter(grupo_sala.get("portoes", [])), None)
    aberto = gate.get("aberto", False) if gate else False

    if mapa_idx == 6:
        runas = len(getattr(jogador, "runas_ativadas", set())) if jogador else 0
        if runas < 3:
            return (f"Glifos ({runas}/3) — Quebre o Escudo!", False)
        return ("Escudo Quebrado! Derrote o Chefe" if boss_vivo else "Atravesse o Portal!", True)
    if not aberto:
        if gate and gate.get("tipo") == "ponte_levadica":
            return ("Ative a Ponte Levadiça", False)
        return ("Destranque o Portão (Alavanca ou Chave)", False)
    return ("Derrote o Guardião" if boss_vivo else "Atravesse o Portal", True)


def obter_sub_regiao(sala_idx, y_absoluto_jogador):
    mapa = DADOS_MAPAS.get(sala_idx)
    faixas = mapa.get("sub_regioes") if mapa and mapa.get("sub_regioes") else SUB_REGIOES.get(sala_idx, [])
    for y_min, y_max, nome in faixas:
        if y_min <= y_absoluto_jogador < y_max:
            return nome
    return ""


def desenhar_atmosfera_camada(surface, sala_idx, camera_y, jogador_y_abs, tempo=0.0):
    w, h = surface.get_size()
    if jogador_y_abs > LIMITE_SUBSOLO:
        fog = pygame.Surface((w, 36), pygame.SRCALPHA)
        for fy in range(36):
            pygame.draw.line(fog, (16, 24, 34, int((fy / 35.0) * 44)), (0, fy), (w, fy))
        surface.blit(fog, (0, h - 36))
    elif jogador_y_abs < LIMITE_AEREO:
        brisa = pygame.Surface((w, 24), pygame.SRCALPHA)
        for by in range(24):
            pygame.draw.line(brisa, (148, 163, 184, int((1.0 - by / 23.0) * 18)), (0, by), (w, by))
        surface.blit(brisa, (0, 0))


class Vagalumes:
    def __init__(self, quantidade=48):
        self.itens = [self._novo() for _ in range(quantidade)]
        self.t = 0.0

    @staticmethod
    def _novo():
        return {
            "x": random.uniform(0, LARGURA_TELA), "y": random.uniform(80, ALTURA_TELA - 40),
            "vx": random.uniform(-10, 10), "vy": random.uniform(-14, -3),
            "fase": random.uniform(0, 6.28), "r": random.choice((1, 2, 2)),
        }

    def update(self, dt):
        self.t += dt
        for p in self.itens:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] < 40 or p["x"] < -10 or p["x"] > LARGURA_TELA + 10:
                p.update(self._novo())
                p["y"] = random.uniform(ALTURA_TELA - 140, ALTURA_TELA - 20)

    def draw(self, surface, cor):
        for p in self.itens:
            a = 0.5 + 0.5 * math.sin(self.t * 2.2 + p["fase"])
            r = p["r"]
            halo = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*cor, int(45 * a)), (r * 3, r * 3), r * 3)
            pygame.draw.circle(halo, (*cor, int(90 + 165 * a)), (r * 3, r * 3), r)
            surface.blit(halo, (int(p["x"]) - r * 3, int(p["y"]) - r * 3))


_cenario_25d_fallback = None


def desenhar_fundo_combate(surface, tempo=0.0, cam=None, sala_idx=0):
    global _cenario_25d_fallback
    if _cenario_25d_fallback is None:
        _cenario_25d_fallback = CenarioCombate25D(LARGURA_TELA, ALTURA_TELA, sala_idx=sala_idx)
    else:
        _cenario_25d_fallback.definir_sala(sala_idx)
    _cenario_25d_fallback.tempo = tempo
    cam_use = cam if cam is not None else CameraCombate25D(LARGURA_TELA, ALTURA_TELA)
    _cenario_25d_fallback.desenhar_completo(surface, cam_use, [])
