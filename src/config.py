# -*- coding: utf-8 -*-
# ==============================================================================
# ELOS DO VAZIO - ARQUIVO DE CONFIGURAÇÃO DE BALANCEAMENTO (STATS)
# ==============================================================================
# Altere os valores abaixo para ajustar a dificuldade, dano, vida e AP do jogo.

CONFIG = {
    # Jogador (Cantriz)
    "jogador_hp_inicial": 120,
    "jogador_ap_inicial": 4,
    "jogador_max_ap": 6,

    # Inimigos Comuns (Salas 1, 2 e 3)
    "inimigo_hp_padrao": 140,
    "inimigo_dano_corte": 18,
    "inimigo_dano_esmagamento": 28,
    "inimigo_dano_rastria": 22,

    # Bosses (Fim de cada sala)
    "boss_sala1_hp": 280,
    "boss_sala2_hp": 360,
    "boss_sala3_hp": 460,

    # Itens Consumíveis no Inventário Inicial
    "pocoes_cura_inicial": 3,
    "cura_pocao_valor": 50,
    "cristais_ap_inicial": 2,
    "ap_cristal_valor": 3,

    # Configurações de Dano das Habilidades do Jogador (+20% de Dano)
    "habilidade_assalto_dano": 8.64,
    "habilidade_corte_dano": 11.52,
    "habilidade_danca_dano": 14.4,
    "habilidade_danca_custo": 6,
    "habilidade_cura_valor": 50,

    # Ataque exclusivo dos bosses: ONDA DE CHOQUE (so se evita pulando)
    "boss_dano_onda_choque": 30,           # dano base se nao pular (bosses ainda tem +25% de dano)
    "boss_contra_ataque_pulo_dano": 31.68, # dano do contra-ataque ao pular a onda (+20%: 26.4 * 1.2 = 31.68)

    # ------------------------------------------------------------------
    # MODO EXPOSIÇÃO / DEMONSTRAÇÃO (KIOSK / SHOWCASE MODE)
    # Configure para eventos, feiras de jogos e estandes de teste.
    # ------------------------------------------------------------------
    "modo_exposicao_ativo": False,             # Ativa limite de tempo e salas para feiras
    "exposicao_tempo_limite_segundos": 420,    # Tempo total por sessão em segundos (300s = 5 minutos)
    "exposicao_sala_limite": 5,                # Sala limite da demonstração (encerra ao cruzar o portal desta sala)

    # ------------------------------------------------------------------
    # Sprites - Tiny RPG Character Asset Pack (Zerie)
    # Extraia o pack dentro da pasta "assets". Nomes iguais aos das pastas/arquivos do pack.
    # Se um personagem nao existir, usa a lista "sprite_fallback"; se nada existir, usa retangulos.
    # ------------------------------------------------------------------
    "pasta_assets": "assets",
    "sprite_escala_mapa": 1.15,            # tamanho equilibrado dos sprites no mapa
    "sprite_jogador": "Hero",
    # Os inimigos e chefes de cada sala (e o sprite de cada um) ficam em cenarios.py,
    # junto do layout da sala. Os nomes sao os mesmos das pastas dentro de "assets".
    "sprite_fallback": ["Orc"],
}
