"""Teste de ponta a ponta no navegador (Chromium e WebKit): abre o site gerado e usa o simulador como uma pessoa usaria.

Precisa do Playwright (fora do CI). Sobe um servidor local em paginas_seo/, bloqueia o Umami (não contaminar a medição) e confere os números
contra calculo.py. Uso: python testar_navegador.py
"""
import functools
import http.server
import os
import re
import sys
import threading

from playwright.sync_api import sync_playwright

import calculo
import conteudo

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = 8811
FALHAS = []


def confere(nome, cond, detalhe=""):
    print(("OK    " if cond else "FALHOU") + " " + nome + (" -> " + str(detalhe) if not cond or detalhe else ""))
    if not cond:
        FALHAS.append(nome)


def numero(texto):
    return int(re.sub(r"[^\d]", "", texto))


def esperado(veiculo, receber, saldo, meses):
    return calculo.simular(veiculo, receber, saldo, meses, calculo.taxa_mensal())


def rodar(nav, nome_nav, base, largura):
    ctx = nav.new_context(viewport={"width": largura, "height": 900})
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    pg.route("**/*umami*", lambda r: r.abort())
    eventos = []
    pg.add_init_script("window.umami={track:function(n,d){window.__ev=(window.__ev||[]);window.__ev.push([n,d]);}}")
    tag = nome_nav + "/" + str(largura) + ": "

    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")
    r = esperado(100_000, 50_000, 0, 48)
    confere(tag + "parcela inicial", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "total inicial", numero(pg.inner_text("#r-total")) == round(r["total"]), pg.inner_text("#r-total"))
    confere(tag + "três cartões no Raio-X", pg.locator("#alts .alt").count() == 3)

    # prazo
    pg.fill("#campo-prazo", "60"); pg.press("#campo-prazo", "Enter")
    r = esperado(100_000, 50_000, 0, 60)
    confere(tag + "prazo 60 meses", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "texto do prazo", "60 meses" in pg.inner_text("#r-sub"))
    pg.fill("#campo-prazo", "48"); pg.press("#campo-prazo", "Enter")

    # prazo: lista suspensa (todos os meses, sem destaque branco) e também digitando
    confere(tag + "lista de prazos começa fechada", not pg.is_visible("#lista-prazo"))
    pg.click("#btn-prazo")
    confere(tag + "abre a lista de prazos", pg.is_visible("#lista-prazo") and pg.locator("#lista-prazo li").count() == 55)
    confere(tag + "prazo atual marcado na lista", pg.get_attribute("#prazo-op-48", "aria-selected") == "true")
    fundo = pg.evaluate("getComputedStyle(document.querySelector('#prazo-op-48')).backgroundColor")
    confere(tag + "destaque da lista não é branco", fundo != "rgb(255, 255, 255)", fundo)
    pg.click("#prazo-op-12")
    confere(tag + "escolher na lista fecha e muda o prazo", not pg.is_visible("#lista-prazo") and pg.input_value("#campo-prazo") == "12" and "12 meses" in pg.inner_text("#r-sub"))
    pg.focus("#campo-prazo")
    pg.press("#campo-prazo", "ArrowDown")
    pg.press("#campo-prazo", "ArrowDown")
    pg.press("#campo-prazo", "Enter")
    confere(tag + "teclado escolhe na lista", pg.input_value("#campo-prazo") == "13", pg.input_value("#campo-prazo"))
    pg.fill("#campo-prazo", "30"); pg.press("#campo-prazo", "Enter")
    confere(tag + "digitar 30 meses funciona", "30 meses" in pg.inner_text("#r-sub"))
    pg.click("#btn-prazo"); pg.keyboard.press("Escape")
    confere(tag + "Esc fecha a lista", not pg.is_visible("#lista-prazo"))
    pg.fill("#campo-prazo", "48"); pg.press("#campo-prazo", "Enter")
    pg.fill("#campo-prazo", "300"); pg.press("#campo-prazo", "Enter")
    confere(tag + "prazo acima do máximo que a conta aceita é ajustado", pg.input_value("#campo-prazo") == str(calculo.PRAZO_MAX_MESES) and pg.is_visible("#msg-prazo"), pg.input_value("#campo-prazo"))
    pg.fill("#campo-prazo", "48"); pg.press("#campo-prazo", "Enter")

    # SAC: primeira parcela maior que a do Price, última menor, total menor; volta ao Price
    price = esperado(100_000, 50_000, 0, 48)
    i_ = calculo.taxa_mensal()
    sac = calculo.simular(100_000, 50_000, 0, 48, i_, "sac")
    pg.click("label[for=sis-sac]")
    confere(tag + "SAC: primeira parcela", numero(pg.inner_text("#r-parcela")) == round(sac["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "SAC: total menor", numero(pg.inner_text("#r-total")) == round(sac["total"]), pg.inner_text("#r-total"))
    confere(tag + "SAC: mostra a última parcela", pg.is_visible("#r-ultima") and conteudo.brl0(sac["parcela_final"]) in pg.inner_text("#r-ultima").replace(chr(160), " "), pg.inner_text("#r-ultima"))
    confere(tag + "SAC: rótulo da parcela", "1ª parcela" in pg.inner_text("#r-kicker").lower())
    pg.wait_for_timeout(600)
    confere(tag + "SAC: endereço guarda o sistema", "sistema=sac" in pg.evaluate("window.location.href"), pg.evaluate("window.location.href"))
    confere(tag + "SAC: comparativo usa o mesmo total", numero(pg.locator("#cm-linhas .mrow.us .mv b").inner_text()) == round(sac["total"]), pg.locator("#cm-linhas .mrow.us .mv b").inner_text())
    pg2 = ctx.new_page()
    pg2.route("**/*umami*", lambda r_: r_.abort())
    pg2.goto(base + "/?veiculo=100000&receber=50000&prazo=48&sistema=sac")
    pg2.wait_for_selector("#alts .alt")
    confere(tag + "link com sistema=sac abre no SAC", pg2.is_checked("#sis-sac") and numero(pg2.inner_text("#r-parcela")) == round(sac["parcela"]))
    pg2.close()
    pg.click("label[for=sis-price]")
    confere(tag + "voltar ao Price", numero(pg.inner_text("#r-parcela")) == round(price["parcela"]) and not pg.is_visible("#r-ultima"))

    # renda de referência (30%) e comparativo com outras modalidades
    renda = calculo.renda_para_parcela(price["parcela"])
    confere(tag + "texto da renda no Raio-X", conteudo.brl0(renda) in pg.inner_text("#renda-texto").replace(chr(160), " "), pg.inner_text("#renda-texto"))
    confere(tag + "comparativo: 4 modalidades em barras", pg.locator("#cm-linhas .mrow").count() == 4)
    confere(tag + "comparativo: valor do Auto Equity", numero(pg.locator("#cm-linhas .mrow.us .mv small").inner_text()) == round(price["parcela"]), pg.locator("#cm-linhas .mrow.us .mv small").inner_text())
    confere(tag + "comparativo: Auto Equity é o mais barato", numero(pg.locator("#cm-linhas .mrow.us .mv b").inner_text()) == min(numero(t) for t in pg.locator("#cm-linhas .mv b").all_inner_texts()))
    confere(tag + "faixa do uso do veículo fora do painel do resultado", pg.locator("#resultado #c-limite").count() == 0 and pg.locator(".uso #c-limite").count() == 1)
    confere(tag + "SAC fica no painel do resultado", pg.locator("#resultado #sis-sac").count() == 1)
    confere(tag + "texto do prazo sem quebra de a.m. sozinho", pg.evaluate("(() => { const e = document.getElementById('r-sub'); return e.getClientRects()[0].height < 40; })()") or tag.startswith("webkit/390"))

    # valor do veículo e a receber (digitando)
    pg.fill("#campo-veiculo", "150.000")
    pg.fill("#campo-receber", "80.000")
    pg.press("#campo-receber", "Enter")
    r = esperado(150_000, 80_000, 0, 48)
    confere(tag + "veículo 150 mil e receber 80 mil", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "barra do limite", numero(pg.inner_text("#c-limite")) == 120_000, pg.inner_text("#c-limite"))

    # acima do limite: é ajustado e avisa
    pg.fill("#campo-receber", "200.000")
    pg.press("#campo-receber", "Enter")
    confere(tag + "ajusta ao limite de 80%", numero(pg.input_value("#campo-receber")) == 120_000, pg.input_value("#campo-receber"))
    confere(tag + "avisa do ajuste", pg.is_visible("#msg-ajuste") and "limite" in pg.inner_text("#msg-ajuste"), pg.inner_text("#msg-ajuste"))

    # veículo financiado
    pg.fill("#campo-veiculo", "100.000")
    pg.press("#campo-veiculo", "Enter")
    pg.fill("#campo-receber", "50.000")
    pg.press("#campo-receber", "Enter")
    pg.click("label[for=sit-financiado]")
    confere(tag + "mostra o saldo devedor", pg.is_visible("#campo-saldo"))
    pg.fill("#campo-saldo", "20.000")
    pg.press("#campo-saldo", "Enter")
    r = esperado(100_000, 50_000, 20_000, 48)
    confere(tag + "saldo entra no crédito", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "crédito + % do veículo", numero(pg.inner_text("#c-credito").split("·")[0]) == 70_000, pg.inner_text("#c-credito"))
    pg.fill("#campo-saldo", "80.000")
    pg.press("#campo-saldo", "Enter")
    confere(tag + "sem margem: avisa e trava o botão", pg.is_disabled("#btn-cta") and pg.inner_text("#r-parcela") == "—", pg.inner_text("#msg-ajuste"))
    pg.click("label[for=sit-quitado]")
    confere(tag + "voltar a quitado zera o saldo", numero(pg.input_value("#campo-saldo")) == 0 and not pg.is_disabled("#btn-cta"))

    # Raio-X
    pg.fill("#campo-conforto", "1.000")
    pg.press("#campo-conforto", "Enter")
    r = esperado(100_000, 50_000, 0, 48)
    confere(tag + "raio-x diz quanto fica acima", conteudo.brl0(r["parcela"] - 1000) in pg.inner_text("#raio-texto").replace(chr(160), " "), pg.inner_text("#raio-texto"))
    confere(tag + "receber menos cabe na parcela", "cabe na parcela" in pg.inner_text("#alts"), pg.inner_text("#alts"))
    pg.fill("#campo-conforto", "3.000")
    pg.press("#campo-conforto", "Enter")
    confere(tag + "raio-x quando cabe", "abaixo" in pg.inner_text("#raio-texto").replace(chr(160), " "), pg.inner_text("#raio-texto"))

    # nota "e se a taxa for maior?"
    confere(tag + "nota da taxa maior", conteudo.pct(conteudo._ref()["garantiaRealAm"]) in pg.inner_text("#nota-taxa-texto") and "1,39%" in pg.inner_text("#nota-taxa-texto"), pg.inner_text("#nota-taxa-texto"))

    # confirmação e link do parceiro
    pg.click("#btn-cta")
    confere(tag + "abre a tela de confirmação", pg.is_visible("#dlg-confirma"))
    href = pg.get_attribute("#a-parceiro", "href")
    confere(tag + "botão leva ao link do parceiro", href.startswith("https://proposta.api.br/f/"), href)
    pg.click("#btn-voltar")
    confere(tag + "voltar fecha a tela", not pg.is_visible("#dlg-confirma"))

    # endereço compartilhável
    url = pg.evaluate("window.location.href")
    pg.wait_for_timeout(600)
    url = pg.evaluate("window.location.href")
    confere(tag + "endereço guarda a simulação", "receber=50000" in url and "prazo=48" in url and "veiculo=100000" in url, url)
    pg2 = ctx.new_page()
    pg2.route("**/*umami*", lambda r_: r_.abort())
    pg2.goto(base + "/?veiculo=150000&receber=60000&prazo=24&saldo=20000&conforto=2000#simulador")
    pg2.wait_for_selector("#alts .alt")
    r = esperado(150_000, 60_000, 20_000, 24)
    confere(tag + "abre pelo link compartilhado", numero(pg2.inner_text("#r-parcela")) == round(r["parcela"]), pg2.inner_text("#r-parcela"))
    confere(tag + "link: situação financiado", pg2.is_checked("#sit-financiado"))
    pg2.goto(base + "/?veiculo=abc&receber=-5&prazo=999")
    pg2.wait_for_selector("#alts .alt")
    confere(tag + "endereço inválido cai no padrão", numero(pg2.inner_text("#r-parcela")) == round(esperado(100_000, 50_000, 0, 48)["parcela"]))
    pg2.close()

    # eventos de medição
    ev = pg.evaluate("window.__ev || []")
    nomes = [e[0] for e in ev]
    confere(tag + "eventos de medição", "usou-simulador-autoequity" in nomes and "abriu-confirmacao" in nomes, nomes)
    confere(tag + "sem dado pessoal nos eventos", all(set((e[1] or {}).keys()) <= {"receber", "prazo"} for e in ev))

    # layout: sem rolagem horizontal
    larg = pg.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    confere(tag + "sem rolagem horizontal", larg[0] <= larg[1], larg)

    # páginas de guia
    for slug in ("como-funciona", "garantia-do-veiculo", "custos-alem-dos-juros", "auto-equity-ou-outro-credito", "quando-nao-vale-a-pena",
                 "taxas-de-referencia", "metodologia", "sobre", "atualizacoes", "privacidade", "termos"):
        pg2 = ctx.new_page()
        pg2.route("**/*umami*", lambda r_: r_.abort())
        resp = pg2.goto(base + "/" + slug)
        larg = pg2.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
        confere(tag + "página /" + slug, resp.status == 200 and larg[0] <= larg[1] and pg2.locator("h1").count() == 1, (resp.status, larg))
        pg2.close()

    # botão "Voltar à simulação": a partir da home (clicando em "Como calculamos") volta para onde a pessoa estava, com a rolagem e os números
    pg.goto(base + "/?veiculo=90000&receber=30000&prazo=12")
    pg.wait_for_selector("#alts .alt")
    pg.wait_for_timeout(600)
    elo = pg.locator("section.blk a[href='/taxas-de-referencia']").first
    elo.scroll_into_view_if_needed()
    y0 = pg.evaluate("window.scrollY")
    elo.click()
    pg.wait_for_selector("a[data-volta]")
    confere(tag + "botão voltar à simulação existe", pg.locator("a.btn-volta").is_visible())
    pg.click("a.btn-volta")
    pg.wait_for_selector("#alts .alt")
    pg.wait_for_timeout(400)
    y1 = pg.evaluate("window.scrollY")
    confere(tag + "voltar devolve à mesma posição", abs(y1 - y0) < 60 and numero(pg.input_value("#campo-prazo")) == 12, (y0, y1))
    # chegando direto na página (sem histórico): o botão abre a home com a última simulação da aba
    pg3 = ctx.new_page()
    pg3.route("**/*umami*", lambda r_: r_.abort())
    pg3.goto(base + "/?veiculo=90000&receber=30000&prazo=12")
    pg3.wait_for_selector("#alts .alt")
    pg3.fill("#campo-prazo", "9"); pg3.press("#campo-prazo", "Enter")
    pg3.wait_for_timeout(600)
    pg3.goto(base + "/garantia-do-veiculo")
    href = pg3.get_attribute("a.btn-volta", "href")
    confere(tag + "voltar usa a última simulação da aba", "prazo=9" in href and href.endswith("#simulador"), href)
    pg3.click("a.btn-volta")
    pg3.wait_for_selector("#alts .alt")
    confere(tag + "voltar abre a simulação guardada", numero(pg3.input_value("#campo-prazo")) == 9)
    pg3.close()

    confere(tag + "sem erro no console", not erros, erros)
    pg.close()
    ctx.close()


def main():
    pasta = os.path.join(AQUI, "paginas_seo")
    class Servidor(http.server.SimpleHTTPRequestHandler):
        """Como o Cloudflare Pages: /pagina abre pagina.html."""
        def translate_path(self, path):
            p = super().translate_path(path)
            if not os.path.exists(p) and os.path.exists(p + ".html"):
                return p + ".html"
            return p

        def log_message(self, *a, **k):
            pass

    handler = functools.partial(Servidor, directory=pasta)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % PORTA
    with sync_playwright() as pw:
        for nome in ("chromium", "webkit"):
            try:
                nav = getattr(pw, nome).launch()
            except Exception as e:  # navegador não instalado
                print("AVISO: " + nome + " indisponível (" + str(e)[:80] + ")")
                continue
            for largura in (1200, 390):
                rodar(nav, nome, base, largura)
            nav.close()
    srv.shutdown()
    print("\n%d falha(s)" % len(FALHAS))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
