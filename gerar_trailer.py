# -*- coding: utf-8 -*-
"""
Gerador do Trailer Oficial de Lançamento — Elos do Vazio (`gerar_trailer.py`).

Compõe, simula e exporta um trailer cinematográfico Dark Fantasy em MP4 Full HD
(1920x1080 @ 60 FPS, H.264 + AAC estéreo, duração 45s) na raiz do projeto
(`trailer_elos_do_vazio.mp4`), reutilizando os cenários reais das 7 salas
(`cenarios.py`, `cenario_combate_25d.py`), animações (`sprites.py`), logos
oficiais (GoZygrid Studios e Elos do Vazio) e trilha + efeitos sonoros locais.
"""

import argparse
import glob
import io
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import wave
import zipfile


RAIZ = os.path.dirname(os.path.abspath(__file__))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

LARGURA_VIDEO = 1920
ALTURA_VIDEO = 1080
FPS_VIDEO = 60
DURACAO_TOTAL = 45.0
TAXA_AUDIO = 44100
SAIDA_PADRAO = os.path.join(RAIZ, "trailer_elos_do_vazio.mp4")


def garantir_dependencias(permitir_instalar=True):
    """Verifica e instala dependências multimídia necessárias se faltarem."""
    pacotes_modulos = [
        ("pygame", "pygame-ce"),
        ("numpy", "numpy"),
        ("PIL", "pillow"),
        ("imageio_ffmpeg", "imageio-ffmpeg"),
    ]
    faltantes = []
    for mod, pkg in pacotes_modulos:
        try:
            __import__(mod)
        except ImportError:
            faltantes.append(pkg)

    if faltantes and permitir_instalar:
        print(f"[trailer] Instalando dependências essenciais: {', '.join(faltantes)} ...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *faltantes])
        except Exception as exc:
            print(f"[trailer] Aviso ao instalar via pip ({exc}). Tentando prosseguir com recursos disponíveis.")

    try:
        __import__("moviepy")
    except ImportError:
        if permitir_instalar and shutil.which("ffmpeg") is None:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy"])
            except Exception:
                pass

    # Garante execução headless estável caso não exista janela gráfica ativa
    if not os.environ.get("SDL_VIDEODRIVER"):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    if not os.environ.get("SDL_AUDIODRIVER"):
        os.environ["SDL_AUDIODRIVER"] = "dummy"


# ==============================================================================
# 1. CARREGADORES DE IMAGENS, LOGOS, SPRITES E ASSETS DO PROJETO
# ==============================================================================
def _abrir_pil_candidatos(caminhos, zip_alvo=None):
    from PIL import Image as PILImage

    for cand in caminhos:
        p_abs = cand if os.path.isabs(cand) else os.path.join(RAIZ, cand)
        if os.path.isfile(p_abs):
            try:
                return PILImage.open(p_abs).convert("RGBA")
            except Exception:
                pass

    if zip_alvo:
        alvo_l = zip_alvo.lower()
        for pad in (
            os.path.join(RAIZ, "Legacy-Dungeon*.zip"),
            os.path.join(RAIZ, "assets", "Legacy-Dungeon*.zip"),
            os.path.join(RAIZ, "*.zip"),
        ):
            for zp in glob.glob(pad):
                if "legacy" not in os.path.basename(zp).lower():
                    continue
                try:
                    with zipfile.ZipFile(zp, "r") as zf:
                        matches = [n for n in zf.namelist() if n.lower().endswith("/" + alvo_l) or n.lower() == alvo_l]
                        if matches:
                            matches.sort(key=lambda s: (0 if "final/assets" in s.lower() else 1, len(s)))
                            return PILImage.open(io.BytesIO(zf.read(matches[0]))).convert("RGBA")
                except Exception:
                    pass
    return None


def _pil_para_surface(pil_img, max_w=None, max_h=None):
    import pygame
    from PIL import Image as PILImage

    if pil_img is None:
        return None
    img = pil_img.convert("RGBA")
    if max_w and max_h:
        esc = min(max_w / float(max(1, img.width)), max_h / float(max(1, img.height)))
        nw = max(1, int(round(img.width * esc)))
        nh = max(1, int(round(img.height * esc)))
        if (nw, nh) != img.size:
            img = img.resize((nw, nh), PILImage.Resampling.LANCZOS)
    raw = img.tobytes()
    surf = pygame.image.frombytes(raw, img.size, "RGBA")
    if pygame.display.get_surface() is not None:
        try:
            surf = surf.convert_alpha()
        except pygame.error:
            pass
    return surf


def _suavizar_fundo_escuro_logo(pil_img):
    """Remove suavemente borda escura sólida da logo JPEG/JFIF para fusão limpa em Dark Fantasy."""
    import numpy as np
    from PIL import Image as PILImage

    if pil_img is None:
        return None
    arr = np.array(pil_img.convert("RGBA"), dtype=np.float32)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    # Torna transparentes os pixels quase pretos fora do emblema com transição suave
    alpha_mask = np.clip((lum - 24.0) / 28.0, 0.0, 1.0) * 255.0
    arr[..., 3] = np.minimum(arr[..., 3], alpha_mask)
    out = PILImage.fromarray(arr.astype(np.uint8), mode="RGBA")
    bbox = out.split()[-1].getbbox()
    if bbox:
        pad = 10
        out = out.crop((
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(out.width, bbox[2] + pad),
            min(out.height, bbox[3] + pad),
        ))
    return out


def _desenhar_logo_gozygrid_vetorial(w=620, h=360):
    import pygame

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, int(h * 0.42)
    r = int(min(w, h) * 0.27)
    pts = [(cx + r * math.cos(math.radians(60 * k - 90)), cy + r * math.sin(math.radians(60 * k - 90))) for k in range(6)]
    pygame.draw.polygon(surf, (13, 19, 34, 240), pts)
    pygame.draw.polygon(surf, (217, 119, 6, 255), pts, 6)
    pygame.draw.polygon(surf, (56, 189, 248, 200), [
        (cx + (r - 12) * math.cos(math.radians(60 * k - 90)), cy + (r - 12) * math.sin(math.radians(60 * k - 90)))
        for k in range(6)
    ], 2)

    f_z = pygame.font.SysFont("georgia", int(r * 1.15), bold=True)
    s_z = f_z.render("Z", True, (253, 230, 138))
    surf.blit(s_z, (cx - s_z.get_width() // 2, cy - s_z.get_height() // 2 - 4))

    f_tit = pygame.font.SysFont("georgia", 46, bold=True)
    f_sub = pygame.font.SysFont("arial", 22, bold=True)
    t_g = f_tit.render("GoZygrid", True, (253, 230, 138))
    t_s = f_sub.render("S T U D I O S", True, (203, 213, 225))
    surf.blit(t_g, (cx - t_g.get_width() // 2, cy + r + 16))
    surf.blit(t_s, (cx - t_s.get_width() // 2, cy + r + 70))
    return surf


def _desenhar_logo_jogo_vetorial(w=980, h=260):
    import pygame

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (13, 18, 32, 230), (14, 14, w - 28, h - 28), border_radius=12)
    pygame.draw.rect(surf, (217, 119, 6, 255), (14, 14, w - 28, h - 28), 4, border_radius=12)
    pygame.draw.rect(surf, (146, 64, 14, 220), (24, 24, w - 48, h - 48), 2, border_radius=8)

    f_tit = pygame.font.SysFont("georgia", 86, bold=True)
    f_sub = pygame.font.SysFont("georgia", 24, bold=True)
    txt_s = f_tit.render("ELOS DO VAZIO", True, (8, 10, 16))
    txt_f = f_tit.render("ELOS DO VAZIO", True, (253, 230, 138))
    sub = f_sub.render("DARK FANTASY  •  AÇÃO E PLATAFORMA 2D", True, (56, 189, 248))
    cx, cy = w // 2, h // 2 - 14
    surf.blit(txt_s, (cx - txt_f.get_width() // 2 + 4, cy - txt_f.get_height() // 2 + 4))
    surf.blit(txt_f, (cx - txt_f.get_width() // 2, cy - txt_f.get_height() // 2))
    surf.blit(sub, (cx - sub.get_width() // 2, cy + txt_f.get_height() // 2 + 12))
    return surf


def carregar_logos():
    pil_studio = _abrir_pil_candidatos([
        "assets/logo_gozygrid.png",
        "assets/ui/logo_gozygrid.png",
        "assets/ui/logo_gozygrid_studios.jpg",
        "assets/logo_gozygrid.jpg",
        "assets/logo_gozygrid.jfif",
    ])
    if pil_studio is not None:
        surf_studio = _pil_para_surface(_suavizar_fundo_escuro_logo(pil_studio), 720, 440)
    else:
        surf_studio = _desenhar_logo_gozygrid_vetorial()

    pil_jogo = _abrir_pil_candidatos([
        "assets/logo_jogo.png",
        "assets/titulo_elos_do_vazio.png",
        "assets/ui/logo_elos_do_vazio.png",
    ])
    if pil_jogo is not None:
        surf_jogo = _pil_para_surface(pil_jogo, 1140, 380)
    else:
        surf_jogo = _desenhar_logo_jogo_vetorial()

    return surf_studio, surf_jogo


def _carregar_animador_seguro(candidatos, tint_rgba=None):
    """Usa `sprites.criar_animador` ou monta folha de `Character_Sprite_Sheet.png` / silhueta de emergência."""
    import pygame
    import sprites

    anim = sprites.criar_animador(candidatos)
    if anim.ativo and tint_rgba is None:
        return anim

    if anim.ativo and tint_rgba is not None and anim.personagem is not None:
        # Cria variante de cor isolada (ex: Jogador 2 no Cooperativo Local)
        import copy
        p_clone = copy.copy(anim.personagem)
        p_clone._cache = {}
        novas_anims = {}
        for k_anim, frames in anim.personagem.anims.items():
            lst = []
            for f in frames:
                fc = f.copy()
                tint = pygame.Surface(fc.get_size(), pygame.SRCALPHA)
                tint.fill(tint_rgba)
                fc.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                lst.append(fc)
            novas_anims[k_anim] = lst
        p_clone.anims = novas_anims
        return sprites.Animador(p_clone)

    # Tenta fatiar Character_Sprite_Sheet.png de Legacy-Dungeon se disponível
    pil_sheet = _abrir_pil_candidatos([
        "Final/Assets/Character_Sprite_Sheet.png",
        "assets/Character_Sprite_Sheet.png",
        "assets/final_pack/Character_Sprite_Sheet.png",
    ], zip_alvo="Character_Sprite_Sheet.png")
    if pil_sheet is not None:
        surf_sh = _pil_para_surface(pil_sheet)
        sw, sh = surf_sh.get_size()
        tam = 32 if sh >= 64 else sh
        cols = max(1, sw // tam)
        frames = [surf_sh.subsurface(pygame.Rect(c * tam, 0, tam, min(sh, tam))).copy() for c in range(min(6, cols))]
        p_fake = type("PersonagemFallback", (), {})()
        p_fake.nome = str(candidatos[0] if isinstance(candidatos, (list, tuple)) else candidatos)
        p_fake.anims = {"idle": frames[:2], "walk": frames, "attack": frames[:3], "dodge": frames[:2], "block": frames[:2]}
        p_fake.bbox = pygame.Rect(4, 2, tam - 8, tam - 4)
        p_fake._cache = {}
        p_fake.resolver = lambda n: n if n in p_fake.anims else "idle"

        def _quadro(a, idx, esc, esp):
            base = p_fake.anims[a][idx % len(p_fake.anims[a])]
            img = pygame.transform.scale(base, (max(1, int(base.get_width() * esc)), max(1, int(base.get_height() * esc))))
            if esp:
                img = pygame.transform.flip(img, True, False)
            return img, esc

        p_fake.quadro = _quadro
        return sprites.Animador(p_fake)

    # Fallback final procedural: silhueta gótica de guerreiro/monstro nunca retorna quadro vazio
    return sprites.Animador(None)


def _desenhar_combatente_fallback(surface, rect, cor_corpo=(148, 163, 184), atacando=False, espelhar=False, eter=False):
    import pygame

    d = -1 if espelhar else 1
    cx = rect.centerx
    pygame.draw.rect(surface, (10, 12, 20), rect.inflate(2, 2), border_radius=6)
    pygame.draw.rect(surface, cor_corpo, rect, border_radius=6)
    pygame.draw.circle(surface, (226, 232, 240), (cx + d * 4, rect.top + 10), 6)
    c_olho = (56, 189, 248) if eter else (251, 146, 60)
    pygame.draw.circle(surface, c_olho, (cx + d * 6, rect.top + 9), 2)
    p_mao = (cx + d * 10, rect.centery)
    p_ponta = (cx + d * (44 if atacando else 26), rect.centery - (14 if atacando else 18))
    pygame.draw.line(surface, (248, 250, 252) if not eter else (125, 211, 252), p_mao, p_ponta, 3)


# ==============================================================================
# 2. SISTEMA DE ÁUDIO ESTÉREO 44.1 kHz (MÚSICA + SFX SINCRONIZADOS NO COMPASSO)
# ==============================================================================
def _encontrar_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _decodificar_audio_ffmpeg(caminho, ffmpeg_exe, sr=TAXA_AUDIO):
    import numpy as np

    if not caminho or not os.path.isfile(caminho) or not ffmpeg_exe:
        return None
    try:
        cmd = [
            ffmpeg_exe, "-v", "error", "-i", caminho,
            "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(sr), "pipe:1",
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=25)
        if res.returncode == 0 and res.stdout:
            arr = np.frombuffer(res.stdout, dtype=np.float32)
            if len(arr) >= 2:
                return arr.reshape((-1, 2)).copy()
    except Exception:
        pass
    return None


def _sintetizar_trilha_orquestral_gotica(duracao=DURACAO_TOTAL, sr=TAXA_AUDIO):
    """Gera trilha orquestral Dark Fantasy em Ré Menor se nenhum `.ogg` externo for decodificado."""
    import numpy as np

    n = int(duracao * sr)
    t = np.arange(n, dtype=np.float32) / float(sr)
    audio = np.zeros((n, 2), dtype=np.float32)

    # Progressão épica Dm - Bb - C - Dm (compasso 0.5s / batida 120 BPM)
    acordes = [
        (73.42, 146.83, 220.00, 293.66, 349.23),
        (58.27, 116.54, 174.61, 233.08, 293.66),
        (65.41, 130.81, 196.00, 261.63, 329.63),
        (73.42, 146.83, 220.00, 261.63, 349.23),
    ]
    dur_bloco = 3.0
    for idx_b in range(int(math.ceil(duracao / dur_bloco))):
        i0 = int(idx_b * dur_bloco * sr)
        i1 = min(n, int((idx_b + 1) * dur_bloco * sr))
        if i0 >= i1:
            break
        tl = t[i0:i1] - idx_b * dur_bloco
        env = np.minimum(1.0, tl / 0.22) * np.minimum(1.0, (dur_bloco - tl) / 0.28 + 0.35)
        freqs = acordes[idx_b % len(acordes)]
        pad = np.zeros_like(tl)
        for fi, f in enumerate(freqs):
            peso = 0.28 if fi < 2 else 0.14
            pad += peso * np.sin(2.0 * math.pi * f * tl) + 0.04 * np.sin(2.0 * math.pi * f * 2.0 * tl)
        intensidade = 0.45 if t[i0] < 14.0 else (0.72 if t[i0] < 38.0 else 0.85)
        sig = pad * env * intensidade
        audio[i0:i1, 0] += sig * 0.96
        audio[i0:i1, 1] += sig * 1.04

    # Percussão orquestral de guerra nos atos de ação e combate (14s -> 37.5s)
    for beat_t in np.arange(14.0, 37.5, 0.5):
        i0 = int(beat_t * sr)
        dur_b = int(0.32 * sr)
        if i0 + dur_b >= n:
            break
        tb = np.arange(dur_b, dtype=np.float32) / float(sr)
        f_drop = 92.0 * np.exp(-tb * 14.0) + 42.0
        forte = 1.0 if int(round((beat_t - 14.0) * 2)) % 2 == 0 else 0.62
        drum = np.sin(2.0 * math.pi * f_drop * tb) * np.exp(-tb * 11.0) * 0.45 * forte
        audio[i0:i0 + dur_b, 0] += drum
        audio[i0:i0 + dur_b, 1] += drum

    return audio


def _sfx_sino_catedral(sr=TAXA_AUDIO, dur=2.8):
    import numpy as np

    t = np.arange(int(dur * sr), dtype=np.float32) / float(sr)
    parciais = ((146.83, 0.55, 1.2), (220.00, 0.32, 1.6), (293.66, 0.38, 2.0), (440.00, 0.16, 2.8), (587.33, 0.10, 3.8))
    sig = np.zeros_like(t)
    atk = np.minimum(1.0, t / 0.015)
    for freq, amp, dec in parciais:
        sig += amp * np.sin(2.0 * math.pi * freq * t) * np.exp(-t * dec)
    mono = sig * atk * 0.62
    return np.stack([mono * 0.95, mono * 1.05], axis=1)


def _sfx_corte_espada(sr=TAXA_AUDIO, dur=0.22):
    import numpy as np

    rng = np.random.default_rng(77)
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / float(sr)
    ruido = rng.normal(0.0, 1.0, n).astype(np.float32)
    env = np.minimum(1.0, t / 0.015) * np.exp(-t * 17.0)
    whoosh = ruido * env * 0.28 + np.sin(2.0 * math.pi * (880.0 - t * 2400.0) * t) * np.exp(-t * 22.0) * 0.35
    return np.stack([whoosh, whoosh * 0.92], axis=1)


def _sfx_parry_clash(sr=TAXA_AUDIO, dur=0.65):
    import numpy as np

    rng = np.random.default_rng(91)
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / float(sr)
    estouro = rng.normal(0.0, 1.0, n).astype(np.float32) * np.exp(-t * 48.0) * 0.50
    metais = (
        0.48 * np.sin(2.0 * math.pi * 1760.0 * t) * np.exp(-t * 8.5)
        + 0.36 * np.sin(2.0 * math.pi * 2489.0 * t) * np.exp(-t * 10.5)
        + 0.25 * np.sin(2.0 * math.pi * 3520.0 * t) * np.exp(-t * 14.0)
    )
    mono = (estouro + metais) * 0.72
    return np.stack([mono * 1.04, mono * 0.96], axis=1)


def _sfx_passo_pedra(sr=TAXA_AUDIO, dur=0.09):
    import numpy as np

    rng = np.random.default_rng(13)
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / float(sr)
    click = rng.normal(0.0, 1.0, n).astype(np.float32) * np.exp(-t * 68.0) * 0.16
    thud = np.sin(2.0 * math.pi * 115.0 * t) * np.exp(-t * 42.0) * 0.18
    mono = click + thud
    return np.stack([mono, mono], axis=1)


def _sfx_estrondo_portao(sr=TAXA_AUDIO, dur=1.6):
    import numpy as np

    rng = np.random.default_rng(42)
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / float(sr)
    sub = np.sin(2.0 * math.pi * (62.0 - t * 14.0) * t) * np.exp(-t * 2.2) * 0.55
    corrente = rng.normal(0.0, 1.0, n).astype(np.float32) * np.exp(-t * 4.5) * (0.22 + 0.14 * np.sin(2.0 * math.pi * 18.0 * t))
    mono = (sub + corrente) * 0.70
    return np.stack([mono, mono], axis=1)


def construir_trilha_audio_wav(caminho_wav, ffmpeg_exe, duracao=DURACAO_TOTAL):
    """Monta trilha estéreo 44.1 kHz com tema de fundo + SFX reais e sintetizados sincronizados."""
    import numpy as np

    n_total = int(duracao * TAXA_AUDIO)
    mix = np.zeros((n_total, 2), dtype=np.float32)

    # 1) BGM prioritária: tema_instalador.ogg ou title/dungeon_theme.ogg
    bgm = None
    for rel_bgm in (
        os.path.join("assets", "sons", "tema_instalador.ogg"),
        os.path.join("assets", "sons", "tema_instalador.wav"),
        os.path.join("assets", "audio", "music", "dungeon_theme.ogg"),
        os.path.join("assets", "audio", "music", "title_theme.ogg"),
    ):
        bgm = _decodificar_audio_ffmpeg(os.path.join(RAIZ, rel_bgm), ffmpeg_exe)
        if bgm is not None and len(bgm) > TAXA_AUDIO:
            print(f"[audio] Trilha carregada: {rel_bgm}")
            break

    if bgm is None:
        print("[audio] Usando síntese orquestral Dark Fantasy procedural para a trilha.")
        bgm = _sintetizar_trilha_orquestral_gotica(duracao=duracao)
    else:
        # Repete ou recorta suavemente para preencher a duração exata do trailer
        reps = int(math.ceil(n_total / float(len(bgm))))
        bgm = np.tile(bgm, (reps, 1))[:n_total].copy()

    # Curva dinâmica de volume (crescendo nos atos de ação e clímax)
    t_ax = np.arange(n_total, dtype=np.float32) / float(TAXA_AUDIO)
    env_bgm = np.where(t_ax < 4.5, 0.42, np.where(t_ax < 14.0, 0.52, np.where(t_ax < 37.5, 0.62, 0.72)))
    fade_in = np.minimum(1.0, t_ax / 0.8)
    fade_out = np.minimum(1.0, np.maximum(0.0, (duracao - t_ax) / 1.4))
    mix += bgm * (env_bgm * fade_in * fade_out)[:, None]

    def _mixar(arr_fx, t_sec, ganho=1.0):
        if arr_fx is None or len(arr_fx) == 0:
            return
        i0 = max(0, int(t_sec * TAXA_AUDIO))
        i1 = min(n_total, i0 + len(arr_fx))
        if i1 > i0:
            mix[i0:i1] += arr_fx[: i1 - i0] * float(ganho)

    # Carrega SFX nativos do jogo quando presentes (mantendo síntese gótica complementar)
    sfx_cache = {}
    for nome_fx in ("parry", "sword_crit", "hit_enemy", "dodge", "boss_hit", "level_up", "shield"):
        p_fx = os.path.join(RAIZ, "assets", "audio", "sfx", f"{nome_fx}.ogg")
        sfx_cache[nome_fx] = _decodificar_audio_ffmpeg(p_fx, ffmpeg_exe)

    sino = _sfx_sino_catedral()
    corte = _sfx_corte_espada()
    clash = _sfx_parry_clash()
    passo = _sfx_passo_pedra()
    portao = _sfx_estrondo_portao()

    # Sincronização exata com os eventos visuais do roteiro (0s -> 45s):
    _mixar(sino, 0.35, 0.80)          # Ato 1: Sino da catedral com a logo GoZygrid Studios
    _mixar(portao, 4.50, 0.48)        # Cartão 1: Impacto grave rúnico
    for tp in (7.0, 7.35, 7.7, 8.05, 8.95, 11.1, 11.5, 12.8):
        _mixar(passo, tp, 0.72)       # Passos rápidos em cantaria nas Ameias/Torres

    _mixar(portao, 14.00, 0.52)       # Cartão 2: Impacto rúnico
    # Ato 3A: Combo 3 golpes + Esquiva
    for tc in (16.45, 16.95, 17.50):
        _mixar(sfx_cache.get("hit_enemy") if sfx_cache.get("hit_enemy") is not None else corte, tc, 0.78)
        _mixar(corte, tc - 0.04, 0.70)
    _mixar(sfx_cache.get("dodge") if sfx_cache.get("dodge") is not None else corte, 18.35, 0.85)

    # Ato 3B: Parry Perfeito (t=21.05s) + Contra-Ataque (t=21.75s)
    _mixar(sfx_cache.get("parry"), 21.05, 0.95)
    _mixar(clash, 21.05, 0.95)
    _mixar(sfx_cache.get("sword_crit") if sfx_cache.get("sword_crit") is not None else corte, 21.75, 0.90)
    _mixar(corte, 21.72, 0.80)

    # Ato 3C: Boss Rush golpes sincronizados
    for t_coop in (24.1, 24.55, 25.1, 25.6):
        _mixar(sfx_cache.get("hit_enemy") if sfx_cache.get("hit_enemy") is not None else corte, t_coop, 0.72)

    # Ato 4: Cartão + Portão colossal da Sala 7 + Ataque Aéreo de Clímax
    _mixar(portao, 26.50, 0.58)
    _mixar(portao, 29.00, 0.95)
    _mixar(sfx_cache.get("shield"), 29.35, 0.75)
    _mixar(corte, 35.80, 0.90)
    _mixar(sfx_cache.get("boss_hit"), 37.10, 1.05)
    _mixar(clash, 37.10, 0.85)
    _mixar(portao, 37.10, 0.95)

    # Ato 5: Encerramento com sino solene e brilho de Éter
    _mixar(sino, 37.60, 0.75)
    _mixar(sfx_cache.get("level_up"), 38.00, 0.65)

    # Soft-clipping limpo evitando saturação
    mix = np.tanh(mix * 0.92) * 0.90
    pcm = (np.clip(mix, -1.0, 1.0) * 32767.0).astype("<i2")

    with wave.open(caminho_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(TAXA_AUDIO)
        wf.writeframes(pcm.tobytes())


# ==============================================================================
# 3. MOTOR DE CENA, PARTÍCULAS, COMBATE E COREOGRAFIA DE GAMEPLAY REAL
# ==============================================================================
class MotorParticulasTrailer:
    """Partículas determinísticas de brasa, Éter, faíscas de aço, poeira e anéis de impacto."""

    def __init__(self):
        rng = random.Random(3311)
        self.ambiente_1080 = [
            {
                "x": rng.uniform(0, LARGURA_VIDEO),
                "y": rng.uniform(0, ALTURA_VIDEO),
                "vx": rng.uniform(-18, 22),
                "vy": rng.uniform(-42, -12),
                "raio": rng.choice((1, 2, 2, 3)),
                "fase": rng.uniform(0, math.tau),
                "tipo": "eter" if i % 3 == 0 else "brasa",
            }
            for i in range(68)
        ]
        self.faiscas_mundo = []
        self.arcos_espada = []
        self.ondas = []
        self.rastros_fantasma = []

    def emitir_faiscas(self, x, y, n=18, cores=((254, 240, 138), (249, 115, 22), (255, 255, 255)), vel=260.0):
        for i in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(vel * 0.35, vel * 1.15)
            self.faiscas_mundo.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd - 45.0,
                "vida": random.uniform(0.22, 0.55), "max_vida": 0.55,
                "cor": cores[i % len(cores)], "r": random.choice((2, 2, 3)),
            })

    def emitir_arco(self, cx, cy, dir_x=1, cor=(248, 250, 252), raio=54, dur=0.18):
        self.arcos_espada.append({
            "x": float(cx), "y": float(cy), "dir": 1 if dir_x >= 0 else -1,
            "cor": cor, "raio": raio, "vida": dur, "max_vida": dur,
        })

    def emitir_onda(self, cx, cy, cor=(56, 189, 248), raio_max=150, dur=0.40):
        self.ondas.append({
            "x": float(cx), "y": float(cy), "cor": cor,
            "raio_max": raio_max, "vida": dur, "max_vida": dur,
        })

    def emitir_fantasma(self, x, y, w, h, cor=(56, 189, 248)):
        self.rastros_fantasma.append({
            "x": float(x), "y": float(y), "w": int(w), "h": int(h),
            "cor": cor, "vida": 0.24, "max_vida": 0.24,
        })

    def limpar_mundo(self):
        self.faiscas_mundo.clear()
        self.arcos_espada.clear()
        self.ondas.clear()
        self.rastros_fantasma.clear()

    def atualizar(self, dt):
        for p in self.ambiente_1080:
            p["x"] = (p["x"] + p["vx"] * dt) % LARGURA_VIDEO
            p["y"] = (p["y"] + p["vy"] * dt) % ALTURA_VIDEO

        novas_f = []
        for f in self.faiscas_mundo:
            f["x"] += f["vx"] * dt
            f["y"] += f["vy"] * dt
            f["vy"] += 420.0 * dt
            f["vida"] -= dt
            if f["vida"] > 0:
                novas_f.append(f)
        self.faiscas_mundo = novas_f

        self.arcos_espada = [a for a in self.arcos_espada if self._dec(a, dt)]
        self.ondas = [o for o in self.ondas if self._dec(o, dt)]
        self.rastros_fantasma = [g for g in self.rastros_fantasma if self._dec(g, dt)]

    @staticmethod
    def _dec(item, dt):
        item["vida"] -= dt
        return item["vida"] > 0

    def desenhar_fx_mundo(self, surf_mundo, cam_x, cam_y):
        import pygame

        for g in self.rastros_fantasma:
            a = max(0, min(145, int(145 * (g["vida"] / g["max_vida"]))))
            sg = pygame.Surface((g["w"], g["h"]), pygame.SRCALPHA)
            pygame.draw.ellipse(sg, (*g["cor"], a), (0, 0, g["w"], g["h"]))
            surf_mundo.blit(sg, (int(g["x"] - cam_x), int(g["y"] - cam_y)))

        for arc in self.arcos_espada:
            prog = 1.0 - (arc["vida"] / arc["max_vida"])
            alpha = max(0, min(255, int(255 * (1.0 - prog))))
            r = arc["raio"]
            sa = pygame.Surface((r * 2 + 12, r * 2 + 12), pygame.SRCALPHA)
            rect_a = pygame.Rect(6, 6, r * 2, r * 2)
            ini, fim = (-0.9, 0.9) if arc["dir"] > 0 else (math.pi - 0.9, math.pi + 0.9)
            pygame.draw.arc(sa, (*arc["cor"], alpha), rect_a, ini, fim, 7)
            pygame.draw.arc(sa, (255, 255, 255, min(255, alpha)), rect_a.inflate(-10, -10), ini, fim, 3)
            surf_mundo.blit(sa, (int(arc["x"] - cam_x - r - 6), int(arc["y"] - cam_y - r - 6)))

        for o in self.ondas:
            prog = 1.0 - (o["vida"] / o["max_vida"])
            r = max(4, int(o["raio_max"] * prog))
            alpha = max(0, min(240, int(240 * (1.0 - prog))))
            so = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(so, (*o["cor"], alpha), (r + 4, r + 4), r, max(2, int(6 * (1.0 - prog))))
            surf_mundo.blit(so, (int(o["x"] - cam_x - r - 4), int(o["y"] - cam_y - r - 4)))

        for f in self.faiscas_mundo:
            alpha = max(0, min(255, int(255 * (f["vida"] / f["max_vida"]))))
            fx = int(f["x"] - cam_x)
            fy = int(f["y"] - cam_y)
            sf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(sf, (*f["cor"], alpha), (5, 5), f["r"])
            surf_mundo.blit(sf, (fx - 5, fy - 5))

    def desenhar_poeira_1080(self, surf_1080, t, fator_eter=1.0):
        import pygame

        for p in self.ambiente_1080:
            pulso = 0.45 + 0.55 * math.sin(t * 2.8 + p["fase"])
            cor = (56, 189, 248) if p["tipo"] == "eter" else (245, 158, 11)
            alpha = int(125 * pulso * fator_eter)
            r = p["raio"]
            sp = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
            pygame.draw.circle(sp, (*cor, max(10, alpha // 3)), (r * 3, r * 3), r * 2)
            pygame.draw.circle(sp, (*cor, max(20, alpha)), (r * 3, r * 3), r)
            surf_1080.blit(sp, (int(p["x"]) - r * 3, int(p["y"]) - r * 3))


class DiretorTrailer:
    """Orquestra o roteiro completo de 45s sobre o motor visual de Elos do Vazio."""

    def __init__(self):
        import pygame
        import cenarios
        from cenario_combate_25d import CenarioCombate25D, CameraCombate25D

        if pygame.display.get_surface() is None:
            try:
                pygame.display.set_mode((cenarios.LARGURA_TELA, cenarios.ALTURA_TELA))
            except pygame.error:
                os.environ.pop("SDL_VIDEODRIVER", None)
                pygame.display.set_mode((cenarios.LARGURA_TELA, cenarios.ALTURA_TELA))

        cenarios.iniciar()
        self.cenarios = cenarios
        self.surf_mundo = pygame.Surface((cenarios.LARGURA_TELA, cenarios.ALTURA_TELA))
        self.surf_1080 = pygame.Surface((LARGURA_VIDEO, ALTURA_VIDEO))
        self.vinheta_1080 = self._criar_vinheta_1080()

        self.logo_estudio, self.logo_jogo = carregar_logos()
        self.particulas = MotorParticulasTrailer()

        # Animadores de personagens reais do projeto (sem inimigos removidos)
        self.anim_p1 = _carregar_animador_seguro(["Hero", "Soldier"])
        self.anim_boss_rush = _carregar_animador_seguro(["Boss_ReiSangrento", "Boss_Guardiao", "Demon Carmesim"])
        self.anim_cripta = _carregar_animador_seguro(["Demon Carmesim", "Esqueleto", "Orc"])
        self.anim_duelista = _carregar_animador_seguro(["Demon_A", "Boss_Sentinela", "Esqueleto", "Demon Carmesim"])
        self.anim_boss = _carregar_animador_seguro(["Boss_Bibliotecario", "GuardiaoVazio", "Boss_Guardiao", "Demon Carmesim"])

        self.arena_25d = CenarioCombate25D(cenarios.LARGURA_TELA, cenarios.ALTURA_TELA, sala_idx=4)
        self.cam_25d = CameraCombate25D(cenarios.LARGURA_TELA, cenarios.ALTURA_TELA)

        self.fontes = {
            "card": pygame.font.SysFont("georgia", 54, bold=True),
            "sub": pygame.font.SysFont("georgia", 28, italic=True),
            "mini": pygame.font.SysFont("arial", 22, bold=True),
            "cta": pygame.font.SysFont("georgia", 32, bold=True),
            "tag": pygame.font.SysFont("arial", 13, bold=True),
            "fx_mundo": pygame.font.SysFont("georgia", 20, bold=True),
        }

        self.estados_disparados = set()
        self.hitstop_restante = 0
        self.shake_restante = 0.0
        self.shake_forca = 0.0
        self.flash_cor = None
        self.flash_alpha = 0.0
        self.cena_anterior = None

        self.vagalumes = cenarios.Vagalumes(42)
        self._gravacoes_combate = {}

    def _obter_quadro_combate_turnos(self, chave, tempo_local, sala_idx, duracao_clip, modo_boss_rush=False, usar_boss=False, ataque_steps_baixo=1):
        """
        Simula e armazena em cache quadros reais do sistema de combate por turnos
        (`CombateExpedition33`), garantindo que todas as lutas do trailer exibam
        menu de turnos, barra de iniciativa, QTE e reações defensivas autênticas.
        """
        import pygame
        import main
        from combate import CombateExpedition33

        if chave not in self._gravacoes_combate:
            rng_state = random.getstate()
            random.seed(1337 + int(sala_idx) * 31 + (7 if usar_boss else 0))
            try:
                from progresso import Progresso
                prog_limpo = Progresso()
                prog_limpo.nome_heroi = "Viajante"
                prog_limpo.nivel = 1
                prog_limpo.xp = 0
                prog_limpo.pocoes_encontradas = 3
                prog_limpo.cristais_encontrados = 2
                prog_limpo.registrar_rank_sala = lambda *a, **kw: None
                prog_limpo.salvar = lambda *a, **kw: None
                salas = main.criar_entidades_das_salas(prog_limpo)
                grupo = salas[sala_idx]
                sp = self.cenarios.DADOS_MAPAS[sala_idx].get("spawn_heroi", (110, 680))
                jog = main.JogadorMapa(sp[0], sp[1])
                jog.progresso_ref = prog_limpo
                jog.mapa_idx = sala_idx
                jog.max_hp = 120
                jog.hp = 120

                if usar_boss:
                    boss = grupo["boss"]
                    boss.vivo = True
                    boss.hp = boss.max_hp
                    alvos = [boss]
                else:
                    alvos = [e for e in grupo["inimigos"][:2]]
                    for e in alvos:
                        e.vivo = True
                        e.hp = e.max_hp
                    if not alvos:
                        boss = grupo["boss"]
                        boss.vivo = True
                        boss.hp = boss.max_hp
                        alvos = [boss]

                comb = CombateExpedition33(
                    jog,
                    alvos[0],
                    vantagem="NEUTRO",
                    sala_idx=sala_idx,
                    alvos_disponiveis=alvos,
                    modo_boss_rush=modo_boss_rush,
                    sala_atual=sala_idx,
                )

                fps_sim = 30
                dt_sim = 1.0 / float(fps_sim)
                total_steps = max(2, int(round(duracao_clip * fps_sim)) + 4)
                quadros = []
                surf_c = pygame.Surface((self.cenarios.LARGURA_TELA, self.cenarios.ALTURA_TELA))

                abriu_atk = False
                escolheu_atk = False
                confirmou_alvo = False
                reacao_feita = False
                espera_menu = 0.0

                for step in range(total_steps):
                    t_sim = step * dt_sim
                    if comb.estado == "MENU_JOGADOR":
                        reacao_feita = False
                        espera_menu += dt_sim
                        if comb.menu_categoria == "PRINCIPAL" and not abriu_atk and espera_menu >= 0.40:
                            comb.handle_keydown(pygame.K_RETURN)
                            abriu_atk = True
                        elif comb.menu_categoria == "ATAQUES" and not escolheu_atk and espera_menu >= 0.85:
                            for _ in range(max(0, int(ataque_steps_baixo))):
                                comb.handle_keydown(pygame.K_DOWN)
                            comb.handle_keydown(pygame.K_RETURN)
                            escolheu_atk = True
                        elif comb.menu_categoria == "SELECAO_ALVO" and not confirmou_alvo and espera_menu >= 1.25:
                            comb.handle_keydown(pygame.K_RETURN)
                            confirmou_alvo = True
                        elif abriu_atk and escolheu_atk and confirmou_alvo and espera_menu >= 0.55 and comb.menu_categoria == "PRINCIPAL":
                            # Segundo turno caso o clipe alcance outra rodada
                            abriu_atk = False
                            escolheu_atk = False
                            confirmou_alvo = False
                            espera_menu = 0.0
                    elif comb.estado == "QTE_JOGADOR":
                        espera_menu = 0.0
                        if comb.qte_timer / max(0.01, comb.qte_duracao) >= 0.80:
                            comb.handle_keydown(pygame.K_z)
                    elif comb.estado == "TURNO_INIMIGO":
                        espera_menu = 0.0
                        restante = comb.tempo_impacto - comb.inimigo_timer
                        tipo = comb.tipo_golpe_atual()
                        if not reacao_feita and restante <= 0.12:
                            if tipo in (
                                "RASTEIRA", "ONDA_CHOQUE", "INVESTIDA", "TERREMOTO",
                                "BOTE_FENDIDO", "CLAVA_SISMICA", "FURIA_CORRENTES", "FURIA_ELOS_CORRENTES",
                            ):
                                comb.handle_keydown(pygame.K_SPACE)
                            elif tipo in (
                                "VENENO", "RUGIDO", "GOLPE_ARCANO", "GARRAS",
                                "LANCA_DO_VAZIO", "GUILHOTINA_TRIPLICE", "FURIA_EXPLOSAO", "FURIA_ELOS_DETONACAO",
                            ):
                                comb.handle_keydown(pygame.K_c)
                            else:
                                comb.handle_keydown(pygame.K_x)
                            reacao_feita = True
                    else:
                        reacao_feita = False

                    comb.update(dt_sim)
                    comb.draw(surf_c)
                    quadros.append(surf_c.copy())

                self._gravacoes_combate[chave] = (fps_sim, quadros)
            finally:
                random.setstate(rng_state)

        fps_sim, quadros = self._gravacoes_combate[chave]
        idx = max(0, min(len(quadros) - 1, int(round(max(0.0, tempo_local) * fps_sim))))
        self.surf_mundo.blit(quadros[idx], (0, 0))

    @staticmethod
    def _criar_vinheta_1080():
        import pygame

        v = pygame.Surface((LARGURA_VIDEO, ALTURA_VIDEO), pygame.SRCALPHA)
        for k in range(18):
            a = int((18 - k) * 9.5)
            esp = (18 - k) * 9
            pygame.draw.rect(v, (4, 6, 12, min(200, a // 3)), (k * 8, k * 5, LARGURA_VIDEO - k * 16, ALTURA_VIDEO - k * 10), esp // 2)
        # Barras letterbox cinematográficas superior e inferior (44 px)
        pygame.draw.rect(v, (5, 7, 13, 245), (0, 0, LARGURA_VIDEO, 44))
        pygame.draw.rect(v, (5, 7, 13, 245), (0, ALTURA_VIDEO - 44, LARGURA_VIDEO, 44))
        pygame.draw.line(v, (146, 64, 14, 150), (0, 44), (LARGURA_VIDEO, 44), 1)
        pygame.draw.line(v, (146, 64, 14, 150), (0, ALTURA_VIDEO - 45), (LARGURA_VIDEO, ALTURA_VIDEO - 45), 1)
        return v

    def _once(self, chave):
        if chave in self.estados_disparados:
            return False
        self.estados_disparados.add(chave)
        return True

    def _desenhar_sala_base(self, sala_idx, cam_x, cam_y, tempo, portao_aberto=False):
        c = self.cenarios
        mapa = c.DADOS_MAPAS[sala_idx]
        c.desenhar_fundo_sala(self.surf_mundo, sala_idx, offset_x=cam_x, offset_y=cam_y)
        c.desenhar_decoracoes(self.surf_mundo, sala_idx, cam_x, camera_y=cam_y)
        c.desenhar_estruturas_organicas(self.surf_mundo, sala_idx, cam_x, camera_y=cam_y, tempo=tempo)
        c.desenhar_terreno(self.surf_mundo, sala_idx, cam_x, camera_y=cam_y)
        c.desenhar_armadilhas(self.surf_mundo, sala_idx, cam_x, tempo, camera_y=cam_y)
        portoes = [dict(p, aberto=portao_aberto) for p in mapa.get("portoes", [])]
        grupo = {"portoes": portoes, "alavancas": mapa.get("alavancas", []), "chaves": mapa.get("chaves", []), "baus": mapa.get("baus", [])}
        c.desenhar_portoes(self.surf_mundo, grupo, cam_x, cam_y, tempo)
        c.desenhar_alavancas(self.surf_mundo, grupo, cam_x, cam_y, tempo)
        c.desenhar_baus(self.surf_mundo, grupo, cam_x, cam_y, tempo)
        self.vagalumes.draw(self.surf_mundo, mapa["visual"].get("vagalumes", (170, 235, 165)))

    @staticmethod
    def _render_actor(animador, surf, world_rect, cam_x, cam_y, espelhar=False, escala_extra=1.18, cor_fb=(148, 163, 184), atacando=False, eter=False):
        import pygame

        r_tela = pygame.Rect(int(world_rect.x - cam_x), int(world_rect.y - cam_y), world_rect.width, world_rect.height)
        # Sombra ancorada ao solo
        sh_w = max(24, int(r_tela.width * 0.9))
        sombra = pygame.Surface((sh_w, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (4, 6, 12, 145), (0, 0, sh_w, 10))
        surf.blit(sombra, (r_tela.centerx - sh_w // 2, r_tela.bottom - 5))

        if animador and animador.ativo:
            animador.desenhar(surf, r_tela, espelhar=espelhar, escala_extra=escala_extra)
        else:
            _desenhar_combatente_fallback(surf, r_tela, cor_corpo=cor_fb, atacando=atacando, espelhar=espelhar, eter=eter)

    def _cartao_texto_runico(self, titulo, subtitulo="", prog=0.5):
        import pygame

        self.surf_1080.fill((6, 8, 15))
        # Brilho sutil e névoa horizontal atrás do cartão
        glow = pygame.Surface((1200, 320), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (56, 189, 248, 18), (60, 20, 1080, 280))
        pygame.draw.ellipse(glow, (217, 119, 6, 20), (180, 70, 840, 180))
        self.surf_1080.blit(glow, (LARGURA_VIDEO // 2 - 600, ALTURA_VIDEO // 2 - 160))

        self.particulas.desenhar_poeira_1080(self.surf_1080, prog * 2.5, fator_eter=1.0)

        w_box, h_box = 1480, 230
        bx = (LARGURA_VIDEO - w_box) // 2
        by = (ALTURA_VIDEO - h_box) // 2
        pygame.draw.rect(self.surf_1080, (13, 18, 32), (bx, by, w_box, h_box), border_radius=10)
        pygame.draw.rect(self.surf_1080, (217, 119, 6), (bx, by, w_box, h_box), 3, border_radius=10)
        pygame.draw.rect(self.surf_1080, (120, 53, 15), (bx + 10, by + 10, w_box - 20, h_box - 20), 1, border_radius=8)

        # Adornos de cantos e losangos centrais dourados
        for cx_l, cy_l in ((LARGURA_VIDEO // 2, by), (LARGURA_VIDEO // 2, by + h_box)):
            pygame.draw.polygon(self.surf_1080, (253, 230, 138), [(cx_l, cy_l - 8), (cx_l + 9, cy_l), (cx_l, cy_l + 8), (cx_l - 9, cy_l)])

        f_tit = self.fontes["card"]
        t_somb = f_tit.render(titulo, True, (6, 8, 14))
        t_img = f_tit.render(titulo, True, (253, 230, 138))
        ty = ALTURA_VIDEO // 2 - (38 if subtitulo else t_img.get_height() // 2)
        self.surf_1080.blit(t_somb, (LARGURA_VIDEO // 2 - t_img.get_width() // 2 + 3, ty + 3))
        self.surf_1080.blit(t_img, (LARGURA_VIDEO // 2 - t_img.get_width() // 2, ty))

        if subtitulo:
            sub_img = self.fontes["sub"].render(subtitulo, True, (203, 213, 225))
            self.surf_1080.blit(sub_img, (LARGURA_VIDEO // 2 - sub_img.get_width() // 2, ty + 76))

    def _blitar_gameplay_em_1080(self, zoom=1.0, foco_x=0.5, foco_y=0.5):
        import pygame

        esc = max(1.0, float(zoom))
        if abs(esc - 1.0) < 0.005:
            escalado = pygame.transform.scale(self.surf_mundo, (LARGURA_VIDEO, ALTURA_VIDEO))
            self.surf_1080.blit(escalado, (0, 0))
            return
        nw = int(round(LARGURA_VIDEO * esc))
        nh = int(round(ALTURA_VIDEO * esc))
        escalado = pygame.transform.scale(self.surf_mundo, (nw, nh))
        ox = int((nw - LARGURA_VIDEO) * max(0.0, min(1.0, foco_x)))
        oy = int((nh - ALTURA_VIDEO) * max(0.0, min(1.0, foco_y)))
        self.surf_1080.blit(escalado, (-ox, -oy))

    def renderizar_quadro(self, t, dt):
        import pygame

        # Gerencia Hitstop físico de 4 frames (congela mundo no clímax do Parry)
        congelado = self.hitstop_restante > 0
        if congelado:
            self.hitstop_restante -= 1
            dt_world = 0.0
        else:
            dt_world = dt
            self.particulas.atualizar(dt)
            self.vagalumes.update(dt)
            for anim in (self.anim_p1, self.anim_boss_rush, self.anim_cripta, self.anim_duelista, self.anim_boss):
                anim.update(dt)

        if self.shake_restante > 0:
            self.shake_restante = max(0.0, self.shake_restante - dt)
        if self.flash_alpha > 0:
            self.flash_alpha = max(0.0, self.flash_alpha - dt * 520.0)

        fade_preto = 0
        zoom_cam, foco_x, foco_y = 1.0, 0.5, 0.5

        # ----------------------------------------------------------------------
        # ATO 1: O SELO DO ESTÚDIO (0.0s -> 4.5s)
        # ----------------------------------------------------------------------
        if t < 4.5:
            if self.cena_anterior != "ATO1":
                self.cena_anterior = "ATO1"
            self.surf_1080.fill((6, 8, 16))
            # Névoa profunda ascendente atrás do emblema
            for k in range(5):
                fy = int(ALTURA_VIDEO * (0.85 - (t / 4.5) * 0.25) - k * 55 + math.sin(t * 1.4 + k) * 14)
                fog = pygame.Surface((LARGURA_VIDEO, 180), pygame.SRCALPHA)
                fog.fill((22, 30, 52, 28 - k * 4))
                self.surf_1080.blit(fog, (0, fy))

            a_logo = int(255 * min(1.0, t / 1.1) * min(1.0, max(0.0, (4.3 - t) / 0.7)))
            brilho = pygame.Surface((900, 520), pygame.SRCALPHA)
            pygame.draw.ellipse(brilho, (217, 119, 6, max(0, a_logo // 9)), (120, 40, 660, 440))
            pygame.draw.ellipse(brilho, (56, 189, 248, max(0, a_logo // 12)), (190, 90, 520, 340))
            self.surf_1080.blit(brilho, (LARGURA_VIDEO // 2 - 450, ALTURA_VIDEO // 2 - 260))

            s_est = self.logo_estudio.copy()
            s_est.set_alpha(a_logo)
            self.surf_1080.blit(s_est, (LARGURA_VIDEO // 2 - s_est.get_width() // 2, ALTURA_VIDEO // 2 - s_est.get_height() // 2 - 14))
            self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=0.8)
            fade_preto = int(255 * max(0.0, (t - 3.9) / 0.6))

        # ----------------------------------------------------------------------
        # CARTÃO DE TEXTO RÚNICO 1 (4.5s -> 6.8s)
        # ----------------------------------------------------------------------
        elif t < 6.8:
            self.cena_anterior = "CARD1"
            self._cartao_texto_runico(
                "SETE SALAS ESQUECIDAS PELO TEMPO...",
                "Quando os laços se romperam, restou apenas a lâmina.",
                prog=(t - 4.5) / 2.3,
            )
            fade_preto = int(255 * max(max(0.0, 1.0 - (t - 4.5) / 0.35), max(0.0, (t - 6.45) / 0.35)))

        # ----------------------------------------------------------------------
        # ATO 2A: AMEIAS SOB A LUA CHEIA — EXPLORAÇÃO E SALTO (6.8s -> 10.6s, Sala 1)
        # ----------------------------------------------------------------------
        elif t < 10.6:
            if self.cena_anterior != "ATO2A":
                self.cena_anterior = "ATO2A"
                self.particulas.limpar_mundo()
            tl = t - 6.8
            chao_y = self.cenarios.DADOS_MAPAS[0]["chao"].top
            hx = 175.0 + tl * 225.0
            # Salto cinematográfico subindo no parapeito p1 (x=420..615, y=chao_y-96)
            if tl < 1.3:
                hy = chao_y - 56
                anim_st = "walk"
            elif tl < 2.25:
                u = (tl - 1.3) / 0.95
                hy = (chao_y - 56) - 96 * math.sin(u * math.pi * 0.85) - (96 * u * 0.65)
                hy = min(chao_y - 56 - 96 * min(1.0, u * 1.15), hy)
                anim_st = "jump"
                if self._once("ato2a_pulo"):
                    self.particulas.emitir_faiscas(hx + 18, chao_y - 4, n=10, cores=((148, 163, 184), (203, 213, 225)), vel=120.0)
            else:
                hy = chao_y - 96 - 56
                anim_st = "walk"
            self.anim_p1.tocar(anim_st, loop=True)

            cam_x = max(0.0, hx - 340.0)
            cam_y = max(0.0, chao_y - 385.0)
            self._desenhar_sala_base(0, cam_x, cam_y, t)
            self._render_actor(self.anim_p1, self.surf_mundo, pygame.Rect(int(hx), int(hy), 36, 56), cam_x, cam_y, cor_fb=(100, 145, 225))
            self.particulas.desenhar_fx_mundo(self.surf_mundo, cam_x, cam_y)
            self._blitar_gameplay_em_1080(zoom=1.08, foco_x=0.5, foco_y=0.55)
            self.particulas.desenhar_poeira_1080(self.surf_1080, t)
            fade_preto = int(255 * max(max(0.0, 1.0 - tl / 0.35), max(0.0, (tl - 3.45) / 0.35)))

        # ----------------------------------------------------------------------
        # ATO 2B: GALERIAS DAS TORRES SUSPENSAS POR CORRENTES (10.6s -> 14.0s, Sala 4)
        # ----------------------------------------------------------------------
        elif t < 14.0:
            if self.cena_anterior != "ATO2B":
                self.cena_anterior = "ATO2B"
                self.particulas.limpar_mundo()
            tl = t - 10.6
            y_var = 780.0
            hx = 480.0 + tl * 215.0
            # Saltando entre plataformas suspensas ps1 (y-68), ps2 (y-148), ps3 (y-76)
            arc = abs(math.sin(tl * math.pi * 0.95))
            hy = (y_var - 150.0) - arc * 92.0
            self.anim_p1.tocar("jump" if arc > 0.28 else "walk", loop=True)

            cam_x = max(0.0, hx - 370.0)
            cam_y = 435.0
            self._desenhar_sala_base(3, cam_x, cam_y, t)
            self._render_actor(self.anim_p1, self.surf_mundo, pygame.Rect(int(hx), int(hy), 36, 56), cam_x, cam_y, cor_fb=(100, 145, 225))
            self.particulas.desenhar_fx_mundo(self.surf_mundo, cam_x, cam_y)
            self._blitar_gameplay_em_1080(zoom=1.06, foco_x=0.5, foco_y=0.5)
            self.particulas.desenhar_poeira_1080(self.surf_1080, t)
            fade_preto = int(255 * max(max(0.0, 1.0 - tl / 0.3), max(0.0, (tl - 3.05) / 0.35)))

        # ----------------------------------------------------------------------
        # CARTÃO DE TEXTO RÚNICO 2 (14.0s -> 16.0s)
        # ----------------------------------------------------------------------
        elif t < 16.0:
            self.cena_anterior = "CARD2"
            self._cartao_texto_runico(
                "COMBATE TÁTICO POR TURNOS",
                "Escolha suas habilidades, acerte o QTE e domine o Parry",
                prog=(t - 14.0) / 2.0,
            )
            fade_preto = int(255 * max(max(0.0, 1.0 - (t - 14.0) / 0.28), max(0.0, (t - 15.7) / 0.3)))

        # ----------------------------------------------------------------------
        # ATO 3A + 3B: COMBATE POR TURNOS 2.5D NAS CATACUMBAS (16.0s -> 23.4s, Sala 5)
        # Turno do Jogador (Menu -> Alvo -> QTE) + Turno Inimigo (Parry / Esquiva + Contra-Ataque)
        # ----------------------------------------------------------------------
        elif t < 23.4:
            if self.cena_anterior != "ATO3_TURNOS":
                self.cena_anterior = "ATO3_TURNOS"
                self.particulas.limpar_mundo()
            tl = t - 16.0
            self._obter_quadro_combate_turnos(
                "catacumbas_turnos",
                tl,
                sala_idx=4,
                duracao_clip=7.4,
                modo_boss_rush=False,
                usar_boss=False,
                ataque_steps_baixo=1,
            )
            self._blitar_gameplay_em_1080(zoom=1.0)
            self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=0.65)
            fade_preto = int(255 * max(max(0.0, 1.0 - tl / 0.25), max(0.0, (tl - 7.1) / 0.3)))

        # ----------------------------------------------------------------------
        # ATO 3C: MODO BOSS RUSH POR TURNOS — REI DA LUA SANGRENTA (23.4s -> 26.5s, Sala 6)
        # ----------------------------------------------------------------------
        elif t < 26.5:
            if self.cena_anterior != "ATO3C":
                self.cena_anterior = "ATO3C"
                self.particulas.limpar_mundo()
            tl = t - 23.4
            self._obter_quadro_combate_turnos(
                "boss_rush_sala6",
                tl + 0.35,
                sala_idx=5,
                duracao_clip=3.8,
                modo_boss_rush=True,
                usar_boss=True,
                ataque_steps_baixo=1,
            )
            self._blitar_gameplay_em_1080(zoom=1.0)
            tag_rush = self.fontes["mini"].render("BOSS RUSH  •  COMBATE POR TURNOS CONTRA OS 7 CHEFES", True, (253, 230, 138))
            self.surf_1080.blit(tag_rush, (LARGURA_VIDEO // 2 - tag_rush.get_width() // 2, 52))
            self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=0.75)
            fade_preto = int(255 * max(max(0.0, 1.0 - tl / 0.25), max(0.0, (tl - 2.8) / 0.3)))

        # ----------------------------------------------------------------------
        # CARTÃO DE TEXTO RÚNICO 3 (26.5s -> 28.5s)
        # ----------------------------------------------------------------------
        elif t < 28.5:
            self.cena_anterior = "CARD3"
            self._cartao_texto_runico(
                "O SANTUÁRIO EXIGE SANGUE",
                "Enfrente o Guardião além dos portões titânicos",
                prog=(t - 26.5) / 2.0,
            )
            fade_preto = int(255 * max(max(0.0, 1.0 - (t - 26.5) / 0.25), max(0.0, (t - 28.2) / 0.3)))

        # ----------------------------------------------------------------------
        # ATO 4: ENTRADA NO SANTUÁRIO (SALA 7) + COMBATE POR TURNOS CONTRA O CHEFE FINAL (28.5s -> 37.5s)
        # ----------------------------------------------------------------------
        elif t < 37.5:
            if self.cena_anterior != "ATO4":
                self.cena_anterior = "ATO4"
                self.particulas.limpar_mundo()
            tl = t - 28.5

            if tl < 3.4:
                # Exploração pura na Sala 7: abertura do portão rúnico e avanço até o confronto
                chao_y = self.cenarios.DADOS_MAPAS[6]["chao"].top
                portao_aberto = tl >= 1.55
                if 0.5 <= tl < 1.9:
                    self.shake_restante, self.shake_forca = 0.08, 4.5
                if self._once("ato4_portao") and portao_aberto:
                    self.particulas.emitir_onda(836, chao_y - 104, cor=(56, 189, 248), raio_max=160, dur=0.55)
                    self.particulas.emitir_faiscas(836, chao_y - 40, n=32, cores=((56, 189, 248), (253, 230, 138)), vel=240.0)
                    self.shake_restante, self.shake_forca = 0.25, 8.0

                boss_x = 640.0
                hx, hy = 135.0 + max(0.0, tl - 1.2) * 72.0, chao_y - 56
                self.anim_p1.tocar("walk" if tl > 1.2 else "idle", loop=True)
                self.anim_boss.tocar("idle", loop=True)
                zoom_cam, foco_x, foco_y = 1.0 + 0.06 * (tl / 3.4), 0.65, 0.58

                self._desenhar_sala_base(6, 0.0, 0.0, t, portao_aberto=portao_aberto)
                self._render_actor(self.anim_boss, self.surf_mundo, pygame.Rect(int(boss_x), int(chao_y - 96), 72, 96), 0.0, 0.0, espelhar=True, escala_extra=1.35, cor_fb=(155, 45, 185), eter=True)
                self._render_actor(self.anim_p1, self.surf_mundo, pygame.Rect(int(hx), int(hy), 36, 56), 0.0, 0.0, cor_fb=(100, 145, 225))
                self.particulas.desenhar_fx_mundo(self.surf_mundo, 0.0, 0.0)
                self._blitar_gameplay_em_1080(zoom=zoom_cam, foco_x=foco_x, foco_y=foco_y)
                self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=1.1)
                if tl < 0.35:
                    fade_preto = int(255 * (1.0 - tl / 0.35))
                elif tl > 3.10:
                    fade_preto = int(255 * ((tl - 3.10) / 0.30))
            else:
                # Transição para o Combate por Turnos 2.5D real contra o Bibliotecário do Vazio
                tl_comb = tl - 3.4
                self._obter_quadro_combate_turnos(
                    "boss_final_sala7",
                    tl_comb + 0.40,
                    sala_idx=6,
                    duracao_clip=6.2,
                    modo_boss_rush=False,
                    usar_boss=True,
                    ataque_steps_baixo=1,
                )
                self._blitar_gameplay_em_1080(zoom=1.0)
                self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=0.8)
                if tl_comb < 0.30:
                    fade_preto = int(255 * (1.0 - tl_comb / 0.30))
                if tl >= 8.55:
                    a_branco = int(255 * min(1.0, (tl - 8.55) / 0.40))
                    self.flash_cor = (240, 249, 255)
                    self.flash_alpha = float(a_branco)

        # ----------------------------------------------------------------------
        # ATO 5: ENCERRAMENTO MONUMENTAL & CHAMADA PARA AÇÃO (37.5s -> 45.0s)
        # ----------------------------------------------------------------------
        else:
            self.cena_anterior = "ATO5"
            tl = t - 37.5
            self.surf_1080.fill((7, 10, 19))

            # Halo radial de Éter e ouro por trás da Logo Oficial de ELOS DO VAZIO
            halo = pygame.Surface((1280, 620), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (56, 189, 248, 22), (80, 40, 1120, 540))
            pygame.draw.ellipse(halo, (217, 119, 6, 26), (260, 120, 760, 380))
            self.surf_1080.blit(halo, (LARGURA_VIDEO // 2 - 640, 70))

            # Logo principal do jogo (com escala suave de impacto inicial)
            esc_l = 1.0 + max(0.0, 0.14 * (1.0 - min(1.0, tl / 0.45)))
            lj_w = int(self.logo_jogo.get_width() * esc_l)
            lj_h = int(self.logo_jogo.get_height() * esc_l)
            s_lj = pygame.transform.smoothscale(self.logo_jogo, (lj_w, lj_h))
            self.surf_1080.blit(s_lj, (LARGURA_VIDEO // 2 - lj_w // 2, 115))

            # Assinatura GoZygrid Studios com mini emblema
            s_est_peq = pygame.transform.smoothscale(self.logo_estudio, (130, int(130 * self.logo_estudio.get_height() / float(max(1, self.logo_estudio.get_width())))))
            a_cta = int(255 * min(1.0, max(0.0, (tl - 0.55) / 0.65)))
            t_dev = self.fontes["sub"].render("Desenvolvido por GoZygrid Studios", True, (241, 245, 249))
            t_dev.set_alpha(a_cta)
            w_ass = s_est_peq.get_width() + 20 + t_dev.get_width()
            x_ass = LARGURA_VIDEO // 2 - w_ass // 2
            s_est_peq.set_alpha(a_cta)
            self.surf_1080.blit(s_est_peq, (x_ass, 525))
            self.surf_1080.blit(t_dev, (x_ass + s_est_peq.get_width() + 20, 525 + s_est_peq.get_height() // 2 - t_dev.get_height() // 2))

            # Botão / Pílula de Chamada para Ação em Latão e Ciano
            cta_w, cta_h = 840, 86
            cx_b, cy_b = LARGURA_VIDEO // 2 - cta_w // 2, 665
            pulso = 0.5 + 0.5 * math.sin(t * 4.0)
            s_cta = pygame.Surface((cta_w, cta_h), pygame.SRCALPHA)
            pygame.draw.rect(s_cta, (19, 25, 43, int(235 * (a_cta / 255.0))), (0, 0, cta_w, cta_h), border_radius=10)
            cor_borda = (245, int(158 + 50 * pulso), int(11 + 60 * pulso), a_cta)
            pygame.draw.rect(s_cta, cor_borda, (0, 0, cta_w, cta_h), 3, border_radius=10)
            txt_cta = self.fontes["cta"].render("DISPONÍVEL AGORA  |  BAIXE O INSTALADOR", True, (253, 230, 138))
            txt_cta.set_alpha(a_cta)
            s_cta.blit(txt_cta, (cta_w // 2 - txt_cta.get_width() // 2, cta_h // 2 - txt_cta.get_height() // 2))
            self.surf_1080.blit(s_cta, (cx_b, cy_b))

            t_links = self.fontes["mini"].render("GitHub (github.com/GoKaio/elos-do-vazio)   •   PC (Windows 10 / 11)", True, (56, 189, 248))
            t_links.set_alpha(a_cta)
            self.surf_1080.blit(t_links, (LARGURA_VIDEO // 2 - t_links.get_width() // 2, 780))

            self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=1.1)

            # Dissolução suave vinda do clarão branco de clímax -> encerramento escuro final
            if tl < 0.70:
                self.flash_cor = (240, 249, 255)
                self.flash_alpha = 255.0 * (1.0 - tl / 0.70)
            if tl > 6.45:
                fade_preto = int(255 * min(1.0, (tl - 6.45) / 1.05))

        # Aplica vinheta cinematográfica e barras letterbox em todo o trailer
        self.surf_1080.blit(self.vinheta_1080, (0, 0))

        # Aplica flash luminoso (Parry / Clímax) e Fade-to-Black entre atos
        if self.flash_alpha > 1.0 and self.flash_cor is not None:
            fl = pygame.Surface((LARGURA_VIDEO, ALTURA_VIDEO), pygame.SRCALPHA)
            fl.fill((*self.flash_cor, max(0, min(255, int(self.flash_alpha)))))
            self.surf_1080.blit(fl, (0, 0))

        if fade_preto > 0:
            fd = pygame.Surface((LARGURA_VIDEO, ALTURA_VIDEO), pygame.SRCALPHA)
            fd.fill((0, 0, 0, max(0, min(255, fade_preto))))
            self.surf_1080.blit(fd, (0, 0))

        return pygame.image.tobytes(self.surf_1080, "RGB")


# ==============================================================================
# 4. EXPORTAÇÃO H.264 1080p @ 60 FPS COM ÁUDIO ESTÉREO (FFMPEG / MOVIEPY / CV2)
# ==============================================================================
def _exportar_via_ffmpeg(diretor, wav_path, saida_mp4, ffmpeg_exe, fps=FPS_VIDEO, duracao=DURACAO_TOTAL):
    total_frames = int(round(duracao * fps))
    dt = 1.0 / float(fps)
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{LARGURA_VIDEO}x{ALTURA_VIDEO}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        saida_mp4,
    ]
    print(f"[trailer] Exportando via FFmpeg ({total_frames} quadros @ {fps} FPS -> {LARGURA_VIDEO}x{ALTURA_VIDEO})...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for i in range(total_frames):
            t = i * dt
            frame_bytes = diretor.renderizar_quadro(t, dt)
            proc.stdin.write(frame_bytes)
            if (i + 1) % (fps * 5) == 0 or i + 1 == total_frames:
                print(f"  -> Progresso: {((i + 1) / float(total_frames)) * 100.0:5.1f}% ({i + 1}/{total_frames})")
        proc.stdin.close()
        stderr_out = proc.stderr.read().decode("utf-8", errors="replace")
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg retornou erro {ret}: {stderr_out[-400:]}")
    except Exception:
        proc.kill()
        raise


def _exportar_via_moviepy(diretor, wav_path, saida_mp4, fps=FPS_VIDEO, duracao=DURACAO_TOTAL):
    import numpy as np

    try:
        from moviepy.editor import VideoClip, AudioFileClip
        v2 = False
    except ImportError:
        from moviepy import VideoClip, AudioFileClip
        v2 = True

    dt = 1.0 / float(fps)

    def _make_frame(t):
        raw = diretor.renderizar_quadro(float(t), dt)
        return np.frombuffer(raw, dtype=np.uint8).reshape((ALTURA_VIDEO, LARGURA_VIDEO, 3))

    clip = VideoClip(_make_frame, duration=duracao)
    audio = AudioFileClip(wav_path)
    clip = clip.with_audio(audio) if v2 else clip.set_audio(audio)
    clip.write_videofile(
        saida_mp4, fps=fps, codec="libx264", audio_codec="aac",
        audio_bitrate="192k", preset="medium", ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    clip.close()
    audio.close()


def gerar_trailer_completo(saida_mp4=SAIDA_PADRAO, fps=FPS_VIDEO, duracao=DURACAO_TOTAL, permitir_instalar=True):
    garantir_dependencias(permitir_instalar=permitir_instalar)

    import pygame
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()

    ffmpeg_exe = _encontrar_ffmpeg()
    fd_wav, wav_path = tempfile.mkstemp(prefix="elos_trailer_", suffix=".wav")
    os.close(fd_wav)

    try:
        print("[1/3] Compondo trilha sonora e sincronizando SFX...")
        construir_trilha_audio_wav(wav_path, ffmpeg_exe, duracao=duracao)

        print("[2/3] Inicializando motor visual de Elos do Vazio e coreografia...")
        diretor = DiretorTrailer()

        print(f"[3/3] Renderizando MP4 Full HD -> {saida_mp4}")
        if ffmpeg_exe:
            _exportar_via_ffmpeg(diretor, wav_path, saida_mp4, ffmpeg_exe, fps=fps, duracao=duracao)
        else:
            _exportar_via_moviepy(diretor, wav_path, saida_mp4, fps=fps, duracao=duracao)

        if os.path.isfile(saida_mp4):
            tam_mb = os.path.getsize(saida_mp4) / (1024.0 * 1024.0)
            print(f"[OK] Trailer renderizado com sucesso: {saida_mp4} ({tam_mb:.2f} MB)")
        else:
            raise FileNotFoundError(f"Arquivo final não encontrado: {saida_mp4}")
    finally:
        try:
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Gera Trailer Oficial Full HD 60FPS de Elos do Vazio.")
    parser.add_argument("--saida", default=SAIDA_PADRAO, help="Caminho do arquivo .mp4 de saída.")
    parser.add_argument("--fps", type=int, default=FPS_VIDEO, help="Quadros por segundo (padrão: 60).")
    parser.add_argument("--duracao", type=float, default=DURACAO_TOTAL, help="Duração em segundos (padrão: 45.0).")
    parser.add_argument("--no-install", action="store_true", help="Não instalar pacotes faltantes automaticamente.")
    args = parser.parse_args()

    gerar_trailer_completo(
        saida_mp4=args.saida,
        fps=max(24, args.fps),
        duracao=max(10.0, args.duracao),
        permitir_instalar=not args.no_install,
    )


if __name__ == "__main__":
    main()
