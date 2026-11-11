# -*- coding: utf-8 -*-
"""
Animação simples de abertura do estúdio (GoZygrid STUDIOS) ao iniciar o jogo.

Exibe o emblema do estúdio com entrada e saída suaves sobre fundo escuro,
sem efeitos de luz ou brilhos exagerados, antes de revelar o menu principal.
"""

import os
import pygame

from caminhos import obter_caminho_recurso, log_aviso
import ui_procedural

COR_FUNDO_SPLASH = (10, 10, 14)


def _suavizar_bordas_surface(surface, margem_x=110, margem_y=22):
    """Aplica fade suave apenas nas extremidades externas para integrar ao fundo."""
    w, h = surface.get_size()
    resultado = surface.convert_alpha()

    if margem_x > 0 and w > margem_x * 2:
        mascara_h = pygame.Surface((w, h), pygame.SRCALPHA)
        mascara_h.fill((255, 255, 255, 255))
        for x in range(margem_x):
            t = (x + 0.5) / float(margem_x)
            alfa = int(255 * (t * t * (3.0 - 2.0 * t)))
            pygame.draw.line(mascara_h, (255, 255, 255, alfa), (x, 0), (x, h - 1))
            pygame.draw.line(mascara_h, (255, 255, 255, alfa), (w - 1 - x, 0), (w - 1 - x, h - 1))
        resultado.blit(mascara_h, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    if margem_y > 0 and h > margem_y * 2:
        mascara_v = pygame.Surface((w, h), pygame.SRCALPHA)
        mascara_v.fill((255, 255, 255, 255))
        for y in range(margem_y):
            t = (y + 0.5) / float(margem_y)
            alfa = int(255 * (t * t * (3.0 - 2.0 * t)))
            pygame.draw.line(mascara_v, (255, 255, 255, alfa), (0, y), (w - 1, y))
            pygame.draw.line(mascara_v, (255, 255, 255, alfa), (0, h - 1 - y), (w - 1, h - 1 - y))
        resultado.blit(mascara_v, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return resultado


class AnimacaoAberturaEstudio:
    """Splash screen simples e discreta exibida ao abrir o executável."""

    DURACAO_ENTRADA = 0.80
    DURACAO_EXIBICAO = 1.60
    DURACAO_SAIDA = 0.70
    DURACAO_SAIDA_RAPIDA = 0.22
    ATRASO_MINIMO_PULAR = 0.20

    def __init__(self, largura_tela=960, altura_tela=540):
        self.largura_tela = int(largura_tela)
        self.altura_tela = int(altura_tela)
        self.fase = "ENTRADA"  # ENTRADA -> EXIBICAO -> SAIDA -> CONCLUIDA
        self.tempo_total = 0.0
        self.tempo_fase = 0.0
        self.alpha_atual = 0
        self.alpha_inicio_saida = 255
        self.duracao_saida_atual = self.DURACAO_SAIDA
        self.escala_atual = 0.96
        self.offset_y = 6
        self.concluida = False

        self._logo_base = self._carregar_logo()
        self._fonte_pular = ui_procedural.obter_fonte_serif(11, bold=False)

    def _carregar_logo(self):
        caminho = obter_caminho_recurso(os.path.join("assets", "ui", "logo_gozygrid_studios.jpg"))
        if os.path.exists(caminho):
            try:
                bruta = pygame.image.load(caminho).convert()
                bw, bh = bruta.get_size()
                alvo_w = min(900, self.largura_tela - 48)
                alvo_h = max(1, int(round(alvo_w * (bh / float(max(1, bw))))))
                max_h = self.altura_tela - 28
                if alvo_h > max_h:
                    alvo_h = max_h
                    alvo_w = max(1, int(round(alvo_h * (bw / float(max(1, bh))))))
                escalada = pygame.transform.smoothscale(bruta, (alvo_w, alvo_h))
                return _suavizar_bordas_surface(escalada, margem_x=110, margem_y=22)
            except Exception as exc:
                log_aviso(f"[splash_estudio] Falha ao carregar logo do estúdio: {exc}")

        # Fallback simples caso a imagem não esteja disponível
        fallback = pygame.Surface((480, 140), pygame.SRCALPHA)
        f_tit = ui_procedural.obter_fonte_serif(40, bold=True)
        f_sub = ui_procedural.obter_fonte_serif(18, bold=False)
        s_tit = f_tit.render("GoZygrid", True, ui_procedural.COR_OURO_VIVO)
        s_sub = f_sub.render("STUDIOS", True, ui_procedural.COR_CINZA_TEXTO)
        fallback.blit(s_tit, ((480 - s_tit.get_width()) // 2, 24))
        fallback.blit(s_sub, ((480 - s_sub.get_width()) // 2, 82))
        return fallback

    def pular(self):
        """Inicia saída rápida e suave quando o jogador pressiona uma tecla/botão."""
        if self.concluida or self.tempo_total < self.ATRASO_MINIMO_PULAR:
            return False
        if self.fase != "SAIDA":
            self.fase = "SAIDA"
            self.tempo_fase = 0.0
            self.alpha_inicio_saida = max(1, self.alpha_atual)
            self.duracao_saida_atual = self.DURACAO_SAIDA_RAPIDA
            return True
        return False

    def handle_event(self, event):
        if self.concluida:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                return self.pular()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.pular()
        return False

    def update(self, dt):
        if self.concluida:
            return
        dt = max(0.0, min(0.05, float(dt)))
        self.tempo_total += dt
        self.tempo_fase += dt

        if self.fase == "ENTRADA":
            t = min(1.0, self.tempo_fase / self.DURACAO_ENTRADA)
            ease = 1.0 - (1.0 - t) ** 3
            self.alpha_atual = int(round(255 * ease))
            self.escala_atual = 0.96 + 0.04 * ease
            self.offset_y = int(round(6.0 * (1.0 - ease)))
            if t >= 1.0:
                self.fase = "EXIBICAO"
                self.tempo_fase = 0.0
                self.alpha_atual = 255
                self.escala_atual = 1.0
                self.offset_y = 0

        elif self.fase == "EXIBICAO":
            self.alpha_atual = 255
            self.escala_atual = 1.0
            self.offset_y = 0
            if self.tempo_fase >= self.DURACAO_EXIBICAO:
                self.fase = "SAIDA"
                self.tempo_fase = 0.0
                self.alpha_inicio_saida = 255
                self.duracao_saida_atual = self.DURACAO_SAIDA

        elif self.fase == "SAIDA":
            t = min(1.0, self.tempo_fase / max(0.05, self.duracao_saida_atual))
            ease = t * t * (3.0 - 2.0 * t)
            self.alpha_atual = max(0, int(round(self.alpha_inicio_saida * (1.0 - ease))))
            self.escala_atual = 1.0
            self.offset_y = 0
            if t >= 1.0:
                self.fase = "CONCLUIDA"
                self.alpha_atual = 0
                self.concluida = True

    def draw(self, surface):
        surface.fill(COR_FUNDO_SPLASH)
        if self.concluida or self.alpha_atual <= 0 or self._logo_base is None:
            return

        if abs(self.escala_atual - 1.0) < 0.001:
            quadro = self._logo_base
        else:
            bw, bh = self._logo_base.get_size()
            nw = max(1, int(round(bw * self.escala_atual)))
            nh = max(1, int(round(bh * self.escala_atual)))
            quadro = pygame.transform.smoothscale(self._logo_base, (nw, nh))

        quadro.set_alpha(self.alpha_atual)
        x = (self.largura_tela - quadro.get_width()) // 2
        y = (self.altura_tela - quadro.get_height()) // 2 + self.offset_y
        surface.blit(quadro, (x, y))

        if self.tempo_total >= 0.65 and self.fase != "SAIDA":
            alfa_dica = min(105, int(105 * min(1.0, (self.tempo_total - 0.65) / 0.45)))
            if alfa_dica > 0:
                dica = self._fonte_pular.render("Pular [ESPAÇO / ESC]", True, (100, 110, 128))
                dica.set_alpha(alfa_dica)
                surface.blit(dica, (self.largura_tela - dica.get_width() - 18, self.altura_tela - dica.get_height() - 14))
