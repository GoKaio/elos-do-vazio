# -*- coding: utf-8 -*-
"""
Motor Cinematográfico de Cutscenes - Elos do Vazio.

Inspirado na direção de arte refinada e minimalista de Clair Obscur: Expedition 33:
  - Barras letterbox pretas deslizantes (52 px) com filete dourado (#B45309) de 1 px.
  - Camadas parallax de ruínas góticas, lua pálida, névoa rasteira e esporos de Éter.
  - Vinheta cinematográfica e vitrine/silhueta do orador com rim-light suave (SRCALPHA puro).
  - Sistema de roteiro temporal (orador, texto, duracao, tempo_fade) com efeito
    máquina de escrever, quebra de linha automática, fonte serif dourada com sombra,
    gema de Éter pulsante ([ESPAÇO]) e skip rápido ([ESC]).
  - Integração segura com SFX (audio.py) e transição suave fade-to-black.
"""

import math
import random
import pygame

import ui_procedural as uip

try:
    import audio
except Exception:
    audio = None


ALTURA_LETTERBOX = 52
COR_BORDA_LETTERBOX = uip.COR_OURO_DIVISOR   # #B45309 (180, 83, 9)
COR_TEXTO_DOURADO = uip.COR_OURO_VIVO        # #FDE68A (253, 230, 138)
COR_TEXTO_ESCURO = (6, 8, 16)
COR_SKIP = (100, 116, 139)                   # #64748B


def _tocar_sfx_seguro(nome, volume=0.45):
    if audio is None:
        return
    try:
        if hasattr(audio, "tocar_sfx"):
            audio.tocar_sfx(nome, mult_volume=volume)
    except Exception:
        pass


def _quebrar_linhas(texto, fonte, largura_max):
    palavras = str(texto or "").split()
    if not palavras:
        return []
    linhas = []
    atual = palavras[0]
    for p in palavras[1:]:
        teste = f"{atual} {p}"
        if fonte.size(teste)[0] <= largura_max:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


class GerenciadorCutscenes:
    """Controlador reutilizável de sequências narrativas cinematográficas (960x540 nativo)."""

    def __init__(
        self,
        roteiro,
        callback_fim=None,
        anim_heroi=None,
        fundo_modo="cidadela",
        titulo_cena="",
        auto_avancar=True,
    ):
        self.roteiro = list(roteiro or [])
        self.callback_fim = callback_fim
        self.anim_heroi = anim_heroi
        self.fundo_modo = str(fundo_modo or "cidadela").lower()
        self.titulo_cena = str(titulo_cena or "")
        self.auto_avancar = bool(auto_avancar)

        self.indice = 0
        self.tempo_total = 0.0
        self.tempo_slide = 0.0
        self.fase = "ENTRADA"   # ENTRADA -> DIGITANDO -> PAUSA -> SAIDA_SLIDE -> FADE_OUT -> FIM
        self.alfa_cena = 0.0    # 0 = preto, 1 = visível
        self.alfa_texto = 0.0
        self.progresso_barras = 0.0
        self.progresso_digitacao = 0.0
        self.velocidade_chars = 46.0
        self.skip_rapido = False
        self.concluida = False
        self._callback_disparado = False
        self._sfx_tocado_slide = -1

        # Partículas atmosféricas (esporos de Éter ciano e cinzas suaves)
        rng = random.Random(3301)
        self._particulas = []
        for i in range(68):
            tipo = "eter" if i % 4 == 0 else "cinza"
            self._particulas.append({
                "x": rng.uniform(0.0, 960.0),
                "y": rng.uniform(55.0, 485.0),
                "vx": rng.uniform(-14.0, 12.0),
                "vy": rng.uniform(-24.0, -7.0),
                "tam": rng.choice((1, 2, 2, 3)),
                "tipo": tipo,
                "fase": rng.uniform(0.0, math.tau),
                "alfa_base": rng.randint(85, 200),
            })

        # Camadas estáticas em cache por dimensão/modo
        self._cache_dim = None
        self._surf_fundo = None
        self._surf_silhuetas_bg = None
        self._surf_silhuetas_fg = None
        self._surf_vinheta = None
        self._surf_halo_eter = None
        self._surf_halo_ouro = None

    def _passo_atual(self):
        if 0 <= self.indice < len(self.roteiro):
            return self.roteiro[self.indice]
        return None

    def _garantir_cache(self, w, h, modo):
        chave = (int(w), int(h), str(modo))
        if self._cache_dim == chave and self._surf_fundo is not None:
            return
        self._cache_dim = chave

        # 1) Gradiente noturno/aurora + lua pálida (SRCALPHA sem BLEND_ADD)
        s_bg = pygame.Surface((w, h)).convert()
        if modo == "aurora":
            top_c, mid_c, bot_c = (12, 16, 28), (30, 36, 56), (18, 22, 32)
            cor_lua = (254, 243, 199)
        elif modo in ("subterraneo", "abismo"):
            top_c, mid_c, bot_c = (5, 7, 13), (12, 14, 24), (8, 9, 16)
            cor_lua = (148, 163, 184)
        else:
            top_c, mid_c, bot_c = (7, 9, 18), (16, 22, 38), (11, 13, 22)
            cor_lua = (226, 232, 240)

        meio = int(h * 0.62)
        for py in range(h):
            if py < meio:
                t = py / float(max(1, meio))
                cor = (
                    int(top_c[0] + (mid_c[0] - top_c[0]) * t),
                    int(top_c[1] + (mid_c[1] - top_c[1]) * t),
                    int(top_c[2] + (mid_c[2] - top_c[2]) * t),
                )
            else:
                t = (py - meio) / float(max(1, h - meio))
                cor = (
                    int(mid_c[0] + (bot_c[0] - mid_c[0]) * t),
                    int(mid_c[1] + (bot_c[1] - mid_c[1]) * t),
                    int(mid_c[2] + (bot_c[2] - mid_c[2]) * t),
                )
            pygame.draw.line(s_bg, cor, (0, py), (w, py))

        # Estrelas discretas e lua pálida com halo suave SRCALPHA
        rng = random.Random(7711)
        if modo != "subterraneo":
            for _ in range(75):
                sx = rng.randint(12, w - 12)
                sy = rng.randint(40, int(h * 0.56))
                br = rng.randint(70, 155)
                s_bg.set_at((sx, sy), (br, br + 6, min(255, br + 18)))

            lx, ly = int(w * 0.74), int(h * 0.25)
            s_lua = pygame.Surface((260, 260), pygame.SRCALPHA)
            for rad, alf in ((120, 10), (88, 18), (64, 30), (48, 52)):
                pygame.draw.circle(s_lua, (*cor_lua, alf), (130, 130), rad)
            pygame.draw.circle(s_lua, (*cor_lua, 215), (130, 130), 34)
            # Crateras tênues
            pygame.draw.circle(s_lua, (185, 194, 212, 65), (120, 122), 8)
            pygame.draw.circle(s_lua, (185, 194, 212, 55), (140, 136), 6)
            s_bg.blit(s_lua, (lx - 130, ly - 130))

        self._surf_fundo = s_bg

        # 2) Silhuetas parallax distantes (ruínas, pináculos e arcos partidos)
        s_far = pygame.Surface((w * 2, h), pygame.SRCALPHA)
        cor_far = (14, 18, 30, 200) if modo != "subterraneo" else (12, 13, 22, 220)
        cor_linha_far = (34, 42, 64, 110)
        hor_far = int(h * 0.68)
        pygame.draw.rect(s_far, cor_far, (0, hor_far, w * 2, h - hor_far))
        px = 0
        rng_r = random.Random(4202)
        while px < w * 2:
            larg_t = rng_r.randint(44, 96)
            alt_t = rng_r.randint(68, 168)
            topo = hor_far - alt_t
            pygame.draw.rect(s_far, cor_far, (px, topo, larg_t, alt_t + 8))
            if px % 3 == 0:
                # Pináculo gótico quebrado
                pts = [(px, topo), (px + larg_t // 2, topo - 36), (px + larg_t, topo)]
                pygame.draw.polygon(s_far, cor_far, pts)
            else:
                # Ameias de muralha antiga
                for mx in range(px, px + larg_t - 10, 16):
                    pygame.draw.rect(s_far, cor_far, (mx, topo - 10, 9, 10))
            pygame.draw.line(s_far, cor_linha_far, (px, topo), (px + larg_t, topo), 1)
            px += larg_t + rng_r.randint(24, 62)
        self._surf_silhuetas_bg = s_far.convert_alpha()

        # 3) Silhuetas médias (colunas quebradas, lápides e arcos góticos)
        s_mid = pygame.Surface((w * 2, h), pygame.SRCALPHA)
        cor_mid = (9, 11, 19, 235)
        cor_bevel = (48, 56, 82, 95)
        hor_mid = int(h * 0.74)
        pygame.draw.rect(s_mid, cor_mid, (0, hor_mid, w * 2, h - hor_mid))
        mx = 20
        while mx < w * 2:
            if (mx // 70) % 3 == 0:
                # Arco de ruína partida
                aw = 76
                pygame.draw.rect(s_mid, cor_mid, (mx, hor_mid - 118, 14, 118))
                pygame.draw.rect(s_mid, cor_mid, (mx + aw - 14, hor_mid - 104, 14, 104))
                pygame.draw.arc(s_mid, cor_mid, (mx, hor_mid - 144, aw, 54), 0.15, math.pi * 0.88, 12)
                pygame.draw.line(s_mid, cor_bevel, (mx, hor_mid - 118), (mx, hor_mid), 1)
                mx += aw + 72
            else:
                # Coluna partida / obelisco
                cw = rng_r.randint(20, 34)
                ch = rng_r.randint(60, 130)
                pygame.draw.rect(s_mid, cor_mid, (mx, hor_mid - ch, cw, ch))
                pygame.draw.line(s_mid, cor_bevel, (mx, hor_mid - ch), (mx + cw, hor_mid - ch + 5), 1)
                mx += cw + rng_r.randint(52, 98)
        self._surf_silhuetas_fg = s_mid.convert_alpha()

        # 4) Vinheta cinematográfica escura nos cantos e laterais
        s_vin = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(28):
            passo = i / 27.0
            a_borda = int(175 * (1.0 - passo) ** 1.65)
            esp_x = max(1, int(w * 0.0085))
            esp_y = max(1, int(h * 0.0085))
            rect_b = pygame.Rect(i * esp_x, i * esp_y, max(2, w - 2 * i * esp_x), max(2, h - 2 * i * esp_y))
            pygame.draw.rect(s_vin, (3, 4, 9, a_borda), rect_b, width=max(esp_x, esp_y))
        self._surf_vinheta = s_vin.convert_alpha()

        # 5) Halos suaves para rim-light (SRCALPHA puro)
        s_he = pygame.Surface((160, 160), pygame.SRCALPHA)
        for rad, alf in ((74, 14), (50, 26), (28, 42)):
            pygame.draw.circle(s_he, (*uip.COR_AZUL_ETER, alf), (80, 80), rad)
        self._surf_halo_eter = s_he.convert_alpha()

        s_ho = pygame.Surface((160, 160), pygame.SRCALPHA)
        for rad, alf in ((74, 12), (50, 22), (28, 36)):
            pygame.draw.circle(s_ho, (*uip.COR_OURO_BRILHO, alf), (80, 80), rad)
        self._surf_halo_ouro = s_ho.convert_alpha()

    def avancar_ato(self):
        """Completa a digitação atual ou avança suavemente para o próximo quadro do roteiro."""
        if self.concluida or self.fase in ("FADE_OUT", "FIM"):
            return
        passo = self._passo_atual()
        if passo is None:
            self.fase = "FADE_OUT"
            return

        texto_alvo = str(passo.get("texto", ""))
        if self.fase == "DIGITANDO" and self.progresso_digitacao < len(texto_alvo):
            self.progresso_digitacao = float(len(texto_alvo))
            self.fase = "PAUSA"
            self.tempo_slide = 0.0
            _tocar_sfx_seguro("passo", 0.35)
            return

        _tocar_sfx_seguro("passo", 0.45)
        if self.indice + 1 < len(self.roteiro):
            self.fase = "SAIDA_SLIDE"
            self.tempo_slide = 0.0
        else:
            self.fase = "FADE_OUT"
            self.tempo_slide = 0.0

    def pular(self):
        """Ativa o fade-out acelerado para encerrar a cutscene imediatamente."""
        if self.concluida or self.fase == "FIM":
            return
        self.skip_rapido = True
        self.fase = "FADE_OUT"
        _tocar_sfx_seguro("passo", 0.35)

    def handle_keydown(self, key):
        if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_z):
            self.avancar_ato()
            return True
        if key == pygame.K_ESCAPE:
            self.pular()
            return True
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            return self.handle_keydown(event.key)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.avancar_ato()
            return True
        return False

    def _atualizar_particulas(self, dt, w, h):
        for p in self._particulas:
            p["x"] += (p["vx"] + math.sin(self.tempo_total * 1.1 + p["fase"]) * 6.0) * dt
            p["y"] += p["vy"] * dt
            if p["y"] < ALTURA_LETTERBOX - 6:
                p["y"] = float(h - ALTURA_LETTERBOX + 4)
                p["x"] = (p["x"] + 137.0) % max(1, w)
            if p["x"] < -10:
                p["x"] += w + 20
            elif p["x"] > w + 10:
                p["x"] -= w + 20

    def update(self, dt):
        dt = max(0.0, min(0.08, float(dt)))
        self.tempo_total += dt
        self._atualizar_particulas(dt, 960, 540)

        # Deslizamento suave das barras letterbox 52 px
        if self.fase != "FADE_OUT":
            self.progresso_barras = min(1.0, self.progresso_barras + dt / 0.65)
        elif self.skip_rapido:
            self.progresso_barras = max(0.0, self.progresso_barras - dt / 0.35)

        passo = self._passo_atual()
        tempo_fade = max(0.20, float((passo or {}).get("tempo_fade", 0.55)))

        if self.fase == "ENTRADA":
            self.alfa_cena = min(1.0, self.alfa_cena + dt / 0.70)
            self.alfa_texto = min(1.0, self.alfa_texto + dt / tempo_fade)
            if passo and self._sfx_tocado_slide != self.indice:
                self._sfx_tocado_slide = self.indice
                sfx = passo.get("sfx")
                if sfx:
                    _tocar_sfx_seguro(sfx, 0.55)
            if self.alfa_cena >= 0.98:
                self.alfa_cena = 1.0
                self.fase = "DIGITANDO"
                self.tempo_slide = 0.0

        elif self.fase == "DIGITANDO":
            self.alfa_cena = 1.0
            self.alfa_texto = min(1.0, self.alfa_texto + dt / tempo_fade)
            if passo and self._sfx_tocado_slide != self.indice:
                self._sfx_tocado_slide = self.indice
                sfx = passo.get("sfx")
                if sfx:
                    _tocar_sfx_seguro(sfx, 0.55)
            txt = str((passo or {}).get("texto", ""))
            self.progresso_digitacao = min(float(len(txt)), self.progresso_digitacao + self.velocidade_chars * dt)
            if self.progresso_digitacao >= len(txt):
                self.fase = "PAUSA"
                self.tempo_slide = 0.0

        elif self.fase == "PAUSA":
            self.alfa_cena = 1.0
            self.alfa_texto = 1.0
            self.tempo_slide += dt
            dur = float((passo or {}).get("duracao", 5.2))
            if self.auto_avancar and dur > 0.0 and self.tempo_slide >= dur:
                if self.indice + 1 < len(self.roteiro):
                    self.fase = "SAIDA_SLIDE"
                    self.tempo_slide = 0.0
                else:
                    self.fase = "FADE_OUT"
                    self.tempo_slide = 0.0

        elif self.fase == "SAIDA_SLIDE":
            self.alfa_texto = max(0.0, self.alfa_texto - dt / max(0.22, tempo_fade * 0.65))
            if self.alfa_texto <= 0.02:
                self.indice += 1
                self.progresso_digitacao = 0.0
                self.tempo_slide = 0.0
                if self.indice >= len(self.roteiro):
                    self.fase = "FADE_OUT"
                else:
                    self.fase = "DIGITANDO"
                    nxt = self._passo_atual()
                    if nxt and nxt.get("fundo"):
                        self.fundo_modo = str(nxt.get("fundo")).lower()

        elif self.fase == "FADE_OUT":
            vel_fade = 3.2 if self.skip_rapido else 1.25
            self.alfa_texto = max(0.0, self.alfa_texto - vel_fade * 1.4 * dt)
            self.alfa_cena = max(0.0, self.alfa_cena - vel_fade * dt)
            if self.alfa_cena <= 0.01:
                self.alfa_cena = 0.0
                self.fase = "FIM"
                self.concluida = True
                if not self._callback_disparado and callable(self.callback_fim):
                    self._callback_disparado = True
                    self.callback_fim()

        return self.concluida

    def _desenhar_nevoa(self, surface, w, h):
        s_neb = pygame.Surface((w, 120), pygame.SRCALPHA)
        for faixa in range(3):
            y_f = 22 + faixa * 28
            desloc = math.sin(self.tempo_total * (0.35 + faixa * 0.14) + faixa * 1.7) * 42.0
            for gx in range(-80, w + 120, 140):
                rx = int(gx + desloc)
                rw = 210 + (faixa * 35)
                pygame.draw.ellipse(s_neb, (148, 163, 184, 12 + faixa * 4), (rx, y_f, rw, 44))
        surface.blit(s_neb, (0, h - ALTURA_LETTERBOX - 135))

    def _desenhar_silhueta_orador(self, surface, w, h, passo):
        tipo = str((passo or {}).get("silhueta", "")).lower()
        orador_l = str((passo or {}).get("orador", "")).lower()
        if not tipo:
            if "kaelen" in orador_l or "her" in orador_l or "viaj" in orador_l or "cavaleiro" in orador_l:
                tipo = "heroi"
            elif "or" in orador_l or "eco" in orador_l or "sombra" in orador_l or "vazio" in orador_l:
                tipo = "oraculo"
            elif "guard" in orador_l or "chefe" in orador_l or "rei" in orador_l:
                tipo = "guardiao"
            else:
                return

        cx = int(w * 0.5)
        cy = int(h - ALTURA_LETTERBOX - 178)
        pulso = 0.5 + 0.5 * math.sin(self.tempo_total * 2.2)

        # Halo rim-light atrás da silhueta (SRCALPHA normal, zero BLEND_ADD)
        halo = self._surf_halo_ouro if tipo == "guardiao" else self._surf_halo_eter
        if halo is not None:
            surface.blit(halo, (cx - 80, cy - 92))

        if tipo == "heroi" and self.anim_heroi is not None:
            try:
                pers = getattr(self.anim_heroi, "personagem", self.anim_heroi)
                if hasattr(pers, "quadro") and hasattr(pers, "anims") and "idle" in pers.anims:
                    quadros = pers.anims["idle"]
                    if quadros:
                        idx_q = int(self.tempo_total * 7.0) % len(quadros)
                        img_q, _ = pers.quadro("idle", idx_q, 2.5, False)
                        pe_y = cy + 62
                        s_pe = pygame.Surface((68, 16), pygame.SRCALPHA)
                        pygame.draw.ellipse(s_pe, (4, 6, 12, 135), (0, 0, 68, 16))
                        surface.blit(s_pe, (cx - 34, pe_y - 8))
                        surface.blit(img_q, (cx - img_q.get_width() // 2, pe_y - img_q.get_height()))
                        return
            except Exception:
                pass

        # Silhueta estilizada gótica com recorte luminoso (rim light)
        s_sil = pygame.Surface((140, 160), pygame.SRCALPHA)
        cor_corpo = (10, 12, 22, 240)
        cor_rim = uip.COR_AZUL_ETER if tipo in ("heroi", "oraculo") else uip.COR_OURO_BRILHO
        cor_rim_a = (*cor_rim, int(130 + 60 * pulso))

        if tipo == "oraculo":
            # Manto esvoaçante + capuz encimado por runa de Éter
            manto = [(70, 34), (42, 74), (28, 148), (112, 148), (98, 74)]
            pygame.draw.polygon(s_sil, cor_corpo, manto)
            pygame.draw.circle(s_sil, cor_corpo, (70, 38), 16)
            pygame.draw.lines(s_sil, cor_rim_a, False, [(42, 74), (70, 22), (98, 74)], 2)
            # Olhos/visor de éter tênue
            pygame.draw.circle(s_sil, (*uip.COR_AZUL_ETER_CLARO, 210), (65, 39), 2)
            pygame.draw.circle(s_sil, (*uip.COR_AZUL_ETER_CLARO, 210), (75, 39), 2)
        elif tipo == "guardiao":
            # Grande armadura com elmo de chifres / coroa quebrada e alabarda
            pygame.draw.rect(s_sil, cor_corpo, (42, 56, 56, 92), border_radius=4)
            pygame.draw.rect(s_sil, cor_corpo, (54, 28, 32, 30), border_radius=6)
            pygame.draw.polygon(s_sil, cor_corpo, [(54, 34), (44, 14), (58, 28)])
            pygame.draw.polygon(s_sil, cor_corpo, [(86, 34), (96, 14), (82, 28)])
            pygame.draw.line(s_sil, cor_rim_a, (108, 16), (108, 150), 2)
            pygame.draw.polygon(s_sil, cor_rim_a, [(108, 14), (120, 32), (108, 42)])
            pygame.draw.rect(s_sil, (*uip.COR_OURO_VIVO, 185), (60, 41, 20, 3))
        else:
            # Cavaleiro solitário em vigília com capa e espada embainhada
            capa = [(60, 52), (34, 142), (96, 144), (84, 54)]
            pygame.draw.polygon(s_sil, cor_corpo, capa)
            pygame.draw.rect(s_sil, cor_corpo, (54, 48, 30, 86), border_radius=3)
            pygame.draw.circle(s_sil, cor_corpo, (69, 34), 13)
            pygame.draw.lines(s_sil, cor_rim_a, False, [(56, 32), (69, 21), (82, 32)], 2)
            pygame.draw.line(s_sil, cor_rim_a, (48, 86), (92, 54), 2)

        surface.blit(s_sil, (cx - 70, cy - 78))

    def draw(self, surface):
        w, h = surface.get_size()
        modo = str((self._passo_atual() or {}).get("fundo") or self.fundo_modo).lower()
        self._garantir_cache(w, h, modo)

        # 1) Fundo noturno + lua pálida
        surface.blit(self._surf_fundo, (0, 0))

        # 2) Parallax contínuo lento das ruínas distantes e arcos médios
        off_far = int((self.tempo_total * 8.0) % w)
        off_mid = int((self.tempo_total * 16.0) % w)
        if self._surf_silhuetas_bg is not None:
            surface.blit(self._surf_silhuetas_bg, (-off_far, 0))
        if self._surf_silhuetas_fg is not None:
            surface.blit(self._surf_silhuetas_fg, (-off_mid, 0))

        # 3) Névoa rasteira translúcida
        self._desenhar_nevoa(surface, w, h)

        # 4) Silhueta / Sprite com rim-light sutil do orador
        self._desenhar_silhueta_orador(surface, w, h, self._passo_atual())

        # 5) Partículas (esporos de Éter ciano + cinzas)
        for p in self._particulas:
            px, py = int(p["x"] % max(1, w)), int(p["y"])
            if py < ALTURA_LETTERBOX or py > h - ALTURA_LETTERBOX:
                continue
            cor_b = uip.COR_AZUL_ETER if p["tipo"] == "eter" else uip.COR_CINZA_TEXTO
            if p["tipo"] == "eter":
                pygame.draw.circle(surface, cor_b, (px, py), p["tam"])
                if p["tam"] >= 2:
                    pygame.draw.circle(surface, uip.COR_AZUL_ETER_CLARO, (px, py), 1)
            else:
                pygame.draw.rect(surface, cor_b, (px, py, p["tam"], p["tam"]))

        # 6) Vinheta escura cinematográfica
        if self._surf_vinheta is not None:
            surface.blit(self._surf_vinheta, (0, 0))

        # 7) Caixa narrativa centralizada acima da barra inferior
        passo = self._passo_atual()
        if passo and self.alfa_texto > 0.03:
            alfa_u8 = int(max(0, min(255, self.alfa_texto * 255)))
            box_w = min(760, w - 80)
            box_h = 126
            box_x = (w - box_w) // 2
            box_y = h - ALTURA_LETTERBOX - box_h - 14

            # Painel escuro gótico translúcido com moldura de ui_procedural
            uip.desenhar_moldura_gotica(
                surface, box_x, box_y, box_w, box_h,
                chanfro=8, destacado=False, alpha=int(215 * self.alfa_texto),
                borda_ouro=True, cantoneiras=True, cranios=False,
            )

            orador = str(passo.get("orador", "Narrador")).strip()
            f_orador = uip.obter_fonte_serif(13, bold=True)
            cor_orador = uip.COR_AZUL_ETER if any(k in orador.lower() for k in ("or", "eco", "vazio")) else COR_TEXTO_DOURADO

            # Orador centralizado + divisor dourado ornamental
            s_ora_sh = f_orador.render(orador.upper(), True, COR_TEXTO_ESCURO)
            s_ora = f_orador.render(orador.upper(), True, cor_orador)
            s_ora_sh.set_alpha(alfa_u8)
            s_ora.set_alpha(alfa_u8)
            ox = box_x + (box_w - s_ora.get_width()) // 2
            surface.blit(s_ora_sh, (ox + 1, box_y + 11))
            surface.blit(s_ora, (ox, box_y + 10))
            uip.desenhar_divisor_dourado(surface, box_x + 70, box_y + 31, box_w - 140)

            # Texto serif dourado (#FDE68A) com sombra e quebra automática
            f_txt = uip.obter_fonte_serif(17, bold=False)
            texto_total = str(passo.get("texto", ""))
            visivel = texto_total[:int(self.progresso_digitacao)]
            linhas = _quebrar_linhas(visivel, f_txt, box_w - 64)
            y_txt = box_y + 42
            for idx_l, linha in enumerate(linhas[:3]):
                s_sh = f_txt.render(linha, True, COR_TEXTO_ESCURO)
                s_tx = f_txt.render(linha, True, COR_TEXTO_DOURADO)
                s_sh.set_alpha(alfa_u8)
                s_tx.set_alpha(alfa_u8)
                lx = box_x + (box_w - s_tx.get_width()) // 2
                ly = y_txt + idx_l * 24
                surface.blit(s_sh, (lx + 1, ly + 1))
                surface.blit(s_tx, (lx, ly))

            # Gema de Éter pulsante + prompt [ESPAÇO] no canto inferior direito do painel
            pronto = (self.progresso_digitacao >= len(texto_total))
            pulso_gema = (math.sin(self.tempo_total * 5.2) > -0.25) if pronto else False
            f_hint = uip.obter_fonte_serif(11, bold=True)
            txt_hint = "Continuar" if pronto else "Revelar"
            s_hint = f_hint.render(txt_hint, True, uip.COR_AZUL_ETER_CLARO if pronto else uip.COR_CINZA_TEXTO)
            s_hint.set_alpha(alfa_u8)
            hx = box_x + box_w - s_hint.get_width() - 16
            hy = box_y + box_h - 22
            ic_h = uip.desenhar_icone_botao(surface, hx - 26, hy + 7, "ESPACO", escala=0.82)
            uip.desenhar_cristal_eter(surface, ic_h.left - 10, hy + 7, tamanho=4, ativo=bool(pronto and pulso_gema))
            surface.blit(s_hint, (hx, hy))

        # 8) Barras letterbox pretas deslizantes (52 px) + filete #B45309 de 1 px
        alt_barra = int(round(ALTURA_LETTERBOX * self.progresso_barras))
        if alt_barra > 0:
            pygame.draw.rect(surface, (0, 0, 0), (0, 0, w, alt_barra))
            pygame.draw.line(surface, COR_BORDA_LETTERBOX, (0, alt_barra - 1), (w, alt_barra - 1), 1)
            pygame.draw.rect(surface, (0, 0, 0), (0, h - alt_barra, w, alt_barra))
            pygame.draw.line(surface, COR_BORDA_LETTERBOX, (0, h - alt_barra), (w, h - alt_barra), 1)

        # Título do ato discreto à esquerda na barra superior + [ESC] Pular à direita
        if alt_barra >= 28:
            f_bar = uip.obter_fonte_serif(12, bold=True)
            titulo = (passo or {}).get("titulo_ato") or self.titulo_cena
            if titulo:
                s_tit = f_bar.render(str(titulo).upper(), True, uip.COR_CINZA_TEXTO)
                surface.blit(s_tit, (22, max(6, (alt_barra - s_tit.get_height()) // 2)))
            s_esc = f_bar.render("Pular", True, COR_SKIP)
            ey = max(6, (alt_barra - s_esc.get_height()) // 2)
            ex = w - s_esc.get_width() - 22
            uip.desenhar_icone_botao(surface, ex - 20, ey + s_esc.get_height() // 2, "CANCELAR", escala=0.80)
            surface.blit(s_esc, (ex, ey))

        # 9) Cortina preta final de fade-in / fade-out
        if self.alfa_cena < 0.995:
            alfa_escuro = int(max(0, min(255, (1.0 - self.alfa_cena) * 255)))
            s_fade = pygame.Surface((w, h), pygame.SRCALPHA)
            s_fade.fill((0, 0, 0, alfa_escuro))
            surface.blit(s_fade, (0, 0))


MotorCutscene = GerenciadorCutscenes
