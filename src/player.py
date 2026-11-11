# -*- coding: utf-8 -*-
"""
Módulo do Jogador (Estritamente Single-Player) — Elos do Vazio (`player.py`).

Implementa física 2D de plataforma, animações modulares e as duas mecânicas
obrigatórias de resposta e desvio para combate de precisão:
  1. Esquiva Rasteira / Rolamento com I-Frames (Roll Dash): 14 frames de
     invencibilidade total e hitbox reduzida à metade da altura.
  2. Salto de Reação / Impulso Aéreo com Pogo (Vault Leap): pulo duplo rápido
     e ataque descendente com rebote vertical (`pogo bounce`).
"""

import math
import random
import pygame

from config import CONFIG
import audio
from sprites import criar_animador
import cenarios


ESCALA_SPRITE_MAPA = CONFIG.get("sprite_escala_mapa", 1.15)
ESQUIVA_IFRAMES = 14
DURACAO_ROLL_DASH = 0.28
COOLDOWN_ROLL_DASH = 0.42
VELOCIDADE_ROLL_DASH = 560.0
FORCA_SALTO_REACAO = -610.0
FORCA_POGO_BOUNCE = -590.0


class Jogador:
    """Entidade exclusiva do jogador único (1 Jogador) para exploração e combate 2D."""

    def __init__(self, x, y):
        self.largura = 36
        self.altura = 56
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)

        self.hp = CONFIG["jogador_hp_inicial"]
        self.max_hp = CONFIG["jogador_hp_inicial"]
        self.progresso_ref = None
        self.mapa_idx = 0

        self.vx = 0.0
        self.vy = 0.0
        self.velocidade = 340.0
        self.forca_pulo = -640.0
        self.gravidade = 1500.0

        self.no_chao = False
        self.olhando_direita = True
        self.tempo_coyote = 0.0
        self.buffer_pulo = 0.0
        self.pulos_aereos_disponiveis = 1
        self.salto_reacao_ativo = False

        # Mecânica 1: Esquiva Rasteira / Rolamento com 14 I-Frames e hitbox pela metade
        self.em_esquiva = False
        self.esquiva_timer = 0.0
        self.esquiva_cooldown = 0.0
        self.esquiva_dir = 1
        self.esquiva_frames_restantes = 0
        self.iframes_tempo = 0.0
        self._accum_frame_60 = 0.0
        self.hitbox_reduzida = False
        self.rastros_esquiva = []

        # Mecânica 2: Ataque padrão e Pogo Bounce (golpe descendente no ar)
        self.atacando = False
        self.atacando_baixo = False
        self.tempo_ataque = 0.0
        self.hitbox_ataque = None
        self.hitbox_pogo = None
        self.aneis_salto = []

        # Defesa / Stagger / Armadilhas
        self.bloqueando = False
        self.stagger_timer = 0.0
        self.tempo_imune_armadilha = 0.0
        self.flash_armadilha = 0.0
        self.tempo_invuln_contato = 0.0
        self.ultimo_motivo_dano = ""
        self.msg_reacao = ""
        self.timer_msg_reacao = 0.0

        self.classe = "GUERREIRO"
        self.anim = criar_animador(CONFIG.get("sprite_jogador"))
        self.invocacoes = []
        self.alvo_invocacao = 0
        self.tempo_invocar = 0.0
        mult_p = self.progresso_ref.multiplicador_poder() if self.progresso_ref else 1.0
        self.dano_invocacao = 6.48 * mult_p
        self.runas_ativadas = set()
        self.chaves_bolsa = 0
        self.chaves_coletadas_ids = set()
        self._pontes_ativas = []

    @property
    def esta_invencivel(self):
        return self.esquiva_frames_restantes > 0 or self.iframes_tempo > 0.0 or self.tempo_invuln_contato > 0.0

    def obter_hurtbox(self):
        """Retorna a hurtbox do jogador; durante Roll Dash a altura é reduzida pela metade."""
        if self.hitbox_reduzida or self.em_esquiva:
            alt_meia = max(16, self.altura // 2)
            return pygame.Rect(int(self.x), int(self.y + self.altura - alt_meia), self.largura, alt_meia)
        return self.rect.copy()

    def iniciar_esquiva(self, direcao=None):
        """Executa Esquiva Rasteira (Roll Dash): 14 frames de I-Frames + hitbox pela metade."""
        if self.em_esquiva or self.esquiva_cooldown > 0.0 or self.stagger_timer > 0.0:
            return False
        if not (self.no_chao or self.tempo_coyote > 0.0):
            return False

        self.em_esquiva = True
        self.hitbox_reduzida = True
        self.esquiva_timer = DURACAO_ROLL_DASH
        self.esquiva_cooldown = COOLDOWN_ROLL_DASH
        self.esquiva_frames_restantes = ESQUIVA_IFRAMES
        self.iframes_tempo = ESQUIVA_IFRAMES / 60.0
        self._accum_frame_60 = 0.0
        self.bloqueando = False
        self.atacando = False
        self.atacando_baixo = False
        self.hitbox_ataque = None
        self.hitbox_pogo = None

        if direcao in (-1, 1):
            self.esquiva_dir = int(direcao)
            self.olhando_direita = self.esquiva_dir > 0
        else:
            self.esquiva_dir = 1 if self.olhando_direita else -1

        if self.anim and self.anim.ativo:
            self.anim.tocar("dodge", loop=False, duracao=DURACAO_ROLL_DASH, forcar=True)
        audio.tocar_sfx("dodge", 0.90)
        return True

    def solicitar_pulo(self):
        """Pulo no chão (com coyote time) ou Salto de Reação rápido (pulo duplo no ar)."""
        if self.stagger_timer > 0.0:
            return False
        if self.no_chao or self.tempo_coyote > 0.0:
            self.buffer_pulo = 0.15
            audio.tocar_sfx("teleport", 0.45)
            return True
        if self.pulos_aereos_disponiveis > 0:
            self.pulos_aereos_disponiveis -= 1
            self.vy = FORCA_SALTO_REACAO
            self.salto_reacao_ativo = True
            self.em_esquiva = False
            self.hitbox_reduzida = False
            self.aneis_salto.append({"x": self.x + self.largura / 2.0, "y": self.y + self.altura, "vida": 0.28})
            if self.anim and self.anim.ativo:
                self.anim.tocar("jump", loop=False, duracao=0.45, forcar=True)
            audio.tocar_sfx("jump", 0.85)
            return True
        self.buffer_pulo = 0.15
        return False

    def cortar_pulo(self):
        if self.vy < -220.0:
            self.vy = -220.0

    def atacar(self, para_baixo=False):
        """Executa corte frontal ou ataque pogo descendente no ar."""
        if self.stagger_timer > 0.0 or self.em_esquiva:
            return False
        if not self.atacando:
            self.atacando = True
            self.atacando_baixo = bool(para_baixo and not self.no_chao)
            audio.tocar_sfx("sword", 0.78)
            self.tempo_ataque = 0.24
            anim_ataque = "attack_aereo" if self.atacando_baixo else random.choice(("attack", "attack2", "attack3"))
            if self.anim and self.anim.ativo:
                self.anim.tocar(anim_ataque, loop=False, duracao=0.24, forcar=True)
            self._atualizar_hitboxes_ataque()
            return True
        return False

    def _atualizar_hitboxes_ataque(self):
        if self.atacando_baixo:
            self.hitbox_pogo = pygame.Rect(int(self.x - 4), int(self.y + self.altura - 2), self.largura + 8, 34)
            self.hitbox_ataque = self.hitbox_pogo.copy()
        else:
            alcance = 56
            offset_x = self.largura if self.olhando_direita else -alcance
            self.hitbox_ataque = pygame.Rect(int(self.x + offset_x), int(self.y + 10), alcance, 36)
            self.hitbox_pogo = None

    def executar_pogo_bounce(self):
        """Rebote imediato (pogo bounce) ao atingir inimigo ou onda de choque de cima para baixo."""
        self.vy = FORCA_POGO_BOUNCE
        self.no_chao = False
        self.salto_reacao_ativo = True
        self.pulos_aereos_disponiveis = 1
        self.esquiva_cooldown = 0.0
        self.tempo_invuln_contato = max(self.tempo_invuln_contato, 0.12)
        self.atacando = False
        self.atacando_baixo = False
        self.hitbox_pogo = None
        self.hitbox_ataque = None
        self.aneis_salto.append({"x": self.x + self.largura / 2.0, "y": self.y + self.altura + 8, "vida": 0.30})
        if self.anim and self.anim.ativo:
            self.anim.tocar("jump", loop=False, duracao=0.42, forcar=True)
        audio.tocar_sfx("sword_crit", 0.85)

    def aplicar_stagger(self, duracao=0.65, motivo="GUARDA QUEBRADA!"):
        self.stagger_timer = max(self.stagger_timer, float(duracao))
        self.bloqueando = False
        self.atacando = False
        self.hitbox_ataque = None
        self.hitbox_pogo = None
        self.msg_reacao = motivo
        self.timer_msg_reacao = 0.90
        if self.anim and self.anim.ativo:
            self.anim.tocar("hurt", loop=False, duracao=0.40, forcar=True)

    def sofrer_dano(
        self,
        dano,
        tipo_ataque="CORTE",
        quebra_guarda=False,
        ignora_esquiva_chao=False,
        exige_esquiva_rasteira=False,
        empurrao_x=0.0,
        chao_referencia_y=None,
    ):
        """Avalia colisão estritamente individual (1 jogador) contra ataques exclusivos."""
        hurtbox = self.obter_hurtbox()

        if exige_esquiva_rasteira and (self.esta_invencivel or self.hitbox_reduzida):
            self.msg_reacao = "ESQUIVA RASTEIRA!"
            self.timer_msg_reacao = 0.70
            return {"atingido": False, "motivo": "ESQUIVA_RASTEIRA", "dano": 0, "contra_aberta": True}

        if ignora_esquiva_chao:
            no_ar_limpo = (not self.no_chao) and (
                chao_referencia_y is None or hurtbox.bottom < (chao_referencia_y - 18)
            )
            if no_ar_limpo or self.tempo_invuln_contato > 0.0:
                self.msg_reacao = "SALTO DE REAÇÃO!"
                self.timer_msg_reacao = 0.70
                return {"atingido": False, "motivo": "SALTO_REACAO", "dano": 0, "contra_aberta": True}
        elif self.esta_invencivel:
            self.msg_reacao = "I-FRAMES (ESQUIVA)!"
            self.timer_msg_reacao = 0.70
            return {"atingido": False, "motivo": "IFRAMES", "dano": 0, "contra_aberta": True}

        if self.bloqueando and (quebra_guarda or ignora_esquiva_chao or exige_esquiva_rasteira):
            self.aplicar_stagger(0.65, motivo="BLOQUEIO QUEBRADO!")
        elif self.bloqueando and not quebra_guarda:
            dano_mit = max(1, int(dano * 0.20))
            self.hp = max(1, self.hp - dano_mit)
            self.msg_reacao = "BLOQUEADO"
            self.timer_msg_reacao = 0.55
            audio.tocar_sfx("parry", 0.75)
            return {"atingido": True, "motivo": "BLOQUEADO", "dano": dano_mit, "contra_aberta": False}

        dano_final = max(1, int(dano))
        self.hp = max(0, self.hp - dano_final)
        self.flash_armadilha = 0.28
        self.tempo_invuln_contato = 0.55
        if abs(empurrao_x) > 0.1:
            self.vx = float(empurrao_x)
        if self.anim and self.anim.ativo:
            self.anim.tocar("hurt", loop=False, duracao=0.38, forcar=True)
        audio.tocar_sfx("hit_player", 0.90)
        return {"atingido": True, "motivo": str(tipo_ataque), "dano": dano_final, "contra_aberta": False}

    def mover_horizontal(self, direcao):
        self.vx = direcao * self.velocidade
        if direcao > 0:
            self.olhando_direita = True
        elif direcao < 0:
            self.olhando_direita = False

    def _controle_ativo_fallback(self):
        if pygame.joystick.get_init() and pygame.joystick.get_count() > 0:
            try:
                j = pygame.joystick.Joystick(0)
                if not j.get_init():
                    j.init()
                return j
            except pygame.error:
                return None
        return None

    def update(self, dt, mapa_atual, grupo_sala=None, controle_ativo=None, bot=None):
        self.tempo_imune_armadilha = max(0.0, self.tempo_imune_armadilha - dt)
        self.flash_armadilha = max(0.0, self.flash_armadilha - dt)
        self.esquiva_cooldown = max(0.0, self.esquiva_cooldown - dt)
        self.tempo_invuln_contato = max(0.0, self.tempo_invuln_contato - dt)
        self.timer_msg_reacao = max(0.0, self.timer_msg_reacao - dt)
        self.iframes_tempo = max(0.0, self.iframes_tempo - dt)
        self.stagger_timer = max(0.0, self.stagger_timer - dt)

        # Decremento preciso em frames @ 60 FPS para os 14 I-Frames do Roll Dash
        if self.esquiva_frames_restantes > 0:
            self._accum_frame_60 += dt * 60.0
            passos = int(self._accum_frame_60)
            if passos > 0:
                self._accum_frame_60 -= passos
                self.esquiva_frames_restantes = max(0, self.esquiva_frames_restantes - passos)

        for rastro in self.rastros_esquiva[:]:
            rastro["vida"] -= dt
            if rastro["vida"] <= 0:
                self.rastros_esquiva.remove(rastro)
        for anel in self.aneis_salto[:]:
            anel["vida"] -= dt
            if anel["vida"] <= 0:
                self.aneis_salto.remove(anel)

        keys = pygame.key.get_pressed()
        bot_ativo = bool(bot and getattr(bot, "ativo", False))

        if self.em_esquiva:
            self.esquiva_timer -= dt
            self.vx = self.esquiva_dir * VELOCIDADE_ROLL_DASH
            self.rastros_esquiva.append({"x": self.x, "y": self.y, "vida": 0.16, "meia_alt": True})
            if self.esquiva_timer <= 0.0:
                self.em_esquiva = False
                self.hitbox_reduzida = False
                self.vx = 0.0
        elif self.stagger_timer > 0.0:
            self.vx *= max(0.0, 1.0 - dt * 8.0)
            self.bloqueando = False
        else:
            self.vx = 0.0
            if bot_ativo:
                self.vx = self.velocidade
            else:
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.vx -= self.velocidade
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.vx += self.velocidade
                self.bloqueando = bool(keys[pygame.K_x]) and self.no_chao and not self.atacando

                joy = controle_ativo if controle_ativo is not None else self._controle_ativo_fallback()
                if joy is not None:
                    try:
                        eixo_x = joy.get_axis(0) if joy.get_numaxes() > 0 else 0.0
                        if abs(eixo_x) > 0.18:
                            self.vx = float(eixo_x) * self.velocidade
                        elif joy.get_numhats() > 0:
                            hx, _ = joy.get_hat(0)
                            if hx != 0:
                                self.vx = float(hx) * self.velocidade
                    except pygame.error:
                        pass

            if self.vx < -1:
                self.olhando_direita = False
            elif self.vx > 1:
                self.olhando_direita = True

        if self.no_chao:
            self.tempo_coyote = 0.12
            self.pulos_aereos_disponiveis = 1
            self.salto_reacao_ativo = False
        else:
            self.tempo_coyote = max(0.0, self.tempo_coyote - dt)

        self.buffer_pulo = max(0.0, self.buffer_pulo - dt)

        if self.buffer_pulo > 0.0 and (self.no_chao or self.tempo_coyote > 0.0) and self.stagger_timer <= 0.0:
            self.vy = self.forca_pulo
            self.buffer_pulo = 0.0
            self.tempo_coyote = 0.0
            self.no_chao = False

        if self.atacando:
            self.tempo_ataque -= dt
            if self.tempo_ataque <= 0:
                self.atacando = False
                self.atacando_baixo = False
                self.hitbox_ataque = None
                self.hitbox_pogo = None
            else:
                self._atualizar_hitboxes_ataque()

        # Movimento Horizontal com bloqueio por portões trancados e paredes
        dx = self.vx * dt
        portoes = grupo_sala.get("portoes", []) if grupo_sala else mapa_atual.get("portoes", [])
        paredes = mapa_atual.get("paredes", [])
        larg_m = mapa_atual.get("largura", cenarios.LARGURA_MUNDO)
        bloqueios_solidos = [g["rect"] for g in portoes if not g.get("aberto", False)] + list(paredes)

        futuro_x = pygame.Rect(int(self.x + dx), int(self.y) + 2, self.largura, max(4, self.altura - 4))
        bloqueado_x = False
        for b_rect in bloqueios_solidos:
            if futuro_x.colliderect(b_rect):
                if self.vy >= 0 and b_rect.top > 0 and (self.y + self.altura) - b_rect.top <= 6.0:
                    continue
                bloqueado_x = True
                if dx > 0:
                    self.x = float(b_rect.left - self.largura)
                elif dx < 0:
                    self.x = float(b_rect.right)
                self.vx = 0.0
                break
        if not bloqueado_x:
            self.x += dx

        self.x = max(0.0, min(float(larg_m - self.largura), self.x))

        # Gravidade e Movimento Vertical
        self.vy += self.gravidade * dt
        dy = self.vy * dt
        pe_anterior = self.y + self.altura
        em_superficie = False

        futuro_topo = self.y + dy
        futuro_pe = futuro_topo + self.altura
        limite_v = max(14.0, abs(dy) + 8.0)
        for b_rect in bloqueios_solidos:
            if b_rect.top > 0 and self.vy >= 0 and pe_anterior <= b_rect.top + limite_v and futuro_pe >= b_rect.top - 1.5:
                if (self.x + self.largura - 2) > b_rect.left and (self.x + 2) < b_rect.right:
                    self.y = float(b_rect.top - self.altura)
                    self.vy = 0.0
                    em_superficie = True
                    dy = 0.0
                    break
            elif self.vy < 0 and self.y >= b_rect.bottom - limite_v and futuro_topo <= b_rect.bottom:
                if (self.x + self.largura - 4) > b_rect.left and (self.x + 4) < b_rect.right:
                    self.y = float(b_rect.bottom)
                    self.vy = 0.0
                    dy = 0.0
                    break

        self.y += dy
        if self.y < 0.0:
            self.y = 0.0
            if self.vy < 0.0:
                self.vy = 0.0

        chao = mapa_atual["chao"]
        if (self.y + self.altura) >= chao.top:
            self.y = chao.top - self.altura
            self.vy = 0.0
            em_superficie = True

        pontes_ativas = [
            g["ponte"] for g in (grupo_sala.get("portoes", []) if grupo_sala else [])
            if g.get("aberto", False) and "ponte" in g
        ]
        self._pontes_ativas = pontes_ativas
        limite_tol = max(14.0, dy + 8.0)
        plat_apoiada = None
        for plat in list(mapa_atual["plataformas"]) + pontes_ativas:
            if self.vy >= 0:
                if pe_anterior <= plat.top + limite_tol + 6.0 and (self.y + self.altura) >= plat.top - 4:
                    if (self.x + self.largura - 4) > plat.left and (self.x + 4) < plat.right:
                        self.y = plat.top - self.altura
                        self.vy = 0.0
                        em_superficie = True
                        plat_apoiada = plat

        if plat_apoiada is not None:
            for pm in mapa_atual.get("plataformas_moveis", []):
                if pm["rect"] is plat_apoiada:
                    self.x = max(0.0, min(float(larg_m - self.largura), self.x + pm.get("dx", 0.0)))
                    break

        self.no_chao = em_superficie
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if self.anim and self.anim.ativo:
            if not self.atacando and not self.em_esquiva and self.stagger_timer <= 0.0:
                if self.bloqueando:
                    self.anim.tocar("block")
                elif not self.no_chao:
                    self.anim.tocar("jump")
                else:
                    self.anim.tocar("walk" if self.vx != 0 else "idle")
            self.anim.update(dt)

    def escolher_classe(self, classe):
        """Alterna arquétipo mantendo o combate estritamente individual (1 jogador)."""
        perfis = {
            "GUERREIRO": ("Hero", 120, 340.0, -640.0),
            "PATRULHEIRO": ("Orc Bronze", 105, 390.0, -690.0),
            "NECROMANTE": ("Necromante", 95, 320.0, -610.0),
        }
        if classe not in perfis:
            return
        self.classe = classe
        sprite, vida, velocidade, pulo = perfis[classe]
        self.max_hp = max(self.max_hp, vida)
        self.hp = min(self.max_hp, self.hp + 10)
        self.velocidade, self.forca_pulo = velocidade, pulo
        self.anim = criar_animador(sprite)

    def invocar_esqueleto(self, inimigos):
        if self.classe != "NECROMANTE" or self.tempo_invocar > 0:
            return
        alvos = [i for i in inimigos if i.vivo]
        if not alvos:
            return
        alvo = alvos[self.alvo_invocacao % len(alvos)]
        self.invocacoes.append({"alvo": alvo, "vida": 8.0, "tempo_ataque": 0.0, "x": self.x - 18.0})
        self.tempo_invocar = 5.0

    def atualizar_invocacoes(self, dt, inimigos):
        self.tempo_invocar = max(0.0, self.tempo_invocar - dt)
        vivos = [i for i in inimigos if i.vivo]
        for inv in self.invocacoes[:]:
            inv["vida"] -= dt
            alvo = inv["alvo"]
            if not alvo.vivo and vivos:
                alvo = min(vivos, key=lambda i: abs(i.x - inv["x"]))
                inv["alvo"] = alvo
            if not alvo.vivo or inv["vida"] <= 0:
                self.invocacoes.remove(inv)
                continue
            dx = alvo.x - inv["x"]
            inv["x"] += max(-150 * dt, min(150 * dt, dx))
            inv["tempo_ataque"] -= dt
            if abs(dx) < 65 and inv["tempo_ataque"] <= 0:
                alvo.hp = max(0, alvo.hp - self.dano_invocacao)
                inv["tempo_ataque"] = 1.0
                if alvo.hp <= 0:
                    alvo.vivo = False

    def desenhar_invocacoes(self, surface, camera):
        for inv in self.invocacoes:
            x = int(inv["x"] - camera.offset_x)
            alvo = inv["alvo"]
            cor = (170, 225, 220) if alvo.vivo else (100, 100, 110)
            pygame.draw.ellipse(surface, (20, 12, 30), (x + 4, 459, 28, 8))
            pygame.draw.circle(surface, cor, (x + 18, 438), 10)
            pygame.draw.rect(surface, (105, 125, 150), (x + 8, 447, 20, 28), border_radius=5)
            pygame.draw.line(surface, (210, 220, 235), (x + 8, 452), (x, 468), 3)
            pygame.draw.line(surface, (210, 220, 235), (x + 28, 452), (x + 36, 468), 3)
            if alvo.vivo:
                pygame.draw.line(surface, (185, 90, 255), (x + 18, 434),
                                 (int(alvo.rect.centerx - camera.offset_x), alvo.rect.centery), 1)

    def draw(self, surface, camera):
        pos_tela = camera.aplicar(self.rect)
        mapa = cenarios.DADOS_MAPAS.get(getattr(self, "mapa_idx", 0), cenarios.DADOS_MAPAS[0])
        pe_x = self.x + self.largura / 2
        paredes_pisaveis = [
            pr for pr in mapa.get("paredes", [])
            if pr.y > 120 and pr.width >= 60 and (pr.height <= 42 or pr.width >= 68)
        ]
        pontes_ativas = getattr(self, "_pontes_ativas", [])
        superficies = [mapa["chao"].top] + [
            pl.top for pl in (list(mapa["plataformas"]) + paredes_pisaveis + pontes_ativas)
            if pl.left - 8 <= pe_x <= pl.right + 8 and pl.top >= self.y + self.altura - 4
        ]
        base_y = min(superficies) if superficies else mapa["chao"].top
        altura_ar = max(0, base_y - (self.y + self.altura))
        sombra_y = int(base_y - camera.offset_y + getattr(camera, "shake_y", 0.0))
        if -20 <= sombra_y <= cenarios.ALTURA_TELA + 20:
            sombra_x = int(pos_tela.centerx)
            sombra_w = max(12, int(34 - min(22, altura_ar * 0.045)))
            sombra_h = max(4, int(10 - min(6, altura_ar * 0.013)))
            sombra = pygame.Surface((sombra_w * 2, sombra_h * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra, (0, 0, 0, max(40, 140 - int(altura_ar * 0.30))),
                                (sombra_w // 2, sombra_h // 2, sombra_w, sombra_h))
            surface.blit(sombra, (sombra_x - sombra_w, sombra_y - sombra_h))

        # Rastros translúcidos da Esquiva Rasteira (I-Frames em ciano de Éter)
        for rastro in self.rastros_esquiva:
            alpha_r = max(20, min(140, int(140 * (rastro["vida"] / 0.16))))
            rx = int(rastro["x"] - camera.offset_x + getattr(camera, "shake_x", 0.0))
            ry = int(rastro["y"] + (self.altura // 2) - camera.offset_y + getattr(camera, "shake_y", 0.0))
            s_r = pygame.Surface((self.largura, max(16, self.altura // 2)), pygame.SRCALPHA)
            pygame.draw.ellipse(s_r, (56, 189, 248, alpha_r), s_r.get_rect())
            surface.blit(s_r, (rx, ry))

        # Anéis de vento do Salto de Reação / Pogo Bounce
        for anel in self.aneis_salto:
            ax = int(anel["x"] - camera.offset_x + getattr(camera, "shake_x", 0.0))
            ay = int(anel["y"] - camera.offset_y + getattr(camera, "shake_y", 0.0))
            prog = 1.0 - (anel["vida"] / 0.30)
            rw = int(28 + 34 * prog)
            sa = pygame.Surface((rw * 2, 16), pygame.SRCALPHA)
            pygame.draw.ellipse(sa, (120, 245, 255, max(20, int(210 * (1.0 - prog)))), (0, 0, rw * 2, 16), 2)
            surface.blit(sa, (ax - rw, ay - 8))

        if self.em_esquiva:
            hurt_tela = camera.aplicar(self.obter_hurtbox())
            s_roll = pygame.Surface((hurt_tela.width + 8, hurt_tela.height + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(s_roll, (56, 189, 248, 220), (0, 0, s_roll.get_width(), s_roll.get_height()), 2)
            pygame.draw.ellipse(s_roll, (186, 230, 253, 95), (4, 4, s_roll.get_width() - 8, max(6, s_roll.get_height() - 8)))
            surface.blit(s_roll, (hurt_tela.x - 4, hurt_tela.y - 2))

        if self.anim and self.anim.ativo:
            if self.em_esquiva:
                rect_des = pygame.Rect(pos_tela.x, pos_tela.bottom - max(24, int(self.altura * 0.58)), pos_tela.width, max(24, int(self.altura * 0.58)))
            else:
                rect_des = pos_tela
            self.anim.desenhar(surface, rect_des, espelhar=not self.olhando_direita, escala_extra=ESCALA_SPRITE_MAPA)
        else:
            rect_fb = camera.aplicar(self.obter_hurtbox())
            pygame.draw.rect(surface, (230, 235, 245), rect_fb, border_radius=4)
            olho_x = rect_fb.x + (24 if self.olhando_direita else 6)
            pygame.draw.circle(surface, (25, 25, 35), (olho_x, rect_fb.y + 10), 4)

        if self.flash_armadilha > 0 or self.stagger_timer > 0:
            brilho = pygame.Surface((pos_tela.w + 10, pos_tela.h + 8), pygame.SRCALPHA)
            cor_b = (255, 195, 50, 95) if self.stagger_timer > 0 else (255, 65, 85, 90)
            pygame.draw.rect(brilho, cor_b, brilho.get_rect(), border_radius=5)
            surface.blit(brilho, (pos_tela.x - 5, pos_tela.y - 4))

        if self.atacando and self.hitbox_ataque:
            hitbox_tela = camera.aplicar(self.hitbox_ataque)
            cor_hb = (253, 230, 138) if self.atacando_baixo else (80, 245, 215)
            pygame.draw.rect(surface, cor_hb, hitbox_tela, 2, border_radius=4)


JogadorMapa = Jogador
__all__ = [
    "Jogador",
    "JogadorMapa",
    "ESQUIVA_IFRAMES",
    "DURACAO_ROLL_DASH",
    "COOLDOWN_ROLL_DASH",
    "VELOCIDADE_ROLL_DASH",
    "FORCA_SALTO_REACAO",
    "FORCA_POGO_BOUNCE",
]

