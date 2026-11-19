"""Conta do simulador de Auto Equity (referência em Python; src/simulador.js usa a mesma conta, gerada em calculo.js, e os testes comparam as duas).

Modelo: parcela fixa (tabela Price, padrão) ou parcelas que caem (SAC) sobre o crédito total, com a taxa de referência do parceiro (sem IPCA).
O SAC é uma opção de simulação na mesma taxa: o parceiro confirma na proposta quais sistemas oferece.
  - taxa do parceiro: "média" de 1,39% a.m. no gráfico de taxas de veículo em garantia (página pública do parceiro, conferida em 18/11/2026). É média divulgada, não "a partir de";
    não há atualização por IPCA: a parcela é fixa;
  - limite: o parceiro divulga que libera "até 80% do valor do veículo".
NÃO são publicados pelo parceiro (por isso os valores abaixo são limites de INTERFACE, a confirmar, e não regra dele): prazo máximo, crédito mínimo e teto de crédito.
É ESTIMATIVA: a taxa e o limite finais saem da análise do parceiro. Não inclui IOF, avaliação do veículo, registro do gravame nem seguros.
"""

TAXA_PARCEIRO_AM = 1.39   # % ao mês, "média" divulgada pelo parceiro (parcela fixa, sem IPCA)
LTV_MAX = 0.80            # fração do valor do veículo
# --- A CONFIRMAR: o parceiro não publica prazo máximo, mínimo nem teto de crédito. Limites conservadores só da interface. ---
PRAZO_MIN_MESES = 6       # limite de interface
PRAZO_MAX_MESES = 60      # limite de interface (sugestão do plano; não é regra do parceiro)
CREDITO_MAX = 200_000     # teto de crédito da interface (sugestão do plano; não é regra do parceiro)
RECEBER_MIN = 5_000       # crédito mínimo da interface (não é regra do parceiro)
RECEBER_PASSO = 1_000     # passo das sugestões e do controle deslizante
VEICULO_MIN = 15_000
VEICULO_MAX = 2_000_000
TAXA_PROPRIA_MIN = 0.5    # faixa aceita no campo "taxa da proposta" (% ao mês, digitada como está, sem IPCA)
TAXA_PROPRIA_MAX = 6.0
PERIODO_MESES = 6         # a amortização e os gráficos agrupam a conta em blocos de 6 meses
SISTEMAS = ("price", "sac")  # price = parcela fixa; sac = amortização constante, parcela que cai
RENDA_REFERENCIA = 0.30      # referência de mercado (política de crédito das instituições), não regra do parceiro nem norma específica de crédito com veículo em garantia


def taxa_mensal(base_am=TAXA_PARCEIRO_AM):
    """Taxa mensal de referência, em fração. Sem IPCA: é a taxa do parceiro (ou a que a pessoa digitou da proposta), % ao mês -> fração."""
    return base_am / 100


def pmt(principal, i, n):
    """Parcela fixa (Price). i em fração ao mês, n em meses."""
    if n <= 0:
        raise ValueError("prazo precisa ser positivo")
    if i == 0:
        return principal / n
    return principal * i / (1 - (1 + i) ** -n)


def valor_presente(parcela, i, n):
    """Crédito que gera esta parcela (inverso do pmt)."""
    if i == 0:
        return parcela * n
    return parcela * (1 - (1 + i) ** -n) / i


def valor_presente_sac(primeira_parcela, i, n):
    """Crédito cuja PRIMEIRA parcela no SAC é primeira_parcela (primeira = credito/n + credito*i)."""
    return primeira_parcela / (1 / n + i)


def plano(credito, i, meses, sistema="price"):
    """(primeira parcela, última parcela, total pago). No Price as duas parcelas são iguais; no SAC a parcela cai todo mês."""
    if sistema == "sac":
        amort = credito / meses
        return amort + credito * i, amort * (1 + i), credito + credito * i * (meses + 1) / 2
    p = pmt(credito, i, meses)
    return p, p, p * meses


def acumulado_mensal(credito, i, meses, sistema="price"):
    """Total pago até o fim de cada mês (índice 0 = 0). Dá a linha do gráfico 'quanto você terá pago ao longo do tempo'."""
    saida = [0.0]
    total = 0.0
    if sistema == "sac":
        amort = credito / meses
        saldo = credito
        for _ in range(meses):
            total += amort + saldo * i
            saldo -= amort
            saida.append(total)
        return saida
    p = pmt(credito, i, meses)
    return [p * k for k in range(meses + 1)]


def renda_para_parcela(parcela, fracao=RENDA_REFERENCIA):
    """Renda mensal em que a parcela ocupa a fração dada (referência de 30%)."""
    return parcela / fracao


def limite_credito(valor_veiculo):
    return min(LTV_MAX * valor_veiculo, CREDITO_MAX)


def receber_maximo(valor_veiculo, saldo):
    return max(0.0, limite_credito(valor_veiculo) - saldo)


def simular(valor_veiculo, receber, saldo, meses, i, sistema="price"):
    """Devolve parcela (a primeira, no SAC), última parcela, total, juros e a relação crédito/veículo. credito = o que você recebe + o saldo do financiamento que o novo crédito quita."""
    credito = receber + saldo
    parcela, ultima, total = plano(credito, i, meses, sistema)
    return {
        "credito": credito,
        "parcela": parcela,
        "parcela_final": ultima,
        "total": total,
        "juros": total - credito,
        "ltv": credito / valor_veiculo if valor_veiculo > 0 else 0.0,
        "limite": limite_credito(valor_veiculo),
        "acima_limite": credito > limite_credito(valor_veiculo) + 1e-9,
    }


def amortizacao_periodos(credito, i, meses, sistema="price", bloco=PERIODO_MESES):
    """Como a dívida cai por bloco de `bloco` meses (padrão 6, o prazo é curto): juros pagos, amortização e saldo devedor no fim de cada bloco."""
    parcela = pmt(credito, i, meses)
    amort_sac = credito / meses
    saldo = credito
    linhas = []
    restante = meses
    n = 0
    while restante > 0:
        n += 1
        juros = amortizado = 0.0
        for _ in range(min(bloco, restante)):
            j = saldo * i
            a = amort_sac if sistema == "sac" else parcela - j
            saldo -= a
            juros += j
            amortizado += a
        restante -= bloco
        linhas.append({"periodo": n, "juros": juros, "amortizacao": amortizado, "saldo": saldo if saldo > 0.005 else 0.0})
    return linhas


def amortizar_antes(credito, i, meses, sistema="price", extra_mensal=0.0, unico=0.0, mes_unico=0, modo="prazo"):
    """Efeito de pagar a mais: `extra_mensal` em toda parcela e/ou `unico` no começo do mês `mes_unico` (0 = antes da 1ª parcela).
    modo "prazo": a parcela segue igual e a dívida acaba antes; "parcela": depois do valor único a parcela é recalculada para o prazo restante (o extra mensal sempre encurta o prazo).
    Devolve meses até quitar, total pago (parcelas + extras), juros e a primeira parcela depois do valor único (no SAC, a parcela daquele mês)."""
    saldo = credito
    parcela = pmt(credito, i, meses)
    amort = credito / meses
    total = 0.0
    nova = None
    for m in range(meses):
        if m == mes_unico and unico > 0:
            u = min(unico, saldo)
            saldo -= u
            total += u
            if modo == "parcela" and saldo > 0.005:
                parcela = pmt(saldo, i, meses - m)
                amort = saldo / (meses - m)
        if saldo <= 0.005:
            return {"meses": m, "total": total, "juros": total - credito, "parcela_nova": nova}
        j = saldo * i
        pago = (amort + j if sistema == "sac" else parcela) + extra_mensal
        pago = min(pago, saldo + j)
        if m == mes_unico and nova is None:
            nova = amort + j if sistema == "sac" else parcela
        saldo -= pago - j
        total += pago
    return {"meses": meses, "total": total, "juros": total - credito, "parcela_nova": nova}


def comparar_quitacao(divida, taxa_divida_am, meses, i, sistema="price"):
    """Mesma dívida e mesmo prazo: parcela e total na taxa da dívida (taxa_divida_am em fração ao mês, sempre parcela fixa) e no Auto Equity (taxa i, no sistema escolhido).
    Com SAC, a parcela do Auto Equity é a primeira. juros_mes1 = o que a dívida cobra de juros só no primeiro mês."""
    atual = pmt(divida, taxa_divida_am, meses)
    ae, _, total_ae = plano(divida, i, meses, sistema)
    return {
        "divida": divida,
        "parcela_atual": atual, "total_atual": atual * meses, "juros_mes1": divida * taxa_divida_am,
        "parcela_ae": ae, "total_ae": total_ae,
        "economia_mes": atual - ae, "economia_total": atual * meses - total_ae,
    }


def receber_para_parcela(parcela_alvo, saldo, meses, i, passo=RECEBER_PASSO, sistema="price"):
    """Maior valor a receber (múltiplo de `passo`) cuja parcela (a primeira, no SAC) cabe em parcela_alvo; 0 se nem o menor valor cabe."""
    bruto = (valor_presente_sac(parcela_alvo, i, meses) if sistema == "sac" else valor_presente(parcela_alvo, i, meses)) - saldo
    return max(0, int(bruto // passo) * passo)
