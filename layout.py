"""HTML do layout (cabeçalho, rodapé), da home e dos blocos dos guias. Os marcadores @@NOME@@ são trocados pelo gerador.

Sem atributo style nem script inline (a CSP não permite). Os desenhos de barras são SVG com atributos; a lógica fica em src/simulador.js.
"""

LOGO = """<span class="tile"><svg viewBox="0 0 44 44" width="32" height="32" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="22" cy="29" rx="19" ry="6.2" transform="rotate(-22 22 29)" stroke-width="1.3" opacity=".6"/><path d="M17.5 11.5h9M18.8 11.5V22L9.7 37.6a2.3 2.3 0 0 0 2 3.4h20.6a2.3 2.3 0 0 0 2-3.4L25.2 22V11.5" stroke-width="2"/><g fill="currentColor" stroke="none"><rect x="16" y="34" width="2.2" height="4.6" rx=".6"/><rect x="19.6" y="31" width="2.2" height="7.6" rx=".6"/><rect x="23.2" y="33" width="2.2" height="5.6" rx=".6"/><rect x="26.8" y="29.5" width="2.2" height="9.1" rx=".6"/><rect x="19.4" y="6.6" width="1.7" height="3.4" rx=".5"/><rect x="22.4" y="5" width="1.7" height="5" rx=".5"/><rect x="25.4" y="3.6" width="1.7" height="6.4" rx=".5"/><circle cx="31" cy="9.5" r="1.3"/><circle cx="35.5" cy="5.6" r="1.3"/></g><path d="M31 9.5l4.5-3.9" stroke-width="1.3"/></svg></span>"""

LAYOUT = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<meta name="robots" content="@@ROBOTS@@">
<link rel="canonical" href="@@CANONICAL@@">
<link rel="icon" href="/favicon.ico?v=@@ICONV@@" sizes="any">
<link rel="icon" href="/favicon-32.png?v=@@ICONV@@" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=@@ICONV@@">
<meta property="og:type" content="@@OGTYPE@@">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Datalab Global">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:url" content="@@CANONICAL@@">
<meta property="og:image" content="@@DOMINIO@@/og-image.png?v=@@OGV@@">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="@@TITLE@@">
<meta name="twitter:description" content="@@DESC@@">
<meta name="twitter:image" content="@@DOMINIO@@/og-image.png?v=@@OGV@@">
<meta name="theme-color" content="#020617">
<link rel="preload" href="/fonts/playfair-display-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/styles.css?v=@@CSSV@@">
<link rel="alternate" type="application/atom+xml" title="Auto Equity — Datalab Global" href="/feed.xml">
@@JSONLD@@@@UMAMI@@</head>
<body>
<a href="#conteudo" class="skip">Ir para o conteúdo</a>
<header class="top">
  <div class="wrap">
    <span class="bk"><a href="https://www.datalabglobal.com/" class="brand" aria-label="Datalab Global, site principal">@@LOGO@@<span class="wm"><b>Datalab</b><i>GLOBAL</i></span></a><a href="/" class="prod" aria-label="Auto Equity, página inicial do simulador">Auto Equity</a></span>
    <nav class="m" aria-label="Principal">@@NAV@@</nav>
    <div class="free"><span class="dot"></span>Simulação gratuita</div>
    <details class="menu">
      <summary>Menu</summary>
      <nav aria-label="Menu">@@NAVMOBILE@@</nav>
    </details>
  </div>
</header>

<main id="conteudo" class="wrap">
@@MAIN@@
</main>

<footer class="rod">
  <div class="wrap">
    <div class="cols">
      <div>
        <a href="https://www.datalabglobal.com/" class="brand" aria-label="Datalab Global, site principal">@@LOGO@@<span class="wm"><b>Datalab</b><i>GLOBAL</i></span></a>
        <p>Simulador de Auto Equity: veja parcela e custo total do crédito com veículo em garantia, antes de qualquer pedido.</p>
      </div>
      <nav aria-label="Entenda"><h2>Entenda</h2><ul>@@FOOT_ENTENDA@@</ul></nav>
      <nav aria-label="Transparência"><h2>Transparência</h2><ul>@@FOOT_TRANSP@@</ul></nav>
      <nav aria-label="Legal"><h2>Legal</h2><ul>@@FOOT_LEGAL@@</ul></nav>
      <nav aria-label="Outros simuladores da Datalab Global"><h2>Outros simuladores</h2><ul>@@FOOT_OUTROS@@</ul></nav>
    </div>
    <div class="base">
      <p>Atualizado em @@ATUALIZADO@@. Taxas de referência: Banco Central e parceiro de crédito.</p>
      <p>Datalab Global é marca de @@RAZAO@@, CNPJ @@CNPJ@@. Contato: <a href="mailto:@@EMAIL@@">@@EMAIL@@</a>.</p>
      <p>A simulação é uma estimativa, não é proposta de crédito. O crédito depende de análise e aprovação, sem garantia de aprovação.</p>
    </div>
  </div>
</footer>
@@SCRIPTS@@</body>
</html>
"""

HOME_MAIN = """  <section class="hero">
    <h1>Quanto o seu veículo pode <em>liberar?</em></h1>
    <p>Simule a parcela e o custo total do Auto Equity em segundos.</p>
    <div class="fine">Grátis · sem cadastro · estimativa, não proposta</div>
  </section>

  <div class="grid" id="simulador">
    <section class="panel" aria-labelledby="t-cenario">
      <h2 id="t-cenario">Seu cenário</h2>
      <div class="f">
        <div class="lb" id="lb-situacao">Situação do veículo</div>
        <div class="seg" role="radiogroup" aria-labelledby="lb-situacao">
          <input type="radio" name="situacao" id="sit-quitado" value="quitado" checked><label for="sit-quitado">Quitado</label>
          <input type="radio" name="situacao" id="sit-financiado" value="financiado"><label for="sit-financiado">Ainda financiado</label>
        </div>
      </div>
      <div class="f">
        <label for="campo-veiculo">Valor do veículo <span>aproximado</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-veiculo" type="text" inputmode="numeric" autocomplete="off" value="100.000" class="num"></div>
        <input id="range-veiculo" type="range" aria-label="Valor do veículo, controle deslizante" min="15000" max="500000" step="5000" value="100000">
        <div class="slabel"><span>R$ 15 mil</span><span>R$ 500 mil</span></div>
      </div>
      <div class="f" id="bloco-saldo" hidden>
        <label for="campo-saldo">Saldo devedor do financiamento <span>quanto falta pagar</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-saldo" type="text" inputmode="numeric" autocomplete="off" value="0" class="num"></div>
        <div class="hint">Se o carro ainda está financiado, o novo crédito liquida esse saldo e o restante cai na sua conta.</div>
      </div>
      <div class="f">
        <label for="campo-receber">Quanto você quer receber <span>valor líquido</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-receber" type="text" inputmode="numeric" autocomplete="off" value="50.000" class="num"></div>
        <input id="range-receber" type="range" aria-label="Quanto você quer receber, controle deslizante" min="5000" max="80000" step="1000" value="50000">
        <div class="slabel"><span id="min-receber">R$ 5 mil</span><span id="max-receber">R$ 80 mil</span></div>
        <div class="hint warn" id="msg-ajuste" hidden></div>
      </div>
      <div class="f">
        <label for="campo-prazo">Prazo <span>de @@PRAZO_MIN@@ a @@PRAZO_MAX@@ meses</span></label>
        <div class="inp combo" id="combo-prazo">
          <input id="campo-prazo" type="text" inputmode="numeric" autocomplete="off" value="48" class="num" role="combobox" aria-autocomplete="none" aria-expanded="false" aria-controls="lista-prazo" aria-describedby="msg-prazo" aria-label="Prazo em meses: escolha na lista ou digite">
          <em>meses</em>
          <button type="button" class="caret" id="btn-prazo" aria-label="Abrir a lista de prazos" aria-haspopup="listbox" aria-controls="lista-prazo"><svg viewBox="0 0 12 8" width="12" height="8" aria-hidden="true"><path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          <ul class="opts" id="lista-prazo" role="listbox" aria-label="Prazos disponíveis" hidden></ul>
        </div>
        <input id="range-prazo" type="range" aria-label="Prazo em meses, controle deslizante" min="@@SL_PRAZO_MIN@@" max="@@SL_PRAZO_MAX@@" step="1" value="48">
        <div class="slabel"><span>@@SL_PRAZO_MIN@@ meses</span><span>@@SL_PRAZO_MAX@@ meses</span></div>
        <div class="hint warn" id="msg-prazo" hidden></div>
      </div>
      <details class="outra" id="det-taxa">
        <summary>Já tem uma proposta? Use a taxa dela</summary>
        <div class="oi">
          <label for="campo-taxa-prop">Taxa da proposta <span>% ao mês</span></label>
          <div class="inp"><input id="campo-taxa-prop" type="text" inputmode="decimal" autocomplete="off" placeholder="ex.: 1,39" class="num" aria-describedby="msg-taxa-prop"><em>% a.m.</em></div>
          <div class="hint" id="msg-taxa-prop">Deixe em branco para usar a taxa de referência. Digite a taxa mensal da proposta, como está.</div>
        </div>
      </details>
    </section>

    <section class="panel resp" id="resultado" aria-labelledby="t-resultado" aria-live="polite">
      <h2 class="kicker kres" id="t-resultado">Resultado da simulação</h2>
      <div class="res">
        <div>
          <div class="kicker" id="r-kicker">Parcela estimada</div>
          <div class="big num"><span id="r-parcela">@@D_PARCELA@@</span> <small>/mês</small></div>
          <div class="dim" id="r-sub">@@D_SUB@@</div>
          <div class="dim ult" id="r-ultima" hidden></div>
          <hr class="sep">
          <div class="dim lab">Total estimado ao final</div>
          <div class="mid num" id="r-total">@@D_TOTAL@@</div>
          <div class="dim"><a href="/metodologia">Como calculamos</a></div>
        </div>
        <div class="ctx sis">
          <div class="t" id="lb-sistema">Tipo de parcela</div>
          <div class="seg s2" role="radiogroup" aria-labelledby="lb-sistema">
            <input type="radio" name="sistema" id="sis-price" value="price" checked><label for="sis-price">Price <small>parcela fixa</small></label>
            <input type="radio" name="sistema" id="sis-sac" value="sac"><label for="sis-sac">SAC <small>parcela cai</small></label>
          </div>
          <div class="hint" id="hint-sistema">@@D_HINT_SIS@@</div>
        </div>
      </div>
      <div class="callout"><p id="r-resumo">@@D_RESUMO@@</p></div>
      <div class="rosca">
        <svg viewBox="0 0 120 120" width="120" height="120" role="img" id="rosca-svg" aria-label="Do total pago, @@D_PCT_JUROS@@% é juros">
          <circle cx="60" cy="60" r="46" fill="none" stroke="#f0807a" stroke-width="14"/>
          <circle id="rosca-cred" cx="60" cy="60" r="46" fill="none" stroke="#f59e0b" stroke-width="14" stroke-dasharray="@@D_ROSCA_P@@ 289.03" transform="rotate(-90 60 60)"/>
          <text x="60" y="61" text-anchor="middle" class="rc-n" id="rosca-pct">@@D_PCT_JUROS@@%</text>
          <text x="60" y="77" text-anchor="middle" class="rc-t">em juros</text>
        </svg>
        <div class="rc-l">
          <div class="kicker">Para onde vai o total</div>
          <div class="lg"><span><s></s>Crédito</span><b class="num" id="rosca-cred-v">@@D_L_CRED@@</b></div>
          <div class="lg"><span><s class="jr"></s>Juros</span><b class="num" id="rosca-juros-v">@@D_L_JUROS@@</b></div>
        </div>
      </div>
      <div class="rodape-res">
        <div class="cta">
          <div><strong>Faça sua proposta</strong><span class="s">Com um parceiro de crédito · sem compromisso</span></div>
          <button type="button" class="btn" id="btn-cta">Consultar opções →</button>
        </div>
        <div class="fine2">Estimativa: a taxa final sai da análise do crédito e da avaliação do veículo. O veículo fica como garantia da operação e pode ser retomado em caso de atraso — <a href="#garantia">entenda abaixo</a>.</div>
        <div class="copiar"><button type="button" id="btn-copiar">Copiar o link desta simulação</button><span id="msg-copiado" role="status"></span></div>
      </div>
    </section>
  </div>

  <div class="uso" aria-label="Quanto do valor do veículo o crédito usa">
    <div class="uso-t"><span class="t">Valor do veículo</span><b class="v num" id="c-veiculo">R$ 100.000</b></div>
    <div class="uso-b"><svg class="bar" id="bar-ltv" width="100%" height="12" role="img" aria-label="Quanto do valor do veículo o crédito usa">
            <rect width="100%" height="12" rx="6" fill="rgba(255,255,255,.1)"/><rect id="bar-fill" width="@@D_BARRA@@%" height="12" rx="6" fill="#f59e0b"/><rect id="bar-mark" x="80%" y="-3" width="2" height="18" fill="#e2e8f0"/>
          </svg></div>
    <div class="uso-l">
      <div class="lg"><span><s></s>Crédito (<span id="c-ltv-rot">você recebe</span>)</span><b class="num" id="c-credito">@@D_CREDITO@@</b></div>
      <div class="lg"><span><s class="lim"></s><span id="c-limite-rot">Limite (80%)</span></span><b class="num" id="c-limite">@@D_LIMITE@@</b></div>
    </div>
  </div>

  <div class="kpis" aria-label="Três números para ler o custo">
    <div class="kp"><span class="t">Quita por volta de</span><b class="num" id="k-quita">—</b><small id="k-quita-s"></small></div>
    <div class="kp"><span class="t">Cada R$ 1 de crédito custa</span><b class="num" id="k-juro1">—</b><small>de juros até o fim</small></div>
    <div class="kp"><span class="t">Taxa equivalente ao ano</span><b class="num" id="k-aa">—</b><small id="k-aa-s">para comparar com outras taxas</small></div>
  </div>
  <p class="hint kpn" id="k-nota">Estimativa, não é oferta. Taxa média do parceiro conferida em 18/11/2026.</p>

  <section class="band fatos" aria-label="Condições divulgadas por um parceiro de crédito">
    <div class="fatos-g">
      <div><b class="num">@@FATO_TAXA@@</b><span>ao mês, taxa média divulgada</span></div>
      <div><b class="num">@@FATO_LTV@@</b><span>do valor do veículo, no máximo</span></div>
      <div><b class="num">Fixa</b><span>parcela, sem atualização pelo IPCA</span></div>
      <div><b class="num">R$ 0</b><span>e sem cadastro para simular</span></div>
    </div>
    <p class="hint">O parceiro de crédito mostra a taxa média e o teto de 80% do valor do veículo. Prazo e valores mínimo e máximo ele não publica, e a tela não impõe limite. Taxa e limite definitivos vêm da análise e da avaliação do veículo.</p>
  </section>

  <section class="blk" aria-labelledby="t-raio">
    <div class="raio">
      <div class="hd">
        <div><div class="kicker">Raio-X da decisão</div><h2 id="t-raio">A parcela do veículo cabe no seu mês?</h2></div>
      </div>
      <div class="mini-in"><label for="campo-conforto">Quanto de parcela cabe no seu mês?</label><div class="inp"><span class="pre">R$</span><input id="campo-conforto" type="text" inputmode="numeric" autocomplete="off" value="1.500" class="num"><em>/mês</em></div></div>
      <p id="raio-texto">@@D_RAIO@@</p>
      <div class="alts" id="alts"></div>
      <div class="regra" id="regra-renda">
        <div class="rt"><b>E o limite de 30% da renda?</b> <span id="renda-texto">@@D_RENDA@@</span></div>
        <details class="rdet" id="det-renda">
          <summary>Como a renda entra na análise do Auto Equity</summary>
          @@REGRA_RENDA@@
        </details>
      </div>
      <div class="hint">Nada aqui aponta o prazo “melhor”: isso depende do que pesa mais para você. O valor de parcela que você digita é só a sua régua, não uma análise de crédito.</div>
    </div>
  </section>

  <section class="blk amsec" id="amortizacao" aria-labelledby="t-amort">
    <div class="kicker">Amortização</div>
    <h2 id="t-amort">Antecipar parcelas pode economizar milhares de reais</h2>
    <p class="lead amlead">Nos primeiros meses, a maior parte da parcela do veículo vai para juros. Cada valor extra que você paga reduz o saldo sobre o qual os juros são cobrados: a dívida acaba antes e custa menos. Veja o efeito no seu cenário.</p>

    <div class="split amwhy">
      <div class="split-t">
        <h3 class="sub"><span class="n" aria-hidden="true">1</span>Os juros vêm primeiro</h3>
        <div class="giga num"><span id="amort-pct">@@D_AMORT_PCT@@%</span><small id="amort-pct-rot">@@D_AMORT_PCT_ROT@@</small></div>
        <p class="lead" id="amort-resumo">@@D_AMORT_RESUMO@@</p>
      </div>
      <div class="panel graf">
        <div class="leg">
          <span><s class="jr"></s>Juros do bloco de 6 meses</span><span><s></s>Amortização do bloco</span><span><s class="ln"></s>Saldo devedor</span>
        </div>
        <svg id="amort-graf" viewBox="0 0 640 220" preserveAspectRatio="none" role="img" aria-label="Gráfico: juros e amortização de cada bloco de 6 meses e saldo devedor"></svg>
        <div class="eixo"><span>Mês 1</span><span id="amort-fim">@@D_AMORT_FIM@@</span></div>
      </div>
    </div>

    <details class="amort amsim" id="det-amsim">
      <summary>Simular: pagar a mais todo mês ou amortizar de uma vez</summary>
    <div class="panel amx">
      <h3 class="sub"><span class="n" aria-hidden="true">2</span>Amortização: quanto você poupa pagando a mais</h3>
      <p class="amsub">Escolha o valor e o momento. Quanto mais cedo, maior a economia.</p>
      <div class="amin">
        <div class="f">
          <label for="campo-extra">Pagar a mais todo mês <span>além da parcela</span></label>
          <div class="inp"><span class="pre">R$</span><input id="campo-extra" type="text" inputmode="numeric" autocomplete="off" value="200" class="num"><em>/mês</em></div>
        </div>
        <div class="f">
          <label for="campo-unico">Amortização única <span>um valor de uma vez</span></label>
          <div class="inp"><span class="pre">R$</span><input id="campo-unico" type="text" inputmode="numeric" autocomplete="off" value="5.000" class="num"></div>
        </div>
        <div class="f">
          <label for="range-quando">Quando fazer a única <span id="quando-rot">depois da 6ª parcela</span></label>
          <input id="range-quando" type="range" min="0" max="47" step="1" value="6" aria-describedby="quando-rot">
        </div>
      </div>
      <div class="amcards" id="am-cartoes"></div>
      <p class="qtxt" id="am-texto"></p>
    </div>

    <div class="panel graf amtempo">
      <h3 class="sub"><span class="n" aria-hidden="true">3</span>O mesmo valor, em momentos diferentes</h3>
      <p class="amsub" id="am-tempo-txt"></p>
      <svg id="am-tempo" viewBox="0 0 640 150" preserveAspectRatio="none" role="img" aria-label="Gráfico: economia de juros conforme o momento da amortização única"></svg>
      <div class="eixo"><span>Logo no início</span><span id="am-tempo-fim">Depois da 47ª parcela</span></div>
    </div>

    <div class="amdicas">
      <div class="amd"><h4>Prazo ou parcela?</h4><p>Encurtar o prazo é o que mais corta juros, porque as parcelas do final desaparecem. Baixar a parcela, em troca, alivia o orçamento mensal. Decida pelo que o seu momento pede.</p></div>
      <div class="amd"><h4>Veja o que o contrato diz</h4><p>Antes de adiantar dinheiro, pergunte à instituição como se pede a amortização, se existe valor mínimo ou tarifa e se o abatimento diminui o prazo ou a parcela. O Código de Defesa do Consumidor (art. 52, § 2º) garante a redução proporcional dos juros na liquidação antecipada; veja como o seu contrato trata isso.</p></div>
      <div class="amd"><h4>Compare com outro uso do dinheiro</h4><p>Adiantar parcelas rende, na prática, a taxa da dívida: <b id="am-taxa-aa">@@D_AM_TAXA@@</b> ao ano neste cenário. Compare com o que esse dinheiro faria em outra aplicação, depois dos impostos, e guarde uma reserva de emergência antes de antecipar. Isto não é recomendação de investimento.</p></div>
    </div>

    </details>

    <details class="amort" id="det-amort">
      <summary>Ver a amortização a cada 6 meses</summary>
      <div class="tw"><table id="tab-amort">
        <caption id="amort-cap">Parcela fixa: juros, amortização e saldo devedor no fim de cada bloco de 6 meses</caption>
        <thead><tr><th scope="col">Meses</th><th scope="col">Juros</th><th scope="col">Amortização</th><th scope="col">Saldo devedor</th></tr></thead>
        <tbody id="amort-corpo">@@D_AMORT_LINHAS@@</tbody>
        <tfoot id="amort-rodape">@@D_AMORT_TOTAL@@</tfoot>
      </table></div>
      <div class="hint" id="amort-nota">@@D_AMORT_NOTA@@</div>
    </details>
  </section>

  <section class="blk" aria-labelledby="t-cmp">
    <div class="kicker">Taxas</div>
    <h2 id="t-cmp">O custo mensal do Auto Equity frente a outros créditos</h2>
    <p class="lead">O veículo em garantia derruba o juro mensal em relação ao crédito sem garantia; veja por quanto.</p>
    <div class="panel">@@COMPARACAO@@</div>
    <div class="note" id="nota-taxa"><b>E se a taxa for maior?</b> <span id="nota-taxa-texto">@@NOTA_TAXA@@</span></div>
  </section>

  <section class="blk" aria-labelledby="t-cmpmod">
    <div class="kicker">Comparativo</div>
    <h2 id="t-cmpmod">O mesmo crédito em outras modalidades</h2>
    <p class="lead" id="cm-lead">@@D_CM_LEAD@@</p>
    <div class="panel cmpx">
      <div class="cmleg"><span><s class="cr"></s>O que você recebe</span><span><s class="jr2"></s>Juros pagos até o fim</span></div>
      <div class="cmrows" id="cm-linhas"></div>
      <div class="cmgap">
        <div class="gv num" id="cm-gap-v">@@D_CM_GAPV@@</div>
        <p id="cm-gap">@@D_CM_GAP@@</p>
      </div>
    </div>
    <div class="hint" id="cm-nota">@@D_CM_NOTA@@</div>
  </section>

  <section class="band" aria-labelledby="t-quitar">
    <div class="kicker">Dívida cara</div>
    <h2 id="t-quitar">Tem uma dívida cara? Veja se vale trocar</h2>
    <p class="lead">A mesma dívida, no mesmo prazo do simulador, na taxa média do mercado e no Auto Equity.</p>
    <div class="qgrid">
      <div class="panel quitar">
        <div class="f">
          <div class="lb" id="lb-tipodiv">Tipo de dívida</div>
          <div class="seg s2" role="radiogroup" aria-labelledby="lb-tipodiv">@@DIVIDA_OPCOES@@</div>
        </div>
        <div class="f">
          <label for="campo-divida">Quanto você deve <span>saldo da dívida</span></label>
          <div class="inp"><span class="pre">R$</span><input id="campo-divida" type="text" inputmode="numeric" autocomplete="off" value="60.000" class="num"></div>
        </div>
        <div class="f" id="bloco-taxa-div" hidden>
          <label for="campo-taxa-div">Taxa da sua dívida <span>% ao mês</span></label>
          <div class="inp"><input id="campo-taxa-div" type="text" inputmode="decimal" autocomplete="off" value="5" class="num"><em>% a.m.</em></div>
        </div>
        <div class="row2"><button type="button" class="ghost" id="btn-usar-divida">Simular com este valor</button></div>
      </div>
      <div class="panel qres">
        <div class="hint warn" id="q-aviso" hidden></div>
        <div class="alts dois" id="q-cartoes">@@D_Q_CARTOES@@</div>
        <div class="qviz" id="q-grafico"></div>
        <p class="qtxt" id="q-texto">@@D_Q_TEXTO@@</p>
      </div>
    </div>
    <div class="hint">Conta de comparação: as duas dívidas têm a mesma duração. Cheque especial e rotativo não costumam durar tanto; o ponto é ver quanto o juro pesa por mês. A troca coloca o veículo como garantia: <a href="/garantia-do-veiculo">veja o que muda</a> e <a href="/custos-alem-dos-juros">os custos além dos juros</a>.</div>
  </section>

  <section class="blk" id="garantia" aria-labelledby="t-gar">
    <div class="split gar">
      <div class="split-t">
        <div class="kicker">Garantia</div>
        <h2 id="t-gar">Como funciona a garantia do veículo</h2>
        <p class="lead">Saber o que fica registrado no veículo ajuda a escolher uma parcela que não aperte.</p>
        <p class="hint"><a href="/garantia-do-veiculo">Leia o guia completo sobre a garantia</a></p>
      </div>
      <div class="lista3">
        <div class="li3"><span class="n" aria-hidden="true">1</span><div><h4>O que muda para você</h4><ul><li>Você continua usando o veículo</li><li>A garantia é o que permite juros menores</li></ul></div></div>
        <div class="li3"><span class="n" aria-hidden="true">2</span><div><h4>O que fica registrado</h4><ul><li>O veículo é dado em garantia à instituição, com o gravame registrado no cadastro dele</li><li>Não dá para vender sem acertar com o credor; o gravame sai quando a dívida é quitada</li></ul></div></div>
        <div class="li3"><span class="n" aria-hidden="true">3</span><div><h4>Para ficar tranquilo</h4><ul><li>Prefira uma parcela que sobre no orçamento</li><li>Em atraso prolongado, o veículo pode ser retomado, como o contrato e a lei preveem</li></ul></div></div>
      </div>
    </div>
  </section>

  <section class="band" aria-labelledby="t-pede">
    <div class="kicker">Documentos</div>
    <h2 id="t-pede">O que o parceiro costuma pedir</h2>
    <p class="lead">Cada instituição tem a sua lista. Em geral, para Auto Equity:</p>
    <div class="steps">
      <div class="st"><span class="sn" aria-hidden="true">01</span><h4>Sobre você</h4><ul><li>Documento e comprovante de residência</li><li>Comprovante de renda ou extratos (inclusive para autônomos)</li><li>Se o veículo não está no seu nome, quem é o dono entra na operação</li></ul></div>
      <div class="st"><span class="sn" aria-hidden="true">02</span><h4>Sobre o veículo</h4><ul><li>Documento do veículo e situação do financiamento, se houver</li><li>Avaliação: idade, modelo, quilometragem e conservação</li><li>Consórcio não entra; caminhões, vans e ônibus só em algumas instituições</li></ul></div>
      <div class="st"><span class="sn" aria-hidden="true">03</span><h4>Etapas até receber</h4><ul><li>Análise de crédito</li><li>Avaliação do veículo</li><li>Contrato e registro do gravame</li></ul></div>
    </div>
  </section>

  <section class="blk" aria-labelledby="t-guias">
    <h2 id="t-guias">Entenda antes de decidir</h2>
    <div class="cols3">@@CARTOES@@</div>
  </section>

  <section class="blk split faqs" aria-labelledby="t-faq">
    <div class="split-t">
      <div class="kicker">Dúvidas</div>
      <h2 id="t-faq">Perguntas frequentes</h2>
    </div>
    <div class="faq">@@FAQ@@</div>
  </section>

  <dialog id="dlg-confirma" aria-labelledby="dlg-titulo">
    <h3 id="dlg-titulo">Antes de continuar</h3>
    <p>Você vai preencher um formulário de um <b>parceiro de crédito</b>, que analisa o seu pedido. A página dele mostra o nome da empresa.</p>
    <ul>
      <li>Se o veículo está no seu nome, valor aproximado dele e o valor que você quer.</li>
      <li>Dados pessoais e de renda, e documentos do veículo mais adiante.</li>
      <li>O parceiro pode consultar bureaus de crédito, conforme o aviso dele.</li>
      <li>O veículo fica como garantia da operação e pode ser retomado em caso de atraso: leia as condições com calma.</li>
      <li>Simular aqui não é aprovação e você não é obrigado a contratar.</li>
    </ul>
    <p class="dim">Veja a <a href="/privacidade">política de privacidade</a> e <a href="/metodologia">como calculamos</a>.</p>
    <div class="row"><a class="btn" id="a-parceiro" href="@@PARCEIRO@@" target="_blank" rel="noopener sponsored">Continuar para o parceiro →</a><button type="button" class="ghost" id="btn-voltar">Voltar e ajustar</button></div>
  </dialog>
"""

GUIA_CABECALHO = """<div class="volta"><a class="btn-volta" href="/#simulador" data-volta>← Voltar à simulação</a></div>
<nav class="crumb" aria-label="Você está em"><a href="/">Auto Equity <span>@@ROTULO_PAGINA@@</span></a></nav>
<article class="guia">
  <h1>@@H1@@</h1>
  <p class="meta">Atualizado em @@ATUALIZADO@@ · @@RAZAO@@</p>
  <div class="prose">
"""

GUIA_MEIO = """  </div>
"""

GUIA_FECHO = """  <aside class="fecho">
    <p class="t">Simule com o seu veículo</p>
    <p>Confira a parcela e o custo total antes de fechar.</p>
    <a class="btn" href="/#simulador" data-volta>Voltar à simulação →</a>
  </aside>
  <section class="rel" aria-labelledby="veja-tambem">
    <h2 id="veja-tambem">Veja também</h2>
    <ul>@@RELACIONADOS@@</ul>
  </section>
"""
