# -*- coding: utf-8 -*-
"""
ENDBOUND - Progresso salvo (perfis isolados, tempo acumulado contínuo, ranks por sala,
nível, poções, cristais de éter e sistema de Tentativas/Vidas).

Guarda em perfis/perfil_<nome>.json e em endbound_save.json (perfil ativo):
  nome_usuario              -> nome do perfil ativo
  sala_atual                -> sala atual (1-based)
  tempo_acumulado_segundos  -> cronômetro acumulado persistente por usuário
  vidas                     -> tentativas restantes (máximo 3)
  hp_atual                  -> HP atual na sala ativa
  ranks                     -> melhores ranks obtidos por sala / modo
"""
import json
import os
import re

from config import CONFIG
from caminhos import obter_caminho_save, obter_dir_dados, log_info, log_erro

ARQUIVO_SAVE = obter_caminho_save()
DIR_PERFIS = os.path.join(obter_dir_dados(), "perfis")
NUM_SALAS = 7
TENTATIVAS_MAX = 3

_ORDEM_RANK = {"S": 4, "A": 3, "B": 2, "C": 1}


def _sanitizar_slug_perfil(nome_usuario):
    texto = str(nome_usuario or "").strip().lower()
    slug = re.sub(r"[^a-z0-9_-]+", "_", texto).strip("_")
    return slug or "padrao"


def obter_caminho_perfil(nome_usuario):
    return os.path.join(DIR_PERFIS, f"perfil_{_sanitizar_slug_perfil(nome_usuario)}.json")


class Progresso:
    def __init__(self):
        self.nivel = 1
        self.xp = 0
        self.xp_proximo = 80
        self.max_hp_base = CONFIG["jogador_hp_inicial"]
        self.max_hp = self.max_hp_total()
        self.tentativas_max = TENTATIVAS_MAX
        self.tentativas = TENTATIVAS_MAX
        self.nome_heroi = "Guerreiro"
        self._tempo_acumulado_segundos = 0.0
        self.tempo_sala_atual = 0.0
        self.tentativas_gastas = 1
        self.vida = {i: None for i in range(NUM_SALAS)}   # None = sala ainda não visitada
        self.chefes = set()
        self.ultima_sala = 0
        self.pocoes_encontradas = 0
        self.cristais_encontrados = 0
        self.ranks = {}
        self.ranks_detalhes = {}
        self.carregar()

    @property
    def tempo_acumulado_segundos(self):
        return self._tempo_acumulado_segundos

    @tempo_acumulado_segundos.setter
    def tempo_acumulado_segundos(self, valor):
        self._tempo_acumulado_segundos = max(0.0, float(valor or 0.0))

    @property
    def tempo_decorrido(self):
        """Tempo contínuo total exibido: tempo acumulado salvo + tempo decorrido na sala atual."""
        return self._tempo_acumulado_segundos + self.tempo_sala_atual

    @tempo_decorrido.setter
    def tempo_decorrido(self, valor):
        val = max(0.0, float(valor or 0.0))
        if val == 0.0:
            self._tempo_acumulado_segundos = 0.0
            self.tempo_sala_atual = 0.0
        elif val >= self._tempo_acumulado_segundos:
            self.tempo_sala_atual = val - self._tempo_acumulado_segundos
        else:
            self._tempo_acumulado_segundos = val
            self.tempo_sala_atual = 0.0

    def avancar_tempo(self, dt):
        """Incrementa o cronômetro da sala ativa sem alterar a base acumulada salva."""
        self.tempo_sala_atual += max(0.0, float(dt or 0.0))

    def consolidar_tempo_sala(self):
        """Incorpora o tempo da sala atual ao tempo acumulado antes de trocar de fase ou salvar."""
        if self.tempo_sala_atual > 0.0:
            self._tempo_acumulado_segundos += self.tempo_sala_atual
            self.tempo_sala_atual = 0.0

    def tempo_total_exibicao(self):
        return self._tempo_acumulado_segundos + self.tempo_sala_atual

    def registrar_rank_sala(self, sala_chave, rank_letra, pontuacao=0, sem_avaria=False):
        """Registra o melhor rank e pontuação da sala ou modo no perfil ativo."""
        if isinstance(sala_chave, int):
            chave = f"sala_{sala_chave + 1}" if sala_chave >= 0 else "sala_1"
        else:
            chave = str(sala_chave)
        letra = str(rank_letra or "C").upper()[:1]
        if letra not in _ORDEM_RANK:
            letra = "C"
        pts = max(0, int(pontuacao or 0))
        detalhe_atual = self.ranks_detalhes.get(chave, {})
        pts_ant = int(detalhe_atual.get("pontuacao", -1))
        rank_ant = self.ranks.get(chave)
        ord_ant = _ORDEM_RANK.get(rank_ant, 0)
        if _ORDEM_RANK[letra] > ord_ant or (_ORDEM_RANK[letra] == ord_ant and pts >= pts_ant):
            self.ranks[chave] = letra
            self.ranks_detalhes[chave] = {
                "rank": letra,
                "pontuacao": pts,
                "sem_avaria": bool(sem_avaria),
            }
        return self.ranks.get(chave, letra)

    # ---- Sistema de Tentativas (Vidas) ---------------------------------------
    def perder_tentativa(self):
        """Reduz 1 tentativa ao morrer e incrementa o total de tentativas gastas.
        Se as tentativas se esgotarem (0 restantes), indica game over total.
        Retorna (game_over_total, tentativas_restantes).
        """
        self.tentativas_gastas += 1
        self.tentativas = max(0, self.tentativas - 1)
        if self.tentativas <= 0:
            return True, 0
        else:
            self.salvar()
            return False, self.tentativas

    # ---- Sistema de Nível e Bônus --------------------------------------------
    def bonus_hp(self):
        """Bônus de vida máxima por nível (+15 HP por nível acima do 1)."""
        return (self.nivel - 1) * 15

    def bonus_dano(self):
        """Bônus de ataque por nível (+2 dano a cada ataque por nível acima do 1)."""
        return (self.nivel - 1) * 2

    def multiplicador_poder(self):
        """Multiplicador de dano/poder do jogador: aumenta em +5% a cada nível acima do nível 1."""
        return 1.0 + max(0, self.nivel - 1) * 0.05

    def bonus_poder_percentual(self):
        """Porcentagem de bônus de poder do personagem (+5% por nível)."""
        return max(0, self.nivel - 1) * 5

    def bonus_pocoes_cura(self):
        """Bônus de poções de cura ganhas por nível (+1 a cada nível acima do 1)."""
        return max(0, self.nivel - 1)

    def bonus_cristais_eter(self):
        """Bônus de cristais de éter ganhos por nível (+1 a cada nível acima do 1)."""
        return max(0, self.nivel - 1)

    def total_pocoes_cura(self):
        """Quantidade total de poções de cura (+1 a cada nível conquistado + encontradas em baús)."""
        return CONFIG.get("pocoes_cura_inicial", 3) + self.bonus_pocoes_cura() + getattr(self, "pocoes_encontradas", 0)

    def total_cristais_eter(self):
        """Quantidade total de cristais de éter (+1 a cada nível conquistado + encontrados em baús)."""
        return CONFIG.get("cristais_ap_inicial", 2) + self.bonus_cristais_eter() + getattr(self, "cristais_encontrados", 0)

    def adicionar_pocao_cura(self, qtd=1):
        """Adiciona poções coletadas em baús de exploração."""
        self.pocoes_encontradas = getattr(self, "pocoes_encontradas", 0) + qtd
        self.salvar()

    def adicionar_frasco_eter(self, qtd=1):
        """Adiciona frascos de éter coletados em baús de exploração."""
        self.cristais_encontrados = getattr(self, "cristais_encontrados", 0) + qtd
        self.salvar()

    def obter_pocoes_max(self):
        return self.total_pocoes_cura()

    def obter_cristais_max(self):
        return self.total_cristais_eter()

    def fator_escala_inimigos(self):
        """Fator de aumento de HP dos inimigos com base no nível do jogador (+15% HP por nível acima do 1)."""
        return 1.0 + (self.nivel - 1) * 0.15

    def escalar_hp_inimigo(self, hp_base):
        """Calcula a vida do inimigo ou chefe de acordo com o nível atual do jogador."""
        return max(1, int(round(hp_base * self.fator_escala_inimigos())))

    def max_hp_total(self):
        return self.max_hp_base + self.bonus_hp()

    def calcular_xp_proximo(self, nivel):
        return int(80 * (1.35 ** max(0, nivel - 1)))

    def ganhar_xp(self, qtd):
        """Adiciona XP e processa subida de nível. Retorna (subiu_nivel, novo_nivel, niveis_ganhos)."""
        self.xp += max(0, int(qtd))
        subiu = False
        niveis_ganhos = 0
        while self.xp >= self.xp_proximo:
            self.xp -= self.xp_proximo
            self.nivel += 1
            niveis_ganhos += 1
            subiu = True
            self.xp_proximo = self.calcular_xp_proximo(self.nivel)

        if subiu:
            self.max_hp = self.max_hp_total()
            self.salvar()
        return subiu, self.nivel, niveis_ganhos

    # ---- consulta -----------------------------------------------------------
    def hp_da_sala(self, idx):
        """HP com que o personagem entra na sala (cheio se nunca visitou)."""
        hp = self.vida.get(idx)
        max_total = self.max_hp_total()
        return max_total if hp is None else max(1, min(max_total, hp))

    def visitada(self, idx):
        return self.vida.get(idx) is not None

    # ---- atualização --------------------------------------------------------
    def registrar_vida(self, idx, hp):
        max_total = self.max_hp_total()
        self.vida[idx] = int(max(1, min(max_total, hp)))

    def curar_sala(self, idx):
        self.vida[idx] = self.max_hp_total()

    def marcar_chefe(self, idx):
        self.chefes.add(idx)

    # ---- disco & perfis isolados -------------------------------------------
    def _aplicar_dados_perfil(self, dados):
        self.vida = {i: None for i in range(NUM_SALAS)}
        for k, v in dados.get("vida", {}).items():
            idx_s = int(k)
            if idx_s in self.vida and isinstance(v, (int, float)):
                self.vida[idx_s] = int(v)
        self.chefes = {int(i) for i in dados.get("chefes", []) if 0 <= int(i) < NUM_SALAS}
        if "ultima_sala" in dados:
            self.ultima_sala = max(0, min(NUM_SALAS - 1, int(dados.get("ultima_sala", 0))))
        elif "sala_atual" in dados:
            self.ultima_sala = max(0, min(NUM_SALAS - 1, int(dados.get("sala_atual", 1)) - 1))
        else:
            self.ultima_sala = 0

        if "hp_atual" in dados and self.vida.get(self.ultima_sala) is None:
            try:
                self.vida[self.ultima_sala] = max(1, int(dados["hp_atual"]))
            except Exception:
                pass

        self.nivel = max(1, int(dados.get("nivel", 1)))
        self.xp = max(0, int(dados.get("xp", 0)))
        self.xp_proximo = self.calcular_xp_proximo(self.nivel)
        self.max_hp = self.max_hp_total()
        vidas_val = dados.get("tentativas", dados.get("vidas", self.tentativas_max))
        self.tentativas = max(1, min(self.tentativas_max, int(vidas_val)))
        nome_val = dados.get("nome_heroi", dados.get("nome_usuario", "Guerreiro"))
        self.nome_heroi = str(nome_val).strip()[:16] or "Guerreiro"
        tempo_val = dados.get("tempo_acumulado_segundos", dados.get("tempo_decorrido", 0.0))
        self._tempo_acumulado_segundos = max(0.0, float(tempo_val))
        self.tempo_sala_atual = 0.0
        self.tentativas_gastas = max(1, int(dados.get("tentativas_gastas", 1)))
        self.pocoes_encontradas = max(0, int(dados.get("pocoes_encontradas", 0)))
        self.cristais_encontrados = max(0, int(dados.get("cristais_encontrados", 0)))
        ranks_raw = dados.get("ranks", {})
        self.ranks = {str(k): str(v).upper()[:1] for k, v in ranks_raw.items()} if isinstance(ranks_raw, dict) else {}
        det_raw = dados.get("ranks_detalhes", {})
        self.ranks_detalhes = dict(det_raw) if isinstance(det_raw, dict) else {}

    def exportar_dados_perfil(self):
        tempo_total = round(self.tempo_total_exibicao(), 2)
        hp_atual = self.hp_da_sala(self.ultima_sala)
        return {
            "nome_usuario": self.nome_heroi,
            "sala_atual": self.ultima_sala + 1,
            "tempo_acumulado_segundos": tempo_total,
            "vidas": self.tentativas,
            "hp_atual": hp_atual,
            "ranks": dict(self.ranks),
            "ranks_detalhes": dict(self.ranks_detalhes),
            "vida": {str(k): v for k, v in self.vida.items() if v is not None},
            "chefes": sorted(self.chefes),
            "ultima_sala": self.ultima_sala,
            "nivel": self.nivel,
            "xp": self.xp,
            "tentativas": self.tentativas,
            "nome_heroi": self.nome_heroi,
            "tempo_decorrido": round(tempo_total, 1),
            "tentativas_gastas": self.tentativas_gastas,
            "pocoes_encontradas": getattr(self, "pocoes_encontradas", 0),
            "cristais_encontrados": getattr(self, "cristais_encontrados", 0),
        }

    def carregar(self, caminho=None):
        alvo = caminho or ARQUIVO_SAVE
        try:
            if not os.path.exists(alvo):
                log_info("Arquivo de save não encontrado. Iniciando novo progresso padrão.")
                return
            with open(alvo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            self._aplicar_dados_perfil(dados)
            log_info(f"Progresso carregado com sucesso (Herói: {self.nome_heroi}, Sala: {self.ultima_sala}, Nível: {self.nivel}, Vidas: {self.tentativas}, Tempo: {self.tempo_decorrido:.1f}s).")
        except Exception as e:
            log_erro(f"Falha ao carregar save de '{alvo}': {e}", exc_info=e)

    def salvar(self, salvar_global=True):
        dados = self.exportar_dados_perfil()
        caminho_perfil = obter_caminho_perfil(self.nome_heroi)
        try:
            os.makedirs(os.path.dirname(caminho_perfil), exist_ok=True)
            with open(caminho_perfil, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            if salvar_global:
                with open(ARQUIVO_SAVE, "w", encoding="utf-8") as f:
                    json.dump(dados, f, indent=2, ensure_ascii=False)
            log_info(f"Progresso salvo com sucesso (Perfil: {self.nome_heroi}, Sala: {self.ultima_sala}, Nível: {self.nivel}, Vidas: {self.tentativas}, Tempo: {self.tempo_decorrido:.1f}s).")
        except Exception as e:
            log_erro(f"Falha ao salvar progresso em '{ARQUIVO_SAVE}': {e}", exc_info=e)

    def trocar_perfil(self, novo_nome, salvar_anterior=True):
        """
        Alterna o perfil ativo mantendo isolamento total de dados e sem zerar o cronômetro
        ao retornar para um perfil já existente.
        Retorna True se o perfil alternado já existia salvo em disco.
        """
        nome_limpo = str(novo_nome or "").strip()[:16] or "Guerreiro"
        if nome_limpo == self.nome_heroi:
            self.salvar()
            return os.path.exists(obter_caminho_perfil(nome_limpo))

        if salvar_anterior and self.nome_heroi:
            self.salvar(salvar_global=False)

        caminho_destino = obter_caminho_perfil(nome_limpo)
        if os.path.exists(caminho_destino):
            self.carregar(caminho_destino)
            self.salvar(salvar_global=True)
            log_info(f"Perfil '{self.nome_heroi}' carregado com tempo acumulado preservado ({self.tempo_decorrido:.1f}s).")
            return True

        # Novo perfil inédito: cria slot isolado limpo para esse usuário
        self.vida = {i: None for i in range(NUM_SALAS)}
        self.chefes = set()
        self.ultima_sala = 0
        self.nivel = 1
        self.xp = 0
        self.xp_proximo = self.calcular_xp_proximo(1)
        self.max_hp = self.max_hp_total()
        self.tentativas = self.tentativas_max
        self.tentativas_gastas = 1
        self.pocoes_encontradas = 0
        self.cristais_encontrados = 0
        self.ranks = {}
        self.ranks_detalhes = {}
        self.nome_heroi = nome_limpo
        self._tempo_acumulado_segundos = 0.0
        self.tempo_sala_atual = 0.0
        self.salvar(salvar_global=True)
        log_info(f"Novo perfil '{self.nome_heroi}' criado e isolado.")
        return False

    def listar_perfis(self):
        """Retorna os perfis salvos em disco ordenados por nome."""
        perfis = []
        if os.path.isdir(DIR_PERFIS):
            for arq in sorted(os.listdir(DIR_PERFIS)):
                if arq.startswith("perfil_") and arq.endswith(".json"):
                    caminho = os.path.join(DIR_PERFIS, arq)
                    try:
                        with open(caminho, "r", encoding="utf-8") as f:
                            d = json.load(f)
                        perfis.append({
                            "nome_usuario": str(d.get("nome_usuario", d.get("nome_heroi", "Guerreiro"))),
                            "tempo_acumulado_segundos": float(d.get("tempo_acumulado_segundos", d.get("tempo_decorrido", 0.0))),
                            "sala_atual": int(d.get("sala_atual", int(d.get("ultima_sala", 0)) + 1)),
                            "vidas": int(d.get("vidas", d.get("tentativas", self.tentativas_max))),
                            "ranks": dict(d.get("ranks", {})),
                        })
                    except Exception:
                        pass
        return perfis

    def reviver_jogador(self):
        """Restaura o estado do jogador mantendo o tempo decorrido acumulado."""
        self.tentativas = self.tentativas_max
        self.salvar()

    def resetar_tempo(self):
        """Zera explicitamente o cronômetro apenas ao iniciar uma nova jornada explícita."""
        self._tempo_acumulado_segundos = 0.0
        self.tempo_sala_atual = 0.0
        self.tentativas_gastas = 1
        self.tentativas = self.tentativas_max
        self.salvar()

    def apagar(self, manter_nome=True, manter_tempo=True):
        """Reseta todas as salas e o nível mantendo o tempo acumulado salvo quando solicitado."""
        if manter_tempo:
            self.consolidar_tempo_sala()
        else:
            self._tempo_acumulado_segundos = 0.0
            self.tempo_sala_atual = 0.0
            self.tentativas_gastas = 1
        self.vida = {i: None for i in range(NUM_SALAS)}
        self.chefes = set()
        self.ultima_sala = 0
        self.nivel = 1
        self.xp = 0
        self.xp_proximo = self.calcular_xp_proximo(1)
        self.max_hp = self.max_hp_total()
        self.tentativas = self.tentativas_max
        self.pocoes_encontradas = 0
        self.cristais_encontrados = 0
        if not manter_nome:
            self.nome_heroi = "Guerreiro"
        log_info(f"Progresso resetado para nova tentativa (Nível 1, 3 vidas, tempo mantido: {self.tempo_decorrido:.1f}s).")
        self.salvar()
