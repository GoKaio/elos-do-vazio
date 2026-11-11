# -*- coding: utf-8 -*-
"""
Cutscenes de Transição Entre Salas e Epílogo Final - Elos do Vazio.

Padronizado sobre `cutscene.GerenciadorCutscenes` e `ui_procedural.py` para manter
unidade visual absoluta entre introdução, transições de masmorra e final da jornada.
"""

import math
import pygame

import ui_procedural as uip
from cutscene import GerenciadorCutscenes, ALTURA_LETTERBOX, COR_BORDA_LETTERBOX


_TITULOS_SALAS = (
    ("Cemitério da Lua Pálida", "cidadela", "O vento gélido carrega ecos antigos pelos túmulos esquecidos."),
    ("Túnel da Cripta", "subterraneo", "Pedras úmidas e tochas mortiças anunciam os salões subterrâneos."),
    ("Pátio das Ruínas", "cidadela", "Arcos partidos se erguem sobre o abismo onde outrora marchou a guarda."),
    ("Catedral Submersa", "subterraneo", "Sinos mudos repousam sob a névoa azulada de Éter condensado."),
    ("Fornalha de Cinzas", "abismo", "Brasas ancestrais ainda ardem sob o aço dos sentinelas caídos."),
    ("Torre do Eclipse", "cidadela", "Mais alto na espiral sombria, o céu noturno pesa sobre os ombros."),
    ("Santuário do Vazio", "abismo", "Adiante aguarda o último selo — e o coração silenciado do Vazio."),
)


class MiniCutscenePassagemSala:
    """Cutscene curta de passagem entre salas da expedição."""

    def __init__(self, sala_origem_idx, sala_destino_idx, hp_jogador=100, callback_conclusao=None):
        self.sala_origem_idx = int(sala_origem_idx)
        self.sala_destino_idx = int(sala_destino_idx)
        self.hp_jogador = int(hp_jogador)
        self.callback_conclusao = callback_conclusao

        idx_safe = max(0, min(len(_TITULOS_SALAS) - 1, self.sala_destino_idx))
        nome_dest, fundo_dest, desc_dest = _TITULOS_SALAS[idx_safe]

        aviso_hp = (
            "Tuas feridas sangram pesado, mas a chama interior ainda recusa ceder."
            if self.hp_jogador <= 45
            else "Teu passo ecoa firme na pedra antiga rumo à próxima câmara."
        )

        roteiro = [
            {
                "titulo_ato": f"Sala {self.sala_destino_idx + 1} — {nome_dest}",
                "orador": f"Sala {self.sala_destino_idx + 1}: {nome_dest}",
                "texto": f"{desc_dest} {aviso_hp}",
                "duracao": 3.4,
                "tempo_fade": 0.42,
                "silhueta": "heroi",
                "fundo": fundo_dest,
                "sfx": "passo",
            }
        ]

        self.motor = GerenciadorCutscenes(
            roteiro=roteiro,
            callback_fim=self.callback_conclusao,
            anim_heroi=None,
            fundo_modo=fundo_dest,
            titulo_cena=f"TRAVESSIA — {nome_dest.upper()}",
            auto_avancar=True,
        )

    @property
    def concluida(self):
        return self.motor.concluida

    def avancar_ato(self):
        self.motor.avancar_ato()

    def pular(self):
        self.motor.pular()

    def handle_keydown(self, key):
        return self.motor.handle_keydown(key)

    def handle_event(self, event):
        return self.motor.handle_event(event)

    def update(self, dt):
        return self.motor.update(dt)

    def draw(self, surface):
        self.motor.draw(surface)


class CutsceneFinalJogo:
    """Epílogo cinematográfico ao concluir o Santuário do Vazio, seguido por cartão de decisão gótico."""

    def __init__(self, callback_retorno_menu=None, resumo_rank=None, tempo_total=None, nome_heroi=None):
        self.callback_retorno_menu = callback_retorno_menu
        self.resumo_rank = resumo_rank
        self.tempo_total = tempo_total
        self.nome_heroi = nome_heroi
        self.em_menu_final = False
        self.selecionado = 0
        self.tempo_menu = 0.0
        self.opcoes = [
            ("NOVA EXPEDIÇÃO", "REINICIAR", "espada"),
            ("MENU PRINCIPAL", "MENU", "escudo"),
        ]
        self._rects_botoes = []

        roteiro_epilogo = [
            {
                "titulo_ato": "Epílogo — O Último Elo Partido",
                "orador": "Crônica do Vazio",
                "texto": (
                    "Com a queda do último guardião, os grilhões de ferro se desfazem "
                    "em poeira luminosa e o silêncio da cidadela enfim se rompe."
                ),
                "duracao": 5.5,
                "tempo_fade": 0.60,
                "silhueta": "guardiao",
                "fundo": "abismo",
                "sfx": "curar",
            },
            {
                "titulo_ato": "Epílogo — Alvorada Sobre a Cidadela",
                "orador": "Oráculo das Cinzas",
                "texto": (
                    "Os fragmentos de Éter retornam ao firmamento. Pela primeira vez em eras, "
                    "um fio pálido de aurora toca as torres partidas."
                ),
                "duracao": 5.8,
                "tempo_fade": 0.65,
                "silhueta": "oraculo",
                "fundo": "aurora",
                "sfx": "curar",
            },
            {
                "titulo_ato": "Epílogo — Lenda Eterna",
                "orador": "Crônica do Vazio",
                "texto": (
                    "Teu nome ficará gravado nas pedras da expedição: aquele que caminhou pela noite "
                    "e reacendeu a esperança nos Elos do Vazio."
                ),
                "duracao": 5.2,
                "tempo_fade": 0.60,
                "silhueta": "heroi",
                "fundo": "aurora",
            },
        ]

        self.motor = GerenciadorCutscenes(
            roteiro=roteiro_epilogo,
            callback_fim=self._entrar_menu_final,
            anim_heroi=None,
            fundo_modo="aurora",
            titulo_cena="FIM DA JORNADA — ELOS RESTAURADOS",
            auto_avancar=True,
        )

    def definir_resultado(self, resumo_rank=None, tempo_total=None, nome_heroi=None):
        self.resumo_rank = resumo_rank
        if tempo_total is not None:
            self.tempo_total = float(tempo_total)
        if nome_heroi:
            self.nome_heroi = str(nome_heroi)

    def _entrar_menu_final(self):
        self.em_menu_final = True
        self.tempo_menu = 0.0

    def handle_keydown(self, key):
        if not self.em_menu_final:
            self.motor.handle_keydown(key)
            return None

        if key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            self.selecionado = (self.selecionado - 1) % len(self.opcoes)
            return None
        if key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
            self.selecionado = (self.selecionado + 1) % len(self.opcoes)
            return None
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            acao = self.opcoes[self.selecionado][1]
            if acao == "MENU" and callable(self.callback_retorno_menu):
                self.callback_retorno_menu()
            return acao
        if key == pygame.K_ESCAPE:
            if callable(self.callback_retorno_menu):
                self.callback_retorno_menu()
            return "MENU"
        return None

    def update(self, dt):
        if not self.em_menu_final:
            self.motor.update(dt)
        else:
            self.tempo_menu += max(0.0, min(0.08, float(dt)))

    def draw(self, surface):
        if not self.em_menu_final:
            self.motor.draw(surface)
            return

        w, h = surface.get_size()
        # Reutiliza cenário aurora estático + barras letterbox 52px + cartão gótico central
        self.motor._garantir_cache(w, h, "aurora")
        if self.motor._surf_fundo is not None:
            surface.blit(self.motor._surf_fundo, (0, 0))
        if self.motor._surf_silhuetas_bg is not None:
            surface.blit(self.motor._surf_silhuetas_bg, (0, 0))
        if self.motor._surf_vinheta is not None:
            surface.blit(self.motor._surf_vinheta, (0, 0))

        # Moldura gótica centralizada em ui_procedural (com brasão de Rank quando disponível)
        tem_rank = bool(getattr(self, "resumo_rank", None))
        pw = 560 if tem_rank else 460
        ph = 300 if tem_rank else 284
        px, py = (w - pw) // 2, (h - ph) // 2
        uip.desenhar_moldura_gotica(
            surface, px, py, pw, ph,
            chanfro=10, destacado=True, alpha=244, borda_ouro=True, cantoneiras=True, cranios=True,
        )

        f_tit = uip.obter_fonte_serif(24, bold=True)
        f_sub = uip.obter_fonte_serif(13, bold=False)
        f_btn = uip.obter_fonte_serif(15, bold=True)
        f_micro = uip.obter_fonte_serif(11, bold=False)

        pulso = 0.5 + 0.5 * math.sin(self.tempo_menu * 4.0)
        uip.desenhar_cristal_eter(surface, w // 2, py + 24, tamanho=6, ativo=(pulso > 0.2))

        s_tit = f_tit.render("EXPEDIÇÃO CONCLUÍDA", True, uip.COR_OURO_VIVO)
        s_tit_sh = f_tit.render("EXPEDIÇÃO CONCLUÍDA", True, (6, 8, 16))
        surface.blit(s_tit_sh, (w // 2 - s_tit.get_width() // 2 + 1, py + 43))
        surface.blit(s_tit, (w // 2 - s_tit.get_width() // 2, py + 42))

        uip.desenhar_divisor_dourado(surface, px + 36, py + 76, pw - 72)

        sub_txt = "A aurora voltou a brilhar sobre as ruínas da Cidadela."
        if self.nome_heroi and self.tempo_total is not None:
            t_seg = max(0.0, float(self.tempo_total))
            mm, ss = int(t_seg // 60), int(t_seg % 60)
            dc = int((t_seg - int(t_seg)) * 10)
            sub_txt = f"{self.nome_heroi}  ·  Tempo Total: {mm:02d}:{ss:02d}.{dc}"
        s_sub = f_sub.render(sub_txt, True, uip.COR_BRANCO_PEROLA)
        surface.blit(s_sub, (w // 2 - s_sub.get_width() // 2, py + 88))

        self._rects_botoes = []
        if tem_rank:
            # Brasão de Rank à esquerda e botões de decisão à direita sem qualquer sobreposição
            uip.desenhar_brasao_rank(
                surface,
                px + 108,
                py + 178,
                self.resumo_rank.get("rank", "C"),
                pontuacao=self.resumo_rank.get("pontuacao", 0),
                tamanho=72,
                sem_avaria=self.resumo_rank.get("sem_avaria", False),
                titulo="RANK FINAL",
                anim_t=self.tempo_menu,
            )
            bw, bh = 280, 44
            bx = px + 218
            for i, (rotulo, _acao, icone) in enumerate(self.opcoes):
                by = py + 136 + i * 56
                rect_b = pygame.Rect(bx, by, bw, bh)
                self._rects_botoes.append(rect_b)
                uip.desenhar_botao_gotico(
                    surface, rect_b, rotulo, f_btn,
                    selecionado=(i == self.selecionado), icone=icone,
                )
        else:
            bw, bh = 280, 44
            bx = w // 2 - bw // 2
            for i, (rotulo, _acao, icone) in enumerate(self.opcoes):
                by = py + 132 + i * 56
                rect_b = pygame.Rect(bx, by, bw, bh)
                self._rects_botoes.append(rect_b)
                uip.desenhar_botao_gotico(
                    surface, rect_b, rotulo, f_btn,
                    selecionado=(i == self.selecionado), icone=icone,
                )

        uip.desenhar_rodape_comandos(surface, py + ph - 24, ["[W/S] Selecionar", "[ENTER] Confirmar"], f_micro, largura=w)

        # Barras letterbox 52px consistentes
        pygame.draw.rect(surface, (0, 0, 0), (0, 0, w, ALTURA_LETTERBOX))
        pygame.draw.line(surface, COR_BORDA_LETTERBOX, (0, ALTURA_LETTERBOX - 1), (w, ALTURA_LETTERBOX - 1), 1)
        pygame.draw.rect(surface, (0, 0, 0), (0, h - ALTURA_LETTERBOX, w, ALTURA_LETTERBOX))
        pygame.draw.line(surface, COR_BORDA_LETTERBOX, (0, h - ALTURA_LETTERBOX), (w, h - ALTURA_LETTERBOX), 1)
