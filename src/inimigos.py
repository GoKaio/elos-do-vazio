# -*- coding: utf-8 -*-
"""
Módulo de Inimigos, Estados de Ataque e IA Single-Player — Elos do Vazio (`inimigos.py`).

Define os 5 arquétipos exclusivos com máquina de estados explícita em combate
(`PREPARANDO` -> `EXECUTANDO` -> `RECUPERACAO`), telegrafias visuais e exigência
precisa das 2 mecânicas obrigatórias de desvio do jogador único:
  1. CarnicalDasAmeias     -> BOTE_FENDIDO          (Exige Salto de Reação; bloqueio causa stagger)
  2. SentinelaDePedra      -> CLAVA_SISMICA         (Onda sísmica no solo; exige Salto de Reação)
  3. CultistaDaCripta      -> LANCA_DO_VAZIO        (Raio contínuo à meia-altura; exige Esquiva Rasteira)
  4. AlgozDasCatacumbas    -> GUILHOTINA_TRIPLICE   (3 cortes altos, 2º quebra parry; exige Esquiva Rasteira)
  5. GuardiaoDoSantuario   -> FURIA_ELOS_RUNICOS    (Correntes no chão -> Salto, depois detonações -> Rolamento)
"""

import math
import random
import pygame

from config import CONFIG
from sprites import criar_animador
import cenarios
import audio


ESCALA_SPRITE_MAPA = CONFIG.get("sprite_escala_mapa", 1.15)

ESTADO_PREPARANDO = "PREPARANDO"
ESTADO_EXECUTANDO = "EXECUTANDO"
ESTADO_RECUPERACAO = "RECUPERACAO"


_FONTES_CACHE = {}


def _obter_fonte(tam, bold=True):
    chave = (tam, bold)
    if chave not in _FONTES_CACHE:
        try:
            _FONTES_CACHE[chave] = pygame.font.SysFont("georgia", tam, bold=bold)
        except Exception:
            _FONTES_CACHE[chave] = pygame.font.Font(None, tam + 4)
    return _FONTES_CACHE[chave]


CATALOGO_ATAQUES_EXCLUSIVOS = {
    "BOTE_FENDIDO": {
        "classe": "CarnicalDasAmeias",
        "nome": "Bote Fendido",
        "contra_medida": "SALTO",
        "ignora_esquiva_chao": True,
        "exige_esquiva_rasteira": False,
        "quebra_guarda": True,
        "dano_mult": 1.10,
        "dur_preparando": 0.65,
        "dur_executando": 0.42,
        "dur_recuperacao": 0.75,
        "aviso": "BOTE FENDIDO! PULE [ESPAÇO] (BLOQUEIO DERRUBA)!",
        "cor": (255, 110, 50),
    },
    "CLAVA_SISMICA": {
        "classe": "SentinelaDePedra",
        "nome": "Clava Sísmica",
        "contra_medida": "SALTO",
        "ignora_esquiva_chao": True,
        "exige_esquiva_rasteira": False,
        "quebra_guarda": True,
        "dano_mult": 1.25,
        "dur_preparando": 0.85,
        "dur_executando": 0.72,
        "dur_recuperacao": 0.88,
        "aviso": "CLAVA SÍSMICA! SALTO DE REAÇÃO [ESPAÇO] SOBRE A ONDA!",
        "cor": (255, 65, 55),
    },
    "LANCA_DO_VAZIO": {
        "classe": "CultistaDaCripta",
        "nome": "Lança do Vazio",
        "contra_medida": "ESQUIVA_RASTEIRA",
        "ignora_esquiva_chao": False,
        "exige_esquiva_rasteira": True,
        "quebra_guarda": True,
        "dano_mult": 1.15,
        "dur_preparando": 0.85,
        "dur_executando": 0.56,
        "dur_recuperacao": 0.78,
        "aviso": "LANÇA DO VAZIO! ESQUIVA RASTEIRA [C / SHIFT] PARA PASSAR POR BAIXO!",
        "cor": (180, 90, 255),
    },
    "GUILHOTINA_TRIPLICE": {
        "classe": "AlgozDasCatacumbas",
        "nome": "Guilhotina Tríplice",
        "contra_medida": "ESQUIVA_RASTEIRA",
        "ignora_esquiva_chao": False,
        "exige_esquiva_rasteira": True,
        "quebra_guarda": True,
        "dano_mult": 1.20,
        "dur_preparando": 0.55,
        "dur_executando": 0.78,
        "dur_recuperacao": 0.86,
        "aviso": "GUILHOTINA TRÍPLICE (2º GOLPE QUEBRA PARRY)! ROLE [C / SHIFT]!",
        "cor": (244, 63, 94),
    },
    "FURIA_ELOS_RUNICOS": {
        "classe": "GuardiaoDoSantuario",
        "nome": "Fúria dos Elos Rúnicos",
        "contra_medida": "SALTO_E_ESQUIVA",
        "ignora_esquiva_chao": True,
        "exige_esquiva_rasteira": True,
        "quebra_guarda": True,
        "dano_mult": 1.35,
        "dur_preparando": 0.95,
        "dur_executando": 1.65,
        "dur_recuperacao": 1.05,
        "aviso": "FÚRIA DOS ELOS! PULE AS CORRENTES [ESPAÇO] E ROLE NA QUEDA [C]!",
        "cor": (56, 189, 248),
    },
}


def inferir_classe_inimigo(nome, sprite=None, is_boss=False):
    """Mapeia qualquer inimigo ou chefe das 7 salas para uma das 5 classes oficiais."""
    texto = f"{nome or ''} {sprite or ''}".lower()
    if is_boss or any(k in texto for k in ("guardiao", "guardião", "bibliotecario", "santuario", "santuário")):
        if not ("sentinela de pedra" in texto and not is_boss):
            return GuardiaoDoSantuario
    if any(k in texto for k in ("cultista", "necromante", "acólito", "acolito", "mago", "lich", "espectro", "demon_a")):
        return CultistaDaCripta
    if any(k in texto for k in ("algoz", "carrasco", "esqueleto", "pretor", "sombra", "demon carmesim", "demon_carmesim", "campeão", "campeao", "coveiro")):
        return AlgozDasCatacumbas
    if any(k in texto for k in ("sentinela", "gargula", "gárgula", "bruto", "golem", "blood", "aberracao", "aberração", "vigia")):
        return SentinelaDePedra
    return CarnicalDasAmeias


def inferir_id_ataque_exclusivo(nome, sprite=None, is_boss=False):
    cls = inferir_classe_inimigo(nome, sprite=sprite, is_boss=is_boss)
    return cls.ATAQUE_EXCLUSIVO


class InimigoBase:
    """
    Base comum dos inimigos 2D Single-Player com patrulha segura, IA de perseguição
    e máquina de estados para ataques exclusivos: PREPARANDO -> EXECUTANDO -> RECUPERACAO.
    """

    ATAQUE_EXCLUSIVO = "BOTE_FENDIDO"
    NOME_CLASSE = "InimigoBase"

    def __init__(self, x, y, dist_patrulha, nome, hp, cor, is_boss=False, num_combos=2, mapa=None, sprite=None):
        self.is_boss = bool(is_boss)
        self.largura = 68 if self.is_boss else 42
        self.altura = 88 if self.is_boss else 52
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)

        self.vel_patrulha = 90.0 if self.is_boss else 75.0
        self.vel_perseguir = 150.0 if self.is_boss else 135.0
        self.alcance_visao = 195 if isinstance(self, GuardiaoDoSantuario) else (400 if self.is_boss else 280)
        self.alcance_ataque = 210 if self.is_boss else 165
        self.dist_patrulha = dist_patrulha
        self.pos_inicial_x = float(x)

        self.nome = nome
        self.sprite_nome = sprite or nome
        self.hp = int(hp)
        self.max_hp = int(hp)
        self._hp_base = int(hp)
        self.cor = cor
        self.num_combos = int(num_combos)
        self.vivo = True
        self.debuffs = []

        self.direcao = random.choice((-1, 1))
        self.estado = "PATRULHA"
        self.timer_estado = 0.0
        self.tempo_perdeu = 0.0
        self.tempo_anim = random.uniform(0.0, 6.0)
        self.andando = False
        self.anim = criar_animador(sprite)

        # Máquina de estados do Ataque Exclusivo (PREPARANDO -> EXECUTANDO -> RECUPERACAO)
        self.estado_ataque = None
        self.timer_ataque_esp = 0.0
        self.duracao_fase = 0.0
        self.cooldown_ataque_esp = random.uniform(0.4, 1.0)
        self.hitboxes_ataque = []
        self.vulneravel_contra_ataque = False
        self.acertou_jogador_neste_ataque = False
        self.ondas_choque = []
        self.explosoes_aereas = []
        self.sub_golpe_idx = 0
        self.dano_base_ataque = int(CONFIG.get("inimigo_dano_esmagamento", 28) if self.is_boss else CONFIG.get("inimigo_dano_corte", 18))

        self._calcular_limites(mapa)

    def _calcular_limites(self, mapa):
        pe = self.y + self.altura
        plataforma = None
        if mapa:
            superficies = list(mapa["plataformas"]) + [
                p for p in mapa.get("paredes", []) if p.y > 120 and p.width >= 90
            ]
            candidatas = []
            for plat in superficies:
                sobre_plataforma = (self.x + self.largura > plat.left + 2 and self.x < plat.right - 2)
                diferenca = plat.top - pe
                if sobre_plataforma and -8 <= diferenca <= 95:
                    candidatas.append((abs(diferenca), plat))
            if candidatas:
                plataforma = min(candidatas, key=lambda item: item[0])[1]
                self.y = float(plataforma.top - self.altura)
                self.rect.y = int(self.y)
                pe = self.y + self.altura
            elif pe <= mapa["chao"].top and mapa["chao"].top - pe <= 95:
                self.y = float(mapa["chao"].top - self.altura)
                self.rect.y = int(self.y)
                pe = self.y + self.altura

        if plataforma is not None:
            self.cham_min = float(plataforma.left + 4)
            self.cham_max = float(plataforma.right - self.largura - 4)
        else:
            folga = 420 if self.is_boss else 260
            larg_m = mapa.get("largura", cenarios.LARGURA_MUNDO) if mapa else cenarios.LARGURA_MUNDO
            spawn_x = mapa.get("spawn_heroi", (100, 0))[0] if mapa else 100
            min_seguro = float(spawn_x + 260) if self.pos_inicial_x >= spawn_x + 320 else 40.0
            self.cham_min = max(min_seguro, self.pos_inicial_x - self.dist_patrulha - folga)
            self.cham_max = min(larg_m - self.largura - 40.0, self.pos_inicial_x + self.dist_patrulha + folga)

        if self.cham_min > self.cham_max:
            self.cham_min = self.cham_max = max(40.0, self.pos_inicial_x)

        self.pat_min = max(self.cham_min, self.pos_inicial_x - self.dist_patrulha)
        self.pat_max = min(self.cham_max, self.pos_inicial_x + self.dist_patrulha)
        if self.pat_min > self.pat_max:
            self.pat_min = self.pat_max = max(self.cham_min, min(self.cham_max, self.pos_inicial_x))
        self.pos_inicial_x = max(self.pat_min, min(self.pat_max, self.pos_inicial_x))
        self.x = max(self.cham_min, min(self.cham_max, self.x))
        self.rect.x = int(self.x)

    def resetar_comportamento(self):
        self.estado = "PATRULHA"
        self.timer_estado = 0.0
        self.tempo_perdeu = 0.0
        self.estado_ataque = None
        self.timer_ataque_esp = 0.0
        self.hitboxes_ataque.clear()
        self.ondas_choque.clear()
        self.explosoes_aereas.clear()
        self.vulneravel_contra_ataque = False
        self.acertou_jogador_neste_ataque = False

    def _mover(self, delta, minimo, maximo):
        self.x = max(minimo, min(maximo, self.x + delta))
        self.rect.x = int(self.x)

    def spec_ataque(self):
        return CATALOGO_ATAQUES_EXCLUSIVOS[self.ATAQUE_EXCLUSIVO]

    def iniciar_ataque_exclusivo(self, jogador=None):
        """Entra no estado PREPARANDO com aviso visual nítido para o jogador."""
        spec = self.spec_ataque()
        if jogador is not None:
            dx = (jogador.x + jogador.largura / 2.0) - (self.x + self.largura / 2.0)
            self.direcao = 1 if dx >= 0 else -1
        self.estado_ataque = ESTADO_PREPARANDO
        self.timer_ataque_esp = 0.0
        self.duracao_fase = spec["dur_preparando"]
        self.hitboxes_ataque.clear()
        self.ondas_choque.clear()
        self.explosoes_aereas.clear()
        self.vulneravel_contra_ataque = False
        self.acertou_jogador_neste_ataque = False
        self.sub_golpe_idx = 0

    def _ao_entrar_executando(self, jogador=None):
        pass

    def _atualizar_executando(self, dt, jogador=None):
        pass

    def _ao_entrar_recuperacao(self):
        self.hitboxes_ataque.clear()
        self.vulneravel_contra_ataque = True

    def _atualizar_maquina_ataque(self, dt, jogador):
        spec = self.spec_ataque()
        self.timer_ataque_esp += dt

        if self.estado_ataque == ESTADO_PREPARANDO:
            if self.timer_ataque_esp >= self.duracao_fase:
                self.estado_ataque = ESTADO_EXECUTANDO
                self.timer_ataque_esp = 0.0
                self.duracao_fase = spec["dur_executando"]
                self._ao_entrar_executando(jogador)
                if self.anim and self.anim.ativo:
                    self.anim.tocar("attack", loop=False, duracao=min(0.65, self.duracao_fase), forcar=True)

        elif self.estado_ataque == ESTADO_EXECUTANDO:
            self._atualizar_executando(dt, jogador)
            if self.timer_ataque_esp >= self.duracao_fase:
                self.estado_ataque = ESTADO_RECUPERACAO
                self.timer_ataque_esp = 0.0
                self.duracao_fase = spec["dur_recuperacao"]
                self._ao_entrar_recuperacao()

        elif self.estado_ataque == ESTADO_RECUPERACAO:
            if self.timer_ataque_esp >= self.duracao_fase:
                self.estado_ataque = None
                self.vulneravel_contra_ataque = False
                self.cooldown_ataque_esp = 1.15 if self.is_boss else 1.45

    def verificar_colisao_ataque(self, jogador):
        """
        Avalia colisão estritamente individual (1 jogador) contra as hitboxes
        ativas durante `EXECUTANDO`. Retorna o resultado de `jogador.sofrer_dano` ou None.
        """
        if not self.vivo or self.estado_ataque != ESTADO_EXECUTANDO or jogador is None:
            return None
        if self.acertou_jogador_neste_ataque:
            return None

        hurtbox = jogador.obter_hurtbox()
        for item in self.hitboxes_ataque:
            rect_h = item["rect"]
            if hurtbox.colliderect(rect_h):
                res = jogador.sofrer_dano(
                    dano=item.get("dano", self.dano_base_ataque),
                    tipo_ataque=self.ATAQUE_EXCLUSIVO,
                    quebra_guarda=item.get("quebra_guarda", True),
                    ignora_esquiva_chao=item.get("ignora_esquiva_chao", False),
                    exige_esquiva_rasteira=item.get("exige_esquiva_rasteira", False),
                    empurrao_x=self.direcao * 220.0,
                    chao_referencia_y=self.y + self.altura,
                )
                if res["atingido"]:
                    self.acertou_jogador_neste_ataque = True
                return res
        return None

    def sofrer_contra_ataque(self, dano_base):
        """Aplica bônus de punição (+50%) caso o inimigo esteja na janela RECUPERACAO."""
        mult = 1.50 if self.vulneravel_contra_ataque else 1.0
        dano_final = max(1, int(round(dano_base * mult)))
        self.hp = max(0, self.hp - dano_final)
        if self.hp <= 0:
            self.vivo = False
            self.estado_ataque = None
            self.hitboxes_ataque.clear()
        if self.anim and self.anim.ativo:
            self.anim.tocar("hurt" if self.vivo else "death", loop=False, duracao=0.35, forcar=True)
        return dano_final

    def update(self, dt, jogador=None):
        if not self.vivo:
            return
        self.tempo_anim += dt
        self.cooldown_ataque_esp = max(0.0, self.cooldown_ataque_esp - dt)
        self.andando = False

        if self.estado_ataque is not None:
            self._atualizar_maquina_ataque(dt, jogador)
            if self.anim and self.anim.ativo:
                self.anim.update(dt)
            return

        ve_jogador = False
        dx = 0.0
        if jogador is not None:
            dx = (jogador.x + jogador.largura / 2.0) - (self.x + self.largura / 2.0)
            mesmo_nivel = abs((jogador.y + jogador.altura) - (self.y + self.altura)) <= 90
            perseguindo = self.estado == "PERSEGUIR"
            alcance = self.alcance_visao * (1.5 if perseguindo else 1.0)
            na_frente = (dx * self.direcao) >= -100
            ve_jogador = mesmo_nivel and abs(dx) <= alcance and (na_frente or perseguindo)

        if self.estado in ("PATRULHA", "PAUSA", "VOLTAR") and ve_jogador:
            self.estado = "ALERTA"
            self.timer_estado = 0.25 if self.is_boss else 0.35
            self.direcao = 1 if dx >= 0 else -1

        if self.estado == "PATRULHA":
            self._mover(self.direcao * self.vel_patrulha * dt, self.pat_min, self.pat_max)
            self.andando = True
            if (self.direcao > 0 and self.x >= self.pat_max) or (self.direcao < 0 and self.x <= self.pat_min):
                self.estado = "PAUSA"
                self.timer_estado = random.uniform(0.5, 1.1)
                self.andando = False

        elif self.estado == "PAUSA":
            self.timer_estado -= dt
            if self.timer_estado <= 0:
                self.direcao *= -1
                self.estado = "PATRULHA"

        elif self.estado == "ALERTA":
            self.direcao = 1 if dx >= 0 else -1
            self.timer_estado -= dt
            if self.timer_estado <= 0:
                self.estado = "PERSEGUIR"
                self.tempo_perdeu = 0.0

        elif self.estado == "PERSEGUIR":
            if ve_jogador:
                self.tempo_perdeu = 0.0
            else:
                self.tempo_perdeu += dt
                if self.tempo_perdeu >= 1.6:
                    self.estado = "VOLTAR"
            if abs(dx) <= self.alcance_ataque and ve_jogador and self.cooldown_ataque_esp <= 0.0:
                self.iniciar_ataque_exclusivo(jogador)
                return
            if abs(dx) > 6:
                self.direcao = 1 if dx > 0 else -1
                antes = self.x
                self._mover(self.direcao * self.vel_perseguir * dt, self.cham_min, self.cham_max)
                self.andando = abs(self.x - antes) > 0.01

        elif self.estado == "VOLTAR":
            alvo = self.pos_inicial_x
            distancia = alvo - self.x
            if abs(distancia) <= 4.0:
                self.estado = "PATRULHA"
            else:
                self.direcao = 1 if distancia > 0 else -1
                passo = min(abs(distancia), self.vel_patrulha * dt)
                self._mover(self.direcao * passo, self.cham_min, self.cham_max)
                self.andando = True

        if self.anim and self.anim.ativo:
            self.anim.tocar("walk" if self.andando else "idle")
            self.anim.update(dt)

    def desenhar_telegraph_e_ataque(self, surface, camera):
        """Desenha avisos visuais de PREPARANDO, hitboxes de EXECUTANDO e janela RECUPERACAO."""
        if self.estado_ataque is None:
            return
        pos_tela = camera.aplicar(self.rect)
        spec = self.spec_ataque()
        cor = spec["cor"]
        prog = min(1.0, self.timer_ataque_esp / max(0.01, self.duracao_fase))

        if self.estado_ataque == ESTADO_PREPARANDO:
            pulso = int(120 + 135 * abs(math.sin(self.tempo_anim * 16.0)))
            halo = pygame.Surface((pos_tela.width + 24, pos_tela.height + 24), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (*cor, min(200, pulso)), halo.get_rect(), 3)
            surface.blit(halo, (pos_tela.x - 12, pos_tela.y - 12))

            f_av = _obter_fonte(13, True)
            rotulo = "SALTE!" if spec["contra_medida"] == "SALTO" else ("ROLE!" if spec["contra_medida"] == "ESQUIVA_RASTEIRA" else "SALTE -> ROLE!")
            txt = f_av.render(f"! {rotulo}", True, cor)
            surface.blit(txt, (pos_tela.centerx - txt.get_width() // 2, pos_tela.top - 22))
            self._desenhar_telegrafo_especifico(surface, camera, pos_tela, prog)

        elif self.estado_ataque == ESTADO_EXECUTANDO:
            self._desenhar_hitboxes_execucao(surface, camera, cor)

        elif self.estado_ataque == ESTADO_RECUPERACAO:
            f_rec = _obter_fonte(12, True)
            txt = f_rec.render("VULNERÁVEL", True, (80, 255, 195))
            surface.blit(txt, (pos_tela.centerx - txt.get_width() // 2, pos_tela.top - 20))
            pygame.draw.rect(surface, (80, 255, 195), pos_tela.inflate(6, 6), 2, border_radius=5)

    def _desenhar_telegrafo_especifico(self, surface, camera, pos_tela, prog):
        y_line = pos_tela.bottom - 8
        x1 = pos_tela.centerx + self.direcao * int(180 * prog)
        pygame.draw.line(surface, (255, 120, 60), (pos_tela.centerx, y_line), (x1, y_line), 3)

    def _desenhar_hitboxes_execucao(self, surface, camera, cor):
        for item in self.hitboxes_ataque:
            rt = camera.aplicar(item["rect"])
            s = pygame.Surface((max(4, rt.width), max(4, rt.height)), pygame.SRCALPHA)
            s.fill((*cor, 130))
            surface.blit(s, rt.topleft)
            pygame.draw.rect(surface, (255, 245, 200), rt, 2)

    def draw(self, surface, camera):
        if not self.vivo:
            return
        pos_tela = camera.aplicar(self.rect)
        sombra_w = 42 if self.is_boss else 26
        sombra_h = 10 if self.is_boss else 6
        sombra = pygame.Surface((sombra_w * 2, sombra_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 140 if self.is_boss else 110),
                            (sombra_w // 2, sombra_h // 2, sombra_w, sombra_h))
        surface.blit(sombra, (pos_tela.centerx - sombra_w, pos_tela.bottom - sombra_h // 2))

        olhar = self.direcao
        if self.anim and self.anim.ativo:
            self.anim.desenhar(surface, pos_tela, espelhar=(olhar < 0), escala_extra=ESCALA_SPRITE_MAPA)
            if self.is_boss:
                lbl = _obter_fonte(14, True).render(self.nome, True, (255, 220, 110))
                surface.blit(lbl, (pos_tela.centerx - lbl.get_width() // 2, pos_tela.top - 40))
        elif self.is_boss:
            pygame.draw.rect(surface, (40, 20, 55), pos_tela.inflate(12, 12), border_radius=8)
            pygame.draw.rect(surface, self.cor, pos_tela, border_radius=6)
            pygame.draw.rect(surface, (255, 215, 90), pos_tela, 3, border_radius=6)
            lbl = _obter_fonte(14, True).render(self.nome, True, (255, 220, 110))
            surface.blit(lbl, (pos_tela.centerx - lbl.get_width() // 2, pos_tela.top - 40))
        else:
            pygame.draw.rect(surface, self.cor, pos_tela, border_radius=4)
            pygame.draw.rect(surface, (255, 130, 140), pos_tela, 2, border_radius=4)
            pygame.draw.circle(surface, (255, 235, 90), (pos_tela.centerx + olhar * 8, pos_tela.y + 16), 5)

        self.desenhar_telegraph_e_ataque(surface, camera)

        if self.estado in ("ALERTA", "PERSEGUIR") and self.estado_ataque is None:
            cor_alerta = (255, 90, 80) if self.estado == "PERSEGUIR" else (255, 230, 90)
            lbl_a = _obter_fonte(24, True).render("!", True, cor_alerta)
            topo = pos_tela.top - (56 if self.is_boss else 26)
            surface.blit(lbl_a, (pos_tela.centerx - lbl_a.get_width() // 2, topo))


# ==============================================================================
# OS 5 INIMIGOS COM ATAQUES EXCLUSIVOS E TELEGRAFIAS ÚNICAS
# ==============================================================================
class CarnicalDasAmeias(InimigoBase):
    """Inimigo 1: Rastejador Veloz — Ataque Exclusivo: BOTE FENDIDO."""

    ATAQUE_EXCLUSIVO = "BOTE_FENDIDO"
    NOME_CLASSE = "CarnicalDasAmeias"

    def _ao_entrar_executando(self, jogador=None):
        audio.tocar_sfx("dodge", 0.90)

    def _atualizar_executando(self, dt, jogador=None):
        self._mover(self.direcao * 485.0 * dt, self.cham_min, self.cham_max)
        hb = pygame.Rect(int(self.x - 6), int(self.y + self.altura - 28), self.largura + 12, 28)
        self.hitboxes_ataque = [{
            "rect": hb,
            "dano": int(self.dano_base_ataque * 1.15),
            "quebra_guarda": True,
            "ignora_esquiva_chao": True,
            "exige_esquiva_rasteira": False,
        }]


class SentinelaDePedra(InimigoBase):
    """Inimigo 2: Guerreiro Pesado — Ataque Exclusivo: CLAVA SÍSMICA (Ground Slam)."""

    ATAQUE_EXCLUSIVO = "CLAVA_SISMICA"
    NOME_CLASSE = "SentinelaDePedra"

    def _ao_entrar_executando(self, jogador=None):
        y_solo = self.y + self.altura
        cx = self.x + self.largura / 2.0
        self.ondas_choque = [
            {"x": cx, "dir": -1, "w": 36, "h": 26, "vel": 365.0},
            {"x": cx, "dir": 1, "w": 36, "h": 26, "vel": 365.0},
        ]
        self._y_solo_onda = y_solo
        audio.tocar_sfx("boss_hit", 0.90)

    def _atualizar_executando(self, dt, jogador=None):
        self.hitboxes_ataque.clear()
        for onda in self.ondas_choque:
            onda["x"] += onda["dir"] * onda["vel"] * dt
            r_onda = pygame.Rect(int(onda["x"] - onda["w"] / 2), int(self._y_solo_onda - onda["h"]), onda["w"], onda["h"])
            self.hitboxes_ataque.append({
                "rect": r_onda,
                "dano": int(self.dano_base_ataque * 1.25),
                "quebra_guarda": True,
                "ignora_esquiva_chao": True,
                "exige_esquiva_rasteira": False,
            })

    def _desenhar_telegrafo_especifico(self, surface, camera, pos_tela, prog):
        r_runa = int(16 + 18 * prog)
        cx, cy = pos_tela.centerx, pos_tela.top - 10
        pygame.draw.circle(surface, (255, 65, 55), (cx, cy), r_runa, 3)

    def _desenhar_hitboxes_execucao(self, surface, camera, cor):
        for item in self.hitboxes_ataque:
            rt = camera.aplicar(item["rect"])
            pts = [(rt.left, rt.bottom), (rt.centerx, rt.top - 8), (rt.right, rt.bottom)]
            pygame.draw.polygon(surface, (255, 110, 45), pts)
            pygame.draw.polygon(surface, (254, 240, 138), pts, 2)


class CultistaDaCripta(InimigoBase):
    """Inimigo 3: Mago de Éter Escuro — Ataque Exclusivo: LANÇA DO VAZIO."""

    ATAQUE_EXCLUSIVO = "LANCA_DO_VAZIO"
    NOME_CLASSE = "CultistaDaCripta"

    def _ao_entrar_executando(self, jogador=None):
        # Raio espesso à meia-altura e acima da cabeça: apenas hitbox reduzida (Esquiva Rasteira) escapa!
        alcance = 460
        x0 = self.x + self.largura if self.direcao > 0 else self.x - alcance
        y_topo = int(self.y - 34)
        alt_feixe = max(22, self.altura - 30 + 34)
        self.hitboxes_ataque = [{
            "rect": pygame.Rect(int(x0), y_topo, alcance, alt_feixe),
            "dano": int(self.dano_base_ataque * 1.15),
            "quebra_guarda": True,
            "ignora_esquiva_chao": False,
            "exige_esquiva_rasteira": True,
        }]
        audio.tocar_sfx("shock", 0.90)

    def _desenhar_telegrafo_especifico(self, surface, camera, pos_tela, prog):
        x0 = pos_tela.right if self.direcao > 0 else pos_tela.left
        x1 = x0 + self.direcao * 420
        ym = pos_tela.centery - 6
        pygame.draw.line(surface, (190, 95, 255), (x0, ym), (x1, ym), max(1, int(4 * prog)))

    def _desenhar_hitboxes_execucao(self, surface, camera, cor):
        for item in self.hitboxes_ataque:
            rt = camera.aplicar(item["rect"])
            s = pygame.Surface((rt.width, rt.height), pygame.SRCALPHA)
            s.fill((147, 51, 234, 175))
            pygame.draw.rect(s, (224, 242, 254, 235), (0, rt.height // 3, rt.width, max(6, rt.height // 3)))
            surface.blit(s, rt.topleft)
            pygame.draw.rect(surface, (233, 213, 255), rt, 2)


class AlgozDasCatacumbas(InimigoBase):
    """Inimigo 4: Assassino Ágil — Ataque Exclusivo: GUILHOTINA TRÍPLICE."""

    ATAQUE_EXCLUSIVO = "GUILHOTINA_TRIPLICE"
    NOME_CLASSE = "AlgozDasCatacumbas"

    def _ao_entrar_executando(self, jogador=None):
        if jogador is not None:
            dx = (jogador.x + jogador.largura / 2.0) - (self.x + self.largura / 2.0)
            self.direcao = 1 if dx >= 0 else -1
            # Teleporte curto para a frente do alvo
            alvo_x = jogador.x - self.direcao * (self.largura + 18)
            self.x = max(self.cham_min, min(self.cham_max, alvo_x))
            self.rect.x = int(self.x)
        self.sub_golpe_idx = 0
        audio.tocar_sfx("sword_crit", 0.90)

    def _atualizar_executando(self, dt, jogador=None):
        sub_novo = min(2, int(self.timer_ataque_esp / max(0.05, self.duracao_fase / 3.0)))
        if sub_novo != self.sub_golpe_idx:
            self.sub_golpe_idx = sub_novo
            self.acertou_jogador_neste_ataque = False
            self._mover(self.direcao * 26.0, self.cham_min, self.cham_max)
            audio.tocar_sfx("sword", 0.95)
        alc = 68
        hx = int(self.x + self.largura - 6) if self.direcao > 0 else int(self.x - alc + 6)
        # Cortes em arco alto: hitbox ocupa apenas a metade superior (Esquiva Rasteira passa por baixo!)
        hb = pygame.Rect(hx, int(self.y - 10), alc, max(22, self.altura - 30 + 10))
        self.hitboxes_ataque = [{
            "rect": hb,
            "dano": int(self.dano_base_ataque * 0.65),
            "quebra_guarda": (self.sub_golpe_idx >= 1),  # 2º golpe quebra o parry!
            "ignora_esquiva_chao": False,
            "exige_esquiva_rasteira": True,
        }]

    def _desenhar_hitboxes_execucao(self, surface, camera, cor):
        for item in self.hitboxes_ataque:
            rt = camera.aplicar(item["rect"])
            sa = pygame.Surface((rt.width + 16, rt.height + 16), pygame.SRCALPHA)
            ini, fim = (-0.9, 0.9) if self.direcao > 0 else (math.pi - 0.9, math.pi + 0.9)
            pygame.draw.arc(sa, (244, 63, 94, 230), (4, 4, rt.width + 8, rt.height + 8), ini, fim, 6)
            pygame.draw.arc(sa, (254, 240, 138, 240), (8, 8, rt.width, rt.height), ini, fim, 3)
            surface.blit(sa, (rt.x - 8, rt.y - 8))


class GuardiaoDoSantuario(InimigoBase):
    """Inimigo 5: Chefe Supremo da Sala 7 — Ataque Exclusivo: FÚRIA DOS ELOS RÚNICOS."""

    ATAQUE_EXCLUSIVO = "FURIA_ELOS_RUNICOS"
    NOME_CLASSE = "GuardiaoDoSantuario"

    def _ao_entrar_executando(self, jogador=None):
        self._y_solo_arena = self.y + self.altura
        self.sub_golpe_idx = 0
        audio.tocar_sfx("boss_hit", 1.0)

    def _atualizar_executando(self, dt, jogador=None):
        self.hitboxes_ataque.clear()
        cx = self.x + self.largura / 2.0
        # Sub-fase 1 (0..0.80s): Correntes espectrais varrendo o piso -> Exige SALTO DE REAÇÃO
        if self.timer_ataque_esp < 0.80:
            alc = 360
            r_correntes = pygame.Rect(int(cx - alc / 2), int(self._y_solo_arena - 24), alc, 24)
            self.hitboxes_ataque.append({
                "rect": r_correntes,
                "dano": int(self.dano_base_ataque * 1.10),
                "quebra_guarda": True,
                "ignora_esquiva_chao": True,
                "exige_esquiva_rasteira": False,
            })
        else:
            # Sub-fase 2 (0.80..1.65s): Detonações aéreas acima do nível do rolamento -> Exige ROLL DASH ao cair
            if self.sub_golpe_idx == 0:
                self.sub_golpe_idx = 1
                self.acertou_jogador_neste_ataque = False
                audio.tocar_sfx("shock", 0.95)
            for off_x in (-130, 0, 130):
                r_exp = pygame.Rect(int(cx + off_x - 42), int(self._y_solo_arena - 110), 84, 82)
                self.hitboxes_ataque.append({
                    "rect": r_exp,
                    "dano": int(self.dano_base_ataque * 1.25),
                    "quebra_guarda": True,
                    "ignora_esquiva_chao": False,
                    "exige_esquiva_rasteira": True,
                })

    def _desenhar_telegrafo_especifico(self, surface, camera, pos_tela, prog):
        y_fissura = pos_tela.bottom - 4
        pygame.draw.line(surface, (56, 189, 248), (pos_tela.centerx - 170, y_fissura), (pos_tela.centerx + 170, y_fissura), 3)
        for ox in (-130, 0, 130):
            pygame.draw.circle(surface, (244, 63, 94), (pos_tela.centerx + ox, pos_tela.bottom - 72), int(18 * prog), 2)

    def _desenhar_hitboxes_execucao(self, surface, camera, cor):
        if self.timer_ataque_esp < 0.80:
            for item in self.hitboxes_ataque:
                rt = camera.aplicar(item["rect"])
                for ex in range(rt.left, rt.right, 16):
                    pygame.draw.rect(surface, (56, 189, 248), (ex, rt.centery - 4, 12, 8), 2)
                pygame.draw.rect(surface, (224, 242, 254), rt, 1)
        else:
            for item in self.hitboxes_ataque:
                rt = camera.aplicar(item["rect"])
                s = pygame.Surface((rt.width, rt.height), pygame.SRCALPHA)
                pygame.draw.circle(s, (244, 63, 94, 170), (rt.width // 2, rt.height // 2), min(rt.width, rt.height) // 2)
                pygame.draw.circle(s, (254, 240, 138, 220), (rt.width // 2, rt.height // 2), min(rt.width, rt.height) // 3, 2)
                surface.blit(s, rt.topleft)


def criar_inimigo_mapa(x, y, dist_patrulha, nome, hp, cor, is_boss=False, num_combos=2, mapa=None, sprite=None):
    """Fábrica que instancia automaticamente a classe de inimigo correspondente."""
    cls = inferir_classe_inimigo(nome, sprite=sprite, is_boss=is_boss)
    return cls(
        x=x, y=y, dist_patrulha=dist_patrulha, nome=nome, hp=hp, cor=cor,
        is_boss=is_boss, num_combos=num_combos, mapa=mapa, sprite=sprite,
    )


InimigoMapa = criar_inimigo_mapa

__all__ = [
    "ESTADO_PREPARANDO",
    "ESTADO_EXECUTANDO",
    "ESTADO_RECUPERACAO",
    "CATALOGO_ATAQUES_EXCLUSIVOS",
    "InimigoBase",
    "CarnicalDasAmeias",
    "SentinelaDePedra",
    "CultistaDaCripta",
    "AlgozDasCatacumbas",
    "GuardiaoDoSantuario",
    "InimigoMapa",
    "criar_inimigo_mapa",
    "inferir_classe_inimigo",
    "inferir_id_ataque_exclusivo",
]
