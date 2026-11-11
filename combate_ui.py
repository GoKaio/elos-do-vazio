# -*- coding: utf-8 -*-
"""HUD e interface tática do combate 2.5D integrada ao sistema gótico procedural (ui_procedural)."""

import math
import pygame
import ui_procedural
import ui_medieval
from sprites import projetar_ponto_25d

COR_OURO_BRILHO = ui_procedural.COR_OURO_VIVO
COR_OURO_MEDIO  = ui_procedural.COR_LATAO_BORDA
COR_OURO_SOMBRA = ui_procedural.COR_OURO_ESCURO
COR_OURO_ESCURO = ui_procedural.COR_OURO_ESCURO
COR_PERGAMINHO  = ui_procedural.COR_BRANCO_PEROLA
COR_PERG_LUZ    = ui_procedural.COR_CINZA_TEXTO
COR_SANGUE_ESC  = ui_procedural.COR_VERMELHO_SOMB
COR_SANGUE_VIVO = ui_procedural.COR_VERMELHO_DANO
COR_AZUL_ETER   = ui_procedural.COR_AZUL_ETER
COR_VERDE_ALQ   = ui_procedural.COR_ESMERALDA_VIDA


def _retrato_sprite(frame, tamanho):
    if frame is None:
        return None
    try:
        rect = frame.get_bounding_rect(min_alpha=5)
        if rect.width < 4 or rect.height < 4:
            return pygame.transform.scale(frame, (tamanho, tamanho))
        pad = max(6, max(rect.width, rect.height) // 3)
        x, y = max(0, rect.x - pad), max(0, rect.y - pad)
        w = min(frame.get_width() - x, rect.width + pad * 2)
        h = min(frame.get_height() - y, rect.height + pad * 2)
        return pygame.transform.scale(frame.subsurface(pygame.Rect(x, y, w, h)), (tamanho, tamanho))
    except Exception:
        try:
            return pygame.transform.scale(frame, (tamanho, tamanho))
        except Exception:
            return None


def desenhar_hud_inimigos_coletivo(surface, combatentes_inimigos, inimigo_focado_ref, cam, tempo_combate, is_aoe, fonte_pequena, fonte_micro):
    """Renderiza mira tática e barra compacta sobre inimigos comuns (Chefes usam barra monumental no topo)."""
    if not combatentes_inimigos:
        return

    vivos = [
        (inim_ref, cb) for inim_ref, cb in combatentes_inimigos
        if getattr(inim_ref, "vivo", True) and getattr(inim_ref, "hp", 0) > 0
    ]

    for inim_ref, cb in vivos:
        rect_sprite = getattr(cb, "ultimo_rect_25d", None) or getattr(cb, "rect_tela", None)
        if rect_sprite is not None:
            pes_x = rect_sprite.centerx
            topo_y = rect_sprite.top - 18
            fator_pes = getattr(cb, "escala_atual", 1.0)
        else:
            if hasattr(cam, "projetar"):
                pes_x, pes_y, fator_pes = cam.projetar(cb.pos_mundo[0], cb.pos_mundo[1], cb.pos_mundo[2])
            else:
                pes_x, pes_y, fator_pes = projetar_ponto_25d(cb.pos_mundo[0], cb.pos_mundo[1], cb.pos_mundo[2], cam_x=cam.x, cam_y=cam.y)
            altura_proj = int(cb.altura_base * max(0.4, min(3.0, fator_pes * (1.3 if cb.is_boss else 1.0))))
            topo_y = int(pes_y - altura_proj - 22)
            larg_box = int(cb.largura_base * fator_pes)
            rect_sprite = pygame.Rect(int(pes_x - larg_box // 2), int(pes_y - altura_proj), larg_box, altura_proj)

        is_alvo = (inim_ref is inimigo_focado_ref)
        if is_aoe or is_alvo:
            ui_procedural.desenhar_reticulo_mira(
                surface, rect_sprite, tempo=tempo_combate,
                estilo="aoe" if is_aoe else "unitario"
            )

        if not cb.is_boss:
            max_hp = max(1, getattr(inim_ref, "max_hp", inim_ref.hp))
            lbl_nome = f"{inim_ref.nome}  {int(inim_ref.hp)}/{max_hp}"
            f_nome = (fonte_pequena if is_alvo else fonte_micro) or fonte_pequena
            if f_nome:
                cor_nome = ui_procedural.COR_OURO_VIVO if is_alvo else ui_procedural.COR_BRANCO_PEROLA
                txt_nome = f_nome.render(lbl_nome, True, cor_nome)
                nx = int(pes_x - txt_nome.get_width() // 2)
                ny = topo_y - 16
                surface.blit(f_nome.render(lbl_nome, True, (6, 8, 12)), (nx + 1, ny + 1))
                surface.blit(txt_nome, (nx, ny))

            bw = max(76, min(116, int(92 * fator_pes)))
            bx = int(pes_x - bw // 2)
            ui_procedural.desenhar_barra_segmentada(surface, bx, topo_y, bw, 10, inim_ref.hp, max_hp, segmentos=8)

        debuffs = getattr(inim_ref, "debuffs", [])
        if debuffs and fonte_micro:
            deb_y = topo_y - (24 if cb.is_boss else 32)
            cur_dx = int(pes_x - (len(debuffs) * 44) // 2)
            for deb in debuffs:
                lbl_d = f"{deb.get('icone', '*')} {deb.get('turnos', 1)}t"
                txt_d = fonte_micro.render(lbl_d, True, deb.get("cor", (255, 160, 100)))
                dw = txt_d.get_width() + 8
                ui_procedural.desenhar_moldura_gotica(surface, cur_dx, deb_y, dw, 15, chanfro=3, destacado=False, alpha=230, cantoneiras=False)
                surface.blit(txt_d, (cur_dx + 4, deb_y + 1))
                cur_dx += dw + 4


def desenhar_painel_viajante(surface, x, y, w, h, jogador_hp, jogador_max_hp, jogador_ap, max_ap, qtd_pocao, qtd_cristal, progresso, debuffs_jogador, anim_jog, fontes):
    """Painel de status do Viajante com moldura gótica escura, cantoneiras douradas e Éter em losango."""
    fonte_pequena = fontes.get("pequena")
    fonte_menu = fontes.get("menu", fontes.get("normal"))

    ui_procedural.desenhar_moldura_gotica(surface, x, y, w, h, chanfro=7, destacado=True, alpha=244, cantoneiras=True, cranios=False)

    rx, ry, rw, rh = x + 12, y + 12, 44, 44
    ui_procedural.desenhar_moldura_gotica(surface, rx, ry, rw, rh, chanfro=4, destacado=False, alpha=248, cantoneiras=False)
    personagem_jog = getattr(anim_jog, "personagem", None)
    if personagem_jog and personagem_jog.anims.get("idle"):
        ret_img = _retrato_sprite(personagem_jog.anims["idle"][0], rw - 6)
        if ret_img:
            surface.blit(ret_img, (rx + 3, ry + 3))

    nv = progresso.nivel if progresso else 1
    if fonte_pequena:
        nv_rend = fonte_pequena.render(f"NV.{nv}", True, ui_procedural.COR_OURO_VIVO)
        surface.blit(nv_rend, (rx + (rw - nv_rend.get_width()) // 2, ry + rh + 4))

    cx = rx + rw + 12
    nome_h = getattr(progresso, "nome_heroi", "Viajante") if progresso else "Viajante"
    # Linha 1: Nome truncado em max_width = 150px alinhado estritamente à esquerda
    f_nome_p = fontes.get("normal", fonte_menu or fonte_pequena)
    if f_nome_p:
        nome_u = str(nome_h or "Viajante").upper()
        if f_nome_p.size(nome_u)[0] > 150:
            while len(nome_u) > 1 and f_nome_p.size(nome_u + "...")[0] > 150:
                nome_u = nome_u[:-1]
            nome_u = nome_u + "..."
        surface.blit(f_nome_p.render(nome_u, True, ui_procedural.COR_OURO_VIVO), (cx, y + 10))

    # Linha 2: Barra de HP segmentada separada abaixo do nome
    bar_w = w - (rw + 36)
    ui_procedural.desenhar_barra_segmentada(surface, cx, y + 34, bar_w, 12, jogador_hp, jogador_max_hp, segmentos=12)

    # Linha 3 (>= 40px abaixo do nome): Vidas à esquerda e HP numérico à direita sem colisão
    if fonte_pequena:
        if progresso:
            vidas_str = f"Vidas {progresso.tentativas}/3"
            surface.blit(fonte_pequena.render(vidas_str, True, ui_procedural.COR_CINZA_TEXTO), (cx, y + 52))
        cor_hp = ui_procedural.COR_ESMERALDA_VIDA if jogador_hp > jogador_max_hp * 0.25 else ui_procedural.COR_VERMELHO_DANO
        hp_rend = fonte_pequena.render(f"{int(jogador_hp)} / {int(jogador_max_hp)} HP", True, cor_hp)
        surface.blit(hp_rend, (x + w - hp_rend.get_width() - 14, y + 52))

    sep_y = y + 76
    ui_procedural.desenhar_divisor_dourado(surface, x + 12, sep_y, w - 24)

    if fonte_pequena:
        surface.blit(fonte_pequena.render("ÉTER", True, ui_procedural.COR_AZUL_ETER), (x + 14, sep_y + 8))

    for ap_i in range(max_ap):
        ax = x + 66 + ap_i * 22
        ay = sep_y + 15
        ui_procedural.desenhar_cristal_eter(surface, ax, ay, tamanho=6, ativo=(ap_i < jogador_ap))

    itens_y = sep_y + 30
    if fonte_pequena:
        ui_procedural.desenhar_icone_tematico(surface, "frasco", x + 20, itens_y + 8, tamanho=14, aceso=(qtd_pocao > 0))
        surface.blit(fonte_pequena.render(f"Poções: {qtd_pocao}", True, (110, 231, 183)), (x + 32, itens_y))
        ui_procedural.desenhar_cristal_eter(surface, x + 152, itens_y + 8, tamanho=5, ativo=(qtd_cristal > 0))
        surface.blit(fonte_pequena.render(f"Éter: {qtd_cristal}", True, ui_procedural.COR_AZUL_ETER_CLARO), (x + 164, itens_y))

    if debuffs_jogador and fonte_pequena:
        deb_y = y - 22
        cur_dx = x + 8
        for deb in debuffs_jogador:
            lbl_deb = f"{deb.get('icone', '*')} {deb.get('turnos', 1)}t"
            txt_s = fonte_pequena.render(lbl_deb, True, deb.get("cor", (255, 140, 90)))
            w_deb = txt_s.get_width() + 10
            ui_procedural.desenhar_moldura_gotica(surface, cur_dx, deb_y, w_deb, 17, chanfro=3, alpha=235, cantoneiras=False)
            surface.blit(txt_s, (cur_dx + 5, deb_y + 1))
            cur_dx += w_deb + 5


def desenhar_menu_comandos(surface, x, y, menu_w, menu_h, estado, menu_categoria, opcao_principal, opcao_ataque, opcao_item, acoes_ataque, ap_atual, inimigo_focado_nome, fontes):
    """Menu de ações gótico em moldura chanfrada com rebites, ícones temáticos e realce vinho/ouro."""
    fonte = fontes.get("normal")
    fonte_pequena = fontes.get("pequena")
    fonte_micro = fontes.get("micro")

    ui_procedural.desenhar_moldura_gotica(surface, x, y, menu_w, menu_h, chanfro=7, destacado=True, alpha=246, cantoneiras=True, cranios=False)
    rects_botoes = []

    if menu_categoria == "PRINCIPAL":
        opcoes = [
            ("Atacar / Habilidades", "espada"),
            ("Itens de Suporte", "frasco"),
            ("Fugir da Batalha", "grade"),
        ]
        btn_h, espaco_y, ini_y = 34, 6, y + 10
        for i, (txt_op, ico_op) in enumerate(opcoes):
            r_btn = pygame.Rect(x + 16, ini_y + i * (btn_h + espaco_y), menu_w - 32, btn_h)
            rects_botoes.append((i, r_btn))
            ui_procedural.desenhar_botao_gotico(surface, r_btn, txt_op, fonte, selecionado=(i == opcao_principal), icone=ico_op)

    elif menu_categoria == "ATAQUES":
        btn_h, ini_y = 22, y + 6
        for i, acao in enumerate(acoes_ataque):
            sel = (i == opcao_ataque)
            custo = acao.get("custo", 0)
            tem_ap = (ap_atual >= custo)
            r_btn = pygame.Rect(x + 14, ini_y + i * (btn_h + 2), menu_w - 28, btn_h)
            rects_botoes.append((i, r_btn))

            ui_procedural.desenhar_botao_gotico(
                surface, r_btn, "", fonte_pequena,
                selecionado=sel, desabilitado=(not tem_ap and not sel)
            )
            ui_procedural.desenhar_cristal_eter(surface, r_btn.x + 16, r_btn.centery, tamanho=4, ativo=(custo > 0 and tem_ap))
            if fonte_pequena:
                cor_c = ui_procedural.COR_AZUL_ETER if tem_ap else ui_procedural.COR_VERMELHO_DANO
                surface.blit(fonte_pequena.render(f"{custo}", True, cor_c), (r_btn.x + 26, r_btn.y + 3))
                cor_txt = ui_procedural.COR_OURO_VIVO if sel else (ui_procedural.COR_BRANCO_PEROLA if tem_ap else ui_procedural.COR_CINZA_TEXTO)
                surface.blit(fonte_pequena.render(acao.get("nome", ""), True, cor_txt), (r_btn.x + 42, r_btn.y + 3))
                if acao.get("badge") and fonte_micro:
                    b_r = fonte_micro.render(acao["badge"], True, ui_procedural.COR_OURO_VIVO if sel else ui_procedural.COR_CINZA_TEXTO)
                    surface.blit(b_r, (r_btn.right - b_r.get_width() - 12, r_btn.y + 4))

    elif menu_categoria == "SELECAO_ALVO":
        if fonte_pequena:
            lbl_tit = fonte_pequena.render("SELECIONE O ALVO", True, ui_procedural.COR_OURO_VIVO)
            w_tot = lbl_tit.get_width() + 48
            tx_ini = x + (menu_w - w_tot) // 2
            surface.blit(lbl_tit, (tx_ini, y + 12))
            ui_procedural.desenhar_icone_botao(surface, tx_ini + lbl_tit.get_width() + 26, y + 12 + lbl_tit.get_height() // 2, "ALVOS", escala=0.88)
        ui_procedural.desenhar_divisor_dourado(surface, x + 22, y + 34, menu_w - 44)
        r_alvo = pygame.Rect(x + 18, y + 44, menu_w - 36, 42)
        rects_botoes.append((0, r_alvo))
        ui_procedural.desenhar_botao_gotico(surface, r_alvo, f"Alvo: {inimigo_focado_nome}", fonte, selecionado=True, icone="espada")
        if fonte_pequena:
            ic_ok = ui_procedural.desenhar_icone_botao(surface, x + 42, y + 109, "CONFIRMAR", escala=0.86)
            surface.blit(fonte_pequena.render("Confirmar", True, ui_procedural.COR_ESMERALDA_VIDA), (ic_ok.right + 6, y + 102))
            lbl_v = fonte_pequena.render("Voltar", True, ui_procedural.COR_CINZA_TEXTO)
            vx_txt = x + menu_w - 22 - lbl_v.get_width()
            ui_procedural.desenhar_icone_botao(surface, vx_txt - 18, y + 109, "CANCELAR", escala=0.86)
            surface.blit(lbl_v, (vx_txt, y + 102))

    elif menu_categoria == "ITENS":
        itens_menu = [
            ("Poção de Cura (+50 HP)", "frasco"),
            ("Frasco de Éter (+3 AP)", "cristal"),
        ]
        for i, (txt_it, ico_it) in enumerate(itens_menu):
            r_btn = pygame.Rect(x + 16, y + 14 + i * 46, menu_w - 32, 38)
            rects_botoes.append((i, r_btn))
            ui_procedural.desenhar_botao_gotico(surface, r_btn, txt_it, fonte, selecionado=(i == opcao_item), icone=ico_it)
        if fonte_micro or fonte_pequena:
            f_voltar = fonte_micro or fonte_pequena
            s_v = f_voltar.render("Voltar", True, ui_procedural.COR_CINZA_TEXTO)
            w_grp = 24 + 6 + s_v.get_width()
            gx = x + (menu_w - w_grp) // 2
            ic_v = ui_procedural.desenhar_icone_botao(surface, gx + 12, y + menu_h - 14, "CANCELAR", escala=0.80)
            surface.blit(s_v, (ic_v.right + 6, y + menu_h - 14 - s_v.get_height() // 2))

    return rects_botoes


def desenhar_linha_tempo_vertical(surface, x, y, timeline, tempo, anim_jog, fontes, deslocar_abaixo_badge=False):
    """Cartões verticais de iniciativa no canto esquerdo respeitando margem segura (16px)."""
    if not timeline:
        return
    x = max(16, int(x))
    y_ini = max(16, max(y, 56) if deslocar_abaixo_badge else y)

    for idx, turno in enumerate(timeline[:5]):
        ativo = (idx == 0)
        tamanho = 44 if ativo else 36
        ty = y_ini + idx * (tamanho + 7)
        card = pygame.Rect(x, ty, tamanho, tamanho)

        dono_tipo = turno["tipo"] if isinstance(turno, dict) else turno
        is_jogador = (dono_tipo == "JOGADOR")

        ui_procedural.desenhar_moldura_gotica(surface, card, chanfro=4, destacado=ativo, alpha=240, borda_ouro=is_jogador, cantoneiras=False)

        if is_jogador:
            p_j = getattr(anim_jog, "personagem", None)
            if p_j and p_j.anims.get("idle"):
                ret_img = _retrato_sprite(p_j.anims["idle"][0], tamanho - 6)
                if ret_img:
                    surface.blit(ret_img, (card.x + 3, card.y + 3))
        else:
            cb_ent = turno.get("cb") if isinstance(turno, dict) else None
            p_in = cb_ent.animador.personagem if (cb_ent and getattr(cb_ent, "animador", None)) else None
            if p_in and p_in.anims.get("idle"):
                ret_img = _retrato_sprite(p_in.anims["idle"][0], tamanho - 6)
                if ret_img:
                    surface.blit(ret_img, (card.x + 3, card.y + 3))

        if ativo:
            pygame.draw.polygon(
                surface, ui_procedural.COR_OURO_VIVO,
                [(card.right + 4, card.centery - 5), (card.right + 11, card.centery), (card.right + 4, card.centery + 5)]
            )


def desenhar_banner_central(surface, texto, cor=None, fontes=None, com_boss=False):
    """Banner limpo posicionado no terço médio superior (y=68 com Boss) sem colisões de HUD."""
    if not texto or not fontes or not fontes.get("normal"):
        return
    fonte = fontes["normal"]
    txt_s = fonte.render(str(texto)[:70], True, cor or ui_procedural.COR_OURO_VIVO)
    txt_sh = fonte.render(str(texto)[:70], True, (6, 8, 12))
    bw = max(250, txt_s.get_width() + 40)
    bh = 28
    bx = (960 - bw) // 2
    by = 68 if com_boss else 16

    ui_procedural.desenhar_moldura_gotica(surface, bx, by, bw, bh, chanfro=5, destacado=False, alpha=240, cantoneiras=False)
    tx = bx + (bw - txt_s.get_width()) // 2
    ty = by + (bh - txt_s.get_height()) // 2
    surface.blit(txt_sh, (tx + 1, ty + 1))
    surface.blit(txt_s, (tx, ty))


def desenhar_reacao_defensiva(surface, x, y, w, h, tipo_golpe, fontes):
    """Caixa compacta de comandos de defesa alinhada horizontalmente dentro de h=68."""
    fonte_pequena = fontes.get("pequena")
    if not fonte_pequena:
        return

    ui_procedural.desenhar_moldura_gotica(surface, x, y, w, h, chanfro=6, destacado=True, alpha=244, cantoneiras=True)
    lbl_tit = fonte_pequena.render("REAÇÃO DEFENSIVA", True, ui_procedural.COR_OURO_VIVO)
    surface.blit(lbl_tit, (x + (w - lbl_tit.get_width()) // 2, y + 7))
    ui_procedural.desenhar_divisor_dourado(surface, x + 18, y + 28, w - 36)

    s_tipo = str(tipo_golpe).upper()
    g_pulo = any(k in s_tipo for k in ("PULO", "ONDA", "RASTEIRA", "FENDA", "MIASMA", "INVESTIDA", "TERREMOTO"))
    g_parry = any(k in s_tipo for k in ("PARRY", "ESMAGAMENTO", "TITANICO", "QUEBRA", "RODOPIO"))
    g_desvio = any(k in s_tipo for k in ("DESVIO", "VENENO", "ECLIPSE", "RUGIDO", "ARCANO", "GARRAS"))

    cor_p = (80, 240, 255) if (g_parry or (not g_pulo and not g_desvio)) else ui_procedural.COR_CINZA_TEXTO
    cor_d = (100, 255, 140) if (g_desvio or (not g_pulo and not g_parry)) else ui_procedural.COR_CINZA_TEXTO
    cor_j = ui_procedural.COR_OURO_VIVO if g_pulo else ui_procedural.COR_CINZA_TEXTO

    itens = [
        ("PARRY", "Parry", cor_p),
        ("DESVIO", "Esquiva", cor_d),
        ("PULO", "Salto", cor_j),
    ]
    col_w = w // 3
    for idx, (acao_ic, lbl, cor_i) in enumerate(itens):
        s_i = fonte_pequena.render(lbl, True, cor_i)
        ic_w = 24 if not ui_procedural.INPUT_MANAGER.usar_controle() else 18
        tot_w = ic_w + 5 + s_i.get_width()
        ix = x + idx * col_w + (col_w - tot_w) // 2
        cy_i = y + 46
        ic_r = ui_procedural.desenhar_icone_botao(surface, ix + ic_w // 2, cy_i, acao_ic, escala=0.84)
        surface.blit(s_i, (ic_r.right + 5, cy_i - s_i.get_height() // 2))


def desenhar_painel_rank_combate(surface, resultado_rank, tempo_combate=0.0, eh_boss=False):
    """Exibe o brasão gótico de Rank S/A/B/C centralizado e sem sobreposições ao vencer o combate."""
    if not resultado_rank:
        return
    larg = surface.get_width()
    pw, ph = 310, 152
    px = (larg - pw) // 2
    py = 112 if eh_boss else 86
    painel = pygame.Rect(px, py, pw, ph)
    ui_procedural.desenhar_moldura_gotica(surface, painel, chanfro=7, destacado=True, alpha=242, cantoneiras=True)

    f_sub = ui_procedural.obter_fonte_serif(11, bold=False)
    lbl_t = f_sub.render(f"DESEMPENHO EM COMBATE · {tempo_combate:.1f}s", True, ui_procedural.COR_BRANCO_PEROLA)
    surface.blit(lbl_t, (painel.centerx - lbl_t.get_width() // 2, painel.top + 10))
    ui_procedural.desenhar_divisor_dourado(surface, painel.left + 20, painel.top + 28, pw - 40)

    ui_procedural.desenhar_brasao_rank(
        surface,
        painel.centerx,
        painel.top + 66,
        resultado_rank.get("rank", "C"),
        pontuacao=resultado_rank.get("pontuacao", 0),
        tamanho=60,
        sem_avaria=resultado_rank.get("sem_avaria", False),
        anim_t=tempo_combate,
    )


def desenhar_barra_boss_combate(surface, x, y, w, h, boss_ref, tempo, fontes, modo_boss_rush=False, boss_rush_idx=0, tempo_rush_str="00:00.00"):
    """Renderiza a barra monumental do Chefe e, no modo Boss Rush, o HUD de progresso/relógio."""
    if not boss_ref:
        return
    hp_atual = max(0, getattr(boss_ref, "hp", 0))
    if hp_atual <= 0 and not getattr(boss_ref, "vivo", True):
        return

    max_hp = max(1, getattr(boss_ref, "max_hp", max(1, hp_atual)))
    nome_raw = getattr(boss_ref, "nome", "CHEFE DO VAZIO")
    fases_totais = 3 if getattr(boss_ref, "num_combos", 3) >= 4 else 2
    fase_atual = 1 if hp_atual > max_hp / float(fases_totais) else fases_totais

    larg_bar = max(500, min(600, int(w)))
    bx = (surface.get_width() - larg_bar) // 2
    by = 28

    ui_procedural.desenhar_barra_boss_monumental(
        surface, bx, by, larg_bar, 12, hp_atual, max_hp, nome_raw,
        fase_atual=fase_atual, fases_totais=fases_totais, tempo=tempo,
        fonte_nome=fontes.get("media") or fontes.get("normal"),
        fonte_info=fontes.get("micro") or fontes.get("pequena"),
    )

    if modo_boss_rush:
        ui_procedural.desenhar_hud_boss_rush(surface, boss_rush_idx + 1, 7, tempo_rush_str)
