# -*- coding: utf-8 -*-
"""
Prólogo Cinematográfico de Abertura - Elos do Vazio.

Orquestra a sequência inicial do jogo utilizando o motor modular
`cutscene.GerenciadorCutscenes` com barras letterbox deslizantes (52 px),
ruínas em paralaxe, silhuetas com rim-light e narração dourada em serif.
"""

import config
from cutscene import GerenciadorCutscenes

try:
    import sprites
except Exception:
    sprites = None


def _criar_roteiro_intro(heroi_nome):
    nome = str(heroi_nome or "Viajante").strip() or "Viajante"
    return [
        {
            "titulo_ato": "Prólogo — O Silêncio das Ruínas",
            "orador": "Crônica do Vazio",
            "texto": (
                "Quando os sete selos de Éter se partiram sobre a Cidadela, a última aurora "
                "mergulhou em cinzas e a lua pálida tornou-se vigia eterna dos mortos."
            ),
            "duracao": 5.8,
            "tempo_fade": 0.65,
            "silhueta": "vazio",
            "fundo": "cidadela",
            "sfx": "vento",
        },
        {
            "titulo_ato": "Ato I — O Chamado do Oráculo",
            "orador": "Oráculo das Cinzas",
            "texto": (
                f"Desperta, {nome}. Mesmo sob o véu do esquecimento, tua lâmina ainda guarda "
                "memória do fogo antigo e tua centelha recusa o silêncio do abismo."
            ),
            "duracao": 5.8,
            "tempo_fade": 0.55,
            "silhueta": "oraculo",
            "fundo": "cidadela",
            "sfx": "curar",
        },
        {
            "titulo_ato": "Ato II — O Juramento de Aço",
            "orador": nome,
            "texto": (
                "Se os guardiões caídos erguem muralhas entre este mundo e a alvorada, "
                "cruzarei cada câmara até devolver a luz aos Elos do Vazio."
            ),
            "duracao": 5.5,
            "tempo_fade": 0.55,
            "silhueta": "heroi",
            "fundo": "cidadela",
            "sfx": "espada",
        },
        {
            "titulo_ato": "Ato III — Às Portas da Expedição",
            "orador": "Crônica do Vazio",
            "texto": (
                "Domina o ritmo do aço e da esquiva. No silêncio das catacumbas, "
                "um único passo em falso separa a glória do esquecimento."
            ),
            "duracao": 5.2,
            "tempo_fade": 0.55,
            "silhueta": "guardiao",
            "fundo": "subterraneo",
            "sfx": "escudo",
        },
    ]


class CutsceneIntroducao:
    """Wrapper de alto nível para o prólogo cinematográfico em `cutscene.GerenciadorCutscenes`."""

    def __init__(self, heroi_nome="Kaelen", callback_conclusao=None):
        self.heroi_nome = str(heroi_nome or "Viajante")
        self.callback_conclusao = callback_conclusao

        anim_heroi = None
        if sprites is not None:
            try:
                sprite_nome = getattr(config, "sprite_jogador", "Hero")
                anim_heroi = sprites.criar_animador(sprite_nome)
            except Exception:
                anim_heroi = None

        self.motor = GerenciadorCutscenes(
            roteiro=_criar_roteiro_intro(self.heroi_nome),
            callback_fim=self.callback_conclusao,
            anim_heroi=anim_heroi,
            fundo_modo="cidadela",
            titulo_cena="ELOS DO VAZIO — PRÓLOGO",
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


IntroducaoCinematica = CutsceneIntroducao
