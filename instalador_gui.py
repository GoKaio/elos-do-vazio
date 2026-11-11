# -*- coding: utf-8 -*-
"""
Instalador Personalizado Desktop — Elos do Vazio (`instalador_gui.py`).

Janela 800x500 px fiel ao fluxo e diagramação de referência:
  - Cenário gótico vivo ao fundo atrás do cartão central (céu lunar, ruínas,
    chão de cantaria, tochas oscilantes e silhuetas/sprites animados do Herói e Chefe).
  - Cartão flutuante gótico com moldura dupla em latão/ouro (`#D97706`), fundo
    ardósia (`#0F0F1A`), cantoneiras e mini-crânios nos cantos (`ui_procedural.py`).
  - Cabeçalho fixo com título monumental "ELOS DO VAZIO", duas pílulas no topo
    (`VERSÃO 1.0 • WINDOWS` e `[♪ MÚSICA: LIGADA/DESLIGADA]`) e divisor dourado.
  - Fluxo de 4 telas: BOAS_VINDAS -> CONFIG -> INSTALANDO (thread) -> CONCLUIDO.
  - Áudio `pygame.mixer`: música gótica em loop, click metálico e badalo de sino aos 100%.
  - Criação automática de atalhos `.lnk` no Windows via PowerShell (`WScript.Shell`).
"""

import ctypes
import io
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import wave
import zipfile
import pygame

import ui_procedural


LARGURA_JANELA = 800
ALTURA_JANELA = 500
NOME_EXECUTAVEL = "Elos_do_Vazio.exe"
NOME_APLICACAO = "Elos do Vazio"
VERSAO_APLICACAO = "VERSÃO 1.1 • WINDOWS"
CAMINHO_INSTALACAO_PADRAO = r"C:\Jogos\Elos do Vazio"
PAYLOAD_ZIP_RELATIVO = os.path.join("payload", "elos_do_vazio_payload.zip")


def resource_path(relative_path):
    """Resolve caminhos de recursos em modo script ou empacotado via PyInstaller (`_MEIPASS`)."""
    bases = []
    if hasattr(sys, "_MEIPASS"):
        bases.append(sys._MEIPASS)
    bases.append(os.path.dirname(os.path.abspath(__file__)))
    bases.append(os.path.abspath("."))
    for base in bases:
        candidato = os.path.join(base, relative_path)
        if os.path.exists(candidato):
            return candidato
    base_padrao = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_padrao, relative_path)


def obter_pasta_usuario_fallback():
    """Diretório gravável em `%LOCALAPPDATA%` caso falte permissão em `C:\\Jogos`."""
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        return os.path.join(local_app, "Programs", NOME_APLICACAO)
    return os.path.join(os.path.expanduser("~"), NOME_APLICACAO)


def obter_pasta_especial_windows(csidl, fallback):
    """Resolve caminhos reais de Área de Trabalho ou Menu Iniciar no Windows."""
    if sys.platform == "win32":
        try:
            buf = ctypes.create_unicode_buffer(260)
            res = ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
            if res == 0 and buf.value:
                return buf.value
        except Exception:
            pass
    return fallback


def obter_desktop_usuario():
    return obter_pasta_especial_windows(0x0010, os.path.join(os.path.expanduser("~"), "Desktop"))


def obter_menu_iniciar_programas():
    appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    padrao = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")
    return obter_pasta_especial_windows(0x0002, padrao)


def testar_permissao_escrita(caminho_destino):
    """Verifica criação e escrita real no diretório escolhido antes da extração em thread."""
    alvo = os.path.abspath(str(caminho_destino or "").strip())
    if not alvo:
        return False, "Informe um diretório de destino válido."

    criados = []
    try:
        cur = alvo
        faltantes = []
        while cur and not os.path.exists(cur):
            pai = os.path.dirname(cur)
            if pai == cur:
                break
            faltantes.append(cur)
            cur = pai

        os.makedirs(alvo, exist_ok=True)
        for d in faltantes:
            criados.append(d)

        sonda = os.path.join(alvo, ".elos_perm_check.tmp")
        with open(sonda, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(sonda)
        return True, ""
    except PermissionError:
        return False, "Sem permissão de escrita nesta pasta (tente 'Pasta do Usuário' ou Admin)."
    except OSError as exc:
        return False, f"Diretório inacessível ({exc.strerror or exc})."
    finally:
        if criados and os.path.isdir(alvo):
            try:
                if not os.listdir(alvo):
                    for d in criados:
                        if os.path.isdir(d) and not os.listdir(d):
                            os.rmdir(d)
            except Exception:
                pass


def criar_atalho(origem, destino, icone="", pasta_trabalho="", descricao="Elos do Vazio"):
    """Cria atalho `.lnk` nativo no Windows via PowerShell (`WScript.Shell`)."""
    if sys.platform != "win32":
        return False, "Atalhos .lnk suportados apenas no Windows."

    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    pasta_trab = pasta_trabalho or os.path.dirname(os.path.abspath(origem))

    def _esc_ps(val):
        return str(val or "").replace("'", "''")

    cmd = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{_esc_ps(destino)}'); "
        f"$s.TargetPath = '{_esc_ps(origem)}'; "
        f"$s.WorkingDirectory = '{_esc_ps(pasta_trab)}'; "
        f"$s.Description = '{_esc_ps(descricao)}'; "
        f"if ('{_esc_ps(icone)}' -ne '') {{ $s.IconLocation = '{_esc_ps(icone)}'; }} "
        "$s.Save();"
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            creationflags=flags,
            capture_output=True,
            timeout=15,
        )
        if proc.returncode == 0 and os.path.exists(destino):
            return True, ""
    except Exception:
        pass

    def _esc_vbs(val):
        return str(val or "").replace('"', '""')

    vbs = (
        'Set oWS = WScript.CreateObject("WScript.Shell")\r\n'
        f'Set oLink = oWS.CreateShortcut("{_esc_vbs(destino)}")\r\n'
        f'oLink.TargetPath = "{_esc_vbs(origem)}"\r\n'
        f'oLink.WorkingDirectory = "{_esc_vbs(pasta_trab)}"\r\n'
        f'oLink.Description = "{_esc_vbs(descricao)}"\r\n'
    )
    if icone and os.path.exists(icone):
        vbs += f'oLink.IconLocation = "{_esc_vbs(icone)}"\r\n'
    vbs += 'oLink.Save\r\n'

    fd, caminho_vbs = tempfile.mkstemp(prefix="elos_lnk_", suffix=".vbs")
    os.close(fd)
    try:
        with open(caminho_vbs, "w", encoding="utf-16") as f:
            f.write(vbs)
        proc_v = subprocess.run(["wscript.exe", "//Nologo", caminho_vbs], creationflags=flags, capture_output=True, timeout=15)
        if proc_v.returncode == 0 and os.path.exists(destino):
            return True, ""
        return False, "Falha ao registrar atalho."
    except Exception as exc:
        return False, str(exc)
    finally:
        try:
            os.remove(caminho_vbs)
        except Exception:
            pass


def _sintetizar_wav_pcm(amostras_float, sr=22050):
    """Converte amostras mono [-1.0, 1.0] em WAV PCM em memória."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = bytearray()
        for v in amostras_float:
            s_i16 = max(-32767, min(32767, int(v * 32767.0)))
            frames.extend(struct.pack("<h", s_i16))
        wf.writeframes(bytes(frames))
    buf.seek(0)
    return buf


class AudioInstalador:
    """Música tema em loop infinito (`pygame.mixer`), click metálico e badalo de sino aos 100%."""

    def __init__(self):
        self.ativo = False
        self.mudo = False
        self._som_tema_proc = None
        self._som_click = None
        self._som_sino = None
        self._iniciar()

    def _iniciar(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.ativo = True
        except Exception:
            self.ativo = False
            return

        for cand in (
            os.path.join("assets", "sons", "click_metal.wav"),
            os.path.join("assets", "audio", "sfx", "ui_select.ogg"),
            os.path.join("assets", "audio", "sfx", "parry.ogg"),
        ):
            p = resource_path(cand)
            if os.path.isfile(p):
                try:
                    self._som_click = pygame.mixer.Sound(p)
                    self._som_click.set_volume(0.55)
                    break
                except Exception:
                    pass
        if self._som_click is None:
            self._som_click = self._gerar_click_metal()

        for cand in (
            os.path.join("assets", "sons", "sino_gotico.wav"),
            os.path.join("assets", "audio", "sfx", "level_up.ogg"),
        ):
            p = resource_path(cand)
            if os.path.isfile(p):
                try:
                    self._som_sino = pygame.mixer.Sound(p)
                    self._som_sino.set_volume(0.75)
                    break
                except Exception:
                    pass
        if self._som_sino is None:
            self._som_sino = self._gerar_sino_gotico()

        musica_ok = False
        for cand in (
            os.path.join("assets", "sons", "tema_instalador.ogg"),
            os.path.join("assets", "sons", "tema_instalador.wav"),
            os.path.join("assets", "audio", "music", "title_theme.ogg"),
            os.path.join("assets", "audio", "music", "safe_room_theme.ogg"),
        ):
            p = resource_path(cand)
            if os.path.isfile(p):
                try:
                    pygame.mixer.music.load(p)
                    pygame.mixer.music.set_volume(0.45)
                    pygame.mixer.music.play(-1, fade_ms=900)
                    musica_ok = True
                    break
                except Exception:
                    pass

        if not musica_ok:
            try:
                self._som_tema_proc = self._gerar_tema_organo_gotico()
                if self._som_tema_proc is not None:
                    self._som_tema_proc.set_volume(0.30)
                    self._som_tema_proc.play(loops=-1, fade_ms=900)
            except Exception:
                pass

    def _gerar_click_metal(self):
        sr = 22050
        n = int(sr * 0.08)
        amostras = []
        for i in range(n):
            t = i / float(sr)
            env = math.exp(-t * 58.0)
            sig = (
                0.55 * math.sin(2.0 * math.pi * 1320.0 * t)
                + 0.30 * math.sin(2.0 * math.pi * 2410.0 * t)
                + 0.15 * math.sin(2.0 * math.pi * 680.0 * t)
            )
            amostras.append(sig * env * 0.65)
        try:
            snd = pygame.mixer.Sound(file=_sintetizar_wav_pcm(amostras, sr))
            snd.set_volume(0.48)
            return snd
        except Exception:
            return None

    def _gerar_sino_gotico(self):
        sr = 22050
        n = int(sr * 2.4)
        amostras = []
        parciais = ((146.83, 0.50, 1.3), (220.00, 0.28, 1.7), (293.66, 0.34, 2.1), (349.23, 0.18, 2.8), (587.33, 0.10, 4.2))
        for i in range(n):
            t = i / float(sr)
            atk = min(1.0, t / 0.015)
            val = 0.0
            for freq, amp, decaimento in parciais:
                val += amp * math.sin(2.0 * math.pi * freq * t) * math.exp(-t * decaimento)
            amostras.append(val * atk * 0.72)
        try:
            snd = pygame.mixer.Sound(file=_sintetizar_wav_pcm(amostras, sr))
            snd.set_volume(0.68)
            return snd
        except Exception:
            return None

    def _gerar_tema_organo_gotico(self):
        sr = 22050
        dur = 8.0
        n = int(sr * dur)
        acordes = (
            (146.83, 220.00, 293.66, 349.23),
            (116.54, 174.61, 233.08, 293.66),
            (130.81, 196.00, 261.63, 329.63),
            (146.83, 220.00, 293.66, 329.63),
        )
        amostras = []
        fade_borda = int(sr * 0.12)
        for i in range(n):
            t = i / float(sr)
            bloco = min(3, int(t // 2.0))
            t_local = t - bloco * 2.0
            env_acorde = min(1.0, t_local / 0.25) * min(1.0, (2.0 - t_local) / 0.25 + 0.35)
            freqs = acordes[bloco]
            soma = 0.0
            for idx_f, f in enumerate(freqs):
                vib = 1.0 + 0.0022 * math.sin(2.0 * math.pi * (0.4 + idx_f * 0.15) * t)
                soma += (0.34 if idx_f == 0 else 0.20) * math.sin(2.0 * math.pi * f * vib * t)
                soma += 0.06 * math.sin(2.0 * math.pi * (f * 2.0) * t)
            resp = 0.78 + 0.22 * math.sin(2.0 * math.pi * 0.25 * t)
            v = soma * env_acorde * resp * 0.36
            if i < fade_borda:
                v *= i / float(fade_borda)
            elif i > n - fade_borda:
                v *= (n - i) / float(fade_borda)
            amostras.append(v)
        try:
            return pygame.mixer.Sound(file=_sintetizar_wav_pcm(amostras, sr))
        except Exception:
            return None

    def tocar_click(self):
        if self.ativo and not self.mudo and self._som_click is not None:
            try:
                self._som_click.play()
            except Exception:
                pass

    def tocar_sino(self):
        if self.ativo and not self.mudo and self._som_sino is not None:
            try:
                self._som_sino.play()
            except Exception:
                pass

    def alternar_mudo(self):
        self.mudo = not self.mudo
        if not self.ativo:
            return
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.set_volume(0.0 if self.mudo else 0.45)
            if self._som_tema_proc is not None:
                self._som_tema_proc.set_volume(0.0 if self.mudo else 0.30)
        except Exception:
            pass

    def encerrar(self):
        try:
            if self.ativo:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
        except Exception:
            pass


class FundoVivoCidadela:
    """
    Cenário gótico vivo atrás do cartão central do instalador (igual ao vídeo referência):
    céu noturno com lua pálida, silhuetas das ruínas, piso de pedra, tochas nas laterais
    e bonecos pixelados (Cavaleiro à esquerda e Guardião à direita) respirando nas extremidades.
    """

    def __init__(self, w=LARGURA_JANELA, h=ALTURA_JANELA):
        self.w = w
        self.h = h
        self._bg_estatico = self._construir_fundo_base()
        self._particulas = [
            {
                "x": random.uniform(0, w),
                "y": random.uniform(20, h - 40),
                "vx": random.uniform(-9.0, 9.0),
                "vy": random.uniform(-18.0, -7.0),
                "r": random.choice((1, 1, 2)),
                "fase": random.uniform(0.0, math.tau),
                "eter": (i % 3 == 0),
            }
            for i in range(42)
        ]

    def _carregar_camada(self, nome):
        for rel in (
            os.path.join("assets", "final_pack", nome),
            os.path.join("assets", "Legacy-Dungeon", "Final", "Assets", nome),
            os.path.join("assets", nome),
        ):
            p = resource_path(rel)
            if os.path.isfile(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    esc = self.h / float(img.get_height())
                    nw = max(self.w, int(img.get_width() * esc))
                    return pygame.transform.smoothscale(img, (nw, self.h))
                except Exception:
                    pass
        return None

    def _construir_fundo_base(self):
        surf = pygame.Surface((self.w, self.h)).convert()
        # Gradiente noturno + chão de cantaria na base
        for y in range(self.h):
            t = y / float(max(1, self.h - 1))
            r = int(9 + 12 * t)
            g = int(12 + 16 * t)
            b = int(24 + 26 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.w, y))

        bg0 = self._carregar_camada("Background_0.png")
        if bg0 is not None:
            surf.blit(bg0, (0, 0))
        else:
            # Lua pálida visível no canto superior esquerdo/direito fora do cartão
            pygame.draw.circle(surf, (226, 232, 240), (748, 72), 26)
            pygame.draw.circle(surf, (186, 200, 224), (741, 67), 6)

        bg1 = self._carregar_camada("Background_1.png")
        if bg1 is not None:
            surf.blit(bg1, (0, 0))
        else:
            # Silhuetas góticas de torres e sepulturas nas bordas
            cor_sil = (15, 19, 32)
            for tx, tw, th in ((8, 56, 210), (728, 66, 240), (670, 50, 165)):
                pygame.draw.rect(surf, cor_sil, (tx, self.h - 56 - th, tw, th))
                pygame.draw.polygon(surf, cor_sil, [(tx, self.h - 56 - th), (tx + tw // 2, self.h - 92 - th), (tx + tw, self.h - 56 - th)])

        # Piso de pedra escura contínuo na base (y = h - 58 .. h)
        y_solo = self.h - 58
        pygame.draw.rect(surf, (18, 22, 34), (0, y_solo, self.w, 58))
        pygame.draw.line(surf, (71, 85, 105), (0, y_solo), (self.w, y_solo), 2)
        for bx in range(0, self.w, 44):
            pygame.draw.rect(surf, (10, 12, 20), (bx, y_solo + 2, 44, 24), 1)
            pygame.draw.rect(surf, (10, 12, 20), (bx - 22, y_solo + 26, 44, 32), 1)

        # Leve véu atmosférico escuro para dar destaque ao cartão central
        veu = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        veu.fill((6, 8, 15, 118))
        surf.blit(veu, (0, 0))
        return surf

    def update(self, dt):
        for p in self._particulas:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] < 12:
                p["y"] = self.h - 62
                p["x"] = random.uniform(10, self.w - 10)

    def _desenhar_guarda_esquerdo(self, surface, cx, pe_y, tempo):
        """Cavaleiro pixelado respirando na borda inferior esquerda (emoldura o cartão)."""
        resp = int(round(math.sin(tempo * 3.0) * 1.5))
        pygame.draw.ellipse(surface, (4, 6, 12), (cx - 18, pe_y - 4, 36, 9))
        # Capa azul escura e armadura em pixel-blocks
        pygame.draw.polygon(surface, (30, 58, 138), [(cx - 10, pe_y - 34 + resp), (cx - 20, pe_y - 6), (cx + 4, pe_y - 6)])
        pygame.draw.rect(surface, (51, 65, 85), (cx - 9, pe_y - 32 + resp, 18, 24))
        pygame.draw.rect(surface, (148, 163, 184), (cx - 10, pe_y - 48 + resp, 20, 16), border_radius=3)
        pygame.draw.rect(surface, (15, 23, 42), (cx - 4, pe_y - 41 + resp, 12, 4))
        pygame.draw.rect(surface, (56, 189, 248), (cx + 1, pe_y - 40 + resp, 5, 2))
        # Espada em guarda
        pygame.draw.line(surface, (226, 232, 240), (cx + 10, pe_y - 22 + resp), (cx + 22, pe_y - 44 + resp), 2)
        pygame.draw.line(surface, (245, 158, 11), (cx + 7, pe_y - 24 + resp), (cx + 13, pe_y - 20 + resp), 2)

    def _desenhar_boss_direito(self, surface, cx, pe_y, tempo):
        """Sentinela/Orc gótico à direita emoldurando a base do instalador."""
        resp = int(round(math.sin(tempo * 2.6 + 1.4) * 1.8))
        pygame.draw.ellipse(surface, (4, 6, 12), (cx - 20, pe_y - 4, 40, 10))
        pygame.draw.rect(surface, (64, 24, 38), (cx - 12, pe_y - 38 + resp, 24, 30), border_radius=3)
        pygame.draw.rect(surface, (127, 29, 29), (cx - 10, pe_y - 52 + resp, 20, 15), border_radius=3)
        pygame.draw.polygon(surface, (245, 158, 11), [(cx - 9, pe_y - 52 + resp), (cx - 14, pe_y - 62 + resp), (cx - 4, pe_y - 52 + resp)])
        pygame.draw.polygon(surface, (245, 158, 11), [(cx + 9, pe_y - 52 + resp), (cx + 14, pe_y - 62 + resp), (cx + 4, pe_y - 52 + resp)])
        pygame.draw.rect(surface, (253, 224, 71), (cx - 6, pe_y - 46 + resp, 4, 3))
        pygame.draw.rect(surface, (253, 224, 71), (cx + 1, pe_y - 46 + resp, 4, 3))

    def draw(self, surface, tempo):
        surface.blit(self._bg_estatico, (0, 0))
        y_solo = self.h - 58

        # Tochas suaves nos cantos externos (SRCALPHA sem BLEND_ADD)
        for tx in (36, self.w - 36):
            osc = math.sin(tempo * 7.2 + tx)
            ty = y_solo - 82
            sh = pygame.Surface((74, 74), pygame.SRCALPHA)
            pygame.draw.circle(sh, (249, 115, 22, 22), (37, 37), int(32 + osc * 3))
            pygame.draw.circle(sh, (254, 240, 138, 44), (37, 37), 11)
            surface.blit(sh, (tx - 37, ty - 40))
            pygame.draw.rect(surface, (30, 41, 59), (tx - 2, ty, 5, 18))
            pygame.draw.polygon(surface, (249, 115, 22), [(tx - 4, ty), (tx + int(osc), ty - 14), (tx + 4, ty)])
            pygame.draw.circle(surface, (254, 240, 138), (tx, ty - 4), 2)

        # Personagens vivos nas bordas inferiores do cenário atrás do cartão
        self._desenhar_guarda_esquerdo(surface, 36, y_solo + 6, tempo)
        self._desenhar_boss_direito(surface, self.w - 38, y_solo + 6, tempo)

        for p in self._particulas:
            cor = ui_procedural.COR_AZUL_ETER if p["eter"] else ui_procedural.COR_OURO_VIVO
            pygame.draw.circle(surface, cor, (int(p["x"]), int(p["y"])), p["r"])


def _abreviar_caminho(caminho, limite=52):
    txt = str(caminho or "")
    if len(txt) <= limite:
        return txt
    partes = txt.split(os.sep)
    if len(partes) >= 3:
        cand = os.path.join(partes[0] + os.sep, "...", *partes[-2:])
        if len(cand) <= limite:
            return cand
    return "..." + txt[-(limite - 3):]


class InstaladorApp:
    """Controlador das 4 telas do Instalador Gótico Desktop (800x500 px) estilo cartão central."""

    def __init__(self, pasta_inicial=None, audio_ctrl=None):
        self.estado = "BOAS_VINDAS"  # BOAS_VINDAS | CONFIG | INSTALANDO | CONCLUIDO | ERRO
        self.destino_dir = str(pasta_inicial or CAMINHO_INSTALACAO_PADRAO)
        self.editando_caminho = False
        self.criar_atalho_desktop = True
        self.criar_atalho_menu_iniciar = True
        self.executar_apos_instalar = True
        self.audio = audio_ctrl
        self.fundo_vivo = FundoVivoCidadela(LARGURA_JANELA, ALTURA_JANELA)

        self.tempo = 0.0
        self.progresso = 0.0
        self.mensagem_status = "Preparando arquivos da expedição..."
        self.mensagem_erro = ""
        self.arquivos_processados = 0
        self.arquivos_totais = 0
        self.tamanho_estimado_mb = self._estimar_tamanho_payload()
        self.atalhos_criados = []
        self.foco_btn = 1
        self._sino_tocado = False
        self._concluindo_pausa = 0.0
        self._pronto_concluir = False
        self._lock = threading.Lock()
        self._thread = None
        self._pedir_fechar = False

        # Retângulos interativos atualizados a cada frame no draw()
        self.rect_btn_som = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_cancelar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_avancar = pygame.Rect(0, 0, 0, 0)
        self.rect_caixa_dir = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_procurar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_pasta_user = pygame.Rect(0, 0, 0, 0)
        self.rect_chk_desktop = pygame.Rect(0, 0, 0, 0)
        self.rect_chk_menu = pygame.Rect(0, 0, 0, 0)
        self.rect_chk_exec = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_instalar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_jogar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_fechar = pygame.Rect(0, 0, 0, 0)

    def _estimar_tamanho_payload(self):
        zp = resource_path(PAYLOAD_ZIP_RELATIVO)
        if os.path.isfile(zp):
            try:
                return max(12, int(round(os.path.getsize(zp) / (1024.0 * 1024.0) * 1.45)))
            except Exception:
                pass
        return 185

    def _click_som(self):
        if self.audio is not None:
            self.audio.tocar_click()

    def _localizar_fonte_instalacao(self):
        zip_path = resource_path(PAYLOAD_ZIP_RELATIVO)
        if os.path.isfile(zip_path):
            return ("zip", zip_path)
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "Elos_do_Vazio")
        if os.path.isdir(dist_dir) and os.path.isfile(os.path.join(dist_dir, NOME_EXECUTAVEL)):
            return ("dir", dist_dir)
        return (None, None)

    def selecionar_diretorio_dialogo(self):
        """Abre seletor nativo do Windows (`tkinter.filedialog.askdirectory`) sem fechar o Pygame."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            inicial = self.destino_dir if os.path.isdir(self.destino_dir) else os.path.dirname(self.destino_dir)
            escolhido = filedialog.askdirectory(
                title="Escolha o diretório de instalação — Elos do Vazio",
                initialdir=inicial or "C:\\",
            )
            root.destroy()
            if escolhido:
                escolhido = os.path.abspath(escolhido)
                if os.path.basename(escolhido).lower() != NOME_APLICACAO.lower():
                    escolhido = os.path.join(escolhido, NOME_APLICACAO)
                self.destino_dir = escolhido
                self.editando_caminho = False
                ok, motivo = testar_permissao_escrita(self.destino_dir)
                self.mensagem_erro = "" if ok else motivo
        except Exception as exc:
            self.mensagem_erro = f"Seletor indisponível ({exc}). Edite o caminho na caixa."

    def iniciar_instalacao(self):
        if self.estado == "INSTALANDO":
            return False

        self.destino_dir = str(self.destino_dir or "").strip() or CAMINHO_INSTALACAO_PADRAO
        ok_perm, msg_perm = testar_permissao_escrita(self.destino_dir)
        if not ok_perm:
            self.mensagem_erro = msg_perm
            return False

        tipo_fonte, caminho_fonte = self._localizar_fonte_instalacao()
        if not tipo_fonte:
            self.mensagem_erro = "Pacote de arquivos não encontrado. Execute build_tudo.bat antes."
            self.estado = "ERRO"
            return False

        self.mensagem_erro = ""
        self.estado = "INSTALANDO"
        self.progresso = 0.03
        self.arquivos_processados = 0
        self.arquivos_totais = 1
        self.atalhos_criados = []
        self._sino_tocado = False
        self._pronto_concluir = False
        self._concluindo_pausa = 0.0
        self.mensagem_status = "Copiando cenários..."

        self._thread = threading.Thread(
            target=self._executar_instalacao_worker,
            args=(tipo_fonte, caminho_fonte),
            daemon=True,
        )
        self._thread.start()
        return True

    def _status_por_progresso(self, frac):
        if frac < 0.30:
            return "Copiando cenários..."
        if frac < 0.62:
            return "Configurando texturas..."
        if frac < 0.88:
            return "Preparando sprites e áudio..."
        return "Registrando atalhos..."

    def _executar_instalacao_worker(self, tipo_fonte, caminho_fonte):
        destino_abs = os.path.abspath(self.destino_dir)
        try:
            os.makedirs(destino_abs, exist_ok=True)
            if tipo_fonte == "zip":
                with zipfile.ZipFile(caminho_fonte, "r") as zf:
                    membros = [m for m in zf.infolist() if not m.is_dir()]
                    total = max(1, len(membros))
                    with self._lock:
                        self.arquivos_totais = total

                    for idx, info in enumerate(membros, start=1):
                        rel_norm = os.path.normpath(info.filename).lstrip("\\/")
                        alvo_arquivo = os.path.abspath(os.path.join(destino_abs, rel_norm))
                        if not (alvo_arquivo == destino_abs or alvo_arquivo.startswith(destino_abs + os.sep)):
                            continue
                        os.makedirs(os.path.dirname(alvo_arquivo), exist_ok=True)
                        with zf.open(info, "r") as src, open(alvo_arquivo, "wb") as dst:
                            shutil.copyfileobj(src, dst, length=1024 * 128)

                        frac = 0.05 + 0.84 * (idx / float(total))
                        with self._lock:
                            self.arquivos_processados = idx
                            self.progresso = frac
                            self.mensagem_status = self._status_por_progresso(frac)
            else:
                lista_arqs = []
                for raiz, _, arqs in os.walk(caminho_fonte):
                    for arq in arqs:
                        lista_arqs.append(os.path.join(raiz, arq))
                total = max(1, len(lista_arqs))
                with self._lock:
                    self.arquivos_totais = total

                for idx, orig in enumerate(lista_arqs, start=1):
                    rel = os.path.relpath(orig, caminho_fonte)
                    alvo_arquivo = os.path.join(destino_abs, rel)
                    os.makedirs(os.path.dirname(alvo_arquivo), exist_ok=True)
                    shutil.copy2(orig, alvo_arquivo)
                    frac = 0.05 + 0.84 * (idx / float(total))
                    with self._lock:
                        self.arquivos_processados = idx
                        self.progresso = frac
                        self.mensagem_status = self._status_por_progresso(frac)

            with self._lock:
                self.progresso = 0.93
                self.mensagem_status = "Registrando atalhos..."

            exe_destino = os.path.join(destino_abs, NOME_EXECUTAVEL)
            ico_cand_1 = os.path.join(destino_abs, "assets", "icone_jogo.ico")
            ico_cand_2 = os.path.join(destino_abs, "_internal", "assets", "icone_jogo.ico")
            ico_cand_3 = os.path.join(destino_abs, "icon.ico")
            icone_destino = next((p for p in (ico_cand_1, ico_cand_2, ico_cand_3) if os.path.exists(p)), "")

            criados = []
            if os.path.exists(exe_destino):
                if self.criar_atalho_desktop:
                    lnk_desk = os.path.join(obter_desktop_usuario(), f"{NOME_APLICACAO}.lnk")
                    ok_d, _ = criar_atalho(exe_destino, lnk_desk, icone_destino, pasta_trabalho=destino_abs)
                    if ok_d:
                        criados.append("Área de Trabalho")

                if self.criar_atalho_menu_iniciar:
                    pasta_menu = os.path.join(obter_menu_iniciar_programas(), NOME_APLICACAO)
                    lnk_menu = os.path.join(pasta_menu, f"{NOME_APLICACAO}.lnk")
                    ok_m, _ = criar_atalho(exe_destino, lnk_menu, icone_destino, pasta_trabalho=destino_abs)
                    if ok_m:
                        criados.append("Menu Iniciar")

            with self._lock:
                self.atalhos_criados = criados
                self.progresso = 1.0
                self.mensagem_status = "Instalação finalizada com êxito!"
                self._pronto_concluir = True
        except PermissionError:
            with self._lock:
                self.mensagem_erro = "Permissão de escrita negada durante a cópia. Escolha outra pasta."
                self.estado = "ERRO"
        except Exception as exc:
            with self._lock:
                self.mensagem_erro = f"Falha na instalação: {exc}"
                self.estado = "ERRO"

    def executar_jogo_instalado(self):
        exe_destino = os.path.join(os.path.abspath(self.destino_dir), NOME_EXECUTAVEL)
        if os.path.isfile(exe_destino):
            try:
                if self.audio is not None:
                    self.audio.encerrar()
                subprocess.Popen([exe_destino], cwd=os.path.dirname(exe_destino))
                self._pedir_fechar = True
                return True
            except Exception as exc:
                self.mensagem_erro = f"Não foi possível iniciar o jogo: {exc}"
        else:
            self.mensagem_erro = f"Executável não encontrado em '{exe_destino}'."
        return False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            if self.estado != "INSTALANDO":
                self._pedir_fechar = True
            return

        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_m and not self.editando_caminho and self.audio is not None:
                self.audio.alternar_mudo()
                return

            if self.estado == "BOAS_VINDAS":
                if k == pygame.K_ESCAPE:
                    self._click_som()
                    self._pedir_fechar = True
                elif k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                    self._click_som()
                    self.foco_btn = 1 - self.foco_btn
                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._click_som()
                    if self.foco_btn == 1:
                        self.estado = "CONFIG"
                        self.foco_btn = 1
                    else:
                        self._pedir_fechar = True

            elif self.estado == "CONFIG":
                if self.editando_caminho:
                    if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                        self.editando_caminho = False
                        self._click_som()
                    elif k == pygame.K_BACKSPACE:
                        self.destino_dir = self.destino_dir[:-1]
                    elif event.unicode and ord(event.unicode) >= 32 and len(self.destino_dir) < 120:
                        if event.unicode not in '<>"|?*':
                            self.destino_dir += event.unicode
                    return

                if k == pygame.K_ESCAPE:
                    self._click_som()
                    self.estado = "BOAS_VINDAS"
                    self.foco_btn = 1
                elif k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                    self._click_som()
                    self.foco_btn = 1 - self.foco_btn
                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._click_som()
                    if self.foco_btn == 1:
                        self.iniciar_instalacao()
                    else:
                        self.estado = "BOAS_VINDAS"
                        self.foco_btn = 1

            elif self.estado == "CONCLUIDO":
                if k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                    self._click_som()
                    self.foco_btn = 1 - self.foco_btn
                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._click_som()
                    if self.foco_btn == 1:
                        self.executar_jogo_instalado()
                    else:
                        self._pedir_fechar = True
                elif k == pygame.K_ESCAPE:
                    self._click_som()
                    self._pedir_fechar = True

            elif self.estado == "ERRO":
                if k in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._click_som()
                    self.estado = "CONFIG"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.rect_btn_som.collidepoint(pos) and self.audio is not None:
                self._click_som()
                self.audio.alternar_mudo()
                return

            if self.estado == "BOAS_VINDAS":
                if self.rect_btn_cancelar.collidepoint(pos):
                    self._click_som()
                    self._pedir_fechar = True
                elif self.rect_btn_avancar.collidepoint(pos):
                    self._click_som()
                    self.estado = "CONFIG"
                    self.foco_btn = 1

            elif self.estado == "CONFIG":
                if self.rect_caixa_dir.collidepoint(pos):
                    self._click_som()
                    self.editando_caminho = True
                    return
                self.editando_caminho = False

                if self.rect_btn_procurar.collidepoint(pos):
                    self._click_som()
                    self.selecionar_diretorio_dialogo()
                elif self.rect_btn_pasta_user.width > 0 and self.rect_btn_pasta_user.collidepoint(pos):
                    self._click_som()
                    self.destino_dir = obter_pasta_usuario_fallback()
                    ok, motivo = testar_permissao_escrita(self.destino_dir)
                    self.mensagem_erro = "" if ok else motivo
                elif self.rect_chk_desktop.collidepoint(pos):
                    self._click_som()
                    self.criar_atalho_desktop = not self.criar_atalho_desktop
                elif self.rect_chk_menu.collidepoint(pos):
                    self._click_som()
                    self.criar_atalho_menu_iniciar = not self.criar_atalho_menu_iniciar
                elif self.rect_chk_exec.collidepoint(pos):
                    self._click_som()
                    self.executar_apos_instalar = not self.executar_apos_instalar
                elif self.rect_btn_voltar.collidepoint(pos):
                    self._click_som()
                    self.estado = "BOAS_VINDAS"
                    self.foco_btn = 1
                elif self.rect_btn_instalar.collidepoint(pos):
                    self._click_som()
                    self.iniciar_instalacao()

            elif self.estado == "CONCLUIDO":
                if self.rect_btn_jogar.collidepoint(pos):
                    self._click_som()
                    self.executar_jogo_instalado()
                elif self.rect_btn_fechar.collidepoint(pos):
                    self._click_som()
                    self._pedir_fechar = True

            elif self.estado == "ERRO":
                if self.rect_btn_fechar.collidepoint(pos):
                    self._click_som()
                    self.estado = "CONFIG"

    def update(self, dt):
        self.tempo += dt
        self.fundo_vivo.update(dt)

        with self._lock:
            pronto = self._pronto_concluir
            em_inst = (self.estado == "INSTALANDO")

        if em_inst and pronto:
            if not self._sino_tocado:
                self._sino_tocado = True
                if self.audio is not None:
                    self.audio.tocar_sino()
            self._concluindo_pausa += dt
            if self._concluindo_pausa >= 0.45:
                with self._lock:
                    self.estado = "CONCLUIDO"
                    self.foco_btn = 1

    def _desenhar_pilula_cabecalho(self, surface, rect, texto, fonte, cor_bg, cor_borda, cor_texto):
        pygame.draw.rect(surface, cor_bg, rect, border_radius=3)
        pygame.draw.rect(surface, cor_borda, rect, 1, border_radius=3)
        s = fonte.render(texto, True, cor_texto)
        surface.blit(s, (rect.centerx - s.get_width() // 2, rect.centery - s.get_height() // 2))

    def _desenhar_checkbox(self, surface, x, y, marcado, texto, fonte):
        box = pygame.Rect(x, y, 20, 20)
        ui_procedural.desenhar_moldura_gotica(
            surface, box, chanfro=3, destacado=marcado, alpha=245, borda_ouro=marcado, cantoneiras=False
        )
        if marcado:
            pts = [(box.left + 4, box.centery + 1), (box.left + 8, box.bottom - 5), (box.right - 4, box.top + 5)]
            pygame.draw.lines(surface, ui_procedural.COR_AZUL_ETER, False, pts, 3)
        lbl = fonte.render(texto, True, ui_procedural.COR_BRANCO_PEROLA if marcado else ui_procedural.COR_CINZA_TEXTO)
        surface.blit(lbl, (box.right + 12, box.centery - lbl.get_height() // 2))
        return pygame.Rect(box.left, box.top - 2, box.width + 14 + lbl.get_width(), 24)

    def draw(self, surface):
        # 1) Cenário vivo ao fundo fora e atrás do cartão central
        self.fundo_vivo.draw(surface, self.tempo)

        # 2) Cartão central estilo referência (centralizado com margem para o cenário vivo)
        card_w, card_h = 668, 434
        card_x = (LARGURA_JANELA - card_w) // 2
        card_y = (ALTURA_JANELA - card_h) // 2
        painel = pygame.Rect(card_x, card_y, card_w, card_h)

        # Sombra externa do cartão sobre o cenário vivo
        s_somb = pygame.Surface((card_w + 18, card_h + 18), pygame.SRCALPHA)
        pygame.draw.rect(s_somb, (0, 0, 0, 145), (0, 0, card_w + 18, card_h + 18), border_radius=12)
        surface.blit(s_somb, (card_x - 9, card_y - 6))

        ui_procedural.desenhar_moldura_gotica(
            surface, painel, chanfro=9, destacado=True, alpha=245,
            borda_ouro=True, cantoneiras=True, cranios=True
        )

        f_tit = ui_procedural.obter_fonte_serif(34, bold=True)
        f_subtit = ui_procedural.obter_fonte_serif(18, bold=True)
        f_txt = ui_procedural.obter_fonte_serif(13, bold=False)
        f_lbl = ui_procedural.obter_fonte_serif(13, bold=True)
        f_btn = ui_procedural.obter_fonte_serif(14, bold=True)
        f_micro = ui_procedural.obter_fonte_serif(11, bold=True)
        f_pct = ui_procedural.obter_fonte_serif(34, bold=True)

        cx = LARGURA_JANELA // 2

        # Título monumental + 2 pílulas superiores (Versão e Música) + linha dupla divisória
        t_logo = f_tit.render("ELOS DO VAZIO", True, ui_procedural.COR_OURO_VIVO)
        t_logo_s = f_tit.render("ELOS DO VAZIO", True, (6, 8, 12))
        surface.blit(t_logo_s, (cx - t_logo.get_width() // 2 + 2, card_y + 20))
        surface.blit(t_logo, (cx - t_logo.get_width() // 2, card_y + 18))

        r_ver = pygame.Rect(cx - 210, card_y + 66, 200, 22)
        self._desenhar_pilula_cabecalho(
            surface, r_ver, VERSAO_APLICACAO, f_micro,
            (28, 30, 48), ui_procedural.COR_METAL_BORDA, ui_procedural.COR_CINZA_TEXTO
        )

        mudo = self.audio.mudo if self.audio else True
        self.rect_btn_som = pygame.Rect(cx + 8, card_y + 66, 198, 22)
        self._desenhar_pilula_cabecalho(
            surface,
            self.rect_btn_som,
            "MÚSICA: DESLIGADA" if mudo else "MÚSICA: LIGADA",
            f_micro,
            (34, 24, 30) if mudo else (22, 42, 34),
            ui_procedural.COR_METAL_BORDA if mudo else ui_procedural.COR_ESMERALDA_VIDA,
            ui_procedural.COR_CINZA_TEXTO if mudo else ui_procedural.COR_OURO_VIVO,
        )

        ui_procedural.desenhar_divisor_dourado(surface, card_x + 28, card_y + 100, card_w - 56)

        mpos = pygame.mouse.get_pos()

        with self._lock:
            est = self.estado
            prog = float(self.progresso)
            msg_st = self.mensagem_status
            msg_err = self.mensagem_erro
            atalhos_ok = list(self.atalhos_criados)

        btn_y = card_y + card_h - 68
        btn_w = 244
        btn_h = 44

        if est == "BOAS_VINDAS":
            s_bv = f_subtit.render("BEM-VINDO À EXPEDIÇÃO DO VAZIO!", True, ui_procedural.COR_BRANCO_PEROLA)
            surface.blit(s_bv, (cx - s_bv.get_width() // 2, card_y + 116))

            linhas = [
                "Prepare a espada, a Esquiva Rasteira e o Salto com Pogo nas ruínas.",
                "Este assistente instalará a versão mais recente (Solo) no computador.",
                "Com o jogo instalado, você pode iniciar pelo atalho ou pelo menu.",
                "A música ambiente foi ligada — fique à vontade para escolher!",
            ]
            for i_l, lin in enumerate(linhas):
                sl = f_txt.render(lin, True, ui_procedural.COR_CINZA_TEXTO)
                surface.blit(sl, (cx - sl.get_width() // 2, card_y + 154 + i_l * 26))

            caixa_info = pygame.Rect(card_x + 56, card_y + 272, card_w - 112, 62)
            ui_procedural.desenhar_moldura_gotica(surface, caixa_info, chanfro=5, destacado=False, alpha=232, cantoneiras=False)
            l1 = f_micro.render(
                f"Espaço livre necessário: ~{self.tamanho_estimado_mb} MB   |   Sistema: Windows 10/11",
                True, ui_procedural.COR_OURO_VIVO
            )
            l2 = f_txt.render(
                "O instalador grava cenários góticos, sprites, áudio e atalhos oficiais.",
                True, ui_procedural.COR_BRANCO_PEROLA
            )
            surface.blit(l1, (cx - l1.get_width() // 2, caixa_info.top + 12))
            surface.blit(l2, (cx - l2.get_width() // 2, caixa_info.top + 34))

            self.rect_btn_cancelar = pygame.Rect(card_x + 42, btn_y, btn_w, btn_h)
            self.rect_btn_avancar = pygame.Rect(card_x + card_w - 42 - btn_w, btn_y, btn_w, btn_h)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_cancelar, "CANCELAR", f_btn, selecionado=False)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_avancar, "AVANÇAR >", f_btn, selecionado=True, icone="espada")

        elif est == "CONFIG":
            s_cfg = f_subtit.render("ONDE ERGUER O SANTUÁRIO?", True, ui_procedural.COR_BRANCO_PEROLA)
            surface.blit(s_cfg, (cx - s_cfg.get_width() // 2, card_y + 114))

            surface.blit(f_lbl.render("Pasta de Instalação:", True, ui_procedural.COR_OURO_VIVO), (card_x + 36, card_y + 148))

            self.rect_caixa_dir = pygame.Rect(card_x + 36, card_y + 172, card_w - 208, 38)
            ui_procedural.desenhar_moldura_gotica(
                surface, self.rect_caixa_dir, chanfro=4, destacado=self.editando_caminho,
                alpha=250, borda_ouro=self.editando_caminho, cantoneiras=False
            )
            cursor = "|" if (self.editando_caminho and int(self.tempo * 2.5) % 2 == 0) else ""
            s_dir = f_txt.render(_abreviar_caminho(self.destino_dir, 50) + cursor, True, ui_procedural.COR_BRANCO_PEROLA)
            surface.blit(s_dir, (self.rect_caixa_dir.left + 12, self.rect_caixa_dir.centery - s_dir.get_height() // 2))

            self.rect_btn_procurar = pygame.Rect(self.rect_caixa_dir.right + 12, card_y + 172, 124, 38)
            ui_procedural.desenhar_botao_gotico(
                surface, self.rect_btn_procurar, "PROCURAR...", f_micro,
                selecionado=self.rect_btn_procurar.collidepoint(mpos), icone="grade"
            )

            self.rect_chk_desktop = self._desenhar_checkbox(
                surface, card_x + 36, card_y + 228, self.criar_atalho_desktop, "Criar atalho na Área de Trabalho", f_txt
            )
            self.rect_chk_menu = self._desenhar_checkbox(
                surface, card_x + 36, card_y + 260, self.criar_atalho_menu_iniciar, "Criar atalho no Menu Iniciar", f_txt
            )
            self.rect_chk_exec = self._desenhar_checkbox(
                surface, card_x + 36, card_y + 292, self.executar_apos_instalar, "Executar o jogo após instalar", f_txt
            )

            self.rect_btn_pasta_user = pygame.Rect(0, 0, 0, 0)
            if msg_err:
                s_err = f_micro.render(msg_err[:64], True, ui_procedural.COR_VERMELHO_DANO)
                surface.blit(s_err, (card_x + 36, card_y + 328))
                self.rect_btn_pasta_user = pygame.Rect(card_x + card_w - 196, card_y + 322, 160, 24)
                self._desenhar_pilula_cabecalho(
                    surface, self.rect_btn_pasta_user, "Usar Pasta do Usuário",
                    f_micro, (32, 34, 52), ui_procedural.COR_OURO_BRILHO, ui_procedural.COR_OURO_VIVO
                )

            self.rect_btn_voltar = pygame.Rect(card_x + 42, btn_y, btn_w, btn_h)
            self.rect_btn_instalar = pygame.Rect(card_x + card_w - 42 - btn_w, btn_y, btn_w, btn_h)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_voltar, "< VOLTAR", f_btn, selecionado=False)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_instalar, "INSTALAR AGORA", f_btn, selecionado=True, icone="espada")

        elif est == "INSTALANDO":
            s_prep = f_subtit.render("FORJANDO A CIDADELA...", True, ui_procedural.COR_BRANCO_PEROLA)
            surface.blit(s_prep, (cx - s_prep.get_width() // 2, card_y + 136))

            bar_w, bar_h = card_w - 108, 28
            bar_x = cx - bar_w // 2
            bar_y = card_y + 206
            pct = max(0, min(100, int(round(prog * 100))))

            # Barra segmentada em ciano de Éter (#38BDF8) + cristal/espada à esquerda igual ao vídeo
            ui_procedural.desenhar_barra_segmentada(
                surface, bar_x, bar_y, bar_w, bar_h,
                atual=pct, maximo=100, segmentos=26,
                cor_ativo=ui_procedural.COR_AZUL_ETER, tipo="eter"
            )
            ui_procedural.desenhar_icone_tematico(surface, "espada", bar_x - 2, bar_y + bar_h // 2, tamanho=30, aceso=True)

            s_pct = f_pct.render(f"{pct}%", True, ui_procedural.COR_OURO_VIVO)
            s_pct_s = f_pct.render(f"{pct}%", True, (6, 8, 12))
            surface.blit(s_pct_s, (cx - s_pct.get_width() // 2 + 1, bar_y + 53))
            surface.blit(s_pct, (cx - s_pct.get_width() // 2, bar_y + 52))

            s_st = f_txt.render(msg_st, True, ui_procedural.COR_AZUL_ETER_CLARO)
            surface.blit(s_st, (cx - s_st.get_width() // 2, bar_y + 102))

        elif est == "CONCLUIDO":
            f_concl = ui_procedural.obter_fonte_serif(27, bold=True)
            s_ok = f_concl.render("INSTALAÇÃO CONCLUÍDA!", True, ui_procedural.COR_OURO_BRILHO)
            s_ok_s = f_concl.render("INSTALAÇÃO CONCLUÍDA!", True, (6, 8, 12))
            surface.blit(s_ok_s, (cx - s_ok.get_width() // 2 + 1, card_y + 122))
            surface.blit(s_ok, (cx - s_ok.get_width() // 2, card_y + 120))

            s_sub_ok = f_txt.render("Elos do Vazio foi instalado com sucesso!", True, ui_procedural.COR_BRANCO_PEROLA)
            surface.blit(s_sub_ok, (cx - s_sub_ok.get_width() // 2, card_y + 168))

            box_fin = pygame.Rect(card_x + 76, card_y + 206, card_w - 152, 118)
            ui_procedural.desenhar_moldura_gotica(surface, box_fin, chanfro=6, destacado=False, alpha=234, cantoneiras=False)
            atalho_txt = ", ".join(atalhos_ok) if atalhos_ok else "Sem atalhos adicionais"
            f_lin = [
                ("Você já pode começar sua jornada pelo botão abaixo.", ui_procedural.COR_BRANCO_PEROLA),
                ("Use o teclado ou controle e domine a lâmina e o Éter!", ui_procedural.COR_CINZA_TEXTO),
                (f"Pasta: {_abreviar_caminho(self.destino_dir, 46)}  |  {atalho_txt}", ui_procedural.COR_OURO_VIVO),
            ]
            for i_f, (txt_f, cor_f) in enumerate(f_lin):
                sf = f_micro.render(txt_f, True, cor_f)
                surface.blit(sf, (cx - sf.get_width() // 2, box_fin.top + 18 + i_f * 28))

            self.rect_btn_fechar = pygame.Rect(card_x + 42, btn_y, btn_w, btn_h)
            self.rect_btn_jogar = pygame.Rect(card_x + card_w - 42 - btn_w, btn_y, btn_w, btn_h)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_fechar, "FECHAR", f_btn, selecionado=False)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_jogar, "JOGAR AGORA", f_btn, selecionado=True, icone="espada")

        elif est == "ERRO":
            s_err_t = f_subtit.render("FALHA NA INSTALAÇÃO", True, ui_procedural.COR_VERMELHO_DANO)
            surface.blit(s_err_t, (cx - s_err_t.get_width() // 2, card_y + 132))
            box_e = pygame.Rect(card_x + 52, card_y + 186, card_w - 104, 118)
            ui_procedural.desenhar_moldura_gotica(surface, box_e, chanfro=6, destacado=False, alpha=238, cantoneiras=False)
            s_m = f_txt.render(msg_err[:68], True, ui_procedural.COR_BRANCO_PEROLA)
            surface.blit(s_m, (cx - s_m.get_width() // 2, box_e.centery - s_m.get_height() // 2))
            self.rect_btn_fechar = pygame.Rect(cx - btn_w // 2, btn_y, btn_w, btn_h)
            ui_procedural.desenhar_botao_gotico(surface, self.rect_btn_fechar, "< VOLTAR", f_btn, selecionado=True, icone="grade")


def main():
    pygame.init()
    audio_ctrl = AudioInstalador()
    tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
    pygame.display.set_caption("Instalador — Elos do Vazio")
    for ico_cand in ("assets/icone_jogo.ico", "icon.ico", "assets/ui/logo_elos_do_vazio.png"):
        ico_p = resource_path(ico_cand)
        if os.path.exists(ico_p):
            try:
                pygame.display.set_icon(pygame.image.load(ico_p))
                break
            except Exception:
                pass

    app = InstaladorApp(audio_ctrl=audio_ctrl)
    relogio = pygame.time.Clock()

    while not app._pedir_fechar:
        dt = min(0.05, relogio.tick(60) / 1000.0)
        for event in pygame.event.get():
            app.handle_event(event)
        app.update(dt)
        app.draw(tela)
        pygame.display.flip()

    audio_ctrl.encerrar()
    pygame.quit()


if __name__ == "__main__":
    main()
