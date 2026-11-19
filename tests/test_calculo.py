import pytest

import calculo as c


def test_pmt_exemplo_do_cenario_padrao():
    i = c.taxa_mensal()
    assert i == pytest.approx(0.0139)
    r = c.simular(100_000, 50_000, 0, 48, i)
    assert round(r["parcela"]) == 1434
    assert round(r["total"]) == 68855
    assert r["ltv"] == pytest.approx(0.5)
    assert not r["acima_limite"]


def test_taxa_propria_vale_como_esta_sem_ipca():
    assert c.taxa_mensal(2.5) == pytest.approx(0.025)
    assert c.taxa_mensal() == pytest.approx(c.TAXA_PARCEIRO_AM / 100)


def test_parcela_com_taxa_zero_divide_igual():
    assert c.pmt(12_000, 0, 12) == 1000


def test_valor_presente_e_inverso_do_pmt():
    i = 0.0139
    assert c.valor_presente(c.pmt(40_000, i, 36), i, 36) == pytest.approx(40_000)


def test_saldo_entra_no_credito_e_no_limite():
    r = c.simular(100_000, 20_000, 30_000, 36, 0.0139)
    assert r["credito"] == 50_000
    assert r["limite"] == 80_000
    assert not r["acima_limite"]
    assert c.simular(100_000, 60_000, 30_000, 36, 0.0139)["acima_limite"]
    assert c.receber_maximo(100_000, 30_000) == 50_000
    assert c.receber_maximo(100_000, 90_000) == 0


def test_receber_para_parcela_cabe_na_parcela_alvo():
    i = 0.0139
    v = c.receber_para_parcela(1500, 0, 48, i)
    assert v % c.RECEBER_PASSO == 0
    assert c.pmt(v, i, 48) <= 1500
    assert c.pmt(v + c.RECEBER_PASSO, i, 48) > 1500


def test_prazo_invalido():
    with pytest.raises(ValueError):
        c.pmt(1000, 0.01, 0)


def test_limites_divulgados_pelo_parceiro():
    assert c.LTV_MAX == 0.80
    assert c.TAXA_PARCEIRO_AM == 1.39


def test_limites_de_interface_a_confirmar_estao_nas_constantes():
    """O parceiro não publica prazo máximo nem mínimo/teto de crédito: são limites da tela (a confirmar), não regra dele."""
    assert (c.PRAZO_MIN_MESES, c.PRAZO_MAX_MESES) == (6, 60)
    assert (c.RECEBER_MIN, c.CREDITO_MAX) == (5_000, 200_000)
    assert c.RECEBER_MIN < c.CREDITO_MAX and c.VEICULO_MIN < c.VEICULO_MAX


def test_teto_de_credito_da_ferramenta():
    assert c.limite_credito(100_000) == 80_000            # 80% vale abaixo do teto
    assert c.limite_credito(1_000_000) == 200_000         # acima, o teto vale
    assert c.receber_maximo(1_000_000, 50_000) == 150_000
    assert c.simular(1_000_000, 210_000, 0, 48, 0.0139)["acima_limite"] is True


def test_sac_fecha_a_conta():
    i = c.taxa_mensal()
    cred, n = 50_000, 48
    r = c.simular(100_000, cred, 0, n, i, "sac")
    assert r["parcela"] == pytest.approx(cred / n + cred * i)
    assert r["parcela_final"] == pytest.approx(cred / n * (1 + i))
    acum = c.acumulado_mensal(cred, i, n, "sac")
    assert acum[-1] == pytest.approx(r["total"]) and len(acum) == n + 1
    p = c.simular(100_000, cred, 0, n, i)
    assert r["total"] < p["total"] and r["parcela"] > p["parcela"] and r["parcela_final"] < p["parcela"]
    assert p["parcela_final"] == pytest.approx(p["parcela"])
    assert c.valor_presente_sac(r["parcela"], i, n) == pytest.approx(cred)


def test_receber_para_parcela_sac_cabe_na_parcela():
    i = c.taxa_mensal()
    alvo = c.receber_para_parcela(2500, 0, 36, i, sistema="sac")
    assert alvo > 0
    assert c.simular(100_000, alvo, 0, 36, i, "sac")["parcela"] <= 2500
    assert c.simular(100_000, alvo + c.RECEBER_PASSO, 0, 36, i, "sac")["parcela"] > 2500


def test_renda_para_parcela_usa_30_por_cento():
    assert c.renda_para_parcela(3000) == pytest.approx(10_000)
