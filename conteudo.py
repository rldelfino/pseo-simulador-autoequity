"""Conteúdo das páginas. Cada página tem texto próprio; nada de páginas quase iguais.

Regras: nenhum número que não venha de calculo.py, dos dados do Banco Central (dados/taxas_referencia.csv) ou de uma fonte citada; nenhum banco citado
nem ranking; sem prometer aprovação; tom calmo (a garantia é explicada sem alarmismo, mas sem esconder o risco). Os números dos textos são calculados
aqui, a partir de calculo.py, para não divergirem do simulador. Sem f-string aninhada (o CI roda Python 3.10).

O parceiro NÃO publica prazo máximo, crédito mínimo nem teto de crédito do Auto Equity: a tela não impõe limite onde o parceiro não divulga (só o LTV de 80% é dele).
"""
import calculo
import taxas_referencia as tr

# Cenário padrão da home (o JS desenha o mesmo ao abrir a página).
VEICULO_PADRAO = 100_000
RECEBER_PADRAO = 50_000
MESES_PADRAO = 48
CONFORTO_PADRAO = 1_500

# ---------- formatação ----------


def _milhar(texto):
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


def brl0(v):
    return "R$ " + _milhar(format(round(v), ",d"))


def pct(v):
    return _milhar(format(round(v, 2), ",.2f")) + "%"


def mes_curto(ano_mes):
    ano, mes = ano_mes.split("-")
    return ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][int(mes) - 1] + "/" + ano


# ---------- blocos de HTML ----------


def h2(t):
    return "<h2>" + t + "</h2>\n"


def h3(t):
    return "<h3>" + t + "</h3>\n"


def p(t):
    return "<p>" + t + "</p>\n"


def ul(itens):
    return "<ul>" + "".join("<li>" + i + "</li>" for i in itens) + "</ul>\n"


def ol(itens):
    return "<ol>" + "".join("<li>" + i + "</li>" for i in itens) + "</ol>\n"


def aviso(t, ok=False):
    return '<div class="aviso' + (" ok" if ok else "") + '">' + t + "</div>\n"


def a(href, texto):
    return '<a href="' + href + '">' + texto + "</a>"


def tabela(cabecalho, linhas, legenda):
    topo = "".join('<th scope="col">' + c + "</th>" for c in cabecalho)
    # data-l: rótulo da coluna, usado no celular (o CSS empilha cada linha em um cartão; sem rolagem lateral)
    corpo = "".join("<tr>" + "".join('<td data-l="' + cabecalho[i] + '">' + c + "</td>" for i, c in enumerate(l)) + "</tr>" for l in linhas)
    return '<div class="tw"><table><caption>' + legenda + "</caption><thead><tr>" + topo + "</tr></thead><tbody>" + corpo + "</tbody></table></div>\n"


# ---------- números compartilhados ----------


def _ref():
    linhas = tr.ler()
    # defesa em profundidade: o ETL já filtra, mas se o CSV vier adulterado ou corrompido o site não pode ir ao ar com número absurdo
    for sd in tr.SERIES:
        ult = tr.ultima(sd["codigo"], linhas)
        lo, hi = sd["faixa"]
        if not (lo <= ult["valor"] <= hi):
            raise ValueError("taxa fora da faixa plausível na série %s: %s" % (sd["codigo"], ult["valor"]))
    gar = tr.ultima(tr.CODIGO_GARANTIA_REAL, linhas)
    return {"garantiaRealAm": tr.ao_mes(gar), "garantiaRealMes": mes_curto(gar["mes"])}


def taxa_ref():
    return calculo.taxa_mensal()


def cenario_padrao():
    return calculo.simular(VEICULO_PADRAO, RECEBER_PADRAO, 0, MESES_PADRAO, taxa_ref())


def nota_taxa_maior(ref, i, veiculo, receber, saldo, meses):
    """Mesmo texto que o simulador.js escreve na nota "E se a taxa for maior?" para o cenário informado."""
    r = calculo.simular(veiculo, receber, saldo, meses, ref["garantiaRealAm"] / 100)
    return ("A estimativa usa a taxa de referência do parceiro (" + pct(calculo.TAXA_PARCEIRO_AM) + " a.m., média divulgada, parcela fixa e sem IPCA). "
            "A média do Banco Central para crédito com garantia real, que mistura imóvel e veículo, é " + pct(ref["garantiaRealAm"]) + " a.m. (" + ref["garantiaRealMes"] +
            "): nessa taxa, a parcela do cenário acima seria de " + brl0(r["parcela"]) + ". A taxa final vem da análise.")


CITACAO = "Datalab Global (https://autoequity.datalabglobal.com/dados-abertos)"

# Cores das outras modalidades (o âmbar é só do Auto Equity; o coral é dos juros); o simulador.js usa as mesmas.
COR_MODALIDADE = {tr.CODIGO_GARANTIA_REAL: "#7ea6d9", 20742: "#b69be0", 20741: "#7dc4b0", 22022: "#d98fb8"}


# ---------- amortização e "quitar dívida" (home): mesmos textos que o simulador.js escreve ----------
DIVIDAS = [("pessoal", "Crédito pessoal sem garantia"), ("cheque", "Cheque especial"), ("rotativo", "Cartão de crédito rotativo")]
DIVIDA_PADRAO = 20_000
DIVIDA_TIPO_PADRAO = "pessoal"


def rotulo_periodo(n, meses):
    """Rótulo da linha da tabela de amortização (blocos de 6 meses): "1 a 6", "7 a 12"... O JS monta o mesmo."""
    ini = (n - 1) * calculo.PERIODO_MESES + 1
    fim = min(n * calculo.PERIODO_MESES, meses)
    return str(ini) if ini == fim else str(ini) + " a " + str(fim)


def amort_resumo(r, linhas, meses):
    """Frase acima da tabela de amortização: quanto dos primeiros meses é juros."""
    pago = linhas[0]["juros"] + linhas[0]["amortizacao"]
    j = linhas[0]["juros"]
    p1 = min(calculo.PERIODO_MESES, meses)
    cauda = "A parcela é fixa: com o tempo ela amortiza mais a dívida e os juros caem."
    return ("Nos primeiros " + str(p1) + " meses, " + brl0(j) + " dos " + brl0(pago) + " que você paga são juros (" + str(round(j / pago * 100)) + "%). " + cauda)


def amort_nota(i):
    return ("A conta usa a taxa de " + pct(i * 100) + " ao mês, com parcela fixa e sem IPCA. Não inclui IOF, avaliação do veículo, registro do gravame nem seguros.")


AMORT_LEGENDA = {"price": "Parcela fixa: juros, amortização e saldo devedor no fim de cada bloco de 6 meses"}


# ---------- renda (home): mesmo texto que o simulador.js escreve ----------
def renda_texto(parcela):
    nome = "a parcela estimada"
    return ("A lei não fixa um percentual para o crédito com veículo em garantia: cada instituição decide na análise. Muita gente usa como régua uma parcela de até cerca de 30% da renda mensal. "
            "Nessa régua, " + nome + " de " + brl0(parcela) + " exigiria uma renda mensal comprovada de cerca de " + brl0(calculo.renda_para_parcela(parcela)) + " (conta nossa, não é análise de crédito).")


def regra_renda():
    """Explicação (home e página como-funciona) de como a renda entra na análise do Auto Equity."""
    return (
        p("Nenhuma lei define um percentual de renda para o crédito com veículo em garantia. A política de crédito de cada instituição decide, caso a caso, e o parceiro não informa o dele.")
        + p("A régua mais comum no mercado é a parcela de até cerca de <b>30% da renda mensal</b> (algumas instituições aceitam um pouco mais). É costume de bancos, citado no "
            "crédito em geral; não achamos norma própria do Auto Equity que a exija. Neste simulador ela só serve de referência para estimar a renda que a parcela pede.")
        + p("O que costuma entrar na análise:")
        + ul([
            "renda comprovada (o parceiro costuma pedir comprovação, inclusive de autônomos);",
            "outras dívidas e parcelas já em andamento;",
            "histórico de crédito e restrições no seu nome;",
            "valor de avaliação, idade, modelo, quilometragem e conservação do veículo: a avaliação define o limite, de até 80% do valor;",
            "valor e prazo do crédito.",
        ])
        + p("Como todos esses itens pesam, a parcela que cabe no seu caso pode ficar abaixo ou acima de 30% da renda. Prefira uma parcela que deixe sobra no orçamento.")
    )


# ---------- "o mesmo crédito em outras modalidades" (home) ----------
def cm_lead(credito, meses):
    return ("Com o mesmo crédito de " + brl0(credito) + " e o mesmo prazo de " + str(meses) + " meses, veja quanto você pagaria em cada modalidade. "
            "As outras taxas são médias de mercado do Banco Central.")


def cm_gap_valor(ref, credito, meses, ae_total):
    """Quanto a mais o mesmo crédito custaria, no total, no crédito pessoal sem garantia (média de mercado)."""
    return calculo.pmt(credito, ref["pessoalAm"] / 100, meses) * meses - ae_total


def cm_gap(ref, credito, meses):
    pa = calculo.pmt(credito, ref["pessoalAm"] / 100, meses)
    return ("a mais no crédito pessoal sem garantia (média de " + pct(ref["pessoalAm"]) + " a.m.): " + brl0(pa) + " por mês, " + brl0(pa * meses) + " no total.")


def cm_nota(ref):
    return ("Conta de comparação: mesmo crédito e mesma duração, com parcela fixa nas outras modalidades. Cheque especial e rotativo raramente duram esse tempo todo; a conta serve para mostrar o peso do juro. A média de garantia real do Banco Central soma imóvel e veículo. Médias de mercado de " + ref["garantiaRealMes"] + " (Banco Central), só para comparar; não são oferta.")


def amort_linhas(linhas, meses):
    """Linhas <tr> da tabela (o JS monta as mesmas)."""
    return "".join('<tr><th scope="row">' + rotulo_periodo(x["periodo"], meses) + "</th><td>" + brl0(x["juros"]) + "</td><td>" + brl0(x["amortizacao"]) + "</td><td>" + brl0(x["saldo"]) + "</td></tr>"
                   for x in linhas)


def amort_total(linhas, credito):
    juros = sum(x["juros"] for x in linhas)
    return '<tr><th scope="row">Total</th><td>' + brl0(juros) + "</td><td>" + brl0(credito) + "</td><td></td></tr>"


def quitar_cartoes(c, taxa_div_pct, meses, ae_pct, custom=False):
    """Dois cartões: a dívida na taxa dela e no Auto Equity (mesmo prazo). c vem de calculo.comparar_quitacao."""
    nome_a = ("Na taxa da sua dívida (" if custom else "Na taxa média (") + pct(taxa_div_pct) + " a.m.)"
    a_ = ('<div class="alt"><h3>' + nome_a + '</h3><div class="p num">' + brl0(c["parcela_atual"]) + '</div><div class="d">Só de juros: ' + brl0(c["juros_mes1"]) +
          " no 1º mês<br>Total em " + str(meses) + " meses: " + brl0(c["total_atual"]) + "</div></div>")
    if c["economia_mes"] > 0:
        dest = '<span class="dn">' + brl0(c["economia_mes"]) + " a menos por mês</span>"
    else:
        dest = '<span class="up">sem redução de parcela nesta conta</span>'
    b = ('<div class="alt cur"><h3>No Auto Equity (' + pct(ae_pct) + ' a.m.)</h3><div class="p num">' + brl0(c["parcela_ae"]) + '</div><div class="d">Total em ' + str(meses) +
         " meses: " + brl0(c["total_ae"]) + "<br>" + dest + "</div></div>")
    return a_ + b


def quitar_texto(c, meses):
    if c["economia_mes"] > 0:
        return ("Trocar esta dívida reduziria a parcela em " + brl0(c["economia_mes"]) + " por mês e o total pago em cerca de " + brl0(c["economia_total"]) +
                ", com a mesma duração (" + str(meses) + " meses). Avaliação, gravame e seguros ficam fora desta conta e encolhem a economia.")
    return "Com esta taxa, o Auto Equity não reduz a parcela da dívida. Peça o CET da proposta e compare antes de decidir."


# ---------- perguntas frequentes (home) ----------
FAQ = [
    ("Posso continuar usando o veículo?",
     "Sim. No Auto Equity o veículo fica como garantia, mas você continua usando: dirigindo, trabalhando com ele, conforme o contrato. "
     "O que muda é o registro da garantia (o gravame) no cadastro do veículo, que sai quando a dívida é quitada. Veja " + a("/garantia-do-veiculo", "como funciona a garantia") + "."),
    ("Posso usar um veículo que ainda está financiado?",
     "Em geral é possível, conforme a instituição: o novo crédito liquida o financiamento do carro e o que sobra fica com você. Por isso o simulador tem a opção "
     "\"Ainda financiado\": o saldo entra no total do crédito e conta para o limite de 80% do valor do veículo. Veículo de consórcio não entra."),
    ("Por que a parcela é fixa e sem IPCA?",
     "Porque o simulador parte da taxa média que o parceiro divulga para veículo em garantia, " + pct(calculo.TAXA_PARCEIRO_AM) + " ao mês, que não vem somada ao IPCA. A parcela é igual do primeiro ao último mês "
     "(tabela Price). A proposta real traz a taxa, o sistema e o CET: confira lá, porque a taxa que você recebe pode ser menor ou maior que a média."),
    ("Qual é o prazo e o valor mínimo e máximo?",
     "O parceiro divulga que libera até " + str(round(calculo.LTV_MAX * 100)) + "% do valor do veículo. Ele não divulga prazo, valor mínimo nem teto de crédito, e a tela não impõe nenhum: aceita qualquer valor positivo e prazo de " +
     str(calculo.PRAZO_MIN_MESES) + " a " + str(calculo.PRAZO_MAX_MESES) + " meses, só barrando o que quebraria a conta. A proposta mostra o que vale para o seu caso."),
    ("Que veículos entram?",
     "Quem decide é a instituição, na avaliação: idade, modelo, quilometragem e conservação mudam o valor e o limite. Veículo de consórcio não entra, e caminhões, vans e ônibus só são aceitos por algumas instituições."),
    ("Posso vender o veículo enquanto ele está em garantia?",
     "Não sem acertar antes com o credor: o gravame impede a transferência normal. Para vender, em geral é preciso quitar a dívida ou combinar a troca da garantia com a instituição. Veja " + a("/garantia-do-veiculo", "a garantia do veículo") + "."),
    ("E se eu atrasar as parcelas do veículo?",
     "Cada dia de atraso gera os encargos do contrato e, se a dívida não for regularizada, a lei prevê um procedimento que pode chegar à retomada e à venda do veículo dado em garantia. "
     "Por isso a parcela deve sobrar no orçamento, e não apenas caber. Detalhes em " + a("/garantia-do-veiculo", "Garantia do veículo") + "."),
    ("Auto Equity é o mesmo que refinanciamento ou portabilidade?",
     "Não. No refinanciamento do veículo, o novo crédito quita o saldo do financiamento e libera a diferença; é o que a opção \"Ainda financiado\" do simulador calcula. Portabilidade é transferir uma dívida que "
     "já existe para outro credor, normalmente em busca de taxa menor. Já o Auto Equity, também chamado de empréstimo com garantia de veículo, é um crédito novo com o veículo em garantia. Veja " + a("/auto-equity-ou-outro-credito", "a comparação") + "."),
    ("Que fatia da renda a parcela do veículo pode tomar?",
     "A lei não fixa um percentual para o crédito com veículo em garantia: cada instituição decide na análise de crédito, e o parceiro não divulga o dele. Muita gente usa como régua uma parcela de até "
     "cerca de 30% da renda mensal. Entram na conta a renda comprovada, outras dívidas, o histórico de crédito e a avaliação do veículo. Veja " + a("/como-funciona", "como funciona") + "."),
    ("A parcela é fixa ou diminui com o tempo?",
     "No Auto Equity a parcela é fixa (tabela Price): é igual do início ao fim do contrato, e o simulador mostra só esse formato. "
     "A taxa e o CET finais, só a proposta do parceiro diz."),
    ("A simulação vale como proposta?",
     "Não. É uma estimativa feita com taxa de referência, sem consultar você nem o veículo. A taxa, o limite e o prazo finais saem da análise de crédito e da avaliação do veículo."),
]


# ---------- páginas ----------


def corpo_como_funciona(ctx):
    r = cenario_padrao()
    return (
        p("Auto Equity, também chamado de empréstimo com garantia de veículo (ou crédito com garantia de veículo), é um crédito em que você oferece um veículo como garantia e recebe dinheiro para pagar em parcelas. "
          "Com o veículo como garantia, a instituição assume menos risco e cobra juros bem abaixo dos do crédito pessoal ou do cartão. O carro segue com você.")
        + h2("O que entra na conta e quanto o veículo libera")
        + p("O parceiro de crédito divulga que o Auto Equity libera <b>até 80% do valor do veículo</b>, com taxa média de <b>" + pct(calculo.TAXA_PARCEIRO_AM) + " ao mês</b>. "
            "O veículo pode estar quitado ou financiado: se estiver financiado, o novo crédito quita o saldo e libera a diferença para você. Veículo de consórcio não entra.")
        + p("Exemplo do simulador: veículo de " + brl0(VEICULO_PADRAO) + ", você quer receber " + brl0(RECEBER_PADRAO) + " em " + str(MESES_PADRAO) + " meses. O crédito usa " + str(round(r["ltv"] * 100)) +
            "% do valor do veículo, a parcela estimada é de " + brl0(r["parcela"]) + " por mês e o total ao final é de " + brl0(r["total"]) + ".")
        + aviso("O parceiro divulga o limite de <b>até " + str(round(calculo.LTV_MAX * 100)) + "% do valor do veículo</b>. Ele <b>não divulga prazo, valor mínimo nem teto</b> de crédito, e a tela não impõe nenhum. A proposta mostra o que vale.")
        + h2("Passo a passo")
        + ol([
            "<b>Simulação.</b> Aqui você vê a estimativa sem informar dado pessoal.",
            "<b>Pedido e análise de crédito.</b> Você preenche o formulário de um parceiro de crédito, que examina renda, histórico e dívidas e devolve uma proposta.",
            "<b>Documentos.</b> Seus documentos, a comprovação de renda e os do veículo.",
            "<b>Avaliação do veículo.</b> A instituição avalia o veículo (idade, modelo, quilometragem e conservação mudam o valor, que pode ser diferente do que você imagina).",
            "<b>Contrato e registro da garantia.</b> Você assina o contrato e a garantia (gravame) é registrada no cadastro do veículo.",
            "<b>Liberação.</b> O valor cai na sua conta e as parcelas começam a correr.",
        ])
        + h2("Quanto da renda a parcela pode ocupar")
        + regra_renda()
        + h2("Parcela fixa (Price)")
        + p("No Auto Equity a parcela é fixa, pela tabela <b>Price</b>: não muda ao longo do contrato. Nos primeiros meses, a maior parte da parcela é juros; com o tempo, "
            "o abatimento da dívida cresce. Não existe a opção de parcela que diminui (SAC) neste crédito, por isso o simulador não a oferece.")
        + h2("Para que as pessoas usam")
        + ul([
            "Trocar dívidas caras (cartão, cheque especial, empréstimos sem garantia) por uma parcela de juro menor, em prazo mais curto.",
            "Capital de giro para o próprio negócio, inclusive de quem trabalha com o veículo.",
            "Uma despesa grande e planejada, como uma reforma ou um curso.",
        ])
        + aviso("Alongar o prazo reduz a parcela, mas eleva o total pago; o <b>Raio-X da decisão</b> põe as duas faces lado a lado.", ok=True)
        + p("Veja também " + a("/garantia-do-veiculo", "como funciona a garantia") + ", " + a("/custos-alem-dos-juros", "os custos além dos juros") + " e " + a("/metodologia", "como calculamos") + ".")
    )


def corpo_garantia(ctx):
    return (
        p("A garantia é o que torna o Auto Equity mais barato: a instituição corre menos risco e cobra juros menores. Saber como ela funciona antes de pedir ajuda a dimensionar "
          "a parcela com folga. O texto é informativo: não substitui o contrato nem a orientação de um advogado.")
        + h2("O que muda para você")
        + ul([
            "Você continua com a posse e o uso do veículo: pode dirigir, trabalhar com ele, conforme o contrato.",
            "A propriedade fica em garantia com a instituição (veja abaixo), e a garantia fica registrada no cadastro do veículo, o chamado gravame.",
        ])
        + h2("O que fica registrado")
        + p("A modalidade mais comum é a <b>alienação fiduciária</b> de bem móvel: a propriedade fica em garantia com a instituição enquanto a dívida existe, e o gravame é registrado no cadastro do veículo (Detran). "
            "Quando você quita a dívida, a instituição libera a baixa do gravame. A forma exata (inclusive quanto a veículo ainda financiado) é definida no contrato de cada instituição.")
        + h2("Vender, transferir ou trocar o veículo")
        + p("Com o gravame, <b>você não pode vender o veículo sem acertar antes com o credor</b>: a transferência normal fica bloqueada. Em geral é preciso quitar a dívida (inclusive de forma antecipada, com a redução de juros prevista em lei) "
            "ou combinar a troca da garantia com a instituição. Vale conferir isso antes de contratar, se você pensa em trocar de veículo nos próximos anos.")
        + h2("Se as parcelas deixarem de ser pagas")
        + p("Cada atraso gera os encargos do contrato. Se a dívida continuar sem pagamento, a lei prevê um procedimento: o credor pode pedir a busca e apreensão do veículo e vendê-lo para cobrir a dívida. "
            "Se o valor arrecadado superar a dívida e os custos, a diferença é devolvida a você; se ficar abaixo, pode sobrar saldo a pagar. "
            "A retomada é o último recurso; procurar a instituição antes do atraso muitas vezes abre saída, como renegociar o prazo.")
        + h2("O que mexe no valor da garantia")
        + ul([
            "<b>Idade e modelo:</b> veículos mais antigos ou de menor procura costumam valer menos para a instituição.",
            "<b>Quilometragem e conservação:</b> a avaliação considera o estado do veículo, e o valor dela pode ser diferente do que você esperava.",
            "<b>Tipo de veículo:</b> caminhões, vans e ônibus só são aceitos por algumas instituições, e veículo de consórcio não entra.",
        ])
        + h2("Como ficar mais tranquilo")
        + ul([
            "Dimensione a parcela com sobra no orçamento; o campo de parcela do Raio-X serve de régua.",
            "Com renda variável, vale manter uma reserva equivalente a alguns meses de parcela.",
            "Mantenha em dia o que o contrato exige do veículo (por exemplo, licenciamento e seguro, quando previstos).",
            "Leia o contrato até o fim, com atenção a atraso, quitação antecipada e seguros.",
        ])
        + aviso("Vender ou alugar o veículo dado em garantia, ou fazer outra operação sobre ele, normalmente exige falar com a instituição antes. Confira o que o contrato prevê.")
        + p("Veja também " + a("/custos-alem-dos-juros", "os custos além dos juros") + " e " + a("/quando-nao-vale-a-pena", "quando o Auto Equity não vale a pena") + ".")
    )


def corpo_custos(ctx):
    i = taxa_ref()
    linhas = []
    for m in (12, 24, 36, 48, 60):
        rr = calculo.simular(VEICULO_PADRAO, RECEBER_PADRAO, 0, m, i)
        linhas.append([str(m) + " meses", brl0(rr["parcela"]), brl0(rr["total"]), brl0(rr["juros"])])
    p48 = cenario_padrao()
    return (
        p("A tela mostra parcela e total só com juros. A proposta de verdade pode embutir outras despesas, e por isso traz o <b>CET (Custo Efetivo Total)</b>, "
          "que soma juros e custos da operação. Peça o CET e compare propostas por ele, e não apenas pela taxa.")
        + h2("O que pode entrar além dos juros")
        + ul([
            "<b>IOF</b>, o imposto sobre operações de crédito.",
            "<b>Avaliação ou vistoria do veículo</b>, feita pela instituição.",
            "<b>Registro do gravame</b> (da garantia) no cadastro do veículo.",
            "<b>Seguros</b>, como o de vida e o do veículo, quando exigidos pela instituição.",
            "<b>Tarifas</b> cobradas no cadastro ou na análise, se houver.",
        ])
        + p("Nem toda instituição cobra todos esses itens, e os valores diferem. O simulador <b>deixa tudo isso de fora</b>, então a parcela exibida é uma estimativa.")
        + h2("Parcela fixa, sem IPCA")
        + p("A taxa de referência é a média divulgada pelo parceiro, " + pct(i * 100) + " ao mês, sem atualização por IPCA: a parcela é a mesma todos os meses. "
            "Para " + brl0(RECEBER_PADRAO) + " em " + str(MESES_PADRAO) + " meses, com o veículo de " + brl0(VEICULO_PADRAO) + ", a parcela estimada é de " + brl0(p48["parcela"]) + ".")
        + h2("Exemplo de como o prazo pesa")
        + tabela(["Prazo", "Parcela estimada", "Total ao final", "Juros no total"], linhas,
                 "Receber " + brl0(RECEBER_PADRAO) + " com veículo de " + brl0(VEICULO_PADRAO) + ", taxa de referência " + pct(i * 100) + " ao mês, sem IOF e sem tarifas.")
        + p("Quanto mais longo o prazo, menor a parcela e maior o total pago. A escolha depende do seu orçamento e das suas prioridades.")
        + h2("Depois de contratar")
        + p("Quitar antes reduz os juros: o bloco <b>Antecipar parcelas pode economizar milhares de reais</b> mostra quanto. Peça no contrato como funciona a liquidação antecipada e se há tarifa.")
    )


def corpo_comparar(ctx):
    linhas = tr.ler()
    i_ref = taxa_ref()
    itens = [("Auto Equity (média do parceiro)", i_ref * 100)]
    for c in tr.CODIGOS_COMPARACAO:
        u = tr.ultima(c, linhas)
        itens.append((tr.serie_def(c)["nome"] + " (média do mercado)", tr.ao_mes(u)))
    base = 30_000
    meses = 36
    tab = []
    for nome, taxa in itens:
        pm = calculo.pmt(base, taxa / 100, meses)
        tab.append([nome, pct(taxa), brl0(pm), brl0(pm * meses - base)])
    return (
        p("O Auto Equity, também chamado de empréstimo com garantia de veículo, costuma ter juros mensais bem menores que os do crédito sem garantia. O quadro abaixo aplica a mesma conta a todas as modalidades: pegar " + brl0(base) + " em " + str(meses) +
          " meses, parcela fixa, cada modalidade com a sua taxa.")
        + tabela(["Modalidade", "Juros ao mês", "Parcela", "Juros no total"], tab,
                 "Valor e prazo iguais; só a taxa muda. Médias do Banco Central (" + mes_curto(tr.ultima(29976, linhas)["mes"]) + "); a taxa do Auto Equity é a média divulgada pelo parceiro.")
        + aviso("Comparamos taxas, não ofertas. Na prática o crédito sem garantia costuma ter prazo e valor máximos menores, e o Auto Equity pode ter custos de avaliação e registro. "
                "A média do Banco Central para garantia real mistura imóvel e veículo. Antes de decidir, compare o CET de cada proposta.")
        + h2("Refinanciar o carro ou portar a dívida: diferenças")
        + p("No <b>refinanciamento do veículo</b>, com o veículo ainda financiado, o novo crédito quita o saldo e libera a diferença para você; é o que a opção \"Ainda financiado\" do simulador calcula. "
            "A <b>portabilidade de crédito</b> é diferente: transfere uma dívida que já existe para outro credor, geralmente atrás de taxa menor. "
            "Usar o Auto Equity para quitar uma dívida é contratar um crédito novo, com o veículo em garantia.")
        + h2("O que a garantia muda")
        + ul([
            "<b>Rotativo do cartão e cheque especial</b> estão entre os mais caros e foram pensados para dias, não meses; carregar dívida neles encarece muito.",
            "<b>Crédito pessoal sem garantia</b> não exige um bem em garantia, mas cobra juros mais altos.",
            "<b>Crédito com garantia real</b> (veículo ou imóvel) tem juros menores, em troca de colocar um bem em garantia. O crédito com imóvel em garantia (Home Equity) costuma ter prazos bem mais longos e exige avaliação e registro em cartório.",
        ])
        + p("Se o objetivo é trocar uma dívida cara, o simulador de Auto Equity mostra quanto ficaria a parcela; o " + a("/quando-nao-vale-a-pena", "texto sobre quando não vale a pena")
            + " ajuda a pesar o outro lado.")
    )


def corpo_quando_nao(ctx):
    return (
        p("O Auto Equity pode ser uma opção boa, e há situações em que vale pensar duas vezes. Estes são os pontos que a gente conferiria antes de pedir.")
        + h2("Quando vale pensar duas vezes")
        + ul([
            "<b>A parcela só cabe com aperto.</b> Se a parcela estimada aperta o orçamento, peça menos, estique o prazo ou aguarde. Use o Raio-X do simulador.",
            "<b>Você depende do veículo e a renda é incerta.</b> Com a garantia em jogo, uma queda de renda pesa mais, sobretudo se o veículo é a sua ferramenta de trabalho; uma reserva de alguns meses de parcela ajuda.",
            "<b>O dinheiro vai para algo que não se paga sozinho.</b> Usar uma dívida de vários meses para uma despesa de consumo de curto prazo costuma sair caro no total.",
            "<b>O valor é pequeno.</b> Avaliação, registro do gravame e seguros pesam mais em valores baixos; compare o CET com o de outras opções.",
            "<b>Existe crédito mais barato disponível.</b> Consignado, portabilidade da dívida atual para uma instituição com taxa menor, refinanciamento do financiamento do veículo ou pagar a dívida com recursos próprios podem custar menos.",
            "<b>Você pensa em vender ou trocar o veículo logo.</b> Com o gravame, a venda exige acertar com o credor antes.",
            "<b>O veículo é antigo ou de baixa procura.</b> A avaliação pode vir bem abaixo do que você espera e o limite cai junto.",
        ])
        + h2("Quando pode fazer sentido")
        + ul([
            "Substituir dívidas de juro altíssimo por uma parcela fixa menor, num prazo que dê para acompanhar.",
            "Bancar um projeto ou negócio cujo retorno esperado supera o custo do crédito.",
            "Consolidar várias dívidas numa só, com o orçamento reorganizado em seguida.",
        ])
        + aviso("Isto não é recomendação financeira personalizada. O simulador entrega números; a decisão é sua, e na dúvida compensa ouvir alguém de confiança ou um profissional.", ok=True)
        + p("Antes de decidir, veja " + a("/custos-alem-dos-juros", "os custos além dos juros") + " e " + a("/garantia-do-veiculo", "como funciona a garantia") + ".")
    )


def corpo_taxas(ctx):
    linhas = tr.ler()
    ref = []
    for s in tr.SERIES:
        u = tr.ultima(s["codigo"], linhas)
        if not u:
            continue
        valor = pct(u["valor"]) + (" ao mês" if s["unidade"] == "am" else " ao ano")
        mensal = pct(tr.ao_mes(u)) + " ao mês"
        ref.append([s["nome"], mes_curto(u["mes"]), valor, mensal, '<a href="' + tr.url_fonte(s["codigo"]) + '" rel="noopener">SGS ' + str(s["codigo"]) + "</a>"])
    gar = tr.ultima(tr.CODIGO_GARANTIA_REAL, linhas)
    return (
        p("Há dois tipos de taxa por trás dos números: a <b>taxa divulgada pelo parceiro</b>, que estima a parcela, e as <b>médias do Banco Central</b>, que servem de comparação e do aviso \"e se a taxa for maior?\".")
        + h2("Taxa de referência do Auto Equity")
        + p("O parceiro de crédito mostra, no gráfico de taxas de veículo em garantia, uma <b>média de " + pct(calculo.TAXA_PARCEIRO_AM) + " ao mês</b>. É a taxa que usamos, sem somar IPCA: a parcela é fixa. "
            "É uma média divulgada, não uma garantia: a sua taxa pode ser menor ou maior, conforme a análise de crédito, o valor, o prazo e o veículo. Conferido em 18/11/2026.")
        + h2("Médias do Banco Central")
        + tabela(["Série", "Mês", "Valor da série", "Em % ao mês", "Fonte"], ref,
                 "Taxas médias das novas operações de crédito livre de pessoas físicas. Dados do Banco Central do Brasil (SGS), sob licença ODbL.")
        + p("A média do Banco Central para crédito com garantia real está em " + pct(tr.ao_mes(gar)) + " ao mês (" + mes_curto(gar["mes"]) + "). Esses números são renovados toda semana a partir da API do Banco Central. "
            "Os dados em CSV estão em " + a("/dados/taxas-referencia.csv", "/dados/taxas-referencia.csv") + ".")
        + h2("Limites desses números")
        + ul([
            "A série de <b>crédito com garantia real</b> mistura imóvel e veículo: o Banco Central não separa o crédito com veículo em garantia. Por isso ela é uma referência, não a taxa do Auto Equity.",
            "Média é média: a sua taxa pode ser menor ou maior, conforme a análise de crédito, o valor, o prazo e o veículo.",
            "As taxas do Banco Central refletem contratos do mês indicado e são divulgadas com atraso.",
            "Nenhuma delas é oferta de crédito.",
        ])
    )


def corpo_metodologia(ctx):
    i = taxa_ref()
    r = cenario_padrao()
    return (
        p("Em poucas linhas: o simulador calcula a parcela fixa de um empréstimo, com a taxa de referência do parceiro, sobre o crédito que você pediria. Aqui está cada parte da conta.")
        + h2("A conta")
        + ol([
            "<b>Crédito total</b> = valor que você quer receber + saldo devedor do financiamento, se o veículo ainda estiver financiado (o novo crédito quita esse saldo).",
            "<b>Taxa mensal</b> = " + pct(calculo.TAXA_PARCEIRO_AM) + " ao mês, a média que o parceiro divulga. Não há atualização por IPCA.",
            "<b>Parcela</b> (Price): crédito × i / (1 − (1 + i)^−n), em que i é a taxa ao mês e n o número de meses; resulta em parcela fixa.",
            "<b>Total ao final</b> = parcela × n. <b>Juros no total</b> = total − crédito.",
            "<b>Limite</b> = 80% do valor do veículo, conforme divulgado pelo parceiro. O saldo devedor conta para esse limite.",
        ])
        + p("Exemplo: veículo de " + brl0(VEICULO_PADRAO) + ", receber " + brl0(RECEBER_PADRAO) + ", " + str(MESES_PADRAO) + " meses, taxa " + pct(i * 100) + " ao mês. Resultado: parcela de " + brl0(r["parcela"]) +
            " e total de " + brl0(r["total"]) + ".")
        + h2("O que o parceiro divulga e o que a tela não impõe")
        + p("O parceiro divulga que libera até " + str(round(calculo.LTV_MAX * 100)) + "% do valor do veículo, e a tela respeita esse limite. Ele não divulga prazo, valor mínimo nem teto de crédito, e a tela não impõe nenhum: "
            "aceita qualquer valor positivo e prazo de " + str(calculo.PRAZO_MIN_MESES) + " a " + str(calculo.PRAZO_MAX_MESES) + " meses, só barrando zero e números absurdos. "
            "O controle deslizante do prazo vai de " + str(calculo.SLIDER_PRAZO_MIN) + " a " + str(calculo.SLIDER_PRAZO_MAX) + " meses só para facilitar. O que vale é o que o parceiro informar na proposta.")
        + h2("O que a conta não inclui")
        + ul([
            "IOF, tarifas, avaliação do veículo, registro do gravame e seguros (veja " + a("/custos-alem-dos-juros", "custos além dos juros") + ").",
            "Análise de crédito, valor de avaliação do veículo e limite de cada instituição, que definem a oferta real.",
        ])
        + h2("Amortização e pagar antes")
        + p("A tabela de amortização agrupa a conta em blocos de 6 meses (o prazo é curto): juros pagos, amortização e saldo devedor no fim de cada bloco. "
            "A simulação de pagar a mais mostra quanto de juros some se você somar um valor à parcela todo mês ou pagar um valor único em algum momento, reduzindo o prazo ou a parcela. "
            "Os valores são em reais de hoje, sem tarifas da instituição e sem o que o dinheiro renderia em outra aplicação.")
        + h2("O Raio-X da decisão")
        + p("O valor de parcela que você digita no Raio-X é só uma referência sua. O simulador compara: indica quanto a parcela estimada fica acima ou abaixo dela e propõe duas saídas (receber menos ou mudar o prazo) na mesma taxa. "
            "Ele <b>não avalia capacidade de pagamento</b> nem decide por você. Ele ainda calcula a renda necessária se a parcela ocupar 30% dela, régua de mercado e não regra do parceiro (veja " + a("/como-funciona", "como funciona") + ").")
        + h2("Conferência")
        + p("Cada alteração do site passa por testes automáticos que confrontam o cálculo do navegador com o de referência em Python, em dezenas de cenários.")
    )


def _ultimos():
    saida = []
    for s in tr.SERIES:
        u = tr.ultima(s["codigo"])
        if u:
            saida.append([s["nome"], mes_curto(u["mes"]), pct(u["valor"]) + (" ao mês" if u["unidade"] == "am" else " ao ano")])
    return saida


def _leitura_garantia(frase_final):
    """Compara garantia real e crédito pessoal no último mês, com as contas feitas sobre o próprio CSV."""
    g, pe = tr.ultima(29976), tr.ultima(20742)
    if not g or not pe:
        return ""
    g_ano = ((1 + g["valor"] / 100) ** 12 - 1) * 100
    return ("No último mês do arquivo (" + tr.mes_extenso(g["mes"]) + "), o crédito com garantia real custou " + pct(g["valor"]) + " ao mês, o que dá cerca de " + pct(g_ano) +
            " ao ano; o crédito pessoal sem garantia custou " + pct(pe["valor"]) + " ao ano. " + frase_final)


def corpo_dados_abertos(ctx):
    linhas = tr.ler()
    meses = sorted({l["mes"] for l in linhas})
    colunas = [
        ("codigo_serie", "Código da série no SGS (Banco Central)"),
        ("modalidade", "Nome da série (por exemplo, Crédito pessoal não consignado)"),
        ("mes_referencia", "Mês de referência (AAAA-MM)"),
        ("valor", "Valor da série, em %"),
        ("unidade", "\"am\" = % ao mês; \"aa\" = % ao ano"),
    ]
    series = [[str(s["codigo"]), s["nome"], "% ao mês" if s["unidade"] == "am" else "% ao ano", '<a href="' + tr.url_fonte(s["codigo"]) + '" rel="noopener">SGS ' + str(s["codigo"]) + "</a>"]
              for s in tr.SERIES]
    return (
        p("O CSV abaixo reúne as taxas de referência do simulador de Auto Equity, para quem quiser conferir, citar ou reaproveitar em outra análise. "
          "São médias de mercado do Banco Central, não ofertas de crédito.")
        + h2("O arquivo")
        + tabela(["Arquivo", "Formato", "Período"],
                 [[a("/dados/taxas-referencia.csv", "taxas-referencia.csv"), "CSV, UTF-8, separador ponto e vírgula", mes_curto(meses[0]) + " a " + mes_curto(meses[-1]) + ", " + str(len(linhas)) + " linhas"]],
                 "Atualizado toda semana. Página atualizada em " + ctx["atualizado"] + ".")
        + h2("Cópias para citar")
        + tabela(["Onde", "Para quê"],
                 [[a("https://doi.org/10.5281/zenodo.24475517", "Zenodo (DOI)"), "Cópia com DOI, para citar (mesma licença)"],
                  [a("https://huggingface.co/datasets/datalabglobal/auto-equity-taxas-referencia-bcb", "Hugging Face"), "Cópia para carregar em código (mesma licença)"],
                  [a("https://www.kaggle.com/datasets/rodolfodelfino/taxas-de-referncia-para-auto-equity-bcb", "Kaggle"), "Cópia para notebooks (mesma licença)"]],
                 "Essas cópias foram publicadas em 23/11/2026 e não se atualizam sozinhas: o arquivo desta página é o mais recente.")
        + h2("Colunas")
        + ul(["<code>" + n + "</code>: " + d for n, d in colunas])
        + h2("Séries incluídas")
        + tabela(["Código", "Série", "Unidade", "Fonte"], series, "Séries do Banco Central (SGS) usadas no simulador de Auto Equity.")
        + h2("Último mês de cada série")
        + tabela(["Série", "Mês", "Valor"], _ultimos(), "Valores do arquivo desta página, sem arredondar além de duas casas.")
        + p(_leitura_garantia("Quem pensa em dar o veículo em garantia pode usar essa distância como régua para a conversa com o parceiro: ela é média de mercado, não taxa de proposta."))
        + h2("Licença")
        + p("Inclui dados do Banco Central do Brasil, que os publica sob a licença ODbL 1.0 (" + a("https://opendatacommons.org/licenses/odbl/1-0/", "https://opendatacommons.org/licenses/odbl/1-0/") +
            "). A base derivada segue a mesma licença ODbL 1.0: pode copiar, distribuir e adaptar, desde que cite a fonte e mantenha a licença.")
        + h2("Como citar")
        + p("Cite como: " + CITACAO + ", com a data de acesso, e cite também o Banco Central do Brasil como fonte original.")
        + h2("Limites")
        + ul([
            "Média de mercado de contratos novos não é oferta: a sua taxa pode ficar acima ou abaixo.",
            "A série de crédito com garantia real mistura imóvel e veículo; o Banco Central não separa o Auto Equity.",
            "As séries saem com defasagem. Veja " + a("/taxas-de-referencia", "de onde vêm os números") + " e " + a("/metodologia", "como calculamos") + ".",
            "Para acompanhar as atualizações, use o " + a("/feed.xml", "feed Atom") + " ou a página " + a("/atualizacoes", "Atualizações") + ".",
        ])
    )


def corpo_sobre(ctx):
    return (
        p("Datalab Global é uma marca de " + ctx["razao"] + ", CNPJ " + ctx["cnpj"] + ". Este simulador existe para você ver a parcela e o custo do Auto Equity antes de pedir uma proposta.")
        + h2("Quem analisa o seu pedido")
        + p("Quem analisa o pedido é um parceiro de crédito: é dele a avaliação do veículo e a proposta. A Datalab Global não empresta dinheiro e não é banco.")
        + h2("O que fazemos")
        + ul([
            "Exibimos a parcela e o total estimados, com a conta e as fontes à vista (veja " + a("/metodologia", "Metodologia") + ").",
            "Ao lado, as taxas do Banco Central permitem comparar tipos de crédito (veja " + a("/taxas-de-referencia", "Taxas do Banco Central") + ").",
            "Este site não coleta dado pessoal: o que você digita fica no seu navegador.",
            "Não fazemos ranking de bancos nem recomendamos uma instituição.",
            "Não prometemos aprovação: quem decide é a análise do parceiro.",
        ])
        + h2("Por que este simulador existe")
        + p("Dar o carro em garantia é uma decisão séria, e a parcela é só uma parte dela. Fizemos o simulador para mostrar primeiro o custo e as alternativas e só depois o caminho até o pedido.")
        + h2("Contato")
        + p('E-mail: <a href="mailto:' + ctx["email"] + '">' + ctx["email"] + "</a>. Achou um número errado ou desatualizado? Escreva: corrigimos e anotamos em "
            + a("/atualizacoes", "Atualizações") + ".")
    )


ATUALIZACOES = [
    ("23/11/2026", "Retirada a opção SAC do simulador: o Auto Equity tem só parcela fixa (Price). Links antigos com sistema=sac abrem no Price."),
    ("19/11/2026", "Primeira versão do simulador de Auto Equity: parcela estimada para o crédito com veículo em garantia, Raio-X da decisão, escolha entre Price e SAC, amortização e pagar antes, comparação com outros tipos de crédito, troca de dívida cara e guias sobre garantia, custos e taxas."),
]


def corpo_atualizacoes(ctx):
    itens = "".join("<li><b>" + d + "</b> — " + t + "</li>" for d, t in ctx["atualizacoes"])
    return p("Registro das mudanças relevantes: conferências, correções e novas páginas. A mais recente aparece primeiro.") + "<ul>" + itens + "</ul>\n"


def _secoes(secoes):
    return "".join(h2(t) + "".join(p(x) for x in ps) for t, ps in secoes)


def corpo_privacidade(ctx):
    return (
        p("Esta Política explica como este site trata dados pessoais, em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018). Última atualização: " + ctx["atualizado"] + ".")
        + _secoes([
            ("1. Dados que este site coleta",
             ["Nenhum dado pessoal é pedido neste site. Os valores que você digita no simulador ficam no seu navegador. Se você escrever para " + ctx["email"] +
              ", guardamos o seu e-mail e o conteúdo da mensagem para responder."]),
            ("2. Medição de uso",
             ["Usamos o Umami, que não usa cookies e não identifica você. Ele conta visitas e alguns eventos (usar a simulação, abrir a tela de confirmação, seguir para o parceiro e copiar o link), "
              "com o valor a receber e o prazo simulados. A hospedagem (Cloudflare) pode tratar o endereço IP para entregar o site e proteger contra ataques."]),
            ("3. Ao seguir para o parceiro",
             ["Ao clicar em continuar para o parceiro, você sai deste site e abre o formulário de um parceiro de crédito. Este site não envia a ele os valores da simulação. "
              "Os dados que você digitar lá (documentos, renda, dados do veículo) são tratados pelo parceiro, conforme a política dele, e não passam por este site."]),
            ("4. Bases legais",
             ["Tratamos dados com base no legítimo interesse (segurança e melhoria do site), no cumprimento de obrigações legais e, quando for o caso, no seu consentimento."]),
            ("5. Compartilhamento",
             ["Não vendemos dados. Compartilhamos o mínimo com provedores que operam o site (hospedagem e medição), sob contrato."]),
            ("6. Seus direitos",
             ["Você pode pedir confirmação de tratamento, acesso, correção, eliminação e revogação de consentimento, a qualquer momento, pelo e-mail " + ctx["email"] + "."]),
            ("7. Cookies e armazenamento", ["Este site não usa cookies de publicidade nem de rastreamento.", "Para o botão \"Voltar à simulação\" funcionar, os números da última simulação (valor do veículo, valor a receber, prazo e sistema) ficam guardados só na aba do seu navegador e somem quando ela é fechada. Nada disso é enviado para fora."]),
            ("8. Contato e alterações",
             ["O canal para assuntos de privacidade é " + ctx["email"] + ". Esta Política pode ser atualizada; vale a versão publicada nesta página. Responsável: " + ctx["razao"] + ", CNPJ " + ctx["cnpj"] + "."]),
        ])
    )


def corpo_termos(ctx):
    return (
        p("Estes Termos regulam o uso deste site. Ao usar o site, você concorda com as condições abaixo. Última atualização: " + ctx["atualizado"] + ".")
        + _secoes([
            ("1. O que é este site",
             ["Um simulador de Auto Equity mantido por " + ctx["razao"] + " (marca Datalab Global). Ele mostra estimativas e leva você ao formulário de um parceiro de crédito, que é quem analisa o pedido."]),
            ("2. A simulação não é proposta de crédito",
             ["Os números são estimativas informativas, feitas com taxas de referência. Não são oferta, promessa de crédito nem recomendação financeira. "
              "A aprovação, o valor, a taxa e as condições finais dependem da análise de crédito e da avaliação do veículo pelo parceiro."]),
            ("3. Uso permitido",
             ["Você pode usar o site para fins lícitos. É proibido tentar acessar áreas restritas, sobrecarregar a infraestrutura ou extrair dados em massa de forma automatizada sem autorização."]),
            ("4. Propriedade intelectual",
             ["Marca, layout e textos pertencem aos seus titulares. Os dados das taxas do Banco Central seguem a licença da fonte (ODbL 1.0)."]),
            ("5. Limitação de responsabilidade",
             ["O site é oferecido no estado em que se encontra. Fazemos esforços razoáveis para mantê-lo correto e disponível, mas não garantimos ausência de falhas. A relação de crédito é entre você e o parceiro."]),
            ("6. Alterações e contato", ["Podemos atualizar estes Termos; vale a versão publicada nesta página. Dúvidas: " + ctx["email"] + "."]),
        ])
    )


# slug, título (≤ 60 caracteres), h1, descrição, corpo, cartão na home (texto) ou None
PAGINAS = [
    dict(slug="como-funciona", cartao="Como funciona o Auto Equity", title="Como funciona o Auto Equity, passo a passo",
         h1="Como funciona o Auto Equity, passo a passo",
         desc="Entenda o crédito com veículo em garantia: quanto libera, como se paga, o que o parceiro analisa e as etapas até receber.", corpo=corpo_como_funciona),
    dict(slug="garantia-do-veiculo", cartao="A garantia do veículo", title="Garantia do veículo no Auto Equity: como funciona",
         h1="Como funciona a garantia do veículo",
         desc="O que muda quando o veículo fica como garantia: uso, gravame, venda, o que acontece em caso de atraso e como escolher uma parcela com folga.", corpo=corpo_garantia),
    dict(slug="custos-alem-dos-juros", cartao="Custos além dos juros", title="Custos do Auto Equity além dos juros",
         h1="Custos do Auto Equity além dos juros",
         desc="IOF, avaliação do veículo, registro do gravame e seguros: o que pode somar à parcela e por que pedir o CET da proposta.", corpo=corpo_custos),
    dict(slug="auto-equity-ou-outro-credito", cartao="Auto Equity ou outro crédito", title="Auto Equity ou outro crédito: compare o custo mensal",
         h1="Auto Equity ou outro crédito: compare o custo mensal",
         desc="A mesma conta para Auto Equity, crédito pessoal, cheque especial e cartão rotativo, com as médias do Banco Central.", corpo=corpo_comparar),
    dict(slug="quando-nao-vale-a-pena", cartao="Quando não vale a pena", title="Quando o Auto Equity não vale a pena (e quando pode valer)",
         h1="Quando o Auto Equity não vale a pena",
         desc="Situações em que vale pensar duas vezes antes de dar o veículo em garantia, e as em que o crédito pode fazer sentido.", corpo=corpo_quando_nao),
    dict(slug="taxas-de-referencia", cartao="Taxas do Banco Central", title="Taxas de referência do Auto Equity e do Banco Central",
         h1="Taxas de referência: de onde vêm os números",
         desc="A taxa média do parceiro (1,39% ao mês) e as médias do Banco Central usadas no simulador, com o mês e a fonte de cada uma.", corpo=corpo_taxas),
    dict(slug="metodologia", cartao=None, menu="Metodologia", title="Metodologia: como calculamos o Auto Equity",
         h1="Metodologia: como calculamos a parcela", desc="A conta do simulador, passo a passo, o que o parceiro divulga, o que a tela não impõe e como o Raio-X compara cenários.", corpo=corpo_metodologia),
    dict(slug="dados-abertos", cartao=None, menu="Dados abertos", title="Dados abertos: taxas de referência do Auto Equity (CSV)",
         h1="Dados abertos: taxas de referência em CSV",
         desc="Baixe em CSV as taxas médias do Banco Central usadas no simulador de Auto Equity, com colunas, licença ODbL 1.0 e como citar.", corpo=corpo_dados_abertos),
    dict(slug="sobre", cartao=None, menu="Sobre", title="Sobre o simulador de Auto Equity da Datalab Global",
         h1="Sobre este simulador", desc="Quem mantém o simulador de Auto Equity (empréstimo com garantia de veículo), o que a Datalab Global faz, o que não faz e como falar com a gente.", corpo=corpo_sobre),
    dict(slug="atualizacoes", cartao=None, menu="Atualizações", title="Atualizações do simulador de Auto Equity",
         h1="Atualizações do simulador", desc="Registro das mudanças, conferências de taxas e correções do simulador de Auto Equity, com a data de cada atualização.", corpo=corpo_atualizacoes, guia=False),
    dict(slug="privacidade", cartao=None, menu="Privacidade", title="Privacidade do simulador de Auto Equity", h1="Política de Privacidade",
         desc="Como o simulador de Auto Equity trata dados pessoais (LGPD): o que não coletamos, a medição sem cookies e como falar com a gente.", corpo=corpo_privacidade, guia=False),
    dict(slug="termos", cartao=None, menu="Termos de uso", title="Termos de uso do simulador de Auto Equity", h1="Termos de Uso",
         desc="Condições de uso do simulador de Auto Equity: a simulação não é proposta de crédito, limites de responsabilidade e como falar com a gente.", corpo=corpo_termos, guia=False),
]
