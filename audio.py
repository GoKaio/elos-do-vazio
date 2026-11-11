# -*- coding: utf-8 -*-
"""
ELOS DO VAZIO - Sistema de Áudio (SFX e Músicas de Fundo - BGM).

Gerencia:
  1. Carregamento e reprodução de efeitos sonoros (.ogg) com cache e canais dedicados.
  2. Transições suaves e controle de faixas de música de fundo (.ogg).
  3. Resolução de caminhos transparente via caminhos.obter_caminho_recurso().
  4. Tolerância total a falhas (caso o dispositivo de áudio esteja indisponível).
"""
import os
import pygame
from caminhos import obter_caminho_recurso, log_info, log_aviso, log_erro

_MIXER_INICIALIZADO = False
_SOM_CACHE = {}
_MUSICA_ATUAL = None

VOLUME_MUSICA_PADRAO = 0.55
VOLUME_SFX_PADRAO = 0.75

def iniciar():
    """Inicializa o subsistema de áudio do Pygame com parâmetros de alta fidelidade."""
    global _MIXER_INICIALIZADO
    if _MIXER_INICIALIZADO:
        return True
    try:
        # 44.1kHz, 16-bit estéreo, buffer 1024 para baixa latência em efeitos de combate
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.set_num_channels(24)
        _MIXER_INICIALIZADO = True
        log_info("Sistema de áudio e mixer inicializados com sucesso (44.1kHz, 24 canais).")
        return True
    except Exception as e:
        log_aviso(f"Dispositivo de áudio não disponível ou erro no mixer: {e}. O jogo rodará sem som.")
        _MIXER_INICIALIZADO = False
        return False


def obter_som(nome):
    """Carrega e armazena em cache um efeito sonoro de assets/audio/sfx/."""
    if not _MIXER_INICIALIZADO:
        return None
    if nome in _SOM_CACHE:
        return _SOM_CACHE[nome]

    # Suporta nome com ou sem extensão
    nome_arq = nome if nome.endswith(".ogg") else f"{nome}.ogg"
    caminho = obter_caminho_recurso(os.path.join("assets", "audio", "sfx", nome_arq))
    
    if os.path.exists(caminho):
        try:
            snd = pygame.mixer.Sound(caminho)
            snd.set_volume(VOLUME_SFX_PADRAO)
            _SOM_CACHE[nome] = snd
            return snd
        except Exception as e:
            log_aviso(f"Erro ao carregar efeito sonoro '{caminho}': {e}")
            _SOM_CACHE[nome] = None
            return None
    else:
        log_aviso(f"Efeito sonoro não encontrado: {caminho}")
        _SOM_CACHE[nome] = None
        return None


def tocar_sfx(nome, mult_volume=1.0):
    """Toca um efeito sonoro caso o áudio esteja ativo."""
    if not _MIXER_INICIALIZADO:
        return
    snd = obter_som(nome)
    if snd is not None:
        try:
            vol = max(0.0, min(1.0, VOLUME_SFX_PADRAO * mult_volume))
            snd.set_volume(vol)
            snd.play()
        except Exception:
            pass


def tocar_musica(nome_faixa, loop=True, fade_ms=800):
    """Troca a música atual com fade suave se a faixa for diferente da que está tocando."""
    global _MUSICA_ATUAL
    if not _MIXER_INICIALIZADO:
        return

    nome_arq = nome_faixa if nome_faixa.endswith(".ogg") else f"{nome_faixa}.ogg"
    if _MUSICA_ATUAL == nome_arq and pygame.mixer.music.get_busy():
        return  # Já está tocando esta mesma música

    caminho = obter_caminho_recurso(os.path.join("assets", "audio", "music", nome_arq))
    if not os.path.exists(caminho):
        log_aviso(f"Música de fundo não encontrada: {caminho}")
        return

    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(VOLUME_MUSICA_PADRAO)
        pygame.mixer.music.play(-1 if loop else 1, fade_ms=fade_ms)
        _MUSICA_ATUAL = nome_arq
        log_info(f"Reproduzindo música de fundo: '{nome_arq}'.")
    except Exception as e:
        log_aviso(f"Erro ao reproduzir música '{caminho}': {e}")


def parar_musica(fade_ms=600):
    """Interrompe a música atual suavemente."""
    global _MUSICA_ATUAL
    if not _MIXER_INICIALIZADO:
        return
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
        _MUSICA_ATUAL = None
    except Exception:
        pass


def definir_volume_musica(volume):
    """Ajusta o volume da música de 0.0 a 1.0."""
    global VOLUME_MUSICA_PADRAO
    VOLUME_MUSICA_PADRAO = max(0.0, min(1.0, float(volume)))
    if _MIXER_INICIALIZADO:
        try:
            pygame.mixer.music.set_volume(VOLUME_MUSICA_PADRAO)
        except Exception:
            pass


def definir_volume_sfx(volume):
    """Ajusta o volume dos efeitos sonoros de 0.0 a 1.0."""
    global VOLUME_SFX_PADRAO
    VOLUME_SFX_PADRAO = max(0.0, min(1.0, float(volume)))
    for snd in _SOM_CACHE.values():
        if snd is not None:
            try:
                snd.set_volume(VOLUME_SFX_PADRAO)
            except Exception:
                pass
