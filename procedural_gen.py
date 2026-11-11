# -*- coding: utf-8 -*-
"""Motor matemático procedural (BSP, Autômatos Celulares, Ruído Simplex e Projeção Cônica 2.5D)."""

import math
import random


class RuidoSimplex:
    """Ruído Simplex 2D determinístico em Python puro (derivado de pyprocgen)."""

    _GRAD3 = (
        (1, 1), (-1, 1), (1, -1), (-1, -1),
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (-1, 1), (1, -1), (-1, -1),
    )
    _F2 = 0.5 * (math.sqrt(3.0) - 1.0)
    _G2 = (3.0 - math.sqrt(3.0)) / 6.0

    def __init__(self, semente=0):
        rng = random.Random(semente)
        perm = list(range(256))
        rng.shuffle(perm)
        self.perm = tuple(perm * 2)

    def noise2(self, x, y):
        s = (x + y) * self._F2
        i = math.floor(x + s)
        j = math.floor(y + s)
        t = (i + j) * self._G2
        x0 = x - (i - t)
        y0 = y - (j - t)

        i1, j1 = (1, 0) if x0 > y0 else (0, 1)
        x1 = x0 - i1 + self._G2
        y1 = y0 - j1 + self._G2
        x2 = x0 + self._G2 * 2.0 - 1.0
        y2 = y0 + self._G2 * 2.0 - 1.0

        ii = int(i) & 255
        jj = int(j) & 255
        perm = self.perm
        gi0 = perm[ii + perm[jj]] % 12
        gi1 = perm[ii + i1 + perm[jj + j1]] % 12
        gi2 = perm[ii + 1 + perm[jj + 1]] % 12

        noise = 0.0
        for cx, cy, gi in ((x0, y0, gi0), (x1, y1, gi1), (x2, y2, gi2)):
            tt = 0.5 - cx * cx - cy * cy
            if tt > 0.0:
                g = self._GRAD3[gi]
                noise += (tt ** 4) * (g[0] * cx + g[1] * cy)
        return noise * 70.0


class BSPNo:
    """Nó da árvore Binary Space Partitioning para divisão orgânica de câmaras (derivado de pybsp)."""

    def __init__(self, x, y, w, h, rng, min_w=240, min_h=150, prof=0):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.esq = None
        self.dir = None
        self.sala = None
        self._dividir(rng, min_w, min_h, prof)

    def _dividir(self, rng, min_w, min_h, prof):
        if prof >= 4:
            return
        pode_h = self.h >= min_h * 2
        pode_v = self.w >= min_w * 2
        if not pode_h and not pode_v:
            return

        if pode_h and pode_v:
            split_h = (self.h / float(max(1, self.w))) > 0.65 if rng.random() < 0.7 else (rng.random() >= 0.5)
        else:
            split_h = pode_h

        if split_h:
            corte = rng.randint(min_h, self.h - min_h)
            self.esq = BSPNo(self.x, self.y, self.w, corte, rng, min_w, min_h, prof + 1)
            self.dir = BSPNo(self.x, self.y + corte, self.w, self.h - corte, rng, min_w, min_h, prof + 1)
        else:
            corte = rng.randint(min_w, self.w - min_w)
            self.esq = BSPNo(self.x, self.y, corte, self.h, rng, min_w, min_h, prof + 1)
            self.dir = BSPNo(self.x + corte, self.y, self.w - corte, self.h, rng, min_w, min_h, prof + 1)

    def folhas(self):
        if self.esq is None and self.dir is None:
            return [self]
        res = []
        if self.esq:
            res.extend(self.esq.folhas())
        if self.dir:
            res.extend(self.dir.folhas())
        return res


def gerar_camaras_bsp(x0, y0, largura, altura, semente=1, min_w=260, min_h=160):
    """Particiona um retângulo arquitetônico por BSP e retorna câmaras góticas internas."""
    rng = random.Random(semente)
    raiz = BSPNo(x0, y0, largura, altura, rng, min_w=min_w, min_h=min_h)
    camaras = []
    for folha in raiz.folhas():
        pad_x = rng.randint(14, 28)
        pad_y = rng.randint(12, 24)
        rw = max(120, folha.w - pad_x * 2)
        rh = max(90, folha.h - pad_y * 2)
        camaras.append((folha.x + pad_x, folha.y + pad_y, rw, rh))
    return camaras


def gerar_caverna_automato_celular(colunas, linhas, semente=1, densidade_rocha=0.44, iteracoes=4):
    """
    Gera matriz 2D de caverna subterrânea por autômatos celulares (regra 4-5):
    0 = espaço escavado (ar), 1 = rocha bruta, 2 = musgo/umidade, 3 = poça d'água.
    """
    rng = random.Random(semente)
    grade = [
        [1 if (x == 0 or x == colunas - 1 or y == linhas - 1 or rng.random() < densidade_rocha) else 0
         for x in range(colunas)]
        for y in range(linhas)
    ]

    for _ in range(iteracoes):
        nova = [[1] * colunas for _ in range(linhas)]
        for y in range(linhas):
            for x in range(colunas):
                if x == 0 or x == colunas - 1 or y == linhas - 1:
                    nova[y][x] = 1
                    continue
                if y == 0:
                    nova[y][x] = 0
                    continue
                vizinhos = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < linhas and 0 <= nx < colunas:
                            vizinhos += 1 if grade[ny][nx] == 1 else 0
                        else:
                            vizinhos += 1
                if grade[y][x] == 1:
                    nova[y][x] = 1 if vizinhos >= 4 else 0
                else:
                    nova[y][x] = 1 if vizinhos >= 5 else 0
        grade = nova

    # Adiciona vegetação úmida (musgo) e poças d'água nos contornos rochosos
    ruido = RuidoSimplex(semente + 77)
    for y in range(1, linhas - 1):
        for x in range(1, colunas - 1):
            if grade[y][x] == 0:
                if grade[y - 1][x] == 1 and ruido.noise2(x * 0.25, y * 0.25) > 0.12:
                    grade[y][x] = 2  # Musgo/raízes no teto da rocha
                elif grade[y + 1][x] == 1 and ruido.noise2(x * 0.3, y * 0.3) > 0.22:
                    grade[y][x] = 3  # Poça de umidade no solo

    return grade


def projetar_ponto_conico(x_mundo, y_mundo, z_mundo, centro_x, horizonte_y, distancia_focal=320.0):
    """
    Projeção cônica de perspectiva 2.5D:
      X_tela = X_centro + (X * f) / (Z + f)
      Y_tela = Y_horizonte + (Y * f) / (Z + f)
    Retorna (tela_x, tela_y, escala).
    """
    denom = max(12.0, float(z_mundo) + float(distancia_focal))
    escala = float(distancia_focal) / denom
    tela_x = centro_x + float(x_mundo) * escala
    tela_y = horizonte_y + float(y_mundo) * escala
    return tela_x, tela_y, escala


def gerar_faixas_1_sobre_z(z_frente, z_fundo, num_faixas):
    """Calcula profundidades Z com progressão geométrica proporcional a 1/Z para lajes de perspectiva."""
    inv_frente = 1.0 / max(20.0, 320.0 + float(z_frente))
    inv_fundo = 1.0 / max(20.0, 320.0 + float(z_fundo))
    valores = []
    for i in range(num_faixas + 1):
        frac = i / float(max(1, num_faixas))
        inv_z = inv_fundo + frac * (inv_frente - inv_fundo)
        valores.append((1.0 / max(1e-5, inv_z)) - 320.0)
    return valores

