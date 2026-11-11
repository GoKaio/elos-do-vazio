# -*- coding: utf-8 -*-
"""UI original simples de ELOS DO VAZIO."""
import pygame

def iniciar():
    pass

def desenhar_barra_ui(surface, rect, ratio, cor="red", moldura="brown"):
    ratio = max(0.0, min(1.0, float(ratio)))
    fills = {
        "red": ((160, 35, 35), (210, 60, 50)),
        "yellow": ((170, 130, 25), (220, 180, 45)),
        "green": ((35, 120, 50), (60, 180, 75)),
        "blue": ((35, 80, 150), (60, 130, 200)),
    }
    c_dark, c_light = fills.get(cor, fills["red"])
    pygame.draw.rect(surface, (25, 16, 10), rect)
    pygame.draw.rect(surface, (140, 100, 40), rect, 2)
    pad = 3
    fw = int((rect.width - pad * 2) * ratio)
    if fw > 0:
        fr = pygame.Rect(rect.x + pad, rect.y + pad, fw, rect.height - pad * 2)
        pygame.draw.rect(surface, c_dark, fr)
        pygame.draw.rect(surface, c_light, (fr.x, fr.y, fr.width, max(1, fr.height // 3)))

def desenhar_botao_ui(surface, rect, selecionado=False):
    bg = (110, 78, 32) if selecionado else (55, 38, 20)
    border = (230, 190, 70) if selecionado else (120, 90, 45)
    pygame.draw.rect(surface, bg, rect)
    pygame.draw.rect(surface, border, rect, 2)

def desenhar_painel_ornamentado(surface, rect, alpha_fundo=230, pequeno=False):
    """Fallback: painel simples (UI original)."""
    pygame.draw.rect(surface, (48, 32, 18, min(255, alpha_fundo)), rect)
    pygame.draw.rect(surface, (180, 150, 60), rect, 2)

def desenhar_retrato_ornamentado(surface, rect, sprite_surf=None):
    """Retrato simples com borda dourada."""
    pygame.draw.rect(surface, (35, 22, 12), rect)
    if sprite_surf is not None:
        pad = 4
        inner = rect.width - pad * 2
        sp = pygame.transform.scale(sprite_surf, (inner, inner))
        surface.blit(sp, (rect.x + pad, rect.y + pad))
    pygame.draw.rect(surface, (200, 160, 50), rect, 2)

def painel_botao(largura=200, altura=36, estilo="brown"):
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    desenhar_botao_ui(s, s.get_rect(), selecionado=(estilo=="brown"))
    return s

def painel_escuro(largura, altura):
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    s.fill((40, 28, 16, 235))
    pygame.draw.rect(s, (150, 110, 50), s.get_rect(), 2)
    return s
