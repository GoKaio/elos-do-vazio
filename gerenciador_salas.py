# -*- coding: utf-8 -*-
"""
Gerenciador das 7 Salas Góticas em 4 Biomas Temáticos - Elos do Vazio.

Integra os recursos do pacote `Legacy-Dungeon_V0.2_vacaroxa.zip` (`Final/Assets/` ->
`Background_1.png`, `Background_2.png`, `Background_0.png`, `Assets.png`) com carregamento
automático em disco ou direto do `.zip` em memória, mantendo fallback procedural de pixel art
para cada camada e prop (arandelas, mastros com bandeira, correntes, grades, arcos,
lápides, tochas frias, plataformas móveis, pilares com gárgulas e portão titânico rúnico).
"""

import glob
import io
import math
import os
import random
import zipfile
import pygame

from config import CONFIG
from caminhos import obter_caminho_recurso, obter_dir_base

HP_BASE = CONFIG.get("inimigo_hp_padrao", 140)

BIOMAS_TEMATICOS = {
    "ameias": {
        "titulo": "Ameias e Pátio Superior",
        "fundo": "Background_1.png",
        "ceu_aberto": True,
        "estilo_chao": "pedra",
        "estilo_plat": "pedra",
        "cor_fundo": (12, 16, 28),
        "tint": (10, 18, 42, 22),
        "vagalumes": (170, 235, 165),
    },
    "torres": {
        "titulo": "Galerias das Torres de Vigia",
        "fundo": "Background_2.png",
        "ceu_aberto": True,
        "estilo_chao": "ferro",
        "estilo_plat": "pedra",
        "cor_fundo": (13, 15, 28),
        "tint": (18, 22, 54, 30),
        "vagalumes": (165, 210, 255),
    },
    "catacumbas": {
        "titulo": "Cripta e Catacumbas Subterrâneas",
        "fundo": None,
        "ceu_aberto": False,
        "estilo_chao": "cripta",
        "estilo_plat": "cripta",
        "cor_fundo": (8, 9, 16),
        "tint": (28, 16, 48, 36),
        "vagalumes": (160, 185, 255),
    },
    "santuario": {
        "titulo": "Santuário do Guardião",
        "fundo": "Background_2.png",
        "ceu_aberto": False,
        "estilo_chao": "arcano",
        "estilo_plat": "catedral",
        "cor_fundo": (9, 11, 22),
        "tint": (22, 18, 58, 38),
        "vagalumes": (120, 225, 255),
    },
}


class CarregadorAssetsDungeon:
    """Localiza PNGs em `Final/Assets/`, `assets/final_pack/` ou direto de `.zip`."""

    def __init__(self):
        self._cache_imgs = {}
        self._zip_paths = None

    def _candidatos_dir(self):
        bases = []
        dir_base = obter_dir_base()
        pasta_cfg = CONFIG.get("pasta_assets", "assets")
        for rel in (
            os.path.join(pasta_cfg, "Legacy-Dungeon", "Final", "Assets"),
            os.path.join(pasta_cfg, "legacy_dungeon", "Final", "Assets"),
            os.path.join(pasta_cfg, "Legacy-Dungeon_V0.2_vacaroxa", "Final", "Assets"),
            os.path.join(pasta_cfg, "Final", "Assets"),
            os.path.join("Final", "Assets"),
            os.path.join(pasta_cfg, "final_pack"),
        ):
            p = obter_caminho_recurso(rel)
            if p not in bases:
                bases.append(p)
            p_loc = os.path.join(dir_base, rel)
            if p_loc not in bases:
                bases.append(p_loc)
        return bases

    def _listar_zips(self):
        if self._zip_paths is not None:
            return self._zip_paths
        zips = []
        dir_base = obter_dir_base()
        padroes = [
            os.path.join(dir_base, "Legacy-Dungeon*.zip"),
            os.path.join(dir_base, "assets", "Legacy-Dungeon*.zip"),
            os.path.join(dir_base, "*.zip"),
        ]
        for pad in padroes:
            for arq in glob.glob(pad):
                if "legacy" in os.path.basename(arq).lower() and arq not in zips:
                    zips.append(arq)
        self._zip_paths = zips
        return zips

    def carregar_imagem(self, nome_arquivo):
        chave = str(nome_arquivo or "").strip()
        if not chave:
            return None
        if chave in self._cache_imgs:
            return self._cache_imgs[chave]

        # 1) Procura descompactado em disco (priorizando Final/Assets e assets/final_pack)
        for pasta in self._candidatos_dir():
            cand = os.path.join(pasta, chave)
            if os.path.isfile(cand):
                try:
                    surf = pygame.image.load(cand).convert_alpha()
                    self._cache_imgs[chave] = surf
                    return surf
                except Exception:
                    pass

        # 2) Fallback direto em memória caso o usuário tenha deixado Legacy-Dungeon_V0.2_vacaroxa.zip no projeto
        alvo_lower = chave.lower()
        for zip_path in self._listar_zips():
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    candidatos_m = [
                        n for n in zf.namelist()
                        if n.lower().endswith("/" + alvo_lower) or n.lower() == alvo_lower
                    ]
                    if candidatos_m:
                        candidatos_m.sort(key=lambda s: (0 if "final/assets" in s.lower() else 1, len(s)))
                        dados = zf.read(candidatos_m[0])
                        surf = pygame.image.load(io.BytesIO(dados), chave).convert_alpha()
                        self._cache_imgs[chave] = surf
                        return surf
            except Exception:
                pass

        self._cache_imgs[chave] = None
        return None


ASSETS_DUNGEON = CarregadorAssetsDungeon()


def _spec_inimigo(nome, hp, cor, sprite, patrulha, combos):
    return {
        "nome": nome,
        "hp": int(hp),
        "cor": cor,
        "sprite": sprite,
        "patrulha": int(patrulha),
        "combos": int(combos),
    }


def _boss_spec(nome, hp, cor, combos, sprite, x, y, patrulha=95):
    return {
        "x": int(x),
        "y": int(y),
        "patrulha": int(patrulha),
        "nome": nome,
        "hp": int(hp),
        "cor": cor,
        "combos": int(combos),
        "sprite": sprite,
    }


class GerenciadorSalas:
    """
    Constrói, valida, atualiza e fornece as 7 salas completas em 4 biomas distintos:
      - Salas 1 e 2 (índices 0, 1): Bioma Ameias & Pátio Superior Exterior (`Background_1.png`)
      - Salas 3 e 4 (índices 2, 3): Bioma Galerias das Torres de Vigia (`Background_2.png`)
      - Salas 5 e 6 (índices 4, 5): Bioma Cripta & Catacumbas Subterrâneas (teto fechado)
      - Sala 7      (índice 6):     Bioma Santuário do Guardião (Arena 960 px Boss Room)
    """

    def __init__(self):
        self.assets = ASSETS_DUNGEON
        self.salas = {}
        self.sala_atual_idx = 0

    def construir_todas_salas(self, semente_base=None):
        rng_base = random.Random(semente_base) if semente_base is not None else random.Random()
        construtores = {
            0: self._construir_sala_1,
            1: self._construir_sala_2,
            2: self._construir_sala_3,
            3: self._construir_sala_4,
            4: self._construir_sala_5,
            5: self._construir_sala_6,
            6: self._construir_sala_7,
        }
        self.salas = {}
        for idx, fn in construtores.items():
            seed_s = rng_base.randint(1000, 99999)
            self.salas[idx] = fn(random.Random(seed_s))
        return self.salas

    def obter_sala(self, idx):
        if not self.salas:
            self.construir_todas_salas()
        return self.salas.get(max(0, min(6, int(idx))), self.salas[0])

    @staticmethod
    def _registrar_suporte(suportes, plat, tipo, paredes, chao):
        """Calcula apoio físico real de toda plataforma até a primeira alvenaria sólida abaixo."""
        y_bot = plat.bottom
        if tipo == "corrente":
            # Correntes presas no alto + suportes de pedra lascada nas bordas até o piso abaixo
            y_anc_top = 0
            for par in paredes:
                if par.bottom <= plat.top and par.left <= plat.centerx <= par.right:
                    y_anc_top = max(y_anc_top, par.bottom)
            for cx in (plat.left + 12, plat.right - 12):
                suportes.append({
                    "tipo": "corrente",
                    "plat": plat,
                    "x": int(cx),
                    "y_topo": int(y_anc_top),
                    "y_fim": int(plat.top),
                })
            # Consolo de pedra lascada abaixo da plataforma suspensa
            h_col = GerenciadorSalas._altura_ate_solo(plat.centerx, y_bot, paredes, chao)
            suportes.append({
                "tipo": "pedra_lascada",
                "plat": plat,
                "rect": pygame.Rect(plat.centerx - 12, y_bot, 24, min(28, h_col)),
            })
            return

        if tipo == "movel":
            suportes.append({
                "tipo": "trilho_movel",
                "plat": plat,
                "rect": pygame.Rect(plat.left, plat.top, plat.width, plat.height),
            })
            return

        if tipo == "coluna_dupla" and plat.width >= 110:
            for cx in (plat.left + 16, plat.right - 34):
                h_col = GerenciadorSalas._altura_ate_solo(cx + 9, y_bot, paredes, chao)
                suportes.append({"tipo": "coluna", "plat": plat, "rect": pygame.Rect(cx, y_bot, 18, h_col)})
        elif tipo == "escadaria":
            h_esc = GerenciadorSalas._altura_ate_solo(plat.centerx, y_bot, paredes, chao)
            suportes.append({"tipo": "escadaria", "plat": plat, "rect": pygame.Rect(plat.left + 4, y_bot, max(16, plat.width - 8), h_esc)})
        else:
            cx = plat.centerx - 11
            h_col = GerenciadorSalas._altura_ate_solo(plat.centerx, y_bot, paredes, chao)
            suportes.append({"tipo": "coluna", "plat": plat, "rect": pygame.Rect(cx, y_bot, 22, h_col)})

    @staticmethod
    def _altura_ate_solo(x_centro, y_inicio, paredes, chao, limite=720):
        melhor = chao.top if (chao.left <= x_centro <= chao.right and chao.top >= y_inicio) else (y_inicio + limite)
        for par in paredes:
            if par.left <= x_centro <= par.right and par.top >= y_inicio:
                if par.top < melhor:
                    melhor = par.top
        return max(8, int(melhor - y_inicio))

    @staticmethod
    def _montar_inimigos(specs, candidatos, spawn_x):
        usados = [(spawn_x, 0)]
        out = []
        for idx, sp in enumerate(specs):
            ax, ay_top, _ = candidatos[idx % len(candidatos)]
            ix = max(spawn_x + 340, int(ax))
            # Evita empilhamento em coordenadas próximas
            while any(abs(ux - ix) < 120 and abs(uy - ay_top) < 85 for ux, uy in usados):
                ix += 130
            usados.append((ix, ay_top))
            out.append({
                "x": ix,
                "y": int(ay_top - 52),
                "patrulha": sp["patrulha"],
                "nome": sp["nome"],
                "hp": sp["hp"],
                "cor": sp["cor"],
                "sprite": sp["sprite"],
                "combos": sp["combos"],
            })
        return out

    # =========================================================================
    # BIOMA 1: AMEIAS E PÁTIO SUPERIOR EXTERIOR (Salas 1 e 2)
    # =========================================================================
    def _construir_sala_1(self, rng):
        """Sala 1 (Entrada): Pátio das Ameias — Background_1.png, tochas de parede, mastros, chão contínuo."""
        bio = BIOMAS_TEMATICOS["ameias"]
        larg_m, alt_m, chao_y = 2160, 740, 660
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)
        gate_x = 1660

        paredes = [
            # Muralha de entrada à esquerda (torre de guarda parcial) e batente esquerdo
            pygame.Rect(0, 120, 40, chao_y - 120 - 150),
            # Mureta / baluarte médio divisório transponível por salto simples
            pygame.Rect(740, chao_y - 54, 110, 54),
            # Muralha leste sólida assentada no chão abrigando o portão de saída
            pygame.Rect(gate_x - 10, 0, 58, chao_y - 180),
        ]

        plataformas, suportes = [], []

        def _p(x, y, w, sup="coluna_dupla"):
            r = pygame.Rect(int(x), int(y), int(w), 18)
            plataformas.append(r)
            self._registrar_suporte(suportes, r, sup, paredes, chao)
            return r

        # Patamares de ameias baixas para ritmo fluido de combate e exploração
        p1 = _p(420, chao_y - 96, 195, "escadaria")
        p2 = _p(690, chao_y - 144, 210, "coluna_dupla")
        p3 = _p(1030, chao_y - 98, 220, "escadaria")
        p_alav = _p(1335, chao_y - 188, 200, "coluna_dupla")

        spawn_x = rng.randint(86, 122)
        spawn_heroi = (spawn_x, chao_y - 56)

        portoes = [{
            "id": "gate_sala1",
            "rect": pygame.Rect(gate_x, chao_y - 180, 38, 180),
            "aberto": False,
            "tipo": "grade_ferro",
            "nome": "Portão do Pátio das Ameias",
        }]
        alavancas = [{
            "id": "alav_s1",
            "x": p_alav.centerx,
            "y": p_alav.top,
            "alvo": "gate_sala1",
            "acionada": False,
            "texto": "Alavanca da Guarita",
            "msg_destrancado": "Portão do Pátio das Ameias Ergido!",
        }]
        chaves = [{
            "id": "chave_s1",
            "x": p2.centerx,
            "y": p2.top,
            "alvo": "gate_sala1",
            "coletada": False,
            "nome": "Chave do Pátio",
        }]
        baus = [{
            "id": "bau_s1",
            "x": p1.centerx,
            "y": p1.top,
            "aberto": False,
            "tipo": "pocao",
            "quantidade": 1,
            "nome": "Baú da Guarita",
        }]

        specs = [
            _spec_inimigo("Coveiro Sombrio", HP_BASE, (200, 50, 65), "Demon Carmesim", 85, 2),
            _spec_inimigo("Batedor das Ameias", HP_BASE - 15, (80, 150, 205), "Orc", 60, 2),
            _spec_inimigo("Vigia da Muralha", HP_BASE + 15, (140, 65, 150), "Blood Monster_A", 75, 2),
            _spec_inimigo("Sentinelas da Lua", HP_BASE + 20, (170, 50, 90), "Esqueleto", 85, 2),
        ]
        candidatos = [
            (520, chao_y, p1),
            (795, p2.top, p2),
            (1140, p3.top, p3),
            (1460, chao_y, chao),
        ]
        inimigos_spec = self._montar_inimigos(specs, candidatos, spawn_x)
        boss = _boss_spec("BOSS: GUARDIÃO DO CEMITÉRIO", CONFIG["boss_sala1_hp"], (155, 30, 195), 3, "Boss_Guardiao", x=gate_x + 170, y=chao_y - 88)

        # Elementos temáticos de Bioma 1: Arandelas de parede + Mastros com bandeira
        props = {
            "tochas_parede": [
                (210, chao_y - 96, "quente"),
                (540, chao_y - 104, "quente"),
                (960, chao_y - 102, "quente"),
                (1280, chao_y - 110, "quente"),
                (gate_x - 36, chao_y - 132, "quente"),
                (gate_x + 92, chao_y - 132, "quente"),
            ],
            "mastros": [
                (165, chao_y, (153, 27, 27), (245, 158, 11)),
                (910, chao_y, (30, 58, 138), (245, 158, 11)),
                (1560, chao_y, (153, 27, 27), (253, 230, 138)),
            ],
            "muretas_ameia": [(x_m, chao_y) for x_m in range(120, gate_x - 80, 140)],
        }

        return {
            "nome": "Pátio das Ameias",
            "bioma": "ameias",
            "tipologia": "BIOMA1_PATIO",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": True,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": [],
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": alavancas,
            "chaves": chaves,
            "baus": baus,
            "armadilhas": [(pygame.Rect(1180, chao_y - 18, 95, 18), "espinhos")],
            "spawn_heroi": spawn_heroi,
            "portal_saida": (larg_m - 175, chao_y - 180),
            "inimigos_spec": inimigos_spec,
            "boss": boss,
            "objetivo_tipo": "alavanca",
            "props": props,
            "semente": 101,
            "visual": {
                "mid": False, "grama": 1, "tint": bio["tint"], "chao": "pedra",
                "plataforma": "pedra", "vagalumes": bio["vagalumes"], "ceu_aberto": True,
                "fundo_arquivo": "Background_1.png",
                "decor": [("coluna", 320, 1.0, 1.0), ("estatua", 1590, 0.85, 1.0)],
            },
            "sub_regioes": [(0, alt_m, "Pátio das Ameias Exterior")],
        }

    def _construir_sala_2(self, rng):
        """Sala 2 (Ameias Superiores): Background_1.png, plataformas de pedra em 3 alturas, vãos entre muretas."""
        bio = BIOMAS_TEMATICOS["ameias"]
        larg_m, alt_m, chao_y = 2280, 900, 820
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)
        gate_x = 1780

        # Muretas escalonadas criando vãos entre trechos da ameia
        paredes = [
            pygame.Rect(460, chao_y - 68, 72, 68),
            pygame.Rect(980, chao_y - 84, 84, 84),
            pygame.Rect(1420, chao_y - 68, 72, 68),
            # Muralha sólida direita ancorando o portão até o topo
            pygame.Rect(gate_x - 10, 0, 58, chao_y - 180),
        ]

        plataformas, suportes = [], []

        def _p(x, y, w, sup="coluna_dupla"):
            r = pygame.Rect(int(x), int(y), int(w), 18)
            plataformas.append(r)
            self._registrar_suporte(suportes, r, sup, paredes, chao)
            return r

        # Desafio vertical em 3 alturas crescentes e decrescentes (degraus <= 96px, headroom >= 96px)
        y_n1 = chao_y - 96    # 724
        y_n2 = chao_y - 192   # 628
        y_n3 = chao_y - 288   # 532

        p_a1 = _p(265, y_n1, 180, "escadaria")
        p_b1 = _p(560, y_n2, 200, "coluna_dupla")
        p_c1 = _p(790, y_n3, 230, "coluna_dupla")
        p_b2 = _p(1090, y_n2, 210, "coluna_dupla")
        p_c2 = _p(1320, y_n3, 220, "coluna_dupla")
        p_a2 = _p(1545, y_n1, 195, "escadaria")

        spawn_x = rng.randint(86, 122)
        spawn_heroi = (spawn_x, chao_y - 56)

        portoes = [{
            "id": "gate_sala2",
            "rect": pygame.Rect(gate_x, chao_y - 180, 38, 180),
            "aberto": False,
            "tipo": "grade_ferro",
            "nome": "Portão das Ameias Altas",
        }]
        alavancas = [{
            "id": "alav_s2",
            "x": p_c2.centerx,
            "y": p_c2.top,
            "alvo": "gate_sala2",
            "acionada": False,
            "texto": "Guincho do Baluarte",
            "msg_destrancado": "Portão das Ameias Altas Destrancado!",
        }]
        chaves = [{
            "id": "chave_s2",
            "x": p_c1.centerx,
            "y": p_c1.top,
            "alvo": "gate_sala2",
            "coletada": False,
            "nome": "Chave da Vigia",
        }]
        baus = [{
            "id": "bau_s2",
            "x": p_b2.centerx,
            "y": p_b2.top,
            "aberto": False,
            "tipo": "eter",
            "quantidade": 2,
            "nome": "Baú das Ameias",
        }]

        specs = [
            _spec_inimigo("Atirador do Parapeito", HP_BASE + 10, (190, 75, 55), "Orc", 65, 2),
            _spec_inimigo("Bruto da Mureta", HP_BASE + 25, (145, 70, 110), "Aberração Hemática", 75, 3),
            _spec_inimigo("Sombra das Ameias", HP_BASE + 20, (125, 75, 165), "Blood Monster_A", 75, 2),
            _spec_inimigo("Carrasco Superior", HP_BASE + 30, (210, 55, 65), "Demon Carmesim", 80, 2),
        ]
        candidatos = [
            (p_b1.centerx, p_b1.top, p_b1),
            (p_c1.centerx, p_c1.top, p_c1),
            (p_b2.centerx, p_b2.top, p_b2),
            (p_a2.centerx, p_a2.top, p_a2),
        ]
        inimigos_spec = self._montar_inimigos(specs, candidatos, spawn_x)
        boss = _boss_spec("BOSS: ENTE DA ÁRVORE TORTA", CONFIG["boss_sala2_hp"], (215, 130, 30), 3, "Boss_Ente", x=gate_x + 175, y=chao_y - 88)

        props = {
            "tochas_parede": [
                (230, chao_y - 102, "quente"),
                (660, y_n2 - 64, "quente"),
                (900, y_n3 - 64, "quente"),
                (1425, y_n3 - 64, "quente"),
                (gate_x - 38, chao_y - 130, "quente"),
            ],
            "mastros": [
                (160, chao_y, (30, 64, 175), (253, 230, 138)),
                (p_c1.centerx - 55, p_c1.top, (153, 27, 27), (253, 230, 138)),
                (p_c2.centerx + 55, p_c2.top, (153, 27, 27), (245, 158, 11)),
            ],
        }

        return {
            "nome": "Ameias Superiores",
            "bioma": "ameias",
            "tipologia": "BIOMA1_VERTICAL",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": True,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": [],
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": alavancas,
            "chaves": chaves,
            "baus": baus,
            "armadilhas": [
                (pygame.Rect(690, chao_y - 18, 120, 18), "espinhos"),
                (pygame.Rect(1180, chao_y - 18, 115, 18), "veneno"),
            ],
            "spawn_heroi": spawn_heroi,
            "portal_saida": (larg_m - 175, chao_y - 180),
            "inimigos_spec": inimigos_spec,
            "boss": boss,
            "objetivo_tipo": "chave",
            "props": props,
            "semente": 202,
            "visual": {
                "mid": False, "grama": 2, "tint": bio["tint"], "chao": "pedra",
                "plataforma": "pedra", "vagalumes": bio["vagalumes"], "ceu_aberto": True,
                "fundo_arquivo": "Background_1.png",
                "decor": [("arbusto", 540, 0.55, 1.0), ("coluna", 1620, 1.0, 1.0)],
            },
            "sub_regioes": [(0, 620, "Patamar das Torres"), (620, alt_m, "Ameias Inferiores")],
        }

    # =========================================================================
    # BIOMA 2: GALERIAS DAS TORRES DE VIGIA (Salas 3 e 4 - Background_2.png)
    # =========================================================================
    def _construir_sala_3(self, rng):
        """Sala 3 (Galeria da Torre): Background_2.png em paralaxe, chão rebaixado em degraus, portão assentado no solo."""
        bio = BIOMAS_TEMATICOS["torres"]
        larg_m, alt_m = 2480, 1180
        chao_y = 1100
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)

        # Terraço oeste elevado -> descida escalonada -> pátio rebaixado -> pátio leste com portão assentado
        y_oeste = 840
        y_deg1 = 925
        y_deg2 = 1010
        y_leste = 916
        gate_x = 1800

        paredes = [
            # Terraço Oeste de entrada
            pygame.Rect(0, y_oeste, 520, chao_y - y_oeste),
            # Degraus largos descendo para o pátio central rebaixado
            pygame.Rect(520, y_deg1, 210, chao_y - y_deg1),
            pygame.Rect(730, y_deg2, 210, chao_y - y_deg2),
            # Degrau de subida leste até o Pátio do Portão (degraus <= 94 px para subida e retorno limpos)
            pygame.Rect(1420, y_deg2, 160, chao_y - y_deg2),
            pygame.Rect(1580, y_leste, larg_m - 1580, chao_y - y_leste),
            # Muralha sólida acima do portão (o portão assenta exatamente em y_leste!)
            pygame.Rect(gate_x - 10, 0, 58, y_leste - 180),
        ]

        plataformas, suportes = [], []

        def _p(x, y, w, sup="coluna_dupla"):
            r = pygame.Rect(int(x), int(y), int(w), 18)
            plataformas.append(r)
            self._registrar_suporte(suportes, r, sup, paredes, chao)
            return r

        # Galerias superiores da torre sem sobreposição baixa na cabeça (headroom livre >= 120 px)
        p_t1 = _p(970, y_deg2 - 94, 195, "coluna_dupla")
        p_t2 = _p(1255, y_leste - 94, 195, "coluna_dupla")
        p_alav = _p(1005, y_leste - 184, 210, "corrente")

        spawn_x = rng.randint(86, 122)
        spawn_heroi = (spawn_x, y_oeste - 56)

        # REGRA CRÍTICA: portão assentado perfeitamente no solo do pátio leste (rect.bottom == y_leste)
        portoes = [{
            "id": "gate_sala3",
            "rect": pygame.Rect(gate_x, y_leste - 180, 40, 180),
            "aberto": False,
            "tipo": "grade_ferro",
            "nome": "Portão da Galeria da Torre",
        }]
        alavancas = [{
            "id": "alav_s3",
            "x": p_alav.centerx,
            "y": p_alav.top,
            "alvo": "gate_sala3",
            "acionada": False,
            "texto": "Mecanismo da Torre",
            "msg_destrancado": "Portão da Galeria Erguido nas Roldanas!",
        }]
        chaves = [{
            "id": "chave_s3",
            "x": p_t1.centerx,
            "y": p_t1.top,
            "alvo": "gate_sala3",
            "coletada": False,
            "nome": "Chave do Carcereiro",
        }]
        baus = [{
            "id": "bau_s3",
            "x": p_t2.centerx,
            "y": p_t2.top,
            "aberto": False,
            "tipo": "pocao",
            "quantidade": 1,
            "nome": "Baú dos Degraus",
        }]

        specs = [
            _spec_inimigo("Sentinela de Ferro", HP_BASE + 15, (170, 40, 110), "Blood Monster_A", 80, 2),
            _spec_inimigo("Bruto dos Degraus", HP_BASE + 20, (190, 40, 80), "Orc", 65, 2),
            _spec_inimigo("Carrasco Corrompido", HP_BASE + 30, (180, 60, 90), "Demon Carmesim", 75, 3),
            _spec_inimigo("Algoz da Galeria", HP_BASE + 30, (120, 45, 160), "Esqueleto", 75, 2),
        ]
        candidatos = [
            (620, y_deg1, paredes[1]),
            (1080, chao_y, chao),
            (p_t2.centerx, p_t2.top, p_t2),
            (1660, y_leste, paredes[4]),
        ]
        inimigos_spec = self._montar_inimigos(specs, candidatos, spawn_x)
        boss = _boss_spec("BOSS: CARCEREIRO DOS PORTÕES", CONFIG["boss_sala3_hp"], (220, 35, 95), 4, "Boss_Carcereiro", x=max(gate_x + 185, larg_m - 420), y=y_leste - 88)

        props = {
            "tochas_parede": [
                (280, y_oeste - 96, "quente"),
                (625, y_deg1 - 92, "quente"),
                (1180, chao_y - 96, "quente"),
                (1720, y_leste - 115, "quente"),
                (gate_x + 110, y_leste - 115, "quente"),
            ],
            "torres_fundo": [(340, y_oeste), (1120, chao_y), (1880, y_leste)],
        }

        return {
            "nome": "Galeria da Torre",
            "bioma": "torres",
            "tipologia": "BIOMA2_DEGRAUS",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": True,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": [],
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": alavancas,
            "chaves": chaves,
            "baus": baus,
            "armadilhas": [(pygame.Rect(1140, chao_y - 18, 130, 18), "espinhos")],
            "spawn_heroi": spawn_heroi,
            "portal_saida": (larg_m - 175, y_leste - 180),
            "inimigos_spec": inimigos_spec,
            "boss": boss,
            "objetivo_tipo": "alavanca",
            "props": props,
            "semente": 303,
            "visual": {
                "mid": True, "grama": 1, "tint": bio["tint"], "chao": "ferro",
                "plataforma": "pedra", "vagalumes": bio["vagalumes"], "ceu_aberto": True,
                "fundo_arquivo": "Background_2.png",
                "decor": [("cerca", 410, 1.1, 1.0), ("torre", 1920, 0.85, 1.0)],
            },
            "sub_regioes": [(0, y_leste + 40, "Galerias das Torres"), (y_leste + 40, alt_m, "Pátio Rebaixado")],
        }

    def _construir_sala_4(self, rng):
        """Sala 4 (Torre de Vigia Suspensa): Background_2.png, plataformas suspensas + escadaria de retorno do fosso."""
        bio = BIOMAS_TEMATICOS["torres"]
        larg_m, alt_m, chao_y = 2480, 1130, 1050
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)
        y_varanda = 780
        gate_x = 1860

        paredes = [
            # Baluarte de embarque Oeste e Pátio Leste conectados pelas passarelas suspensas
            pygame.Rect(0, y_varanda, 420, chao_y - y_varanda),
            pygame.Rect(1690, y_varanda, larg_m - 1690, chao_y - y_varanda),
            # Muralha direita com portão assentado em y_varanda
            pygame.Rect(gate_x - 10, 0, 58, y_varanda - 180),
        ]

        plataformas, suportes = [], []

        def _p(x, y, w, sup="corrente"):
            r = pygame.Rect(int(x), int(y), int(w), 20)
            plataformas.append(r)
            self._registrar_suporte(suportes, r, sup, paredes, chao)
            return r

        # Sequência suspensa por correntes verticais sobre o fosso
        ps1 = _p(485, y_varanda - 68, 195, "corrente")
        ps2 = _p(755, y_varanda - 148, 210, "corrente")
        ps3 = _p(1035, y_varanda - 76, 225, "corrente")
        ps4 = _p(1325, y_varanda - 156, 205, "corrente")

        # Rota garantida de retorno ao topo caso o jogador caia ou desça ao fosso (degraus <= 90 px, sem sobreposição)
        ps_bot_w = _p(750, chao_y - 90, 200, "escadaria")      # 960
        ps_ret_w = _p(465, y_varanda + 88, 215, "coluna_dupla") # 868 -> sobe p/ paredes[0] (780) em 88 px!
        ps_bot_e = _p(1210, chao_y - 90, 200, "escadaria")     # 960
        ps_ret_e = _p(1455, y_varanda + 88, 195, "coluna_dupla") # 868 -> sobe p/ paredes[1] (780) em 88 px!
        ps_baixa = ps_ret_w

        spawn_x = rng.randint(86, 122)
        spawn_heroi = (spawn_x, y_varanda - 56)

        portoes = [{
            "id": "gate_sala4",
            "rect": pygame.Rect(gate_x, y_varanda - 180, 38, 180),
            "aberto": False,
            "tipo": "grade_ferro",
            "nome": "Portão da Torre Suspensa",
        }]
        alavancas = [{
            "id": "alav_s4",
            "x": ps4.centerx,
            "y": ps4.top,
            "alvo": "gate_sala4",
            "acionada": False,
            "texto": "Roldana das Correntes",
            "msg_destrancado": "Portão da Torre Suspensa Liberado!",
        }]
        chaves = [{
            "id": "chave_s4",
            "x": ps2.centerx,
            "y": ps2.top,
            "alvo": "gate_sala4",
            "coletada": False,
            "nome": "Chave de Vigia",
        }]
        baus = [{
            "id": "bau_s4",
            "x": ps_bot_w.centerx,
            "y": ps_bot_w.top,
            "aberto": False,
            "tipo": "pocao",
            "quantidade": 1,
            "nome": "Baú do Fosso",
        }]

        specs = [
            _spec_inimigo("Acólito da Vigia", 165, (135, 55, 210), "Necromante", 65, 2),
            _spec_inimigo("Mago das Torres", 190, (175, 65, 205), "Necromante", 70, 3),
            _spec_inimigo("Guardião da Corrente", 215, (155, 55, 230), "Blood Monster_A", 75, 3),
            _spec_inimigo("Sentinela do Fosso", 205, (170, 60, 230), "Esqueleto", 85, 3),
        ]
        candidatos = [
            (ps2.centerx, ps2.top, ps2),
            (ps3.centerx, ps3.top, ps3),
            (ps4.centerx, ps4.top, ps4),
            (ps_bot_e.centerx, ps_bot_e.top, ps_bot_e),
        ]
        inimigos_spec = self._montar_inimigos(specs, candidatos, spawn_x)
        boss = _boss_spec("CHEFE: ZELADOR DO MAUSOLÉU", 520, (170, 45, 240), 4, "Boss_Mausoleu", x=max(gate_x + 180, larg_m - 420), y=y_varanda - 88)

        props = {
            "tochas_parede": [
                (220, y_varanda - 95, "quente"),
                (1775, y_varanda - 115, "quente"),
                (gate_x + 95, y_varanda - 115, "quente"),
            ],
            "torres_fundo": [(260, y_varanda), (1050, chao_y), (2060, y_varanda)],
        }

        return {
            "nome": "Torre de Vigia Suspensa",
            "bioma": "torres",
            "tipologia": "BIOMA2_SUSPENSA",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": True,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": [],
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": alavancas,
            "chaves": chaves,
            "baus": baus,
            "armadilhas": [
                (pygame.Rect(520, chao_y - 18, 120, 18), "espinhos"),
                (pygame.Rect(1020, chao_y - 18, 120, 18), "espinhos"),
            ],
            "spawn_heroi": spawn_heroi,
            "portal_saida": (larg_m - 175, y_varanda - 180),
            "inimigos_spec": inimigos_spec,
            "boss": boss,
            "objetivo_tipo": "alavanca",
            "props": props,
            "semente": 404,
            "visual": {
                "mid": True, "grama": 1, "tint": bio["tint"], "chao": "ferro",
                "plataforma": "pedra", "vagalumes": bio["vagalumes"], "ceu_aberto": True,
                "fundo_arquivo": "Background_2.png",
                "decor": [("coluna", 330, 1.0, 1.0), ("estatua", 1960, 0.9, 1.0)],
            },
            "sub_regioes": [(0, y_varanda + 40, "Passarelas Suspensas"), (y_varanda + 40, alt_m, "Fosso das Correntes")],
        }

    # =========================================================================
    # BIOMA 3: CRIPTA E CATACUMBAS SUBTERRÂNEAS (Salas 5 e 6 - Interior Fechado)
    # =========================================================================
    def _construir_sala_5(self, rng):
        """Sala 5 (Catacumbas): Teto e paredes escuras bloqueando céu, grades de ferro ao fundo, arcos e lápides."""
        bio = BIOMAS_TEMATICOS["catacumbas"]
        larg_m, alt_m = 2520, 1100
        chao_y = 1020
        y_mid = 740
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)
        gate_x = 1860

        paredes = [
            # Teto maciço contínuo bloqueando completamente o céu exterior
            pygame.Rect(0, 0, larg_m, 108),
            # Parede externa esquerda acima da entrada subterrânea
            pygame.Rect(0, 108, 42, y_mid - 108 - 140),
            # Piso superior da catacumba com poço oeste (860..1140) e poço leste amplo (1430..1725)
            pygame.Rect(0, y_mid, 860, 28),
            pygame.Rect(1140, y_mid, 290, 28),
            pygame.Rect(1725, y_mid, larg_m - 1725, 28),
            # Pilastra sólida do portão da catacumba do teto até o chão
            pygame.Rect(gate_x - 10, 108, 58, max(40, y_mid - 180 - 108)),
            pygame.Rect(gate_x - 10, y_mid + 28, 58, chao_y - (y_mid + 28)),
        ]

        plataformas, suportes = [], []

        def _p(x, y, w, sup="coluna_dupla"):
            r = pygame.Rect(int(x), int(y), int(w), 18)
            plataformas.append(r)
            self._registrar_suporte(suportes, r, sup, paredes, chao)
            return r

        # Galerias superiores + subida limpa nos dois poços (degraus <= 94 px e zero bloqueio de cabeça)
        p_sup1 = _p(420, y_mid - 96, 195, "coluna_dupla")
        p_sup2 = _p(710, y_mid - 190, 210, "coluna_dupla")
        p_sub_w_low = _p(875, chao_y - 92, 125, "escadaria")   # 928
        p_sub1 = _p(1010, y_mid + 94, 125, "coluna_dupla")     # 834 -> sobe p/ 740 em 94 px!
        p_sub2 = _p(1170, chao_y - 92, 220, "coluna_dupla")    # 928
        p_sub_up1 = _p(1445, chao_y - 92, 120, "escadaria")    # 928
        p_sub3 = _p(1580, y_mid + 94, 130, "coluna_dupla")     # 834 -> sobe p/ paredes[4] (740) em 94 px!

        spawn_x = rng.randint(86, 122)
        spawn_heroi = (spawn_x, y_mid - 56)

        portoes = [{
            "id": "gate_sala5",
            "rect": pygame.Rect(gate_x, y_mid - 180, 38, 180),
            "aberto": False,
            "tipo": "cripta",
            "nome": "Grade da Catacumba Interior",
        }]
        alavancas = [{
            "id": "alav_s5",
            "x": p_sub3.centerx,
            "y": p_sub3.top,
            "alvo": "gate_sala5",
            "acionada": False,
            "texto": "Alavanca do Ossuário",
            "msg_destrancado": "Grade da Catacumba Destrancada!",
        }]
        chaves = [{
            "id": "chave_s5",
            "x": p_sup2.centerx,
            "y": p_sup2.top,
            "alvo": "gate_sala5",
            "coletada": False,
            "nome": "Chave de Ferro Frio",
        }]
        baus = [{
            "id": "bau_s5",
            "x": p_sub2.centerx,
            "y": p_sub2.top,
            "aberto": False,
            "tipo": "eter",
            "quantidade": 2,
            "nome": "Urna Funerária",
        }]

        specs = [
            _spec_inimigo("Esqueleto Reanimado", 180, (155, 65, 195), "Esqueleto", 80, 2),
            _spec_inimigo("Acólito das Cinzas", 190, (130, 50, 210), "Necromante", 65, 3),
            _spec_inimigo("Lich Menor", 220, (165, 55, 235), "Demon_A", 70, 3),
            _spec_inimigo("Golem da Cripta", 240, (110, 100, 125), "Orc", 85, 3),
        ]
        candidatos = [
            (p_sup1.centerx, p_sup1.top, p_sup1),
            (600, chao_y, chao),
            (p_sub2.centerx, p_sub2.top, p_sub2),
            (1775, y_mid, paredes[4]),
        ]
        inimigos_spec = self._montar_inimigos(specs, candidatos, spawn_x)
        boss = _boss_spec("CHEFE: SENTINELA DE PEDRA", 620, (190, 55, 255), 4, "Boss_Sentinela", x=max(gate_x + 175, larg_m - 420), y=y_mid - 88)

        props = {
            "grades_fundo": [(x_g, y_mid - 140, 120, 140) for x_g in range(180, larg_m - 240, 420)],
            "arcos_cripta": [(x_a, 108, 220) for x_a in range(120, larg_m - 220, 340)],
            "lapides": [(x_l, y_mid) for x_l in (260, 490, 740, 1340, 1620)] + [(x_l, chao_y) for x_l in (440, 820, 1380)],
            "tochas_parede": [
                (210, y_mid - 108, "fria_azul"),
                (620, y_mid - 108, "fria_roxa"),
                (960, chao_y - 108, "fria_azul"),
                (1520, y_mid - 108, "fria_roxa"),
            ],
        }

        return {
            "nome": "Catacumbas Subterrâneas",
            "bioma": "catacumbas",
            "tipologia": "BIOMA3_CATACUMBAS",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": False,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": [],
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": alavancas,
            "chaves": chaves,
            "baus": baus,
            "armadilhas": [(pygame.Rect(730, chao_y - 18, 120, 18), "ossos")],
            "spawn_heroi": spawn_heroi,
            "portal_saida": (larg_m - 175, y_mid - 180),
            "inimigos_spec": inimigos_spec,
            "boss": boss,
            "objetivo_tipo": "alavanca",
            "props": props,
            "semente": 505,
            "visual": {
                "mid": False, "grama": 0, "tint": bio["tint"], "chao": "cripta",
                "plataforma": "cripta", "vagalumes": bio["vagalumes"], "ceu_aberto": False,
                "fundo_arquivo": None,
                "decor": [("estatua", 1360, 0.95, 1.0)],
            },
            "sub_regioes": [(0, y_mid + 40, "Galeria das Lápides"), (y_mid + 40, alt_m, "Subsolo da Cripta")],
        }

    def _construir_sala_6(self, rng):
        """Sala 6 (Cripta dos Ossos): Interior escuro, poços com espinhos, tochas frias azuis/roxas, plataformas móveis."""
        bio = BIOMAS_TEMATICOS["catacumbas"]
        larg_m, alt_m = 2560, 1120
        chao_y = 1040
        y_cripta = 800
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)
        gate_x = 1890

        paredes = [
            # Teto maciço contínuo sem céu aberto
            pygame.Rect(0, 0, larg_m, 108),
            # Entrada Oeste e Santuário Leste separados pelo salão dos poços de ossos
            pygame.Rect(0, y_cripta, 460, chao_y - y_cripta),
            pygame.Rect(1660, y_cripta, larg_m - 1660, chao_y - y_cripta),
            # Pilastras de alvenaria sustentando os vãos do abismo entre poços estreitos
            pygame.Rect(780, y_cripta + 96, 140, chao_y - (y_cripta + 96)),
            pygame.Rect(1220, y_cripta + 72, 140, chao_y - (y_cripta + 72)),
            # Muralha sólida do portão
            pygame.Rect(gate_x - 10, 108, 58, max(40, y_cripta - 180 - 108)),
        ]

        plataformas, suportes = [], []

        def _p(x, y, w, sup="coluna_dupla"):
            r = pygame.Rect(int(x), int(y), int(w), 18)
            plataformas.append(r)
            self._registrar_suporte(suportes, r, sup, paredes, chao)
            return r

        # Plataformas fixas nos pilares + degraus de saída em todos os 3 poços + 3 plataformas móveis
        p_alav = _p(1210, y_cripta - 94, 170, "coluna_dupla")   # 706
        p_resc1 = _p(580, chao_y - 88, 145, "escadaria")       # 952 (sobe p/ Pilar 1 y=896 em 56 px, vão 55 px)
        p_resc2 = _p(1005, chao_y - 88, 145, "escadaria")      # 952 (sobe p/ Pilar 1 896 ou Pilar 2 872 em <=80 px!)
        p_resc3 = _p(1395, chao_y - 86, 115, "escadaria")      # 954
        p_resc3b = _p(1535, y_cripta + 92, 110, "coluna_dupla") # 892 -> sobe p/ paredes[2] (800) em 92 px!

        pm1 = pygame.Rect(510, y_cripta, 145, 20)
        pm2 = pygame.Rect(980, y_cripta - 12, 145, 20)
        pm3 = pygame.Rect(1425, y_cripta - 20, 145, 20)

        plataformas.extend([pm1, pm2, pm3])
        for pm in (pm1, pm2, pm3):
            self._registrar_suporte(suportes, pm, "movel", paredes, chao)

        plataformas_moveis = [
            {"rect": pm1, "base_x": float(pm1.x), "base_y": float(pm1.y), "amp_x": 95.0, "amp_y": 0.0, "vel": 1.35, "fase": 0.0, "dx": 0.0, "dy": 0.0},
            {"rect": pm2, "base_x": float(pm2.x), "base_y": float(pm2.y), "amp_x": 0.0, "amp_y": 42.0, "vel": 1.65, "fase": 1.2, "dx": 0.0, "dy": 0.0},
            {"rect": pm3, "base_x": float(pm3.x), "base_y": float(pm3.y), "amp_x": 85.0, "amp_y": 0.0, "vel": 1.45, "fase": 2.4, "dx": 0.0, "dy": 0.0},
        ]

        spawn_x = rng.randint(86, 122)
        spawn_heroi = (spawn_x, y_cripta - 56)

        portoes = [{
            "id": "gate_sala6",
            "rect": pygame.Rect(gate_x, y_cripta - 180, 40, 180),
            "aberto": False,
            "tipo": "sangue",
            "nome": "Portão da Cripta dos Ossos",
        }]
        alavancas = [{
            "id": "alav_s6",
            "x": p_alav.centerx,
            "y": p_alav.top,
            "alvo": "gate_sala6",
            "acionada": False,
            "texto": "Selo dos Ossos",
            "msg_destrancado": "Portão da Cripta dos Ossos Liberado!",
        }]
        chaves = [{
            "id": "chave_s6",
            "x": 850,
            "y": y_cripta + 96,
            "alvo": "gate_sala6",
            "coletada": False,
            "nome": "Chave de Marfim",
        }]
        baus = [{
            "id": "bau_s6",
            "x": 1290,
            "y": y_cripta + 72,
            "aberto": False,
            "tipo": "pocao",
            "quantidade": 2,
            "nome": "Relicário dos Ossos",
        }]

        specs = [
            _spec_inimigo("Cavaleiro Reanimado", 215, (130, 50, 210), "Necromante", 60, 2),
            _spec_inimigo("Arauto dos Ossos", 240, (185, 70, 240), "Demon_A", 55, 3),
            _spec_inimigo("Campeão da Cripta", 260, (110, 50, 200), "Blood Monster_A", 55, 3),
            _spec_inimigo("Pretor Sanguinário", 295, (190, 25, 55), "Blood Monster_A", 80, 3),
        ]
        candidatos = [
            (845, y_cripta + 96, paredes[3]),
            (1290, y_cripta + 72, paredes[4]),
            (p_alav.centerx, p_alav.top, p_alav),
            (1750, y_cripta, paredes[2]),
        ]
        inimigos_spec = self._montar_inimigos(specs, candidatos, spawn_x)
        boss = _boss_spec("CHEFE FINAL: REI DA LUA SANGRENTA", 780, (205, 65, 255), 5, "Boss_ReiSangrento", x=max(gate_x + 175, larg_m - 420), y=y_cripta - 88)

        # Poços estreitos com espinhos centralizados (bordas livres para escapar) e tochas frias
        armadilhas = [
            (pygame.Rect(485, chao_y - 20, 80, 20), "ossos"),
            (pygame.Rect(930, chao_y - 20, 65, 20), "espinhos"),
            (pygame.Rect(1530, chao_y - 20, 110, 20), "ossos"),
        ]
        props = {
            "grades_fundo": [(x_g, y_cripta - 150, 110, 150) for x_g in (200, 820, 1260, 1740)],
            "arcos_cripta": [(x_a, 108, 240) for x_a in range(140, larg_m - 220, 380)],
            "lapides": [(240, y_cripta), (850, y_cripta + 96), (1735, y_cripta)],
            "tochas_parede": [
                (190, y_cripta - 110, "fria_azul"),
                (850, y_cripta - 45, "fria_roxa"),
                (1290, y_cripta - 55, "fria_azul"),
                (1775, y_cripta - 110, "fria_roxa"),
                (gate_x + 95, y_cripta - 110, "fria_azul"),
            ],
        }

        return {
            "nome": "Cripta dos Ossos",
            "bioma": "catacumbas",
            "tipologia": "BIOMA3_CRIPTAS_MOVEIS",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": False,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": plataformas_moveis,
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": alavancas,
            "chaves": chaves,
            "baus": baus,
            "armadilhas": armadilhas,
            "spawn_heroi": spawn_heroi,
            "portal_saida": (larg_m - 175, y_cripta - 180),
            "inimigos_spec": inimigos_spec,
            "boss": boss,
            "objetivo_tipo": "alavanca",
            "props": props,
            "semente": 606,
            "visual": {
                "mid": False, "grama": 0, "tint": bio["tint"], "chao": "sangue",
                "plataforma": "cripta", "vagalumes": (140, 165, 255), "ceu_aberto": False,
                "fundo_arquivo": None,
                "decor": [("coluna", 320, 1.0, 1.0)],
            },
            "sub_regioes": [(0, alt_m, "Cripta dos Ossos")],
        }

    # =========================================================================
    # BIOMA 4: ARENA DO GUARDIÃO / BOSS ROOM (Sala 7 - 960 px plana)
    # =========================================================================
    def _construir_sala_7(self, rng):
        """Sala 7 (Santuário do Guardião): Arena plana e ampla de 960 px, pilares com gárgulas, portão titânico rúnico."""
        bio = BIOMAS_TEMATICOS["santuario"]
        larg_m, alt_m, chao_y = 960, 540, 468
        chao = pygame.Rect(0, chao_y, larg_m, alt_m - chao_y)
        gate_x = 815

        paredes = [
            # Teto monumental de cantaria da Arena do Guardião
            pygame.Rect(0, 0, larg_m, 44),
            # Muralha sólida direita ancorando o portão titânico com fechadura rúnica
            pygame.Rect(gate_x - 10, 44, 64, chao_y - 208 - 44),
        ]

        plataformas, suportes = [], []
        spawn_x = 92
        spawn_heroi = (spawn_x, chao_y - 56)

        portoes = [{
            "id": "gate_sala7",
            "rect": pygame.Rect(gate_x, chao_y - 208, 44, 208),
            "aberto": False,
            "tipo": "titanico_runico",
            "nome": "Portão Titânico com Fechadura Rúnica",
        }]
        runas = [(235, chao_y), (390, chao_y), (545, chao_y)]

        boss = _boss_spec(
            "CHEFE FINAL: BIBLIOTECÁRIO DO VAZIO",
            950, (220, 90, 255), 5, "Boss_Bibliotecario",
            x=700, y=chao_y - 88, patrulha=45
        )

        props = {
            "pilares_gargulas": [
                (148, chao_y, False),
                (736, chao_y, True),
            ],
            "grades_fundo": [(310, chao_y - 160, 110, 160), (520, chao_y - 160, 110, 160)],
            "arcos_cripta": [(95, 44, 250), (345, 44, 250), (595, 44, 250)],
            "tochas_parede": [
                (198, chao_y - 118, "fria_azul"),
                (470, chao_y - 140, "fria_roxa"),
                (695, chao_y - 118, "fria_azul"),
                (gate_x - 30, chao_y - 135, "fria_roxa"),
            ],
        }

        return {
            "nome": "Santuário do Guardião",
            "bioma": "santuario",
            "tipologia": "BIOMA4_ARENA",
            "nome_tipologia": bio["titulo"],
            "ceu_aberto": False,
            "cor_fundo": bio["cor_fundo"],
            "largura": larg_m,
            "altura": alt_m,
            "chao": chao,
            "paredes": paredes,
            "plataformas": plataformas,
            "plataformas_moveis": [],
            "suportes": suportes,
            "portoes": portoes,
            "alavancas": [],
            "chaves": [],
            "baus": [],
            "armadilhas": [],
            "spawn_heroi": spawn_heroi,
            "portal_saida": (918, chao_y - 180),
            "inimigos_spec": [],
            "boss": boss,
            "runas_pos": runas,
            "objetivo_tipo": "runas_vazio",
            "props": props,
            "semente": 707,
            "visual": {
                "mid": True, "grama": 0, "tint": bio["tint"], "chao": "arcano",
                "plataforma": "catedral", "vagalumes": bio["vagalumes"], "ceu_aberto": False,
                "fundo_arquivo": "Background_2.png",
                "decor": [],
            },
            "sub_regioes": [(0, alt_m, "Arena do Guardião")],
        }

    def atualizar_sala(self, mapa, dt, tempo):
        """Atualiza plataformas móveis da sala atual calculando delta (dx, dy) por frame."""
        if not mapa:
            return
        for pm in mapa.get("plataformas_moveis", []):
            rect = pm["rect"]
            ant_x, ant_y = rect.x, rect.y
            nx = int(round(pm["base_x"] + math.sin(tempo * pm["vel"] + pm["fase"]) * pm["amp_x"]))
            ny = int(round(pm["base_y"] + math.sin(tempo * pm["vel"] + pm["fase"]) * pm["amp_y"]))
            rect.x = nx
            rect.y = ny
            pm["dx"] = float(nx - ant_x)
            pm["dy"] = float(ny - ant_y)
