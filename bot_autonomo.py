# -*- coding: utf-8 -*-
"""
ELOS DO VAZIO - Módulo de Bot Autônomo (Auto-Play).
Permite que o jogo jogue sozinho automaticamente quando ativado,
controlando a movimentação e pulos no mapa, decisões táticas e timing
perfeito de QTEs ofensivos e defensivos no combate.
"""

import math
import random
import pygame

GOLPES_SO_PULO = (
    "ONDA_CHOQUE", "RASTEIRA", "BOTE_FENDIDO", "CLAVA_SISMICA", "FURIA_ELOS_CORRENTES",
)
GOLPES_SO_DESVIO = (
    "VENENO", "INVESTIDA", "RUGIDO",
    "LANCA_DO_VAZIO", "GUILHOTINA_TRIPLICE", "FURIA_ELOS_DETONACAO",
)


class BotAutonomo:
    def __init__(self):
        self.ativo = False
        self.modo_vitrine = False
        self.timer_acao_combate = 0.25
        self.timer_pulo_mapa = 0.0
        self.timer_morte = 0.0
        self.tempo_total_bot = 0.0
        self.combates_vencidos = 0
        self.inimigos_derrotados = 0

    def alternar(self):
        """Liga ou desliga o modo Bot."""
        self.ativo = not self.ativo
        if not self.ativo:
            self.modo_vitrine = False
        self.timer_acao_combate = 0.25
        self.timer_morte = 0.0
        return self.ativo

    def ligar(self, vitrine=False):
        self.ativo = True
        self.modo_vitrine = vitrine
        self.timer_acao_combate = 0.25
        self.timer_morte = 0.0

    def desligar(self):
        self.ativo = False
        self.modo_vitrine = False

    # =========================================================================
    # 1. COMPORTAMENTO NO MAPA DE EXPLORAÇÃO
    # =========================================================================
    def atualizar_mapa(self, dt, jogador, mapa_atual, inimigos_sala, mapa_idx=0):
        if not self.ativo or not jogador:
            return

        self.tempo_total_bot += dt
        self.timer_pulo_mapa = max(0.0, self.timer_pulo_mapa - dt)

        # 1. Se estiver bloqueado por uma parede ou degrau no chão, pula
        if jogador.no_chao and abs(jogador.vx) < 5.0 and self.timer_pulo_mapa <= 0:
            jogador.solicitar_pulo()
            self.timer_pulo_mapa = 0.45

        # 2. Detecta armadilhas ou espinhos à frente e salta por cima
        for area_perigosa, tipo_perigo in mapa_atual.get("armadilhas", []):
            dist_x = area_perigosa.left - jogador.rect.right
            if 0 < dist_x < 85 and abs(area_perigosa.top - jogador.rect.bottom) < 40:
                if jogador.no_chao and self.timer_pulo_mapa <= 0:
                    jogador.solicitar_pulo()
                    self.timer_pulo_mapa = 0.60
                    break

        # 3. Ataca com a espada ao se aproximar de inimigos (garante Ataque Preventivo)
        for inim in inimigos_sala:
            if getattr(inim, "vivo", True):
                dist_inim = inim.x - jogador.x
                if 0 < dist_inim < 115 and not jogador.atacando:
                    jogador.atacar()
                    break

        # 4. Na Sala 7 (Arquivo das Almas): ativa runas misteriosas ao passar por elas
        if mapa_idx == 6:
            from cenarios import POS_RUNAS_SALA7
            for ri, (rx, ry) in enumerate(POS_RUNAS_SALA7):
                if ri not in jogador.runas_ativadas:
                    if math.hypot((jogador.x + jogador.largura / 2) - rx, (jogador.y + jogador.altura / 2) - ry) < 100:
                        jogador.runas_ativadas.add(ri)

    # =========================================================================
    # 2. COMPORTAMENTO NO COMBATE TÁTICO (EXPEDITION 33)
    # =========================================================================
    def atualizar_combate(self, dt, combate):
        if not self.ativo or not combate:
            return

        # --- A. TURNO DO JOGADOR: ESCOLHA INTELIGENTE DE HABILIDADES OU ITENS ---
        if combate.estado == "MENU_JOGADOR":
            self.timer_acao_combate -= dt
            if self.timer_acao_combate > 0:
                return

            # 1. Cura de emergência: se vida estiver <= 38% e tiver poções
            precisa_curar = (combate.jogador_hp <= combate.jogador_max_hp * 0.38 and combate.qtd_pocao > 0)

            if precisa_curar:
                if combate.menu_categoria == "PRINCIPAL":
                    combate.opcao_principal = 1  # Submenu Itens
                    combate.handle_keydown(pygame.K_RETURN)
                    self.timer_acao_combate = 0.20
                    return
                elif combate.menu_categoria == "ITENS":
                    combate.opcao_item = 0  # Poção de Cura
                    combate.handle_keydown(pygame.K_RETURN)
                    self.timer_acao_combate = 0.35
                    return

            # 2. Ataque / Habilidades
            if combate.menu_categoria == "PRINCIPAL":
                combate.opcao_principal = 0  # Submenu Ataques
                combate.handle_keydown(pygame.K_RETURN)
                self.timer_acao_combate = 0.20
                return

            elif combate.menu_categoria == "ATAQUES":
                ap = combate.jogador_ap
                melhor_idx = 0

                # Heurística tática baseada em AP disponível:
                # Se tem 6 AP: USA Dança do Éter (Dano Colossal + Fenda 35%)
                # Se tem >= 2 AP: USA Corte Lumina (Dano Alto + Fogo DoT)
                # Se tem 1 AP: USA Lâmina Tóxica (Veneno)
                # Se tem 0 AP: USA Foco Absoluto (Purifica debuff e gera +2 AP) ou Assalto Rápido (+1 AP)
                indice_danca = None
                indice_corte = None
                indice_toxica = None
                indice_foco = None
                indice_assalto = None

                for idx, acao in enumerate(combate.acoes_ataque):
                    nome = acao.get("nome", "")
                    if "Dança" in nome or "Éter" in nome:
                        indice_danca = idx
                    elif "Corte" in nome or "Lumina" in nome:
                        indice_corte = idx
                    elif "Tóxica" in nome:
                        indice_toxica = idx
                    elif "Foco" in nome:
                        indice_foco = idx
                    elif "Assalto" in nome:
                        indice_assalto = idx

                if ap >= 6 and indice_danca is not None:
                    melhor_idx = indice_danca
                elif ap >= 2 and indice_corte is not None:
                    melhor_idx = indice_corte
                elif ap >= 1 and indice_toxica is not None:
                    melhor_idx = indice_toxica
                elif ap == 0:
                    if combate.debuffs_jogador and indice_foco is not None:
                        melhor_idx = indice_foco
                    elif indice_assalto is not None:
                        melhor_idx = indice_assalto
                    elif indice_foco is not None:
                        melhor_idx = indice_foco

                combate.opcao_ataque = melhor_idx
                combate.handle_keydown(pygame.K_RETURN)
                self.timer_acao_combate = 0.35
                return

        # --- B. TIMING DO GOLPE DO JOGADOR (QTE DE ATAQUE) ---
        elif combate.estado == "QTE_JOGADOR":
            progresso_qte = combate.qte_timer / max(0.001, combate.qte_duracao)
            # Acerta no sweet spot perfeito (entre 80% e 96% do círculo de timing)
            if 0.80 <= progresso_qte <= 0.96:
                combate.resolver_golpe_qte(apertou_botao=True)

        # --- C. DEFESA REATIVA CONTRA ATAQUES INIMIGOS (PARRY, PULO, DESVIO) ---
        elif combate.estado == "TURNO_INIMIGO":
            tipo_golpe = combate.tipo_golpe_atual()
            delta_tempo = abs(combate.tempo_impacto - combate.inimigo_timer)

            # Janela de reação perfeita no momento exato do impacto (0.02s a 0.12s)
            if delta_tempo <= 0.12:
                if tipo_golpe in GOLPES_SO_PULO:
                    # Rasteiras e Ondas de Choque exigem Pulo!
                    if not combate.pulando:
                        combate.pular()
                elif tipo_golpe in GOLPES_SO_DESVIO:
                    # Névoas e Miasmas exigem Desvio!
                    if combate.janela_desvio_ativa <= 0:
                        combate.desviar()
                else:
                    # Golpes cortantes e esmagamentos: Parry Perfeito!
                    if combate.janela_parry_ativa <= 0:
                        combate.parry()

    # =========================================================================
    # 3. COMPORTAMENTO EM TELAS DE MORTE OU VITÓRIA (LOOP INFINITO)
    # =========================================================================
    def atualizar_morte(self, dt):
        """Aguarda um momento e reinicia o jogo automaticamente para continuar jogando."""
        if not self.ativo:
            return False
        self.timer_morte += dt
        if self.timer_morte >= 2.0:
            self.timer_morte = 0.0
            return True  # Sinaliza para reiniciar
        return False

    # =========================================================================
    # 4. RENDERIZAÇÃO DO BADGE VISUAL DE AUTO-PLAY NA TELA
    # =========================================================================
    def desenhar_overlay(self, surface, largura_tela, altura_tela, fonte_peq):
        if not self.ativo or not surface or not fonte_peq:
            return

        # Pulso sutil de iluminação
        t = pygame.time.get_ticks() / 1000.0
        pulso = 0.5 + 0.5 * math.sin(t * 5.0)

        if self.modo_vitrine:
            # Banner arcade grandioso para modo vitrine de exposição
            largura_badge = 540
            altura_badge = 32
            bx = largura_tela // 2 - largura_badge // 2
            by = 10

            rect_bg = pygame.Rect(bx, by, largura_badge, altura_badge)
            surf_badge = pygame.Surface((largura_badge, altura_badge), pygame.SRCALPHA)
            surf_badge.fill((16, 10, 24, 235))
            surface.blit(surf_badge, (bx, by))

            cor_borda = (int(220 + 35 * pulso), int(170 + 70 * pulso), int(40 + 50 * pulso))
            pygame.draw.rect(surface, (6, 4, 10), rect_bg, 3)
            pygame.draw.rect(surface, cor_borda, rect_bg, 2)

            for px, py in [(bx + 3, by + 3), (bx + largura_badge - 5, by + 3), (bx + 3, by + altura_badge - 5), (bx + largura_badge - 5, by + altura_badge - 5)]:
                pygame.draw.rect(surface, (255, 235, 140), (px, py, 3, 3))

            texto = "MODO VITRINE (DEMO AUTOMÁTICA)  •  TOQUE EM QUALQUER BOTÃO PARA JOGAR"
            txt_sombra = fonte_peq.render(texto, True, (0, 0, 0))
            cor_txt = (255, 240, 160) if pulso > 0.4 else (255, 215, 90)
            txt_surf = fonte_peq.render(texto, True, cor_txt)
            surface.blit(txt_sombra, (bx + largura_badge // 2 - txt_surf.get_width() // 2 + 1, by + 8))
            surface.blit(txt_surf, (bx + largura_badge // 2 - txt_surf.get_width() // 2, by + 7))
        else:
            largura_badge = 410
            altura_badge = 26
            bx = largura_tela // 2 - largura_badge // 2
            by = 8

            rect_bg = pygame.Rect(bx, by, largura_badge, altura_badge)
            surf_badge = pygame.Surface((largura_badge, altura_badge), pygame.SRCALPHA)
            surf_badge.fill((18, 14, 28, 220))
            surface.blit(surf_badge, (bx, by))

            cor_borda = (int(190 + 65 * pulso), int(150 + 70 * pulso), 80)
            pygame.draw.rect(surface, (8, 6, 12), rect_bg, 3)
            pygame.draw.rect(surface, cor_borda, rect_bg, 1)

            for px, py in [(bx + 3, by + 3), (bx + largura_badge - 4, by + 3), (bx + 3, by + altura_badge - 4), (bx + largura_badge - 4, by + altura_badge - 4)]:
                pygame.draw.rect(surface, (255, 230, 120), (px, py, 2, 2))

            texto = "⚔ MODO BOT ATIVO (AUTO-PLAY)  |  [F2] Assumir Controle"
            txt_sombra = fonte_peq.render(texto, True, (8, 6, 12))
            txt_surf = fonte_peq.render(texto, True, (245, 230, 160) if pulso > 0.4 else (210, 240, 255))
            surface.blit(txt_sombra, (bx + largura_badge // 2 - txt_surf.get_width() // 2 + 1, by + 5))
            surface.blit(txt_surf, (bx + largura_badge // 2 - txt_surf.get_width() // 2, by + 4))


# Instância global do Bot Autônomo
BOT = BotAutonomo()
