/* GERADO por gerador_autoequity.py a partir de calculo.py e dados/taxas_referencia.csv. Não edite à mão.
   Mesma conta de calculo.py (os testes comparam os dois). */
(function (root) {
  'use strict';
  var TAXA_PARCEIRO_AM = 1.39;
  var LTV_MAX = 0.8;
  var CREDITO_MAX = 1000000000;
  var PRAZO_MIN_MESES = 1;
  var PRAZO_MAX_MESES = 120;
  var SLIDER_PRAZO_MIN = 6;
  var SLIDER_PRAZO_MAX = 60;
  var PRAZO_SUGERIDO_MAX = 60;
  var VEICULO_MIN = 1;
  var VEICULO_MAX = 1000000000;
  var RECEBER_MIN = 1;
  var RECEBER_PASSO = 1000;
  var TAXA_PROPRIA_MIN = 0.01;
  var TAXA_PROPRIA_MAX = 30.0;
  var PERIODO_MESES = 6;
  var RENDA_REFERENCIA = 0.3;
  // Referências do Banco Central (médias de mercado, não oferta): taxa média de crédito com garantia real e das dívidas caras (% ao mês).
  var REF = {"chequeAm": 7.5316195526967, "chequeMes": "set/2026", "garantiaRealAm": 2.14, "garantiaRealMes": "set/2026", "pessoalAm": 6.417547301774995, "pessoalMes": "set/2026", "rotativoAm": 15.294671960948625, "rotativoMes": "set/2026"};

  function taxaMensal(baseAm) { return (baseAm === undefined ? TAXA_PARCEIRO_AM : baseAm) / 100; }
  function pmt(principal, i, n) { return i === 0 ? principal / n : principal * i / (1 - Math.pow(1 + i, -n)); }
  function valorPresente(parcela, i, n) { return i === 0 ? parcela * n : parcela * (1 - Math.pow(1 + i, -n)) / i; }
  function valorPresenteSac(primeira, i, n) { return primeira / (1 / n + i); }
  function limiteCredito(veiculo) { return Math.min(LTV_MAX * veiculo, CREDITO_MAX); }
  function rendaParaParcela(parcela, fracao) { return parcela / (fracao === undefined ? RENDA_REFERENCIA : fracao); }

  // [primeira parcela, última parcela, total pago]. No Price as duas parcelas são iguais; no SAC a parcela cai todo mês.
  function plano(credito, i, meses, sistema) {
    if (sistema === 'sac') {
      var am = credito / meses;
      return [am + credito * i, am * (1 + i), credito + credito * i * (meses + 1) / 2];
    }
    var p = pmt(credito, i, meses);
    return [p, p, p * meses];
  }

  function simular(veiculo, receber, saldo, meses, i, sistema) {
    var credito = receber + saldo;
    var pl = plano(credito, i, meses, sistema);
    return { credito: credito, parcela: pl[0], parcelaFinal: pl[1], total: pl[2], juros: pl[2] - credito, ltv: veiculo > 0 ? credito / veiculo : 0,
             limite: limiteCredito(veiculo), acimaLimite: credito > limiteCredito(veiculo) + 1e-9 };
  }

  function receberParaParcela(parcelaAlvo, saldo, meses, i, passo, sistema) {
    var bruto = (sistema === 'sac' ? valorPresenteSac(parcelaAlvo, i, meses) : valorPresente(parcelaAlvo, i, meses)) - saldo;
    return Math.max(0, Math.floor(bruto / passo) * passo);
  }

  // Juros, amortização e saldo devedor por bloco de `bloco` meses (padrão 6).
  function amortizacaoPeriodos(credito, i, meses, sistema, bloco) {
    bloco = bloco || PERIODO_MESES;
    var parcela = pmt(credito, i, meses), amSac = credito / meses, saldo = credito, restante = meses, n = 0, linhas = [];
    while (restante > 0) {
      n += 1;
      var juros = 0, amortizado = 0, q = Math.min(bloco, restante);
      for (var k = 0; k < q; k++) { var j = saldo * i, a = sistema === 'sac' ? amSac : parcela - j; saldo -= a; juros += j; amortizado += a; }
      restante -= bloco;
      linhas.push({ periodo: n, juros: juros, amortizacao: amortizado, saldo: saldo > 0.005 ? saldo : 0 });
    }
    return linhas;
  }

  // Total pago até o fim de cada mês (índice 0 = 0): a linha do gráfico "quanto você terá pago ao longo do tempo".
  function acumuladoMensal(credito, i, meses, sistema) {
    var saida = [0], total = 0, k;
    if (sistema === 'sac') {
      var am = credito / meses, saldo = credito;
      for (k = 0; k < meses; k++) { total += am + saldo * i; saldo -= am; saida.push(total); }
      return saida;
    }
    var p = pmt(credito, i, meses);
    saida = [];
    for (k = 0; k <= meses; k++) saida.push(p * k);
    return saida;
  }

  // Pagar a mais: extraMensal em toda parcela e/ou unico no começo do mês mesUnico (0 = antes da 1ª parcela). modo "prazo" (parcela igual, acaba antes) ou "parcela" (recalcula depois do valor único).
  function amortizarAntes(credito, i, meses, sistema, extraMensal, unico, mesUnico, modo) {
    var saldo = credito, parcela = pmt(credito, i, meses), am = credito / meses, total = 0, nova = null;
    for (var m = 0; m < meses; m++) {
      if (m === mesUnico && unico > 0) {
        var u = Math.min(unico, saldo);
        saldo -= u; total += u;
        if (modo === 'parcela' && saldo > 0.005) { parcela = pmt(saldo, i, meses - m); am = saldo / (meses - m); }
      }
      if (saldo <= 0.005) return { meses: m, total: total, juros: total - credito, parcelaNova: nova };
      var j = saldo * i, pago = (sistema === 'sac' ? am + j : parcela) + extraMensal;
      pago = Math.min(pago, saldo + j);
      if (m === mesUnico && nova === null) nova = sistema === 'sac' ? am + j : parcela;
      saldo -= pago - j; total += pago;
    }
    return { meses: meses, total: total, juros: total - credito, parcelaNova: nova };
  }

  function compararQuitacao(divida, taxaDividaAm, meses, i, sistema) {
    var atual = pmt(divida, taxaDividaAm, meses), pl = plano(divida, i, meses, sistema);
    return { divida: divida, parcelaAtual: atual, totalAtual: atual * meses, jurosMes1: divida * taxaDividaAm,
             parcelaAe: pl[0], totalAe: pl[2], economiaMes: atual - pl[0], economiaTotal: atual * meses - pl[2] };
  }

  function brl(v) { return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(Math.round(v)); }
  function pct(v) { return v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%'; }

  var api = { TAXA_PARCEIRO_AM: TAXA_PARCEIRO_AM, LTV_MAX: LTV_MAX, CREDITO_MAX: CREDITO_MAX, PRAZO_MIN_MESES: PRAZO_MIN_MESES, PRAZO_MAX_MESES: PRAZO_MAX_MESES, SLIDER_PRAZO_MIN: SLIDER_PRAZO_MIN, SLIDER_PRAZO_MAX: SLIDER_PRAZO_MAX, PRAZO_SUGERIDO_MAX: PRAZO_SUGERIDO_MAX, VEICULO_MIN: VEICULO_MIN, VEICULO_MAX: VEICULO_MAX,
              RECEBER_MIN: RECEBER_MIN, RECEBER_PASSO: RECEBER_PASSO, TAXA_PROPRIA_MIN: TAXA_PROPRIA_MIN, TAXA_PROPRIA_MAX: TAXA_PROPRIA_MAX, PERIODO_MESES: PERIODO_MESES, RENDA_REFERENCIA: RENDA_REFERENCIA,
              ref: REF, taxaMensal: taxaMensal, pmt: pmt, valorPresente: valorPresente, valorPresenteSac: valorPresenteSac, plano: plano, rendaParaParcela: rendaParaParcela, limiteCredito: limiteCredito,
              simular: simular, receberParaParcela: receberParaParcela, amortizacaoPeriodos: amortizacaoPeriodos, acumuladoMensal: acumuladoMensal, amortizarAntes: amortizarAntes, compararQuitacao: compararQuitacao, brl: brl, pct: pct };
  root.DatalabAutoEquity = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
