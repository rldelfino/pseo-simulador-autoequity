"""Amortização antecipada: conta em Python (casos que se conferem na mão) e igualdade com o JS (Node)."""
import json
import shutil
import subprocess

import pytest

import calculo as c
import gerador_autoequity as g

NODE = shutil.which("node")
CASOS = [
    ("price", 50_000, 0.0139, 48, 200, 5_000, 6, "prazo"),
    ("price", 50_000, 0.0139, 48, 0, 5_000, 6, "parcela"),
    ("sac", 50_000, 0.0139, 48, 300, 8_000, 0, "prazo"),
    ("sac", 50_000, 0.0139, 48, 0, 8_000, 24, "parcela"),
    ("price", 20_000, 0.02, 24, 100, 0, 0, "prazo"),
]


@pytest.mark.parametrize("sistema", ["price", "sac"])
def test_sem_extra_nada_muda(sistema):
    r = c.amortizar_antes(50_000, 0.0139, 48, sistema)
    assert r["meses"] == 48
    assert r["total"] == pytest.approx(c.plano(50_000, 0.0139, 48, sistema)[2], rel=1e-9)


def test_extra_mensal_encurta_o_prazo_e_economiza():
    base = c.amortizar_antes(50_000, 0.0139, 48)
    r = c.amortizar_antes(50_000, 0.0139, 48, extra_mensal=200)
    assert r["meses"] < base["meses"]
    assert r["juros"] < base["juros"]
    # o saldo fecha em zero: tudo que foi pago = crédito + juros
    assert r["total"] == pytest.approx(50_000 + r["juros"])


def test_valor_unico_prazo_e_parcela_economizam_menos_que_o_prazo():
    base = c.amortizar_antes(50_000, 0.0139, 48)
    prazo = c.amortizar_antes(50_000, 0.0139, 48, unico=10_000, mes_unico=6, modo="prazo")
    parcela = c.amortizar_antes(50_000, 0.0139, 48, unico=10_000, mes_unico=6, modo="parcela")
    assert prazo["juros"] < base["juros"] and parcela["juros"] < base["juros"]
    assert prazo["meses"] < 48 and parcela["meses"] == 48
    assert prazo["juros"] < parcela["juros"]  # encurtar o prazo poupa mais juros
    assert parcela["parcela_nova"] < c.pmt(50_000, 0.0139, 48)


def test_quanto_antes_mais_economiza():
    juros = [c.amortizar_antes(50_000, 0.0139, 48, unico=6_000, mes_unico=k)["juros"] for k in range(0, 48)]
    assert juros == sorted(juros)  # amortizar mais tarde só encarece


def test_valor_unico_maior_que_o_saldo_quita_tudo():
    r = c.amortizar_antes(20_000, 0.01, 36, unico=10_000_000, mes_unico=6)
    assert r["meses"] == 6
    assert r["total"] == pytest.approx(r["total"]) and r["juros"] > 0


@pytest.mark.skipif(NODE is None, reason="Node não instalado")
@pytest.mark.parametrize("sistema,credito,i,meses,extra,unico,mes,modo", CASOS)
def test_js_igual_ao_python(tmp_path, sistema, credito, i, meses, extra, unico, mes, modo):
    js = tmp_path / "calculo.js"
    js.write_text(g.gerar_calculo_js(), encoding="utf-8")
    prog = ("const H=require(%s);console.log(JSON.stringify(H.amortizarAntes(%r,%r,%r,%r,%r,%r,%r,%r)))"
            % (json.dumps(str(js)), credito, i, meses, sistema, extra, unico, mes, modo))
    out = json.loads(subprocess.run([NODE, "-e", prog], capture_output=True, text=True, check=True, timeout=30).stdout)
    py = c.amortizar_antes(credito, i, meses, sistema, extra, unico, mes, modo)
    assert out["meses"] == py["meses"]
    assert out["total"] == pytest.approx(py["total"], rel=1e-9)
    assert out["juros"] == pytest.approx(py["juros"], rel=1e-9, abs=1e-6)
    if py["parcela_nova"] is None:
        assert out["parcelaNova"] is None
    else:
        assert out["parcelaNova"] == pytest.approx(py["parcela_nova"], rel=1e-9)
