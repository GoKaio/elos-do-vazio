# -*- coding: utf-8 -*-
"""
ELOS DO VAZIO - Sistema de Ranking e Histórico de Heróis (Fases de Sala).
Gerencia o arquivo elos_do_vazio_ranking.json com persistência de pontuações,
tempo de corrida (speedrun), tentativas gastas e status de vitória/derrota nas fases de sala.
"""
import os
import json
import datetime
from caminhos import obter_dir_dados, log_info, log_aviso, log_erro

ARQUIVO_RANKING = os.path.join(obter_dir_dados(), "elos_do_vazio_ranking.json")
_antigo_ranking = os.path.join(obter_dir_dados(), "endbound_ranking.json")
if not os.path.exists(ARQUIVO_RANKING) and os.path.exists(_antigo_ranking):
    try:
        os.replace(_antigo_ranking, ARQUIVO_RANKING)
    except Exception:
        pass


def formatar_tempo(segundos):
    """Formata tempo em segundos para MM:SS ou HH:MM:SS com décimos."""
    segundos = max(0.0, float(segundos))
    total_seg = int(segundos)
    m = total_seg // 60
    s = total_seg % 60
    h = m // 60
    decimos = int((segundos - total_seg) * 10)
    if h > 0:
        m = m % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}.{decimos}"


def formatar_tempo_curto(segundos):
    """Formata tempo em segundos para MM:SS ou HH:MM:SS sem décimos."""
    segundos = max(0.0, float(segundos))
    total_seg = int(segundos)
    m = total_seg // 60
    s = total_seg % 60
    h = m // 60
    if h > 0:
        m = m % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


LIMIARES_RANK = (("S", 9000), ("A", 7500), ("B", 5500), ("C", 0))


def calcular_rank_por_pontuacao(pontuacao):
    """Converte pontuação numérica em Rank S (>=9000), A (7500-8999), B (5500-7499) ou C (<5500)."""
    pts = int(pontuacao or 0)
    for letra, minimo in LIMIARES_RANK:
        if pts >= minimo:
            return letra
    return "C"


def calcular_rank_desempenho(dano_recebido=0, tempo_segundos=0.0, tempo_meta=60.0, qtes_perfeitos=0, parries_perfeitos=0, venceu=True):
    """
    Calcula pontuação balanceada e grau de Rank (S/A/B/C) com base em:
      - Dano recebido (0 = bônus máximo 'Sem Avaria')
      - Tempo de limpeza vs meta
      - QTEs perfeitos e Parries perfeitos executados
    """
    dano = max(0, int(dano_recebido or 0))
    tempo = max(0.0, float(tempo_segundos or 0.0))
    meta = max(10.0, float(tempo_meta or 60.0))
    qtes = max(0, int(qtes_perfeitos or 0))
    parries = max(0, int(parries_perfeitos or 0))

    sem_avaria = bool(venceu and dano == 0)
    if dano == 0:
        bonus_dano = 2600
    else:
        bonus_dano = max(-2200, 1800 - dano * 28)

    razao_t = tempo / meta
    if razao_t <= 1.0:
        bonus_tempo = int(900 + (1.0 - razao_t) * 500)
    else:
        bonus_tempo = max(-1200, int(900 - (razao_t - 1.0) * 1400))

    bonus_precisao = min(1500, qtes * 220 + parries * 320)
    pontuacao = max(0, int(6000 + bonus_dano + bonus_tempo + bonus_precisao))
    if not venceu:
        pontuacao = min(5400, max(500, pontuacao // 3))

    return {
        "rank": calcular_rank_por_pontuacao(pontuacao),
        "pontuacao": pontuacao,
        "sem_avaria": sem_avaria,
        "dano_recebido": dano,
        "tempo_segundos": round(tempo, 1),
        "qtes_perfeitos": qtes,
        "parries_perfeitos": parries,
        "bonus_dano": bonus_dano,
        "bonus_tempo": bonus_tempo,
        "bonus_precisao": bonus_precisao,
    }


class SistemaRanking:
    def __init__(self):
        self.registros = []
        self.carregar()

    def carregar(self):
        if not os.path.exists(ARQUIVO_RANKING):
            self.registros = self._gerar_padroes()
            self.salvar()
            return
        try:
            with open(ARQUIVO_RANKING, "r", encoding="utf-8") as f:
                dados = json.load(f)
            # Carrega filtrando apenas os modos oficiais suportados (CAMPANHA, BOSS_RUSH e DEMO)
            self.registros = [r for r in dados if self._extrair_modo(r) in ("CAMPANHA", "BOSS_RUSH", "DEMO")]
            if not self.registros:
                self.registros = self._gerar_padroes()
            self.salvar()
            log_info(f"Ranking carregado com {len(self.registros)} registros de '{ARQUIVO_RANKING}'.")
        except Exception as e:
            log_aviso(f"Erro ao carregar ranking de {ARQUIVO_RANKING}: {e}")
            self.registros = self._gerar_padroes()

    def salvar(self):
        try:
            with open(ARQUIVO_RANKING, "w", encoding="utf-8") as f:
                json.dump(self.registros, f, indent=2, ensure_ascii=False)
            log_info(f"Ranking salvo com sucesso ({len(self.registros)} registros).")
        except Exception as e:
            log_erro(f"Erro ao salvar ranking em '{ARQUIVO_RANKING}': {e}")

    def _gerar_padroes(self):
        """Registros lendários iniciais para demonstrar o mural da fama das fases de sala."""
        return [
            {
                "nome": "Sir Alden",
                "tempo": 214.2,
                "tentativas": 1,
                "resultado": "PASSOU",
                "sala": 7,
                "modo": "CAMPANHA",
                "data": "30/10/2026 19:40"
            },
            {
                "nome": "Kaelen da Aurora",
                "tempo": 332.8,
                "tentativas": 2,
                "resultado": "PASSOU",
                "sala": 7,
                "modo": "CAMPANHA",
                "data": "30/10/2026 21:15"
            },
            {
                "nome": "Valéria Sombra",
                "tempo": 445.0,
                "tentativas": 3,
                "resultado": "PASSOU",
                "sala": 7,
                "modo": "CAMPANHA",
                "data": "31/10/2026 14:05"
            },
            {
                "nome": "Thorin de Ferro",
                "tempo": 185.4,
                "tentativas": 3,
                "resultado": "PERDEU",
                "sala": 6,
                "modo": "CAMPANHA",
                "data": "31/10/2026 16:20"
            },
            {
                "nome": "Aldo Visitante",
                "tempo": 68.4,
                "tentativas": 1,
                "resultado": "PASSOU",
                "sala": 3,
                "modo": "DEMO",
                "data": "05/11/2026 15:30"
            },
            {
                "nome": "Lara Speedrun",
                "tempo": 89.1,
                "tentativas": 1,
                "resultado": "PASSOU",
                "sala": 3,
                "modo": "DEMO",
                "data": "05/11/2026 16:10"
            },
            {
                "nome": "Campeão Feira",
                "tempo": 115.5,
                "tentativas": 2,
                "resultado": "PASSOU",
                "sala": 3,
                "modo": "DEMO",
                "data": "06/11/2026 10:15"
            }
        ]

    def reiniciar(self, modo=None):
        """Limpa os registros do ranking das fases de sala. Se modo for especificado, limpa apenas daquele modo."""
        if modo:
            self.registros = [r for r in self.registros if self._extrair_modo(r) != modo]
            log_info(f"Ranking do modo {modo} zerado com sucesso.")
        else:
            self.registros = []
            log_info("Ranking global zerado com sucesso.")
        self.salvar()

    def _extrair_modo(self, r):
        m = r.get("modo")
        if m in ("CAMPANHA", "BOSS_RUSH", "DEMO"):
            return m
        if r.get("nome", "").startswith("[RUSH]"):
            return "BOSS_RUSH"
        if r.get("nome", "").startswith("[DEMO]"):
            return "DEMO"
        return "CAMPANHA"

    def adicionar_registro(
        self, nome, tempo, tentativas, passou=True, sala=7, modo="CAMPANHA",
        rank=None, pontuacao=None, dano_recebido=0, parries_perfeitos=0, qtes_perfeitos=0
    ):
        """Adiciona uma nova entrada de corrida ao ranking calculando grau S/A/B/C e pontuação."""
        nome_limpo = (nome or "").strip() or "Herói Sem Nome"
        if modo in ("CAMPANHA", "BOSS_RUSH", "DEMO"):
            modo_final = modo
        elif "[RUSH]" in nome_limpo:
            modo_final = "BOSS_RUSH"
        elif "[DEMO]" in nome_limpo:
            modo_final = "DEMO"
        else:
            modo_final = "CAMPANHA"

        tempo_f = round(max(0.0, float(tempo)), 1)
        sala_f = max(1, min(7, int(sala)))
        if rank is None or pontuacao is None:
            meta_ref = max(45.0, float(sala_f) * 55.0) if modo_final != "BOSS_RUSH" else 220.0
            res_rank = calcular_rank_desempenho(
                dano_recebido=dano_recebido,
                tempo_segundos=tempo_f,
                tempo_meta=meta_ref,
                qtes_perfeitos=qtes_perfeitos,
                parries_perfeitos=parries_perfeitos,
                venceu=bool(passou),
            )
            rank_final = str(rank or res_rank["rank"]).upper()[:1]
            pts_final = int(pontuacao if pontuacao is not None else res_rank["pontuacao"])
        else:
            rank_final = str(rank).upper()[:1]
            pts_final = max(0, int(pontuacao))

        novo = {
            "nome": nome_limpo[:16],
            "tempo": tempo_f,
            "tentativas": max(1, int(tentativas)),
            "resultado": "PASSOU" if passou else "PERDEU",
            "sala": sala_f,
            "modo": modo_final,
            "rank": rank_final,
            "pontuacao": pts_final,
            "sem_avaria": bool(passou and dano_recebido == 0),
            "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        self.registros.append(novo)
        self.ordenar()
        if len(self.registros) > 100:
            self.registros = self.registros[:100]
        self.salvar()
        return novo

    def ordenar(self):
        """Ordena: Vencedores (PASSOU) por menor tempo e maior pontuação, depois Derrotas por maior sala e tempo."""
        def chave(r):
            passou = (r.get("resultado") == "PASSOU")
            tempo = float(r.get("tempo", 999999.0))
            tentativas = int(r.get("tentativas", 99))
            sala = int(r.get("sala", 1))
            pts = int(r.get("pontuacao", 0))
            if passou:
                return (0, tempo, -pts, tentativas, -sala)
            else:
                return (1, -sala, -pts, tempo, tentativas)

        self.registros.sort(key=chave)

    def obter_top(self, limite=10, modo=None):
        self.ordenar()
        if modo:
            filtrados = [r for r in self.registros if self._extrair_modo(r) == modo]
            return filtrados[:limite]
        return self.registros[:limite]


def obter_rank_registro(registro):
    """Retorna (rank_letra, pontuacao) de um registro garantindo compatibilidade com saves antigos."""
    if not isinstance(registro, dict):
        return "C", 0
    r_salvo = registro.get("rank")
    p_salva = registro.get("pontuacao")
    if r_salvo in ("S", "A", "B", "C") and p_salva is not None:
        return r_salvo, int(p_salva)
    res = calcular_rank_desempenho(
        dano_recebido=max(0, (int(registro.get("tentativas", 1)) - 1) * 35),
        tempo_segundos=float(registro.get("tempo", 240.0)),
        tempo_meta=max(60.0, float(registro.get("sala", 7)) * 55.0),
        qtes_perfeitos=2 if registro.get("resultado") == "PASSOU" else 0,
        parries_perfeitos=1 if int(registro.get("tentativas", 1)) == 1 and registro.get("resultado") == "PASSOU" else 0,
        venceu=(registro.get("resultado") == "PASSOU"),
    )
    return str(r_salvo or res["rank"]).upper()[:1], int(p_salva if p_salva is not None else res["pontuacao"])


# Instância global reutilizável
RANKING_GLOBAL = SistemaRanking()
