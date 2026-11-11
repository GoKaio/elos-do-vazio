# -*- coding: utf-8 -*-
"""
Suporte a sprites para o "Tiny RPG Character Asset Pack" (Zerie - itch.io).

Como usar:
  1. Baixe o pack em https://zerie.itch.io/tiny-rpg-character-asset-pack
     (a versao gratuita "Free Soldier&Orc" ja serve para comecar).
  2. Extraia o .zip dentro da pasta "assets" que fica ao lado do main.py
     (qualquer estrutura de subpastas funciona: o jogo procura os .png sozinho).
  3. Rode o jogo. Se algum personagem/animacao nao for encontrado, o jogo
     desenha os retangulos de antes (nada quebra).

O jogo reconhece arquivos no padrao  "<Personagem>-<Animacao>.png", por exemplo:
  Soldier-Idle.png, Soldier-Walk.png, Soldier-Attack01.png, Soldier-Hurt.png,
  Soldier-Death.png, Soldier-Block.png ...
Cada arquivo e uma tira horizontal de quadros quadrados (100x100 no pack);
o numero de quadros e calculado automaticamente (largura // altura).
"""
import os
import re
import unicodedata

import pygame

from config import CONFIG

_REGEX_ARQUIVO = re.compile(
    r"^(?P<nome>.*?)[\s_\-]*(?P<anim>idle|walk|run|attack[_\s]*pulo|attack[_\s]*parry|attack[_\s]*desvio|attack[_\s]*aereo|attack[_\s]*combo|attack\s*\d*|block|parry|jump|dodge|magic|cast|counter|hurt|damage|death|die)$",
    re.IGNORECASE,
)
_IGNORAR = ("effect", "arrow", "projectile")

_FPS_PADRAO = {
    "idle": 6, "walk": 10, "attack": 12, "attack2": 12, "attack3": 12,
    "attack_pulo": 10, "attack_parry": 10, "attack_desvio": 12,
    "attack_aereo": 10, "attack_combo": 12,
    "block": 10, "jump": 10, "dodge": 12, "magic": 10, "counter": 12,
    "hurt": 10, "death": 8
}


def _norm(texto):
    if not texto:
        return ""
    # Normaliza primeiro para NFC conforme solicitado para compatibilidade no Windows
    texto_nfc = unicodedata.normalize('NFC', str(texto))
    # Para a chave de dicionário, decompõe acentos para garantir casamento
    # ex: 'Aberração Hemática' -> 'aberracaohematica'
    nfkd = unicodedata.normalize('NFKD', texto_nfc)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def _chave_anim(texto):
    t = re.sub(r"[\s_\-]", "", texto.lower())
    if t == "run":
        return "walk"
    if t == "damage":
        return "hurt"
    if t == "die":
        return "death"
    if t in ("attack1", "attack01"):
        return "attack"
    if t in ("attack02", "attack2"):
        return "attack2"
    if t in ("attack03", "attack3"):
        return "attack3"
    if t in ("attackpulo", "attack_pulo"):
        return "attack_pulo"
    if t in ("attackparry", "attack_parry"):
        return "attack_parry"
    if t in ("attackdesvio", "attack_desvio"):
        return "attack_desvio"
    if t in ("attackaereo", "attack_aereo"):
        return "attack_aereo"
    if t in ("attackcombo", "attack_combo"):
        return "attack_combo"
    if t == "cast":
        return "magic"
    return t


def indexar_assets(pasta_raiz):
    """Varre pasta_raiz e agrupa arquivos por personagem com normalização NFC de caminhos."""
    indice = {}
    if not os.path.isdir(pasta_raiz):
        return indice

    for raiz, _, arquivos in os.walk(pasta_raiz):
        raiz_nfc = unicodedata.normalize('NFC', raiz)
        for arq in arquivos:
            arq_nfc = unicodedata.normalize('NFC', arq)
            if not arq_nfc.lower().endswith(".png"):
                continue
            base, _ = os.path.splitext(arq_nfc)
            if any(ign in base.lower() for ign in _IGNORAR):
                continue

            m = _REGEX_ARQUIVO.match(base)
            if not m:
                continue
            nome_raw = unicodedata.normalize('NFC', m.group("nome").strip(" -_"))
            anim_raw = m.group("anim")
            chave_p = _norm(nome_raw)
            if not chave_p:
                continue

            chave_a = _chave_anim(anim_raw)
            caminho = os.path.join(raiz_nfc, arq_nfc)

            if chave_p not in indice:
                indice[chave_p] = {"nome": nome_raw, "anims": {}}
            indice[chave_p]["anims"][chave_a] = caminho

    return indice


class Personagem:
    """Carrega as tiras de animacao e faz cache dos quadros escalados."""

    def __init__(self, nome, caminhos):
        self.nome = nome
        self.anims = {}
        self._cache = {}
        for chave, caminho in caminhos.items():
            quadros = self._carregar_tira(caminho)
            if quadros:
                self.anims[chave] = quadros
        if "idle" not in self.anims:
            raise ValueError("personagem sem animacao Idle")

        # Caixa que envolve o corpo (usada para alinhar os pes e escalar)
        x0 = y0 = 10 ** 9
        x1 = y1 = -1
        for q in self.anims["idle"]:
            r = q.get_bounding_rect()
            if r.width > 0 and r.height > 0:
                x0, y0 = min(x0, r.left), min(y0, r.top)
                x1, y1 = max(x1, r.right), max(y1, r.bottom)
        if x1 < 0:
            tam = self.anims["idle"][0].get_height()
            self.bbox = pygame.Rect(0, 0, tam, tam)
        else:
            self.bbox = pygame.Rect(x0, y0, x1 - x0, y1 - y0)

    @staticmethod
    def _carregar_tira(caminho):
        img = pygame.image.load(caminho).convert_alpha()
        alt, larg = img.get_height(), img.get_width()
        if alt <= 0:
            return []
        n = max(1, larg // alt)
        return [img.subsurface(pygame.Rect(i * alt, 0, alt, alt)).copy() for i in range(n)]

    def resolver(self, nome):
        if nome in self.anims:
            return nome
        if nome == "walk":
            return "idle" if "idle" in self.anims else None
        if nome == "attack2" and "attack" in self.anims:
            return "attack"
        if nome == "attack3":
            return "attack2" if "attack2" in self.anims else ("attack" if "attack" in self.anims else None)
        if nome == "attack_pulo":
            return "attack_pulo" if "attack_pulo" in self.anims else ("attack3" if "attack3" in self.anims else ("attack2" if "attack2" in self.anims else ("attack" if "attack" in self.anims else None)))
        if nome == "attack_aereo":
            return "attack_aereo" if "attack_aereo" in self.anims else ("attack_pulo" if "attack_pulo" in self.anims else ("attack3" if "attack3" in self.anims else ("attack" if "attack" in self.anims else None)))
        if nome == "attack_combo":
            return "attack_combo" if "attack_combo" in self.anims else ("attack2" if "attack2" in self.anims else ("attack" if "attack" in self.anims else None))
        if nome == "attack_parry":
            return "attack_parry" if "attack_parry" in self.anims else ("attack" if "attack" in self.anims else None)
        if nome == "attack_desvio":
            return "attack_desvio" if "attack_desvio" in self.anims else ("attack2" if "attack2" in self.anims else ("attack" if "attack" in self.anims else None))
        if nome in ("jump", "dodge"):
            return "walk" if "walk" in self.anims else ("idle" if "idle" in self.anims else None)
        if nome in ("block", "parry"):
            return "block" if "block" in self.anims else ("idle" if "idle" in self.anims else None)
        if nome in ("magic", "cast"):
            return "magic" if "magic" in self.anims else ("block" if "block" in self.anims else ("attack" if "attack" in self.anims else None))
        if nome == "counter":
            return "counter" if "counter" in self.anims else ("attack3" if "attack3" in self.anims else ("attack2" if "attack2" in self.anims else ("attack" if "attack" in self.anims else None)))
        return None

    def quadro(self, anim, idx, escala, espelhar):
        esc = min(15.0, max(0.25, round(escala * 4) / 4))
        chave = (anim, idx, esc, espelhar)
        img = self._cache.get(chave)
        if img is None:
            base = self.anims[anim][idx]
            w, h = base.get_size()
            target_w = max(1, min(1200, int(w * esc)))
            target_h = max(1, min(1200, int(h * esc)))
            try:
                img = pygame.transform.scale(base, (target_w, target_h))
            except (pygame.error, MemoryError):
                self._cache.clear()
                import gc
                gc.collect()
                img = base
            if espelhar:
                img = pygame.transform.flip(img, True, False)
            if len(self._cache) > 100:
                self._cache.clear()
            self._cache[chave] = img
        return img, esc


class Animador:
    """Toca uma animacao no tempo, com troca suave e retorno ao idle."""

    def __init__(self, personagem):
        self.personagem = personagem
        self.anim = None
        self.t = 0.0
        self.loop = True
        self.duracao_forcar = None
        self.retorno = "idle"
        if personagem and "idle" in personagem.anims:
            self.anim = "idle"

    @property
    def ativo(self):
        return self.personagem is not None and self.anim is not None

    def tocar(self, nome, loop=True, duracao=None, forcar=False, retorno="idle"):
        if not self.personagem:
            return
        real = self.personagem.resolver(nome)
        if not real:
            return
        if not forcar and self.duracao_forcar is not None:
            return
        if real == self.anim and self.loop == loop and not forcar:
            return
        self.anim = real
        self.t = 0.0
        self.loop = loop
        self.duracao_forcar = duracao
        self.retorno = retorno

    def _total(self, n_frames):
        if self.duracao_forcar:
            return self.duracao_forcar
        fps = _FPS_PADRAO.get(self.anim, 8)
        return max(0.05, n_frames / float(fps))

    def update(self, dt):
        if not self.ativo:
            return
        self.t += dt
        frames = self.personagem.anims[self.anim]
        total = self._total(len(frames))
        if self.t >= total:
            if self.loop:
                self.t = self.t % total
            else:
                self.duracao_forcar = None
                if self.retorno:
                    self.tocar(self.retorno, loop=True, forcar=True)

    def _indice(self, n):
        if self.loop:
            return int(self.t * _FPS_PADRAO.get(self.anim, 8)) % n
        return min(n - 1, int(min(self.t / self._total(n), 1.0) * n))

    def desenhar(self, surface, rect, espelhar=False, escala_extra=1.0):
        """Desenha com os pes no fundo do rect, centralizado, escalando pela altura do rect."""
        if not self.ativo:
            return
        p = self.personagem
        frames = p.anims[self.anim]
        idx = self._indice(len(frames))
        alt_clamped = max(10, min(420, rect.height))
        escala = (alt_clamped / float(max(1, p.bbox.height))) * escala_extra
        img, esc = p.quadro(self.anim, idx, escala, espelhar)
        w_base, h_base = p.anims[self.anim][idx].get_size()
        real_esc_x = img.get_width() / float(w_base)
        real_esc_y = img.get_height() / float(h_base)
        cx = p.bbox.centerx * real_esc_x
        if espelhar:
            cx = img.get_width() - cx
        pe = (p.bbox.bottom - 1) * real_esc_y - 2
        surface.blit(img, (int(rect.centerx - cx), int(rect.bottom - pe)))


# ----------------------------------------------------------------------------
_indice_cache = None
_personagens = {}
_BASE = os.path.dirname(os.path.abspath(__file__))


def _pasta_assets():
    pasta = CONFIG.get("pasta_assets", "assets")
    if not os.path.isabs(pasta):
        try:
            import caminhos
            return caminhos.obter_caminho_recurso(pasta)
        except Exception:
            return os.path.join(_BASE, pasta)
    return pasta


def _obter_indice():
    global _indice_cache
    if _indice_cache is None:
        pasta = _pasta_assets()
        if os.path.isdir(pasta):
            _indice_cache = indexar_assets(pasta)
        else:
            _indice_cache = {}
    return _indice_cache


_ALIASES = {
    # Mapeamento para os assets originais de alta qualidade
    "demoncarmesim": "demona",
    "demon_carmesim": "demona",
    "coveirosombrio": "demona",
    "caodocemiterio": "demona",
    "guardadoportao": "demona",
    "aberracaohematica": "demona",
    "aberracao_hematica": "demona",
    "necromante": "demona",
    "bloodmonstera": "bloodmonstera",
    "blood_monster_a": "bloodmonstera",
    "soldier": "soldier",
    "orc": "orc",
    "esqueleto": "esqueleto",
    # Chefes originais do projeto
    "bossguardiao": "bossguardiao",
    "boss_guardiao": "bossguardiao",
    "guardiaodocemiterio": "bossguardiao",
    "bossente": "bossente",
    "boss_ente": "bossente",
    "entedaarvoretorta": "bossente",
    "bosscarcereiro": "bosscarcereiro",
    "boss_carcereiro": "bosscarcereiro",
    "bosssentinela": "bosssentinela",
    "boss_sentinela": "bosssentinela",
    "bossmausoleu": "bossmausoleu",
    "boss_mausoleu": "bossmausoleu",
    "bossreisangrento": "bossreisangrento",
    "boss_reisangrento": "bossreisangrento",
    "bossbibliotecario": "bossbibliotecario",
    # Novos combatentes modulares
    "gargula": "gargula",
    "garguladepedra": "gargula",
    "gargula_de_pedra": "gargula",
    "gargulanoturna": "gargula",
    "gargula_noturna": "gargula",
    "cultista": "cultista",
    "cultistavoraz": "cultista",
    "cultista_voraz": "cultista",
    "espectro": "espectro",
    "espectrodopantano": "espectro",
    "espectro_do_pantano": "espectro",
    "guardiaovazio": "guardiaovazio",
    "guardiaodovazio": "guardiaovazio",
    "guardiao_do_vazio": "guardiaovazio",
}


def carregar_personagem(nome):
    chave = _norm(nome)
    if chave in _personagens:
        return _personagens[chave]
    indice = _obter_indice()
    entrada = indice.get(chave)
    if entrada is None and chave in _ALIASES:
        entrada = indice.get(_ALIASES[chave])
    if entrada is None:  # tolera nomes parecidos ("OrcRider" x "Orc rider")
        for k, v in indice.items():
            if chave and (chave in k or k in chave):
                entrada = v
                break
    personagem = None
    if entrada is not None:
        try:
            personagem = Personagem(entrada["nome"], entrada["anims"])
            try:
                print(f"[sprites] {entrada['nome']}: " +
                      " ".join(f"{k}({len(v)})" for k, v in personagem.anims.items()))
            except Exception:
                pass
        except Exception as erro:  # arquivo corrompido etc.
            try:
                print(f"[sprites] Falha ao carregar sprite: {erro}")
            except Exception:
                pass
    _personagens[chave] = personagem
    return personagem


def criar_animador(candidatos):
    """candidatos: nome, ou lista de nomes (tenta na ordem). Sem nada valido -> animador inativo."""
    if candidatos is None:
        return Animador(None)
    if isinstance(candidatos, str):
        candidatos = [candidatos]
    for nome in candidatos:
        if not nome:
            continue
        p = carregar_personagem(nome)
        if p is not None:
            return Animador(p)
    return Animador(None)


# ==============================================================================
# SISTEMA DE COMBATENTES MODULARES E COORDENADAS 2.5D (ELOS DO VAZIO)
# ==============================================================================

DISTANCIA_FOCAL = 380.0
CENTRO_PROJECAO_X = 480.0
CENTRO_PROJECAO_Y = 270.0

def projetar_ponto_25d(x, y, z, cam_x=0.0, cam_y=0.0, cam_z=0.0):
    """
    Projeção cônica de perspectiva tridimensional para coordenadas de tela 2D.
    Retorna (tela_x, tela_y, fator_profundidade).
    """
    rel_z = max(10.0, z - cam_z)
    fator = DISTANCIA_FOCAL / (DISTANCIA_FOCAL + rel_z)
    tela_x = CENTRO_PROJECAO_X + (x - cam_x) * fator
    tela_y = CENTRO_PROJECAO_Y + (y - cam_y) * fator
    return tela_x, tela_y, fator


class NovoCombatente:
    """
    Classe base modular para os novos combatentes no motor 2.5D de Elos do Vazio.
    Suporta posições tridimensionais (X, Y, Z), billboarding escalado seguro (0.3x a 4.0x),
    telegrafia de QTE e pool de ações dinâmicas.
    """
    def __init__(self, nome, hp_max, ap_max=6, arquetipo="BRUTAMONTES", sprite_nome=None, pos_mundo=None, is_boss=False):
        self.nome = unicodedata.normalize('NFC', str(nome))
        self.hp_max = int(hp_max)
        self.hp_atual = int(hp_max)
        self.ap_max = int(ap_max)
        self.ap_atual = int(ap_max // 2)
        self.arquetipo = arquetipo
        self.is_boss = is_boss
        self.pos_mundo = list(pos_mundo or [0.0, 0.0, 0.0])  # [X, Y, Z]
        self.pos_base = list(self.pos_mundo)
        self.pos_alvo = list(self.pos_mundo)
        self.sprite_nome = sprite_nome or nome
        self.animador = criar_animador([self.sprite_nome, "Hero" if arquetipo == "HEROI" else "Demon Carmesim"])
        self.debuffs = []
        self.vivo = True
        self.move_pool = []
        self.acao_atual = None
        self.tempo_acao = 0.0
        self.duracao_acao = 1.0
        self.janela_qte_ativa = False
        self.qte_tipo = None
        self.qte_tecla = None
        self.qte_aviso = ""
        self.cor_telegrafia = (255, 230, 80)
        is_b = self.is_boss
        if self.arquetipo == "HEROI":
            self.altura_base = 88.0
            self.largura_base = 65.0
            self.raio_mira = 22
        elif is_b:
            self.altura_base = 125.0
            self.largura_base = 95.0
            self.raio_mira = 36
        else:
            self.altura_base = 80.0
            self.largura_base = 65.0
            self.raio_mira = 20
        self.escala_base = 1.0 if not is_boss else 1.25
        self.y_offset = 0.0
        self.altura_projetada = int(self.altura_base * 0.65)
        self.tela_x = 0
        self.tela_y = 0
        self.escala_atual = 1.0
        self.ultimo_rect_25d = None
        self.configurar_move_pool()

    @property
    def x_mundo(self):
        return self.pos_mundo[0]

    @x_mundo.setter
    def x_mundo(self, val):
        self.pos_mundo[0] = float(val)

    @property
    def y_mundo(self):
        return self.pos_mundo[1]

    @y_mundo.setter
    def y_mundo(self, val):
        self.pos_mundo[1] = float(val)

    @property
    def z_mundo(self):
        return self.pos_mundo[2]

    @z_mundo.setter
    def z_mundo(self, val):
        self.pos_mundo[2] = float(val)

    def configurar_move_pool(self):
        """Define o catálogo modular de golpes e telegrafias de acordo com o arquétipo."""
        arq = self.arquetipo.upper()
        if arq == "HEROI":
            self.move_pool = [
                {
                    "id": "assalto",
                    "nome": "Assalto Rápido",
                    "custo_ap": 0,
                    "ganho_ap": 1,
                    "dano": 22,
                    "tipo_qte": "JOGADOR_GOLPE",
                    "tecla_qte": "Z",
                    "anim": "attack",
                    "descricao": "Corte ágil de adaga/espada (+1 AP).",
                    "debuff": "SANGRANDO"
                },
                {
                    "id": "corte_cosmico",
                    "nome": "Corte Cósmico",
                    "custo_ap": 2,
                    "ganho_ap": 0,
                    "dano": 36,
                    "tipo_qte": "JOGADOR_GOLPE",
                    "tecla_qte": "Z",
                    "anim": "attack2",
                    "descricao": "Lâmina estelar dupla (DoT Cósmico).",
                    "debuff": "QUEIMADURA"
                },
                {
                    "id": "orbe_vazio",
                    "nome": "Orbe do Vazio",
                    "custo_ap": 6,
                    "ganho_ap": 0,
                    "dano": 74,
                    "tipo_qte": "JOGADOR_GOLPE",
                    "tecla_qte": "Z",
                    "anim": "magic",
                    "descricao": "Disparo arcano com Fenda Temporal (+35% de dano).",
                    "debuff": "VULNERAVEL"
                }
            ]
        elif arq == "BRUTAMONTES":  # Gárgula de Pedra
            self.move_pool = [
                {
                    "id": "onda_choque",
                    "nome": "Onda de Choque",
                    "tipo_qte": "PULO",
                    "tecla_qte": "ESPAÇO",
                    "anim": "attack_pulo",
                    "dano": 28,
                    "tempo_impacto": 1.25,
                    "janela_inicio": 0.68,
                    "janela_fim": 0.98,
                    "aviso": "ONDA DE CHOQUE RASTEIRA! PULE [ESPAÇO]!",
                    "cor": (255, 205, 50),
                    "imparavel": False
                },
                {
                    "id": "salto_esmagador",
                    "nome": "Salto Esmagador",
                    "tipo_qte": "DESVIO_OU_PARRY",
                    "tecla_qte": "C / X",
                    "anim": "attack_aereo",
                    "dano": 38,
                    "tempo_impacto": 1.45,
                    "janela_inicio": 0.70,
                    "janela_fim": 1.02,
                    "aviso": "MERGULHO ESMAGADOR! DESVIE [C] OU PARRY [X] (PULO FALHA)!",
                    "cor": (255, 90, 80),
                    "imparavel": False
                }
            ]
        elif arq == "ASSASSINO":  # Cultista Voraz
            self.move_pool = [
                {
                    "id": "estocada_rapida",
                    "nome": "Estocada Rápida",
                    "tipo_qte": "PARRY",
                    "tecla_qte": "X",
                    "anim": "attack_parry",
                    "dano": 24,
                    "tempo_impacto": 0.95,
                    "janela_inicio": 0.65,
                    "janela_fim": 0.95,
                    "aviso": "ESTOCADA VELOZ! PARRY [X] OU DESVIO [C]!",
                    "cor": (255, 235, 110),
                    "imparavel": False
                },
                {
                    "id": "combo_duplo",
                    "nome": "Combo Duplo de Adagas",
                    "tipo_qte": "COMBO",
                    "tecla_qte": "X",
                    "anim": "attack_combo",
                    "dano": 34,
                    "golpes": 2,
                    "tempo_impacto": 1.30,
                    "janela_inicio": 0.55,
                    "janela_fim": 0.95,
                    "aviso": "GOLPE RÍTMICO DUPLO! PARRY [X] -> PARRY [X]!",
                    "cor": (255, 180, 50),
                    "imparavel": False
                }
            ]
        elif arq == "MESTRE_PESTILENTO":  # Espectro do Pântano
            self.move_pool = [
                {
                    "id": "nuvem_venenosa",
                    "nome": "Nuvem Venenosa",
                    "tipo_qte": "DESVIO",
                    "tecla_qte": "C",
                    "anim": "attack_desvio",
                    "dano": 32,
                    "tempo_impacto": 1.35,
                    "janela_inicio": 0.62,
                    "janela_fim": 0.98,
                    "aviso": "⚠ GOLPE IMPARÁVEL! ESQUIVA LATERAL OBRIGATÓRIA [C]!",
                    "cor": (90, 255, 120),
                    "imparavel": True
                },
                {
                    "id": "lamina_miasma",
                    "nome": "Lâmina de Miasma",
                    "tipo_qte": "PULO",
                    "tecla_qte": "ESPAÇO",
                    "anim": "attack_pulo",
                    "dano": 26,
                    "tempo_impacto": 1.15,
                    "janela_inicio": 0.65,
                    "janela_fim": 0.95,
                    "aviso": "FOGO-FÁTUO RASTEIRO! PULE [ESPAÇO]!",
                    "cor": (190, 110, 255),
                    "imparavel": False
                }
            ]
        elif arq == "CHEFE":  # Guardião do Vazio
            self.move_pool = [
                {
                    "id": "fenda_titanica",
                    "nome": "Fenda Titânica",
                    "tipo_qte": "PULO",
                    "tecla_qte": "ESPAÇO",
                    "anim": "attack_pulo",
                    "dano": 36,
                    "tempo_impacto": 1.30,
                    "janela_inicio": 0.66,
                    "janela_fim": 0.98,
                    "aviso": "ONDA CÓSMICA NO SOLO! PULE [ESPAÇO]!",
                    "cor": (255, 215, 60),
                    "imparavel": False
                },
                {
                    "id": "investida_colossal",
                    "nome": "Investida Colossal",
                    "tipo_qte": "PARRY",
                    "tecla_qte": "X",
                    "anim": "attack_parry",
                    "dano": 42,
                    "tempo_impacto": 1.20,
                    "janela_inicio": 0.65,
                    "janela_fim": 0.95,
                    "aviso": "ESTOCADA TITÂNICA! APARO PERFEITO PARRY [X]!",
                    "cor": (80, 240, 255),
                    "imparavel": False
                },
                {
                    "id": "julgamento_astral",
                    "nome": "Julgamento Astral",
                    "tipo_qte": "DESVIO_OU_PARRY",
                    "tecla_qte": "C / X",
                    "anim": "attack_aereo",
                    "dano": 50,
                    "tempo_impacto": 1.50,
                    "janela_inicio": 0.70,
                    "janela_fim": 1.02,
                    "aviso": "IMPACTO AÉREO DEVASTADOR! ESQUIVA [C] OU PARRY [X]!",
                    "cor": (255, 95, 95),
                    "imparavel": False
                },
                {
                    "id": "explosao_eclipse",
                    "nome": "Explosão do Eclipse",
                    "tipo_qte": "DESVIO",
                    "tecla_qte": "C",
                    "anim": "attack_desvio",
                    "dano": 46,
                    "tempo_impacto": 1.40,
                    "janela_inicio": 0.60,
                    "janela_fim": 0.96,
                    "aviso": "⚠ CHAMAS DO ECLIPSE (IMPARÁVEL)! DESVIE [C]!",
                    "cor": (255, 140, 40),
                    "imparavel": True
                }
            ]

    def iniciar_ataque(self, acao_dict):
        """Dispara uma ação de ataque e aciona a animação correspondente."""
        self.acao_atual = acao_dict
        self.tempo_acao = 0.0
        self.duracao_acao = acao_dict.get("tempo_impacto", 1.2)
        self.janela_qte_ativa = False
        anim_nome = acao_dict.get("anim", "attack")
        if self.animador and self.animador.ativo:
            self.animador.tocar(anim_nome, loop=False, duracao=self.duracao_acao, forcar=True, retorno="idle")

    def update(self, dt):
        """Atualiza animação, interpolação de posição 2.5D e janela de telegrafia."""
        lerp_fator = min(1.0, dt * 10.0)
        for i in range(3):
            self.pos_mundo[i] += (self.pos_alvo[i] - self.pos_mundo[i]) * lerp_fator

        if self.animador and self.animador.ativo:
            self.animador.update(dt)

        if self.acao_atual:
            self.tempo_acao += dt
            prog = self.tempo_acao / max(0.01, self.duracao_acao)
            inicio = self.acao_atual.get("janela_inicio", 0.65)
            fim = self.acao_atual.get("janela_fim", 0.95)
            self.janela_qte_ativa = (inicio <= prog <= fim)
            if self.tempo_acao >= self.duracao_acao:
                self.acao_atual = None
                self.janela_qte_ativa = False

    def obter_frame_atual(self):
        """Retorna o quadro de superfície atual do animador do personagem."""
        if self.animador and self.animador.ativo:
            p = self.animador.personagem
            if p and self.animador.anim in p.anims:
                frames = p.anims[self.animador.anim]
                if frames:
                    idx = self.animador._indice(len(frames))
                    return frames[idx]
        s = pygame.Surface((100, 100), pygame.SRCALPHA)
        cor = (110, 120, 135) if self.arquetipo == "HEROI" else ((160, 60, 60) if self.is_boss else (90, 100, 115))
        pygame.draw.rect(s, cor, (25, 20, 50, 75), border_radius=6)
        return s

    def desenhar_25d(self, superficie, tela_x=None, tela_y=None, escala_profundidade=None, cam_x=0.0, cam_y=0.0, cam_z=0.0, espelhar=None, offset_y_pulo=0.0):
        """
        Renderiza o combatente na posição tridimensional projetada com billboarding seguro
        e proporcionalidade anatômica perfeita via animador/bbox.
        """
        if tela_x is None or escala_profundidade is None:
            wx = self.pos_mundo[0]
            wy = self.pos_mundo[1] - offset_y_pulo
            wz = self.pos_mundo[2]
            tela_x, tela_y, fator = projetar_ponto_25d(wx, wy, wz, cam_x, cam_y, cam_z)
            escala_profundidade = fator

        escala_prof = max(0.3, min(4.0, escala_profundidade))
        alt_render = max(24, int(self.altura_base * escala_prof))
        larg_render = max(20, int(self.largura_base * escala_prof))

        # Ancora a base dos pés no ponto (tela_x, tela_y) do chão da arena
        rect_pe = pygame.Rect(int(tela_x - larg_render // 2), int(tela_y - alt_render), larg_render, alt_render)

        deve_espelhar = (self.arquetipo != "HEROI") if espelhar is None else espelhar

        if self.animador and self.animador.ativo:
            self.animador.desenhar(superficie, rect_pe, espelhar=deve_espelhar)
        else:
            frame_original = self.obter_frame_atual()
            sprite_escalado = pygame.transform.scale(frame_original, (larg_render, alt_render))
            if deve_espelhar:
                sprite_escalado = pygame.transform.flip(sprite_escalado, True, False)
            superficie.blit(sprite_escalado, rect_pe)

        self.ultimo_rect_25d = rect_pe
        self.rect_tela = rect_pe
        self.tela_x = int(tela_x)
        self.tela_y = int(tela_y)
        self.altura_projetada = alt_render
        self.escala_atual = escala_prof
        return rect_pe


def criar_gargula_pedra(x=260.0, y=140.0, z=120.0):
    return NovoCombatente("Gárgula de Pedra", hp_max=280, ap_max=6, arquetipo="BRUTAMONTES", sprite_nome="Gargula", pos_mundo=[x, y, z])

def criar_cultista_voraz(x=260.0, y=140.0, z=100.0):
    return NovoCombatente("Cultista Voraz", hp_max=180, ap_max=6, arquetipo="ASSASSINO", sprite_nome="Cultista", pos_mundo=[x, y, z])

def criar_espectro_pantano(x=250.0, y=135.0, z=130.0):
    return NovoCombatente("Espectro do Pântano", hp_max=220, ap_max=6, arquetipo="MESTRE_PESTILENTO", sprite_nome="Espectro", pos_mundo=[x, y, z])

def criar_guardiao_vazio(x=270.0, y=140.0, z=140.0):
    return NovoCombatente("Guardião do Vazio", hp_max=540, ap_max=8, arquetipo="CHEFE", sprite_nome="GuardiaoVazio", pos_mundo=[x, y, z], is_boss=True)

def criar_heroi_modular(x=-260.0, y=140.0, z=90.0, progresso=None):
    hp_base = 165
    if progresso:
        hp_base = progresso.max_hp_total()
    nome_h = getattr(progresso, "nome_heroi", "Viajante do Éter") if progresso else "Viajante do Éter"
    return NovoCombatente(
        nome=nome_h,
        hp_max=hp_base,
        ap_max=6,
        arquetipo="HEROI",
        sprite_nome=CONFIG.get("sprite_jogador", "Hero"),
        pos_mundo=[x, y, z]
    )
