# -*- coding: utf-8 -*-
import sys
import os


def resource_path(relative_path):
    """Resolve caminhos de recursos em desenvolvimento ou empacotado via PyInstaller (_MEIPASS)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    candidato = os.path.join(base_path, relative_path)
    if os.path.exists(candidato):
        return candidato
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


import caminhos
caminhos.instalar_tratador_excecoes()
try:
    os.chdir(caminhos.obter_dir_base())
except Exception:
    pass

_dir_script = os.path.dirname(os.path.abspath(__file__))
if _dir_script not in sys.path:
    sys.path.insert(0, _dir_script)
import math
import random
from types import SimpleNamespace
import pygame
from config import CONFIG
import sprites
from sprites import (Animador, criar_animador, NovoCombatente, projetar_ponto_25d,
                     criar_heroi_modular, criar_gargula_pedra, criar_cultista_voraz,
                     criar_espectro_pantano, criar_guardiao_vazio)
from progresso import Progresso
import cenarios
from cenarios import (LARGURA_TELA, ALTURA_TELA, LARGURA_MUNDO, ALTURA_MUNDO, DADOS_MAPAS,
                      ARMADILHAS_SALAS, desenhar_fundo_sala, desenhar_decoracoes, desenhar_terreno,
                      desenhar_estruturas_organicas, desenhar_atmosfera_camada,
                      desenhar_armadilhas, desenhar_saida, Vagalumes,
                      desenhar_portoes, desenhar_alavancas, desenhar_chaves, desenhar_baus,
                      desenhar_prompts_interacao, obter_objetivo_sala, obter_sub_regiao,
                      LIMITE_AEREO, LIMITE_SUBSOLO)
from menu import MenuInicial
from splash_estudio import AnimacaoAberturaEstudio, COR_FUNDO_SPLASH
import ui
import ui_assets
import ui_medieval
import ui_procedural
import ui_configurador
from intro import CutsceneIntroducao
from cutscenes import MiniCutscenePassagemSala, CutsceneFinalJogo
from cutscene import GerenciadorCutscenes
import audio
import ranking
from ranking import RANKING_GLOBAL, formatar_tempo
from bot_autonomo import BOT

pygame.init()
audio.iniciar()
# Suporte a controles USB/Bluetooth (Xbox, PlayStation e genéricos via SDL/Pygame).
CONTROLES = []
try:
    pygame.joystick.init()
    for _i in range(pygame.joystick.get_count()):
        _joy = pygame.joystick.Joystick(_i)
        _joy.init()
        CONTROLES.append(_joy)
except pygame.error:
    CONTROLES = []
CONTROLE_ATIVO = CONTROLES[0] if CONTROLES else None

def obter_controle_ativo():
    global CONTROLE_ATIVO, CONTROLES
    if CONTROLE_ATIVO is not None:
        try:
            if CONTROLE_ATIVO.get_init():
                return CONTROLE_ATIVO
        except Exception:
            pass
    if pygame.joystick.get_init() and pygame.joystick.get_count() > 0:
        try:
            joy = pygame.joystick.Joystick(0)
            if not joy.get_init():
                joy.init()
            CONTROLE_ATIVO = joy
            if joy not in CONTROLES:
                CONTROLES.append(joy)
            ui_medieval.definir_dispositivo_input("CONTROLE")
            return joy
        except Exception:
            pass
    return None

if CONTROLE_ATIVO:
    ui_medieval.definir_dispositivo_input("CONTROLE")

FPS = 60

# Inicialização da janela com pygame.SCALED para resolução virtual interna estável (960x540)
try:
    janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.SCALED)
except Exception as e:
    caminhos.log_aviso(f"Não foi possível inicializar com SCALED: {e}. Usando modo padrão.")
    janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))

pygame.display.set_caption("ELOS DO VAZIO")
for _ico_cand in ("assets/icone_jogo.ico", "icon.ico", "assets/ui/logo_elos_do_vazio.png"):
    _ico_path = resource_path(_ico_cand)
    if os.path.exists(_ico_path):
        try:
            _ico_surf = pygame.image.load(_ico_path)
            pygame.display.set_icon(_ico_surf)
            break
        except Exception:
            pass
relogio = pygame.time.Clock()
tela_virtual = pygame.Surface((LARGURA_TELA, ALTURA_TELA))

tela_cheia = False


def _calcular_rect_apresentacao(larg_win, alt_win):
    if larg_win <= 0 or alt_win <= 0:
        return pygame.Rect(0, 0, LARGURA_TELA, ALTURA_TELA)
    escala = min(larg_win / float(LARGURA_TELA), alt_win / float(ALTURA_TELA))
    nw = max(1, int(round(LARGURA_TELA * escala)))
    nh = max(1, int(round(ALTURA_TELA * escala)))
    return pygame.Rect((larg_win - nw) // 2, (alt_win - nh) // 2, nw, nh)


def _apresentar_tela_virtual():
    try:
        win_w, win_h = janela.get_size()
        if win_w == LARGURA_TELA and win_h == ALTURA_TELA:
            janela.blit(tela_virtual, (0, 0))
        else:
            r_dest = _calcular_rect_apresentacao(win_w, win_h)
            janela.fill((0, 0, 0))
            escalada = pygame.transform.smoothscale(tela_virtual, (r_dest.width, r_dest.height))
            janela.blit(escalada, r_dest.topleft)
        pygame.display.flip()
    except Exception as e_disp:
        caminhos.log_aviso(f"Falha ao apresentar quadro virtual: {e_disp}")


def _ajustar_evento_mouse(ev):
    if ev.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        return ev
    try:
        win_w, win_h = janela.get_size()
        if win_w == LARGURA_TELA and win_h == ALTURA_TELA:
            return ev
        r_dest = _calcular_rect_apresentacao(win_w, win_h)
        mx = int((ev.pos[0] - r_dest.x) * LARGURA_TELA / float(max(1, r_dest.width)))
        my = int((ev.pos[1] - r_dest.y) * ALTURA_TELA / float(max(1, r_dest.height)))
        mx = max(0, min(LARGURA_TELA - 1, mx))
        my = max(0, min(ALTURA_TELA - 1, my))
        dados = ev.dict.copy()
        dados["pos"] = (mx, my)
        return pygame.event.Event(ev.type, dados)
    except Exception:
        return ev


def alternar_tela_cheia():
    global janela, tela_cheia
    try:
        if hasattr(pygame.display, "toggle_fullscreen"):
            sucesso = pygame.display.toggle_fullscreen()
            if sucesso:
                tela_cheia = not tela_cheia
                caminhos.log_info(f"Modo Tela Cheia alterado via toggle_fullscreen: {tela_cheia}")
                return
    except Exception as e:
        caminhos.log_aviso(f"toggle_fullscreen falhou: {e}")

    try:
        tela_cheia = not tela_cheia
        if tela_cheia:
            try:
                janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.FULLSCREEN | pygame.SCALED)
            except Exception:
                janela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            try:
                janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.SCALED)
            except Exception:
                janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), 0)
        caminhos.log_info(f"Modo Tela Cheia alterado via set_mode: {tela_cheia} ({janela.get_size()}).")
    except Exception as e_crit:
        caminhos.log_aviso(f"Erro ao alternar tela cheia: {e_crit}. Recuperando janela padrão 960x540.")
        tela_cheia = False
        try:
            janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        except Exception:
            pass

caminhos.log_info(f"Janela inicializada ({LARGURA_TELA}x{ALTURA_TELA} @ {FPS} FPS). Controles conectados: {len(CONTROLES)}.")

# Texturas do pacote Final (fundos, chão, plataformas, decoração) - precisa da janela criada.
cenarios.iniciar()
ui_assets.iniciar()

# Fontes medievais (Cinzel, Cardo, IM Fell, EB Garamond)
def _fonte_med(nomes, tamanho, bold=False):
    for n in nomes:
        try:
            if pygame.font.match_font(n):
                return pygame.font.SysFont(n, tamanho, bold=bold)
        except Exception:
            pass
    try:
        return pygame.font.SysFont("serif", tamanho, bold=bold)
    except Exception:
        return pygame.font.Font(None, tamanho)

fonte_pequena = _fonte_med(["Cardo", "EB Garamond", "Cormorant Garamond", "DejaVu Serif"], 15, True)
fonte = _fonte_med(["Cardo", "EB Garamond", "Cormorant Garamond", "DejaVu Serif"], 18, True)
fonte_menu = _fonte_med(["Cinzel", "Cormorant SC", "Alegreya SC", "DejaVu Serif"], 20, True)
fonte_grande = _fonte_med(["Cinzel", "Cinzel Decorative", "Alfa Slab One", "DejaVu Serif"], 30, True)
fonte_titulo = _fonte_med(["Cinzel Decorative", "Cinzel", "IM FELL English SC", "Alfa Slab One"], 42, True)

# Paleta medieval
COR_PERGAMINHO = (212, 190, 150)
COR_PERGAMINHO_ESC = (168, 140, 100)
COR_MADEIRA = (62, 38, 22)
COR_MADEIRA_CLARA = (98, 62, 36)
COR_OURO = (212, 175, 55)
COR_OURO_ESCURO = (150, 115, 30)
COR_FERRO = (55, 50, 48)
COR_FERRO_CLARO = (95, 88, 82)
COR_SANGUE = (140, 28, 28)
COR_SANGUE_CLARO = (180, 50, 45)
COR_MUSGO = (55, 95, 50)
COR_TEXTO = (35, 25, 15)
COR_TEXTO_CLARO = (235, 220, 185)
COR_TEXTO_OURO = (240, 210, 120)

def desenhar_painel_medieval(surface, rect, preenchimento=None, borda=None, espessura=3, variante="pedra", ativo=False, borda_ouro=False, alpha=245):
    """Renderiza moldura gótica padronizada via ui_procedural."""
    is_ouro = borda_ouro or (borda == COR_OURO) or ativo
    ui_procedural.desenhar_moldura_gotica(surface, rect, chanfro=7, destacado=bool(ativo or is_ouro), alpha=alpha, borda_ouro=is_ouro, cantoneiras=True, variante=variante)

def desenhar_barra_medieval(surface, rect, valor, maximo=1.0, cor_cheia=None, cor_fundo=None, tipo="hp"):
    """Barra de status medieval com moldura forjada, líquido pixelado e divisórias via ui_medieval."""
    if isinstance(maximo, (tuple, list)):  # Suporta assinatura legada: (surface, rect, ratio, cor_cheia)
        ui_medieval.desenhar_barra_medieval(surface, rect, valor, 1.0, tipo=tipo)
    else:
        ui_medieval.desenhar_barra_medieval(surface, rect, valor, maximo, tipo=tipo)


def _retrato_sprite(frame, tamanho):
    """Recorta o personagem e amplia bem para o retrato (sprites 100x100 tem personagem pequeno)."""
    try:
        rect = frame.get_bounding_rect(min_alpha=5)
        if rect.width < 4 or rect.height < 4:
            return pygame.transform.scale(frame, (tamanho, tamanho))
        # margem generosa ao redor do personagem
        pad = max(6, max(rect.width, rect.height) // 3)
        x = max(0, rect.x - pad)
        y = max(0, rect.y - pad)
        w = min(frame.get_width() - x, rect.width + pad * 2)
        h = min(frame.get_height() - y, rect.height + pad * 2)
        cortado = frame.subsurface(pygame.Rect(x, y, w, h)).copy()
        # cobre o quadro inteiro (cover)
        escala = max(tamanho / max(1, cortado.get_width()), tamanho / max(1, cortado.get_height()))
        nw = max(1, int(cortado.get_width() * escala))
        nh = max(1, int(cortado.get_height() * escala))
        scaled = pygame.transform.scale(cortado, (nw, nh))
        out = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        out.blit(scaled, ((tamanho - nw) // 2, (tamanho - nh) // 2))
        return out
    except Exception:
        return pygame.transform.scale(frame, (tamanho, tamanho))



class TelaDeMorte:
    """Tela de morte estilo Dark Souls / Hollow Knight com controle de 3 tentativas e Game Over total."""

    def __init__(self):
        self.tempo = 0.0
        self.opcao_selecionada = 0  # 0: Tentar Novamente / Recomeçar, 1: Voltar ao Menu
        self.bg_morte = None
        self.progresso = None
        self.game_over_total = False
        self.tentativas = 3
        self.modo_boss_rush = False
        self.boss_rush_idx = 0
        self.rects_botoes = []
        caminho_bg = caminhos.obter_caminho_recurso("assets/ui/death_bg.jpg")
        if os.path.exists(caminho_bg):
            try:
                carregada = pygame.image.load(caminho_bg).convert()
                self.bg_morte = pygame.transform.smoothscale(carregada, (LARGURA_TELA, ALTURA_TELA))
            except Exception as e:
                caminhos.log_aviso(f"Erro ao carregar death_bg: {e}")
                self.bg_morte = None

        # Partículas de cinzas vermelhas e névoa ascendente
        self.cinzas = []
        for _ in range(45):
            self.cinzas.append({
                "x": random.uniform(20, LARGURA_TELA - 20),
                "y": random.uniform(ALTURA_TELA * 0.4, ALTURA_TELA + 20),
                "vx": random.uniform(-18, 18),
                "vy": random.uniform(-40, -12),
                "raio": random.uniform(1.5, 3.5),
                "cor": random.choice([(255, 60, 50), (220, 30, 30), (255, 130, 60), (140, 20, 20)]),
                "fase": random.uniform(0, math.tau)
            })

    def resetar(self):
        self.tempo = 0.0
        self.opcao_selecionada = 0

    def configurar(self, progresso, game_over_total=False, tentativas=3, modo_boss_rush=False, boss_rush_idx=0):
        self.progresso = progresso
        self.game_over_total = game_over_total
        self.tentativas = tentativas
        self.modo_boss_rush = modo_boss_rush
        self.boss_rush_idx = boss_rush_idx
        self.tempo = 0.0
        self.opcao_selecionada = 0

    def update(self, dt):
        self.tempo += dt
        for c in self.cinzas:
            c["x"] += c["vx"] * dt
            c["y"] += c["vy"] * dt
            if c["y"] < 60 or c["x"] < 0 or c["x"] > LARGURA_TELA:
                c["y"] = ALTURA_TELA + random.uniform(5, 25)
                c["x"] = random.uniform(20, LARGURA_TELA - 20)

    def draw(self, surface, mapa_idx, progresso=None):
        cx, cy = LARGURA_TELA // 2, ALTURA_TELA // 2
        if progresso is not None:
            self.progresso = progresso
            self.tentativas = getattr(progresso, "tentativas", self.tentativas)

        # 1. Background com zoom dramático
        if self.bg_morte is not None:
            zoom_fator = 1.0 + 0.025 * min(1.0, self.tempo / 4.0)
            bw = int(LARGURA_TELA * zoom_fator)
            bh = int(ALTURA_TELA * zoom_fator)
            surf_z = pygame.transform.smoothscale(self.bg_morte, (bw, bh))
            off_x = (bw - LARGURA_TELA) // 2
            off_y = (bh - ALTURA_TELA) // 2
            surface.blit(surf_z, (-off_x, -off_y))
        else:
            surface.fill((12, 6, 8))

        # 2. Vinheta atmosférica
        s_vinheta = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        for vy in range(120):
            a_sup = int(180 * (1.0 - vy / 120.0))
            a_inf = int(220 * (vy / 120.0))
            pygame.draw.line(s_vinheta, (0, 0, 0, a_sup), (0, vy), (LARGURA_TELA, vy))
            pygame.draw.line(s_vinheta, (12, 4, 6, a_inf), (0, ALTURA_TELA - 120 + vy), (LARGURA_TELA, ALTURA_TELA - 120 + vy))
        pygame.draw.rect(s_vinheta, (0, 0, 0, 85), (0, 0, LARGURA_TELA, ALTURA_TELA))
        surface.blit(s_vinheta, (0, 0))

        # 3. Cinzas ardentes
        for c in self.cinzas:
            brilho = 0.65 + 0.35 * math.sin(self.tempo * 3.5 + c["fase"])
            cor = tuple(min(255, int(v * brilho)) for v in c["cor"])
            pygame.draw.circle(surface, cor, (int(c["x"]), int(c["y"])), int(c["raio"]))

        # 4. Título Principal ("GAME OVER" em 5 mortes, "VOCÊ CAIU" caso contrário)
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 2.4)
        if self.game_over_total:
            texto_titulo = "GAME OVER"
            cor_titulo = (255, int(40 + 25 * pulso), int(40 + 20 * pulso))
            sub_texto = "Você morreu 3 vezes! O ciclo quebrou e todo o progresso ruiu..."
            cor_sub = (255, 120, 130)
        else:
            texto_titulo = "VOCÊ CAIU"
            cor_titulo = (255, int(60 + 35 * pulso), int(60 + 30 * pulso))
            sub_texto = "As sombras consumiram seu fôlego vital..."
            cor_sub = COR_PERGAMINHO

        # Glow atrás do título
        glow_t = pygame.Surface((560, 80), pygame.SRCALPHA)
        for gx in range(560):
            alfa_g = int((45 + 30 * pulso) * (1.0 - abs(gx - 280) / 280.0))
            pygame.draw.line(glow_t, (220, 25, 25, alfa_g), (gx, 0), (gx, 80))
        surface.blit(glow_t, (cx - 280, 48))

        # Linhas ornamentais
        pygame.draw.line(surface, COR_OURO_ESCURO, (cx - 250, 45), (cx + 250, 45), 1)
        pygame.draw.line(surface, COR_OURO_ESCURO, (cx - 250, 115), (cx + 250, 115), 1)
        for sep_x in (cx - 250, cx, cx + 250):
            pts_los = [(sep_x, 45 - 4), (sep_x + 4, 45), (sep_x, 45 + 4), (sep_x - 4, 45)]
            pygame.draw.polygon(surface, COR_OURO, pts_los)
            pts_los2 = [(sep_x, 115 - 4), (sep_x + 4, 115), (sep_x, 115 + 4), (sep_x - 4, 115)]
            pygame.draw.polygon(surface, COR_OURO, pts_los2)

        sombra_t = fonte_titulo.render(texto_titulo, True, (10, 0, 0))
        rend_t = fonte_titulo.render(texto_titulo, True, cor_titulo)
        surface.blit(sombra_t, (cx - rend_t.get_width() // 2 + 3, 56 + 3))
        surface.blit(rend_t, (cx - rend_t.get_width() // 2, 56))

        sub = fonte_menu.render(sub_texto, True, cor_sub)
        surface.blit(sub, (cx - sub.get_width() // 2, 126))

        # 5. Painel Central Gótico Mestre (#0F0F1A, cantoneiras L e crânios marfim)
        painel_w, painel_h = 620, 246
        px, py = ui_configurador.obter_posicao("morte_painel")
        painel_rect = pygame.Rect(px, py, painel_w, painel_h)
        ui_procedural.desenhar_moldura_gotica(
            surface, painel_rect, chanfro=8, destacado=True, alpha=246,
            cranios=True, cantoneiras=True,
            variante="carmesim" if self.game_over_total else "padrao"
        )

        f_cab = ui_procedural.obter_fonte_serif(17, bold=True)
        f_met = ui_procedural.obter_fonte_serif(13, bold=False)
        f_btn = ui_procedural.obter_fonte_serif(14, bold=True)
        f_rod = ui_procedural.obter_fonte_serif(11, bold=False)

        sala_nome = DADOS_MAPAS.get(mapa_idx, {}).get("nome", "Reino Desconhecido")
        if self.modo_boss_rush:
            boss_atual_nome = DADOS_MAPAS.get(self.boss_rush_idx, {}).get("boss", {}).get("nome", "Chefe")
            boss_limpo = boss_atual_nome.replace("BOSS: ", "").replace("CHEFE: ", "").replace("CHEFE FINAL: ", "")
            lbl_txt = f"BOSS RUSH FALHOU — {boss_limpo}" if self.game_over_total else f"BOSS RUSH ({self.boss_rush_idx + 1}/7) — {boss_limpo}"
            cor_cab = (255, 110, 110) if self.game_over_total else ui_procedural.COR_OURO_VIVO
        elif self.game_over_total:
            lbl_txt = "DERROTA DEFINITIVA — 3 MORTES ATINGIDAS"
            cor_cab = (255, 110, 110)
        else:
            lbl_txt = f"Local da Queda: Sala {mapa_idx + 1} — {sala_nome}"
            cor_cab = ui_procedural.COR_OURO_VIVO

        lbl_sala = f_cab.render(lbl_txt, True, cor_cab)
        surface.blit(lbl_sala, (cx - lbl_sala.get_width() // 2, py + 12))

        # Indicadores de Tentativas / Gemas de Éter (losango ciano ativo vs crânio)
        for ki in range(3):
            kx = cx - 44 + ki * 44
            ky = py + 47
            if not self.game_over_total and ki < self.tentativas:
                ui_procedural.desenhar_cristal_eter(surface, kx, ky, tamanho=7, ativo=True)
            else:
                ui_procedural.desenhar_cranio_gotico(surface, kx, ky, tamanho=13, apagado=not self.game_over_total)

        tempo_atual = getattr(self.progresso, "tempo_decorrido", 0.0) if self.progresso else 0.0
        str_tempo = formatar_tempo(tempo_atual)
        if self.game_over_total:
            msg_str = f"Salas reiniciadas para novo ciclo  |  Tempo Contínuo: {str_tempo}"
            cor_msg = (255, 190, 180)
        else:
            msg_str = f"Tentativas restantes: {self.tentativas} de 3  |  Tempo Contínuo: {str_tempo}"
            cor_msg = ui_procedural.COR_BRANCO_PEROLA
        msg_tent = f_met.render(msg_str, True, cor_msg)
        surface.blit(msg_tent, (cx - msg_tent.get_width() // 2, py + 66))

        div_y = py + 90
        ui_procedural.desenhar_divisor_dourado(surface, px + 36, div_y, painel_w - 72)

        # 6. Botões Metálicos Chanfrados em Grade Horizontal
        c = ui_medieval.usar_controle()
        sub_nova = "(A) ou (X)" if c else "[R] ou [ENTER]"
        sub_tentar = "(A) ou (X)" if c else "[R] ou [ENTER]"
        sub_menu = "(B) ou (START)" if c else "[ESC] ou [M]"
        if self.game_over_total:
            opcoes = [
                {"label": "NOVA JORNADA", "sub": sub_nova, "icone": "espada"},
                {"label": "VOLTAR AO MENU", "sub": sub_menu, "icone": "grade"},
            ]
        else:
            opcoes = [
                {"label": "TENTAR NOVAMENTE", "sub": sub_tentar, "icone": "espada"},
                {"label": "VOLTAR AO MENU", "sub": sub_menu, "icone": "grade"},
            ]

        btn_w = 264
        btn_h = 56
        btn_y = py + 104
        self.rects_botoes = []

        for i, op in enumerate(opcoes):
            bx = cx - 278 + i * 292
            sel = (i == self.opcao_selecionada)
            b_rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self.rects_botoes.append(b_rect)
            ui_procedural.desenhar_botao_gotico(
                surface, b_rect, op["label"], f_btn,
                selecionado=sel, icone=op["icone"], subtexto=op["sub"]
            )

        ui_procedural.desenhar_rodape_comandos(
            surface, py + painel_h - 24,
            ["[A / D] Selecionar", "[ENTER] Confirmar", "[ESC] Voltar"],
            f_rod, largura=LARGURA_TELA
        )


class TelaFimExposicao:
    """
    Tela temática de Fim da Demonstração / Kiosk Showcase Mode para feiras e eventos indie.
    Exibe mensagem temática em destaque, estatísticas detalhadas da sessão, tempo decorrido
    e salas superadas, com reinício instantâneo para o próximo jogador (A / ESPAÇO / ENTER)
    e auto-reset por inatividade (60s) para estandes desacompanhados.
    """
    def __init__(self):
        self.tempo = 0.0
        self.timer_inatividade = 0.0
        self.motivo = "TEMPO_ESGOTADO"  # "TEMPO_ESGOTADO" ou "META_ATINGIDA"
        self.progresso = None
        self.mapa_idx = 0
        self.inimigos_derrotados = 0
        self.tempo_decorrido = 0.0
        self.resumo_rank = None
        self.opcao_selecionada = 0  # 0: Reiniciar Demo, 1: Voltar ao Menu
        self.rects_botoes = []
        self.bg_morte = None
        caminho_bg = caminhos.obter_caminho_recurso("assets/ui/death_bg.jpg")
        if os.path.exists(caminho_bg):
            try:
                carregada = pygame.image.load(caminho_bg).convert()
                self.bg_morte = pygame.transform.smoothscale(carregada, (LARGURA_TELA, ALTURA_TELA))
            except Exception:
                self.bg_morte = None

        self.particulas = []
        for _ in range(45):
            self.particulas.append({
                "x": random.uniform(20, LARGURA_TELA - 20),
                "y": random.uniform(20, ALTURA_TELA - 20),
                "vx": random.uniform(-14, 14),
                "vy": random.uniform(-30, -10),
                "cor": random.choice([(255, 220, 110), (240, 180, 70), (140, 215, 255), (200, 150, 255)]),
                "raio": random.uniform(1.5, 3.2),
            })

    def configurar(self, motivo, progresso, mapa_idx, inimigos_derrotados=0, resumo_rank=None):
        self.motivo = motivo
        self.progresso = progresso
        self.mapa_idx = mapa_idx
        self.inimigos_derrotados = inimigos_derrotados
        self.tempo_decorrido = getattr(progresso, "tempo_decorrido", 0.0) if progresso else 0.0
        if resumo_rank is not None:
            self.resumo_rank = resumo_rank
        else:
            self.resumo_rank = ranking.calcular_rank_desempenho(
                dano_recebido=0 if motivo == "META_ATINGIDA" else 65,
                tempo_segundos=self.tempo_decorrido,
                tempo_meta=max(60.0, float(CONFIG.get("exposicao_tempo_limite_segundos", 300)) * 0.75),
                qtes_perfeitos=inimigos_derrotados,
                parries_perfeitos=0,
                venceu=(motivo == "META_ATINGIDA"),
            )
        self.tempo = 0.0
        self.timer_inatividade = 0.0
        self.opcao_selecionada = 0
        if motivo == "META_ATINGIDA":
            audio.tocar_sfx("level_up", 1.0)
            audio.tocar_musica("title_theme.ogg")
        else:
            audio.tocar_sfx("death_player", 0.9)
            audio.tocar_musica("title_theme.ogg")

    def update(self, dt):
        self.tempo += dt
        self.timer_inatividade += dt
        for p in self.particulas:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] < 20 or p["x"] < 0 or p["x"] > LARGURA_TELA:
                p["y"] = ALTURA_TELA + random.uniform(5, 20)
                p["x"] = random.uniform(20, LARGURA_TELA - 20)

        # Se ficar inativo por 60 segundos em estande de evento, reseta para o menu inicial
        if self.timer_inatividade >= 60.0:
            return "RESET_MENU"
        return None

    def draw(self, surface):
        cx, cy = LARGURA_TELA // 2, ALTURA_TELA // 2

        # 1. Fundo atmosférico com vinheta escura
        if self.bg_morte is not None:
            surface.blit(self.bg_morte, (0, 0))
            overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            overlay.fill((10, 8, 16, 210))
            surface.blit(overlay, (0, 0))
        else:
            surface.fill((12, 10, 18))

        # Partículas místicas ascendentes
        for p in self.particulas:
            pygame.draw.circle(surface, p["cor"], (int(p["x"]), int(p["y"])), int(p["raio"]))

        # 2. Painel Central Nobre
        painel_w = 660
        painel_h = 420
        px = cx - painel_w // 2
        py = cy - painel_h // 2
        r_painel = pygame.Rect(px, py, painel_w, painel_h)

        meta_atingida = (self.motivo == "META_ATINGIDA")
        variante_p = "padrao" if meta_atingida else "carmesim"
        ui_procedural.desenhar_moldura_gotica(surface, r_painel, chanfro=8, destacado=True, alpha=246, cranios=True, cantoneiras=True, variante=variante_p)

        # 3. Cabeçalho / Título Temático
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 3.5)
        ico_topo = "coroa" if meta_atingida else "relogio"
        ui_procedural.desenhar_icone_tematico(surface, ico_topo, cx, py + 28, tamanho=26, aceso=True)

        if meta_atingida:
            t_titulo = "DEMONSTRAÇÃO CONCLUÍDA!"
            t_sub = "Você superou todos os desafios de ELOS DO VAZIO!"
            cor_tit = ui_procedural.COR_OURO_VIVO
            cor_sub = ui_procedural.COR_ESMERALDA_VIDA
        else:
            t_titulo = "TEMPO ESGOTADO!"
            t_sub = "O tempo limite de demonstração chegou ao fim."
            cor_tit = (255, int(90 + 90 * pulso), int(90 + 50 * pulso))
            cor_sub = (240, 200, 190)

        surf_tit = fonte_titulo.render(t_titulo, True, cor_tit)
        surf_tit_sombra = fonte_titulo.render(t_titulo, True, (15, 6, 8))
        surface.blit(surf_tit_sombra, (cx - surf_tit.get_width() // 2 + 2, py + 54))
        surface.blit(surf_tit, (cx - surf_tit.get_width() // 2, py + 52))

        surf_sub = fonte_pequena.render(t_sub, True, cor_sub)
        surface.blit(surf_sub, (cx - surf_sub.get_width() // 2, py + 92))

        div_y = py + 116
        ui_procedural.desenhar_divisor_dourado(surface, px + 36, div_y, painel_w - 72)

        # 4. Cartão de Rank à esquerda + Estatísticas da Partida à direita (sem sobreposição)
        rank_x = px + 24
        rank_w = 164
        stat_w = painel_w - 220
        stat_h = 160
        stat_x = px + 196
        stat_y = py + 128

        r_rank_box = pygame.Rect(rank_x, stat_y, rank_w, stat_h)
        ui_procedural.desenhar_moldura_gotica(surface, r_rank_box, chanfro=6, destacado=True, alpha=240, cantoneiras=False)
        res_demo = self.resumo_rank or {"rank": "C", "pontuacao": 0, "sem_avaria": False}
        ui_procedural.desenhar_brasao_rank(
            surface,
            r_rank_box.centerx,
            r_rank_box.top + 58,
            res_demo.get("rank", "C"),
            pontuacao=res_demo.get("pontuacao", 0),
            tamanho=62,
            sem_avaria=res_demo.get("sem_avaria", False),
            titulo="RANK DEMO",
            anim_t=self.tempo,
        )

        r_stat = pygame.Rect(stat_x, stat_y, stat_w, stat_h)
        ui_procedural.desenhar_moldura_gotica(surface, r_stat, chanfro=6, destacado=False, alpha=240, cantoneiras=False)

        nome_h = getattr(self.progresso, "nome_heroi", "Guerreiro") if self.progresso else "Guerreiro"
        nv_h = getattr(self.progresso, "nivel", 1) if self.progresso else 1
        hp_h = getattr(self.progresso, "hp_da_sala", lambda x: 120)(self.mapa_idx) if self.progresso else 120
        max_hp_h = self.progresso.max_hp_total() if self.progresso else 120

        limite_salas = int(CONFIG.get("exposicao_sala_limite", 3))
        tempo_limite = float(CONFIG.get("exposicao_tempo_limite_segundos", 300))

        m_dec, s_dec = int(self.tempo_decorrido // 60), int(self.tempo_decorrido % 60)
        m_lim, s_lim = int(tempo_limite // 60), int(tempo_limite % 60)

        linhas_stats = [
            ("escudo", f"Herói: {nome_h}", f"Nv {nv_h} · HP {hp_h}/{max_hp_h}", ui_procedural.COR_OURO_VIVO),
            ("grade", f"Fase: Sala {self.mapa_idx + 1}", f"Meta: Sala {limite_salas}" if not meta_atingida else "META CONCLUÍDA!", ui_procedural.COR_ESMERALDA_VIDA if meta_atingida else ui_procedural.COR_BRANCO_PEROLA),
            ("espada", "Combates Vencidos:", f"{self.inimigos_derrotados} abatidos", ui_procedural.COR_OURO_VIVO),
            ("relogio", f"Tempo: {m_dec:02d}:{s_dec:02d}", f"Limite: {m_lim:02d}:{s_lim:02d}", ui_procedural.COR_VERMELHO_DANO if not meta_atingida else ui_procedural.COR_AZUL_ETER),
        ]

        for idx_st, (ico_st, txt_esq, txt_dir, cor_destaque) in enumerate(linhas_stats):
            sy = stat_y + 12 + idx_st * 36
            ui_procedural.desenhar_icone_tematico(surface, ico_st, stat_x + 22, sy + 9, tamanho=16, aceso=True)
            surf_e = fonte_pequena.render(txt_esq, True, ui_procedural.COR_BRANCO_PEROLA)
            surf_d = fonte_pequena.render(txt_dir, True, cor_destaque)
            surface.blit(surf_e, (stat_x + 42, sy + 1))
            surface.blit(surf_d, (stat_x + stat_w - surf_d.get_width() - 16, sy + 1))
            if idx_st < 3:
                ui_procedural.desenhar_divisor_dourado(surface, stat_x + 16, sy + 30, stat_w - 32)

        # 5. Botões de Ação para o Próximo Jogador
        c = ui_medieval.usar_controle()
        sub_jogar = "(A)" if c else "[ENTER / ESPAÇO]"
        sub_menu = "(B)" if c else "[ESC]"

        btn_y = py + 302
        btn_w = 276
        btn_h = 54
        self.rects_botoes = []

        opcoes = [
            {"label": "REINICIAR DEMO", "sub": sub_jogar, "icone": "espada"},
            {"label": "VOLTAR AO MENU", "sub": sub_menu, "icone": "grade"},
        ]

        for i, op in enumerate(opcoes):
            bx = cx - 288 + i * 300
            sel = (i == self.opcao_selecionada)
            b_rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self.rects_botoes.append(b_rect)
            ui_procedural.desenhar_botao_gotico(
                surface, b_rect, op["label"], fonte_pequena,
                selecionado=sel, icone=op["icone"], subtexto=op["sub"]
            )

        # 6. Rodapé minimalista
        pos_rank_demo = "-"
        top_demo = RANKING_GLOBAL.obter_top(20, modo="DEMO")
        for idx_r, reg in enumerate(top_demo):
            if reg.get("nome") == nome_h and abs(float(reg.get("tempo", 0.0)) - self.tempo_decorrido) < 1.0:
                pos_rank_demo = f"★ {idx_r + 1}º Lugar no Ranque Demo"
                break

        segundos_restantes_idle = max(0, int(60.0 - self.timer_inatividade))
        if pos_rank_demo != "-":
            itens_kiosk = [pos_rank_demo, ("RANQUE", "Mural Demo"), ("CONFIRMAR", "Reiniciar"), f"Auto-reset {segundos_restantes_idle}s"]
        else:
            itens_kiosk = [("RANQUE", "Mural Demo"), ("CONFIRMAR", "Reiniciar"), f"Auto-reset {segundos_restantes_idle}s"]
        ui_procedural.desenhar_rodape_comandos(
            surface, py + painel_h - 24, itens_kiosk, ui_procedural.obter_fonte_serif(11, bold=False),
            cor=ui_procedural.COR_OURO_VIVO if pos_rank_demo != "-" else ui_procedural.COR_CINZA_TEXTO
        )






class TransicaoMedieval:
    """Animações de transição no estilo medieval entre telas do jogo.

    Estilos:
      - "pergaminho": cortina horizontal de pergaminho que se fecha e abre
      - "fade": fade para preto/sepia e volta
      - "portao": portões de ferro que se fecham ao centro e abrem
      - "selo": círculo dourado se fecha (íris) e reabre
    """

    ESTILOS = ("pergaminho", "fade", "portao", "selo")

    def __init__(self):
        self.ativa = False
        self.fase = "idle"          # idle | fechando | meio | abrindo
        self.progresso = 0.0        # 0 → 1 na fase atual
        self.estilo = "pergaminho"
        self.duracao_fecha = 0.38
        self.duracao_abre = 0.42
        self.modo_destino = None
        self.callback = None
        self.texto = ""
        self._callback_feito = False

    @property
    def bloqueando(self):
        """True enquanto a transição impede input / troca de modo direta."""
        return self.ativa and self.fase in ("fechando", "meio", "abrindo")

    def iniciar(self, modo_destino, estilo=None, texto="", callback=None, duracao=None):
        if self.ativa:
            # Já em transição: aplica destino imediatamente no fim
            self.modo_destino = modo_destino
            self.callback = callback
            return
        self.ativa = True
        self.fase = "fechando"
        self.progresso = 0.0
        self.estilo = estilo if estilo in self.ESTILOS else self._estilo_para(modo_destino)
        self.modo_destino = modo_destino
        self.callback = callback
        self.texto = texto or self._texto_para(modo_destino)
        self._callback_feito = False
        if duracao:
            self.duracao_fecha = duracao * 0.45
            self.duracao_abre = duracao * 0.55

    def _estilo_para(self, modo):
        return {
            "COMBATE": "portao",
            "MAPA": "pergaminho",
            "MENU": "fade",
            "MORTE": "selo",
            "VITORIA": "selo",
        }.get(modo, "pergaminho")

    def _texto_para(self, modo):
        return {
            "COMBATE": "O COMBATE COMEÇA",
            "MAPA": "A JORNADA CONTINUA",
            "MENU": "RETORNO AO REINO",
            "MORTE": "A SOMBRA VENCEU",
            "VITORIA": "GLÓRIA ETERNA",
        }.get(modo, "")

    def update(self, dt):
        if not self.ativa:
            return None
        if self.fase == "fechando":
            self.progresso += dt / max(0.05, self.duracao_fecha)
            if self.progresso >= 1.0:
                self.progresso = 1.0
                self.fase = "meio"
        elif self.fase == "meio":
            # Aplica a troca de modo uma única vez
            destino = self.modo_destino
            if not self._callback_feito:
                self._callback_feito = True
                if self.callback:
                    self.callback()
            self.fase = "abrindo"
            self.progresso = 0.0
            return destino
        elif self.fase == "abrindo":
            self.progresso += dt / max(0.05, self.duracao_abre)
            if self.progresso >= 1.0:
                self.progresso = 1.0
                self.ativa = False
                self.fase = "idle"
                self.modo_destino = None
                self.callback = None
                self.texto = ""
        return None

    def draw(self, surface):
        if not self.ativa:
            return
        if self.fase == "fechando":
            t = self._ease_in(self.progresso)
            self._desenhar(surface, t)
        elif self.fase == "meio":
            self._desenhar(surface, 1.0)
        elif self.fase == "abrindo":
            t = 1.0 - self._ease_out(self.progresso)
            self._desenhar(surface, t)

    @staticmethod
    def _ease_in(t):
        return t * t

    @staticmethod
    def _ease_out(t):
        return 1.0 - (1.0 - t) * (1.0 - t)

    def _desenhar(self, surface, t):
        """t=0 transparente, t=1 totalmente coberto."""
        if t <= 0.001:
            return
        estilo = self.estilo
        if estilo == "fade":
            self._draw_fade(surface, t)
        elif estilo == "portao":
            self._draw_portao(surface, t)
        elif estilo == "selo":
            self._draw_selo(surface, t)
        else:
            self._draw_pergaminho(surface, t)
        if t > 0.35 and self.texto:
            self._draw_texto(surface, t)

    def _draw_fade(self, surface, t):
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        # Sepia escuro
        overlay.fill((18, 12, 8))
        overlay.set_alpha(int(255 * min(1.0, t)))
        surface.blit(overlay, (0, 0))

    def _draw_pergaminho(self, surface, t):
        # Cortinas de pergaminho descendo de cima e subindo de baixo
        h = int(ALTURA_TELA * 0.5 * t) + 4
        # Topo
        topo = pygame.Surface((LARGURA_TELA, h))
        for y in range(h):
            shade = int(180 - 40 * (y / max(1, h)))
            pygame.draw.line(topo, (shade, shade - 25, shade - 55), (0, y), (LARGURA_TELA, y))
        surface.blit(topo, (0, 0))
        # Borda dourada inferior do topo
        pygame.draw.line(surface, COR_OURO, (0, h - 2), (LARGURA_TELA, h - 2), 3)
        pygame.draw.line(surface, COR_OURO_ESCURO, (0, h), (LARGURA_TELA, h), 1)
        # Base
        base = pygame.Surface((LARGURA_TELA, h))
        for y in range(h):
            shade = int(150 - 30 * (y / max(1, h)))
            pygame.draw.line(base, (shade, shade - 20, shade - 50), (0, y), (LARGURA_TELA, y))
        surface.blit(base, (0, ALTURA_TELA - h))
        pygame.draw.line(surface, COR_OURO, (0, ALTURA_TELA - h), (LARGURA_TELA, ALTURA_TELA - h), 3)
        # Ornamentos nos cantos quando quase fechado
        if t > 0.7:
            for cx, cy in [(40, 40), (LARGURA_TELA - 40, 40), (40, ALTURA_TELA - 40), (LARGURA_TELA - 40, ALTURA_TELA - 40)]:
                pygame.draw.circle(surface, COR_OURO, (cx, cy), 8, 2)

    def _draw_portao(self, surface, t):
        # Portões de ferro que se encontram no centro
        w = int(LARGURA_TELA * 0.5 * t) + 6
        for lado, x0 in (("esq", 0), ("dir", LARGURA_TELA - w)):
            painel = pygame.Surface((w, ALTURA_TELA))
            painel.fill((32, 28, 26))
            # Barras verticais
            for bx in range(8, w, 28):
                pygame.draw.line(painel, (55, 50, 48), (bx, 0), (bx, ALTURA_TELA), 4)
                pygame.draw.line(painel, (70, 65, 60), (bx + 2, 0), (bx + 2, ALTURA_TELA), 1)
            # Barras horizontais
            for by in range(40, ALTURA_TELA, 70):
                pygame.draw.line(painel, (50, 46, 44), (0, by), (w, by), 5)
            surface.blit(painel, (x0, 0))
        # Borda dourada no encontro
        if w > 10:
            pygame.draw.line(surface, COR_OURO, (w - 2, 0), (w - 2, ALTURA_TELA), 3)
            pygame.draw.line(surface, COR_OURO, (LARGURA_TELA - w + 1, 0), (LARGURA_TELA - w + 1, ALTURA_TELA), 3)
            # Ponteiros / pontas de lança no topo
            for px in range(20, w, 40):
                pygame.draw.polygon(surface, COR_FERRO_CLARO, [(px, 0), (px + 8, 22), (px - 8, 22)])
                pygame.draw.polygon(surface, COR_FERRO_CLARO, [(LARGURA_TELA - px, 0), (LARGURA_TELA - px + 8, 22), (LARGURA_TELA - px - 8, 22)])

    def _draw_selo(self, surface, t):
        # Íris circular dourada + fundo escuro
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        # Escurece o fundo
        alpha = int(220 * min(1.0, t * 1.2))
        overlay.fill((12, 8, 6, alpha))
        surface.blit(overlay, (0, 0))
        # Anéis concêntricos
        cx, cy = LARGURA_TELA // 2, ALTURA_TELA // 2
        raio_max = int(math.hypot(LARGURA_TELA, ALTURA_TELA) * 0.55)
        raio = int(raio_max * (1.0 - t))
        if t < 0.95:
            for i in range(3):
                r = raio + i * 12
                if r > 0:
                    pygame.draw.circle(surface, COR_OURO if i == 0 else COR_OURO_ESCURO, (cx, cy), r, 3 - i)
        # Selo central quando quase fechado
        if t > 0.55:
            s = int(40 + 30 * (t - 0.55) / 0.45)
            pygame.draw.circle(surface, COR_OURO, (cx, cy), s, 3)
            pygame.draw.circle(surface, COR_OURO_ESCURO, (cx, cy), max(4, s - 12), 2)

    def _draw_texto(self, surface, t):
        # Texto só aparece no meio da transição
        alpha_t = min(1.0, max(0.0, (t - 0.4) / 0.35))
        if alpha_t <= 0:
            return
        try:
            img = fonte_grande.render(self.texto, True, COR_TEXTO_OURO)
        except Exception:
            img = fonte_menu.render(self.texto, True, COR_TEXTO_OURO)
        # Sombra
        sombra = fonte_grande.render(self.texto, True, (20, 12, 8)) if hasattr(fonte_grande, 'render') else img
        x = LARGURA_TELA // 2 - img.get_width() // 2
        y = ALTURA_TELA // 2 - img.get_height() // 2
        # Linhas douradas decorativas
        if alpha_t > 0.5:
            lw = img.get_width() + 40
            pygame.draw.line(surface, COR_OURO, (x - 20, y - 12), (x - 20 + lw, y - 12), 2)
            pygame.draw.line(surface, COR_OURO, (x - 20, y + img.get_height() + 10), (x - 20 + lw, y + img.get_height() + 10), 2)
        surface.blit(sombra, (x + 2, y + 2))
        surface.blit(img, (x, y))




# Golpes inimigos que SÓ podem ser evitados PULANDO [ESPAÇO] (rasteiros/terremotos/ondas)
GOLPES_SO_PULO = ("RASTEIRA", "ONDA_CHOQUE", "INVESTIDA", "TERREMOTO")
# Golpes inimigos que SÓ podem ser defendidos com PARRY [X] (golpes titânicos/esmagadores verticais)
GOLPES_SO_PARRY = ("ESMAGAMENTO", "GOLPE_TITANICO", "QUEBRA_GUARDA", "RODOPIO")
# Golpes inimigos que SÓ podem ser evitados DESVIANDO [C] (névoas/raios/garras rápidas)
GOLPES_SO_DESVIO = ("VENENO", "RUGIDO", "GOLPE_ARCANO", "GARRAS")
# Golpes padrão que podem ser defendidos com PARRY ou DESVIO
GOLPES_PADRAO = ("CORTE",)

# Pools de golpes para sorteio genuinamente aleatório
POOL_GOLPES_COMUNS = ["CORTE", "ESMAGAMENTO", "RASTEIRA", "GARRAS", "VENENO"]
POOL_GOLPES_MEDIOS = POOL_GOLPES_COMUNS + ["RODOPIO", "GOLPE_ARCANO", "QUEBRA_GUARDA"]
POOL_GOLPES_BOSS = POOL_GOLPES_MEDIOS + ["ONDA_CHOQUE", "INVESTIDA", "RUGIDO", "GOLPE_TITANICO", "TERREMOTO"]

# Descrições para os golpes (mostradas na UI e telegrafias)
DESCRICAO_GOLPE = {
    "CORTE": "Lâmina rápida!",
    "ESMAGAMENTO": "Golpe esmagador!",
    "RASTEIRA": "Ataque rasteiro!",
    "ONDA_CHOQUE": "Onda destruidora!",
    "INVESTIDA": "Investida colossal!",
    "TERREMOTO": "Fissura sísmica!",
    "GOLPE_TITANICO": "Clava titânica!",
    "QUEBRA_GUARDA": "Golpe pesado!",
    "RODOPIO": "Giro devastador!",
    "GARRAS": "Garras dilacerantes!",
    "VENENO": "Névoa venenosa!",
    "GOLPE_ARCANO": "Energia arcana!",
    "RUGIDO": "Rugido sônico!",
}

# Dano por tipo de golpe
DANO_GOLPE = {
    "CORTE": CONFIG["inimigo_dano_corte"],
    "ESMAGAMENTO": CONFIG["inimigo_dano_esmagamento"],
    "RASTEIRA": CONFIG["inimigo_dano_rastria"],
    "GARRAS": int(CONFIG["inimigo_dano_corte"] * 0.85),
    "VENENO": int(CONFIG["inimigo_dano_corte"] * 0.70),
    "GOLPE_ARCANO": int(CONFIG["inimigo_dano_esmagamento"] * 0.90),
    "RODOPIO": int(CONFIG["inimigo_dano_esmagamento"] * 1.10),
    "INVESTIDA": int(CONFIG["inimigo_dano_esmagamento"] * 1.05),
    "RUGIDO": int(CONFIG["inimigo_dano_corte"] * 0.60),
    "ONDA_CHOQUE": CONFIG.get("boss_dano_onda_choque", 30),
    "GOLPE_TITANICO": int(CONFIG["inimigo_dano_esmagamento"] * 1.15),
    "QUEBRA_GUARDA": int(CONFIG["inimigo_dano_esmagamento"] * 1.0),
    "TERREMOTO": CONFIG.get("boss_dano_onda_choque", 30),
}

# Informações dos efeitos de status e debuffs de combate
DEBUFFS_INFO = {
    "VENENO": {
        "nome": "Veneno",
        "icone": "[TOX]",
        "cor": (90, 225, 75),
        "cor_bg": (22, 54, 18),
        "desc": "Sofre dano tóxico a cada turno",
    },
    "SANGRANDO": {
        "nome": "Sangria",
        "icone": "[SANG]",
        "cor": (255, 80, 80),
        "cor_bg": (60, 18, 18),
        "desc": "+30% de dano sofrido em ataques",
    },
    "LENTIDAO": {
        "nome": "Lentidão",
        "icone": "[LENT]",
        "cor": (210, 180, 255),
        "cor_bg": (42, 28, 62),
        "desc": "-1 AP no início do turno",
    },
    "FRAQUEZA": {
        "nome": "Fraqueza",
        "icone": "[FRAC]",
        "cor": (175, 140, 255),
        "cor_bg": (38, 24, 60),
        "desc": "Causa -30% de dano",
    },
    "QUEIMADURA": {
        "nome": "Queimadura",
        "icone": "[FOGO]",
        "cor": (255, 175, 45),
        "cor_bg": (60, 36, 14),
        "desc": "Sofre queimação solar periódica",
    },
    "VULNERAVEL": {
        "nome": "Fenda",
        "icone": "[FENDA]",
        "cor": (90, 230, 255),
        "cor_bg": (18, 48, 62),
        "desc": "+35% de dano sofrido de ataques",
    },
}

# Quanto o sprite fica maior que a caixa de colisao no mapa (ajuste em config.py)
ESCALA_SPRITE_MAPA = CONFIG.get("sprite_escala_mapa", 1.15)

# Posições das 3 runas na Sala 7 no centro e topo exatos das plataformas (1650, 215), (3440, 330), (5370, 340)
POS_RUNAS_SALA7 = cenarios.POS_RUNAS_SALA7


# ==============================================================================
# 1. SALAS: os mapas, plataformas, inimigos e texturas ficam em cenarios.py
# ==============================================================================


# ==============================================================================
# 2. CÂMERA E ENTIDADES DO MAPA 2D
# ==============================================================================
class CameraMapa:
    """
    Câmera dinâmica de exploração 2D com interpolação linear (lerp) nos eixos X e Y,
    respeitando os limites ampliados da masmorra não-linear vertical e horizontal,
    com suporte a tremor de tela (screen shake) para alavancas, selos e impactos.
    """
    def __init__(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.alvo_x = 0.0
        self.alvo_y = 0.0
        self.velocidade_lerp = 7.0
        self.shake_intensidade = 0.0
        self.shake_timer = 0.0
        self.shake_x = 0.0
        self.shake_y = 0.0

    def tremer(self, intensidade=7.0, duracao=0.35):
        """Ativa tremor de câmera para feedback tátil ao puxar alavancas ou levar dano."""
        self.shake_intensidade = intensidade
        self.shake_timer = duracao

    def focar_instantaneo(self, alvo_x, alvo_y=None, largura_mundo=LARGURA_MUNDO, altura_mundo=ALTURA_MUNDO):
        """Enquadra o herói instantaneamente sem transição lerp ao entrar em nova sala."""
        alvo_cam_x = alvo_x - (LARGURA_TELA // 2)
        max_x = max(0.0, float(largura_mundo - LARGURA_TELA))
        self.alvo_x = self.offset_x = max(0.0, min(max_x, alvo_cam_x))
        if alvo_y is not None:
            alvo_cam_y = alvo_y - (ALTURA_TELA // 2)
            max_y = max(0.0, float(altura_mundo - ALTURA_TELA))
            self.alvo_y = self.offset_y = max(0.0, min(max_y, alvo_cam_y))
        else:
            self.alvo_y = self.offset_y = 0.0

    def update(self, alvo_x, alvo_y=None, dt=0.016, largura_mundo=LARGURA_MUNDO, altura_mundo=ALTURA_MUNDO, look_dir=0.0):
        # Câmera com antecipação (look-ahead horizontal dinâmico lerpado)
        alvo_cam_x = (alvo_x + look_dir * 70.0) - (LARGURA_TELA // 2)
        max_x = max(0.0, float(largura_mundo - LARGURA_TELA))
        self.alvo_x = max(0.0, min(max_x, alvo_cam_x))

        if alvo_y is not None:
            alvo_cam_y = alvo_y - (ALTURA_TELA // 2)
            max_y = max(0.0, float(altura_mundo - ALTURA_TELA))
            self.alvo_y = max(0.0, min(max_y, alvo_cam_y))
        else:
            self.alvo_y = 0.0

        fator = min(1.0, dt * self.velocidade_lerp)
        self.offset_x += (self.alvo_x - self.offset_x) * fator
        self.offset_y += (self.alvo_y - self.offset_y) * fator

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            self.shake_x = random.uniform(-self.shake_intensidade, self.shake_intensidade)
            self.shake_y = random.uniform(-self.shake_intensidade, self.shake_intensidade)
        else:
            self.shake_x = 0.0
            self.shake_y = 0.0

    def aplicar(self, rect):
        return pygame.Rect(
            int(rect.x - self.offset_x + self.shake_x),
            int(rect.y - self.offset_y + self.shake_y),
            rect.width,
            rect.height
        )

    def aplicar_pos(self, x, y):
        return (
            int(x - self.offset_x + self.shake_x),
            int(y - self.offset_y + self.shake_y)
        )


from player import Jogador, JogadorMapa
from inimigos import InimigoMapa, criar_inimigo_mapa


# ==============================================================================
# 3 & 4. SISTEMA TÁTICO DE COMBATE 2.5D (MÓDULO combate.py)
# ==============================================================================
import combate
from combate import (CameraCombateRig, CombateExpedition33, desenhar_chao_combate_simples,
                     GOLPES_SO_PULO, GOLPES_SO_PARRY, GOLPES_SO_DESVIO, DANO_GOLPE, DEBUFFS_INFO)


# ==============================================================================
# 5. GERENCIADOR DE SALAS E LOOP PRINCIPAL
# ==============================================================================
def criar_entidades_das_salas(progresso=None):
    salas = {}
    for idx, dados in DADOS_MAPAS.items():
        sala_de_necromantes = idx >= 3
        lista_inimigos = []
        for sp in dados["inimigos_spec"]:
            # Cada inimigo usa o proprio sprite/arte; nao usar Orc como fallback visual.
            sprite = sp["sprite"]
            hp_inimigo = progresso.escalar_hp_inimigo(sp["hp"]) if progresso else sp["hp"]
            inimigo = InimigoMapa(sp["x"], sp["y"], sp["patrulha"], sp["nome"], hp_inimigo, sp["cor"],
                                  is_boss=False, num_combos=sp["combos"], mapa=dados, sprite=sprite)
            inimigo._hp_base = sp["hp"]
            if sp["sprite"] == "Necromante":
                velocidade_extra = 1.12
            else:
                velocidade_extra = 1.04 if sala_de_necromantes else 1.0
            inimigo.vel_patrulha *= velocidade_extra
            inimigo.vel_perseguir *= velocidade_extra
            lista_inimigos.append(inimigo)

        b = dados["boss"]
        sprite_boss = b["sprite"]
        hp_boss = progresso.escalar_hp_inimigo(b["hp"]) if progresso else b["hp"]
        boss_obj = InimigoMapa(b["x"], b["y"], b["patrulha"], b["nome"], hp_boss, b["cor"], is_boss=True,
                               num_combos=b["combos"], mapa=dados, sprite=sprite_boss)
        boss_obj._hp_base = b["hp"]
        if sala_de_necromantes:
            boss_obj.vel_patrulha *= 1.10
            boss_obj.vel_perseguir *= 1.10
        if progresso is not None and idx in progresso.chefes:
            boss_obj.hp = 0
            boss_obj.vivo = False

        # Cópia independente de objetos interativos para controle de estado na sessão
        portoes_copia = [
            dict(p, rect=p["rect"].copy(), ponte=p["ponte"].copy()) if "ponte" in p else dict(p, rect=p["rect"].copy())
            for p in dados.get("portoes", [])
        ]
        alavancas_copia = [dict(a) for a in dados.get("alavancas", [])]
        chaves_copia = [dict(c) for c in dados.get("chaves", [])]
        baus_copia = [dict(b) for b in dados.get("baus", [])]

        salas[idx] = {
            "inimigos": lista_inimigos,
            "boss": boss_obj,
            "portoes": portoes_copia,
            "alavancas": alavancas_copia,
            "chaves": chaves_copia,
            "baus": baus_copia
        }
    return salas



def desenhar_banner_sala_hk(surface, nome_sala, sala_idx, tempo_restante, duracao_total=3.2):
    """Exibe um banner imersivo ao entrar em uma sala, no estilo solene de Hollow Knight."""
    if tempo_restante <= 0:
        return
    decorrido = duracao_total - tempo_restante
    if decorrido < 0.5:
        alpha = int(255 * (decorrido / 0.5))
    elif tempo_restante < 0.7:
        alpha = int(255 * (tempo_restante / 0.7))
    else:
        alpha = 255
    alpha = max(0, min(255, alpha))
    if alpha <= 0:
        return

    cx = LARGURA_TELA // 2
    cy = 135

    faixa = pygame.Surface((LARGURA_TELA, 110), pygame.SRCALPHA)
    for py in range(110):
        f = math.sin((py / 110.0) * math.pi)
        faixa_alpha = int(f * (alpha * 0.45))
        pygame.draw.line(faixa, (8, 6, 12, faixa_alpha), (0, py), (LARGURA_TELA, py))
    surface.blit(faixa, (0, cy - 55))

    sub_txt = f"— SALA {sala_idx + 1} DE 7 —"
    render_sub = fonte_pequena.render(sub_txt, True, (215, 180, 100))
    render_sub.set_alpha(alpha)
    surface.blit(render_sub, (cx - render_sub.get_width() // 2, cy - 32))

    render_tit = fonte_titulo.render(nome_sala.upper(), True, (240, 242, 252))
    render_sombra = fonte_titulo.render(nome_sala.upper(), True, (10, 8, 14))
    render_tit.set_alpha(alpha)
    render_sombra.set_alpha(int(alpha * 0.8))
    tw = render_tit.get_width()
    surface.blit(render_sombra, (cx - tw // 2 + 2, cy - 10 + 2))
    surface.blit(render_tit, (cx - tw // 2, cy - 10))

    lin_surf = pygame.Surface((LARGURA_TELA, 30), pygame.SRCALPHA)
    lw = min(460, max(280, tw + 60))
    x_ini = cx - lw // 2
    x_fim = cx + lw // 2
    y_lin = 15

    cor_lin = (212, 175, 55, alpha)
    pygame.draw.line(lin_surf, cor_lin, (x_ini, y_lin), (x_fim, y_lin), 1)
    pts_los = [(cx, y_lin - 4), (cx + 5, y_lin), (cx, y_lin + 4), (cx - 5, y_lin)]
    pygame.draw.polygon(lin_surf, cor_lin, pts_los)
    pygame.draw.circle(lin_surf, cor_lin, (x_ini, y_lin), 2)
    pygame.draw.circle(lin_surf, cor_lin, (x_fim, y_lin), 2)
    surface.blit(lin_surf, (0, cy + 28))


_TEXTURAS_PUZZLE = None

def _obter_texturas_puzzle():
    global _TEXTURAS_PUZZLE
    if _TEXTURAS_PUZZLE is not None:
        return _TEXTURAS_PUZZLE
    
    pasta = caminhos.obter_caminho_recurso("assets/puzzle")
    tex = {}
    try:
        p_altar = os.path.join(pasta, "altar_puzzle_sala7.png")
        if os.path.exists(p_altar):
            tex["altar"] = pygame.image.load(p_altar).convert_alpha()
            
        p_inativa = os.path.join(pasta, "reliquia_sheet_inativa.png")
        if os.path.exists(p_inativa):
            sheet = pygame.image.load(p_inativa).convert_alpha()
            frames = []
            for i in range(8):
                frames.append(sheet.subsurface((i * 48, 0, 48, 48)))
            tex["reliquia_inativa"] = frames
            
        p_ativa = os.path.join(pasta, "reliquia_sheet_ativa.png")
        if os.path.exists(p_ativa):
            sheet = pygame.image.load(p_ativa).convert_alpha()
            frames = []
            for i in range(8):
                frames.append(sheet.subsurface((i * 48, 0, 48, 48)))
            tex["reliquia_ativa"] = frames
            
        p_ico = os.path.join(pasta, "icone_reliquia_puzzle.png")
        if os.path.exists(p_ico):
            tex["icone"] = pygame.image.load(p_ico).convert_alpha()
    except Exception as e:
        caminhos.log_aviso(f"[puzzle] Aviso ao carregar texturas do puzzle: {e}")
        
    _TEXTURAS_PUZZLE = tex
    return _TEXTURAS_PUZZLE


def desenhar_runas_puzzle(surface, camera_offset, jogador, tempo_mundo, camera_offset_y=0):
    """Desenha os altares e as relíquias de puzzle da Sala 7 com texturas ricas de pixel art."""
    tex = _obter_texturas_puzzle()
    tex_altar = tex.get("altar")
    frames_inativo = tex.get("reliquia_inativa", [])
    frames_ativo = tex.get("reliquia_ativa", [])
    tex_icone = tex.get("icone")

    for ri, (rx, ry) in enumerate(cenarios.POS_RUNAS_SALA7):
        sx = int(rx - camera_offset)
        sy = int(ry - camera_offset_y)
        if -80 <= sx <= LARGURA_TELA + 80:
            ativada = (ri in jogador.runas_ativadas)
            pulso = 0.5 + 0.5 * math.sin(tempo_mundo * 3.2 + ri * 2.1)
            flutua_y = int(math.sin(tempo_mundo * 2.5 + ri * 1.5) * 6)
            rune_y = sy - 50 + flutua_y

            # 1. Altar de pedra apoiado na plataforma (base plana toca exatamente no topo da plataforma sy)
            if tex_altar:
                # Sombra suave de contato no topo da plataforma
                pygame.draw.ellipse(surface, (8, 6, 12, 175), (sx - 28, sy - 3, 56, 6))
                # A base do altar (y=34 da textura de 36px) encosta perfeitamente na superfície da plataforma (sy)
                surface.blit(tex_altar, (sx - tex_altar.get_width() // 2, sy - 34))
            else:
                pygame.draw.rect(surface, (32, 28, 40), (sx - 26, sy - 6, 52, 16), border_radius=3)
                pygame.draw.rect(surface, (18, 14, 24), (sx - 20, sy - 18, 40, 14), border_radius=2)
                pygame.draw.rect(surface, (80, 65, 95), (sx - 26, sy - 6, 52, 16), 1, border_radius=3)
                pygame.draw.rect(surface, (95, 80, 115), (sx - 20, sy - 18, 40, 14), 1, border_radius=2)

            # 2. Feixe de luz volumétrico ou aura mística
            cor_tema = (90, 255, 190) if ativada else (185, 95, 255)
            if ativada:
                pilar = pygame.Surface((44, 280), pygame.SRCALPHA)
                for py in range(280):
                    a_pil = int((1.0 - py / 280.0) * (60 + 45 * pulso))
                    pygame.draw.line(pilar, (90, 255, 190, a_pil), (0, py), (44, py))
                    pygame.draw.line(pilar, (240, 255, 250, a_pil // 2), (18, py), (26, py))
                surface.blit(pilar, (sx - 22, rune_y - 270))
            else:
                raio_aura = int(24 + 6 * pulso)
                aura = pygame.Surface((raio_aura * 2, raio_aura * 2), pygame.SRCALPHA)
                pygame.draw.circle(aura, (185, 95, 255, int(45 + 35 * pulso)), (raio_aura, raio_aura), raio_aura)
                surface.blit(aura, (sx - raio_aura, rune_y - raio_aura))

            # 3. Item de Puzzle / Relíquia Arcana (Textura animada de rotação)
            frames_reliquia = frames_ativo if ativada else frames_inativo
            if frames_reliquia:
                velocidade_rot = 9.0 if ativada else 5.0
                f_idx = int((tempo_mundo * velocidade_rot + ri * 2.3)) % len(frames_reliquia)
                frame_atual = frames_reliquia[f_idx]
                surface.blit(frame_atual, (sx - frame_atual.get_width() // 2, rune_y - frame_atual.get_height() // 2))
            else:
                tam = int(15 + (3 * pulso if ativada else 1))
                pts_ext = [(sx, rune_y - tam), (sx + tam, rune_y), (sx, rune_y + tam), (sx - tam, rune_y)]
                pygame.draw.polygon(surface, cor_tema, pts_ext, 3)
                pts_int = [(sx, rune_y - tam // 2), (sx + tam // 2, rune_y), (sx, rune_y + tam // 2), (sx - tam // 2, rune_y)]
                pygame.draw.polygon(surface, (255, 255, 255) if ativada else (220, 180, 255), pts_int)
                pygame.draw.circle(surface, cor_tema, (sx, rune_y), 4)

            # 4. Prompt de proximidade estilizado com ícone da relíquia
            dist_jog_x = abs((jogador.x + jogador.largura / 2) - rx)
            dist_jog_y = abs((jogador.y + jogador.altura / 2) - ry)
            if dist_jog_x < 95 and dist_jog_y < 95:
                if not ativada:
                    tag_e = ui_medieval.tag_comando("interagir")
                    prompt = fonte_pequena.render(f"{tag_e} SINTONIZAR RELÍQUIA ARCANAS ({ri + 1}/3)", True, (255, 235, 140))
                    pw = prompt.get_width() + 44
                    ph = max(34, prompt.get_height() + 10)
                    caixa = pygame.Rect(sx - pw // 2, rune_y - 48, pw, ph)
                    ui_procedural.desenhar_moldura_gotica(surface, caixa, chanfro=5, destacado=True, alpha=244, cantoneiras=False)
                    if tex_icone:
                        surface.blit(tex_icone, (caixa.x + 6, caixa.y + 1))
                    surface.blit(prompt, (caixa.x + 38, caixa.y + (ph - prompt.get_height()) // 2))
                else:
                    prompt = fonte_pequena.render(f"✓ RELÍQUIA {ri + 1} SINTONIZADA", True, (120, 255, 180))
                    pw = prompt.get_width() + 40
                    ph = max(32, prompt.get_height() + 8)
                    caixa = pygame.Rect(sx - pw // 2, rune_y - 44, pw, ph)
                    ui_procedural.desenhar_moldura_gotica(surface, caixa, chanfro=5, destacado=False, alpha=240, cantoneiras=False)
                    if tex_icone:
                        surface.blit(tex_icone, (caixa.x + 6, caixa.y))
                    surface.blit(prompt, (caixa.x + 34, caixa.y + (ph - prompt.get_height()) // 2))


def desenhar_hud_mapa(surface, mapa_idx, mapa_atual, jogador, grupo_sala, boss_atual):
    """HUD limpo em Safe Area (16px): status 260x60 à esquerda e placa de missão 340x28 no centro superior."""
    prog_ref = getattr(jogador, "progresso_ref", None)
    nome_h = getattr(prog_ref, "nome_heroi", "Guerreiro") if prog_ref else "Guerreiro"
    vidas_q = prog_ref.tentativas if prog_ref else 3
    pocoes_q = prog_ref.total_pocoes_cura() if prog_ref else 3
    cristais_q = prog_ref.total_cristais_eter() if prog_ref else 2

    ui.desenhar_hud_mapa_compacto(
        surface, nome_h, jogador.hp, jogador.max_hp,
        cristais_q, pocoes_q, vidas_q, vidas_max=3, margin=16
    )

    chaves_q = getattr(jogador, "chaves_bolsa", 0)
    if chaves_q > 0:
        r_ch = pygame.Rect(16, 82, 134, 24)
        ui_procedural.desenhar_painel_hud_compacto(surface, r_ch, alpha=235, borda_ouro=True, destacado=True)
        pygame.draw.circle(surface, (253, 230, 138), (r_ch.left + 14, r_ch.centery), 5, 2)
        pygame.draw.line(surface, (253, 230, 138), (r_ch.left + 19, r_ch.centery), (r_ch.left + 29, r_ch.centery), 2)
        pygame.draw.line(surface, (253, 230, 138), (r_ch.left + 26, r_ch.centery), (r_ch.left + 26, r_ch.centery + 4), 2)
        s_ch = fonte_pequena.render(f"Chaves: {chaves_q}", True, (253, 230, 138))
        surface.blit(s_ch, (r_ch.left + 36, r_ch.centery - s_ch.get_height() // 2))

    obj_txt, obj_concluido = cenarios.obter_objetivo_sala(mapa_idx, mapa_atual, grupo_sala, jogador)
    sub_reg = cenarios.obter_sub_regiao(mapa_idx, jogador.y + jogador.altura / 2.0)
    texto_missao = f"{sub_reg} — {obj_txt}" if sub_reg else f"{mapa_atual['nome']} — {obj_txt}"
    ui.desenhar_placa_missao_topo(surface, texto_missao, concl=obj_concluido, margin_top=16)


def desenhar_barra_boss_mapa(surface, boss_atual, tempo=0.0):
    """Barra monumental limpa do Chefe no modo de exploração ao aproximar-se da arena."""
    if not boss_atual or not getattr(boss_atual, "vivo", True) or getattr(boss_atual, "hp", 0) <= 0:
        return

    bw, bh = 500, 12
    bx = (LARGURA_TELA - bw) // 2
    by = ALTURA_TELA - 42
    max_hp = max(1, getattr(boss_atual, "max_hp", boss_atual.hp))
    hp_atual = max(0, min(max_hp, boss_atual.hp))
    fase_atual = 1 if (hp_atual / float(max_hp)) > 0.5 else 2
    ui_procedural.desenhar_barra_boss_monumental(
        surface, bx, by, bw, bh, hp_atual, max_hp,
        getattr(boss_atual, "nome", "CHEFE DO VAZIO"),
        fase_atual=fase_atual, fases_totais=2, tempo=tempo,
    )


def desenhar_cronometro_superior(surface, tempo_segundos, modo_jogo="MAPA"):
    """Relógio minimalista: fixo no rodapé inferior esquerdo no Mapa (deixa lua livre no topo direito)."""
    modo_expo = CONFIG.get("modo_exposicao_ativo", False)
    urgente = False
    if modo_expo:
        tempo_limite = float(CONFIG.get("exposicao_tempo_limite_segundos", 300))
        restante = max(0.0, tempo_limite - tempo_segundos)
        m, s = int(restante // 60), int(restante % 60)
        dec = int((restante - int(restante)) * 10)
        texto_tempo = f"{m:02d}:{s:02d}.{dec}"
        urgente = (restante < 60.0)
        txt_rotulo = "DEMO"
    else:
        texto_tempo = formatar_tempo(tempo_segundos)
        txt_rotulo = None

    if modo_jogo == "MAPA":
        pisca_urg = urgente and (math.sin(pygame.time.get_ticks() * 0.01) > 0)
        ui.desenhar_relogio_inferior_esquerdo(surface, texto_tempo, rotulo=txt_rotulo, urgente=pisca_urg, margin=16)
        return

    cx_cron, cy_cron = ui_configurador.obter_posicao("cronometro_combate")
    cx_cron = min(cx_cron, LARGURA_TELA - 16 - 152)
    cy_cron = max(16, cy_cron)
    rect = pygame.Rect(cx_cron, cy_cron, 152, 28)

    f_cron = ui_procedural.obter_fonte_serif(13, bold=True)
    cor_num = ui_procedural.COR_VERMELHO_DANO if (urgente and math.sin(pygame.time.get_ticks() * 0.01) > 0) else (
        ui_procedural.COR_OURO_VIVO if modo_expo else ui_procedural.COR_BRANCO_PEROLA
    )

    ui_procedural.desenhar_painel_hud_compacto(surface, rect, alpha=240, borda_ouro=True, destacado=(not urgente), chanfro=5)
    icx, icy = rect.left + 15, rect.centery
    pygame.draw.circle(surface, ui_procedural.COR_VERMELHO_DANO if urgente else ui_procedural.COR_OURO_BRILHO, (icx, icy), 6, 1)
    pygame.draw.line(surface, ui_procedural.COR_OURO_VIVO, (icx, icy), (icx, icy - 4), 1)
    pygame.draw.line(surface, ui_procedural.COR_OURO_VIVO, (icx, icy), (icx + 3, icy), 1)

    if txt_rotulo:
        s_rot = f_cron.render(txt_rotulo, True, ui_procedural.COR_OURO_BRILHO)
        surface.blit(s_rot, (rect.left + 26, rect.centery - s_rot.get_height() // 2))

    surf_num = f_cron.render(texto_tempo, True, cor_num)
    nx = rect.right - surf_num.get_width() - 12 if txt_rotulo else rect.left + 28
    surface.blit(surf_num, (nx, rect.centery - surf_num.get_height() // 2))


def main():
    global CONTROLE_ATIVO, CONTROLES
    obter_controle_ativo()
    progresso = Progresso()
    salas_entidades = criar_entidades_das_salas(progresso)

    def _criar_jogador_inicial():
        sp0 = DADOS_MAPAS[0].get("spawn_heroi", (80, LIMITE_SUBSOLO - 56))
        jog = JogadorMapa(sp0[0], sp0[1])
        jog.progresso_ref = progresso
        jog.max_hp = progresso.max_hp_total()
        jog.hp = jog.max_hp
        jog.mapa_idx = 0
        return jog

    mapa_idx = progresso.ultima_sala
    mapa_atual = DADOS_MAPAS[mapa_idx]
    spawn_init = mapa_atual.get("spawn_heroi", (80, LIMITE_SUBSOLO - 56))
    jogador = JogadorMapa(spawn_init[0], spawn_init[1])
    jogador.progresso_ref = progresso
    jogador.max_hp = progresso.max_hp_total()
    jogador.hp = progresso.hp_da_sala(mapa_idx)
    jogador.mapa_idx = mapa_idx
    camera = CameraMapa()
    camera.focar_instantaneo(jogador.x, jogador.y, mapa_atual.get("largura", LARGURA_MUNDO), mapa_atual.get("altura", ALTURA_MUNDO))
    menu = MenuInicial(progresso)
    splash_estudio = AnimacaoAberturaEstudio(LARGURA_TELA, ALTURA_TELA)
    abertura_menu_fade = 0.0
    vagalumes = Vagalumes(36)

    modo_jogo = "SPLASH_ESTUDIO"
    tela_morte = TelaDeMorte()
    tela_fim_exposicao = TelaFimExposicao()
    combate = None
    mini_cutscene = None
    cutscene_final = None
    cutscene_intro = None
    inimigo_em_luta = None
    tempo_mundo = 0.0
    timer_ultimo_analogico = 0.0
    timer_inatividade_menu = 0.0
    timer_inatividade_jogo = 0.0
    run_finalizada = False
    modo_boss_rush = False
    boss_rush_idx = 0
    boss_rush_trans = None
    inimigos_derrotados_sessao = 0
    metricas_sessao = {"dano": 0, "parries": 0, "qtes": 0}
    metricas_rush = {"dano": 0, "parries": 0, "qtes": 0, "tempo": 0.0}
    ultimo_rank_resultado = None
    transicao = TransicaoMedieval()
    banner_sala = {"nome": mapa_atual["nome"], "idx": mapa_idx, "tempo": 3.2}
    configurador_ui_global = ui_configurador.TelaMenuConfiguracoes(fonte_pequena, fonte, fonte_grande)
    modo_anterior = "MENU"

    notificacoes_hud = []

    def adicionar_notificacao(texto, cor=(255, 230, 100), duracao=3.2):
        notificacoes_hud.append({"texto": texto, "cor": cor, "tempo": duracao, "tempo_max": duracao})

    def desenhar_notificacoes_hud(surface, dt):
        y_pos = 54
        for notif in list(notificacoes_hud):
            notif["tempo"] -= dt
            if notif["tempo"] <= 0:
                notificacoes_hud.remove(notif)
                continue
            txt = notif["texto"]
            surf_txt = fonte_pequena.render(txt, True, notif["cor"])
            surf_somb = fonte_pequena.render(txt, True, (8, 6, 12))
            bw = min(560, surf_txt.get_width() + 34)
            bh = 30
            bx = (LARGURA_TELA - bw) // 2
            rect_b = pygame.Rect(bx, y_pos, bw, bh)
            ui_procedural.desenhar_painel_hud_compacto(surface, rect_b, alpha=240, borda_ouro=True, destacado=True)
            surface.blit(surf_somb, (rect_b.centerx - surf_txt.get_width() // 2 + 1, rect_b.centery - surf_txt.get_height() // 2 + 1))
            surface.blit(surf_txt, (rect_b.centerx - surf_txt.get_width() // 2, rect_b.centery - surf_txt.get_height() // 2))
            y_pos += bh + 6

    def _coletar_chave(chave, grupo, origem="interacao"):
        if not chave or chave.get("coletada", False):
            return False
        chave["coletada"] = True
        audio.tocar_sfx("potion", 0.9)
        camera.tremer(intensidade=5.0, duracao=0.25)

        jogador.hp = min(jogador.max_hp, jogador.hp + 15)
        subiu_ch, nv_ch, _ = progresso.ganhar_xp(25)
        extra_xp = f" • NÍVEL {nv_ch}!" if subiu_ch else " (+25 XP, +15 HP)"

        alvo_id = chave.get("alvo")
        portao_alvo = None
        for g in grupo.get("portoes", []):
            if g.get("id") == alvo_id:
                portao_alvo = g
                break

        if portao_alvo is not None and not portao_alvo.get("aberto", False):
            portao_alvo["aberto"] = True
            adicionar_notificacao(
                chave.get("msg_coletada", f"{chave.get('nome', 'Chave')}! Portão Destrancado{extra_xp}"),
                cor=(120, 255, 160),
            )
        else:
            # Portão já foi destrancado (ex: pela alavanca): chave vai para a bolsa + enfraquece o Chefe da sala!
            jogador.chaves_bolsa = getattr(jogador, "chaves_bolsa", 0) + 1
            boss_s = grupo.get("boss")
            if boss_s and getattr(boss_s, "vivo", False) and boss_s.hp > 1 and not getattr(boss_s, "enfraquecido_por_chave", False):
                boss_s.enfraquecido_por_chave = True
                boss_s.hp = max(1, int(boss_s.hp * 0.85))
                adicionar_notificacao(
                    f"{chave.get('nome', 'Chave')} Guardada na Bolsa ({jogador.chaves_bolsa})! Chefe -15% HP{extra_xp}",
                    cor=(253, 230, 138),
                )
            else:
                adicionar_notificacao(
                    f"{chave.get('nome', 'Chave')} Guardada na Bolsa ({jogador.chaves_bolsa}){extra_xp}",
                    cor=(253, 230, 138),
                )
        return True

    def _ativar_rel_sala7(ri, grupo, com_chave=False):
        if ri in jogador.runas_ativadas:
            return False
        jogador.runas_ativadas.add(ri)
        audio.tocar_sfx("door_open", 0.9)
        camera.tremer(intensidade=5.5, duracao=0.3)

        qtd = len(jogador.runas_ativadas)
        boss_s7 = grupo.get("boss")
        if boss_s7 and getattr(boss_s7, "vivo", False) and boss_s7.hp > 1:
            boss_s7.hp = max(1, int(boss_s7.hp * 0.88))

        if qtd == 1:
            jogador.hp = min(jogador.max_hp, jogador.hp + 25)
            progresso.ganhar_xp(15)
            adicionar_notificacao("Relíquia 1/3 Sintonizada! Escudo do Chefe -12% HP (+25 HP, +15 XP)!", cor=(180, 140, 255))
        elif qtd == 2:
            if jogador.progresso_ref:
                jogador.progresso_ref.adicionar_frasco_eter(1)
            adicionar_notificacao("Relíquia 2/3 Sintonizada! Escudo Ruindo (-23% HP) +1 Frasco de Éter!", cor=(135, 220, 255))
        else:
            for g in grupo.get("portoes", []):
                g["aberto"] = True
            if boss_s7:
                boss_s7.escudo_quebrado = True
            adicionar_notificacao(
                "ESCUDO ARCANO COLAPSADO (3/3)! Portal Liberado e Vantagem Total no Chefe!",
                cor=(100, 255, 200),
                duracao=4.2,
            )
        return True

    def interagir_com_mapa():
        px = jogador.x + jogador.largura / 2.0
        py = jogador.y + jogador.altura / 2.0
        grupo = salas_entidades[mapa_idx]
        interagiu = False

        # 1. Alavancas e Mecanismos Góticos
        for alavanca in grupo.get("alavancas", []):
            dist = math.hypot(px - alavanca["x"], py - alavanca["y"])
            if dist <= 85.0:
                if not alavanca.get("acionada", False):
                    alavanca["acionada"] = True
                    interagiu = True
                    audio.tocar_sfx("door_open", 0.9)
                    camera.tremer(intensidade=7.5, duracao=0.35)
                    alvo_id = alavanca.get("alvo")
                    levers_alvo = [a for a in grupo.get("alavancas", []) if a.get("alvo") == alvo_id]
                    if all(a.get("acionada", False) for a in levers_alvo):
                        for g in grupo.get("portoes", []):
                            if g.get("id") == alvo_id:
                                g["aberto"] = True
                        adicionar_notificacao(alavanca.get("msg_destrancado", "Mecanismo Acionado! Portão Destrancado!"), cor=(120, 255, 160))
                    else:
                        ativas = sum(1 for a in levers_alvo if a.get("acionada", False))
                        total = len(levers_alvo)
                        adicionar_notificacao(f"Selo Ativado ({ativas}/{total})! Encontre o próximo mecanismo.", cor=(255, 230, 100))
                    break

        if not interagiu:
            # 2. Chaves Rúnicas (portão, enfraquecimento de chefe e reserva na bolsa)
            for chave in grupo.get("chaves", []):
                dist = math.hypot(px - chave["x"], py - chave["y"])
                if dist <= 75.0 and not chave.get("coletada", False):
                    interagiu = _coletar_chave(chave, grupo, origem="E")
                    break

        if not interagiu:
            # 3. Baús de Recompensa (Poções e Frascos de Éter)
            for bau in grupo.get("baus", []):
                dist = math.hypot(px - bau["x"], py - (bau["y"] + 12))
                if dist <= 75.0 and not bau.get("aberto", False):
                    bau["aberto"] = True
                    interagiu = True
                    audio.tocar_sfx("potion", 0.95)
                    camera.tremer(intensidade=4.0, duracao=0.2)
                    tipo_b = bau.get("tipo", "pocao")
                    qtd = bau.get("quantidade", 1)
                    if tipo_b == "pocao":
                        if jogador.progresso_ref:
                            jogador.progresso_ref.adicionar_pocao_cura(qtd)
                        jogador.hp = min(jogador.max_hp, jogador.hp + 50)
                        adicionar_notificacao(f"{bau.get('nome', 'Baú')} Aberto! +{qtd} Poção de Vida (+50 HP)!", cor=(100, 255, 180))
                    elif tipo_b == "eter":
                        if jogador.progresso_ref:
                            jogador.progresso_ref.adicionar_frasco_eter(qtd)
                        adicionar_notificacao(f"{bau.get('nome', 'Baú')} Aberto! +{qtd} Frasco de Éter!", cor=(120, 220, 255))
                    else:
                        jogador.hp = min(jogador.max_hp, jogador.hp + 50)
                        adicionar_notificacao("Tesouro Obtido! Vitalidade Restaurada!", cor=(255, 235, 140))
                    break

        if not interagiu and mapa_idx == 6:
            # 4. Relíquias da Sala 7 (Santuário do Guardião — Quebra o Escudo do Chefe e Abre o Altar)
            for ri, (rx, ry) in enumerate(cenarios.POS_RUNAS_SALA7):
                dist = math.hypot(px - rx, py - ry)
                if dist <= 95.0 and ri not in jogador.runas_ativadas:
                    interagiu = _ativar_rel_sala7(ri, grupo)
                    break

        if not interagiu:
            # 5. Interação direta com portão trancado (usa Chave da Bolsa se houver!)
            for gate in grupo.get("portoes", []):
                if not gate.get("aberto", False):
                    g_rect = gate["rect"]
                    if abs(px - g_rect.centerx) < 68 and abs(py - g_rect.centery) < g_rect.height // 2 + 40:
                        if getattr(jogador, "chaves_bolsa", 0) > 0:
                            jogador.chaves_bolsa -= 1
                            if mapa_idx == 6 and len(jogador.runas_ativadas) < 3:
                                prox_r = next((idx_r for idx_r in range(3) if idx_r not in jogador.runas_ativadas), None)
                                if prox_r is not None:
                                    _ativar_rel_sala7(prox_r, grupo, com_chave=True)
                                if len(jogador.runas_ativadas) >= 3:
                                    gate["aberto"] = True
                            else:
                                gate["aberto"] = True
                                audio.tocar_sfx("door_open", 0.9)
                                camera.tremer(intensidade=6.0, duracao=0.25)
                                adicionar_notificacao(f"Chave da Bolsa usada! {gate.get('nome', 'Portão')} Destrancado!", cor=(120, 255, 160))
                        else:
                            audio.tocar_sfx("parry", 0.6)
                            camera.tremer(intensidade=3.0, duracao=0.15)
                            if mapa_idx == 6:
                                adicionar_notificacao("Sintonize as 3 Relíquias Arcanas para quebrar o selo!", cor=(190, 140, 255))
                            else:
                                adicionar_notificacao(f"{gate.get('nome', 'Portão')} Trancado! Acione a alavanca ou use uma Chave.", cor=(255, 120, 120))
                        break

    def entrar_na_sala(idx, x=None, hp=None):
        """Coloca o personagem na sala `idx` com a vida salva dessa sala (ou `hp`, se informado)."""
        nonlocal mapa_idx, mapa_atual
        mapa_idx = idx
        mapa_atual = DADOS_MAPAS[idx]
        spawn = mapa_atual.get("spawn_heroi", (80, 1084))
        if x is not None:
            jogador.x = float(x)
            larg_m = mapa_atual.get("largura", LARGURA_MUNDO)
            if x > larg_m * 0.5 and "portal_saida" in mapa_atual:
                jogador.y = float(mapa_atual["portal_saida"][1] + 180 - jogador.altura)
            else:
                jogador.y = float(spawn[1])
        else:
            jogador.x = float(spawn[0])
            jogador.y = float(spawn[1])
        jogador.vx = jogador.vy = 0.0
        jogador.no_chao = True
        jogador.tempo_coyote = 0.12
        jogador.buffer_pulo = 0.0
        jogador.rect.x = int(jogador.x)
        jogador.rect.y = int(jogador.y)
        jogador.atacando = False
        jogador.atacando_baixo = False
        jogador.hitbox_ataque = None
        jogador.hitbox_pogo = None
        jogador.em_esquiva = False
        jogador.hitbox_reduzida = False
        jogador.esquiva_frames_restantes = 0
        jogador.iframes_tempo = 0.0
        jogador.stagger_timer = 0.0
        jogador.pulos_aereos_disponiveis = 1
        jogador.progresso_ref = progresso
        jogador.mapa_idx = idx
        jogador.max_hp = progresso.max_hp_total()
        jogador.hp = progresso.hp_da_sala(idx) if hp is None else hp
        progresso.ultima_sala = idx
        progresso.registrar_vida(idx, jogador.hp)
        banner_sala["nome"] = mapa_atual["nome"]
        banner_sala["idx"] = idx
        banner_sala["tempo"] = 3.2
        grupo = salas_entidades[idx]
        for inim in grupo["inimigos"] + [grupo["boss"]]:
            inim.resetar_comportamento()
        larg_m = mapa_atual.get("largura", LARGURA_MUNDO)
        alt_m = mapa_atual.get("altura", ALTURA_MUNDO)
        camera.focar_instantaneo(jogador.x, jogador.y, larg_m, alt_m)
        audio.tocar_sfx("door_open", 0.75)
        if idx in (1, 4, 5):
            audio.tocar_musica("forest_theme")
        else:
            audio.tocar_musica("dungeon_theme")
        caminhos.log_info(f"Entrando na Sala {idx + 1}: {mapa_atual['nome']} (HP: {jogador.hp}/{jogador.max_hp}, Nível: {progresso.nivel}, Vidas: {progresso.tentativas}).")

    running = True
    while running:
        dt = min(relogio.tick(FPS) / 1000.0, 0.05)
        tempo_mundo += dt

        # Cronômetro ininterrupto: separa corrida Boss Rush sem resetar o tempo salvo do perfil de Campanha
        if modo_boss_rush and (modo_jogo in ("COMBATE", "BOSS_RUSH_TRANSICAO", "MORTE") or (transicao.ativa and modo_jogo not in ("MENU", "EXPOSICAO_FIM"))):
            metricas_rush["tempo"] += dt
            if combate is not None:
                combate.tempo_boss_rush_ativo = metricas_rush["tempo"]
        elif modo_jogo in ("MAPA", "COMBATE", "MORTE", "CUTSCENE_PASSAGEM") or (transicao.ativa and modo_jogo not in ("MENU", "EXPOSICAO_FIM")):
            progresso.avancar_tempo(dt)

        # Verificação do Modo Exposição / Demonstração (Showcase Kiosk Mode)
        if CONFIG.get("modo_exposicao_ativo", False) and modo_jogo in ("MAPA", "COMBATE", "MORTE") and not transicao.ativa:
            tempo_limite = float(CONFIG.get("exposicao_tempo_limite_segundos", 300))
            if progresso.tempo_decorrido >= tempo_limite:
                if not run_finalizada:
                    run_finalizada = True
                    rk_demo = ranking.calcular_rank_desempenho(
                        dano_recebido=metricas_sessao["dano"] + 45,
                        tempo_segundos=progresso.tempo_decorrido,
                        tempo_meta=max(60.0, tempo_limite * 0.75),
                        qtes_perfeitos=metricas_sessao["qtes"],
                        parries_perfeitos=metricas_sessao["parries"],
                        venceu=False,
                    )
                    ultimo_rank_resultado = rk_demo
                    RANKING_GLOBAL.adicionar_registro(
                        nome=progresso.nome_heroi,
                        tempo=progresso.tempo_decorrido,
                        tentativas=progresso.tentativas_gastas,
                        passou=False,
                        sala=mapa_idx + 1,
                        modo="DEMO",
                        rank=rk_demo["rank"],
                        pontuacao=rk_demo["pontuacao"],
                        dano_recebido=metricas_sessao["dano"],
                        parries_perfeitos=metricas_sessao["parries"],
                        qtes_perfeitos=metricas_sessao["qtes"],
                    )
                    caminhos.log_info(f"DEMO (TEMPO ESGOTADO): Herói '{progresso.nome_heroi}' gravado no Ranking Demo ({progresso.tempo_decorrido:.1f}s, Sala {mapa_idx + 1}, Rank {rk_demo['rank']}).")
                def _ir_fim_tempo():
                    nonlocal modo_jogo
                    tela_fim_exposicao.configurar(
                        motivo="TEMPO_ESGOTADO",
                        progresso=progresso,
                        mapa_idx=mapa_idx,
                        inimigos_derrotados=inimigos_derrotados_sessao,
                        resumo_rank=ultimo_rank_resultado,
                    )
                    modo_jogo = "EXPOSICAO_FIM"
                transicao.iniciar("EXPOSICAO_FIM", estilo="selo", texto="TEMPO ESGOTADO", callback=_ir_fim_tempo)

        # Transição medieval entre telas
        novo_modo = transicao.update(dt)
        if novo_modo is not None:
            modo_jogo = novo_modo

        for raw_event in pygame.event.get():
            event = _ajustar_evento_mouse(raw_event)
            # Detecção dinâmica unificada (Teclado/Mouse vs Controle Xbox/PS com hot-swap sem flickering)
            joy_atual = obter_controle_ativo()
            joy_nome_atual = ""
            if joy_atual is not None:
                try:
                    joy_nome_atual = joy_atual.get_name()
                except Exception:
                    joy_nome_atual = ""
            ui_procedural.INPUT_MANAGER.processar_evento(event, nome_joystick=joy_nome_atual)
            ui_medieval._dispositivo_input = ui_procedural.INPUT_MANAGER.modo_input

            # Durante transição, só permite QUIT
            if transicao.bloqueando and event.type != pygame.QUIT:
                continue

            # Reset dos cronômetros de inatividade com qualquer interação do jogador
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
                timer_inatividade_menu = 0.0
                timer_inatividade_jogo = 0.0
            elif event.type == pygame.JOYAXISMOTION and abs(event.value) > 0.45:
                timer_inatividade_menu = 0.0
                timer_inatividade_jogo = 0.0
            elif event.type == pygame.MOUSEMOTION and (abs(event.rel[0]) > 4 or abs(event.rel[1]) > 4):
                timer_inatividade_menu = 0.0

            # Interrupção da Vitrine Automática: qualquer toque nos controles assume o jogo na hora!
            if BOT.modo_vitrine:
                if event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.MOUSEBUTTONDOWN):
                    if event.type != pygame.KEYDOWN or event.key not in (pygame.K_F11, pygame.K_F2):
                        BOT.desligar()
                        audio.tocar_sfx("ui_confirm", 0.85)
                        caminhos.log_info("Visitante tocou nos controles: Modo Vitrine finalizado, controle assumido!")

            # Atalho Global para Modo Tela Cheia (F11 ou Alt + Enter) - Disponível em qualquer tela/menu
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_F11 or (event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (event.mod & pygame.KMOD_ALT))):
                alternar_tela_cheia()
                continue

            # Atalho Global para Alternar o Bot Autônomo (F2)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                st = BOT.alternar()
                audio.tocar_sfx("ui_select", 0.6)
                caminhos.log_info(f"Modo Bot alterado via [F2]: {st}")
                continue

            # Atalho Global para Configuração de Posições da UI [F10]
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F10:
                if modo_jogo == "SPLASH_ESTUDIO":
                    continue
                if modo_jogo != "CONFIG_UI":
                    modo_anterior = modo_jogo
                    configurador_ui_global.abrir_hub()
                    modo_jogo = "CONFIG_UI"
                    audio.tocar_sfx("door_open", 0.8)
                    continue
                else:
                    modo_jogo = modo_anterior
                    audio.tocar_sfx("ui_select", 0.5)
                    continue

            if modo_jogo == "CONFIG_UI":
                res = configurador_ui_global.handle_event(event)
                if res in ("voltar", "salvo") and configurador_ui_global.estado == "HUB":
                    modo_jogo = modo_anterior
                continue

            # Reset Rápido do Expositor via Teclado [F5]
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                BOT.desligar()
                timer_inatividade_menu = 0.0
                timer_inatividade_jogo = 0.0
                def _reset_expo():
                    menu.abrir_principal()
                transicao.iniciar("MENU", estilo="fade", texto="REINICIANDO DEMO", callback=_reset_expo)
                continue

            # Reset Rápido do Expositor via Controle Xbox (Apertar Back/View + Menu/Start)
            if event.type == pygame.JOYBUTTONDOWN:
                joy_chk = obter_controle_ativo()
                if joy_chk:
                    try:
                        b_view = joy_chk.get_button(6) if joy_chk.get_numbuttons() > 6 else False
                        b_start = joy_chk.get_button(7) if joy_chk.get_numbuttons() > 7 else False
                        if (b_view and b_start) or (event.button == 6 and b_start) or (event.button == 7 and b_view):
                            BOT.desligar()
                            timer_inatividade_menu = 0.0
                            timer_inatividade_jogo = 0.0
                            def _reset_expo_joy():
                                menu.abrir_principal()
                            transicao.iniciar("MENU", estilo="fade", texto="REINICIANDO DEMO", callback=_reset_expo_joy)
                            continue
                    except Exception:
                        pass

            # Hotplug de controle Xbox / genérico SDL
            if event.type == pygame.JOYDEVICEADDED:
                try:
                    novo_joy = pygame.joystick.Joystick(event.device_index)
                    novo_joy.init()
                    if novo_joy not in CONTROLES:
                        CONTROLES.append(novo_joy)
                    CONTROLE_ATIVO = novo_joy
                    joy_n = ""
                    try:
                        joy_n = novo_joy.get_name()
                    except Exception:
                        pass
                    ui_procedural.INPUT_MANAGER.atualizar_dispositivo_joystick(True, joy_n)
                    ui_medieval.definir_dispositivo_input("CONTROLE", nome_controle=joy_n)
                    caminhos.log_info(f"Controle conectado: '{joy_n}' (Dispositivo {event.device_index}).")
                except Exception as e:
                    caminhos.log_aviso(f"Erro ao inicializar controle: {e}")
                continue
            if event.type == pygame.JOYDEVICEREMOVED:
                CONTROLES = [j for j in CONTROLES if j.get_instance_id() != event.instance_id]
                CONTROLE_ATIVO = CONTROLES[0] if CONTROLES else None
                joy_n_rem = ""
                if CONTROLE_ATIVO is not None:
                    try:
                        joy_n_rem = CONTROLE_ATIVO.get_name()
                    except Exception:
                        pass
                ui_procedural.INPUT_MANAGER.atualizar_dispositivo_joystick(bool(CONTROLES), joy_n_rem)
                if not CONTROLES:
                    ui_medieval.definir_dispositivo_input("TECLADO")
                caminhos.log_info(f"Controle desconectado (Instância {event.instance_id}). Ativos: {len(CONTROLES)}.")
                continue

            # Mapeamento oficial de botões do Controle Xbox (XInput / SDL)
            if event.type == pygame.JOYBUTTONDOWN:
                btn = event.button
                if modo_jogo == "COMBATE" and combate is not None:
                    # No combate tático Expedition 33:
                    if combate.estado == "MENU_JOGADOR":
                        # A (0) ou X (2) = Selecionar / Atacar / Confirmar
                        # B (1) = Voltar / Cancelar
                        # LB (4) = Alvo anterior
                        # RB (5) = Próximo alvo
                        # Back (6) = Alternar tela cheia
                        # Start (7) = Voltar / Pausa
                        if btn in (0, 2):
                            combate.handle_keydown(pygame.K_RETURN)
                        elif btn == 1:
                            combate.handle_keydown(pygame.K_ESCAPE)
                        elif btn == 4:
                            combate.selecionar_alvo(-1)
                        elif btn == 5:
                            combate.selecionar_alvo(1)
                        elif btn == 6:
                            alternar_tela_cheia()
                        elif btn == 7:
                            combate.handle_keydown(pygame.K_ESCAPE)

                    elif combate.estado == "QTE_JOGADOR":
                        # Golpe de Timing: X (2), A (0) ou Y (3) acertam o timing!
                        if btn in (0, 2, 3):
                            combate.resolver_golpe_qte(apertou_botao=True)
                        elif btn == 6:
                            alternar_tela_cheia()

                    elif combate.estado == "TURNO_INIMIGO":
                        # Defesa Reativa no Timing Exato:
                        # A (0) = Pular (golpes rasteiros/sísmicos)
                        # X (2) = Parry (golpes normais e titânicos)
                        # B (1) = Desvio (névoas, rugidos e garras)
                        if btn == 0:
                            combate.handle_keydown(pygame.K_SPACE)
                        elif btn == 2:
                            combate.handle_keydown(pygame.K_x)
                        elif btn == 1:
                            combate.handle_keydown(pygame.K_c)
                        elif btn == 6:
                            alternar_tela_cheia()
                    else:
                        if btn == 6:
                            alternar_tela_cheia()

                elif modo_jogo == "MAPA":
                    # No mapa de exploração (Estritamente 1 Jogador):
                    # A (0) = Pulo / Salto de Reação (Vault Leap)
                    # B (1) = Esquiva Rasteira / Roll Dash (14 I-Frames + hitbox pela metade)
                    # X (2) = Atacar com espada (ou Pogo ↓ segurando para baixo no ar)
                    # Y (3) = Interagir com relíquias / puzzle
                    # Start (7) = Voltar ao Menu
                    # Back (6) = Alternar tela cheia
                    if btn == 0:
                        jogador.solicitar_pulo()
                    elif btn == 1:
                        jogador.iniciar_esquiva()
                    elif btn == 3:
                        interagir_com_mapa()
                    elif btn == 2:
                        px = jogador.x + jogador.largura / 2.0
                        py = jogador.y + jogador.altura / 2.0
                        grupo = salas_entidades[mapa_idx]
                        perto_interativo = (
                            any(math.hypot(px - a["x"], py - a["y"]) <= 85 for a in grupo.get("alavancas", []) if not a.get("acionada", False)) or
                            any(math.hypot(px - c["x"], py - c["y"]) <= 75 for c in grupo.get("chaves", []) if not c.get("coletada", False)) or
                            any(math.hypot(px - b["x"], py - (b["y"] + 12)) <= 75 for b in grupo.get("baus", []) if not b.get("aberto", False)) or
                            any(abs(px - g["rect"].centerx) < 65 and abs(py - g["rect"].centery) < g["rect"].height // 2 + 40 for g in grupo.get("portoes", []) if not g.get("aberto", False)) or
                            (mapa_idx == 6 and any(math.hypot(px - rx, py - ry) <= 95 and ri not in jogador.runas_ativadas for ri, (rx, ry) in enumerate(cenarios.POS_RUNAS_SALA7)))
                        )
                        if perto_interativo:
                            interagir_com_mapa()
                        else:
                            para_baixo_joy = False
                            joy_at = obter_controle_ativo()
                            if joy_at is not None:
                                try:
                                    if joy_at.get_numaxes() > 1 and joy_at.get_axis(1) > 0.45:
                                        para_baixo_joy = True
                                    elif joy_at.get_numhats() > 0 and joy_at.get_hat(0)[1] < 0:
                                        para_baixo_joy = True
                                except pygame.error:
                                    pass
                            keys_joy = pygame.key.get_pressed()
                            jogador.atacar(para_baixo=para_baixo_joy or bool(keys_joy[pygame.K_s] or keys_joy[pygame.K_DOWN]))
                    elif btn == 7:
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="", simulado_controle=True))
                    elif btn == 6:
                        alternar_tela_cheia()

                else:
                    # Nos menus / tela de morte / vitória / exposição / cutscene final:
                    # A (0) = Confirmar (K_RETURN) - evento único e limpo!
                    # B (1) = Voltar (K_ESCAPE)
                    # X (2) = Reiniciar ranque / nova jornada (K_r)
                    # Y (3) = Alternar exposição / mural demo (K_t)
                    # Back (6) = Alternar tela cheia (F11)
                    # Start (7) = Menu / Voltar (K_ESCAPE)
                    if btn == 0:
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", simulado_controle=True))
                    elif btn in (1, 7):
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="", simulado_controle=True))
                    elif btn == 2:
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, mod=0, unicode="", simulado_controle=True))
                    elif btn == 3:
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t, mod=0, unicode="", simulado_controle=True))
                    elif btn == 6:
                        alternar_tela_cheia()
                continue

            if event.type == pygame.JOYBUTTONUP:
                if event.button == 0 and modo_jogo == "MAPA":
                    jogador.cortar_pulo()
                continue

            # D-Pad (Hat) do controle de Xbox - envia apenas uma tecla direcional limpa
            if event.type == pygame.JOYHATMOTION:
                hx, hy = event.value
                if hx < 0:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, mod=0, unicode="", simulado_controle=True))
                elif hx > 0:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode="", simulado_controle=True))
                if hy > 0:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, mod=0, unicode="", simulado_controle=True))
                elif hy < 0:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode="", simulado_controle=True))
                continue

            # Analógico Esquerdo do controle para navegação nos menus (com debounce)
            if event.type == pygame.JOYAXISMOTION and (modo_jogo in ("MENU", "MORTE", "VITORIA", "EXPOSICAO_FIM", "CUTSCENE_FINAL") or (modo_jogo == "COMBATE" and getattr(combate, "estado", "") == "MENU_JOGADOR")):
                if event.axis == 1 and abs(event.value) > 0.65:
                    if tempo_mundo - timer_ultimo_analogico > 0.20:
                        timer_ultimo_analogico = tempo_mundo
                        tecla_ax = pygame.K_DOWN if event.value > 0 else pygame.K_UP
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla_ax, mod=0, unicode="", simulado_controle=True))
                elif event.axis == 0 and abs(event.value) > 0.65:
                    if tempo_mundo - timer_ultimo_analogico > 0.20:
                        timer_ultimo_analogico = tempo_mundo
                        tecla_ax = pygame.K_RIGHT if event.value > 0 else pygame.K_LEFT
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla_ax, mod=0, unicode="", simulado_controle=True))
                continue

            if event.type == pygame.QUIT:
                running = False
                continue

            if modo_jogo == "SPLASH_ESTUDIO":
                splash_estudio.handle_event(event)
                continue

            if modo_jogo == "MENU":
                acao = menu.handle_event(event)
                if acao is None:
                    pass
                elif acao[0] == "sair":
                    running = False
                elif acao[0] == "jogar":
                    modo_boss_rush = False
                    run_finalizada = False
                    metricas_sessao = {"dano": 0, "parries": 0, "qtes": 0}
                    ultimo_rank_resultado = None
                    if len(acao) > 1 and acao[1]:
                        progresso.trocar_perfil(acao[1])
                    if CONFIG.get("modo_exposicao_ativo", False):
                        inimigos_derrotados_sessao = 0
                        progresso.apagar(manter_tempo=False)
                        cenarios.regerar_salas_procedurais()
                        mapa_idx = 0
                        mapa_atual = DADOS_MAPAS[0]
                        salas_entidades = criar_entidades_das_salas(progresso)
                        jogador = _criar_jogador_inicial()
                    else:
                        jogador.max_hp = progresso.max_hp_total()

                    destino_sala = 0 if CONFIG.get("modo_exposicao_ativo", False) else progresso.ultima_sala
                    def _entrar_pos_intro():
                        entrar_na_sala(destino_sala)

                    # Inicia a cinemática de introdução imersiva ao começar na Sala 1
                    if destino_sala == 0 or CONFIG.get("modo_exposicao_ativo", False):
                        def _abrir_intro():
                            nonlocal modo_jogo, cutscene_intro
                            def _fim_intro():
                                transicao.iniciar("MAPA", estilo="fade", texto="ATO I — MURALHA CARMESIM", callback=_entrar_pos_intro)
                            cutscene_intro = CutsceneIntroducao(progresso.nome_heroi, _fim_intro)
                            modo_jogo = "INTRODUCAO"
                        transicao.iniciar("INTRODUCAO", estilo="fade", texto="O DESPERTAR DO VAZIO", callback=_abrir_intro)
                    else:
                        def _entrar_ultima():
                            entrar_na_sala(destino_sala)
                        transicao.iniciar("MAPA", estilo="pergaminho", texto=f"HERÓI: {progresso.nome_heroi.upper()}", callback=_entrar_ultima)
                elif acao[0] == "sala":
                    modo_boss_rush = False
                    run_finalizada = False
                    metricas_sessao = {"dano": 0, "parries": 0, "qtes": 0}
                    ultimo_rank_resultado = None
                    idx_sala = acao[1]
                    if len(acao) > 2 and acao[2]:
                        progresso.trocar_perfil(acao[2])
                    jogador.max_hp = progresso.max_hp_total()
                    def _entrar_sala(i=idx_sala):
                        entrar_na_sala(i)
                    transicao.iniciar("MAPA", estilo="pergaminho", texto=f"SALA {idx_sala + 1} — {progresso.nome_heroi.upper()}", callback=_entrar_sala)
                elif acao[0] == "boss_rush":
                    if len(acao) > 1 and acao[1]:
                        progresso.trocar_perfil(acao[1])
                    modo_boss_rush = True
                    run_finalizada = False
                    boss_rush_idx = 0
                    metricas_rush = {"dano": 0, "parries": 0, "qtes": 0, "tempo": 0.0}
                    ultimo_rank_resultado = None
                    progresso.tentativas = 3
                    progresso.salvar()
                    boss_alvo = salas_entidades[0]["boss"]
                    boss_alvo.hp = boss_alvo.max_hp
                    boss_alvo.vivo = True
                    boss_alvo.resetar_comportamento()
                    jogador.max_hp = progresso.max_hp_total()
                    jogador.hp = jogador.max_hp
                    def _iniciar_rush():
                        nonlocal combate, modo_jogo, mapa_idx
                        mapa_idx = 0
                        jogador.mapa_idx = 0
                        combate = CombateExpedition33(jogador, boss_alvo, vantagem="INIMIGO", sala_idx=0, modo_boss_rush=True, sala_atual=0)
                        combate.tempo_boss_rush_ativo = metricas_rush["tempo"]
                        combate._fim_processado = False
                        audio.tocar_musica("dungeon_theme")
                        modo_jogo = "COMBATE"
                    transicao.iniciar("COMBATE", estilo="portao", texto="BOSS RUSH (1/7) — O DESAFIO COMEÇA!", callback=_iniciar_rush)
                elif acao[0] == "bot":
                    BOT.ligar()
                    progresso.trocar_perfil("Bot_Guerreiro")
                    def _entrar_bot():
                        entrar_na_sala(progresso.ultima_sala)
                    transicao.iniciar("MAPA", estilo="pergaminho", texto="MODO BOT ATIVADO", callback=_entrar_bot)
                elif acao[0] == "reset_salas":
                    progresso.apagar()
                    cenarios.regerar_salas_procedurais()
                    salas_entidades = criar_entidades_das_salas(progresso)
                    jogador = _criar_jogador_inicial()
                    mapa_idx = 0
                    mapa_atual = DADOS_MAPAS[0]
                continue

            if modo_jogo == "EXPOSICAO_FIM":
                tela_fim_exposicao.timer_inatividade = 0.0
                if event.type == pygame.MOUSEMOTION:
                    for i, r in enumerate(getattr(tela_fim_exposicao, "rects_botoes", [])):
                        if r.collidepoint(event.pos):
                            tela_fim_exposicao.opcao_selecionada = i
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, r in enumerate(getattr(tela_fim_exposicao, "rects_botoes", [])):
                        if r.collidepoint(event.pos):
                            tela_fim_exposicao.opcao_selecionada = i
                            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))

            if modo_jogo == "MORTE":
                if event.type == pygame.MOUSEMOTION:
                    for i, r in enumerate(getattr(tela_morte, "rects_botoes", [])):
                        if r.collidepoint(event.pos):
                            tela_morte.opcao_selecionada = i
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, r in enumerate(getattr(tela_morte, "rects_botoes", [])):
                        if r.collidepoint(event.pos):
                            tela_morte.opcao_selecionada = i
                            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))

            elif modo_jogo == "VITORIA":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    painel_left = (LARGURA_TELA - 640) // 2
                    painel_top = (ALTURA_TELA - 320) // 2
                    r_btn_nova = pygame.Rect(painel_left + 236, painel_top + 126, 356, 48)
                    r_btn_menu = pygame.Rect(painel_left + 236, painel_top + 188, 356, 48)
                    if r_btn_nova.collidepoint(event.pos):
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, mod=0, unicode=""))
                    elif r_btn_menu.collidepoint(event.pos):
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))

            elif modo_jogo == "COMBATE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    combate.handle_mouse_click(event.pos)

            if event.type == pygame.KEYDOWN:
                if modo_jogo == "MAPA":
                    if event.key == pygame.K_ESCAPE:
                        progresso.registrar_vida(mapa_idx, jogador.hp)
                        progresso.salvar()
                        def _voltar_menu():
                            menu.abrir_principal()
                        transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_voltar_menu)
                    elif event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        jogador.solicitar_pulo()
                    elif event.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                        keys_dir = pygame.key.get_pressed()
                        dir_esq = None
                        if keys_dir[pygame.K_a] or keys_dir[pygame.K_LEFT]:
                            dir_esq = -1
                        elif keys_dir[pygame.K_d] or keys_dir[pygame.K_RIGHT]:
                            dir_esq = 1
                        jogador.iniciar_esquiva(direcao=dir_esq)
                    elif event.key == pygame.K_z:
                        keys_atk = pygame.key.get_pressed()
                        jogador.atacar(para_baixo=bool(keys_atk[pygame.K_s] or keys_atk[pygame.K_DOWN]))
                    elif event.key == pygame.K_e:
                        interagir_com_mapa()

                elif modo_jogo == "COMBATE":
                    combate.handle_keydown(event.key)

                elif modo_jogo == "MORTE":
                    if event.key in (pygame.K_ESCAPE, pygame.K_m):
                        modo_boss_rush = False
                        def _menu_morte_esc():
                            menu.abrir_principal()
                        transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_menu_morte_esc)
                    elif tela_morte.game_over_total:
                        # Em Game Over total: confirmação inicia novo ciclo preservando o tempo total contado
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            tela_morte.opcao_selecionada = 0
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            tela_morte.opcao_selecionada = 1
                        elif event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                            if event.key == pygame.K_r or tela_morte.opcao_selecionada == 0:
                                if modo_boss_rush:
                                    boss_rush_idx = 0
                                    metricas_rush = {"dano": 0, "parries": 0, "qtes": 0, "tempo": 0.0}
                                    run_finalizada = False
                                    boss_alvo = salas_entidades[0]["boss"]
                                    boss_alvo.hp = boss_alvo.max_hp
                                    boss_alvo.vivo = True
                                    boss_alvo.resetar_comportamento()
                                    jogador.hp = jogador.max_hp
                                    progresso.reviver_jogador()
                                    def _recomecar_rush():
                                        nonlocal combate, modo_jogo, mapa_idx
                                        mapa_idx = 0
                                        jogador.mapa_idx = 0
                                        combate = CombateExpedition33(jogador, boss_alvo, vantagem="INIMIGO", sala_idx=0, sala_atual=0, modo_boss_rush=True)
                                        combate.tempo_boss_rush_ativo = metricas_rush["tempo"]
                                        combate._fim_processado = False
                                        audio.tocar_musica("dungeon_theme")
                                        modo_jogo = "COMBATE"
                                    transicao.iniciar("COMBATE", estilo="portao", texto="RECOMEÇANDO BOSS RUSH (1/7)", callback=_recomecar_rush)
                                else:
                                    def _recomecar_novo_jogo():
                                        nonlocal salas_entidades, jogador, mapa_idx, run_finalizada
                                        run_finalizada = False
                                        progresso.apagar(manter_tempo=True)
                                        cenarios.regerar_salas_procedurais()
                                        salas_entidades = criar_entidades_das_salas(progresso)
                                        spawn_0 = DADOS_MAPAS[0].get("spawn_heroi", (100, 1084))
                                        jogador = JogadorMapa(spawn_0[0], spawn_0[1])
                                        jogador.progresso_ref = progresso
                                        jogador.max_hp = progresso.max_hp_total()
                                        jogador.hp = jogador.max_hp
                                        entrar_na_sala(0, hp=jogador.max_hp)
                                    transicao.iniciar("MAPA", estilo="pergaminho", texto="NOVA JORNADA — SALA 1", callback=_recomecar_novo_jogo)
                            else:
                                modo_boss_rush = False
                                def _menu_morte():
                                    menu.abrir_principal()
                                transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_menu_morte)
                    else:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            tela_morte.opcao_selecionada = 0
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            tela_morte.opcao_selecionada = 1
                        elif event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                            if event.key == pygame.K_r or tela_morte.opcao_selecionada == 0:
                                if modo_boss_rush:
                                    boss_alvo = salas_entidades[boss_rush_idx]["boss"]
                                    boss_alvo.hp = boss_alvo.max_hp
                                    boss_alvo.vivo = True
                                    boss_alvo.resetar_comportamento()
                                    jogador.hp = jogador.max_hp
                                    def _retry_rush():
                                        nonlocal combate, modo_jogo, mapa_idx
                                        mapa_idx = boss_rush_idx
                                        jogador.mapa_idx = boss_rush_idx
                                        combate = CombateExpedition33(jogador, boss_alvo, vantagem="INIMIGO", sala_idx=boss_rush_idx, modo_boss_rush=True, sala_atual=boss_rush_idx)
                                        combate.tempo_boss_rush_ativo = metricas_rush["tempo"]
                                        combate._fim_processado = False
                                        if boss_rush_idx in (1, 4, 5):
                                            audio.tocar_musica("forest_theme")
                                        else:
                                            audio.tocar_musica("dungeon_theme")
                                        modo_jogo = "COMBATE"
                                    transicao.iniciar("COMBATE", estilo="portao", texto=f"RETOMANDO BOSS RUSH ({boss_rush_idx + 1}/7)", callback=_retry_rush)
                                else:
                                    def _retry():
                                        nonlocal salas_entidades
                                        salas_entidades = criar_entidades_das_salas(progresso)
                                        entrar_na_sala(mapa_idx, hp=progresso.max_hp_total())
                                    transicao.iniciar("MAPA", estilo="pergaminho", texto="LEVANTE-SE, GUERREIRO", callback=_retry)
                            else:
                                modo_boss_rush = False
                                def _menu_morte():
                                    menu.abrir_principal()
                                transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_menu_morte)

                elif modo_jogo == "VITORIA":
                    if event.key == pygame.K_r:
                        def _reset():
                            nonlocal salas_entidades, jogador, run_finalizada
                            run_finalizada = False
                            progresso.apagar()
                            cenarios.regerar_salas_procedurais()
                            salas_entidades = criar_entidades_das_salas(progresso)
                            jogador = _criar_jogador_inicial()
                            entrar_na_sala(0)
                            menu.abrir_principal()
                        transicao.iniciar("MENU", estilo="selo", texto="NOVA JORNADA", callback=_reset)
                    elif event.key == pygame.K_ESCAPE:
                        def _menu_vit():
                            menu.abrir_principal()
                        transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_menu_vit)

                elif modo_jogo == "EXPOSICAO_FIM":
                    tela_fim_exposicao.timer_inatividade = 0.0
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        tela_fim_exposicao.opcao_selecionada = 0
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        tela_fim_exposicao.opcao_selecionada = 1
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r, pygame.K_z):
                        if tela_fim_exposicao.opcao_selecionada == 0 or event.key in (pygame.K_SPACE, pygame.K_r):
                            run_finalizada = False
                            inimigos_derrotados_sessao = 0
                            progresso.apagar(manter_tempo=False)
                            cenarios.regerar_salas_procedurais()
                            salas_entidades = criar_entidades_das_salas(progresso)
                            jogador = _criar_jogador_inicial()
                            def _recomecar_demo():
                                nonlocal modo_jogo
                                entrar_na_sala(0, hp=jogador.hp)
                                modo_jogo = "MAPA"
                            transicao.iniciar("MAPA", estilo="selo", texto="NOVA DEMONSTRAÇÃO", callback=_recomecar_demo)
                        else:
                            run_finalizada = False
                            inimigos_derrotados_sessao = 0
                            progresso.apagar(manter_tempo=False)
                            def _menu_demo():
                                nonlocal modo_jogo
                                menu.abrir_principal()
                                modo_jogo = "MENU"
                            transicao.iniciar("MENU", estilo="fade", texto="MENU PRINCIPAL", callback=_menu_demo)
                    elif event.key in (pygame.K_TAB, pygame.K_t):
                        run_finalizada = False
                        inimigos_derrotados_sessao = 0
                        progresso.apagar(manter_tempo=False)
                        def _ir_mural_demo():
                            nonlocal modo_jogo
                            menu.aba_ranque = "DEMO"
                            menu.estado = "RANQUE"
                            modo_jogo = "MENU"
                        transicao.iniciar("MENU", estilo="pergaminho", texto="RANQUE DEMO", callback=_ir_mural_demo)
                    elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                        run_finalizada = False
                        inimigos_derrotados_sessao = 0
                        progresso.apagar(manter_tempo=False)
                        def _menu_demo_esc():
                            nonlocal modo_jogo
                            menu.abrir_principal()
                            modo_jogo = "MENU"
                        transicao.iniciar("MENU", estilo="fade", texto="MENU PRINCIPAL", callback=_menu_demo_esc)

                elif modo_jogo == "CUTSCENE_PASSAGEM":
                    if mini_cutscene:
                        if hasattr(mini_cutscene, "handle_keydown"):
                            mini_cutscene.handle_keydown(event.key)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                            mini_cutscene.pular()

                elif modo_jogo == "CUTSCENE_FINAL":
                    if cutscene_final:
                        acao = cutscene_final.handle_keydown(event.key)
                        if acao == "REINICIAR":
                            def _reset_fim():
                                nonlocal salas_entidades, jogador, run_finalizada
                                run_finalizada = False
                                progresso.apagar()
                                cenarios.regerar_salas_procedurais()
                                salas_entidades = criar_entidades_das_salas(progresso)
                                jogador = _criar_jogador_inicial()
                                entrar_na_sala(0)
                                menu.abrir_principal()
                            transicao.iniciar("MENU", estilo="selo", texto="NOVO CICLO", callback=_reset_fim)
                        elif acao == "MENU":
                            def _menu_fim():
                                menu.abrir_principal()
                            transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_menu_fim)

                elif modo_jogo == "INTRODUCAO":
                    if cutscene_intro:
                        cutscene_intro.handle_keydown(event.key)

                elif modo_jogo == "BOSS_RUSH_TRANSICAO":
                    if boss_rush_trans and event.key in (pygame.K_SPACE, pygame.K_RETURN) and boss_rush_trans["timer"] < 2.4:
                        boss_rush_trans["timer"] = 0.0

            if event.type == pygame.KEYUP:
                if modo_jogo == "MAPA":
                    if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        jogador.cortar_pulo()

        if modo_jogo == "SPLASH_ESTUDIO":
            splash_estudio.update(dt)
            if splash_estudio.concluida:
                modo_jogo = "MENU"
                abertura_menu_fade = 1.0

        elif modo_jogo == "MENU":
            audio.tocar_musica("title_theme")
            menu.update(dt)
            if abertura_menu_fade > 0.0:
                abertura_menu_fade = max(0.0, abertura_menu_fade - dt / 0.42)

        elif modo_jogo == "CONFIG_UI":
            configurador_ui_global.update(dt)
            # Vitrine Automática (Attract Mode de Exposição): após 30s de inatividade no menu
            timer_inatividade_menu += dt
            if timer_inatividade_menu >= 30.0 and not transicao.bloqueando and menu.estado == "PRINCIPAL":
                timer_inatividade_menu = 0.0
                BOT.ligar(vitrine=True)
                progresso.trocar_perfil("Vitrine_Demo")
                def _iniciar_vitrine():
                    entrar_na_sala(0, x=100.0, hp=jogador.max_hp)
                transicao.iniciar("MAPA", estilo="pergaminho", texto="MODO VITRINE — TOQUE PARA JOGAR", callback=_iniciar_vitrine)

        elif modo_jogo == "MAPA":
            if not BOT.ativo:
                timer_inatividade_jogo += dt
                if timer_inatividade_jogo >= 75.0 and not transicao.bloqueando:
                    timer_inatividade_jogo = 0.0
                    def _retorno_abandono_mapa():
                        menu.abrir_principal()
                    transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO MENU", callback=_retorno_abandono_mapa)
            mapa_atual = DADOS_MAPAS[mapa_idx]
            cenarios.atualizar_salas(mapa_idx, dt, tempo_mundo)
            jogador.mapa_idx = mapa_idx
            grupo_sala = salas_entidades[mapa_idx]
            todos_inimigos_sala = grupo_sala["inimigos"] + [grupo_sala["boss"]]
            if BOT.ativo:
                BOT.atualizar_mapa(dt, jogador, mapa_atual, todos_inimigos_sala, mapa_idx=mapa_idx)
            jogador.update(dt, mapa_atual, grupo_sala, controle_ativo=obter_controle_ativo(), bot=BOT)
            vagalumes.update(dt)
            # As armadilhas causam dano com intervalo de segurança e empurram o jogador para trás.
            if jogador.tempo_imune_armadilha <= 0:
                for area_perigosa, tipo_perigo in mapa_atual.get("armadilhas", []):
                    if jogador.rect.colliderect(area_perigosa):
                        audio.tocar_sfx("spikes", 0.85)
                        audio.tocar_sfx("hit_player", 0.70)
                        jogador.hp = max(1, jogador.hp - 18)
                        jogador.tempo_imune_armadilha = 1.15
                        jogador.flash_armadilha = 0.28
                        jogador.x = max(0.0, jogador.x - (42 if jogador.olhando_direita else -42))
                        jogador.vy = -300.0
                        jogador.no_chao = False
                        jogador.rect.x = int(jogador.x)
                        jogador.rect.y = int(jogador.y)
                        camera.tremer(intensidade=6.0, duracao=0.2)
                        break

            larg_m = float(mapa_atual.get("largura", LARGURA_MUNDO))
            alt_m = float(mapa_atual.get("altura", ALTURA_MUNDO))
            look_dir = 1.0 if getattr(jogador, "olhando_direita", True) else -1.0
            camera.update(jogador.x + jogador.largura / 2.0, jogador.y + jogador.altura / 2.0, dt, larg_m, alt_m, look_dir=look_dir)
            progresso.registrar_vida(mapa_idx, jogador.hp)

            for inim in todos_inimigos_sala:
                inim.update(dt, jogador)
            jogador.atualizar_invocacoes(dt, todos_inimigos_sala)

            # Coleta automática ao encostar em Chaves Rúnicas + sintonização de Relíquias via golpe de espada
            for chave in grupo_sala.get("chaves", []):
                if not chave.get("coletada", False):
                    r_ch = pygame.Rect(int(chave["x"] - 18), int(chave["y"] - 28), 36, 36)
                    if jogador.rect.colliderect(r_ch):
                        _coletar_chave(chave, grupo_sala, origem="toque")

            if mapa_idx == 6 and jogador.atacando and jogador.hitbox_ataque:
                for ri, (rx, ry) in enumerate(cenarios.POS_RUNAS_SALA7):
                    if ri not in jogador.runas_ativadas:
                        r_altar = pygame.Rect(int(rx - 28), int(ry - 68), 56, 72)
                        if jogador.hitbox_ataque.colliderect(r_altar):
                            _ativar_rel_sala7(ri, grupo_sala)

            boss_atual = grupo_sala["boss"]

            portal_pos = mapa_atual.get("portal_saida", (larg_m - 140, 960))
            perto_portal = (math.hypot(jogador.x + jogador.largura / 2 - portal_pos[0],
                                       jogador.y + jogador.altura / 2 - portal_pos[1]) < 85)
            chegou_fim = (jogador.rect.right >= larg_m - 30) or perto_portal

            if chegou_fim:
                if boss_atual.vivo:
                    jogador.x = min(jogador.x, float(larg_m - jogador.largura - 40))
                    jogador.rect.x = int(jogador.x)
                else:
                    jogador.x = float(larg_m - jogador.largura - 45)
                    jogador.rect.x = int(jogador.x)
                    limite_salas = int(CONFIG.get("exposicao_sala_limite", 5))
                    if CONFIG.get("modo_exposicao_ativo", False) and (mapa_idx + 1) >= limite_salas:
                        progresso.marcar_chefe(mapa_idx)
                        rk_sala = ranking.calcular_rank_desempenho(
                            dano_recebido=metricas_sessao["dano"],
                            tempo_segundos=progresso.tempo_decorrido,
                            tempo_meta=max(60.0, float(CONFIG.get("exposicao_tempo_limite_segundos", 300)) * 0.75),
                            qtes_perfeitos=metricas_sessao["qtes"],
                            parries_perfeitos=metricas_sessao["parries"],
                            venceu=True,
                        )
                        progresso.registrar_rank_sala(mapa_idx, rk_sala["rank"], rk_sala["pontuacao"], sem_avaria=rk_sala["sem_avaria"])
                        progresso.consolidar_tempo_sala()
                        progresso.salvar()
                        if not run_finalizada:
                            run_finalizada = True
                            ultimo_rank_resultado = rk_sala
                            RANKING_GLOBAL.adicionar_registro(
                                nome=progresso.nome_heroi,
                                tempo=progresso.tempo_decorrido,
                                tentativas=progresso.tentativas_gastas,
                                passou=True,
                                sala=mapa_idx + 1,
                                modo="DEMO",
                                rank=rk_sala["rank"],
                                pontuacao=rk_sala["pontuacao"],
                                dano_recebido=metricas_sessao["dano"],
                                parries_perfeitos=metricas_sessao["parries"],
                                qtes_perfeitos=metricas_sessao["qtes"],
                            )
                            caminhos.log_info(f"DEMO VENCIDA! Herói '{progresso.nome_heroi}' gravado no Ranking Demo ({progresso.tempo_decorrido:.1f}s, Sala {mapa_idx + 1}, Rank {rk_sala['rank']}).")
                        def _ir_fim_meta():
                            nonlocal modo_jogo
                            tela_fim_exposicao.configurar(
                                motivo="META_ATINGIDA",
                                progresso=progresso,
                                mapa_idx=mapa_idx,
                                inimigos_derrotados=inimigos_derrotados_sessao,
                                resumo_rank=ultimo_rank_resultado,
                            )
                            modo_jogo = "EXPOSICAO_FIM"
                        transicao.iniciar("EXPOSICAO_FIM", estilo="selo", texto="DEMONSTRAÇÃO CONCLUÍDA!", callback=_ir_fim_meta)
                    else:
                        proxima_sala = mapa_idx + 1
                        if proxima_sala < len(DADOS_MAPAS) and (proxima_sala in DADOS_MAPAS):
                            rk_sala = ranking.calcular_rank_desempenho(
                                dano_recebido=metricas_sessao["dano"],
                                tempo_segundos=max(1.0, progresso.tempo_sala_atual),
                                tempo_meta=70.0,
                                qtes_perfeitos=metricas_sessao["qtes"],
                                parries_perfeitos=metricas_sessao["parries"],
                                venceu=True,
                            )
                            progresso.registrar_rank_sala(mapa_idx, rk_sala["rank"], rk_sala["pontuacao"], sem_avaria=rk_sala["sem_avaria"])
                            progresso.consolidar_tempo_sala()
                            destino = proxima_sala
                            def _prox(s=destino):
                                nonlocal modo_jogo, mapa_idx
                                mapa_idx = s
                                progresso.ultima_sala = s
                                entrar_na_sala(s, hp=jogador.hp)
                                progresso.salvar()
                                modo_jogo = "MAPA"
                            mini_cutscene = MiniCutscenePassagemSala(mapa_idx, destino, jogador.hp, _prox)
                            modo_jogo = "CUTSCENE_PASSAGEM"
                        else:
                            # Atingiu além da última sala do jogo (vitória na campanha)
                            progresso.consolidar_tempo_sala()
                            rk_final = ranking.calcular_rank_desempenho(
                                dano_recebido=metricas_sessao["dano"],
                                tempo_segundos=progresso.tempo_decorrido,
                                tempo_meta=float(len(DADOS_MAPAS)) * 55.0,
                                qtes_perfeitos=metricas_sessao["qtes"],
                                parries_perfeitos=metricas_sessao["parries"],
                                venceu=True,
                            )
                            ultimo_rank_resultado = rk_final
                            progresso.registrar_rank_sala(mapa_idx, rk_final["rank"], rk_final["pontuacao"], sem_avaria=rk_final["sem_avaria"])
                            progresso.salvar()
                            if not run_finalizada:
                                run_finalizada = True
                                RANKING_GLOBAL.adicionar_registro(
                                    nome=progresso.nome_heroi,
                                    tempo=progresso.tempo_decorrido,
                                    tentativas=progresso.tentativas_gastas,
                                    passou=True,
                                    sala=len(DADOS_MAPAS),
                                    modo="CAMPANHA",
                                    rank=rk_final["rank"],
                                    pontuacao=rk_final["pontuacao"],
                                    dano_recebido=metricas_sessao["dano"],
                                    parries_perfeitos=metricas_sessao["parries"],
                                    qtes_perfeitos=metricas_sessao["qtes"],
                                )
                                caminhos.log_info(f"VITÓRIA FINAL CONQUISTADA! Herói '{progresso.nome_heroi}' gravado no Ranking ({progresso.tempo_decorrido:.1f}s, {progresso.tentativas_gastas} tentativas, Rank {rk_final['rank']}).")
                            def _fim_jogo_saida():
                                nonlocal modo_jogo
                                menu.abrir_principal()
                                modo_jogo = "MENU"
                            cutscene_final = CutsceneFinalJogo(
                                _fim_jogo_saida,
                                resumo_rank=ultimo_rank_resultado,
                                tempo_total=progresso.tempo_decorrido,
                                nome_heroi=progresso.nome_heroi,
                            )
                            transicao.iniciar("CUTSCENE_FINAL", estilo="selo", texto="O COLAPSO DO VAZIO")

            elif jogador.rect.left <= 0:
                if mapa_idx > 0 and (mapa_idx - 1) in DADOS_MAPAS:
                    ant = mapa_idx - 1
                    def _ant(s=ant):
                        larg_ant = DADOS_MAPAS[s].get("largura", LARGURA_MUNDO)
                        entrar_na_sala(s, x=float(larg_ant - jogador.largura - 60), hp=jogador.hp)
                        progresso.salvar()
                    transicao.iniciar("MAPA", estilo="pergaminho", texto=f"SALA {ant + 1}", callback=_ant)
                else:
                    jogador.x = 0.0

            if modo_jogo == "MAPA":
                def _iniciar_encontro(alvo_inim, vantagem="JOGADOR", aviso_extra=None):
                    nonlocal combate, inimigo_em_luta
                    inimigo_em_luta = alvo_inim
                    if alvo_inim.is_boss:
                        equipe = [alvo_inim]
                    else:
                        equipe = [
                            alvo for alvo in todos_inimigos_sala
                            if alvo.vivo and not alvo.is_boss
                            and abs(alvo.x - alvo_inim.x) <= 240
                            and abs(alvo.y - alvo_inim.y) <= 110
                        ]
                        equipe = sorted(equipe, key=lambda alvo: abs(alvo.x - alvo_inim.x))[:3]
                        if alvo_inim not in equipe:
                            equipe.insert(0, alvo_inim)
                    if alvo_inim.is_boss and mapa_idx == 6 and len(getattr(jogador, "runas_ativadas", set())) >= 3:
                        vantagem_efetiva = "JOGADOR"
                    else:
                        vantagem_efetiva = vantagem
                    combate = CombateExpedition33(
                        jogador, alvo_inim, vantagem=vantagem_efetiva,
                        sala_idx=mapa_idx, alvos_disponiveis=equipe, sala_atual=mapa_idx
                    )
                    if aviso_extra:
                        combate.banner_msg = aviso_extra
                    elif len(equipe) > 1:
                        tag_mira = ui_medieval.tag_comando("alvos")
                        pref = "EMBOSCADA!" if vantagem_efetiva == "JOGADOR" else "GRUPO INIMIGO!"
                        combate.banner_msg = f"{pref} {len(equipe)} INIMIGOS {tag_mira} PARA TROCAR ALVO"
                    if alvo_inim.is_boss:
                        txt_b = "ESCUDO QUEBRADO — VOCÊ ATACA PRIMEIRO!" if (mapa_idx == 6 and len(getattr(jogador, "runas_ativadas", set())) >= 3) else "O CHEFE ATACA PRIMEIRO!"
                        transicao.iniciar("COMBATE", estilo="portao", texto=txt_b)
                    else:
                        txt_trans = "O COMBATE COMEÇA" if vantagem_efetiva == "JOGADOR" else "EMBOSCADA!"
                        transicao.iniciar("COMBATE", estilo="portao", texto=txt_trans)

                for inim in todos_inimigos_sala:
                    if not inim.vivo:
                        continue

                    if jogador.atacando_baixo and jogador.hitbox_pogo:
                        if jogador.hitbox_pogo.colliderect(inim.rect):
                            jogador.executar_pogo_bounce()
                            if not transicao.ativa:
                                if getattr(inim, "vulneravel_contra_ataque", False) and inim.hp > 1:
                                    dano_pogo = inim.sofrer_contra_ataque(16)
                                    inim.hp = max(1, inim.hp)
                                    inim.vivo = True
                                    adicionar_notificacao(f"Pogo em RECUPERAÇÃO! (-{dano_pogo})", cor=(110, 255, 220))
                                _iniciar_encontro(inim, vantagem="JOGADOR", aviso_extra="POGO BOUNCE! VANTAGEM DE COMBATE!")
                                break
                        elif any(jogador.hitbox_pogo.colliderect(hb["rect"]) for hb in getattr(inim, "hitboxes_ataque", []) if hb.get("ignora_esquiva_chao")):
                            jogador.executar_pogo_bounce()
                            inim.acertou_jogador_neste_ataque = True
                            adicionar_notificacao("Pogo Bounce sobre a onda sísmica!", cor=(120, 255, 220))

                    if jogador.atacando and jogador.hitbox_ataque and jogador.hitbox_ataque.colliderect(inim.rect):
                        if transicao.ativa:
                            break
                        if getattr(inim, "vulneravel_contra_ataque", False) and inim.hp > 1:
                            dano_p = inim.sofrer_contra_ataque(20)
                            inim.hp = max(1, min(inim.max_hp, inim.hp))
                            inim.vivo = True
                            adicionar_notificacao(f"Contra-ataque em RECUPERAÇÃO! (-{dano_p})", cor=(110, 255, 210))
                        _iniciar_encontro(inim, vantagem="JOGADOR")
                        break

                    res_atk = inim.verificar_colisao_ataque(jogador)
                    if res_atk is not None:
                        if res_atk.get("atingido"):
                            camera.tremer(intensidade=6.0, duracao=0.22)
                            adicionar_notificacao(
                                f"{inim.nome}: {res_atk.get('motivo', 'GOLPE')} (-{res_atk.get('dano', 0)} HP)",
                                cor=(255, 110, 95)
                            )
                            if jogador.hp <= 0:
                                jogador.hp = 1
                                if not transicao.ativa:
                                    _iniciar_encontro(inim, vantagem="INIMIGO")
                                    break
                        elif res_atk.get("contra_aberta"):
                            inim.vulneravel_contra_ataque = True
                            adicionar_notificacao(f"{res_atk.get('motivo', 'ESQUIVA')}! JANELA ABERTA!", cor=(120, 245, 255))

                    elif not jogador.esta_invencivel and not transicao.ativa and jogador.obter_hurtbox().colliderect(inim.rect):
                        _iniciar_encontro(inim, vantagem="INIMIGO")
                        break

        elif modo_jogo == "COMBATE":
            if not BOT.ativo:
                timer_inatividade_jogo += dt
                if timer_inatividade_jogo >= 75.0 and not transicao.bloqueando:
                    timer_inatividade_jogo = 0.0
                    def _retorno_abandono_combate():
                        menu.abrir_principal()
                    transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO MENU", callback=_retorno_abandono_combate)
            if BOT.ativo and combate:
                BOT.atualizar_combate(dt, combate)
            combate.update(dt)
            inimigo_em_luta = combate.inimigo_ref

            if transicao.bloqueando or getattr(combate, "_fim_processado", False):
                pass

            elif combate.fim_concluido and getattr(combate, "fugiu", False):
                combate._fim_processado = True
                jogador.hp = combate.jogador_hp
                jogador.vy = 0.0
                if inimigo_em_luta:
                    delta_fuga = -85.0 if jogador.x < inimigo_em_luta.x else 85.0
                    cand_x = max(50.0, min(float(mapa_atual.get("largura", LARGURA_MUNDO) - 80), jogador.x + delta_fuga))
                    grupo_fuga = salas_entidades[mapa_idx]
                    bloq_fuga = [g["rect"] for g in grupo_fuga.get("portoes", []) if not g.get("aberto", False)] + list(mapa_atual.get("paredes", []))
                    cand_rect = pygame.Rect(int(cand_x), int(jogador.y) + 2, jogador.largura, max(4, jogador.altura - 4))
                    if not any(cand_rect.colliderect(br) for br in bloq_fuga):
                        jogador.x = cand_x
                    jogador.rect.x = int(jogador.x)
                jogador.tempo_imune_armadilha = 2.0
                progresso.registrar_vida(mapa_idx, jogador.hp)
                progresso.salvar()
                if mapa_idx in (1, 4, 5):
                    audio.tocar_musica("forest_theme")
                else:
                    audio.tocar_musica("dungeon_theme")
                transicao.iniciar("MAPA", estilo="pergaminho", texto="FUGA DA BATALHA")

            elif combate.fim_concluido and (getattr(combate, "estado", "") in ("VITORIA", "FIM_VITORIA") or (combate.jogador_hp > 0 and combate.todos_inimigos_mortos())):
                # O alvo atual em combate caiu!
                alvo_derrotado = getattr(combate, "inimigo_ref", inimigo_em_luta)
                alvo_derrotado.hp = 0
                alvo_derrotado.vivo = False
                inimigos_derrotados_sessao += 1

                # Se o alvo derrotado era o Chefe, quaisquer lacaios invocados perecem imediatamente com seu mestre
                if getattr(alvo_derrotado, "is_boss", False):
                    for a_extra in combate.alvos_disponiveis:
                        if a_extra is not alvo_derrotado:
                            a_extra.hp = 0
                            a_extra.vivo = False

                # Verifica se ainda restam outros inimigos vivos neste confronto (ex: Chefe ainda vivo após queda do esqueleto)
                if combate.continuar_luta_em_equipe():
                    combate._fim_processado = False
                    jogador.hp = max(1, combate.jogador_hp)
                    jogador.vy = 0.0
                    jogador.no_chao = True
                    jogador.vivo = True
                    if hasattr(jogador, "anim") and jogador.anim:
                        jogador.anim.tocar("idle", loop=True, forcar=True)
                    xp_ganho = (180 + mapa_idx * 50) if getattr(alvo_derrotado, "is_boss", False) else (35 + mapa_idx * 15)
                    caminhos.log_info(f"Lacaio derrotado em combate: '{alvo_derrotado.nome}'. +{xp_ganho} XP concedidos.")
                    subiu, novo_nv, n_ganhos = progresso.ganhar_xp(xp_ganho)
                    if subiu:
                        audio.tocar_sfx("level_up", 1.0)
                        jogador.max_hp = progresso.max_hp_total()
                        combate.jogador_max_hp = jogador.max_hp
                        combate.jogador_hp = min(jogador.max_hp, combate.jogador_hp + n_ganhos * 15)
                        combate.qtd_pocao += n_ganhos
                        combate.qtd_cristal_ap += n_ganhos
                        combate.adicionar_texto_flutuante(f"NÍVEL SUBIU! NV {novo_nv}!", 180, 110, (255, 230, 80))
                    else:
                        audio.tocar_sfx("xp_gain", 0.85)
                        combate.adicionar_texto_flutuante(f"+{xp_ganho} XP!", 180, 110, (140, 240, 255))
                    jogador.hp = min(jogador.max_hp, jogador.hp + 20)
                    combate.jogador_hp = jogador.hp
                    progresso.registrar_vida(mapa_idx, jogador.hp)
                    progresso.salvar()
                else:
                    # Todos os inimigos do confronto foram eliminados!
                    combate._fim_processado = True
                    inimigo_em_luta.hp = 0
                    inimigo_em_luta.vivo = False
                    for par in getattr(combate, "combatentes_inimigos", []):
                        par[0].hp = 0
                        par[0].vivo = False
                    for a_extra in combate.alvos_disponiveis:
                        a_extra.hp = 0
                        a_extra.vivo = False
                    era_boss = (getattr(inimigo_em_luta, "is_boss", False) or
                                getattr(alvo_derrotado, "is_boss", False) or
                                any(getattr(a, "is_boss", False) for a in combate.alvos_disponiveis))

                    # Sistema de Nível — Ganho de XP ao derrotar inimigo ou chefe
                    xp_ganho = (180 + mapa_idx * 50) if era_boss else (35 + mapa_idx * 15)
                    caminhos.log_info(f"Inimigo derrotado com sucesso: '{inimigo_em_luta.nome}' (Chefe: {era_boss}, Sala {mapa_idx + 1}). +{xp_ganho} XP concedidos.")
                    subiu, novo_nv, n_ganhos = progresso.ganhar_xp(xp_ganho)
                    if subiu:
                        audio.tocar_sfx("level_up", 1.0)
                        caminhos.log_info(f"Nível do jogador aumentou! Nível {novo_nv} (+{n_ganhos*15} HP Máx, +{n_ganhos*2} Dano, +{n_ganhos} Poções, +{n_ganhos} Éter).")
                        jogador.max_hp = progresso.max_hp_total()
                        combate.jogador_max_hp = jogador.max_hp
                        combate.jogador_hp = min(jogador.max_hp, combate.jogador_hp + n_ganhos * 15)
                        combate.qtd_pocao += n_ganhos
                        combate.qtd_cristal_ap += n_ganhos
                        combate.adicionar_texto_flutuante(f"NÍVEL SUBIU! NV {novo_nv} (+{n_ganhos*15} HP, +{n_ganhos*2} DANO, +{n_ganhos} POÇÃO, +{n_ganhos} ÉTER)!", 180, 110, (255, 230, 80))
                        for s_dados in salas_entidades.values():
                            for inim_rest in s_dados.get("inimigos", []):
                                if inim_rest.vivo:
                                    novo_hp_inim = progresso.escalar_hp_inimigo(getattr(inim_rest, "_hp_base", inim_rest.max_hp))
                                    diff = novo_hp_inim - inim_rest.max_hp
                                    if diff > 0:
                                        inim_rest.max_hp = novo_hp_inim
                                        inim_rest.hp = max(1, inim_rest.hp + diff)
                            boss_rest = s_dados.get("boss")
                            if boss_rest and boss_rest.vivo:
                                novo_hp_b = progresso.escalar_hp_inimigo(getattr(boss_rest, "_hp_base", boss_rest.max_hp))
                                diff_b = novo_hp_b - boss_rest.max_hp
                                if diff_b > 0:
                                    boss_rest.max_hp = novo_hp_b
                                    boss_rest.hp = max(1, boss_rest.hp + diff_b)
                    else:
                        audio.tocar_sfx("xp_gain", 0.85)
                        combate.adicionar_texto_flutuante(f"+{xp_ganho} XP (XP: {progresso.xp}/{progresso.xp_proximo})", 180, 110, (140, 240, 255))

                    cura_pos_luta = 0 if modo_boss_rush else (60 if era_boss else 25)
                    hp_base_vit = max(1, int(combate.jogador_hp))
                    jogador.hp = min(jogador.max_hp, hp_base_vit + cura_pos_luta)
                    progresso.registrar_vida(mapa_idx, jogador.hp)
                    if modo_boss_rush:
                        metricas_rush["dano"] += getattr(combate, "dano_recebido_combate", 0)
                        metricas_rush["qtes"] += getattr(combate, "qtes_perfeitos", 0)
                        metricas_rush["parries"] += getattr(combate, "parries_perfeitos", 0)
                    else:
                        metricas_sessao["dano"] += getattr(combate, "dano_recebido_combate", 0)
                        metricas_sessao["qtes"] += getattr(combate, "qtes_perfeitos", 0)
                        metricas_sessao["parries"] += getattr(combate, "parries_perfeitos", 0)

                    if era_boss:
                        progresso.marcar_chefe(mapa_idx)
                    progresso.salvar()

                    if modo_boss_rush:
                        jogador.vy = 0.0
                        jogador.vx = 0.0
                        jogador.no_chao = True
                        jogador.vivo = True
                        jogador.atacando = False
                        jogador.hitbox_ataque = None
                        if hasattr(jogador, "anim") and jogador.anim:
                            jogador.anim.tocar("idle", loop=True, forcar=True)
                        audio.tocar_sfx("boss_hit", 1.0)
                        if boss_rush_idx < 6:
                            boss_rush_idx += 1
                            prox_boss = salas_entidades[boss_rush_idx]["boss"]
                            prox_boss.hp = prox_boss.max_hp
                            prox_boss.vivo = True
                            prox_boss.resetar_comportamento()
                            boss_nome_limpo = prox_boss.nome.replace("BOSS: ", "").replace("CHEFE: ", "").replace("CHEFE FINAL: ", "").strip()
                            progresso.registrar_vida(boss_rush_idx, jogador.hp)
                            progresso.salvar()
                            caminhos.log_info(f"BOSS RUSH: Chefe {boss_rush_idx}/7 derrotado! Próximo: '{boss_nome_limpo}'.")
                            boss_rush_trans = {
                                "idx": boss_rush_idx,
                                "boss": prox_boss,
                                "nome": boss_nome_limpo,
                                "timer": 3.0,
                                "hp": jogador.hp,
                                "ap": int(getattr(combate, "jogador_ap", CONFIG["jogador_ap_inicial"])),
                                "pocao": int(getattr(combate, "qtd_pocao", 1)),
                                "eter": int(getattr(combate, "qtd_cristal_ap", 1)),
                            }
                            modo_jogo = "BOSS_RUSH_TRANSICAO"
                        else:
                            # Derrotou todos os 7 chefes do Boss Rush com glória absoluta!
                            modo_boss_rush = False
                            jogador.vy = 0.0
                            jogador.vx = 0.0
                            jogador.no_chao = True
                            jogador.vivo = True
                            if hasattr(jogador, "anim") and jogador.anim:
                                jogador.anim.tocar("idle", loop=True, forcar=True)
                            audio.tocar_musica("safe_room_theme")
                            if not run_finalizada:
                                run_finalizada = True
                                rk_rush = ranking.calcular_rank_desempenho(
                                    dano_recebido=metricas_rush["dano"],
                                    tempo_segundos=metricas_rush["tempo"],
                                    tempo_meta=240.0,
                                    qtes_perfeitos=metricas_rush["qtes"],
                                    parries_perfeitos=metricas_rush["parries"],
                                    venceu=True,
                                )
                                ultimo_rank_resultado = rk_rush
                                progresso.registrar_rank_sala("boss_rush", rk_rush["rank"], rk_rush["pontuacao"], sem_avaria=rk_rush["sem_avaria"])
                                progresso.salvar()
                                RANKING_GLOBAL.adicionar_registro(
                                    nome=progresso.nome_heroi,
                                    tempo=metricas_rush["tempo"],
                                    tentativas=progresso.tentativas_gastas,
                                    passou=True,
                                    sala=7,
                                    modo="BOSS_RUSH",
                                    rank=rk_rush["rank"],
                                    pontuacao=rk_rush["pontuacao"],
                                    dano_recebido=metricas_rush["dano"],
                                    parries_perfeitos=metricas_rush["parries"],
                                    qtes_perfeitos=metricas_rush["qtes"],
                                )
                                caminhos.log_info(f"★ VITÓRIA NO BOSS RUSH! Herói '{progresso.nome_heroi}' gravado no Ranking ({metricas_rush['tempo']:.1f}s, {progresso.tentativas_gastas} tentativas, Rank {rk_rush['rank']}).")
                            def _fim_rush():
                                nonlocal modo_jogo
                                menu.abrir_principal()
                                modo_jogo = "MENU"
                            cutscene_final = CutsceneFinalJogo(
                                _fim_rush,
                                resumo_rank=ultimo_rank_resultado,
                                tempo_total=metricas_rush["tempo"],
                                nome_heroi=progresso.nome_heroi,
                            )
                            transicao.iniciar("CUTSCENE_FINAL", estilo="selo", texto="★ CAMPEÃO SUPREMO DO BOSS RUSH ★")

                    elif mapa_idx == max(DADOS_MAPAS) and era_boss:
                        jogador.vy = 0.0
                        jogador.vx = 0.0
                        jogador.no_chao = True
                        jogador.vivo = True
                        if hasattr(jogador, "anim") and jogador.anim:
                            jogador.anim.tocar("idle", loop=True, forcar=True)
                        audio.tocar_musica("safe_room_theme")
                        progresso.consolidar_tempo_sala()
                        rk_camp = ranking.calcular_rank_desempenho(
                            dano_recebido=metricas_sessao["dano"],
                            tempo_segundos=progresso.tempo_decorrido,
                            tempo_meta=float(len(DADOS_MAPAS)) * 55.0,
                            qtes_perfeitos=metricas_sessao["qtes"],
                            parries_perfeitos=metricas_sessao["parries"],
                            venceu=True,
                        )
                        ultimo_rank_resultado = rk_camp
                        progresso.registrar_rank_sala(mapa_idx, rk_camp["rank"], rk_camp["pontuacao"], sem_avaria=rk_camp["sem_avaria"])
                        progresso.salvar()
                        if not run_finalizada:
                            run_finalizada = True
                            RANKING_GLOBAL.adicionar_registro(
                                nome=progresso.nome_heroi,
                                tempo=progresso.tempo_decorrido,
                                tentativas=progresso.tentativas_gastas,
                                passou=True,
                                sala=7,
                                modo="CAMPANHA",
                                rank=rk_camp["rank"],
                                pontuacao=rk_camp["pontuacao"],
                                dano_recebido=metricas_sessao["dano"],
                                parries_perfeitos=metricas_sessao["parries"],
                                qtes_perfeitos=metricas_sessao["qtes"],
                            )
                            caminhos.log_info(f"VITÓRIA FINAL CONQUISTADA! Herói '{progresso.nome_heroi}' gravado no Ranking ({progresso.tempo_decorrido:.1f}s, {progresso.tentativas_gastas} tentativas, Rank {rk_camp['rank']}).")
                        def _fim_pos_boss():
                            nonlocal modo_jogo
                            menu.abrir_principal()
                            modo_jogo = "MENU"
                        cutscene_final = CutsceneFinalJogo(
                            _fim_pos_boss,
                            resumo_rank=ultimo_rank_resultado,
                            tempo_total=progresso.tempo_decorrido,
                            nome_heroi=progresso.nome_heroi,
                        )
                        transicao.iniciar("CUTSCENE_FINAL", estilo="selo", texto="O COLAPSO DO VAZIO")
                    else:
                        jogador.vx = 0.0
                        jogador.vy = 0.0
                        jogador.atacando = False
                        jogador.hitbox_ataque = None
                        jogador.tempo_imune_armadilha = 1.0
                        jogador.no_chao = True
                        jogador.vivo = True
                        jogador.rect.x = int(jogador.x)
                        jogador.rect.y = int(jogador.y)
                        if hasattr(jogador, "anim") and jogador.anim:
                            jogador.anim.tocar("idle", loop=True, forcar=True)
                        if mapa_idx in (1, 4, 5):
                            audio.tocar_musica("forest_theme")
                        else:
                            audio.tocar_musica("dungeon_theme")
                        transicao.iniciar("MAPA", estilo="pergaminho", texto="A JORNADA CONTINUA")

            elif combate.fim_concluido and combate.jogador_hp <= 0:
                combate._fim_processado = True
                jogador.hp = 0
                audio.parar_musica(fade_ms=1000)
                game_over_total, tent_restantes = progresso.perder_tentativa()

                if modo_boss_rush:
                    metricas_rush["dano"] += getattr(combate, "dano_recebido_combate", 0)
                    boss_atual_nome = salas_entidades[boss_rush_idx]["boss"].nome.replace("BOSS: ", "").replace("CHEFE: ", "").replace("CHEFE FINAL: ", "")
                    if game_over_total and progresso.tentativas <= 0:
                        if not run_finalizada:
                            run_finalizada = True
                            rk_br_lose = ranking.calcular_rank_desempenho(
                                dano_recebido=metricas_rush["dano"] + 90,
                                tempo_segundos=metricas_rush["tempo"],
                                tempo_meta=240.0,
                                qtes_perfeitos=metricas_rush["qtes"],
                                parries_perfeitos=metricas_rush["parries"],
                                venceu=False,
                            )
                            RANKING_GLOBAL.adicionar_registro(
                                nome=progresso.nome_heroi,
                                tempo=metricas_rush["tempo"],
                                tentativas=progresso.tentativas_gastas,
                                passou=False,
                                sala=boss_rush_idx + 1,
                                modo="BOSS_RUSH",
                                rank=rk_br_lose["rank"],
                                pontuacao=rk_br_lose["pontuacao"],
                                dano_recebido=metricas_rush["dano"],
                                parries_perfeitos=metricas_rush["parries"],
                                qtes_perfeitos=metricas_rush["qtes"],
                            )
                            caminhos.log_info(f"BOSS RUSH: Derrota final gravada no Ranking: Herói '{progresso.nome_heroi}' no Chefe {boss_rush_idx + 1}/7 ({metricas_rush['tempo']:.1f}s, Rank {rk_br_lose['rank']}).")
                        tela_morte.configurar(progresso, game_over_total=True, tentativas=0, modo_boss_rush=True, boss_rush_idx=boss_rush_idx)
                        transicao.iniciar("MORTE", estilo="selo", texto=f"BOSS RUSH FALHOU — {boss_atual_nome} ({boss_rush_idx + 1}/7)")
                    else:
                        caminhos.log_info(f"BOSS RUSH: Jogador caiu contra {boss_atual_nome} ({boss_rush_idx + 1}/7). Vidas: {tent_restantes}/3.")
                        tela_morte.configurar(progresso, game_over_total=False, tentativas=tent_restantes, modo_boss_rush=True, boss_rush_idx=boss_rush_idx)
                        transicao.iniciar("MORTE", estilo="selo", texto=f"BOSS RUSH ({tent_restantes}/3 VIDAS) — {boss_atual_nome}")
                else:
                    metricas_sessao["dano"] += getattr(combate, "dano_recebido_combate", 0)
                    if game_over_total and progresso.tentativas <= 0:
                        if not run_finalizada:
                            run_finalizada = True
                            modo_rk = "DEMO" if CONFIG.get("modo_exposicao_ativo", False) else "CAMPANHA"
                            rk_lose = ranking.calcular_rank_desempenho(
                                dano_recebido=metricas_sessao["dano"] + 90,
                                tempo_segundos=progresso.tempo_decorrido,
                                tempo_meta=max(60.0, float(mapa_idx + 1) * 55.0),
                                qtes_perfeitos=metricas_sessao["qtes"],
                                parries_perfeitos=metricas_sessao["parries"],
                                venceu=False,
                            )
                            RANKING_GLOBAL.adicionar_registro(
                                nome=progresso.nome_heroi,
                                tempo=progresso.tempo_decorrido,
                                tentativas=3,
                                passou=False,
                                sala=mapa_idx + 1,
                                modo=modo_rk,
                                rank=rk_lose["rank"],
                                pontuacao=rk_lose["pontuacao"],
                                dano_recebido=metricas_sessao["dano"],
                                parries_perfeitos=metricas_sessao["parries"],
                                qtes_perfeitos=metricas_sessao["qtes"],
                            )
                            caminhos.log_info(f"DERROTA gravada no Ranking ({modo_rk}): Herói '{progresso.nome_heroi}' após esgotar as 3 vidas ({progresso.tempo_decorrido:.1f}s, Sala {mapa_idx + 1}, Rank {rk_lose['rank']}).")
                        cenarios.regerar_salas_procedurais()
                        salas_entidades = criar_entidades_das_salas(progresso)
                        jogador = _criar_jogador_inicial()
                        mapa_idx = 0
                        mapa_atual = DADOS_MAPAS[0]
                        tela_morte.configurar(progresso, game_over_total=True, tentativas=0)
                        transicao.iniciar("MORTE", estilo="selo", texto="GAME OVER — 3 MORTES")
                    else:
                        caminhos.log_info(f"Jogador caiu em combate na Sala {mapa_idx + 1}. Tentativas restantes: {tent_restantes}/3.")
                        progresso.registrar_vida(mapa_idx, 1)
                        progresso.salvar()
                        tela_morte.configurar(progresso, game_over_total=False, tentativas=tent_restantes)
                        transicao.iniciar("MORTE", estilo="selo", texto=f"A SOMBRA VENCEU ({tent_restantes}/3 VIDAS)")

        elif modo_jogo == "MORTE":
            if BOT.ativo and BOT.atualizar_morte(dt):
                if BOT.modo_vitrine and tela_morte.game_over_total:
                    BOT.desligar()
                    def _menu_vitrine():
                        menu.abrir_principal()
                    transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO MENU", callback=_menu_vitrine)
                elif tela_morte.game_over_total:
                    def _recomecar_bot():
                        nonlocal salas_entidades, jogador, mapa_idx, run_finalizada
                        run_finalizada = False
                        progresso.apagar(manter_tempo=True)
                        cenarios.regerar_salas_procedurais()
                        salas_entidades = criar_entidades_das_salas(progresso)
                        jogador = _criar_jogador_inicial()
                        entrar_na_sala(0)
                    transicao.iniciar("MAPA", estilo="selo", texto="NOVA TENTATIVA DO BOT", callback=_recomecar_bot)
                else:
                    def _reviver_bot():
                        progresso.reviver_jogador()
                        entrar_na_sala(mapa_idx)
                    transicao.iniciar("MAPA", estilo="fade", texto="BOT RETOMANDO", callback=_reviver_bot)

        elif modo_jogo == "CUTSCENE_PASSAGEM":
            if mini_cutscene:
                if BOT.ativo:
                    mini_cutscene.pular()
                else:
                    mini_cutscene.update(dt)

        elif modo_jogo == "CUTSCENE_FINAL":
            if cutscene_final:
                acao = cutscene_final.update(dt)
                if acao == "REINICIAR":
                    def _reset_fim():
                        nonlocal salas_entidades, jogador
                        progresso.apagar()
                        cenarios.regerar_salas_procedurais()
                        salas_entidades = criar_entidades_das_salas(progresso)
                        jogador = _criar_jogador_inicial()
                        entrar_na_sala(0)
                        menu.abrir_principal()
                    transicao.iniciar("MENU", estilo="selo", texto="NOVO CICLO", callback=_reset_fim)
                elif acao == "MENU":
                    def _menu_fim():
                        menu.abrir_principal()
                    transicao.iniciar("MENU", estilo="fade", texto="RETORNO AO REINO", callback=_menu_fim)

        elif modo_jogo == "EXPOSICAO_FIM":
            res_kiosk = tela_fim_exposicao.update(dt)
            if res_kiosk == "RESET_MENU":
                run_finalizada = False
                inimigos_derrotados_sessao = 0
                progresso.apagar(manter_tempo=False)
                def _auto_kiosk_menu():
                    nonlocal modo_jogo
                    menu.abrir_principal()
                    modo_jogo = "MENU"
                transicao.iniciar("MENU", estilo="fade", texto="DEMONSTRAÇÃO REINICIADA", callback=_auto_kiosk_menu)

        elif modo_jogo == "INTRODUCAO":
            if cutscene_intro:
                cutscene_intro.update(dt)

        elif modo_jogo == "BOSS_RUSH_TRANSICAO":
            if boss_rush_trans:
                boss_rush_trans["timer"] -= dt
                if boss_rush_trans["timer"] <= 0.0:
                    novo_idx = boss_rush_trans["idx"]
                    novo_boss = boss_rush_trans["boss"]
                    mapa_idx = novo_idx
                    jogador.mapa_idx = novo_idx
                    jogador.hp = boss_rush_trans["hp"]
                    combate = CombateExpedition33(jogador, novo_boss, vantagem="INIMIGO", sala_idx=novo_idx, modo_boss_rush=True, sala_atual=novo_idx)
                    combate.jogador_hp = boss_rush_trans["hp"]
                    combate.jogador_ap = max(0, min(combate.max_ap, boss_rush_trans["ap"]))
                    combate.qtd_pocao = max(0, boss_rush_trans["pocao"])
                    combate.qtd_cristal_ap = max(0, boss_rush_trans["eter"])
                    combate.tempo_boss_rush_ativo = metricas_rush["tempo"]
                    combate._fim_processado = False
                    boss_rush_trans = None
                    if novo_idx in (1, 4, 5):
                        audio.tocar_musica("forest_theme")
                    else:
                        audio.tocar_musica("dungeon_theme")
                    modo_jogo = "COMBATE"

        if modo_jogo == "SPLASH_ESTUDIO":
            splash_estudio.draw(tela_virtual)

        elif modo_jogo == "MENU":
            menu.draw(tela_virtual)
            if abertura_menu_fade > 0.0:
                veu_abertura = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
                veu_abertura.fill(COR_FUNDO_SPLASH)
                veu_abertura.set_alpha(int(255 * abertura_menu_fade))
                tela_virtual.blit(veu_abertura, (0, 0))

        elif modo_jogo == "MAPA":
            off_x = camera.offset_x - camera.shake_x
            off_y = camera.offset_y - camera.shake_y
            desenhar_fundo_sala(tela_virtual, mapa_idx, offset_x=off_x, offset_y=off_y)
            desenhar_decoracoes(tela_virtual, mapa_idx, off_x, camera_y=off_y)
            desenhar_estruturas_organicas(tela_virtual, mapa_idx, off_x, camera_y=off_y, tempo=tempo_mundo)
            desenhar_terreno(tela_virtual, mapa_idx, off_x, camera_y=off_y)
            desenhar_armadilhas(tela_virtual, mapa_idx, off_x, tempo_mundo, camera_y=off_y)

            mapa_atual = DADOS_MAPAS[mapa_idx]
            jogador.mapa_idx = mapa_idx
            grupo_sala = salas_entidades[mapa_idx]
            boss_atual = grupo_sala["boss"]
            larg_m = float(mapa_atual.get("largura", LARGURA_MUNDO))
            portal_pos = mapa_atual.get("portal_saida", (larg_m - 140, 960))
            desenhar_saida(tela_virtual, off_x, boss_atual.vivo, tempo_mundo, camera_y=off_y, portal_pos=portal_pos)

            desenhar_portoes(tela_virtual, grupo_sala, off_x, off_y, tempo_mundo)
            desenhar_alavancas(tela_virtual, grupo_sala, off_x, off_y, tempo_mundo)
            desenhar_chaves(tela_virtual, grupo_sala, off_x, off_y, tempo_mundo)
            desenhar_baus(tela_virtual, grupo_sala, off_x, off_y, tempo_mundo)

            for inim in grupo_sala["inimigos"]:
                inim.draw(tela_virtual, camera)
            boss_atual.draw(tela_virtual, camera)
            jogador.draw(tela_virtual, camera)

            if mapa_idx == 6:
                desenhar_runas_puzzle(tela_virtual, off_x, jogador, tempo_mundo, camera_offset_y=off_y)
                camadas_esc = max(0, 3 - len(getattr(jogador, "runas_ativadas", set())))
                if camadas_esc == 0:
                    for g in grupo_sala.get("portoes", []):
                        g["aberto"] = True
                if boss_atual.vivo:
                    bx_s = int(boss_atual.x + boss_atual.largura // 2 - off_x)
                    by_s = int(boss_atual.y + boss_atual.altura // 2 - off_y)
                    pulso_esc = 0.5 + 0.5 * math.sin(tempo_mundo * 3.0)
                    if camadas_esc > 0:
                        for c_idx in range(camadas_esc):
                            r_esc = int(42 + c_idx * 10 + 5 * pulso_esc)
                            s_aura = pygame.Surface((r_esc * 2 + 4, r_esc * 2 + 4), pygame.SRCALPHA)
                            pygame.draw.circle(s_aura, (150, 65, 235, int(28 + 20 * pulso_esc)), (r_esc + 2, r_esc + 2), r_esc)
                            pygame.draw.circle(s_aura, (195, 130, 255, 185), (r_esc + 2, r_esc + 2), r_esc, 2)
                            tela_virtual.blit(s_aura, (bx_s - r_esc - 2, by_s - r_esc - 2))
                        lbl_esc = fonte_pequena.render(f"ESCUDO ({camadas_esc}/3)", True, (215, 160, 255))
                        tela_virtual.blit(lbl_esc, (bx_s - lbl_esc.get_width() // 2, by_s - 66))
                    else:
                        lbl_vuln = fonte_pequena.render("SELO QUEBRADO • VULNERÁVEL!", True, (90, 255, 195))
                        tela_virtual.blit(lbl_vuln, (bx_s - lbl_vuln.get_width() // 2, by_s - 66))

            desenhar_prompts_interacao(tela_virtual, grupo_sala, jogador, off_x, off_y, tempo_mundo, fonte_pequena)
            vagalumes.draw(tela_virtual, mapa_atual["visual"]["vagalumes"])
            desenhar_atmosfera_camada(tela_virtual, mapa_idx, off_y, jogador.y, tempo_mundo)

            desenhar_hud_mapa(tela_virtual, mapa_idx, mapa_atual, jogador, grupo_sala, boss_atual)
            if boss_atual and getattr(boss_atual, "vivo", True) and getattr(boss_atual, "hp", 0) > 0:
                if abs(jogador.x - boss_atual.x) < 850:
                    desenhar_barra_boss_mapa(tela_virtual, boss_atual, tempo_mundo)
            desenhar_notificacoes_hud(tela_virtual, dt)
            desenhar_cronometro_superior(tela_virtual, progresso.tempo_decorrido, modo_jogo="MAPA")

            if banner_sala["tempo"] > 0:
                banner_sala["tempo"] -= dt
                desenhar_banner_sala_hk(tela_virtual, banner_sala["nome"], banner_sala["idx"], banner_sala["tempo"])

        elif modo_jogo == "COMBATE":
            combate.draw(tela_virtual)
            if not getattr(combate, "modo_boss_rush", False):
                desenhar_cronometro_superior(tela_virtual, progresso.tempo_decorrido, modo_jogo="COMBATE")

        elif modo_jogo == "BOSS_RUSH_TRANSICAO":
            tela_virtual.fill(ui_procedural.COR_EBANO_FUNDO)
            cx_br, cy_br = LARGURA_TELA // 2, ALTURA_TELA // 2
            if boss_rush_trans:
                f_topo = ui_procedural.obter_fonte_serif(14, bold=True)
                f_nome_br = ui_procedural.obter_fonte_serif(24, bold=True)
                f_rec = ui_procedural.obter_fonte_serif(13, bold=False)

                ui_procedural.desenhar_divisor_dourado(tela_virtual, cx_br - 240, cy_br - 68, 480)
                ui_procedural.desenhar_divisor_dourado(tela_virtual, cx_br - 240, cy_br + 68, 480)

                s_stage = f_topo.render(f"BOSS RUSH  ·  CONFRONTO {boss_rush_trans['idx'] + 1} / 7", True, ui_procedural.COR_CINZA_TEXTO)
                tela_virtual.blit(s_stage, (cx_br - s_stage.get_width() // 2, cy_br - 52))

                cont_seg = max(1, min(3, int(math.ceil(boss_rush_trans["timer"]))))
                txt_prox = f"Próximo: {boss_rush_trans['nome']} em {cont_seg}..."
                s_prox = f_nome_br.render(txt_prox, True, ui_procedural.COR_OURO_VIVO)
                tela_virtual.blit(s_prox, (cx_br - s_prox.get_width() // 2, cy_br - s_prox.get_height() // 2 - 4))

                rec_txt = f"HP {boss_rush_trans['hp']}/{jogador.max_hp}   ·   Éter {boss_rush_trans['ap']}/{CONFIG['jogador_max_ap']}   ·   Poções {boss_rush_trans['pocao']}   ·   Cristais {boss_rush_trans['eter']}"
                s_rec = f_rec.render(rec_txt, True, ui_procedural.COR_AZUL_ETER_CLARO)
                tela_virtual.blit(s_rec, (cx_br - s_rec.get_width() // 2, cy_br + 36))

        elif modo_jogo == "MORTE":
            tela_morte.update(dt)
            tela_morte.draw(tela_virtual, mapa_idx, progresso)
            desenhar_cronometro_superior(tela_virtual, progresso.tempo_decorrido, modo_jogo="MORTE")

        elif modo_jogo == "VITORIA":
            tela_virtual.fill(ui_procedural.COR_EBANO_FUNDO)
            painel_v = pygame.Rect((LARGURA_TELA - 640) // 2, (ALTURA_TELA - 320) // 2, 640, 320)
            ui_procedural.desenhar_moldura_gotica(tela_virtual, painel_v, chanfro=9, destacado=True, alpha=246, cranios=True, cantoneiras=True)

            t_vit = metricas_rush["tempo"] if modo_boss_rush else progresso.tempo_decorrido
            f_v1 = ui_procedural.obter_fonte_serif(26, bold=True)
            f_v2 = ui_procedural.obter_fonte_serif(14, bold=False)
            t1 = f_v1.render("VITÓRIA ALCANÇADA", True, ui_procedural.COR_OURO_VIVO)
            t2 = f_v2.render(f"{progresso.nome_heroi}  ·  Tempo: {formatar_tempo(t_vit)}  ·  Tentativas: {progresso.tentativas_gastas}", True, ui_procedural.COR_BRANCO_PEROLA)

            tela_virtual.blit(t1, (painel_v.centerx - t1.get_width() // 2, painel_v.top + 22))
            tela_virtual.blit(t2, (painel_v.centerx - t2.get_width() // 2, painel_v.top + 60))
            ui_procedural.desenhar_divisor_dourado(tela_virtual, painel_v.left + 40, painel_v.top + 92, painel_v.width - 80)

            rk_vit = ultimo_rank_resultado or ranking.calcular_rank_desempenho(
                dano_recebido=metricas_sessao["dano"],
                tempo_segundos=t_vit,
                tempo_meta=float(len(DADOS_MAPAS)) * 55.0,
                qtes_perfeitos=metricas_sessao["qtes"],
                parries_perfeitos=metricas_sessao["parries"],
                venceu=True,
            )
            ui_procedural.desenhar_brasao_rank(
                tela_virtual,
                painel_v.left + 116,
                painel_v.top + 164,
                rk_vit.get("rank", "C"),
                pontuacao=rk_vit.get("pontuacao", 0),
                tamanho=68,
                sem_avaria=rk_vit.get("sem_avaria", False),
                titulo="RANK FINAL",
                anim_t=tempo_mundo,
            )

            r_btn_nova = pygame.Rect(painel_v.left + 236, painel_v.top + 126, 356, 48)
            r_btn_menu = pygame.Rect(painel_v.left + 236, painel_v.top + 188, 356, 48)
            sub_nova = ui_medieval.tag_comando("reiniciar")
            sub_menu = ui_medieval.tag_comando("cancelar")
            ui_procedural.desenhar_botao_gotico(tela_virtual, r_btn_nova, "NOVA JORNADA", fonte_pequena, selecionado=True, icone="espada", subtexto=sub_nova)
            ui_procedural.desenhar_botao_gotico(tela_virtual, r_btn_menu, "VOLTAR AO MENU", fonte_pequena, selecionado=False, icone="grade", subtexto=sub_menu)
            ui_procedural.desenhar_rodape_comandos(tela_virtual, painel_v.bottom - 24, ["[R] Nova Jornada", "[ESC] Menu Principal"])

        elif modo_jogo == "CUTSCENE_PASSAGEM":
            if mini_cutscene:
                mini_cutscene.draw(tela_virtual)

        elif modo_jogo == "CUTSCENE_FINAL":
            if cutscene_final:
                cutscene_final.draw(tela_virtual)

        elif modo_jogo == "CONFIG_UI":
            configurador_ui_global.draw(tela_virtual)

        elif modo_jogo == "EXPOSICAO_FIM":
            tela_fim_exposicao.draw(tela_virtual)

        elif modo_jogo == "INTRODUCAO":
            if cutscene_intro:
                cutscene_intro.draw(tela_virtual)

        # Overlay de transição (por cima de tudo)
        transicao.draw(tela_virtual)

        # Overlay visual do Bot Autônomo (quando ativo)
        if BOT.ativo and modo_jogo not in ("MENU", "SPLASH_ESTUDIO"):
            BOT.desenhar_overlay(tela_virtual, LARGURA_TELA, ALTURA_TELA, fonte_pequena)

        _apresentar_tela_virtual()

    if modo_jogo == "MAPA":
        progresso.registrar_vida(mapa_idx, jogador.hp)
    progresso.salvar()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
