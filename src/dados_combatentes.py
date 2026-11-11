# -*- coding: utf-8 -*-
"""
Catálogo centralizado de dados dos combatentes, chefes e metadados de arena por sala.
Conecta os biomas 2.5D de `cenario_combate_25d.py` ao motor tático de `combate.py`.
"""

DADOS_BIOMAS_SALAS = {
    0: {
        "sala_num": 1,
        "arena_nome": "Pátio das Ameias da Muralha",
        "subtitulo_boss": "Arena do Capitão Orc",
        "chefe_padrao": "BOSS: GUARDIÃO DO CEMITÉRIO",
        "sprite_boss": "Boss_Guardiao",
        "tipo_fogo": "LARANJA",
    },
    1: {
        "sala_num": 2,
        "arena_nome": "Pátio da Cripta Sombria",
        "subtitulo_boss": "Arena do Lorde Demônio Vermillion",
        "chefe_padrao": "BOSS: ENTE DA ÁRVORE TORTA",
        "sprite_boss": "Boss_Ente",
        "tipo_fogo": "VERMELHO",
    },
    2: {
        "sala_num": 3,
        "arena_nome": "Fóvea dos Lamentos",
        "subtitulo_boss": "Arena da Amálgama Carmesim",
        "chefe_padrao": "BOSS: CARCEREIRO DOS PORTÕES",
        "sprite_boss": "Boss_Carcereiro",
        "tipo_fogo": "VERMELHO",
    },
    3: {
        "sala_num": 4,
        "arena_nome": "Torre Quebrada do Juramento",
        "subtitulo_boss": "Arena do Cavaleiro Corrompido",
        "chefe_padrao": "CHEFE: ZELADOR DO MAUSOLÉU",
        "sprite_boss": "Boss_Mausoleu",
        "tipo_fogo": "VIOLETA",
    },
    4: {
        "sala_num": 5,
        "arena_nome": "Catedrais Subterrâneas de Cantaria",
        "subtitulo_boss": "Arena da Gárgula Patriarca",
        "chefe_padrao": "CHEFE: SENTINELA DE PEDRA",
        "sprite_boss": "Boss_Sentinela",
        "tipo_fogo": "AZUL_ETER",
    },
    5: {
        "sala_num": 6,
        "arena_nome": "Santuário do Miasma Sangrento",
        "subtitulo_boss": "Arena do Sacerdote da Chama",
        "chefe_padrao": "CHEFE FINAL: REI DA LUA SANGRENTA",
        "sprite_boss": "Boss_ReiSangrento",
        "tipo_fogo": "VERMELHO",
    },
    6: {
        "sala_num": 7,
        "arena_nome": "O Vazio Absoluto",
        "subtitulo_boss": "Arena do Guardião do Vazio",
        "chefe_padrao": "CHEFE FINAL: BIBLIOTECÁRIO DO VAZIO",
        "sprite_boss": "Boss_Bibliotecario",
        "tipo_fogo": "CIANO_VAZIO",
    },
}


PERFIS_ARQUETIPOS = {
    "HEROI": {"ap_max": 6, "funcao": "Vanguarda", "destaque": (56, 189, 248)},
    "BRUTAMONTES": {"ap_max": 6, "funcao": "Colosso", "destaque": (245, 158, 11)},
    "ASSASSINO": {"ap_max": 6, "funcao": "Lâmina Veloz", "destaque": (244, 63, 94)},
    "MESTRE_PESTILENTO": {"ap_max": 6, "funcao": "Ocultista", "destaque": (168, 85, 247)},
    "CHEFE": {"ap_max": 8, "funcao": "Guardião", "destaque": (253, 224, 71)},
}


def normalizar_indice_sala(sala_atual):
    """Normaliza o índice da sala para o intervalo válido [0..6]."""
    try:
        idx = int(sala_atual)
    except (TypeError, ValueError):
        idx = 0
    return max(0, min(6, idx))


def obter_dados_arena_sala(sala_atual):
    """Retorna os metadados da arena 2.5D correspondentes à sala informada."""
    return DADOS_BIOMAS_SALAS[normalizar_indice_sala(sala_atual)]


def obter_titulo_arena(sala_atual, is_boss=False):
    """Formata o título contextual exibido na introdução do combate para a sala atual."""
    dados = obter_dados_arena_sala(sala_atual)
    if is_boss:
        return f"{dados['arena_nome']} — {dados['subtitulo_boss']}"
    return dados["arena_nome"]


def inferir_arquetipo_sprite(sprite_nome, is_boss=False):
    """Classifica o arquétipo tático de combate com base no sprite ou status de Chefe."""
    if is_boss:
        return "CHEFE"
    s_low = str(sprite_nome or "").lower()
    if any(k in s_low for k in ("gargula", "aberracao", "aberração", "monolith", "guardiao")):
        return "BRUTAMONTES"
    if any(k in s_low for k in ("cultista", "soldier", "assassino", "demon")):
        return "ASSASSINO"
    if any(k in s_low for k in ("espectro", "necromante", "bruxo", "blood")):
        return "MESTRE_PESTILENTO"
    return "BRUTAMONTES"

