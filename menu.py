# -*- coding: utf-8 -*-
"""Menu Principal, Mapa de Salas em Nós Góticos, Nome do Herói e Ranking (Expedition 33)."""

import math
import os
import pygame

import cenarios
from cenarios import LARGURA_TELA, ALTURA_TELA
from config import CONFIG
from sprites import criar_animador
import ui_assets
import ui_procedural
import ui_medieval
import ui_configurador
import ui
from caminhos import obter_caminho_recurso, log_aviso
import audio
import json
from progresso import obter_caminho_perfil
from ranking import formatar_tempo, obter_rank_registro, RANKING_GLOBAL

PERIGO_SALAS = [
    "Baixo",
    "Moderado",
    "Elevado",
    "Alto",
    "Severo",
    "Extremo",
    "Abissal",
]

ROMANOS = ["I", "II", "III", "IV", "V", "VI", "VII"]


def _fonte(nomes, tam, bold=False):
    for n in nomes:
        try:
            if pygame.font.match_font(n):
                return pygame.font.SysFont(n, tam, bold=bold)
        except Exception:
            pass
    try:
        return pygame.font.SysFont("serif", tam, bold=bold)
    except Exception:
        return pygame.font.Font(None, tam)


class MenuInicial:
    def __init__(self, progresso):
        self.progresso = progresso
        self.fonte_micro = ui_procedural.obter_fonte_serif(12, bold=False)
        self.fonte_peq = ui_procedural.obter_fonte_serif(14, bold=True)
        self.fonte = ui_procedural.obter_fonte_serif(17, bold=True)
        self.fonte_botao = ui_procedural.obter_fonte_serif(18, bold=True)
        self.fonte_titulo = ui_procedural.obter_fonte_serif(44, bold=True)
        self.fonte_grande = ui_procedural.obter_fonte_serif(26, bold=True)

        self.estado = "PRINCIPAL"  # PRINCIPAL | SALAS | RANQUE | NOME_HEROI | CONFIGURACOES
        self.botoes = ["INICIAR JORNADA", "SELEÇÃO DE SALAS", "BOSS RUSH", "RANQUE", "OPÇÕES", "SAIR"]
        self.sel_botao = 0
        self.sel_sala = progresso.ultima_sala
        self.t = 0.0
        self.aviso = ""
        self.tempo_aviso = 0.0
        self.vagalumes = cenarios.Vagalumes(28)
        self.menu_configuracoes = ui_configurador.TelaMenuConfiguracoes(self.fonte_peq, self.fonte, self.fonte_grande)

        self.nome_input = getattr(progresso, "nome_heroi", "Viajante")
        self.destino_acao = ("jogar",)
        self.aba_ranque = "CAMPANHA"
        self.rect_tab_campanha = pygame.Rect(0, 0, 0, 0)
        self.rect_tab_rush = pygame.Rect(0, 0, 0, 0)
        self.rect_tab_demo = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_confirmar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_cancelar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_voltar_ranque = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_reiniciar_ranque = pygame.Rect(0, 0, 0, 0)

        self.heroi = criar_animador(CONFIG.get("sprite_jogador"))
        self.rival = criar_animador(["Orc Vazio", "Orc"])
        self.rects_botoes = []
        self.rects_salas = []
        self.rect_reset = pygame.Rect(0, 0, 0, 0)
        self._titulo_cache = None
        try:
            ui_assets.iniciar()
        except Exception:
            pass

    def abrir_principal(self):
        self.estado = "PRINCIPAL"
        self.sel_sala = self.progresso.ultima_sala

    def _avisar(self, texto):
        self.aviso = texto
        self.tempo_aviso = 2.2

    def _sala_desbloqueada(self, idx):
        if idx <= 0:
            return True
        return (
            (idx - 1) in self.progresso.chefes
            or self.progresso.visitada(idx)
            or idx <= self.progresso.ultima_sala
        )

    def _alternar_exposicao(self):
        ativo_novo = not bool(CONFIG.get("modo_exposicao_ativo", False))
        ui_configurador.salvar_config_exposicao(
            ativo_novo,
            CONFIG.get("exposicao_tempo_limite_segundos", 420),
            CONFIG.get("exposicao_sala_limite", 5),
        )
        self._avisar("Modo Exposição: ATIVADO" if ativo_novo else "Modo Exposição: DESATIVADO")

    def handle_event(self, event):
        if self.estado == "PRINCIPAL":
            return self._evento_principal(event)
        if self.estado == "SALAS":
            return self._evento_salas(event)
        if self.estado == "RANQUE":
            return self._evento_ranque(event)
        if self.estado == "NOME_HEROI":
            return self._evento_nome_heroi(event)
        if self.estado in ("CONFIGURACOES", "CONFIG_UI"):
            res = self.menu_configuracoes.handle_event(event)
            if res in ("voltar", "salvo") and self.menu_configuracoes.estado == "HUB":
                self.abrir_principal()
            return None
        return None

    def _ativar_botao(self, i):
        audio.tocar_sfx("door_open", 0.7)
        if i == 0:
            self.estado = "NOME_HEROI"
            self.destino_acao = ("jogar",)
            self.nome_input = getattr(self.progresso, "nome_heroi", "Viajante")
            return None
        if i == 1:
            self.estado = "SALAS"
            self.sel_sala = self.progresso.ultima_sala
            return None
        if i == 2:
            self.estado = "NOME_HEROI"
            self.destino_acao = ("boss_rush",)
            self.nome_input = getattr(self.progresso, "nome_heroi", "Viajante")
            return None
        if i == 3:
            self.estado = "RANQUE"
            return None
        if i == 4:
            self.menu_configuracoes.abrir_hub()
            self.estado = "CONFIGURACOES"
            return None
        return ("sair",)

    def _evento_principal(self, event):
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_UP, pygame.K_w):
                self.sel_botao = (self.sel_botao - 1) % len(self.botoes)
                audio.tocar_sfx("ui_select", 0.45)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.sel_botao = (self.sel_botao + 1) % len(self.botoes)
                audio.tocar_sfx("ui_select", 0.45)
            elif k == pygame.K_SPACE:
                return self._ativar_botao(0)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._ativar_botao(self.sel_botao)
            elif k == pygame.K_b:
                return self._ativar_botao(2)
            elif k == pygame.K_t:
                self._alternar_exposicao()
                audio.tocar_sfx("ui_select", 0.5)
            elif k == pygame.K_o:
                return self._ativar_botao(4)
            elif k == pygame.K_ESCAPE:
                audio.tocar_sfx("ui_select", 0.4)
                return ("sair",)
        elif event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects_botoes):
                if r.collidepoint(event.pos) and self.sel_botao != i:
                    self.sel_botao = i
                    audio.tocar_sfx("ui_select", 0.3)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.rects_botoes):
                if r.collidepoint(event.pos):
                    self.sel_botao = i
                    return self._ativar_botao(i)
        return None

    def _entrar_sala_se_desbloqueada(self, idx):
        if not self._sala_desbloqueada(idx):
            self._avisar("Sala bloqueada — derrote o guardião anterior.")
            audio.tocar_sfx("ui_select", 0.4)
            return None
        self.estado = "NOME_HEROI"
        self.destino_acao = ("sala", idx)
        self.nome_input = getattr(self.progresso, "nome_heroi", "Viajante")
        return None

    def _evento_salas(self, event):
        n = cenarios.NUM_SALAS
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.sel_sala = (self.sel_sala - 1) % n
                audio.tocar_sfx("ui_select", 0.35)
            elif k in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.sel_sala = (self.sel_sala + 1) % n
                audio.tocar_sfx("ui_select", 0.35)
            elif pygame.K_1 <= k <= pygame.K_9 and (k - pygame.K_1) < n:
                return self._entrar_sala_se_desbloqueada(k - pygame.K_1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self._entrar_sala_se_desbloqueada(self.sel_sala)
            elif k == pygame.K_r:
                self.progresso.curar_sala(self.sel_sala)
                self.progresso.salvar()
                self._avisar(f"HP da Sala {self.sel_sala + 1} restaurado.")
            elif k == pygame.K_t:
                self.progresso.apagar()
                self.sel_sala = 0
                self._avisar("Progresso reiniciado.")
                return ("reset_salas",)
            elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.estado = "PRINCIPAL"
        elif event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects_salas):
                if r.collidepoint(event.pos):
                    self.sel_sala = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect_reset.collidepoint(event.pos):
                self.progresso.apagar()
                self.sel_sala = 0
                self._avisar("Progresso reiniciado.")
                return ("reset_salas",)
            for i, r in enumerate(self.rects_salas):
                if r.collidepoint(event.pos):
                    self.sel_sala = i
                    return self._entrar_sala_se_desbloqueada(i)
        return None

    def _evento_nome_heroi(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._confirmar_nome_heroi()
            if event.key == pygame.K_ESCAPE:
                audio.tocar_sfx("ui_select", 0.4)
                self.estado = "PRINCIPAL"
            elif event.key == pygame.K_BACKSPACE:
                if self.nome_input:
                    self.nome_input = self.nome_input[:-1]
                    audio.tocar_sfx("ui_select", 0.25)
            elif event.unicode and event.unicode.isprintable() and len(self.nome_input) < 16:
                self.nome_input += event.unicode
                audio.tocar_sfx("ui_select", 0.25)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect_btn_confirmar.collidepoint(event.pos):
                return self._confirmar_nome_heroi()
            if self.rect_btn_cancelar.collidepoint(event.pos):
                audio.tocar_sfx("ui_select", 0.4)
                self.estado = "PRINCIPAL"
        return None

    def _confirmar_nome_heroi(self):
        nome_final = (self.nome_input.strip() or "Viajante")[:16]
        self.progresso.trocar_perfil(nome_final)
        self.sel_sala = self.progresso.ultima_sala
        audio.tocar_sfx("door_open", 0.8)
        if self.destino_acao[0] == "jogar":
            return ("jogar", nome_final)
        if self.destino_acao[0] == "sala":
            return ("sala", self.destino_acao[1], nome_final)
        if self.destino_acao[0] == "boss_rush":
            return ("boss_rush", nome_final)
        return ("jogar", nome_final)

    def _evento_ranque(self, event):
        modos = ["CAMPANHA", "BOSS_RUSH", "DEMO"]
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                audio.tocar_sfx("ui_select", 0.4)
                self.estado = "PRINCIPAL"
            elif event.key in (pygame.K_TAB, pygame.K_RIGHT, pygame.K_d):
                idx = modos.index(self.aba_ranque) if self.aba_ranque in modos else 0
                self.aba_ranque = modos[(idx + 1) % len(modos)]
                audio.tocar_sfx("ui_select", 0.45)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                idx = modos.index(self.aba_ranque) if self.aba_ranque in modos else 0
                self.aba_ranque = modos[(idx - 1) % len(modos)]
                audio.tocar_sfx("ui_select", 0.45)
            elif event.key == pygame.K_r:
                RANKING_GLOBAL.reiniciar(self.aba_ranque)
                self._avisar(f"Ranque {self.aba_ranque} zerado.")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect_tab_campanha.collidepoint(event.pos):
                self.aba_ranque = "CAMPANHA"
            elif self.rect_tab_rush.collidepoint(event.pos):
                self.aba_ranque = "BOSS_RUSH"
            elif self.rect_tab_demo.collidepoint(event.pos):
                self.aba_ranque = "DEMO"
            elif self.rect_btn_reiniciar_ranque.collidepoint(event.pos):
                RANKING_GLOBAL.reiniciar(self.aba_ranque)
                self._avisar(f"Ranque {self.aba_ranque} zerado.")
            elif self.rect_btn_voltar_ranque.collidepoint(event.pos):
                self.estado = "PRINCIPAL"
        return None

    def update(self, dt):
        self.t += dt
        self.tempo_aviso = max(0.0, self.tempo_aviso - dt)
        self.vagalumes.update(dt)
        if self.estado in ("CONFIGURACOES", "CONFIG_UI"):
            self.menu_configuracoes.update(dt)
        self.heroi.tocar("idle")
        self.heroi.update(dt)
        self.rival.tocar("idle")
        self.rival.update(dt)

    def draw(self, surface):
        idx_fundo = 2 if self.estado != "SALAS" else self.sel_sala
        cenarios.desenhar_fundo_sala(surface, idx_fundo, offset_x=self.t * 10, forcar_ceu=(self.estado != "SALAS"))
        # Véu ébano translúcido preservando a igreja gótica, lua e nuvens ao fundo
        veu = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        veu.fill((11, 15, 25, 118 if self.estado == "PRINCIPAL" else 165))
        surface.blit(veu, (0, 0))

        if self.estado == "PRINCIPAL":
            self._desenhar_principal(surface)
        elif self.estado == "SALAS":
            self._desenhar_salas(surface)
        elif self.estado == "RANQUE":
            self._desenhar_ranque(surface)
        elif self.estado == "NOME_HEROI":
            self._desenhar_nome_heroi(surface)
        elif self.estado in ("CONFIGURACOES", "CONFIG_UI"):
            self.menu_configuracoes.draw(surface)

        if self.tempo_aviso > 0:
            txt = self.fonte_peq.render(self.aviso, True, ui_procedural.COR_OURO_VIVO)
            bw = txt.get_width() + 32
            bx = (LARGURA_TELA - bw) // 2
            ui_procedural.desenhar_painel_gotico(surface, bx, 452, bw, 32, chanfro=5, destacado=True, alpha=235, cantoneiras=False)
            surface.blit(txt, (bx + 16, 452 + (32 - txt.get_height()) // 2))

    def _titulo(self):
        if self._titulo_cache is None:
            caminho_logo = obter_caminho_recurso("assets/ui/logo_elos_do_vazio.png")
            if os.path.exists(caminho_logo):
                try:
                    img_logo = pygame.image.load(caminho_logo).convert_alpha()
                    w_alvo = 308
                    h_alvo = int(w_alvo * (img_logo.get_height() / float(img_logo.get_width())))
                    if h_alvo > 176:
                        w_alvo = max(180, int(w_alvo * (176.0 / float(h_alvo))))
                        h_alvo = 176
                    self._titulo_cache = pygame.transform.smoothscale(img_logo, (w_alvo, h_alvo))
                except Exception as e:
                    log_aviso(f"[menu] Aviso ao carregar logo: {e}")
                    self._titulo_cache = None
            if self._titulo_cache is None:
                self._titulo_cache = self.fonte_titulo.render("ELOS DO VAZIO", True, ui_procedural.COR_OURO_VIVO)
        return self._titulo_cache

    def _desenhar_principal(self, surface):
        self.vagalumes.draw(surface, (217, 175, 95))

        # Posicionamento balanceado dos personagens à direita apoiados diretamente no solo dourado
        y_solo = 446
        if self.heroi.ativo:
            self.heroi.desenhar(surface, pygame.Rect(461, y_solo - 115, 68, 115), espelhar=False)
        if self.rival.ativo:
            self.rival.desenhar(surface, pygame.Rect(779, y_solo - 121, 72, 121), espelhar=True)

        # Divisória horizontal dourada sutil no solo
        ui_procedural.desenhar_divisor_dourado(surface, 48, y_solo, LARGURA_TELA - 96)

        # Geometria da coluna esquerda (Logo, divisor e painel de botões centralizados no mesmo eixo)
        bx_menu = 64
        bw_menu, bh_menu, gap_menu = 276, 31, 5
        cx_menu = bx_menu + bw_menu // 2
        painel_w = bw_menu + 32
        painel_x = bx_menu - 16

        # Título oficial do jogo alinhado ao centro dos botões e do painel
        logo_surf = self._titulo()
        flutua = int(math.sin(self.t * 1.5) * 2.0)
        logo_x = cx_menu - logo_surf.get_width() // 2
        surface.blit(logo_surf, (logo_x, 16 + flutua))

        # Filete dourado sob o título
        y_sep = 16 + logo_surf.get_height() + 6
        ui_procedural.desenhar_divisor_dourado(surface, cx_menu - 134, y_sep, 268)

        # Painel de menu em ardósia profunda (#0F0F1A) com botões metálicos chanfrados
        icones_menu = ("espada", "portao", "coroa", "relogio", "escudo", "grade")
        self.rects_botoes = []
        painel_h = len(self.botoes) * bh_menu + (len(self.botoes) - 1) * gap_menu + 20
        painel_y = min(y_sep + 8, y_solo - 8 - painel_h)
        by_menu = painel_y + 10
        ui_procedural.desenhar_moldura_gotica(
            surface, painel_x, painel_y, painel_w, painel_h,
            chanfro=7, destacado=True, alpha=244, cantoneiras=True, cranios=False
        )
        for i, nome in enumerate(self.botoes):
            r = pygame.Rect(bx_menu, by_menu + i * (bh_menu + gap_menu), bw_menu, bh_menu)
            self.rects_botoes.append(r)
            ativo = (i == self.sel_botao)
            ui_procedural.desenhar_botao_gotico(
                surface, r, nome, self.fonte_peq,
                selecionado=ativo, icone=icones_menu[i]
            )

        if CONFIG.get("modo_exposicao_ativo", False):
            badge = self.fonte_micro.render("MODO EXPOSIÇÃO ATIVO", True, ui_procedural.COR_OURO_VIVO)
            ui_procedural.desenhar_moldura_gotica(surface, LARGURA_TELA - badge.get_width() - 46, 20, badge.get_width() + 24, 26, chanfro=4, destacado=True, alpha=240, cantoneiras=False)
            surface.blit(badge, (LARGURA_TELA - badge.get_width() - 34, 25))

        if ui_procedural.INPUT_MANAGER.usar_controle():
            comandos = [
                "[ESPAÇO] Iniciar Jornada",
                "[↑ / ↓] Navegar",
                "[ESC] Sair",
            ]
        else:
            comandos = [
                "[ESPAÇO] Iniciar",
                "[B] Boss Rush",
                "[T] Exposição",
                "[ESC] Sair",
            ]
        ui_procedural.desenhar_rodape_comandos(surface, 504, comandos, self.fonte_micro, largura=LARGURA_TELA)

    def _desenhar_salas(self, surface):
        self.vagalumes.draw(surface, (217, 175, 95))

        tit = self.fonte_grande.render("SELEÇÃO DE SALAS", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(tit, (LARGURA_TELA // 2 - tit.get_width() // 2, 24))
        ui_procedural.desenhar_divisor_dourado(surface, LARGURA_TELA // 2 - 190, 62, 380)

        # Nós de mapa góticos em constelação horizontal zig-zag ligados por linhas finas
        n = cenarios.NUM_SALAS
        coords = []
        for i in range(n):
            nx = 96 + i * 128
            ny = 200 if i % 2 == 0 else 296
            coords.append((nx, ny))

        for i in range(n - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            desb_prox = self._sala_desbloqueada(i + 1)
            cor_lin = ui_procedural.COR_OURO_DIVISOR if desb_prox else ui_procedural.COR_METAL_BORDA
            pygame.draw.line(surface, cor_lin, (x1, y1), (x2, y2), 1)

        self.rects_salas = []
        for i in range(n):
            nx, ny = coords[i]
            ativo = (i == self.sel_sala)
            desbloqueada = self._sala_desbloqueada(i)
            derrotado = i in self.progresso.chefes

            r_no = pygame.Rect(nx - 48, ny - 48, 96, 96)
            self.rects_salas.append(r_no)

            raio = 24 if ativo else 19
            pts_los = [(nx, ny - raio), (nx + raio, ny), (nx, ny + raio), (nx - raio, ny)]
            cor_fill = ui_procedural.COR_VINHO_VIVO if (ativo and desbloqueada) else (ui_procedural.COR_EBANO_FUNDO if desbloqueada else (15, 16, 24))
            cor_borda = ui_procedural.COR_OURO_VIVO if ativo else (ui_procedural.COR_LATAO_BORDA if desbloqueada else ui_procedural.COR_METAL_BORDA)
            pygame.draw.polygon(surface, cor_fill, pts_los)
            pygame.draw.polygon(surface, cor_borda, pts_los, 2 if ativo else 1)

            num_s = self.fonte.render(ROMANOS[i], True, ui_procedural.COR_OURO_VIVO if desbloqueada else ui_procedural.COR_CINZA_TEXTO)
            surface.blit(num_s, (nx - num_s.get_width() // 2, ny - num_s.get_height() // 2))

            nome_sala = cenarios.DADOS_MAPAS[i]["nome"]
            perigo = PERIGO_SALAS[i]
            if derrotado:
                estado_txt, cor_est = "Conquistado", ui_procedural.COR_ESMERALDA_VIDA
            elif desbloqueada:
                estado_txt, cor_est = "Desbloqueado", ui_procedural.COR_OURO_VIVO
            else:
                estado_txt, cor_est = "Bloqueado", ui_procedural.COR_CINZA_TEXTO

            lbl_y = ny + raio + 8 if i % 2 == 1 else ny - raio - 44
            s_nome = self.fonte_micro.render(nome_sala, True, ui_procedural.COR_BRANCO_PEROLA if ativo else (200, 208, 220))
            s_info = self.fonte_micro.render(f"Perigo: {perigo}  •  {estado_txt}", True, cor_est)
            surface.blit(s_nome, (nx - s_nome.get_width() // 2, lbl_y))
            surface.blit(s_info, (nx - s_info.get_width() // 2, lbl_y + 15))

        sel_nome = cenarios.DADOS_MAPAS[self.sel_sala]["nome"]
        sel_est = "Desbloqueado" if self._sala_desbloqueada(self.sel_sala) else "Bloqueado"
        sel_info = f"Sala {self.sel_sala + 1}: {sel_nome}   —   Perigo: {PERIGO_SALAS[self.sel_sala]}   —   {sel_est}"
        s_sel = self.fonte.render(sel_info, True, ui_procedural.COR_OURO_VIVO)
        pw = max(500, s_sel.get_width() + 56)
        ui_procedural.desenhar_moldura_gotica(surface, (LARGURA_TELA - pw) // 2, 396, pw, 42, chanfro=6, destacado=True, alpha=244, cantoneiras=True)
        surface.blit(s_sel, (LARGURA_TELA // 2 - s_sel.get_width() // 2, 396 + (42 - s_sel.get_height()) // 2))

        self.rect_reset = pygame.Rect(LARGURA_TELA // 2 - 110, 452, 220, 32)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_reset, "REINICIAR PROGRESSO", self.fonte_micro, selecionado=False, icone="grade")

        comandos = ["[A / D] Selecionar", "[ENTER] Entrar", "[R] Restaurar HP", "[ESC] Voltar"]
        ui_procedural.desenhar_rodape_comandos(surface, 504, comandos, self.fonte_micro, largura=LARGURA_TELA)

    def _obter_resumo_perfil_digitado(self):
        nome_cand = (self.nome_input or "").strip() or "Guerreiro"
        cache = getattr(self, "_cache_perfil_preview", None)
        if cache and cache[0] == nome_cand:
            return cache[1]
        resumo = ("Novo perfil isolado (cronômetro inicia em 00:00.0)", ui_procedural.COR_CINZA_TEXTO)
        try:
            if nome_cand == getattr(self.progresso, "nome_heroi", ""):
                sala_p = int(getattr(self.progresso, "ultima_sala", 0)) + 1
                tempo_p = formatar_tempo(self.progresso.tempo_total_exibicao())
                resumo = (f"Perfil ativo: Sala {sala_p}  ·  Tempo preservado: {tempo_p}", ui_procedural.COR_OURO_VIVO)
            else:
                arq = obter_caminho_perfil(nome_cand)
                if os.path.exists(arq):
                    with open(arq, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    sala_p = int(d.get("sala_atual", int(d.get("ultima_sala", 0)) + 1))
                    tempo_p = formatar_tempo(d.get("tempo_acumulado_segundos", d.get("tempo_decorrido", 0.0)))
                    resumo = (f"Perfil salvo: Sala {sala_p}  ·  Tempo preservado: {tempo_p}", ui_procedural.COR_ESMERALDA_VIDA)
        except Exception:
            pass
        self._cache_perfil_preview = (nome_cand, resumo)
        return resumo

    def _desenhar_nome_heroi(self, surface):
        self.vagalumes.draw(surface, (217, 175, 95))
        nx, ny = LARGURA_TELA // 2 - 270, 128
        ui_procedural.desenhar_moldura_gotica(surface, nx, ny, 540, 266, chanfro=8, destacado=True, alpha=246, cantoneiras=True, cranios=True)

        tit = self.fonte_grande.render("IDENTIDADE DO VIAJANTE", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(tit, (LARGURA_TELA // 2 - tit.get_width() // 2, ny + 22))
        ui_procedural.desenhar_divisor_dourado(surface, nx + 36, ny + 60, 468)

        rect_in = pygame.Rect(LARGURA_TELA // 2 - 180, ny + 74, 360, 42)
        ui_procedural.desenhar_moldura_gotica(surface, rect_in, chanfro=4, destacado=False, alpha=250, cantoneiras=False)
        cursor = "|" if int(self.t * 2.5) % 2 == 0 else ""
        txt_n = self.fonte_grande.render(self.nome_input + cursor, True, ui_procedural.COR_BRANCO_PEROLA)
        surface.blit(txt_n, (rect_in.x + 14, rect_in.centery - txt_n.get_height() // 2))

        info_p, cor_info_p = self._obter_resumo_perfil_digitado()
        s_info = self.fonte_micro.render(info_p, True, cor_info_p)
        surface.blit(s_info, (LARGURA_TELA // 2 - s_info.get_width() // 2, ny + 125))

        mpos = pygame.mouse.get_pos()
        self.rect_btn_confirmar = pygame.Rect(LARGURA_TELA // 2 - 186, ny + 154, 176, 46)
        self.rect_btn_cancelar = pygame.Rect(LARGURA_TELA // 2 + 10, ny + 154, 176, 46)
        hover_cancelar = self.rect_btn_cancelar.collidepoint(mpos)
        ui_procedural.desenhar_botao_gotico(
            surface, self.rect_btn_confirmar, "CONFIRMAR", self.fonte_peq,
            selecionado=not hover_cancelar, icone="espada", subtexto=ui_medieval.tag_comando("confirmar")
        )
        ui_procedural.desenhar_botao_gotico(
            surface, self.rect_btn_cancelar, "VOLTAR", self.fonte_peq,
            selecionado=hover_cancelar, icone="grade", subtexto=ui_medieval.tag_comando("cancelar")
        )
        ui_procedural.desenhar_rodape_comandos(surface, ny + 224, ["Digite o nome do herói", "[ENTER] Confirmar", "[ESC] Voltar"], self.fonte_micro)

    def _desenhar_ranque(self, surface):
        self.vagalumes.draw(surface, (217, 175, 95))
        ui_procedural.desenhar_moldura_gotica(surface, 36, 20, 888, 498, chanfro=8, destacado=True, alpha=246, cantoneiras=True, cranios=True)

        tit = self.fonte_grande.render(f"LIVRO DOS HERÓIS — {self.aba_ranque.replace('_', ' ')}", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(tit, (LARGURA_TELA // 2 - tit.get_width() // 2, 34))
        ui_procedural.desenhar_divisor_dourado(surface, 76, 70, 808)

        self.rect_tab_campanha = pygame.Rect(180, 82, 180, 30)
        self.rect_tab_rush = pygame.Rect(390, 82, 180, 30)
        self.rect_tab_demo = pygame.Rect(600, 82, 180, 30)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_tab_campanha, "CAMPANHA", self.fonte_micro, selecionado=(self.aba_ranque == "CAMPANHA"), icone="espada")
        ui_procedural.desenhar_botao_gotico(surface, self.rect_tab_rush, "BOSS RUSH", self.fonte_micro, selecionado=(self.aba_ranque == "BOSS_RUSH"), icone="coroa")
        ui_procedural.desenhar_botao_gotico(surface, self.rect_tab_demo, "EXPOSIÇÃO", self.fonte_micro, selecionado=(self.aba_ranque == "DEMO"), icone="relogio")

        top = RANKING_GLOBAL.obter_top(7, modo=self.aba_ranque)
        if not top:
            vazio = self.fonte.render("Nenhum registro encontrado.", True, ui_procedural.COR_CINZA_TEXTO)
            surface.blit(vazio, (LARGURA_TELA // 2 - vazio.get_width() // 2, 240))
        else:
            for i, reg in enumerate(top):
                ry = 128 + i * 42
                ui_procedural.desenhar_moldura_gotica(surface, 62, ry, 836, 35, chanfro=4, destacado=(i == 0), alpha=230, cantoneiras=False)
                surface.blit(self.fonte_peq.render(f"{i + 1}º", True, ui_procedural.COR_OURO_VIVO if i == 0 else ui_procedural.COR_BRANCO_PEROLA), (78, ry + 9))
                surface.blit(self.fonte_peq.render(reg.get("nome", "Viajante")[:14], True, ui_procedural.COR_BRANCO_PEROLA), (124, ry + 9))

                letra_r, pts_r = obter_rank_registro(reg)
                cfg_r = ui_procedural.PALETA_RANKS.get(letra_r, ui_procedural.PALETA_RANKS["C"])
                badge_r = pygame.Rect(294, ry + 6, 32, 23)
                pygame.draw.rect(surface, cfg_r["fundo"], badge_r, border_radius=4)
                pygame.draw.rect(surface, cfg_r["cor"], badge_r, 1, border_radius=4)
                s_r = self.fonte_micro.render(letra_r, True, cfg_r["cor"])
                surface.blit(s_r, (badge_r.centerx - s_r.get_width() // 2, badge_r.centery - s_r.get_height() // 2))

                surface.blit(self.fonte_peq.render(formatar_tempo(reg.get("tempo", 0.0)), True, ui_procedural.COR_AZUL_ETER), (344, ry + 9))
                surface.blit(self.fonte_micro.render(f"{pts_r} pts", True, cfg_r["cor"]), (446, ry + 10))
                passou = (reg.get("resultado") == "PASSOU")
                surface.blit(self.fonte_peq.render("PASSOU" if passou else "CAIU", True, ui_procedural.COR_ESMERALDA_VIDA if passou else ui_procedural.COR_VERMELHO_DANO), (546, ry + 9))
                surface.blit(self.fonte_micro.render(f"Sala {reg.get('sala', 1)}", True, ui_procedural.COR_CINZA_TEXTO), (656, ry + 10))
                surface.blit(self.fonte_micro.render(reg.get("data", "--"), True, ui_procedural.COR_CINZA_TEXTO), (748, ry + 10))

        self.rect_btn_reiniciar_ranque = pygame.Rect(80, 446, 224, 36)
        self.rect_btn_voltar_ranque = pygame.Rect(656, 446, 224, 36)
        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_reiniciar_ranque, "ZERAR RANQUE", self.fonte_micro, selecionado=False, icone="frasco", atalho=ui_medieval.tag_comando("reiniciar"))
        ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_voltar_ranque, "VOLTAR AO MENU", self.fonte_micro, selecionado=False, icone="grade", atalho=ui_medieval.tag_comando("cancelar"))
        ui_procedural.desenhar_rodape_comandos(surface, 492, ["[A / D] Alternar Aba", "[R] Zerar", "[ESC] Voltar"], self.fonte_micro)
