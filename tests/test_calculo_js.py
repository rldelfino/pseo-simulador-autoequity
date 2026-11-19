"""A conta do navegador (calculo.js) precisa dar o mesmo resultado que calculo.py. Usa o Node; sem Node o teste é pulado."""
import json
import shutil
import subprocess

import pytest

import calculo as c
import gerador_autoequity as g

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node não instalado")

CASOS = [(100_000, 50_000, 0, 48), (30_000, 10_000, 0, 12), (250_000, 150_000, 0, 60), (80_000, 20_000, 30_000, 36),
         (45_000, 5_000, 20_000, 6), (500_000, 100_000, 50_000, 24), (1_000_000, 190_000, 10_000, 60), (60_000, 30_000, 10_000, 18)]
TAXAS = [0.5, 1.39, 3.0]


def _js(tmp_path):
    js = tmp_path / "calculo.js"
    js.write_text(g.gerar_calculo_js(), encoding="utf-8")
    return json.dumps(str(js))


def _rodar(tmp_path, caso, taxa):
    prog = ("const H=require(%s);const i=H.taxaMensal(%r);const [ve,re,sa,me]=%s;"
            "console.log(JSON.stringify({i:i,r:H.simular(ve,re,sa,me,i),alvo:H.receberParaParcela(1500,sa,me,i,1000)}))") % (_js(tmp_path), taxa, json.dumps(caso))
    out = subprocess.run([NODE, "-e", prog], capture_output=True, text=True, check=True, timeout=30).stdout
    return json.loads(out)


@pytest.mark.parametrize("caso", CASOS)
@pytest.mark.parametrize("taxa", TAXAS)
def test_js_igual_ao_python(tmp_path, caso, taxa):
    ve, re_, sa, me = caso
    r = _rodar(tmp_path, caso, taxa)
    i = c.taxa_mensal(taxa)
    py = c.simular(ve, re_, sa, me, i)
    assert r["i"] == pytest.approx(i, rel=1e-12)
    for k in ("credito", "parcela", "total", "juros", "ltv", "limite"):
        assert r["r"][k] == pytest.approx(py[k], rel=1e-9)
    assert r["r"]["acimaLimite"] == py["acima_limite"]
    assert r["alvo"] == c.receber_para_parcela(1500, sa, me, i)


def test_taxa_padrao_do_js_e_a_do_parceiro(tmp_path):
    out = subprocess.run([NODE, "-e", "const H=require(%s);console.log(H.taxaMensal())" % _js(tmp_path)], capture_output=True, text=True, check=True, timeout=30).stdout
    assert float(out) == pytest.approx(c.taxa_mensal(), rel=1e-12)


def test_calculo_js_tem_as_referencias_do_bcb_e_os_limites(tmp_path):
    texto = g.gerar_calculo_js()
    assert "garantiaRealAm" in texto and "ipca" not in texto.lower()
    assert "@@" not in texto
    assert "PRAZO_MAX_MESES = %d" % c.PRAZO_MAX_MESES in texto and "CREDITO_MAX = %d" % c.CREDITO_MAX in texto


@pytest.mark.parametrize("caso", CASOS)
def test_sac_js_igual_ao_python(tmp_path, caso):
    """SAC: primeira e última parcela, total, amortização por bloco, acumulado mensal, valor a receber e quitação iguais nas duas contas."""
    ve, re_, sa, me = caso
    prog = ("const H=require(%s);const i=H.taxaMensal();const [ve,re,sa,me]=%s;const cr=re+sa;"
            "console.log(JSON.stringify({r:H.simular(ve,re,sa,me,i,'sac'),a:H.amortizacaoPeriodos(cr,i,me,'sac'),ac:H.acumuladoMensal(cr,i,me,'sac'),acp:H.acumuladoMensal(cr,i,me,'price'),"
            "alvo:H.receberParaParcela(3000,sa,me,i,1000,'sac'),q:H.compararQuitacao(20000,0.0642,me,i,'sac'),renda:H.rendaParaParcela(3000)}))") % (_js(tmp_path), json.dumps(caso))
    out = json.loads(subprocess.run([NODE, "-e", prog], capture_output=True, text=True, check=True, timeout=30).stdout)
    i = c.taxa_mensal()
    py = c.simular(ve, re_, sa, me, i, "sac")
    for k_js, k_py in (("credito", "credito"), ("parcela", "parcela"), ("parcelaFinal", "parcela_final"), ("total", "total"), ("juros", "juros")):
        assert out["r"][k_js] == pytest.approx(py[k_py], rel=1e-9)
    assert py["parcela"] > py["parcela_final"]
    esperado = c.amortizacao_periodos(re_ + sa, i, me, "sac")
    assert len(out["a"]) == len(esperado)
    for x, y in zip(out["a"], esperado):
        assert x["periodo"] == y["periodo"]
        for k in ("juros", "amortizacao", "saldo"):
            assert x[k] == pytest.approx(y[k], rel=1e-8, abs=1e-6)
    assert out["ac"] == pytest.approx(c.acumulado_mensal(re_ + sa, i, me, "sac"), rel=1e-9)
    assert out["acp"] == pytest.approx(c.acumulado_mensal(re_ + sa, i, me, "price"), rel=1e-9)
    assert out["ac"][-1] == pytest.approx(py["total"], rel=1e-9)
    assert out["alvo"] == c.receber_para_parcela(3000, sa, me, i, sistema="sac")
    q = c.comparar_quitacao(20000, 0.0642, me, i, "sac")
    for k_js, k_py in (("parcelaAe", "parcela_ae"), ("totalAe", "total_ae"), ("economiaMes", "economia_mes"), ("economiaTotal", "economia_total")):
        assert out["q"][k_js] == pytest.approx(q[k_py], rel=1e-9)
    assert out["renda"] == pytest.approx(c.renda_para_parcela(3000))
