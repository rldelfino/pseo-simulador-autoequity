/* Interface do simulador de Auto Equity. Só textContent e atributos SVG (nada de innerHTML). Depende de calculo.js (window.DatalabAutoEquity).
   Sem cookies e sem dado pessoal: o simulador não envia nada para fora, só mede o uso (valor a receber e prazo) no Umami, sem identificar ninguém. */
(function () {
  'use strict';
  var H = window.DatalabAutoEquity;
  if (!H) return;

  var estado = { sistema: 'price', financiado: false, veiculo: 100000, saldo: 0, receber: 50000, meses: 48, conforto: 1500, divida: 20000, tipoDiv: 'pessoal', taxaDiv: 5, extra: 200, unico: 5000, quando: 6, taxaProp: 0 };
  var usou = false;
  var usouQuitar = false;
  var abriuAmort = false;
  var usouAmortExtra = false;
  var usouTaxaProp = false;
  var desenhos = 0;
  var timerUrl = null;
  var timerCopiado = null;
  var BRL_NUM = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

  function $(id) { return document.getElementById(id); }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function limpar(no) { while (no.firstChild) no.removeChild(no.firstChild); }
  function evento(nome, dados) {
    try { if (window.umami && window.umami.track) window.umami.track(nome, dados); } catch (e) { /* medição nunca quebra o simulador */ }
  }
  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function mil(v) { return v >= 1000000 ? (v / 1000000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' milhões' : 'R$ ' + Math.round(v / 1000) + ' mil'; }

  function lerNumero(texto) {
    var t = String(texto).replace(/[^\d.,]/g, '');
    if (t.indexOf(',') >= 0) t = t.replace(/\./g, '').replace(',', '.');
    else if (/\.\d{3}(\.|$)/.test(t)) t = t.replace(/\./g, '');
    var n = Number(t);
    return isFinite(n) ? n : 0;
  }

  function maxReceber() { return Math.max(0, H.limiteCredito(estado.veiculo) - estado.saldo); }
  function limiteTeto() { return H.LTV_MAX * estado.veiculo > H.CREDITO_MAX; }
  function minReceber() { return Math.min(H.RECEBER_MIN, maxReceber()); }
  // Taxa da proposta (opcional): a taxa mensal digitada vale como está (parcela fixa, sem IPCA).
  function taxaPropria() { return estado.taxaProp >= H.TAXA_PROPRIA_MIN && estado.taxaProp <= H.TAXA_PROPRIA_MAX; }
  function taxa() { return H.taxaMensal(taxaPropria() ? estado.taxaProp : undefined); }

  // estado.receber é o que a pessoa pediu; rec() é o que vale na conta (dentro do limite). O pedido só muda quando ela mexe no campo.
  function rec() { return clamp(estado.receber, minReceber(), maxReceber()); }

  function ajustar() {
    estado.veiculo = clamp(estado.veiculo, H.VEICULO_MIN, H.VEICULO_MAX);
    if (!estado.financiado) estado.saldo = 0;
    estado.saldo = clamp(estado.saldo, 0, H.limiteCredito(estado.veiculo));
    return rec() !== estado.receber;
  }

  function preencherRange(r, valor) {
    var min = Number(r.min), max = Number(r.max);
    var v = clamp(valor, min, max);
    r.value = v;
    // Sem style inline nem CSSOM (a CSP não permite e o Safari reclama): o CSS tem uma regra por inteiro de 0 a 100, escolhida por data-p.
    r.setAttribute('data-p', String(Math.round(max > min ? ((v - min) / (max - min)) * 100 : 0)));
  }

  function sac() { return estado.sistema === 'sac'; }
  // No SAC o número grande é a primeira parcela; os cartões avisam.
  function sufixoSis() { return sac() ? ['1ª parcela, no SAC'] : []; }

  // Cores das outras modalidades (as mesmas de conteudo.py: COR_MODALIDADE); o âmbar é só do Auto Equity.
  var COR = { ae: '#f59e0b', gar: '#7ea6d9', pessoal: '#b69be0', cheque: '#7dc4b0', rotativo: '#d98fb8' };

  function cartaoAlt(titulo, parcela, linhas, atual, destaque) {
    var d = el('div', 'alt' + (atual ? ' cur' : ''));
    d.appendChild(el('h3', '', titulo));
    d.appendChild(el('div', 'p num', H.brl(parcela)));
    var info = el('div', 'd');
    linhas.forEach(function (l, i) { if (i) info.appendChild(document.createElement('br')); info.appendChild(document.createTextNode(l)); });
    if (destaque) { info.appendChild(document.createElement('br')); info.appendChild(el('span', destaque.cls, destaque.texto)); }
    d.appendChild(info);
    return d;
  }

  var NS = 'http://www.w3.org/2000/svg';
  var CIRC = 289.0265; // circunferência da rosca (raio 46)
  function svgEl(tag, atributos) {
    var e = document.createElementNS(NS, tag);
    Object.keys(atributos).forEach(function (k) { e.setAttribute(k, String(atributos[k])); });
    return e;
  }

  // Rosca: do total pago, quanto é crédito e quanto é juros.
  function desenharRosca(r, semMargem) {
    var pj = !semMargem && r.total > 0 ? r.juros / r.total : 0;
    $('rosca-cred').setAttribute('stroke-dasharray', (semMargem ? 0 : (1 - pj) * CIRC).toFixed(1) + ' ' + CIRC.toFixed(2));
    $('rosca-pct').textContent = semMargem ? '—' : Math.round(pj * 100) + '%';
    $('rosca-cred-v').textContent = semMargem ? '—' : H.brl(r.credito);
    $('rosca-juros-v').textContent = semMargem ? '—' : H.brl(r.juros);
    $('rosca-svg').setAttribute('aria-label', semMargem ? 'Sem simulação' : 'Do total pago, ' + Math.round(pj * 100) + '% é juros');
  }

  // Gráfico por blocos de 6 meses: barras (juros em cima, amortização embaixo) e linha do saldo devedor.
  function desenharGrafAmort(linhas, credito, parcelaAno, meses) {
    var g = $('amort-graf');
    limpar(g);
    var n = linhas.length, W = 640, Hh = 220, topo = 12, base = Hh - 4, util = base - topo;
    var slot = W / n, larg = Math.max(4, slot * 0.68);
    var pontos = ['0,' + (base - util).toFixed(1)];
    linhas.forEach(function (x, k) {
      var x0 = k * slot + (slot - larg) / 2;
      var hA = (x.amortizacao / parcelaAno) * util, hJ = (x.juros / parcelaAno) * util;
      g.appendChild(svgEl('rect', { 'class': 'g-a', x: x0.toFixed(1), y: (base - hA).toFixed(1), width: larg.toFixed(1), height: Math.max(0, hA).toFixed(1) }));
      g.appendChild(svgEl('rect', { 'class': 'g-j', x: x0.toFixed(1), y: (base - hA - hJ).toFixed(1), width: larg.toFixed(1), height: Math.max(0, hJ).toFixed(1) }));
      pontos.push(((k + 1) * slot).toFixed(1) + ',' + (base - (x.saldo / credito) * util).toFixed(1));
    });
    g.appendChild(svgEl('polyline', { 'class': 'g-s', points: pontos.join(' ') }));
    $('amort-fim').textContent = 'Mês ' + meses;
    g.setAttribute('aria-label', 'Gráfico: nos primeiros ' + Math.min(H.PERIODO_MESES, meses) + ' meses, ' + H.brl(linhas[0].juros) + ' de juros e ' + H.brl(linhas[0].amortizacao) + ' de amortização; no último bloco, ' +
      H.brl(linhas[n - 1].juros) + ' de juros e ' + H.brl(linhas[n - 1].amortizacao) + ' de amortização. O saldo devedor cai até zero.');
  }

  // Mesmo texto de conteudo.py: renda_texto. 30% é referência de mercado, não regra do parceiro.
  function textoRenda(parcela) {
    return 'A lei não fixa um percentual para o crédito com veículo em garantia: cada instituição decide na análise. Muita gente usa como régua uma parcela de até cerca de 30% da renda mensal. ' +
      'Nessa régua, ' + (sac() ? 'a primeira parcela estimada' : 'a parcela estimada') + ' de ' + H.brl(parcela) + ' exigiria uma renda mensal comprovada de cerca de ' +
      H.brl(H.rendaParaParcela(parcela)) + ' (conta nossa, não é análise de crédito).';
  }

  function desenharRaio(r, i, meses) {
    var c = estado.conforto;
    var txt;
    if (c > 0) {
      var dif = r.parcela - c;
      txt = dif > 0
        ? 'Com a estimativa de ' + H.brl(r.parcela) + ', este cenário fica ' + H.brl(dif) + ' acima do valor que você informou. Veja o que muda com a mesma taxa:'
        : 'Com a estimativa de ' + H.brl(r.parcela) + ', este cenário cabe no valor que você informou (' + H.brl(-dif) + ' abaixo). Veja o que muda com a mesma taxa:';
    } else {
      txt = 'Com a estimativa de ' + H.brl(r.parcela) + ', veja o que muda com a mesma taxa. Informe uma parcela confortável para comparar com o seu orçamento.';
    }
    $('raio-texto').textContent = txt;
    $('renda-texto').textContent = textoRenda(r.parcela);

    var alvo = $('alts');
    limpar(alvo);
    alvo.appendChild(cartaoAlt('Seu cenário', r.parcela, ['Receber ' + H.brl(rec()) + ' em ' + estado.meses + ' meses', 'Total: ' + H.brl(r.total)].concat(sufixoSis()), true));

    // receber menos (nunca abaixo do mínimo da ferramenta; se não dá para ir abaixo, mostra "receber mais"; se nem isso, só o outro prazo)
    var menos;
    var cabe = false;
    if (c > 0 && r.parcela > c) {
      menos = H.receberParaParcela(c, estado.saldo, meses, i, H.RECEBER_PASSO, estado.sistema);
      cabe = menos >= minReceber();
    }
    if (!cabe) menos = Math.floor((rec() * 0.8) / H.RECEBER_PASSO) * H.RECEBER_PASSO;
    if (menos >= rec()) menos = rec() - H.RECEBER_PASSO;
    if (menos >= minReceber()) {
      var r2 = H.simular(estado.veiculo, menos, estado.saldo, meses, i, estado.sistema);
      var nota = (c > 0 && r2.parcela <= c * 1.005) ? { cls: 'dn', texto: 'cabe na parcela que você informou' }
        : (c > 0 && r.parcela > c) ? { cls: 'dn', texto: 'fica mais perto do que você informou' } : { cls: 'dn', texto: 'parcela menor, mesmo prazo' };
      alvo.appendChild(cartaoAlt('Receber menos: ' + H.brl(menos), r2.parcela, ['Total: ' + H.brl(r2.total)].concat(sufixoSis()), false, nota));
    } else {
      var mais = Math.min(Math.floor(maxReceber() / H.RECEBER_PASSO) * H.RECEBER_PASSO, Math.ceil((rec() * 1.2) / H.RECEBER_PASSO) * H.RECEBER_PASSO);
      if (mais > rec()) {
        var r4 = H.simular(estado.veiculo, mais, estado.saldo, meses, i, estado.sistema);
        alvo.appendChild(cartaoAlt('Receber mais: ' + H.brl(mais), r4.parcela, ['Total: ' + H.brl(r4.total)].concat(sufixoSis()), false, { cls: 'up', texto: 'parcela maior, mesmo prazo' }));
      }
    }

    // prazo diferente
    var longo = estado.meses < H.PRAZO_MAX_MESES;
    var meses3 = longo ? H.PRAZO_MAX_MESES : 36;
    var r3 = H.simular(estado.veiculo, rec(), estado.saldo, meses3, i, estado.sistema);
    alvo.appendChild(cartaoAlt((longo ? 'Prazo maior: ' : 'Prazo menor: ') + meses3 + ' meses', r3.parcela, ['Total: ' + H.brl(r3.total)].concat(sufixoSis()), false,
      longo ? { cls: 'up', texto: 'parcela menor, mais juros no total' } : { cls: 'up', texto: 'parcela maior, menos juros no total' }));
    alvo.className = 'alts' + (alvo.children.length === 2 ? ' dois' : '');
  }

  function desenharNota(i, meses) {
    var mercado = H.ref.garantiaRealAm / 100;
    var r = H.simular(estado.veiculo, rec(), estado.saldo, meses, mercado, estado.sistema);
    $('nota-taxa-texto').textContent = 'A estimativa usa a taxa de referência do parceiro (' + H.pct(H.TAXA_PARCEIRO_AM) + ' a.m., média divulgada, parcela fixa e sem IPCA). A média do Banco Central para crédito com garantia real, que mistura imóvel e veículo, é ' +
      H.pct(H.ref.garantiaRealAm) + ' a.m. (' + H.ref.garantiaRealMes + '): nessa taxa, ' + (sac() ? 'a primeira parcela' : 'a parcela') + ' do cenário acima seria de ' + H.brl(r.parcela) + '. A taxa final vem da análise.';
  }

  function celula(tag, texto, escopo) {
    var c = el(tag, '', texto);
    if (escopo) c.setAttribute('scope', escopo);
    return c;
  }

  // Amortização por bloco de 6 meses (mesma conta de calculo.py: amortizacao_periodos). Texto igual ao de conteudo.py.
  function rotPeriodo(n, meses) {
    var ini = (n - 1) * H.PERIODO_MESES + 1, fim = Math.min(n * H.PERIODO_MESES, meses);
    return ini === fim ? String(ini) : ini + ' a ' + fim;
  }
  function desenharAmort(r, i, meses, semMargem) {
    var corpo = $('amort-corpo'), rodape = $('amort-rodape');
    limpar(corpo); limpar(rodape);
    if (semMargem) {
      $('amort-resumo').textContent = 'Ajuste o saldo ou o valor do veículo para ver a amortização.';
      $('amort-nota').textContent = '';
      $('amort-pct').textContent = '—';
      limpar($('amort-graf'));
      return;
    }
    var linhas = H.amortizacaoPeriodos(r.credito, i, meses, estado.sistema);
    var pago = linhas[0].juros + linhas[0].amortizacao; // total pago no 1º bloco (no SAC é o maior)
    var j1 = linhas[0].juros;
    var p1 = Math.min(H.PERIODO_MESES, meses);
    $('amort-pct').textContent = Math.round((j1 / pago) * 100) + '%';
    $('amort-pct-rot').textContent = 'dos primeiros ' + p1 + ' meses é juros';
    desenharGrafAmort(linhas, r.credito, pago, meses);
    $('amort-resumo').textContent = 'Nos primeiros ' + p1 + ' meses, ' + H.brl(j1) + ' dos ' + H.brl(pago) + ' que você paga são juros (' + Math.round((j1 / pago) * 100) +
      '%). ' +
      (sac() ? 'No SAC a amortização é a mesma todo mês: a parcela cai porque os juros caem.' : 'A parcela é fixa: com o tempo ela amortiza mais a dívida e os juros caem.');
    $('amort-cap').textContent = sac() ? 'Parcela que cai: juros, amortização e saldo devedor no fim de cada bloco de 6 meses' : 'Parcela fixa: juros, amortização e saldo devedor no fim de cada bloco de 6 meses';
    var juros = 0;
    linhas.forEach(function (x) {
      var tr = el('tr');
      tr.appendChild(celula('th', rotPeriodo(x.periodo, meses), 'row'));
      tr.appendChild(celula('td', H.brl(x.juros)));
      tr.appendChild(celula('td', H.brl(x.amortizacao)));
      tr.appendChild(celula('td', H.brl(x.saldo)));
      corpo.appendChild(tr);
      juros += x.juros;
    });
    var t = el('tr');
    t.appendChild(celula('th', 'Total', 'row'));
    t.appendChild(celula('td', H.brl(juros)));
    t.appendChild(celula('td', H.brl(r.credito)));
    t.appendChild(celula('td', ''));
    rodape.appendChild(t);
    $('amort-nota').textContent = 'A conta usa a taxa de ' + H.pct(i * 100) + ' ao mês, ' + (sac() ? 'com amortização constante (SAC)' : 'com parcela fixa') + ' e sem IPCA. Não inclui IOF, avaliação do veículo, registro do gravame nem seguros.';
  }

  // "Pagar a mais": quanto de juros some e quanto tempo se ganha (calculo.py: amortizar_antes). O valor único vale no começo do mês `quando` (0 = antes da 1ª parcela).
  function dur(m) {
    var a = Math.floor(m / 12), r = m % 12, p = [];
    if (a) p.push(a + (a === 1 ? ' ano' : ' anos'));
    if (r) p.push(r + (r === 1 ? ' mês' : ' meses'));
    return p.length ? p.join(' e ') : '0 mês';
  }
  function rotQuando(q) { return q === 0 ? 'no início, antes da 1ª parcela' : 'depois da ' + q + 'ª parcela'; }

  function cartaoAm(titulo, big, bigRot, linhas, melhor) {
    var d = el('div', 'amc' + (melhor ? ' best' : ''));
    if (melhor) d.appendChild(el('span', 'tg', 'Maior economia'));
    d.appendChild(el('h4', '', titulo));
    d.appendChild(el('div', 'big num', big));
    d.appendChild(el('div', 'bl', bigRot));
    var ul = el('ul');
    linhas.forEach(function (l) { ul.appendChild(el('li', '', l)); });
    d.appendChild(ul);
    return d;
  }

  function desenharAmortExtra(r, i, meses, semMargem) {
    var cartoes = $('am-cartoes'), texto = $('am-texto'), tempo = $('am-tempo'), ttxt = $('am-tempo-txt');
    limpar(cartoes); limpar(tempo);
    var maxQ = Math.max(0, estado.meses - 1);
    estado.quando = clamp(estado.quando, 0, maxQ);
    var rq = $('range-quando');
    rq.min = '0'; rq.max = String(maxQ);
    preencherRange(rq, estado.quando);
    $('quando-rot').textContent = rotQuando(estado.quando);
    $('am-taxa-aa').textContent = H.pct((Math.pow(1 + i, 12) - 1) * 100);
    $('am-tempo-fim').textContent = 'Depois da ' + maxQ + 'ª parcela';
    if (semMargem) { texto.textContent = 'Ajuste o saldo ou o valor do veículo para simular.'; ttxt.textContent = ''; return; }
    var s = estado.sistema, extra = Math.max(0, estado.extra), unico = Math.max(0, estado.unico), mq = estado.quando;
    if (!(extra > 0) && !(unico > 0)) { texto.textContent = 'Digite um valor mensal ou uma amortização única para ver a economia.'; ttxt.textContent = ''; return; }
    var base = H.amortizarAntes(r.credito, i, meses, s, 0, 0, mq, 'prazo');
    var lista = [];
    function adiciona(titulo, res, linhas) { lista.push({ titulo: titulo, poup: base.juros - res.juros, linhas: linhas }); }
    function tempoLinhas(res) {
      return ['Quita ' + dur(base.meses - res.meses) + ' antes', 'Termina em ' + dur(res.meses) + ', em vez de ' + dur(base.meses)];
    }
    var quando = estado.quando === 0 ? 'no início' : rotQuando(estado.quando);
    if (extra > 0) {
      var rE = H.amortizarAntes(r.credito, i, meses, s, extra, 0, 0, 'prazo');
      adiciona('Pagando ' + H.brl(extra) + ' a mais por mês', rE, tempoLinhas(rE));
    }
    if (unico > 0) {
      var rP = H.amortizarAntes(r.credito, i, meses, s, 0, unico, mq, 'prazo');
      var rC = H.amortizarAntes(r.credito, i, meses, s, 0, unico, mq, 'parcela');
      adiciona('Única de ' + H.brl(unico) + ' ' + quando + ', reduzindo o prazo', rP, rP.meses <= mq ? ['Quita a dívida inteira'] : tempoLinhas(rP));
      var linhasC = rC.meses <= mq ? ['Quita a dívida inteira'] : ['A parcela cai de ' + H.brl(base.parcelaNova) + ' para ' + H.brl(rC.parcelaNova), 'O prazo continua o mesmo'];
      adiciona('Única de ' + H.brl(unico) + ' ' + quando + ', reduzindo a parcela', rC, linhasC);
    }
    if (extra > 0 && unico > 0) {
      var rJ = H.amortizarAntes(r.credito, i, meses, s, extra, unico, mq, 'prazo');
      lista.unshift({ titulo: 'Os dois juntos, reduzindo o prazo', poup: base.juros - rJ.juros, linhas: rJ.meses <= mq ? ['Quita a dívida inteira'] : tempoLinhas(rJ) });
    }
    var melhor = 0;
    lista.forEach(function (c, k) { if (c.poup > lista[melhor].poup) melhor = k; });
    lista.forEach(function (c, k) { cartoes.appendChild(cartaoAm(c.titulo, H.brl(c.poup), 'a menos em juros', c.linhas, lista.length > 1 && k === melhor)); });
    texto.textContent = 'Valores em reais de hoje: não descontam o que esse dinheiro renderia em outra aplicação nem tarifas da instituição. Confirme no contrato como o abatimento é aplicado.';
    desenharTempo(r, i, meses, unico, maxQ);
  }

  // Barras: quanto o mesmo valor único economiza conforme o ano em que é pago (reduzindo o prazo).
  function desenharTempo(r, i, meses, unico, maxQ) {
    var g = $('am-tempo'), ttxt = $('am-tempo-txt');
    if (!(unico > 0) || maxQ < 1) { ttxt.textContent = unico > 0 ? '' : 'Informe uma amortização única para ver como o momento muda a economia.'; return; }
    var s = estado.sistema, n = maxQ + 1, W = 640, Hh = 150, topo = 8, base = Hh - 2, util = base - topo, slot = W / n, larg = Math.max(4, slot * 0.7);
    var juros0 = H.amortizarAntes(r.credito, i, meses, s, 0, 0, 0, 'prazo').juros, econ = [], max = 1;
    for (var q = 0; q <= maxQ; q++) {
      var v = juros0 - H.amortizarAntes(r.credito, i, meses, s, 0, unico, q, 'prazo').juros;
      econ.push(v);
      if (v > max) max = v;
    }
    econ.forEach(function (v, q) {
      var h = Math.max(1.5, (v / max) * util);
      g.appendChild(svgEl('rect', { x: (q * slot + (slot - larg) / 2).toFixed(1), y: (base - h).toFixed(1), width: larg.toFixed(1), height: h.toFixed(1), rx: 2,
        fill: q === estado.quando ? '#fde2a8' : '#f59e0b' }));
    });
    var meio = Math.round(maxQ / 2), pts = [0];
    if (meio > 0 && meio < maxQ) pts.push(meio);
    pts.push(maxQ);
    var partes = pts.map(function (q) { return H.brl(econ[q]) + (q === 0 ? ' logo no início' : ' ' + rotQuando(q)); });
    var ult = partes.pop();
    ttxt.textContent = 'Com ' + H.brl(unico) + ' pagos de uma vez, você poupa ' + partes.join(', ') + ' e ' + ult + '. A barra clara é o momento que você escolheu.';
    g.setAttribute('aria-label', 'Gráfico: a economia vai de ' + H.brl(econ[0]) + ' no início até ' + H.brl(econ[maxQ]) + ' depois da ' + maxQ + 'ª parcela.');
  }

  // "Quitar dívida cara": a mesma dívida e o mesmo prazo na taxa média da dívida e no Auto Equity (conteudo.py: quitar_cartoes/quitar_texto).
  function taxaDivida() { return estado.tipoDiv === 'outra' ? estado.taxaDiv : H.ref[estado.tipoDiv + 'Am']; }

  // Barras lado a lado: parcela por mês e total pago, dívida atual x Auto Equity.
  function grupoBarras(titulo, valA, valB, nomeA, corA) {
    var g = el('div', 'qg');
    g.appendChild(el('h4', '', titulo));
    var max = Math.max(valA, valB, 1);
    [[nomeA, valA, corA || COR.pessoal], ['Auto Equity', valB, COR.ae]].forEach(function (b) {
      var linha = el('div', 'r');
      linha.appendChild(el('span', '', b[0]));
      var s = svgEl('svg', { width: '100%', height: 12, role: 'img', 'aria-label': titulo + ', ' + b[0] + ': ' + H.brl(b[1]) });
      s.appendChild(svgEl('rect', { width: '100%', height: 12, rx: 6, fill: 'rgba(255,255,255,.07)' }));
      s.appendChild(svgEl('rect', { width: Math.max(1.5, (b[1] / max) * 100).toFixed(1) + '%', height: 12, rx: 6, fill: b[2] }));
      linha.appendChild(s);
      linha.appendChild(el('span', 'vv num', H.brl(b[1])));
      g.appendChild(linha);
    });
    return g;
  }

  function desenharGrafQuitar(c, nomeA, corA) {
    var alvo = $('q-grafico');
    limpar(alvo);
    alvo.appendChild(grupoBarras(sac() ? 'Parcela por mês (1ª no SAC)' : 'Parcela por mês', c.parcelaAtual, c.parcelaAe, nomeA, corA));
    alvo.appendChild(grupoBarras('Total pago em ' + estado.meses + ' meses', c.totalAtual, c.totalAe, nomeA, corA));
  }

  function desenharQuitar(i, meses, rmax) {
    var outra = estado.tipoDiv === 'outra';
    var t = taxaDivida();
    var d = estado.divida;
    var aviso = $('q-aviso'), cartoes = $('q-cartoes'), texto = $('q-texto'), usar = $('btn-usar-divida');
    $('bloco-taxa-div').hidden = !outra;
    var erro = '';
    if (!(d > 0)) erro = 'Informe quanto você deve.';
    else if (outra && !(t >= 0.1 && t <= 30)) erro = 'Informe uma taxa entre 0,1% e 30% ao mês.';
    else if (rmax < 1) erro = 'O saldo devedor do veículo já usa o limite: não sobra valor para quitar outra dívida.';
    if (erro) {
      aviso.hidden = false; aviso.textContent = erro;
      limpar(cartoes); limpar($('q-grafico')); texto.textContent = ''; usar.disabled = true;
      return;
    }
    usar.disabled = false;
    var uso = Math.min(d, rmax);
    var msg = '';
    if (d > rmax) msg = 'O limite do veículo cobre até ' + H.brl(rmax) + ': calculamos com esse valor.';
    else if (d < H.RECEBER_MIN) msg = 'O crédito mínimo desta ferramenta é ' + H.brl(H.RECEBER_MIN) + ' (limite da tela; o parceiro não divulga o dele): abaixo disso a troca pode não estar disponível.';
    aviso.hidden = !msg; aviso.textContent = msg;
    var c = H.compararQuitacao(uso, t / 100, meses, i, estado.sistema);
    limpar(cartoes);
    cartoes.appendChild(cartaoAlt((outra ? 'Na taxa da sua dívida (' : 'Na taxa média (') + H.pct(t) + ' a.m.)', c.parcelaAtual,
      ['Só de juros: ' + H.brl(c.jurosMes1) + ' no 1º mês', 'Total em ' + estado.meses + ' meses: ' + H.brl(c.totalAtual)], false));
    var dest = c.economiaMes > 0 ? { cls: 'dn', texto: H.brl(c.economiaMes) + ' a menos por mês' } : { cls: 'up', texto: 'sem redução de parcela nesta conta' };
    cartoes.appendChild(cartaoAlt('No Auto Equity (' + H.pct(i * 100) + ' a.m.)', c.parcelaAe, ['Total em ' + estado.meses + ' meses: ' + H.brl(c.totalAe)].concat(sufixoSis()), true, dest));
    desenharGrafQuitar(c, outra ? 'Sua dívida' : 'Dívida (média)', COR[estado.tipoDiv] || COR.pessoal);
    texto.textContent = c.economiaMes > 0
      ? 'Trocar esta dívida reduziria ' + (sac() ? 'a primeira parcela' : 'a parcela') + ' em ' + H.brl(c.economiaMes) + ' por mês e o total pago em cerca de ' + H.brl(c.economiaTotal) + ', com a mesma duração (' + estado.meses +
        ' meses). Avaliação, gravame e seguros ficam fora desta conta e encolhem a economia.'
      : 'Com esta taxa, o Auto Equity não reduz a parcela da dívida. Peça o CET da proposta e compare antes de decidir.';
  }

  // "O mesmo crédito em outras modalidades": o Auto Equity (no sistema escolhido) contra médias de mercado (parcela fixa), com o mesmo crédito e prazo.
  // Cada linha é uma barra do total pago: a parte clara é o crédito que você recebe e a parte colorida são os juros.
  var MODALIDADES = [
    { k: 'ae', nome: 'Auto Equity' },
    { k: 'gar', nome: 'Garantia real (média)', taxa: function () { return H.ref.garantiaRealAm; } },
    { k: 'pessoal', nome: 'Crédito pessoal', taxa: function () { return H.ref.pessoalAm; } },
    { k: 'cheque', nome: 'Cheque especial', taxa: function () { return H.ref.chequeAm; } }
  ];

  function linhaModalidade(x, max, credito) {
    var l = el('div', 'mrow' + (x.k === 'ae' ? ' us' : ''));
    var nome = el('div', 'mn');
    if (x.k === 'ae') nome.appendChild(el('span', 'tg', 'Seu cenário'));
    nome.appendChild(el('b', '', x.nome));
    nome.appendChild(el('span', 'chip', H.pct(x.taxa * 100) + ' a.m.'));
    l.appendChild(nome);
    var barra = el('div', 'mb');
    var s = svgEl('svg', { width: '100%', height: 16, role: 'img',
      'aria-label': x.nome + ': você recebe ' + H.brl(credito) + ' e paga ' + H.brl(x.v - credito) + ' de juros, ' + H.brl(x.v) + ' no total' });
    s.appendChild(svgEl('rect', { width: '100%', height: 16, rx: 8, fill: 'rgba(255,255,255,.06)' }));
    s.appendChild(svgEl('rect', { width: Math.max(2, (x.v / max) * 100).toFixed(1) + '%', height: 16, rx: 8, fill: COR[x.k] }));
    s.appendChild(svgEl('rect', { width: Math.max(1.5, (credito / max) * 100).toFixed(1) + '%', height: 16, rx: 8, fill: '#e2e8f0' }));
    barra.appendChild(s);
    l.appendChild(barra);
    var val = el('div', 'mv');
    val.appendChild(el('b', 'num', H.brl(x.v)));
    val.appendChild(el('small', 'num', H.brl(x.parcela) + ' /mês' + (x.k === 'ae' && sac() ? ' (1ª)' : '')));
    l.appendChild(val);
    return l;
  }

  function desenharComparativo(r, i, meses, semMargem) {
    var alvo = $('cm-linhas');
    limpar(alvo);
    $('cm-lead').textContent = 'Com o mesmo crédito de ' + H.brl(r.credito) + ' e o mesmo prazo de ' + estado.meses + ' meses, veja quanto você pagaria em cada modalidade. ' +
      'As outras taxas são médias de mercado do Banco Central.';
    if (semMargem) { $('cm-gap-v').textContent = '—'; $('cm-gap').textContent = ''; return; }
    var itens = MODALIDADES.map(function (m) {
      var taxaM = m.k === 'ae' ? i : m.taxa() / 100;
      var pl = H.plano(r.credito, taxaM, meses, m.k === 'ae' ? estado.sistema : 'price');
      return { k: m.k, nome: m.nome, taxa: taxaM, parcela: pl[0], v: pl[2] };
    });
    var max = 1;
    itens.forEach(function (x) { if (x.v > max) max = x.v; });
    itens.forEach(function (x) { alvo.appendChild(linhaModalidade(x, max, r.credito)); });
    var pa = H.pmt(r.credito, H.ref.pessoalAm / 100, meses);
    $('cm-gap-v').textContent = H.brl(pa * meses - r.total);
    $('cm-gap').textContent = 'a mais no crédito pessoal sem garantia (média de ' + H.pct(H.ref.pessoalAm) + ' a.m.): ' + H.brl(pa) + ' por mês, ' + H.brl(pa * meses) + ' no total.';
  }

  // Endereço compartilhável: só números. O canonical da página continua sendo a home.
  function lerEndereco() {
    try {
      var q = new URLSearchParams(window.location.search);
      var so = /^[\d.,]+$/;
      function num(nome) { var t = q.get(nome) || ''; return so.test(t) ? lerNumero(t) : 0; }
      if (num('veiculo') > 0) estado.veiculo = num('veiculo');
      if (num('saldo') > 0) { estado.saldo = num('saldo'); estado.financiado = true; }
      if (num('receber') > 0) estado.receber = num('receber');
      var a = Math.round(num('prazo'));
      if (a >= H.PRAZO_MIN_MESES && a <= H.PRAZO_MAX_MESES) estado.meses = a;
      if (q.get('conforto') !== null) estado.conforto = num('conforto');
      if (q.get('sistema') === 'sac') estado.sistema = 'sac';
      var tp = num('taxa');
      if (tp >= H.TAXA_PROPRIA_MIN && tp <= H.TAXA_PROPRIA_MAX) estado.taxaProp = tp;
    } catch (e) { /* endereço estranho: usa os valores padrão */ }
  }

  // O link compartilhado leva o '#simulador' (abre já no simulador); a barra de endereços fica sem ele,
  // senão o Safari volta para o topo do simulador, e não para onde a pessoa estava, ao voltar de uma página interna.
  function enderecoDaSimulacao(comAncora) {
    var q = new URLSearchParams();
    q.set('veiculo', String(Math.round(estado.veiculo)));
    if (estado.financiado && estado.saldo > 0) q.set('saldo', String(Math.round(estado.saldo)));
    q.set('receber', String(Math.round(rec())));
    q.set('prazo', String(estado.meses));
    if (estado.conforto > 0) q.set('conforto', String(Math.round(estado.conforto)));
    if (sac()) q.set('sistema', 'sac');
    if (taxaPropria()) q.set('taxa', String(estado.taxaProp).replace('.', ','));
    return window.location.origin + window.location.pathname + '?' + q.toString() + (comAncora ? '#simulador' : '');
  }

  // Guarda os números da última simulação só nesta aba (sessionStorage, sem cookie): o botão "Voltar à simulação" das páginas internas usa.
  function guardarSimulacao(url) {
    try { window.sessionStorage.setItem('ae-sim', '?' + url.split('?')[1]); } catch (e) { /* sem armazenamento: o botão leva ao simulador */ }
  }

  function atualizarEndereco() {
    clearTimeout(timerUrl);
    timerUrl = setTimeout(function () {
      var url = enderecoDaSimulacao(false);
      guardarSimulacao(url);
      try { window.history.replaceState(null, '', url); } catch (e) { /* sem histórico: o botão de copiar continua valendo */ }
    }, 400);
  }

  async function copiarLink() {
    var url = enderecoDaSimulacao(true);
    var ok = false;
    try { window.history.replaceState(null, '', enderecoDaSimulacao(false)); } catch (e) { /* ignora */ }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(url); ok = true; }
    } catch (e) { /* tenta o plano B abaixo */ }
    if (!ok) {
      try {
        var t = document.createElement('textarea');
        t.value = url; t.setAttribute('readonly', ''); t.className = 'sr';
        document.body.appendChild(t); t.select();
        ok = document.execCommand('copy');
        document.body.removeChild(t);
      } catch (e) { ok = false; }
    }
    var msg = $('msg-copiado');
    msg.textContent = ok ? 'Link copiado. Quem abrir vê esta mesma simulação.' : 'Não deu para copiar sozinho. O link já está na barra de endereço do navegador.';
    clearTimeout(timerCopiado);
    timerCopiado = setTimeout(function () { msg.textContent = ''; }, 4000);
    evento('copiou-link', { receber: rec(), prazo: estado.meses });
  }

  function desenhar(foco) {
    var ajustou = ajustar();
    var meses = estado.meses;
    var i = taxa();
    var rmax = maxReceber();
    var semMargem = rmax < 1;
    var r = H.simular(estado.veiculo, semMargem ? 0 : rec(), estado.saldo, meses, i, estado.sistema);

    $('bloco-saldo').hidden = !estado.financiado;
    $('sit-quitado').checked = !estado.financiado;
    $('sit-financiado').checked = estado.financiado;
    if (foco !== 'veiculo') $('campo-veiculo').value = BRL_NUM.format(estado.veiculo);
    if (foco !== 'saldo') $('campo-saldo').value = BRL_NUM.format(estado.saldo);
    if (foco !== 'receber') $('campo-receber').value = BRL_NUM.format(rec());
    if (foco !== 'conforto') $('campo-conforto').value = estado.conforto > 0 ? BRL_NUM.format(estado.conforto) : '';
    if (foco !== 'prazo') $('campo-prazo').value = String(estado.meses);
    var rp = $('range-prazo');
    rp.min = String(H.PRAZO_MIN_MESES); rp.max = String(H.PRAZO_MAX_MESES);
    preencherRange(rp, estado.meses);
    $('div-' + estado.tipoDiv).checked = true;
    $('sis-' + estado.sistema).checked = true;
    $('hint-sistema').textContent = sac() ? 'Cai todo mês e paga menos juros. O parceiro confirma na proposta se oferece.' : 'Parcela igual todo mês.';
    if (foco !== 'extra') $('campo-extra').value = estado.extra > 0 ? BRL_NUM.format(estado.extra) : '';
    if (foco !== 'unico') $('campo-unico').value = estado.unico > 0 ? BRL_NUM.format(estado.unico) : '';
    if (foco !== 'divida') $('campo-divida').value = BRL_NUM.format(estado.divida);
    if (foco !== 'taxadiv') $('campo-taxa-div').value = String(estado.taxaDiv).replace('.', ',');
    preencherRange($('range-veiculo'), estado.veiculo);
    var rr = $('range-receber');
    rr.min = String(minReceber()); rr.max = String(Math.max(minReceber(), Math.floor(rmax / H.RECEBER_PASSO) * H.RECEBER_PASSO));
    preencherRange(rr, rec());
    $('min-receber').textContent = mil(Number(rr.min));
    $('max-receber').textContent = mil(Number(rr.max));
    var aviso = $('msg-ajuste');
    if (semMargem) { aviso.hidden = false; aviso.textContent = 'O saldo devedor já usa o limite do veículo: não sobra valor para receber.'; }
    else if (ajustou && foco !== 'receber' && estado.receber < minReceber()) { aviso.hidden = false; aviso.textContent = 'Ajustamos o valor para o mínimo de ' + H.brl(minReceber()) + '.'; }
    else if (ajustou && foco !== 'receber') { aviso.hidden = false; aviso.textContent = 'Ajustamos o valor para o limite de ' + H.brl(rmax) + (limiteTeto() ? ' (teto de ' + H.brl(H.CREDITO_MAX) + ' de crédito' + (estado.saldo > 0 ? ', menos o saldo' : '') + ').' : ' (' + Math.round(H.LTV_MAX * 100) + '% do veículo' + (estado.saldo > 0 ? ' menos o saldo' : '') + ').'); }
    else if (!ajustou) aviso.hidden = true;

    $('r-kicker').textContent = sac() ? '1ª parcela estimada' : 'Parcela estimada';
    var ult = $('r-ultima');
    ult.hidden = !(sac() && !semMargem);
    if (!ult.hidden) ult.textContent = 'A parcela cai todo mês, até ' + H.brl(r.parcelaFinal) + ' na última.';
    $('r-parcela').textContent = semMargem ? '—' : H.brl(r.parcela);
    $('r-sub').textContent = 'em ' + meses + ' meses · taxa ' + H.pct(i * 100) + ' a.m.' + (taxaPropria() ? ' (sua proposta)' : '');
    desenharFaixa(r, i, meses, semMargem);
    if (foco !== 'taxaprop') $('campo-taxa-prop').value = estado.taxaProp > 0 ? String(estado.taxaProp).replace('.', ',') : '';
    if (estado.taxaProp > 0 && !taxaPropria()) { $('msg-taxa-prop').textContent = 'Use uma taxa entre ' + H.pct(H.TAXA_PROPRIA_MIN) + ' e ' + H.pct(H.TAXA_PROPRIA_MAX) + ' ao mês. Enquanto isso, a conta usa a taxa de referência.'; $('msg-taxa-prop').className = 'hint warn'; }
    else { $('msg-taxa-prop').textContent = taxaPropria() ? 'Conta com a taxa da sua proposta, como está: parcela fixa, sem IPCA.' : 'Deixe em branco para usar a taxa de referência. Digite a taxa mensal da proposta, como está.'; $('msg-taxa-prop').className = 'hint'; }

    $('r-total').textContent = semMargem ? '—' : H.brl(r.total);
    $('r-resumo').textContent = semMargem ? 'Ajuste o valor do veículo ou o saldo para ver o custo.' : 'Você recebe ' + H.brl(r.credito) + ' e devolve ' + H.brl(r.total) + ' ao fim do contrato; os juros somam ' + H.brl(r.juros) + '.';
    $('c-veiculo').textContent = H.brl(estado.veiculo);
    var usoPct = Math.min(100, r.ltv * 100);
    $('bar-fill').setAttribute('width', usoPct.toFixed(1) + '%');
    $('c-ltv-rot').textContent = estado.financiado ? 'quita o saldo + você recebe' : 'você recebe';
    $('c-credito').textContent = H.brl(r.credito) + ' · ' + Math.round(r.ltv * 100) + '%';
    $('c-limite').textContent = H.brl(r.limite);
    $('c-limite-rot').textContent = limiteTeto() ? 'Limite (teto de crédito)' : 'Limite (' + Math.round(H.LTV_MAX * 100) + '%)';
    $('bar-mark').setAttribute('x', Math.min(99, (r.limite / estado.veiculo) * 100).toFixed(1) + '%');
    $('btn-cta').disabled = semMargem;
    desenharRosca(r, semMargem);

    if (!semMargem) { desenharRaio(r, i, meses); } else { limpar($('alts')); $('raio-texto').textContent = 'Ajuste o saldo ou o valor do veículo para ver as comparações.'; }
    desenharNota(i, meses);
    desenharAmort(r, i, meses, semMargem);
    desenharAmortExtra(r, i, meses, semMargem);
    desenharComparativo(r, i, meses, semMargem);
    desenharQuitar(i, meses, rmax);
    desenhos += 1;
    if (desenhos > 1) atualizarEndereco();
  }

  function interagiu() {
    if (usou) return;
    usou = true;
    evento('usou-simulador-autoequity', { receber: rec(), prazo: estado.meses });
  }

  function mexeuQuitar() {
    if (usouQuitar) return;
    usouQuitar = true;
    evento('usou-quitar-divida', { tipo: estado.tipoDiv });
  }

  var MESES_CURTOS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  // Faixa com três números: quando quita, quanto cada R$ 1 de crédito custa de juros e a taxa ao ano.
  function desenharFaixa(r, i, meses, semMargem) {
    $('k-aa').textContent = H.pct((Math.pow(1 + i, 12) - 1) * 100);
    $('k-nota').textContent = 'Taxa média divulgada pelo parceiro, conferida em 18/11/2026; médias do Banco Central de ' + H.ref.garantiaRealMes + '. Estimativa, não é oferta.';
    if (semMargem) { $('k-quita').textContent = '—'; $('k-quita-s').textContent = ''; $('k-juro1').textContent = '—'; return; }
    var d = new Date();
    d.setMonth(d.getMonth() + meses + 2);
    $('k-quita').textContent = MESES_CURTOS[d.getMonth()] + '/' + d.getFullYear();
    $('k-quita-s').textContent = meses + ' parcelas, se contratar este mês';
    $('k-juro1').textContent = 'R$ ' + (r.juros / r.credito).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function mexeuTaxaProp() {
    if (usouTaxaProp) return;
    usouTaxaProp = true;
    evento('usou-taxa-propria', { prazo: estado.meses });
  }

  function mexeuAmort() {
    if (usouAmortExtra) return;
    usouAmortExtra = true;
    evento('simulou-amortizacao', { prazo: estado.meses });
  }

  function ligarCampo(id, chave, minimo, foco, aoMexer) {
    var c = $(id);
    var mexeu = aoMexer || interagiu;
    c.addEventListener('input', function (e) {
      var v = lerNumero(e.target.value);
      if (v >= minimo) { estado[chave] = v; mexeu(); desenhar(foco); }
    });
    c.addEventListener('blur', function (e) {
      estado[chave] = lerNumero(e.target.value);
      if (chave === 'conforto' && e.target.value.trim() === '') estado.conforto = 0;
      mexeu();
      desenhar();
    });
    c.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.target.blur(); });
  }

  // Prazo: lista suspensa com todos os meses (de PRAZO_MIN_MESES a PRAZO_MAX_MESES) e também campo digitável e controle deslizante.
  function ligarPrazo() {
    var c = $('campo-prazo'), msg = $('msg-prazo'), lista = $('lista-prazo'), caixa = $('combo-prazo'), btn = $('btn-prazo');
    var min = H.PRAZO_MIN_MESES, max = H.PRAZO_MAX_MESES, ativo = 0;
    for (var a = min; a <= max; a++) {
      var li = el('li');
      li.id = 'prazo-op-' + a;
      li.setAttribute('role', 'option');
      li.setAttribute('data-v', String(a));
      li.appendChild(el('span', '', a + ' meses'));
      if (a >= 12 && a % 6 === 0) li.appendChild(el('small', '', dur(a)));
      lista.appendChild(li);
    }
    function aberta() { return !lista.hidden; }
    function marcar(v) {
      ativo = v;
      Array.prototype.forEach.call(lista.children, function (li) {
        var v2 = Number(li.getAttribute('data-v'));
        li.setAttribute('aria-selected', v2 === estado.meses ? 'true' : 'false');
        li.className = v2 === v ? 'ativo' : '';
      });
      var cur = $('prazo-op-' + v);
      if (cur) {
        c.setAttribute('aria-activedescendant', cur.id);
        if (cur.offsetTop < lista.scrollTop) lista.scrollTop = cur.offsetTop;
        else if (cur.offsetTop + cur.offsetHeight > lista.scrollTop + lista.clientHeight) lista.scrollTop = cur.offsetTop + cur.offsetHeight - lista.clientHeight;
      }
    }
    function abrir() {
      lista.hidden = false;
      c.setAttribute('aria-expanded', 'true');
      caixa.className = 'inp combo aberto';
      marcar(estado.meses);
      var cur = $('prazo-op-' + estado.meses);
      if (cur) lista.scrollTop = Math.max(0, cur.offsetTop - lista.clientHeight / 2 + cur.offsetHeight / 2);
    }
    function fechar() {
      lista.hidden = true;
      c.setAttribute('aria-expanded', 'false');
      c.removeAttribute('aria-activedescendant');
      caixa.className = 'inp combo';
    }
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && aberta()) { fechar(); } });
    function escolher(v) { estado.meses = v; msg.hidden = true; interagiu(); fechar(); desenhar(); }

    c.addEventListener('input', function (e) {
      var v = Math.round(lerNumero(e.target.value));
      if (aberta()) fechar();
      if (v >= min && v <= max) { estado.meses = v; msg.hidden = true; interagiu(); desenhar('prazo'); }
    });
    c.addEventListener('blur', function (e) {
      var v = Math.round(lerNumero(e.target.value));
      if (v >= min && v <= max) msg.hidden = true;
      else {
        v = clamp(v > 0 ? v : estado.meses, min, max);
        msg.hidden = false; msg.textContent = 'O prazo vai de ' + min + ' a ' + max + ' meses. Ajustamos para ' + v + ' meses.';
      }
      estado.meses = v; interagiu(); desenhar();
    });
    c.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!aberta()) { abrir(); return; }
        marcar(clamp(ativo + (e.key === 'ArrowDown' ? 1 : -1), min, max));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (aberta()) escolher(ativo); else e.target.blur();
      } else if (e.key === 'Escape') { if (aberta()) { e.preventDefault(); fechar(); } }
      else if (e.key === 'Tab') fechar();
    });
    btn.addEventListener('mousedown', function (e) { e.preventDefault(); }); // não tira o foco do campo
    btn.addEventListener('click', function () { if (aberta()) fechar(); else abrir(); });
    lista.addEventListener('mousedown', function (e) { e.preventDefault(); });
    lista.addEventListener('click', function (e) {
      var li = e.target.closest ? e.target.closest('li') : null;
      if (li) escolher(Number(li.getAttribute('data-v')));
    });
    document.addEventListener('click', function (e) { if (aberta() && !caixa.contains(e.target)) fechar(); });
    $('range-prazo').addEventListener('input', function (e) { estado.meses = Number(e.target.value); msg.hidden = true; interagiu(); desenhar(); });
  }

  function iniciar() {
    lerEndereco();
    $('sit-quitado').addEventListener('change', function () { estado.financiado = false; estado.saldo = 0; interagiu(); desenhar(); });
    $('sit-financiado').addEventListener('change', function () {
      estado.financiado = true;
      if (estado.saldo === 0) estado.saldo = Math.round(estado.veiculo * 0.2 / 1000) * 1000;
      interagiu(); desenhar();
    });
    if (taxaPropria()) $('det-taxa').open = true;
    ligarCampo('campo-veiculo', 'veiculo', H.VEICULO_MIN, 'veiculo');
    ligarCampo('campo-saldo', 'saldo', 1, 'saldo');
    ligarCampo('campo-receber', 'receber', 1000, 'receber');
    ligarCampo('campo-conforto', 'conforto', 1, 'conforto');
    $('range-veiculo').addEventListener('input', function (e) { estado.veiculo = Number(e.target.value); interagiu(); desenhar(); });
    $('range-receber').addEventListener('input', function (e) { estado.receber = Number(e.target.value); interagiu(); desenhar(); });
    ligarPrazo();
    $('btn-copiar').addEventListener('click', copiarLink);
    Array.prototype.forEach.call(document.querySelectorAll('input[name="sistema"]'), function (rd) {
      rd.addEventListener('change', function (e) { estado.sistema = e.target.value; interagiu(); desenhar(); });
    });

    $('campo-taxa-prop').addEventListener('input', function (e) { estado.taxaProp = lerNumero(e.target.value); mexeuTaxaProp(); desenhar('taxaprop'); });
    $('campo-taxa-prop').addEventListener('blur', function () { desenhar(); });
    $('campo-taxa-prop').addEventListener('keydown', function (e) { if (e.key === 'Enter') e.target.blur(); });
    ligarCampo('campo-extra', 'extra', 1, 'extra', mexeuAmort);
    ligarCampo('campo-unico', 'unico', 1, 'unico', mexeuAmort);
    $('range-quando').addEventListener('input', function (e) { estado.quando = Number(e.target.value); mexeuAmort(); desenhar(); });
    ligarCampo('campo-divida', 'divida', 1, 'divida', mexeuQuitar);
    ligarCampo('campo-taxa-div', 'taxaDiv', 0.01, 'taxadiv', mexeuQuitar);
    Array.prototype.forEach.call(document.querySelectorAll('input[name="tipodiv"]'), function (rd) {
      rd.addEventListener('change', function (e) { estado.tipoDiv = e.target.value; mexeuQuitar(); desenhar(); });
    });
    $('btn-usar-divida').addEventListener('click', function () {
      estado.receber = Math.min(estado.divida, maxReceber());
      interagiu(); desenhar();
      var alvo = $('simulador');
      if (alvo && alvo.scrollIntoView) alvo.scrollIntoView();
    });
    $('det-amort').addEventListener('toggle', function (e) {
      if (e.target.open && !abriuAmort) { abriuAmort = true; evento('abriu-amortizacao', { prazo: estado.meses }); }
    });
    $('det-amsim').addEventListener('toggle', function (e) {
      if (e.target.open && !abriuAmort) { abriuAmort = true; evento('abriu-amortizacao', { prazo: estado.meses }); }
    });

    var dlg = $('dlg-confirma');
    function fechar() { if (typeof dlg.close === 'function') dlg.close(); else { dlg.removeAttribute('open'); devolverFoco(); } }
    // Safari não dá foco ao botão no toque: devolvemos o foco para onde a pessoa estava ao fechar a tela.
    function devolverFoco() { try { $('btn-cta').focus({ preventScroll: true }); } catch (e) { /* ignora */ } }
    $('btn-cta').addEventListener('click', function () {
      evento('abriu-confirmacao', { receber: rec(), prazo: estado.meses });
      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
    });
    dlg.addEventListener('close', devolverFoco);
    $('btn-voltar').addEventListener('click', fechar);
    // Só o clique fora da caixa fecha (o preenchimento interno do diálogo também é o próprio elemento: conferimos pelas coordenadas).
    dlg.addEventListener('click', function (e) {
      if (e.target !== dlg) return;
      var r = dlg.getBoundingClientRect();
      var fora = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      if (fora) fechar();
    });
    $('a-parceiro').addEventListener('click', function () { evento('cta-parceiro', { receber: rec(), prazo: estado.meses }); });
    desenhar();
    guardarSimulacao(enderecoDaSimulacao(false));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
