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

    # Ato 3C: Cooperativo Local golpes sincronizados
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

        # Animadores de personagens carregados diretamente do projeto
        self.anim_p1 = _carregar_animador_seguro(["Hero", "Soldier"])
        self.anim_p2 = _carregar_animador_seguro(["Hero", "Soldier"], tint_rgba=(255, 150, 120, 255))
        self.anim_cripta = _carregar_animador_seguro(["Demon Carmesim", "Esqueleto", "Orc"])
        self.anim_duelista = _carregar_animador_seguro(["Gargula", "Orc", "Blood Monster_A", "Demon Carmesim"])
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
            for anim in (self.anim_p1, self.anim_p2, self.anim_cripta, self.anim_duelista, self.anim_boss):
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
                "DOMINE O AÇO. ROMPA OS ELOS.",
                "Sete salas forjadas em sangue e cantaria",
                prog=(t - 14.0) / 2.0,
            )
            fade_preto = int(255 * max(max(0.0, 1.0 - (t - 14.0) / 0.28), max(0.0, (t - 15.7) / 0.3)))

        # ----------------------------------------------------------------------
        # ATO 3A: COMBATE NAS CATACUMBAS — COMBO DE 3 GOLPES + ESQUIVA (16.0s -> 19.6s, Sala 5)
        # ----------------------------------------------------------------------
        elif t < 19.6:
            if self.cena_anterior != "ATO3A":
                self.cena_anterior = "ATO3A"
                self.particulas.limpar_mundo()
            tl = t - 16.0
            y_solo = 740.0
            cam_x, cam_y = 1480.0, 385.0
            inim_x = 1975.0 + max(0.0, (tl - 0.6) * 28.0)

            # Coreografia: Avança -> 3 Cortes com faíscas -> Esquiva rápida por baixo
            if tl < 0.42:
                hx = 1785.0 + tl * 320.0
                self.anim_p1.tocar("walk", loop=True)
                self.anim_cripta.tocar("idle", loop=True)
            elif tl < 1.85:
                hx = 1920.0 + (tl - 0.42) * 18.0
                golpe = int((tl - 0.42) / 0.48) + 1
                if self._once(f"ato3a_hit_{golpe}"):
                    self.anim_p1.tocar(["attack", "attack2", "attack3"][min(2, golpe - 1)], loop=False, duracao=0.45, forcar=True)
                    self.anim_cripta.tocar("hurt", loop=False, duracao=0.35, forcar=True)
                    self.particulas.emitir_arco(hx + 34, y_solo - 32, dir_x=1, cor=(253, 230, 138) if golpe < 3 else (56, 189, 248))
                    self.particulas.emitir_faiscas(inim_x + 12, y_solo - 32, n=16, vel=280.0)
                    self.shake_restante, self.shake_forca = 0.14, 5.0
            elif tl < 2.28:
                hx = 1945.0
                if self._once("ato3a_inim_sw"):
                    self.anim_cripta.tocar("attack", loop=False, duracao=0.40, forcar=True)
                    self.particulas.emitir_arco(inim_x - 10, y_solo - 34, dir_x=-1, cor=(248, 113, 113), raio=62)
            else:
                # Esquiva veloz passando para a direita por baixo do ataque
                u = min(1.0, (tl - 2.28) / 0.72)
                hx = 1945.0 + u * 215.0
                if self._once("ato3a_dodge"):
                    self.anim_p1.tocar("dodge", loop=False, duracao=0.55, forcar=True)
                if u < 0.85 and int(tl * 30) % 2 == 0:
                    self.particulas.emitir_fantasma(hx, y_solo - 50, 34, 50)

            self._desenhar_sala_base(4, cam_x, cam_y, t)
            self._render_actor(self.anim_cripta, self.surf_mundo, pygame.Rect(int(inim_x), int(y_solo - 64), 44, 64), cam_x, cam_y, espelhar=True, cor_fb=(185, 55, 75), atacando=(1.9 < tl < 2.35))
            self._render_actor(self.anim_p1, self.surf_mundo, pygame.Rect(int(hx), int(y_solo - 56), 36, 56), cam_x, cam_y, cor_fb=(100, 145, 225), atacando=(0.42 <= tl < 1.85), eter=(tl >= 2.28))
            self.particulas.desenhar_fx_mundo(self.surf_mundo, cam_x, cam_y)
            sx = int(random.uniform(-self.shake_forca, self.shake_forca)) if self.shake_restante > 0 else 0
            sy = int(random.uniform(-self.shake_forca, self.shake_forca)) if self.shake_restante > 0 else 0
            self.surf_mundo.scroll(sx, sy)
            self._blitar_gameplay_em_1080(zoom=1.15, foco_x=0.52, foco_y=0.58)
            self.particulas.desenhar_poeira_1080(self.surf_1080, t)
            fade_preto = int(255 * max(max(0.0, 1.0 - tl / 0.25), max(0.0, (tl - 3.3) / 0.3)))

        # ----------------------------------------------------------------------
        # ATO 3B: PARRY DE PRECISÃO 2.5D + HITSTOP 4 FRAMES + CONTRA-ATAQUE (19.6s -> 23.4s)
        # ----------------------------------------------------------------------
        elif t < 23.4:
            if self.cena_anterior != "ATO3B":
                self.cena_anterior = "ATO3B"
                self.particulas.limpar_mundo()
            tl = t - 19.6
            self.arena_25d.tempo = t
            self.cam_25d.atualizar(dt_world)

            # Inimigo avança em Z=35 e golpeia em tl=1.45s -> PARRY com 4 frames de hitstop!
            if tl < 1.45:
                self.cam_25d.focar_qte_defensivo(-90.0, -210.0)
                ex_3d = 120.0 - min(1.0, tl / 1.15) * 200.0
                ez_3d = 90.0 - min(1.0, tl / 1.15) * 45.0
                hx_3d, hz_3d = -210.0, 55.0
                if tl > 0.7:
                    if self._once("ato3b_windup"):
                        self.anim_duelista.tocar("attack_parry", loop=False, duracao=0.75, forcar=True)
                else:
                    self.anim_duelista.tocar("walk", loop=True)
                if tl > 1.25:
                    if self._once("ato3b_guarda"):
                        self.anim_p1.tocar("block", loop=False, duracao=0.35, forcar=True)
                else:
                    self.anim_p1.tocar("idle", loop=True)
            elif tl < 2.15:
                # Momento exato do Parry Perfeito + Hitstop de 4 frames + Contra-ataque
                if self._once("ato3b_parry"):
                    self.anim_p1.tocar("counter", loop=False, duracao=0.60, forcar=True)
                    self.anim_duelista.tocar("hurt", loop=False, duracao=0.50, forcar=True)
                    self.hitstop_restante = 4
                    self.flash_cor = (56, 189, 248)
                    self.flash_alpha = 185.0
                    self.shake_restante, self.shake_forca = 0.28, 12.0
                    self.cam_25d.aplicar_tremor(10.0, 0.28)
                    self.particulas.emitir_onda(435, 315, cor=(56, 189, 248), raio_max=190, dur=0.45)
                    self.particulas.emitir_faiscas(435, 315, n=36, cores=((56, 189, 248), (224, 242, 254), (253, 230, 138)), vel=390.0)
                self.cam_25d.definir_pose(x=-40.0, y=-20.0, zoom=1.34, tilt=-4.0)
                ex_3d, ez_3d = -80.0, 45.0
                hx_3d, hz_3d = -205.0, 55.0
            else:
                # Contra-ataque devastador arremessa o oponente para trás rumo às grades!
                u = min(1.0, (tl - 2.15) / 0.85)
                if self._once("ato3b_contra"):
                    self.anim_p1.tocar("attack3", loop=False, duracao=0.65, forcar=True)
                    self.anim_duelista.tocar("hurt", loop=False, duracao=0.75, forcar=True)
                    self.particulas.emitir_arco(470, 305, dir_x=1, cor=(56, 189, 248), raio=82, dur=0.25)
                    self.particulas.emitir_faiscas(510, 300, n=28, cores=((253, 230, 138), (56, 189, 248)), vel=340.0)
                    self.shake_restante, self.shake_forca = 0.22, 9.0
                self.cam_25d.definir_pose(x=60.0, y=-12.0, zoom=1.22, tilt=2.0)
                hx_3d, hz_3d = -140.0, 55.0
                ex_3d = -80.0 + u * 310.0
                ez_3d = 45.0 + u * 110.0

            self.arena_25d.desenhar_completo(self.surf_mundo, self.cam_25d, [])
            px_h, py_h, esc_h = self.cam_25d.projetar(hx_3d, self.arena_25d.y_chao, hz_3d)
            px_e, py_e, esc_e = self.cam_25d.projetar(ex_3d, self.arena_25d.y_chao, ez_3d)
            r_h = pygame.Rect(int(px_h - 32 * esc_h), int(py_h - 86 * esc_h), int(64 * esc_h), int(86 * esc_h))
            r_e = pygame.Rect(int(px_e - 42 * esc_e), int(py_e - 102 * esc_e), int(84 * esc_e), int(102 * esc_e))
            self._render_actor(self.anim_duelista, self.surf_mundo, r_e, 0, 0, espelhar=True, escala_extra=1.25, cor_fb=(175, 55, 75), atacando=(tl < 1.5))
            self._render_actor(self.anim_p1, self.surf_mundo, r_h, 0, 0, espelhar=False, escala_extra=1.25, cor_fb=(100, 145, 225), atacando=(tl >= 1.45), eter=True)
            self.particulas.desenhar_fx_mundo(self.surf_mundo, 0, 0)

            if 1.45 <= tl < 2.45:
                lbl = self.fontes["fx_mundo"].render("PARRY PERFEITO!", True, (56, 189, 248))
                self.surf_mundo.blit(lbl, (LARGURA_VIDEO // 4 - lbl.get_width() // 2, 118))

            self._blitar_gameplay_em_1080(zoom=1.0)
            # Subtítulo rúnico elegante em sobreposição discreta
            tag_sub = self.fontes["mini"].render("APARE  •  CONTRA-ATAQUE  •  SOBREVIVA", True, (253, 230, 138))
            self.surf_1080.blit(tag_sub, (LARGURA_VIDEO // 2 - tag_sub.get_width() // 2, 74))
            self.particulas.desenhar_poeira_1080(self.surf_1080, t)
            fade_preto = int(255 * max(max(0.0, 1.0 - tl / 0.22), max(0.0, (tl - 3.5) / 0.3)))

        # ----------------------------------------------------------------------
        # ATO 3C: COOPERATIVO LOCAL 2 JOGADORES NAS CATACUMBAS (23.4s -> 26.5s, Sala 6)
        # ----------------------------------------------------------------------
        elif t < 26.5:
            if self.cena_anterior != "ATO3C":
                self.cena_anterior = "ATO3C"
                self.particulas.limpar_mundo()
            tl = t - 23.4
            y_cripta = 800.0
            cam_x, cam_y = 1620.0, 445.0
            p1x = 1810.0 + tl * 72.0
            p2x = 1745.0 + tl * 84.0
            e1x = 2055.0 - min(0.8, tl * 0.25) * 40.0
            e2x = 2135.0 - min(0.8, tl * 0.25) * 55.0

            self.anim_p1.tocar("attack2" if int(tl * 3.0) % 2 == 0 else "attack", loop=True)
            self.anim_p2.tocar("attack" if int(tl * 3.0) % 2 == 1 else "attack3", loop=True)
            self.anim_cripta.tocar("hurt" if tl > 0.7 else "walk", loop=True)

            if self._once("ato3c_slash1") and tl > 0.65:
                self.particulas.emitir_arco(p1x + 42, y_cripta - 32, dir_x=1, cor=(56, 189, 248))
                self.particulas.emitir_faiscas(e1x, y_cripta - 30, n=22, vel=290.0)
            if self._once("ato3c_slash2") and tl > 1.45:
                self.particulas.emitir_arco(p2x + 42, y_cripta - 32, dir_x=1, cor=(251, 146, 60))
                self.particulas.emitir_faiscas(e2x, y_cripta - 30, n=24, vel=310.0)
                self.shake_restante, self.shake_forca = 0.16, 6.0

            self._desenhar_sala_base(5, cam_x, cam_y, t)
            self._render_actor(self.anim_cripta, self.surf_mundo, pygame.Rect(int(e1x), int(y_cripta - 62), 42, 62), cam_x, cam_y, espelhar=True, cor_fb=(185, 55, 75))
            self._render_actor(self.anim_duelista, self.surf_mundo, pygame.Rect(int(e2x), int(y_cripta - 66), 46, 66), cam_x, cam_y, espelhar=True, cor_fb=(145, 70, 155))
            self._render_actor(self.anim_p2, self.surf_mundo, pygame.Rect(int(p2x), int(y_cripta - 56), 36, 56), cam_x, cam_y, cor_fb=(215, 110, 65), atacando=True)
            self._render_actor(self.anim_p1, self.surf_mundo, pygame.Rect(int(p1x), int(y_cripta - 56), 36, 56), cam_x, cam_y, cor_fb=(100, 145, 225), atacando=True, eter=True)

            # Marcadores limpos P1 / P2
            for tag_lbl, tx, cor_tag in (("P1", p1x + 18, (56, 189, 248)), ("P2", p2x + 18, (251, 146, 60))):
                st = self.fontes["tag"].render(tag_lbl, True, cor_tag)
                self.surf_mundo.blit(st, (int(tx - cam_x - st.get_width() // 2), int(y_cripta - 74 - cam_y)))

            self.particulas.desenhar_fx_mundo(self.surf_mundo, cam_x, cam_y)
            self._blitar_gameplay_em_1080(zoom=1.12, foco_x=0.5, foco_y=0.55)
            tag_coop = self.fontes["mini"].render("COOPERATIVO LOCAL  •  2 JOGADORES EM SINTONIA", True, (56, 189, 248))
            self.surf_1080.blit(tag_coop, (LARGURA_VIDEO // 2 - tag_coop.get_width() // 2, 74))
            self.particulas.desenhar_poeira_1080(self.surf_1080, t)
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
        # ATO 4: CONFRONTO FINAL — PORTÃO DA SALA 7 E ATAQUE AÉREO DE CLÍMAX (28.5s -> 37.5s)
        # ----------------------------------------------------------------------
        elif t < 37.5:
            if self.cena_anterior != "ATO4":
                self.cena_anterior = "ATO4"
                self.particulas.limpar_mundo()
            tl = t - 28.5
            chao_y = self.cenarios.DADOS_MAPAS[6]["chao"].top
            portao_aberto = tl >= 1.75
            if 0.6 <= tl < 2.2:
                self.shake_restante, self.shake_forca = 0.08, 4.5
            if self._once("ato4_portao") and portao_aberto:
                self.particulas.emitir_onda(836, chao_y - 104, cor=(56, 189, 248), raio_max=160, dur=0.55)
                self.particulas.emitir_faiscas(836, chao_y - 40, n=32, cores=((56, 189, 248), (253, 230, 138)), vel=240.0)
                self.shake_restante, self.shake_forca = 0.25, 8.0

            boss_x = 640.0
            # Fase A (0..3.6s): Abertura épica do portão | Fase B (3.6..9.0s): Avanço e Ataque Aéreo de Éter
            if tl < 3.6:
                hx, hy = 135.0 + tl * 38.0, chao_y - 56
                self.anim_p1.tocar("walk" if tl > 1.8 else "idle", loop=True)
                self.anim_boss.tocar("idle", loop=True)
                zoom_cam, foco_x, foco_y = 1.0 + 0.05 * (tl / 3.6), 0.72, 0.55
            elif tl < 6.4:
                hx = 270.0 + (tl - 3.6) * 65.0
                hy = chao_y - 56
                self.anim_p1.tocar("walk", loop=True)
                self.anim_boss.tocar("attack" if tl > 5.4 else "idle", loop=(tl <= 5.4))
                zoom_cam, foco_x, foco_y = 1.06 + (tl - 3.6) * 0.03, 0.55, 0.62
            else:
                u = min(1.0, (tl - 6.4) / 2.2)
                hx = 452.0 + u * 165.0
                hy = (chao_y - 56) - math.sin(u * math.pi * 0.85) * 145.0
                if u > 0.45:
                    if self._once("ato4_atk_aereo"):
                        self.anim_p1.tocar("attack_aereo", loop=False, duracao=1.3, forcar=True)
                else:
                    if self._once("ato4_jump_boss"):
                        self.anim_p1.tocar("jump", loop=False, duracao=0.9, forcar=True)
                        self.anim_boss.tocar("attack_parry", loop=False, duracao=1.8, forcar=True)
                if int(tl * 40) % 2 == 0 and u < 0.96:
                    self.particulas.emitir_faiscas(hx + 18, hy + 28, n=4, cores=((56, 189, 248), (224, 242, 254)), vel=110.0)
                if self._once("ato4_climax") and tl >= 8.55:
                    self.particulas.emitir_arco(hx + 30, hy + 20, dir_x=1, cor=(56, 189, 248), raio=95, dur=0.35)
                    self.particulas.emitir_onda(boss_x + 20, chao_y - 52, cor=(224, 242, 254), raio_max=220, dur=0.55)
                    self.shake_restante, self.shake_forca = 0.45, 14.0
                zoom_cam, foco_x, foco_y = 1.14 + u * 0.16, 0.62, 0.62

            self._desenhar_sala_base(6, 0.0, 0.0, t, portao_aberto=portao_aberto)
            self._render_actor(self.anim_boss, self.surf_mundo, pygame.Rect(int(boss_x), int(chao_y - 96), 72, 96), 0.0, 0.0, espelhar=True, escala_extra=1.35, cor_fb=(155, 45, 185), atacando=(tl > 5.4), eter=True)
            self._render_actor(self.anim_p1, self.surf_mundo, pygame.Rect(int(hx), int(hy), 36, 56), 0.0, 0.0, cor_fb=(100, 145, 225), atacando=(tl >= 6.4), eter=(tl >= 6.4))
            self.particulas.desenhar_fx_mundo(self.surf_mundo, 0.0, 0.0)
            self._blitar_gameplay_em_1080(zoom=zoom_cam, foco_x=foco_x, foco_y=foco_y)
            self.particulas.desenhar_poeira_1080(self.surf_1080, t, fator_eter=1.3)

            # Flash branco crescente no impacto exato do golpe de clímax (37.1s -> 37.5s)
            if tl >= 8.55:
                a_branco = int(255 * min(1.0, (tl - 8.55) / 0.40))
                self.flash_cor = (240, 249, 255)
                self.flash_alpha = float(a_branco)
            elif tl < 0.35:
                fade_preto = int(255 * (1.0 - tl / 0.35))

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
