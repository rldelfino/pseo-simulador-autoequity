"""Teste de navegador (Chromium e WebKit, computador e celular) da amortização por blocos de 6 meses, de "pagar antes" e do "quitar dívida cara".

Sobe paginas_seo/ localmente, bloqueia o Umami e confere cada número contra calculo.py. Uso: python testar_amort_quitar.py (precisa do Playwright; fora do CI).
"""
import functools
import http.server
import os
import re
import sys
import threading

from playwright.sync_api import sync_playwright

import calculo
import gerador_autoequity as g

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = 8812
FALHAS = []
REF = g.referencias()
I = calculo.taxa_mensal()


def confere(nome, cond, detalhe=""):
    print(("OK    " if cond else "FALHOU") + " " + nome + (" -> " + str(detalhe) if not cond or detalhe else ""))
    if not cond:
        FALHAS.append(nome)


def n(texto):
    return int(re.sub(r"[^\d]", "", texto))


def linhas_tabela(pg):
    return pg.eval_on_selector_all("#amort-corpo tr", "trs => trs.map(t => [...t.children].map(c => c.textContent))")


def rodar(nav, nome_nav, base, largura):
    tag = nome_nav + "/" + str(largura)
    ctx = nav.new_context(viewport={"width": largura, "height": 900})
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    pg.route("**/*umami*", lambda r: r.abort())
    eventos = []
    pg.add_init_script("window.umami={track:function(n,d){window.__ev=(window.__ev||[]);window.__ev.push([n,d||null]);}};")
    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")

    # --- amortização
    ab = pg.evaluate("document.getElementById('det-amort').open")
    confere(tag + ": amortização começa recolhida", ab is False)
    pg.click("#det-amort summary")
    confere(tag + ": abre ao clicar", pg.evaluate("document.getElementById('det-amort').open") is True)
    r = calculo.simular(100_000, 50_000, 0, 48, I)
    esp = calculo.amortizacao_periodos(r["credito"], I, 48)
    lin = linhas_tabela(pg)
    confere(tag + ": 8 linhas de 6 meses", len(lin) == 8 and lin[0][0] == "1 a 6" and lin[-1][0] == "43 a 48", [l[0] for l in lin])
    ok = all(n(l[1]) == round(e["juros"]) and n(l[2]) == round(e["amortizacao"]) and n(l[3]) == round(e["saldo"]) for l, e in zip(lin, esp))
    confere(tag + ": tabela igual ao calculo.py", ok, lin[0])
    confere(tag + ": saldo final zero", n(lin[-1][3]) == 0)
    # muda prazo e valor: a tabela acompanha
    pg.fill("#campo-prazo", "30"); pg.press("#campo-prazo", "Enter")
    pg.fill("#campo-receber", "30.000")
    pg.press("#campo-receber", "Enter")
    pg.wait_for_timeout(300)
    r2 = calculo.simular(100_000, 30_000, 0, 30, I)
    esp2 = calculo.amortizacao_periodos(r2["credito"], I, 30)
    lin2 = linhas_tabela(pg)
    confere(tag + ": tabela acompanha prazo e valor", len(lin2) == 5 and all(n(l[1]) == round(e["juros"]) and n(l[3]) == round(e["saldo"]) for l, e in zip(lin2, esp2)), len(lin2))
    resumo = pg.inner_text("#amort-resumo")
    pago = r2["parcela"] * 6
    confere(tag + ": resumo cita juros dos primeiros 6 meses", ("%d%%" % round(esp2[0]["juros"] / pago * 100)) in resumo and "primeiros 6 meses" in resumo, resumo)
    rodape = pg.inner_text("#amort-rodape")
    confere(tag + ": total de juros no rodapé", n(rodape.split("\t")[1]) == round(sum(e["juros"] for e in esp2)), rodape)

    # --- prazo livre (em meses), rosca e gráficos
    for meses in (12, 30, 54):
        pg.fill("#campo-prazo", str(meses))
        pg.wait_for_timeout(120)
        rr = calculo.simular(100_000, 30_000, 0, meses, I)
        confere(tag + ": prazo digitado de %d meses" % meses, str(meses) + " meses" in pg.inner_text("#r-sub") and n(pg.inner_text("#r-parcela")) == round(rr["parcela"]) and
                pg.locator("#amort-graf .g-a").count() == -(-meses // 6), pg.inner_text("#r-sub"))
        confere(tag + ": rosca acompanha o prazo de %d meses" % meses, pg.text_content("#rosca-pct") == "%d%%" % round(rr["juros"] / rr["total"] * 100) and
                n(pg.inner_text("#rosca-juros-v")) == round(rr["juros"]), pg.text_content("#rosca-pct"))
    pg.fill("#campo-prazo", "500")
    pg.press("#campo-prazo", "Enter")
    confere(tag + ": prazo acima do máximo vira %d e avisa" % calculo.PRAZO_MAX_MESES, pg.input_value("#campo-prazo") == str(calculo.PRAZO_MAX_MESES) and "%d meses" % calculo.PRAZO_MAX_MESES in pg.inner_text("#msg-prazo") and pg.is_visible("#msg-prazo"))
    pg.evaluate("(()=>{const r=document.getElementById('range-prazo');r.value='18';r.dispatchEvent(new Event('input',{bubbles:true}));})()")
    confere(tag + ": controle deslizante do prazo", pg.input_value("#campo-prazo") == "18" and "18 meses" in pg.inner_text("#r-sub") and pg.locator("#amort-graf .g-a").count() == 3)
    confere(tag + ": painéis de cenário e resultado com a mesma altura", abs(pg.evaluate("document.querySelector('.grid>.panel').offsetHeight - document.getElementById('resultado').offsetHeight")) <= 1 or largura < 900)

    # --- pagar antes (extra mensal R$ 200 + única R$ 5.000 depois da 6ª parcela, valores padrão)
    pg.goto(base + "/")
    pg.evaluate("document.getElementById('det-amsim').open = true")  # o simulador de pagar a mais começa recolhido
    pg.wait_for_selector("#am-cartoes .amc")
    base_ = calculo.amortizar_antes(50_000, I, 48, "price", 0, 0, 6, "prazo")
    extra = calculo.amortizar_antes(50_000, I, 48, "price", 200, 0, 0, "prazo")
    unico_p = calculo.amortizar_antes(50_000, I, 48, "price", 0, 5000, 6, "prazo")
    unico_c = calculo.amortizar_antes(50_000, I, 48, "price", 0, 5000, 6, "parcela")
    juntos = calculo.amortizar_antes(50_000, I, 48, "price", 200, 5000, 6, "prazo")
    big = [n(t) for t in pg.locator("#am-cartoes .amc .big").all_inner_texts()]
    esperados = [round(base_["juros"] - x["juros"]) for x in (juntos, extra, unico_p, unico_c)]
    confere(tag + ": pagar antes: 4 cartões com a economia do calculo.py", big == esperados, (big, esperados))
    confere(tag + ": pagar antes: rótulo do momento", "depois da 6ª parcela" in pg.inner_text("#quando-rot"), pg.inner_text("#quando-rot"))
    pg.evaluate("(()=>{const r=document.getElementById('range-quando');r.value='0';r.dispatchEvent(new Event('input',{bubbles:true}));})()")
    confere(tag + ": pagar antes: no início", "antes da 1ª parcela" in pg.inner_text("#quando-rot"))

    # --- quitar dívida
    pg.goto(base + "/")
    pg.wait_for_selector("#q-cartoes .alt")
    cartoes = pg.inner_text("#q-cartoes")
    q = calculo.comparar_quitacao(20_000, REF["pessoalAm"] / 100, 48, I)
    confere(tag + ": padrão mostra a parcela na taxa média e no Auto Equity", str(round(q["parcela_atual"])) in re.sub(r"[^\d\n]", "", cartoes.replace(".", "")) and
            str(round(q["parcela_ae"])) in cartoes.replace(".", ""), cartoes[:120])
    for tipo, chave in (("cheque", "chequeAm"), ("rotativo", "rotativoAm"), ("pessoal", "pessoalAm")):
        pg.click("label[for=div-" + tipo + "]")
        pg.wait_for_timeout(150)
        qq = calculo.comparar_quitacao(20_000, REF[chave] / 100, 48, I)
        txt = pg.inner_text("#q-cartoes").replace(".", "")
        confere(tag + ": tipo " + tipo, str(round(qq["parcela_atual"])) in txt and str(round(qq["parcela_ae"])) in txt, txt[:90])
    confere(tag + ": gráfico de barras da dívida (4 barras)", pg.locator("#q-grafico .r").count() == 4, pg.locator("#q-grafico .r").count())
    # valor da dívida
    pg.fill("#campo-divida", "40.000")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    q3 = calculo.comparar_quitacao(40_000, REF["pessoalAm"] / 100, 48, I)
    txt = pg.inner_text("#q-cartoes").replace(".", "")
    confere(tag + ": valor da dívida", str(round(q3["parcela_atual"])) in txt and str(round(q3["parcela_ae"])) in txt)
    # taxa própria
    pg.click("label[for=div-outra]")
    confere(tag + ": campo de taxa aparece", pg.is_visible("#campo-taxa-div"))
    pg.fill("#campo-taxa-div", "3,5")
    pg.press("#campo-taxa-div", "Enter")
    pg.wait_for_timeout(200)
    q4 = calculo.comparar_quitacao(40_000, 0.035, 48, I)
    txt = pg.inner_text("#q-cartoes").replace(".", "")
    confere(tag + ": taxa própria", str(round(q4["parcela_atual"])) in txt and "Na taxa da sua dívida (3,50% a.m.)" in pg.inner_text("#q-cartoes"), txt[:90])
    # taxa menor que a do Auto Equity: sem economia
    pg.fill("#campo-taxa-div", "1")
    pg.press("#campo-taxa-div", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": taxa baixa não promete economia", "não reduz a parcela" in pg.inner_text("#q-texto"), pg.inner_text("#q-texto"))
    # taxa inválida
    pg.fill("#campo-taxa-div", "99")
    pg.press("#campo-taxa-div", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": taxa absurda avisa e esconde o resultado", pg.is_visible("#q-aviso") and pg.locator("#q-cartoes .alt").count() == 0 and pg.is_disabled("#btn-usar-divida"))
    pg.fill("#campo-taxa-div", "")
    pg.press("#campo-taxa-div", "Enter")
    pg.fill("#campo-taxa-div", "6")
    pg.press("#campo-taxa-div", "Enter")
    # dívida abaixo do mínimo e acima do limite
    pg.fill("#campo-divida", "3.000")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": dívida pequena é simulada sem aviso de mínimo", not pg.is_visible("#q-aviso") and pg.is_enabled("#btn-usar-divida"))
    pg.fill("#campo-divida", "2.000.000")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": dívida acima do limite usa o limite", "limite do veículo cobre até" in pg.inner_text("#q-aviso"), pg.inner_text("#q-aviso"))
    pg.fill("#campo-divida", "")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": dívida vazia pede o valor", "Informe quanto" in pg.inner_text("#q-aviso"))
    # botão "simular com este valor"
    pg.fill("#campo-divida", "45.000")
    pg.press("#campo-divida", "Enter")
    pg.click("#btn-usar-divida")
    pg.wait_for_timeout(300)
    confere(tag + ": 'Simular com este valor' leva a dívida ao campo de receber", n(pg.input_value("#campo-receber")) == 45_000, pg.input_value("#campo-receber"))
    pg.fill("#campo-divida", "3.000")
    pg.press("#campo-divida", "Enter")
    pg.click("#btn-usar-divida")
    pg.wait_for_timeout(300)
    confere(tag + ": dívida pequena vai inteira ao campo (sem mínimo da tela)", n(pg.input_value("#campo-receber")) == 3_000, pg.input_value("#campo-receber"))
    # medição
    ev = pg.evaluate("window.__ev || []")
    nomes = [e[0] for e in ev]
    confere(tag + ": eventos novos uma vez cada", nomes.count("usou-quitar-divida") == 1 and nomes.count("abriu-amortizacao") == 0 and all(x.endswith("autoequity") or "-" in x for x in nomes), nomes)
    confere(tag + ": sem dado pessoal nos eventos", all(set((e[1] or {}).keys()) <= {"tipo", "prazo", "receber"} for e in ev), ev)
    # sem rolagem lateral e sem erro
    ow = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
    confere(tag + ": sem rolagem horizontal", ow <= 0, ow)
    confere(tag + ": sem erro no console", not [e for e in erros if "beacon" not in e.lower() and "cloudflareinsights" not in e.lower()], erros[:2])
    ctx.close()


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.join(AQUI, "paginas_seo"))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % PORTA
    with sync_playwright() as p:
        for nome, motor in (("chromium", p.chromium), ("webkit", p.webkit)):
            nav = motor.launch()
            for largura in (1280, 390):
                rodar(nav, nome, base, largura)
            nav.close()
    srv.shutdown()
    print("\n%d falha(s)" % len(FALHAS))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
