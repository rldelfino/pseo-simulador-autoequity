"""Teste aleatório da interface (fora do CI): ações aleatórias e, a cada passo, confere a tela contra calculo.py. Uso: python testar_aleatorio.py"""
import functools, http.server, os, random, re, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import calculo, conteudo

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = 8817
FALHAS = []
I = calculo.taxa_mensal()
GAR = conteudo._ref()["garantiaRealAm"] / 100  # média do BCB (garantia real), usada na nota "E se a taxa for maior?"


def num(t):
    d = re.sub(r"[^\d]", "", t or "")
    return int(d) if d else None


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, p):
        r = super().translate_path(p.split("?")[0])
        return r + ".html" if not os.path.exists(r) and os.path.exists(r + ".html") else r

    def log_message(self, *a):
        pass


def estado(pg):
    return pg.evaluate("""() => ({
      veiculo: document.getElementById('campo-veiculo').value, saldo: document.getElementById('campo-saldo').value,
      receber: document.getElementById('campo-receber').value, meses: document.getElementById('campo-prazo').value,
      fin: document.getElementById('sit-financiado').checked, sac: document.getElementById('sis-sac').checked,
      parcela: document.getElementById('r-parcela').textContent, total: document.getElementById('r-total').textContent,
      credito: document.getElementById('c-credito').textContent, limite: document.getElementById('c-limite').textContent,
      rotLim: document.getElementById('c-limite-rot').textContent,
      barra: document.getElementById('bar-fill').getAttribute('width'), marca: document.getElementById('bar-mark').getAttribute('x'),
      btnOff: document.getElementById('btn-cta').disabled, aviso: document.getElementById('msg-ajuste').hidden ? '' : document.getElementById('msg-ajuste').textContent,
      alts: [...document.querySelectorAll('#alts .alt')].map(a => a.innerText), nota: document.getElementById('nota-taxa-texto').textContent,
      rmin: document.getElementById('range-receber').min, rmax: document.getElementById('range-receber').max,
      url: location.href, ctav: document.getElementById('c-veiculo').textContent})""")


def confere(nome, cond, detalhe=""):
    if not cond:
        FALHAS.append((nome, detalhe))
        print("FALHOU", nome, detalhe)


def invariantes(pg, passo, acao):
    e = estado(pg)
    ve, sa, rc, me = num(e["veiculo"]), num(e["saldo"]) or 0, num(e["receber"]), int(e["meses"])
    t = "[%s] %s | " % (passo, acao)
    sis = "sac" if e["sac"] else "price"
    for k in ("parcela", "total", "credito", "limite", "ctav"):
        confere(t + "sem NaN em " + k, "NaN" not in e[k] and "Infinity" not in e[k] and "undefined" not in e[k], e[k])
    confere(t + "veículo dentro da faixa", calculo.VEICULO_MIN <= ve <= calculo.VEICULO_MAX, ve)
    confere(t + "prazo dentro da faixa", calculo.PRAZO_MIN_MESES <= me <= calculo.PRAZO_MAX_MESES, me)
    lim = calculo.limite_credito(ve)
    confere(t + "limite exibido = conta", abs(num(e["limite"]) - round(lim)) <= 1, (e["limite"], lim))
    rot_esperado = "teto" if calculo.LTV_MAX * ve > calculo.CREDITO_MAX else "80%"
    confere(t + "rótulo do limite", rot_esperado in e["rotLim"], e["rotLim"])
    # marca do limite na barra = limite/veículo
    confere(t + "marca da barra", abs(float(e["marca"].rstrip("%")) - min(99, lim / ve * 100)) < 0.2, (e["marca"], lim / ve * 100))
    if e["parcela"] == "—":
        confere(t + "sem margem: botão travado", e["btnOff"])
        return e
    confere(t + "botão liberado", not e["btnOff"])
    confere(t + "a receber dentro do limite", rc + sa <= lim + 1, (rc, sa, lim))
    confere(t + "a receber >= mínimo ou limite", rc >= min(calculo.RECEBER_MIN, lim - sa) - 1, (rc, lim - sa))
    r = calculo.simular(ve, rc, sa, me, I, sis)
    confere(t + "parcela", abs(num(e["parcela"]) - round(r["parcela"])) <= 1, (e["parcela"], r["parcela"]))
    confere(t + "total", abs(num(e["total"]) - round(r["total"])) <= 1, (e["total"], r["total"]))
    pct = int(re.search(r"(\d+)%", e["credito"]).group(1))
    if ve < 1000:   # veículo de poucos reais: a tela arredonda em reais inteiros, o % foge do 80% exato; não é caso de uso
        pass
    else:
      confere(t + "percentual do crédito", pct == int(r["ltv"] * 100 + 0.5), (e["credito"], r["ltv"] * 100))  # o JS arredonda .5 para cima; round() do Python arredonda para o par
      confere(t + "barra de uso", abs(float(e["barra"].rstrip("%")) - min(100, r["ltv"] * 100)) < 0.2, (e["barra"], r["ltv"] * 100))
    confere(t + "crédito exibido", abs(num(e["credito"].split("·")[0]) - round(r["credito"])) <= 1, e["credito"])
    # cartões do Raio-X: dois ou três e coerentes
    confere(t + "2 ou 3 cartões", len(e["alts"]) in (2, 3), len(e["alts"]))
    if len(e["alts"]) in (2, 3):
        p1 = num(e["alts"][0].split("\n")[1])
        confere(t + "cartão 1 = parcela", abs(p1 - round(r["parcela"])) <= 1, (p1, r["parcela"]))
        m = re.search(r"Receber (?:menos|mais): R\$\s?([\d.]+)", e["alts"][1] if len(e["alts"]) > 1 else "")
        if m:
            v = int(m.group(1).replace(".", ""))
            r2 = calculo.simular(ve, v, sa, me, I, sis)
            p2 = num(e["alts"][1].split("\n")[1])
            confere(t + "cartão 2 = conta", abs(p2 - round(r2["parcela"])) <= 1, (p2, r2["parcela"]))
            confere(t + "cartão 2 dentro do limite e do mínimo", calculo.RECEBER_MIN <= v and v + sa <= lim + 1, (v, lim))
        m3 = re.search(r"Prazo (?:maior|menor): (\d+) meses", e["alts"][-1])
        if m3:
            r3 = calculo.simular(ve, rc, sa, int(m3.group(1)), I, sis)
            p3 = num(e["alts"][-1].split("\n")[1])
            confere(t + "cartão 3 = conta", abs(p3 - round(r3["parcela"])) <= 1, (p3, r3["parcela"]))
    # nota da taxa maior (média do BCB para garantia real)
    mm = re.search(r"seria de R\$\s?([\d.]+)", e["nota"])
    if mm:
        rm = calculo.simular(ve, rc, sa, me, GAR, sis)
        confere(t + "nota taxa maior", abs(int(mm.group(1).replace(".", "")) - round(rm["parcela"])) <= 1, (mm.group(1), rm["parcela"]))
    return e


def rodar(nav, nome, seed, passos):
    rnd = random.Random(seed)
    ctx = nav.new_context(viewport={"width": 1100, "height": 900})
    ctx.route("**/*umami*", lambda r: r.abort())
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda x: erros.append(str(x)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:%d/" % PORTA)
    pg.wait_for_selector("#alts .alt")
    for k in range(passos):
        a = rnd.choice(["veiculo", "veiculo", "receber", "receber", "saldo", "prazo", "fin", "quit", "slider_v", "slider_r", "conforto", "sujo", "sis", "sis"])
        if a == "veiculo":
            v = rnd.choice([15000, 30000, 60000, 100000, 250000, 312500, 500000, 1234567, 2000000, 5555000, 9999, rnd.randint(15000, 1500000)])
            pg.fill("#campo-veiculo", f"{v:,}".replace(",", ".")); pg.press("#campo-veiculo", "Enter"); d = "veiculo=%d" % v
        elif a == "receber":
            v = rnd.choice([1, 4999, 5000, 20000, 50000, 80000, 150000, 400000, 9999999, rnd.randint(5000, 250000)])
            pg.fill("#campo-receber", f"{v:,}".replace(",", ".")); pg.press("#campo-receber", "Enter"); d = "receber=%d" % v
        elif a == "saldo":
            if not pg.is_checked("#sit-financiado"):
                pg.click("label[for=sit-financiado]")
            v = rnd.choice([0, 1000, 20000, 50000, 80000, 190000, 2000000, rnd.randint(0, 300000)])
            pg.fill("#campo-saldo", f"{v:,}".replace(",", ".")); pg.press("#campo-saldo", "Enter"); d = "saldo=%d" % v
        elif a == "prazo":
            v = rnd.randint(calculo.PRAZO_MIN_MESES, calculo.PRAZO_MAX_MESES); pg.fill("#campo-prazo", str(v)); pg.press("#campo-prazo", "Enter"); d = "prazo=%d" % v
        elif a == "fin":
            pg.click("label[for=sit-financiado]"); d = "financiado"
        elif a == "quit":
            pg.click("label[for=sit-quitado]"); d = "quitado"
        elif a == "slider_v":
            v = rnd.randint(15000, 500000)
            pg.evaluate("v=>{const r=document.getElementById('range-veiculo');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v); d = "slider veiculo %d" % v
        elif a == "slider_r":
            v = rnd.randint(5000, 80000)
            pg.evaluate("v=>{const r=document.getElementById('range-receber');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v); d = "slider receber %d" % v
        elif a == "sis":
            alvo_sis = rnd.choice(["price", "sac"]); pg.click("label[for=sis-%s]" % alvo_sis); d = "sistema=" + alvo_sis
        elif a == "conforto":
            v = rnd.choice([0, 1, 300, 1500, 5000, 50000]); pg.fill("#campo-conforto", str(v)); pg.press("#campo-conforto", "Enter"); d = "conforto=%d" % v
        else:
            campo = rnd.choice(["#campo-veiculo", "#campo-receber", "#campo-conforto"])
            lixo = rnd.choice(["abc", "", "--", "1e9", "0,0,0", "٣٣٣", "<b>1</b>", "9" * 30, "-5", "1.2.3.4", " "])
            pg.fill(campo, lixo); pg.press(campo, "Enter"); d = "lixo %s em %s" % (lixo[:8], campo)
        invariantes(pg, "%s#%d" % (nome, k), d)
    pg.wait_for_timeout(600)
    # o endereço reabre a mesma simulação
    e = estado(pg)
    pg2 = ctx.new_page()
    pg2.goto(e["url"])
    pg2.wait_for_selector("#resultado .big"); pg2.wait_for_timeout(500)
    e2 = estado(pg2)
    for k in ("parcela", "total", "credito", "veiculo", "receber", "meses", "sac"):
        confere("[%s] link compartilhado reabre igual: %s" % (nome, k), e[k] == e2[k], (e[k], e2[k]))
    confere("[%s] sem erro de JS" % nome, not erros, erros[:3])
    ctx.close()


def casos_fixos(nav):
    ctx = nav.new_context(viewport={"width": 1100, "height": 900})
    ctx.route("**/*umami*", lambda r: r.abort())
    pg = ctx.new_page()
    pg.goto("http://127.0.0.1:%d/" % PORTA); pg.wait_for_selector("#alts .alt")

    def setv(sel, v):
        pg.fill(sel, f"{v:,}".replace(",", ".")); pg.press(sel, "Enter")
    # "outro valor trava?" -> pedido preservado ao baixar e subir o valor do veículo
    setv("#campo-veiculo", 100_000); setv("#campo-receber", 60_000)
    setv("#campo-veiculo", 60_000)
    e = estado(pg); confere("baixar veículo ajusta receber ao limite (80%)", num(e["receber"]) == 48_000, e["receber"])
    setv("#campo-veiculo", 100_000)
    e = estado(pg); confere("subir veículo devolve o valor pedido (não trava)", num(e["receber"]) == 60_000, e["receber"])
    # ajustar receber manualmente depois de ter sido limitado: vale o novo
    setv("#campo-veiculo", 60_000); setv("#campo-receber", 20_000); setv("#campo-veiculo", 100_000)
    e = estado(pg); confere("pedido novo substitui o antigo", num(e["receber"]) == 20_000, e["receber"])
    # financiado: saldo e receber
    pg.click("label[for=sit-financiado]"); setv("#campo-saldo", 30_000); setv("#campo-receber", 60_000)
    e = estado(pg); confere("saldo 30k + receber 60k = 90k é cortado em 80k (receber 50k)", num(e["receber"]) == 50_000, e["receber"])
    pg.click("label[for=sit-quitado]")
    e = estado(pg); confere("voltar a quitado devolve limite cheio, receber pedido 60k", num(e["receber"]) == 60_000 and num(e["saldo"]) == 0, (e["receber"], e["saldo"]))
    # prazo não mexe em receber
    pg.fill("#campo-prazo", "12"); pg.press("#campo-prazo", "Enter")
    e = estado(pg); confere("prazo não altera o valor a receber", num(e["receber"]) == 60_000, e["receber"])
    # prazo fora da faixa é ajustado
    pg.fill("#campo-prazo", "500"); pg.press("#campo-prazo", "Enter")
    e = estado(pg); confere("prazo absurdo (500) vira o máximo que a conta aceita", int(e["meses"]) == calculo.PRAZO_MAX_MESES, e["meses"])
    pg.fill("#campo-prazo", "84"); pg.press("#campo-prazo", "Enter")
    e = estado(pg); confere("prazo de 84 meses (acima do controle, o parceiro não limita) é mantido", int(e["meses"]) == 84, e["meses"])
    # sem teto de crédito: só o LTV de 80%
    setv("#campo-veiculo", 1_000_000); setv("#campo-receber", 250_000)
    e = estado(pg); confere("crédito de R$ 250 mil não é cortado (sem teto da tela)", num(e["receber"]) == 250_000 and "80%" in e["rotLim"], (e["receber"], e["rotLim"]))
    setv("#campo-receber", 900_000)
    e = estado(pg); confere("acima de 80% do veículo vira o limite do parceiro", num(e["receber"]) == 800_000, e["receber"])
    # sem mínimo de negócio
    setv("#campo-receber", 1_000)
    e = estado(pg); confere("R$ 1.000 é aceito (sem mínimo da tela)", num(e["receber"]) == 1_000, e["receber"])
    print("   cartões com receber no mínimo:", estado(pg)["alts"][1].replace("\n", " | "))
    ctx.close()


def main():
    pasta = os.path.join(AQUI, "paginas_seo")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), functools.partial(H, directory=pasta))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        for nome in ("chromium", "webkit"):
            nav = getattr(pw, nome).launch()
            casos_fixos(nav)
            for seed in range(4):
                rodar(nav, nome + str(seed), seed, 70)
            nav.close()
    srv.shutdown()
    vistos = set()
    print("\n%d falha(s)" % len(FALHAS))
    for n, d in FALHAS:
        k = re.sub(r"^\[[^\]]*\] [^|]*\| ", "", n)
        if k not in vistos:
            vistos.add(k); print(" -", n, d)
    sys.exit(1 if FALHAS else 0)


main()
