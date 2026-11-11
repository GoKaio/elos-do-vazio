# -*- coding: utf-8 -*-
"""Arena de Combate 2.5D volumétrica com 7 biomas temáticos, texturas procedurais, halos SRCALPHA e lajes 1/Z."""

import math
import random
import pygame
from procedural_gen import projetar_ponto_conico, gerar_faixas_1_sobre_z


def _clamp_cor(c):
    return (max(0, min(255, int(c[0]))), max(0, min(255, int(c[1]))), max(0, min(255, int(c[2]))))


def _lerp_cor(c1, c2, t):
    t = max(0.0, min(1.0, float(t)))
    return (
        max(0, min(255, int(c1[0] + (c2[0] - c1[0]) * t))),
        max(0, min(255, int(c1[1] + (c2[1] - c1[1]) * t))),
        max(0, min(255, int(c1[2] + (c2[2] - c1[2]) * t))),
    )


def _lerp_multi(paleta, t):
    if not paleta:
        return (24, 28, 42)
    if len(paleta) == 1:
        return paleta[0]
    t = max(0.0, min(1.0, float(t)))
    pos = t * (len(paleta) - 1)
    idx = min(len(paleta) - 2, int(pos))
    return _lerp_cor(paleta[idx], paleta[idx + 1], pos - idx)


PALETA_FOGO = {
    "LARANJA":     {"ponta": (220, 38, 38),  "meio": (249, 115, 22), "nucleo": (254, 240, 138), "halo_ext": (249, 115, 22), "halo_med": (251, 146, 60)},
    "VERMELHO":    {"ponta": (185, 28, 28),  "meio": (239, 68, 68),  "nucleo": (254, 226, 226), "halo_ext": (220, 38, 38),  "halo_med": (248, 113, 113)},
    "VIOLETA":     {"ponta": (126, 34, 206), "meio": (168, 85, 247), "nucleo": (243, 232, 255), "halo_ext": (147, 51, 234), "halo_med": (192, 132, 252)},
    "AZUL_ETER":   {"ponta": (220, 38, 38),  "meio": (249, 115, 22), "nucleo": (254, 240, 138), "halo_ext": (249, 115, 22), "halo_med": (251, 146, 60), "feixe": (56, 189, 248)},
    "CIANO_VAZIO": {"ponta": (14, 165, 233), "meio": (56, 189, 248), "nucleo": (224, 242, 254), "halo_ext": (14, 165, 233), "halo_med": (56, 189, 248)},
}


# Mantém compatibilidade com importadores antigos de PALETAS_ARENA
PALETAS_ARENA = {
    0: {"ceu": (10, 14, 26), "muralha": (30, 41, 59), "piso_a": (34, 42, 58), "piso_b": (56, 68, 88), "eter": (234, 88, 12)},
    1: {"ceu": (18, 8, 14),  "muralha": (32, 16, 24), "piso_a": (18, 15, 24), "piso_b": (36, 28, 42), "eter": (220, 38, 38)},
    2: {"ceu": (14, 8, 12),  "muralha": (28, 18, 22), "piso_a": (24, 20, 26), "piso_b": (44, 34, 40), "eter": (225, 29, 72)},
    3: {"ceu": (8, 12, 28),  "muralha": (24, 26, 48), "piso_a": (25, 26, 46), "piso_b": (48, 46, 78), "eter": (168, 85, 247)},
    4: {"ceu": (10, 12, 22), "muralha": (34, 36, 50), "piso_a": (34, 42, 46), "piso_b": (58, 68, 72), "eter": (56, 189, 248)},
    5: {"ceu": (20, 8, 12),  "muralha": (38, 18, 22), "piso_a": (26, 16, 20), "piso_b": (48, 28, 32), "eter": (245, 158, 11)},
    6: {"ceu": (5, 7, 18),   "muralha": (14, 24, 52), "piso_a": (12, 18, 36), "piso_b": (26, 42, 74), "eter": (56, 189, 248)},
}


class ConfigBiomaCombate:
    """Configuração modular de paleta, iluminação e elementos 2.5D por bioma de sala."""

    def __init__(
        self,
        nome,
        cor_ceu,
        cor_horizonte,
        paleta_piso,
        tipo_fogo,
        particula_cor,
        tema_id="ameias",
        subtitulo="",
        cor_junta=(11, 14, 23),
        cor_luz_laje=(51, 65, 85),
        cor_sombra_laje=(15, 23, 42),
        cor_muralha=(30, 41, 59),
        cor_destaque=(245, 158, 11),
    ):
        self.nome = nome
        self.cor_ceu = cor_ceu
        self.cor_horizonte = cor_horizonte
        self.paleta_piso = list(paleta_piso)
        self.tipo_fogo = tipo_fogo
        self.particula_cor = particula_cor
        self.tema_id = tema_id
        self.subtitulo = subtitulo
        self.cor_junta = cor_junta
        self.cor_luz_laje = cor_luz_laje
        self.cor_sombra_laje = cor_sombra_laje
        self.cor_muralha = cor_muralha
        self.cor_destaque = cor_destaque


class BiomaCombateFactory:
    """Fábrica dos 7 biomas temáticos de combate 2.5D mapeados às salas 1 a 7."""

    _REGISTRY = {
        0: ConfigBiomaCombate(
            nome="Pátio das Ameias da Muralha",
            subtitulo="Arena do Capitão Orc",
            cor_ceu=(9, 13, 25),
            cor_horizonte=(28, 38, 62),
            paleta_piso=[(34, 42, 56), (44, 54, 70), (58, 70, 88)],
            tipo_fogo="LARANJA",
            particula_cor=(251, 146, 60),
            tema_id="ameias",
            cor_junta=(11, 14, 23),
            cor_luz_laje=(51, 65, 85),
            cor_sombra_laje=(15, 23, 42),
            cor_muralha=(30, 41, 59),
            cor_destaque=(245, 158, 11),
        ),
        1: ConfigBiomaCombate(
            nome="Pátio da Cripta Sombria",
            subtitulo="Arena do Lorde Demônio Vermillion",
            cor_ceu=(16, 7, 13),
            cor_horizonte=(58, 15, 25),
            paleta_piso=[(18, 16, 24), (26, 22, 34), (36, 30, 44)],
            tipo_fogo="VERMELHO",
            particula_cor=(248, 113, 113),
            tema_id="cripta_sombria",
            cor_junta=(11, 10, 16),
            cor_luz_laje=(68, 46, 58),
            cor_sombra_laje=(15, 12, 20),
            cor_muralha=(32, 18, 28),
            cor_destaque=(239, 68, 68),
        ),
        2: ConfigBiomaCombate(
            nome="Fóvea dos Lamentos",
            subtitulo="Arena da Amálgama Carmesim",
            cor_ceu=(12, 7, 10),
            cor_horizonte=(42, 13, 19),
            paleta_piso=[(22, 19, 25), (32, 26, 34), (44, 34, 42)],
            tipo_fogo="VERMELHO",
            particula_cor=(244, 63, 94),
            tema_id="fovea_lamentos",
            cor_junta=(11, 10, 15),
            cor_luz_laje=(66, 44, 54),
            cor_sombra_laje=(15, 12, 18),
            cor_muralha=(30, 20, 26),
            cor_destaque=(225, 29, 72),
        ),
        3: ConfigBiomaCombate(
            nome="Torre Quebrada do Juramento",
            subtitulo="Arena do Cavaleiro Corrompido",
            cor_ceu=(7, 11, 26),
            cor_horizonte=(22, 34, 68),
            paleta_piso=[(25, 26, 44), (36, 35, 60), (48, 46, 78)],
            tipo_fogo="VIOLETA",
            particula_cor=(192, 132, 252),
            tema_id="torre_quebrada",
            cor_junta=(11, 12, 24),
            cor_luz_laje=(66, 62, 104),
            cor_sombra_laje=(15, 16, 34),
            cor_muralha=(28, 32, 54),
            cor_destaque=(168, 85, 247),
        ),
        4: ConfigBiomaCombate(
            nome="Catedrais Subterrâneas de Cantaria",
            subtitulo="Arena da Gárgula Patriarca",
            cor_ceu=(9, 12, 22),
            cor_horizonte=(24, 30, 46),
            paleta_piso=[(32, 40, 46), (44, 54, 60), (56, 68, 74)],
            tipo_fogo="AZUL_ETER",
            particula_cor=(245, 188, 92),
            tema_id="catedrais",
            cor_junta=(11, 14, 20),
            cor_luz_laje=(62, 76, 86),
            cor_sombra_laje=(15, 22, 28),
            cor_muralha=(30, 38, 52),
            cor_destaque=(56, 189, 248),
        ),
        5: ConfigBiomaCombate(
            nome="Santuário do Miasma Sangrento",
            subtitulo="Arena do Sacerdote da Chama",
            cor_ceu=(20, 7, 11),
            cor_horizonte=(48, 14, 20),
            paleta_piso=[(28, 16, 22), (38, 22, 28), (50, 28, 34)],
            tipo_fogo="LARANJA",
            particula_cor=(244, 63, 94),
            tema_id="santuario_miasma",
            cor_junta=(12, 10, 14),
            cor_luz_laje=(78, 54, 46),
            cor_sombra_laje=(18, 10, 14),
            cor_muralha=(40, 20, 26),
            cor_destaque=(245, 158, 11),
        ),
        6: ConfigBiomaCombate(
            nome="O Vazio Absoluto",
            subtitulo="Arena do Guardião do Vazio",
            cor_ceu=(4, 6, 16),
            cor_horizonte=(14, 26, 58),
            paleta_piso=[(10, 18, 36), (16, 28, 54), (24, 42, 78)],
            tipo_fogo="CIANO_VAZIO",
            particula_cor=(56, 189, 248),
            tema_id="vazio_absoluto",
            cor_junta=(56, 189, 248),
            cor_luz_laje=(56, 189, 248),
            cor_sombra_laje=(8, 14, 30),
            cor_muralha=(12, 20, 44),
            cor_destaque=(56, 189, 248),
        ),
    }

    @classmethod
    def normalizar_sala(cls, sala_atual):
        try:
            idx = int(sala_atual)
        except (TypeError, ValueError):
            idx = 0
        return max(0, min(6, idx))

    @classmethod
    def criar(cls, sala_atual=0):
        return cls._REGISTRY[cls.normalizar_sala(sala_atual)]

    @classmethod
    def obter_bioma(cls, sala_atual=0):
        return cls.criar(sala_atual)


class CameraCombate25D:
    """Câmera dinâmica 2.5D com interpolação linear (lerp), zoom e tremor."""

    def __init__(self, largura_tela=960, altura_tela=540):
        self.largura = largura_tela
        self.altura = altura_tela
        self.centro_x = largura_tela // 2
        self.horizonte_base_y = int(altura_tela * 0.41)

        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.tilt = 0.0

        self.alvo_x = 0.0
        self.alvo_y = 0.0
        self.alvo_zoom = 1.0
        self.alvo_tilt = 0.0
        self.velocidade_lerp = 6.5

        self.shake_timer = 0.0
        self.shake_intensidade = 0.0

    def focar_visao_geral(self):
        self.alvo_x, self.alvo_y, self.alvo_zoom = 0.0, 0.0, 1.0

    def focar_alvo_unico(self, x_mundo, z_mundo):
        self.alvo_x = x_mundo * 0.42
        self.alvo_y = -15.0
        self.alvo_zoom = 1.18

    def focar_qte_defensivo(self, x_atacante, x_heroi):
        self.alvo_x = (x_atacante + x_heroi) * 0.35
        self.alvo_y = -22.0
        self.alvo_zoom = 1.26

    def aplicar_tremor(self, intensidade=8.0, duracao=0.25):
        self.shake_intensidade = float(intensidade)
        self.shake_timer = float(duracao)

    def tremer(self, duracao=0.25, forca=8.0):
        self.aplicar_tremor(intensidade=float(forca), duracao=duracao)

    def definir_pose(self, x, y, zoom=1.0, tilt=0.0):
        self.alvo_x = float(x)
        self.alvo_y = float(y)
        self.alvo_zoom = float(zoom)
        self.alvo_tilt = float(tilt)

    def transformar_ponto(self, px, py):
        cx, cy = self.centro_x, self.altura // 2
        dx = (px - cx - self.x) * self.zoom
        dy = (py - cy - self.y) * self.zoom
        sx = random.uniform(-self.shake_intensidade, self.shake_intensidade) if self.shake_timer > 0 else 0.0
        sy = random.uniform(-self.shake_intensidade, self.shake_intensidade) if self.shake_timer > 0 else 0.0
        return int(cx + dx + sx), int(cy + dy + sy)

    def update(self, dt):
        self.atualizar(dt)

    def atualizar(self, dt):
        fator = min(1.0, dt * self.velocidade_lerp)
        self.x += (self.alvo_x - self.x) * fator
        self.y += (self.alvo_y - self.y) * fator
        self.zoom += (self.alvo_zoom - self.zoom) * fator
        self.tilt += (self.alvo_tilt - self.tilt) * fator
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)

    def projetar(self, x_mundo, y_mundo, z_mundo, distancia_focal=320.0):
        """Converte (X, Y, Z) -> (X_tela, Y_tela, escala)."""
        horizonte_y = self.horizonte_base_y - self.y * 0.45
        f_efetivo = distancia_focal * self.zoom
        tx, ty, _ = projetar_ponto_conico(
            x_mundo - self.x,
            y_mundo,
            z_mundo,
            self.centro_x,
            horizonte_y,
            distancia_focal=f_efetivo,
        )
        escala_segura = max(0.3, min(4.0, (distancia_focal / max(12.0, z_mundo + distancia_focal)) * self.zoom))

        if self.shake_timer > 0:
            tx += random.uniform(-self.shake_intensidade, self.shake_intensidade)
            ty += random.uniform(-self.shake_intensidade, self.shake_intensidade)

        return int(tx), int(ty), escala_segura


class CenarioCombate25D:
    """Arena gótica 2.5D temática por sala com textura de cantaria, tochas BLEND_ADD e lajes 1/Z."""

    def __init__(self, largura=960, altura=540, sala_idx=0, sala_atual=None):
        self.largura = largura
        self.altura = altura
        self.tempo = 0.0
        self.y_chao = 140.0
        self.z_frente = -115.0
        self.z_fundo = 290.0
        self.largura_mundo = 840.0
        self.pilares_z = [15.0, 115.0, 215.0]
        self._faixas_z = gerar_faixas_1_sobre_z(self.z_frente, self.z_fundo, 12)

        idx_alvo = sala_idx if sala_atual is None else sala_atual
        self.sala_idx = BiomaCombateFactory.normalizar_sala(idx_alvo)
        self.bioma = BiomaCombateFactory.obter_bioma(self.sala_idx)
        self._cache_texturas = {}
        self._construir_bioma_ativo()

    def definir_sala(self, sala_atual):
        """Atualiza automaticamente o bioma da arena quando a sala muda (ex: Boss Rush)."""
        novo_idx = BiomaCombateFactory.normalizar_sala(sala_atual)
        if novo_idx != self.sala_idx or self.bioma is None:
            self.sala_idx = novo_idx
            self.bioma = BiomaCombateFactory.obter_bioma(novo_idx)
            self._construir_bioma_ativo()

    # ------------------------------------------------------------------
    # GERADORES PROCEDURAIS DE TEXTURAS DE CANTARIA, RUÍDO E NÉVOA (PixelArray)
    # ------------------------------------------------------------------
    def _gerar_texturas_bioma(self):
        bio = self.bioma
        if bio.tema_id in self._cache_texturas:
            return self._cache_texturas[bio.tema_id]

        rng = random.Random(717 + self.sala_idx * 41)
        c_muralha = bio.cor_muralha
        c_luz = bio.cor_luz_laje
        c_sombra = bio.cor_sombra_laje
        c_argamassa = (11, 14, 23, 255)  # #0B0E17

        # 1. Textura de Muralha em Cantaria (128x64 tiles replicáveis)
        tex_muralha = pygame.Surface((128, 64))
        tex_muralha.fill(c_muralha)
        pa = pygame.PixelArray(tex_muralha)
        try:
            m = tex_muralha.map_rgb
            m_arg = m((15, 23, 42))   # #0F172A fendas/argamassa
            m_lz = m(_lerp_cor(c_muralha, c_luz, 0.45))
            m_sb = m(c_sombra)
            miolos = [
                m(_clamp_cor((c_muralha[0] - 4, c_muralha[1] - 4, c_muralha[2] - 3))),
                m(c_muralha),
                m(_clamp_cor((c_muralha[0] + 5, c_muralha[1] + 5, c_muralha[2] + 6))),
            ]
            row_h = 16
            col_w = 32
            for y in range(64):
                row_idx = y // row_h
                y_in = y % row_h
                off_x = (col_w // 2) if (row_idx % 2) else 0
                for x in range(128):
                    x_eff = (x + off_x) % 128
                    x_in = x_eff % col_w
                    if y_in == 0 or x_in == 0:
                        pa[x, y] = m_arg
                    elif y_in == 1 or x_in == 1:
                        pa[x, y] = m_lz
                    elif y_in == row_h - 1 or x_in == col_w - 1:
                        pa[x, y] = m_sb
                    else:
                        h = ((x * 73856093) ^ (y * 19349663) ^ (self.sala_idx * 83492791)) & 7
                        pa[x, y] = miolos[0] if h < 2 else (miolos[2] if h == 7 else miolos[1])
            # Fendas diagonais antigas
            for _ in range(3):
                fx, fy = rng.randint(6, 114), rng.randint(4, 48)
                for step in range(9):
                    cx_f = (fx + step) % 128
                    cy_f = min(63, fy + step // 2 + (step % 2))
                    pa[cx_f, cy_f] = m_arg
        finally:
            pa.close()

        # 2. Textura de Pilar de Pedra com chanfro lateral (32x96)
        tex_pilar = pygame.Surface((32, 96))
        tex_pilar.fill(c_muralha)
        pa_p = pygame.PixelArray(tex_pilar)
        try:
            mp = tex_pilar.map_rgb
            mp_arg = mp((11, 14, 23))
            mp_lz = mp(_lerp_cor(c_muralha, c_luz, 0.58))
            mp_sb = mp((15, 23, 42))
            mp_mid = mp(c_muralha)
            mp_hi = mp(_lerp_cor(c_muralha, c_luz, 0.28))
            for y in range(96):
                junta_h = (y % 16 == 0)
                for x in range(32):
                    if junta_h or x in (0, 31):
                        pa_p[x, y] = mp_arg
                    elif x in (1, 2) or (y % 16 == 1 and x < 26):
                        pa_p[x, y] = mp_lz
                    elif x >= 27 or (y % 16 == 15):
                        pa_p[x, y] = mp_sb
                    else:
                        h = ((x * 29 + y * 53 + self.sala_idx * 17) & 7)
                        pa_p[x, y] = mp_hi if (x < 10 and h > 3) else (mp_sb if (x > 20 and h < 3) else mp_mid)
        finally:
            pa_p.close()

        # 3. Textura estocástica de ruído em pixel art para o piso 1/Z (320x120 -> escala 3x para 960x360)
        ruido_base = pygame.Surface((320, 120), pygame.SRCALPHA)
        pa_r = pygame.PixelArray(ruido_base)
        try:
            mr = ruido_base.map_rgb
            m_tr = mr((0, 0, 0, 0))
            m_esc = mr((11, 14, 23, 52))
            m_clr = mr((c_luz[0], c_luz[1], c_luz[2], 36))
            for y in range(120):
                for x in range(320):
                    h = ((x * 374761393) ^ (y * 668265263) ^ (self.sala_idx * 982451653)) & 31
                    if h < 4:
                        pa_r[x, y] = m_esc
                    elif h == 17:
                        pa_r[x, y] = m_clr
                    else:
                        pa_r[x, y] = m_tr
        finally:
            pa_r.close()
        overlay_ruido = pygame.transform.scale(ruido_base, (self.largura, 360))

        # 4. Névoa rasteira translúcida cobrindo a junção piso/horizonte
        nevoa_strip = pygame.Surface((self.largura + 160, 76), pygame.SRCALPHA)
        ch = bio.cor_horizonte
        cor_neb = _lerp_cor(ch, (148, 163, 184), 0.35)
        for fy in range(76):
            # Pico de densidade no meio da faixa (~y=38), esmaecendo em cima e embaixo
            sin_d = math.sin((fy / 75.0) * math.pi)
            alpha_f = int((sin_d ** 1.4) * 56)
            pygame.draw.line(nevoa_strip, (*cor_neb, alpha_f), (0, fy), (nevoa_strip.get_width(), fy))
        for wx in range(0, nevoa_strip.get_width(), 96):
            pygame.draw.ellipse(nevoa_strip, (*cor_neb, 28), (wx - 20, 18, 130, 38))

        # 5. Pré-render do Halo de Tocha Translúcido (128x128 SRCALPHA sem BLEND_ADD opaco)
        halo_suave = pygame.Surface((128, 128), pygame.SRCALPHA)
        fogo_cfg = PALETA_FOGO.get(bio.tipo_fogo, PALETA_FOGO["LARANJA"])
        pygame.draw.circle(halo_suave, (*fogo_cfg["halo_ext"], 12), (64, 64), 60)
        pygame.draw.circle(halo_suave, (*fogo_cfg["halo_med"], 28), (64, 64), 35)
        pygame.draw.circle(halo_suave, (*fogo_cfg["nucleo"], 55), (64, 64), 14)

        bundle = {
            "muralha": tex_muralha,
            "pilar": tex_pilar,
            "ruido_piso": overlay_ruido,
            "nevoa": nevoa_strip,
            "halo_suave": halo_suave,
        }
        self._cache_texturas[bio.tema_id] = bundle
        return bundle

    def _construir_bioma_ativo(self):
        rng = random.Random(4099 + self.sala_idx * 97)
        bio = self.bioma
        tema = bio.tema_id
        fogo_cfg = PALETA_FOGO.get(bio.tipo_fogo, PALETA_FOGO["LARANJA"])

        self._tex = self._gerar_texturas_bioma()

        # Pool de partículas volumétricas do bioma
        self.particulas = []
        for _ in range(44):
            cor_p = rng.choice((bio.particula_cor, fogo_cfg["meio"], bio.cor_destaque))
            vel_y = rng.uniform(-16.0, -5.0)
            if tema == "fovea_lamentos":
                vel_y = rng.uniform(-9.0, -3.0)
            elif tema == "vazio_absoluto":
                vel_y = rng.uniform(-20.0, -8.0)
            self.particulas.append({
                "x": rng.uniform(-540, 540),
                "y": rng.uniform(-90, 132),
                "z": rng.uniform(-60, 250),
                "vel_y": vel_y,
                "fase": rng.uniform(0.0, math.tau),
                "raio": rng.uniform(1.6, 3.4),
                "cor": cor_p,
            })

        self._estrelas = [
            (rng.randint(12, self.largura - 12), rng.randint(8, int(self.altura * 0.42)),
             rng.choice((1, 1, 2)), rng.uniform(0.0, math.tau))
            for _ in range(72 if tema == "vazio_absoluto" else 42)
        ]

        self._nuvens = [
            (rng.randint(-120, self.largura + 120), rng.randint(24, 128), rng.randint(170, 310), rng.randint(24, 48))
            for _ in range(8)
        ]

        self._rachaduras = [
            (rng.uniform(-680, 680), rng.uniform(-35, 240), rng.uniform(50, 140), rng.uniform(-35, 35))
            for _ in range(12)
        ]
        self._pocas_sangue = [
            (rng.uniform(-560, 560), rng.uniform(-10, 220), rng.uniform(65, 135), rng.uniform(18, 34))
            for _ in range(7)
        ]
        self._musgos = [
            (rng.uniform(-640, 640), rng.uniform(-25, 240), rng.uniform(18, 42))
            for _ in range(14)
        ]
        self._estalactites = [
            (i * 68 + rng.randint(-10, 12), rng.randint(42, 108), rng.randint(22, 40))
            for i in range(18)
        ]
        self._raizes = [
            (i * 155 + rng.randint(15, 65), rng.randint(68, 128), rng.uniform(0.0, 6.28))
            for i in range(8)
        ]

        # Objetos em profundidade Z exclusivos do bioma
        self._elementos_z = []
        if tema == "ameias":
            for zx in (-440, 440):
                self._elementos_z.append({"tipo": "est_bandeira", "x": zx, "z": 185.0, "fase": rng.uniform(0, 6.28)})
            for _ in range(9):
                self._elementos_z.append({
                    "tipo": "flecha", "x": rng.uniform(-420, 420), "z": rng.uniform(-25, 195),
                    "ang": rng.uniform(-0.38, 0.25),
                })
        elif tema == "cripta_sombria":
            for gx in (-540, -180, 180, 540):
                self._elementos_z.append({"tipo": "gargula", "x": gx, "z": self.z_fundo - 8})
        elif tema == "fovea_lamentos":
            for _ in range(8):
                self._elementos_z.append({
                    "tipo": "estaca_ossos",
                    "x": rng.uniform(-560, 560),
                    "z": rng.uniform(-10, 235),
                    "inc": rng.uniform(-0.28, 0.28),
                    "h": rng.uniform(44, 86),
                })
        elif tema == "torre_quebrada":
            for _ in range(9):
                self._elementos_z.append({
                    "tipo": "espada_escudo",
                    "x": rng.uniform(-540, 540),
                    "z": rng.uniform(-25, 220),
                    "tem_escudo": rng.random() > 0.45,
                    "ang": rng.uniform(-0.32, 0.32),
                })
        elif tema == "catedrais":
            for side in (-1, 1):
                for idx_p, zp in enumerate((50.0, 180.0)):
                    self._elementos_z.append({
                        "tipo": "pedestal_decap",
                        "x": side * (480 + idx_p * 95),
                        "z": zp,
                    })
        elif tema == "santuario_miasma":
            for ox in (-360, -140, 140, 360):
                self._elementos_z.append({
                    "tipo": "orbe_sangue",
                    "x": ox, "z": rng.uniform(40, 200),
                    "y_base": rng.uniform(20, 75), "fase": rng.uniform(0, 6.28),
                })
        elif tema == "vazio_absoluto":
            for _ in range(14):
                self._elementos_z.append({
                    "tipo": "frag_flutuante",
                    "x": rng.uniform(-620, 620),
                    "z": rng.uniform(-30, 240),
                    "y_base": rng.uniform(-20, 95),
                    "tam": rng.uniform(10, 24),
                    "vel": rng.uniform(0.6, 1.4),
                    "fase": rng.uniform(0, 6.28),
                })

    def atualizar(self, dt):
        self.tempo += dt
        for p in self.particulas:
            p["y"] += p["vel_y"] * dt
            p["x"] += math.sin(self.tempo * 1.6 + p["fase"]) * 9.5 * dt
            if p["y"] < -118:
                p["y"] = 136.0
                p["x"] = random.uniform(-540, 540)

    def _paleta(self):
        return PALETAS_ARENA.get(self.sala_idx, PALETAS_ARENA[0])

    # ------------------------------------------------------------------
    # CAMADA 1: CÉU ATMOSFÉRICO E PARALAXE DISTANTE
    # ------------------------------------------------------------------
    def _desenhar_ceu_e_fundo_paralaxe(self, superficie, camera):
        bio = self.bioma
        tema = bio.tema_id
        horizonte_y = int(camera.horizonte_base_y - camera.y * 0.22)
        h_ceu = max(1, horizonte_y + 42)

        for y in range(0, h_ceu, 4):
            f = y / float(h_ceu)
            pygame.draw.rect(superficie, _lerp_cor(bio.cor_ceu, bio.cor_horizonte, f), (0, y, self.largura, 4))

        base_inf = (5, 7, 16) if tema == "vazio_absoluto" else (7, 9, 15)
        pygame.draw.rect(superficie, base_inf, (0, h_ceu, self.largura, max(1, self.altura - h_ceu)))

        if tema == "ameias":
            # Lua atmosférica com múltiplos halos translúcidos, cráteres e nuvens em paralaxe
            lx = int(self.largura * 0.72 - camera.x * 0.14)
            ly = int(horizonte_y * 0.44 - camera.y * 0.10)
            lua_s = pygame.Surface((260, 260), pygame.SRCALPHA)
            pygame.draw.circle(lua_s, (148, 163, 184, 14), (130, 130), 126)
            pygame.draw.circle(lua_s, (203, 213, 225, 24), (130, 130), 92)
            pygame.draw.circle(lua_s, (226, 232, 240, 52), (130, 130), 64)
            pygame.draw.circle(lua_s, (238, 242, 248, 215), (130, 130), 46)
            pygame.draw.circle(lua_s, (165, 180, 204, 100), (118, 118), 11)
            pygame.draw.circle(lua_s, (165, 180, 204, 75), (144, 138), 8)
            pygame.draw.circle(lua_s, (15, 23, 42, 32), (138, 126), 44)  # leve sombra noturna na borda
            superficie.blit(lua_s, (lx - 130, ly - 130))

            for idx_n, (nx_0, ny_0, nw, nh) in enumerate(self._nuvens):
                nx = int((nx_0 - camera.x * (0.16 + 0.03 * (idx_n % 2)) + self.tempo * (6.0 + idx_n)) % (self.largura + 340)) - 220
                ny = int(ny_0 - camera.y * 0.08)
                n_s = pygame.Surface((nw, nh), pygame.SRCALPHA)
                pygame.draw.ellipse(n_s, (15, 22, 38, 110), (0, 0, nw, nh))
                pygame.draw.ellipse(n_s, (28, 38, 62, 65), (nw // 6, nh // 6, nw * 2 // 3, nh // 2))
                superficie.blit(n_s, (nx, ny))

            off_m = int(-camera.x * 0.24)
            for i in range(-1, 8):
                bx = i * 160 + (off_m % 160)
                by = horizonte_y - int(camera.y * 0.16)
                pygame.draw.rect(superficie, (14, 20, 34), (bx, by - 66, 160, 82))
                for m_i in range(0, 160, 38):
                    pygame.draw.rect(superficie, (14, 20, 34), (bx + m_i, by - 86, 22, 22))
                if i % 2 == 0:
                    pygame.draw.polygon(superficie, (12, 17, 29), [(bx + 54, by - 86), (bx + 78, by - 142), (bx + 102, by - 86)])

        elif tema == "cripta_sombria":
            for layer, (alt_b, col_b, alp) in enumerate(((56, (90, 18, 32), 48), (34, (125, 22, 38), 56))):
                bruma = pygame.Surface((self.largura, alt_b), pygame.SRCALPHA)
                bruma.fill((*col_b, alp))
                superficie.blit(bruma, (0, max(0, horizonte_y - alt_b + layer * 18)))
            off_r = int(-camera.x * 0.22)
            for i in range(-1, 6):
                mx = i * 210 + (off_r % 210)
                my = horizonte_y - int(camera.y * 0.15)
                pygame.draw.rect(superficie, (22, 10, 17), (mx + 22, my - 98, 130, 112))
                pygame.draw.polygon(superficie, (22, 10, 17), [(mx + 14, my - 98), (mx + 87, my - 165), (mx + 160, my - 98)])

        elif tema == "fovea_lamentos":
            off_e = int(-camera.x * 0.18)
            for ex_0, eh, ew in self._estalactites:
                ex = (ex_0 + off_e) % (self.largura + 120) - 60
                pygame.draw.polygon(superficie, (18, 11, 15), [(ex, 0), (ex + ew, 0), (ex + ew // 2, eh)])
                pygame.draw.line(superficie, (46, 20, 28), (ex + 2, 0), (ex + ew // 2, eh), 1)
            for rx_0, rh, fase in self._raizes:
                rx = int((rx_0 - camera.x * 0.24) % (self.largura + 100)) - 40
                bal = math.sin(self.tempo * 1.4 + fase) * 6.0
                pts_r = [(rx, 0), (rx + int(bal * 0.4) - 5, rh // 2), (rx + int(bal), rh)]
                pygame.draw.lines(superficie, (36, 16, 22), False, pts_r, 3)

        elif tema == "torre_quebrada":
            for sx, sy, sr, sf in self._estrelas:
                bri = int(125 + 115 * math.sin(self.tempo * 2.2 + sf))
                pygame.draw.circle(superficie, _clamp_cor((bri - 20, bri, 255)), (int((sx - camera.x * 0.05) % self.largura), sy), sr)
            off_t = int(-camera.x * 0.20)
            my = horizonte_y - int(camera.y * 0.15)
            pygame.draw.polygon(superficie, (14, 22, 48), [
                (180 + off_t, my), (210 + off_t, my - 155), (255 + off_t, my - 135),
                (290 + off_t, my - 165), (320 + off_t, my),
            ])

        elif tema == "catedrais":
            off_c = int(-camera.x * 0.18)
            for i in range(-1, 5):
                ax = i * 260 + (off_c % 260)
                pygame.draw.arc(superficie, (48, 56, 74), (ax, -30, 260, 175), 0, math.pi, 3)
                pygame.draw.line(superficie, (26, 32, 46), (ax, 58), (ax, horizonte_y + 20), 6)
            for vx in (self.largura // 2 - 220, self.largura // 2, self.largura // 2 + 220):
                px_v = vx + int(-camera.x * 0.12)
                py_v = max(48, horizonte_y - 96)
                pygame.draw.circle(superficie, (52, 44, 30), (px_v, py_v), 28, 2)
                pygame.draw.circle(superficie, (86, 68, 34), (px_v, py_v), 20, 1)

        elif tema == "santuario_miasma":
            off_s = int(-camera.x * 0.22)
            for y in range(0, h_ceu, 18):
                desl = (y // 18 % 2) * 24
                for x in range(-24, self.largura + 24, 48):
                    pygame.draw.rect(superficie, (34, 14, 18), (x + desl + (off_s % 48), y, 46, 16), 1)
            for tx in (140, 320, 640, 820):
                px_t = tx + int(-camera.x * 0.20)
                rect_tap = pygame.Rect(px_t - 22, 16, 44, max(40, horizonte_y - 14))
                pygame.draw.polygon(superficie, (115, 16, 24), [
                    (rect_tap.left, rect_tap.top), (rect_tap.right, rect_tap.top),
                    (rect_tap.right, rect_tap.bottom - 18), (rect_tap.centerx, rect_tap.bottom),
                    (rect_tap.left, rect_tap.bottom - 18),
                ])
                pygame.draw.polygon(superficie, (212, 165, 58), [
                    (rect_tap.left, rect_tap.top), (rect_tap.right, rect_tap.top),
                    (rect_tap.right, rect_tap.bottom - 18), (rect_tap.centerx, rect_tap.bottom),
                    (rect_tap.left, rect_tap.bottom - 18),
                ], 2)

        elif tema == "vazio_absoluto":
            for sx, sy, sr, sf in self._estrelas:
                bri = int(145 + 100 * math.sin(self.tempo * 2.4 + sf))
                cor_e = (56, 189, 248) if (int(sf * 10) % 3 == 0) else _clamp_cor((bri, bri, 255))
                pygame.draw.circle(superficie, cor_e, (int((sx - camera.x * 0.06) % self.largura), sy), sr)

            cx_v = self.largura // 2 - int(camera.x * 0.10)
            cy_v = horizonte_y - 36 - int(camera.y * 0.10)
            neb_s = pygame.Surface((460, 220), pygame.SRCALPHA)
            pygame.draw.ellipse(neb_s, (56, 189, 248, 22), (20, 20, 420, 170))
            pygame.draw.ellipse(neb_s, (99, 102, 241, 28), (75, 45, 310, 125))
            superficie.blit(neb_s, (cx_v - 230, cy_v - 110))

            for raio_x, raio_y, vel, cor_an in ((220, 62, 0.22, (56, 189, 248)), (150, 44, -0.34, (129, 140, 248))):
                pts_a = []
                ang_off = self.tempo * vel
                for k in range(36):
                    a = (k / 36.0) * math.tau
                    lx_a, ly_a = math.cos(a) * raio_x, math.sin(a) * raio_y
                    rx_a = lx_a * math.cos(ang_off) - ly_a * math.sin(ang_off) * 0.25
                    ry_a = lx_a * math.sin(ang_off) * 0.25 + ly_a * math.cos(ang_off)
                    pts_a.append((int(cx_v + rx_a), int(cy_v + ry_a)))
                if len(pts_a) >= 3:
                    pygame.draw.polygon(superficie, cor_an, pts_a, 1)

    # ------------------------------------------------------------------
    # TOCHAS PIXEL-ART COM ARANDELA DE FERRO, CHAMA 6x10 E HALO SRCALPHA SUAVE
    # ------------------------------------------------------------------
    def _desenhar_fogo_bioma(self, superficie, tx, ty, esc, fase_seed=0.0, com_arandela=False, chao_y_proj=None):
        bio = self.bioma
        fogo = PALETA_FOGO.get(bio.tipo_fogo, PALETA_FOGO["LARANJA"])
        pulso_norm = math.sin(self.tempo * 6.5 + fase_seed)

        # 1. Arandela de ferro forjado (#1E293B, base ~4x8 px ancorada na pedra)
        if com_arandela:
            aw = max(4, int(round(4 * esc)))
            ah = max(8, int(round(8 * esc)))
            cx_a = int(tx)
            topo_a = int(ty + 1)
            pygame.draw.rect(superficie, (30, 41, 59), (cx_a - aw // 2, topo_a, aw, ah))
            pygame.draw.rect(superficie, (11, 14, 23), (cx_a - aw // 2, topo_a, aw, ah), 1)
            pygame.draw.rect(superficie, (71, 85, 105), (cx_a - max(2, aw), topo_a, max(4, aw * 2), max(2, int(2 * esc))))

        # 2. Halo de luz translúcido suave (raios ~60 / 35 / 14 com pulso natural, sem BLEND_ADD opaco)
        fator_p = 1.0 + 0.08 * pulso_norm
        tam_halo = max(24, int(128 * esc * fator_p))
        halo_esc = pygame.transform.scale(self._tex["halo_suave"], (tam_halo, tam_halo))
        superficie.blit(halo_esc, (int(tx - tam_halo // 2), int(ty - tam_halo // 2)))

        # Reflexo elíptico tênue no piso abaixo do pilar/arandela
        if chao_y_proj is not None:
            pw_g = max(26, int(76 * esc * fator_p))
            ph_g = max(8, int(22 * esc * fator_p))
            g_surf = pygame.Surface((pw_g, ph_g), pygame.SRCALPHA)
            pygame.draw.ellipse(g_surf, (*fogo["halo_ext"], 14), (0, 0, pw_g, ph_g))
            pygame.draw.ellipse(g_surf, (*fogo["halo_med"], 24), (pw_g // 4, ph_g // 4, pw_g // 2, max(2, ph_g // 2)))
            superficie.blit(g_surf, (int(tx - pw_g // 2), int(chao_y_proj - ph_g // 2)))

        # 3. Chama cônica pixel-art (~6x10 px em 3 quadros orgânicos via math.sin)
        quadro = int((math.sin(self.tempo * 12.5 + fase_seed) + 1.0) * 1.499)  # 0, 1 ou 2
        osc_x = (-1 if quadro == 0 else (1 if quadro == 2 else 0)) * max(1, int(round(esc)))
        fh = max(9, int(round((10 + (1 if quadro == 1 else 0)) * esc)))
        fw = max(6, int(round(6 * esc)))
        base_y = int(ty + 1)

        # Ponta externa carmesim escuro (#DC2626)
        pts_ponta = [
            (tx - fw // 2, base_y - max(2, fh // 4)),
            (tx - max(1, fw // 3), base_y - (fh * 2) // 3),
            (tx + osc_x, base_y - fh),
            (tx + max(1, fw // 3), base_y - (fh * 2) // 3),
            (tx + fw // 2, base_y - max(2, fh // 4)),
            (tx, base_y),
        ]
        pygame.draw.polygon(superficie, fogo["ponta"], pts_ponta)

        # Corpo médio laranja vivo (#F97316)
        mw = max(4, int(fw * 0.72))
        mh = max(6, int(fh * 0.70))
        pts_meio = [
            (tx - mw // 2, base_y - 1),
            (tx + osc_x // 2, base_y - mh),
            (tx + mw // 2, base_y - 1),
        ]
        pygame.draw.polygon(superficie, fogo["meio"], pts_meio)

        # Núcleo quente amarelo-palha (#FEF08A)
        nw = max(2, int(fw * 0.36))
        nh = max(3, int(fh * 0.36))
        pygame.draw.polygon(superficie, fogo["nucleo"], [
            (tx - nw // 2, base_y - 1),
            (tx, base_y - nh),
            (tx + nw // 2, base_y - 1),
        ])

    # ------------------------------------------------------------------
    # CAMADA 2: MURALHA TEXTURIZADA DE CANTARIA, ARCOS, SETEIRAS E NÉVOA
    # ------------------------------------------------------------------
    def _desenhar_muralha_horizonte(self, superficie, camera):
        bio = self.bioma
        tema = bio.tema_id
        esq_x, chao_fundo_y, esc_f = camera.projetar(-self.largura_mundo, self.y_chao, self.z_fundo)
        dir_x, _, _ = camera.projetar(self.largura_mundo, self.y_chao, self.z_fundo)
        larg_total = max(1, dir_x - esq_x)

        if tema == "vazio_absoluto":
            pygame.draw.line(superficie, (56, 189, 248), (esq_x, chao_fundo_y), (dir_x, chao_fundo_y), 2)
            return

        altura_parede = int((155 if tema in ("catedrais", "santuario_miasma") else 142) * esc_f)
        if tema == "torre_quebrada":
            altura_parede = int(84 * esc_f)
        topo_y = chao_fundo_y - altura_parede

        # Ladrilhamento da textura procedural de cantaria na muralha (zero bloco liso)
        tex_m = self._tex["muralha"]
        tw, th = tex_m.get_size()
        x_ini = max(0, esq_x)
        x_fim = min(self.largura, dir_x)
        y_ini = max(0, topo_y)
        y_fim = min(self.altura, chao_fundo_y)
        if x_fim > x_ini and y_fim > y_ini:
            clip_ant = superficie.get_clip()
            superficie.set_clip(pygame.Rect(x_ini, y_ini, x_fim - x_ini, y_fim - y_ini))
            start_tx = esq_x + ((x_ini - esq_x) // tw) * tw
            for py_t in range(y_ini, y_fim, th):
                for px_t in range(start_tx, x_fim, tw):
                    superficie.blit(tex_m, (px_t, py_t))
            superficie.set_clip(clip_ant)

        pygame.draw.line(superficie, bio.cor_luz_laje, (esq_x, topo_y), (dir_x, topo_y), 2)
        pygame.draw.line(superficie, bio.cor_sombra_laje, (esq_x, chao_fundo_y), (dir_x, chao_fundo_y), 2)

        num_arcos = 5
        passo = (self.largura_mundo * 2.0) / num_arcos
        for i in range(num_arcos):
            mcx = -self.largura_mundo + (i + 0.5) * passo
            ax, ay, a_esc = camera.projetar(mcx, self.y_chao, self.z_fundo)
            lw, lh = max(14, int(84 * a_esc)), max(18, int(92 * a_esc))

            # Arcos góticos com sombra interna profunda em todos os biomas murados
            if tema in ("ameias", "cripta_sombria", "catedrais", "santuario_miasma"):
                rect_a = pygame.Rect(ax - lw // 2, ay - lh, lw, lh)
                pygame.draw.rect(superficie, (7, 9, 16), rect_a, border_top_left_radius=lw // 2, border_top_right_radius=lw // 2)
                pygame.draw.rect(superficie, (15, 20, 32), rect_a.inflate(-8, -8), width=2, border_top_left_radius=lw // 2, border_top_right_radius=lw // 2)
                if tema == "cripta_sombria":
                    pygame.draw.rect(superficie, (135, 24, 38), rect_a.inflate(-10, -10), border_top_left_radius=lw // 2, border_top_right_radius=lw // 2)
                    pygame.draw.line(superficie, (8, 5, 8), (rect_a.left + 8, rect_a.centery), (rect_a.right - 8, rect_a.top + 22), 2)
                borda_a = (165, 120, 36) if tema == "santuario_miasma" else bio.cor_luz_laje
                pygame.draw.rect(superficie, borda_a, rect_a, width=2, border_top_left_radius=lw // 2, border_top_right_radius=lw // 2)

            if tema == "ameias":
                mx_r = max(8, int(22 * a_esc))
                pygame.draw.rect(superficie, bio.cor_muralha, (ax - mx_r, topo_y - int(18 * a_esc), mx_r * 2, int(18 * a_esc)))
                pygame.draw.rect(superficie, bio.cor_luz_laje, (ax - mx_r, topo_y - int(18 * a_esc), mx_r * 2, int(18 * a_esc)), 1)
                # Seteiras com luz fraca vazando entre os arcos
                sx_f, sy_f, s_esc = camera.projetar(mcx + passo * 0.5, self.y_chao, self.z_fundo)
                fw, fh = max(4, int(10 * s_esc)), max(14, int(38 * s_esc))
                pygame.draw.rect(superficie, (18, 24, 38), (sx_f - fw // 2, sy_f - int(84 * s_esc), fw, fh))
                pygame.draw.rect(superficie, (245, 158, 11), (sx_f - max(1, fw // 4), sy_f - int(80 * s_esc), max(2, fw // 2), fh - 6))
                tx, ty, t_esc = camera.projetar(mcx + passo * 0.45, self.y_chao - 70, self.z_fundo - 6)
                self._desenhar_fogo_bioma(superficie, tx, ty, t_esc, i * 1.4, com_arandela=True)

            elif tema == "cripta_sombria":
                tx, ty, t_esc = camera.projetar(mcx, self.y_chao - 74, self.z_fundo - 6)
                self._desenhar_fogo_bioma(superficie, tx, ty, t_esc, i * 1.2, com_arandela=True)

            elif tema == "fovea_lamentos":
                cx_c, cy_c, c_esc = camera.projetar(mcx, self.y_chao - 38, self.z_fundo - 8)
                pts_cr = [(cx_c - int(9 * c_esc), cy_c + int(22 * c_esc)), (cx_c, cy_c - int(22 * c_esc)), (cx_c + int(9 * c_esc), cy_c + int(22 * c_esc))]
                pygame.draw.polygon(superficie, (190, 24, 58), pts_cr)
                self._desenhar_fogo_bioma(superficie, cx_c, cy_c - int(10 * c_esc), c_esc * 0.85, i * 1.9, com_arandela=False)

            elif tema == "torre_quebrada":
                if i % 2 == 0:
                    pygame.draw.rect(superficie, bio.cor_muralha, (ax - lw // 3, topo_y - int(26 * a_esc), int(lw * 0.66), int(26 * a_esc)))
                    pygame.draw.rect(superficie, bio.cor_luz_laje, (ax - lw // 3, topo_y - int(26 * a_esc), int(lw * 0.66), int(26 * a_esc)), 1)
                tx, ty, t_esc = camera.projetar(mcx, self.y_chao - 58, self.z_fundo - 6)
                self._desenhar_fogo_bioma(superficie, tx, ty, t_esc, i * 1.7, com_arandela=True)

            elif tema == "catedrais":
                pygame.draw.rect(superficie, (38, 46, 62), (ax - int(14 * a_esc), 0, int(28 * a_esc), ay))
                pygame.draw.rect(superficie, bio.cor_luz_laje, (ax - int(14 * a_esc), 0, int(28 * a_esc), ay), 1)
                tx, ty, t_esc = camera.projetar(mcx, self.y_chao - 78, self.z_fundo - 8)
                self._desenhar_fogo_bioma(superficie, tx, ty, t_esc, i * 1.3, com_arandela=True)

            elif tema == "santuario_miasma":
                tx, ty, t_esc = camera.projetar(mcx, self.y_chao - 72, self.z_fundo - 6)
                self._desenhar_fogo_bioma(superficie, tx, ty, t_esc, i * 1.5, com_arandela=True)

        if tema == "santuario_miasma":
            al_x, al_y, al_e = camera.projetar(0.0, self.y_chao, self.z_fundo - 10)
            aw, ah = max(24, int(116 * al_e)), max(18, int(44 * al_e))
            pygame.draw.rect(superficie, (52, 22, 28), (al_x - aw // 2, al_y - ah, aw, ah))
            pygame.draw.rect(superficie, (212, 165, 58), (al_x - aw // 2, al_y - ah, aw, ah), 2)
            self._desenhar_fogo_bioma(superficie, al_x, al_y - ah - int(10 * al_e), al_e * 1.15, 3.14, com_arandela=True)

        # Névoa rasteira translúcida suavizando a junção piso/muralha do horizonte
        neb_off_x = int(math.sin(self.tempo * 0.65) * 35.0) - 80
        superficie.blit(self._tex["nevoa"], (neb_off_x, chao_fundo_y - 38))

    # ------------------------------------------------------------------
    # CAMADA 3: PISO 2.5D EM LAJES TEXTURIZADAS 1/Z (SEM PLANO LISO)
    # ------------------------------------------------------------------
    def _desenhar_piso_trapezio_3d(self, superficie, camera):
        bio = self.bioma
        tema = bio.tema_id
        valores_z = self._faixas_z
        fatias_z = len(valores_z) - 1
        colunas_laje = 10

        alvo_piso = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA) if tema == "vazio_absoluto" else superficie

        # Desenho individual por placa de cantaria alternada (alvenaria intercalada) no espaço 1/Z
        for i in range(fatias_z):
            z1, z2 = valores_z[i], valores_z[i + 1]
            frac = i / float(max(1, fatias_z - 1))
            base_c = _lerp_multi(bio.paleta_piso, frac)
            stagger = 0.5 if (i % 2 == 1) else 0.0

            _, y1, _ = camera.projetar(0.0, self.y_chao, z1)
            _, y2, _ = camera.projetar(0.0, self.y_chao, z2)

            for c in range(colunas_laje + (1 if stagger > 0 else 0)):
                u0 = max(-1.0, -1.0 + (2.0 * (c - stagger)) / float(colunas_laje))
                u1 = min(1.0, -1.0 + (2.0 * (c + 1.0 - stagger)) / float(colunas_laje))
                if u1 <= u0 + 1e-4:
                    continue

                xm0, xm1 = u0 * self.largura_mundo, u1 * self.largura_mundo
                x1_e, _, _ = camera.projetar(xm0, self.y_chao, z1)
                x1_d, _, _ = camera.projetar(xm1, self.y_chao, z1)
                x2_e, _, _ = camera.projetar(xm0, self.y_chao, z2)
                x2_d, _, _ = camera.projetar(xm1, self.y_chao, z2)

                # Alternância sutil de tonalidade entre placas vizinhas simulando cantaria antiga desgastada
                variacao = (((i * 7 + c * 13 + self.sala_idx * 5) % 5) - 2) * 3
                c_laje = _clamp_cor((base_c[0] + variacao, base_c[1] + variacao, base_c[2] + variacao + 2))
                poly = [(x1_e, y1), (x1_d, y1), (x2_d, y2), (x2_e, y2)]

                if tema == "vazio_absoluto":
                    alp = int(145 + 75 * frac)
                    pygame.draw.polygon(alvo_piso, (*c_laje, alp), poly)
                    alp_g = int(45 + 125 * math.sin(frac * math.pi))
                    pygame.draw.line(alvo_piso, (56, 189, 248, alp_g), (x1_e, y1), (x1_d, y1), 1)
                else:
                    pygame.draw.polygon(alvo_piso, c_laje, poly)
                    # Destaque claro de 1px no topo (#334155), borda chanfrada sombreada embaixo (#0F172A) e junta lateral (#0B0E17)
                    pygame.draw.line(alvo_piso, bio.cor_luz_laje, (x1_e + 1, y1 + 1), (x1_d - 1, y1 + 1), 1)
                    pygame.draw.line(alvo_piso, bio.cor_sombra_laje, (x2_e + 1, max(y1, y2 - 1)), (x2_d - 1, max(y1, y2 - 1)), 1)
                    pygame.draw.line(alvo_piso, bio.cor_junta, (x1_e, y1), (x2_e, y2), 1)
                    pygame.draw.line(alvo_piso, bio.cor_junta, (x2_e, y2), (x2_d, y2), 1)

            if tema == "cripta_sombria":
                xe_l, _, _ = camera.projetar(-self.largura_mundo, self.y_chao, z1)
                xd_l, _, _ = camera.projetar(self.largura_mundo, self.y_chao, z1)
                pulso_l = 0.6 + 0.4 * math.sin(self.tempo * 3.8 + i * 0.7)
                c_lava = _clamp_cor((int(195 * pulso_l), int(52 * pulso_l), 20))
                pygame.draw.line(alvo_piso, c_lava, (xe_l, y1), (xd_l, y1), 2 if i % 3 == 0 else 1)

        if tema == "vazio_absoluto":
            superficie.blit(alvo_piso, (0, 0))
        else:
            # Sobrepõe textura estocástica de pixel-art dentro do contorno do trapézio do piso
            esq_x, chao_fundo_y, _ = camera.projetar(-self.largura_mundo, self.y_chao, self.z_fundo)
            fe_x, fe_y, _ = camera.projetar(-self.largura_mundo, self.y_chao, self.z_frente)
            fd_x, fd_y, _ = camera.projetar(self.largura_mundo, self.y_chao, self.z_frente)
            y_clip_top = max(0, chao_fundo_y)
            y_clip_bot = min(self.altura, fe_y)
            if y_clip_bot > y_clip_top:
                clip_ant = superficie.get_clip()
                superficie.set_clip(pygame.Rect(max(0, fe_x), y_clip_top, max(1, min(self.largura, fd_x) - max(0, fe_x)), y_clip_bot - y_clip_top))
                superficie.blit(self._tex["ruido_piso"], (0, y_clip_top))
                superficie.set_clip(clip_ant)

        # Detalhes específicos de piso por bioma
        if tema == "ameias":
            for rx, rz, rl, rd in self._rachaduras:
                p1 = camera.projetar(rx, self.y_chao, rz)[:2]
                p2 = camera.projetar(rx + rl * 0.5, self.y_chao, rz + rd)[:2]
                p3 = camera.projetar(rx + rl, self.y_chao, rz + rd * 0.5)[:2]
                pygame.draw.lines(superficie, (11, 14, 23), False, [p1, p2, p3], 1)

        elif tema == "fovea_lamentos":
            pulso_s = 0.55 + 0.45 * math.sin(self.tempo * 4.2)
            for bx, bz, bw, bh in self._pocas_sangue:
                px_b, py_b, e_b = camera.projetar(bx, self.y_chao, bz)
                rw, rh = max(12, int(bw * e_b)), max(4, int(bh * e_b))
                ps = pygame.Surface((rw, rh), pygame.SRCALPHA)
                pygame.draw.ellipse(ps, (98, 12, 24, 185), (0, 0, rw, rh))
                pygame.draw.ellipse(ps, (215, 48, 72, int(65 + 55 * pulso_s)), (rw // 6, rh // 4, rw // 2, max(2, rh // 3)))
                superficie.blit(ps, (px_b - rw // 2, py_b - rh // 2))

        elif tema == "torre_quebrada":
            pulso_r = 0.5 + 0.5 * math.sin(self.tempo * 3.0)
            cor_r = _clamp_cor((int(145 + 75 * pulso_r), int(65 + 45 * pulso_r), 248))
            for raio_m in (165.0, 235.0):
                pts_r = [camera.projetar(math.cos(k * math.tau / 16.0) * raio_m, self.y_chao, 92.0 + math.sin(k * math.tau / 16.0) * (raio_m * 0.36))[:2] for k in range(16)]
                pygame.draw.polygon(superficie, cor_r, pts_r, 1)
            for rx_g in (-260, 0, 260):
                gx, gy, ge = camera.projetar(rx_g, self.y_chao, 92.0)
                r_g = max(4, int(14 * ge))
                pygame.draw.polygon(superficie, cor_r, [(gx, gy - r_g // 2), (gx + r_g, gy), (gx, gy + r_g // 2), (gx - r_g, gy)], 1)

        elif tema == "catedrais":
            for mx, mz, mw in self._musgos:
                px_m, py_m, e_m = camera.projetar(mx, self.y_chao, mz)
                pygame.draw.ellipse(superficie, (36, 68, 42), (px_m - int(mw * 0.5 * e_m), py_m - 3, max(4, int(mw * e_m)), max(3, int(6 * e_m))))
            luz_feixes = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            for fx_0 in (-240, 20, 280):
                px_f, py_f, _ = camera.projetar(fx_0, self.y_chao, 115.0)
                pygame.draw.polygon(luz_feixes, (56, 189, 248, 22), [
                    (px_f - 95, 0), (px_f - 45, 0), (px_f + 42, py_f + 8), (px_f - 46, py_f + 8),
                ])
            superficie.blit(luz_feixes, (0, 0))

        elif tema == "santuario_miasma":
            cor_ouro = (212, 165, 58)
            for raio_x, raio_z in ((110.0, 42.0), (195.0, 74.0), (285.0, 108.0)):
                pts_c = [camera.projetar(math.cos(k * math.tau / 24.0) * raio_x, self.y_chao, 92.0 + math.sin(k * math.tau / 24.0) * raio_z)[:2] for k in range(24)]
                pygame.draw.polygon(superficie, cor_ouro, pts_c, 1)
            cx_o, cy_o, _ = camera.projetar(0.0, self.y_chao, 92.0)
            for k in range(8):
                ang_s = k * (math.tau / 8.0)
                ex_o, ey_o, _ = camera.projetar(math.cos(ang_s) * 285.0, self.y_chao, 92.0 + math.sin(ang_s) * 108.0)
                pygame.draw.line(superficie, (160, 115, 36), (cx_o, cy_o), (ex_o, ey_o), 1)

        # Degrau frontal da arena texturizado (exceto plataforma suspensa do Vazio)
        if tema != "vazio_absoluto":
            fe_x, fe_y, _ = camera.projetar(-self.largura_mundo, self.y_chao, self.z_frente)
            fd_x, fd_y, _ = camera.projetar(self.largura_mundo, self.y_chao, self.z_frente)
            alt_deg = max(1, self.altura - fe_y)
            tex_m = self._tex["muralha"]
            tw, th = tex_m.get_size()
            x_d0, x_d1 = max(0, fe_x), min(self.largura, fd_x)
            if x_d1 > x_d0 and alt_deg > 0:
                clip_ant = superficie.get_clip()
                superficie.set_clip(pygame.Rect(x_d0, fe_y, x_d1 - x_d0, alt_deg))
                for py_d in range(fe_y, self.altura, th):
                    for px_d in range(x_d0, x_d1, tw):
                        superficie.blit(tex_m, (px_d, py_d))
                superficie.set_clip(clip_ant)
                sombra_deg = pygame.Surface((x_d1 - x_d0, alt_deg), pygame.SRCALPHA)
                sombra_deg.fill((8, 10, 16, 150))
                superficie.blit(sombra_deg, (x_d0, fe_y))
            pygame.draw.line(superficie, bio.cor_luz_laje, (fe_x, fe_y), (fd_x, fd_y), 2)
            pygame.draw.line(superficie, bio.cor_sombra_laje, (fe_x, fe_y + 2), (fd_x, fd_y + 2), 2)

    # ------------------------------------------------------------------
    # CAMADA 4: PILARES TEXTURIZADOS, ILUMINAÇÃO BLEND_ADD E OBJETOS EM Z
    # ------------------------------------------------------------------
    def _desenhar_pilar_lateral(self, superficie, camera, x_mundo, z_mundo):
        bio = self.bioma
        tema = bio.tema_id
        px, py, escala = camera.projetar(x_mundo, self.y_chao, z_mundo)

        if tema == "vazio_absoluto":
            larg = max(8, int(28 * escala))
            alt = max(40, int(230 * escala))
            p_surf = pygame.Surface((larg * 3, alt + 24), pygame.SRCALPHA)
            cx_s = p_surf.get_width() // 2
            pygame.draw.rect(p_surf, (56, 189, 248, 38), (cx_s - larg, 12, larg * 2, alt))
            pygame.draw.rect(p_surf, (125, 211, 252, 110), (cx_s - max(3, larg // 3), 12, max(6, (larg * 2) // 3), alt))
            pts_wave = []
            for wy in range(12, alt + 12, 8):
                wx = cx_s + int(math.sin((wy * 0.08) - self.tempo * 6.5 + z_mundo * 0.05) * larg * 0.65)
                pts_wave.append((wx, wy))
            if len(pts_wave) >= 2:
                pygame.draw.lines(p_surf, (224, 242, 254, 220), False, pts_wave, 2)
            superficie.blit(p_surf, (px - cx_s, py - alt))
            self._desenhar_fogo_bioma(superficie, px, py - alt // 2, escala, z_mundo * 0.1, com_arandela=False, chao_y_proj=py)
            return

        if tema == "fovea_lamentos":
            larg = max(10, int(36 * escala))
            alt = max(24, int(115 * escala))
            pulso = 0.55 + 0.45 * math.sin(self.tempo * 4.5 + z_mundo * 0.08)
            pts_c = [(px - larg // 2, py), (px - larg // 4, py - int(alt * 0.72)), (px, py - alt),
                     (px + larg // 3, py - int(alt * 0.65)), (px + larg // 2, py)]
            pygame.draw.polygon(superficie, (118, 16, 36), pts_c)
            pygame.draw.polygon(superficie, (244, 63, 94), pts_c, 2)
            self._desenhar_fogo_bioma(superficie, px, py - int(alt * 0.72), escala * (0.9 + 0.15 * pulso), z_mundo, com_arandela=False, chao_y_proj=py)
            return

        larg = max(12, int(34 * escala))
        alt = max(24, int((205 if tema in ("catedrais", "santuario_miasma") else 188) * escala))

        sombra_surf = pygame.Surface((larg * 2, max(6, larg // 2)), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra_surf, (5, 7, 12, 155), sombra_surf.get_rect())
        superficie.blit(sombra_surf, (px - larg, py - larg // 4))

        # Blita textura pré-gerada de alvenaria de pedra no fuste do pilar
        tex_pil = pygame.transform.scale(self._tex["pilar"], (larg, alt))
        superficie.blit(tex_pil, (px - larg // 2, py - alt))
        # Base chanfrada e capitel superior
        base_w = int(larg * 1.32)
        base_h = max(8, int(14 * escala))
        pygame.draw.rect(superficie, bio.cor_muralha, (px - base_w // 2, py - base_h, base_w, base_h))
        pygame.draw.rect(superficie, bio.cor_luz_laje, (px - base_w // 2, py - base_h, base_w, 2))
        pygame.draw.rect(superficie, bio.cor_sombra_laje, (px - base_w // 2, py - base_h, base_w, base_h), 1)
        pygame.draw.rect(superficie, bio.cor_muralha, (px - base_w // 2, py - alt, base_w, max(6, base_h - 3)))
        pygame.draw.rect(superficie, bio.cor_luz_laje, (px - base_w // 2, py - alt, base_w, max(6, base_h - 3)), 1)

        if tema == "santuario_miasma":
            pygame.draw.line(superficie, (212, 165, 58), (px, py - int(alt * 0.75)), (px, py - int(alt * 0.25)), 1)
            pygame.draw.circle(superficie, (212, 165, 58), (px, py - int(alt * 0.45)), max(3, int(6 * escala)), 1)

        tx, ty = px, py - int(alt * 0.64)
        self._desenhar_fogo_bioma(superficie, tx, ty, escala, z_mundo * 0.1, com_arandela=True, chao_y_proj=py)

    def _desenhar_elemento_z(self, superficie, camera, elem):
        tipo = elem["tipo"]
        px, py, esc = camera.projetar(elem["x"], self.y_chao, elem["z"])

        if tipo == "est_bandeira":
            h_mastro = max(24, int(145 * esc))
            pygame.draw.line(superficie, (82, 92, 112), (px, py), (px, py - h_mastro), max(2, int(4 * esc)))
            onda = int(math.sin(self.tempo * 3.8 + elem["fase"]) * max(2, 6 * esc))
            bw, bh = max(12, int(36 * esc)), max(20, int(64 * esc))
            pts_b = [
                (px, py - h_mastro + 6),
                (px + bw + onda, py - h_mastro + int(bh * 0.25)),
                (px + int(bw * 0.65) + onda, py - h_mastro + int(bh * 0.72)),
                (px + bw // 3, py - h_mastro + bh),
                (px, py - h_mastro + bh - 8),
            ]
            pygame.draw.polygon(superficie, (125, 22, 34), pts_b)
            pygame.draw.polygon(superficie, (212, 165, 58), pts_b, 1)

        elif tipo == "flecha":
            hl = max(8, int(24 * esc))
            dx = int(math.sin(elem["ang"]) * hl)
            dy = int(math.cos(elem["ang"]) * hl)
            pygame.draw.line(superficie, (132, 96, 56), (px, py), (px + dx, py - dy), max(1, int(2 * esc)))
            pygame.draw.circle(superficie, (203, 213, 225), (px + dx, py - dy), max(1, int(2 * esc)))

        elif tipo == "gargula":
            gw, gh = max(10, int(34 * esc)), max(12, int(38 * esc))
            pygame.draw.rect(superficie, (26, 22, 32), (px - gw // 2, py - int(95 * esc), gw, int(30 * esc)))
            pygame.draw.polygon(superficie, (18, 15, 24), [
                (px - gw // 2, py - int(95 * esc)),
                (px - gw, py - int(95 * esc) - gh),
                (px, py - int(95 * esc) - int(gh * 0.65)),
                (px + gw, py - int(95 * esc) - gh),
                (px + gw // 2, py - int(95 * esc)),
            ])
            pygame.draw.circle(superficie, (239, 68, 68), (px - 3, py - int(106 * esc)), max(1, int(2 * esc)))

        elif tipo == "estaca_ossos":
            hh = max(14, int(elem["h"] * esc))
            dx = int(math.sin(elem["inc"]) * hh)
            pygame.draw.line(superficie, (68, 42, 26), (px, py), (px + dx, py - hh), max(2, int(5 * esc)))
            pygame.draw.line(superficie, (200, 190, 170), (px - int(10 * esc), py - 2), (px + int(10 * esc), py - 5), max(1, int(3 * esc)))
            pygame.draw.circle(superficie, (214, 206, 188), (px + int(12 * esc), py - int(5 * esc)), max(2, int(5 * esc)))

        elif tipo == "espada_escudo":
            hl = max(12, int(36 * esc))
            dx = int(math.sin(elem["ang"]) * hl)
            pygame.draw.line(superficie, (148, 163, 184), (px, py), (px + dx, py - hl), max(2, int(3 * esc)))
            pygame.draw.line(superficie, (112, 92, 54), (px + int(dx * 0.7) - 6, py - int(hl * 0.7)), (px + int(dx * 0.7) + 6, py - int(hl * 0.7)), max(2, int(3 * esc)))
            if elem.get("tem_escudo", False):
                er = max(5, int(13 * esc))
                pygame.draw.ellipse(superficie, (72, 62, 68), (px - er, py - er, er * 2, int(er * 1.4)))
                pygame.draw.ellipse(superficie, (110, 98, 108), (px - er, py - er, er * 2, int(er * 1.4)), 1)

        elif tipo == "pedestal_decap":
            pw, ph = max(14, int(42 * esc)), max(18, int(58 * esc))
            pygame.draw.rect(superficie, (44, 50, 62), (px - pw // 2, py - ph, pw, ph))
            pygame.draw.rect(superficie, (22, 26, 34), (px - pw // 2, py - ph, pw, ph), 2)
            pygame.draw.polygon(superficie, (60, 68, 82), [
                (px - pw // 3, py - ph), (px - pw // 4, py - ph - int(32 * esc)),
                (px + pw // 5, py - ph - int(24 * esc)), (px + pw // 3, py - ph),
            ])
            pygame.draw.rect(superficie, (38, 44, 54), (px + pw // 2, py - int(14 * esc), int(18 * esc), int(14 * esc)))

        elif tipo == "orbe_sangue":
            oy = elem["y_base"] + math.sin(self.tempo * 2.6 + elem["fase"]) * 16.0
            ox_t, oy_t, o_esc = camera.projetar(elem["x"], oy, elem["z"])
            r_o = max(4, int(11 * o_esc))
            o_s = pygame.Surface((r_o * 4, r_o * 4), pygame.SRCALPHA)
            pygame.draw.circle(o_s, (225, 29, 72, 60), (r_o * 2, r_o * 2), r_o * 2)
            pygame.draw.circle(o_s, (244, 63, 94, 215), (r_o * 2, r_o * 2), r_o)
            pygame.draw.circle(o_s, (254, 205, 211, 230), (r_o * 2 - max(1, r_o // 3), r_o * 2 - max(1, r_o // 3)), max(1, r_o // 3))
            superficie.blit(o_s, (ox_t - r_o * 2, oy_t - r_o * 2))

        elif tipo == "frag_flutuante":
            fy = elem["y_base"] - ((self.tempo * 14.0 * elem["vel"] + elem["fase"] * 12.0) % 140.0)
            fx_t, fy_t, f_esc = camera.projetar(elem["x"], fy, elem["z"])
            ft = max(4, int(elem["tam"] * f_esc))
            pts_f = [(fx_t, fy_t - ft), (fx_t + ft, fy_t), (fx_t, fy_t + int(ft * 0.7)), (fx_t - ft, fy_t)]
            pygame.draw.polygon(superficie, (18, 28, 52), pts_f)
            pygame.draw.polygon(superficie, (56, 189, 248), pts_f, 1)

    def _desenhar_candelabros_suspensos(self, superficie, camera):
        if self.bioma.tema_id != "santuario_miasma":
            return
        for cx_m, cz_m in ((-280.0, 75.0), (0.0, 120.0), (280.0, 75.0)):
            px, py, esc = camera.projetar(cx_m, -92.0, cz_m)
            cw = max(24, int(74 * esc))
            pygame.draw.line(superficie, (68, 56, 44), (px, 0), (px, py), max(1, int(2 * esc)))
            pygame.draw.line(superficie, (212, 165, 58), (px - cw // 2, py), (px + cw // 2, py), max(2, int(3 * esc)))
            for off_v in (-cw // 2, 0, cw // 2):
                self._desenhar_fogo_bioma(superficie, px + off_v, py - max(3, int(6 * esc)), esc * 0.85, off_v, com_arandela=False)

    def desenhar_sombra_entidade(self, superficie, camera, x_mundo, z_mundo, raio_base=20, altura_pulo=0.0):
        sx, sy, escala = camera.projetar(x_mundo, self.y_chao, z_mundo)
        fator_pulo = max(0.45, 1.0 - abs(altura_pulo) / 220.0)
        larg = max(10, int(raio_base * 1.85 * escala * fator_pulo))
        alt = max(4, int(raio_base * 0.55 * escala * fator_pulo))
        sombra = pygame.Surface((larg, alt), pygame.SRCALPHA)
        alpha_s = 110 if self.bioma.tema_id == "vazio_absoluto" else 150
        pygame.draw.ellipse(sombra, (4, 6, 12, int(alpha_s * fator_pulo)), (0, 0, larg, alt))
        superficie.blit(sombra, (sx - larg // 2, sy - alt // 2))

    def desenhar_completo(self, superficie, camera, combatentes):
        self._desenhar_ceu_e_fundo_paralaxe(superficie, camera)
        self._desenhar_muralha_horizonte(superficie, camera)
        self._desenhar_piso_trapezio_3d(superficie, camera)
        self._desenhar_candelabros_suspensos(superficie, camera)

        for c in combatentes:
            y_off = getattr(c, "y_offset", 0.0)
            raio = getattr(c, "raio_mira", 20)
            self.desenhar_sombra_entidade(superficie, camera, c.x_mundo, c.z_mundo, raio, altura_pulo=y_off)

        fila_render = []
        for z_pilar in self.pilares_z:
            fila_render.append(("PILAR", z_pilar, (-self.largura_mundo * 0.85, z_pilar)))
            fila_render.append(("PILAR", z_pilar, (self.largura_mundo * 0.85, z_pilar)))

        for elem in self._elementos_z:
            fila_render.append(("ELEM_Z", elem["z"], elem))

        for p in self.particulas:
            fila_render.append(("PARTICULA", p["z"], p))

        for c in combatentes:
            fila_render.append(("COMBATENTE", c.z_mundo, c))

        fila_render.sort(key=lambda item: item[1], reverse=True)

        for tipo, _, obj in fila_render:
            if tipo == "PILAR":
                self._desenhar_pilar_lateral(superficie, camera, obj[0], obj[1])
            elif tipo == "ELEM_Z":
                self._desenhar_elemento_z(superficie, camera, obj)
            elif tipo == "PARTICULA":
                px, py, pesc = camera.projetar(obj["x"], obj["y"], obj["z"])
                pygame.draw.circle(superficie, obj["cor"], (px, py), max(1, int(obj["raio"] * pesc)))
            elif tipo == "COMBATENTE":
                tx, ty, esc = camera.projetar(obj.x_mundo, self.y_chao + getattr(obj, "y_offset", 0.0), obj.z_mundo)
                obj.tela_x = tx
                obj.tela_y = ty
                obj.escala_atual = esc
                if hasattr(obj, "desenhar_25d"):
                    obj.desenhar_25d(superficie, tx, ty, esc)
