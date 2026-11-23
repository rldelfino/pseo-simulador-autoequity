# Simulador de Auto Equity — Datalab Global

Idioma: português do Brasil. Estilo: curto, sem jargão, números reais, dizer o que NÃO foi verificado.
Projeto irmão de `../006-pseo-simulador-homeequity` (esqueleto copiado dele em 19/11/2026; mesmas regras de operação). Plano aprovado: `../_plano-equity-condominio/PLANO.md`.

## Regras fixas
- **Graphify primeiro, sem o dono pedir.** Antes de ler arquivo/grep: `graphify update .` e `graphify query "..."`. Depois de cada ciclo de edição: `graphify update .`.
- Sem gastar dinheiro. Sem postar nem mandar mensagem a pessoas. Nada de CPF/telefone em log, teste ou arquivo.
- **Mensagem agnóstica sobre o parceiro**: "um parceiro de crédito". Sem texto sobre remuneração/comissão e sem citar o nome do parceiro nem de bancos (há teste que barra). Sem ranking.
- Tom calmo sobre a garantia: aviso curto perto do botão (o veículo fica em garantia e pode ser retomado), explicação na seção/página própria. Um valor único de parcela (taxa de referência do parceiro); a média do BCB só na nota "E se a taxa for maior?".
- Link de conversão do parceiro (`LINK_PARCEIRO` em `gerador_autoequity.py`) só no botão da tela de confirmação (teste barra qualquer outra ocorrência). **Hoje o valor é PROVISÓRIO: link recebido antes e NÃO confirmado pelo dono para o Auto Equity.** Confirmar antes de publicar.
- Medição: Umami, `UMAMI_ID` **vazio** (sem script) até o dono decidir o ID. Eventos: `usou-simulador-autoequity`, `abriu-confirmacao`, `cta-parceiro`, `copiou-link` (`receber`, `prazo`), `abriu-amortizacao`, `usou-quitar-divida` (`tipo`), `simulou-amortizacao`, `usou-taxa-propria`. `prazo` = meses. Nos testes o Umami é bloqueado.
- Sem segredo em arquivo/GitHub. Python 3.10 no CI (sem f-string aninhado). CSP: sem `style=` nem script inline; barras são SVG com atributos; sliders usam `data-p`.
- Máximo ~15 páginas indexáveis, cada uma com conteúdo próprio (hoje 13 no sitemap).
- Paleta: **âmbar `#f59e0b`** (produto); **juros em coral `#f0807a`** (não é o âmbar-juros do 006); outras modalidades: garantia real `#7ea6d9`, pessoal `#b69be0`, cheque `#7dc4b0`, rotativo `#d98fb8` (`conteudo.COR_MODALIDADE` = `simulador.js` `COR`).

## Comandos
- Gerar: `python gerador_autoequity.py` (saída em `paginas_seo/`, sem build). CSS à mão em `src/estilo.css`.
- Testes (CI): `python -m pytest -q` (117). Python x JS via Node: `tests/test_calculo_js.py`, `test_amortizar_antes.py`, `test_amortizacao_quitacao.py`.
- Fora do CI (Playwright, Chromium + WebKit): `python testar_navegador.py` (ponta a ponta, desktop e celular), `python testar_aleatorio.py` (8 sessões × 70 passos contra `calculo.py`), `python testar_amort_quitar.py` (amortização por blocos, "pagar antes", quitar dívida), `python varredura_dispositivos.py`.
- Ícones/og-image (âmbar): `python gerar_icones.py`. Taxas do BCB: `python etl_taxas.py`. HTML único de teste: `python gerar_html_unico.py` (gera `auto-equity-teste-v1.html`, ignorado pelo git).

## Fatos do produto (conferidos em 18/11/2026, página pública do parceiro)
- Libera **até 80% do valor do veículo** (`LTV_MAX`). Taxa: **"média" de 1,39% a.m.** no gráfico do parceiro (`TAXA_PARCEIRO_AM`); é média divulgada, NÃO "a partir de". **Sem IPCA**: parcela fixa (Price), SEM SAC (dono, 23/11/2026: o Auto Equity só tem parcela fixa/Price; opção removida da tela, link com `sistema=sac` abre no Price; as funções `sistema="sac"` de `calculo.py` ficam só como conta de referência testada).
- Veículo de consórcio não entra; caminhões, vans e ônibus só em algumas instituições; idade, modelo, km e conservação mudam o valor; não vende sem acertar com o credor; atraso leva à retomada.
- BCB: 29976 (garantia real, mistura imóvel e veículo, só na nota "E se a taxa for maior?"), 20742/20741/22022 (dívidas caras, a.a.). O IPCA (13522) saiu de `taxas_referencia.py` e do CSV.
- Cenário padrão: veículo R$ 100.000, receber R$ 50.000, 48 meses → R$ 1.434/mês, total R$ 68.855 (juros R$ 18.855).
- Páginas: home + como-funciona, garantia-do-veiculo, custos-alem-dos-juros, auto-equity-ou-outro-credito, quando-nao-vale-a-pena, taxas-de-referencia, metodologia, dados-abertos, sobre, atualizacoes, privacidade, termos. Domínio previsto: https://autoequity.datalabglobal.com. Chave IndexNow nova em `indexnow.py` (pública por desenho).

## Limites: a tela só representa os do parceiro (decisão do dono, 21/11/2026)
O parceiro só divulga "até 80% do valor do veículo" (`LTV_MAX`). Prazo, crédito mínimo e teto de crédito NÃO são publicados, então a tela NÃO impõe limite de negócio: só barra zero/negativo/absurdo (`PRAZO_MIN_MESES`=1 a `PRAZO_MAX_MESES`=120, `RECEBER_MIN`=1, `CREDITO_MAX`/`VEICULO_MAX`=1 bilhão, taxa própria 0,01% a 30% a.m.). `SLIDER_PRAZO_MIN/MAX` (6 a 60) é só a faixa da lista suspensa e do controle deslizante; `PRAZO_SUGERIDO_MAX` (60) é o prazo do cartão "Prazo maior" (exemplo, não regra). O site diz isso em `/metodologia` e no FAQ. Se o parceiro publicar valores reais, trocar só as constantes e rodar os testes. Veículo de poucos reais (< R$ 1.000) arredonda em reais inteiros: o teste aleatório ignora o % nesses casos.

## Diferenças em relação ao 006
- Prazo em **meses** (lista suspensa 6–60, digitável, controle deslizante); link compartilhável usa `veiculo`, `saldo`, `receber`, `prazo` (meses), `conforto`, `taxa` (sem `ipca`).
- Amortização e gráficos por **blocos de 6 meses** (`calculo.amortizacao_periodos`, `PERIODO_MESES`), tabela com coluna "Meses" ("1 a 6", "7 a 12"…). "Pagar antes": o valor único é aplicado depois da N-ª parcela (slider em meses, 0 a prazo−1).
- Taxa da proposta: digitada como está (sem caixa "inclui IPCA").
- Seções reaproveitadas do 006: faixa de 3 números, Raio-X (com regra da renda), pagar antes, tabela de taxas por modalidade, comparativo, quitar dívida cara, FAQ.

## ATUALIZAÇÃO 20/11/2026: PUBLICADO
No ar em https://autoequity.datalabglobal.com (repo `rldelfino/pseo-simulador-autoequity`, Cloudflare Pages `pseo-simulador-autoequity`, saída `paginas_seo`, Umami compartilhado com os irmãos, IndexNow enviado, link do parceiro CONFIRMADO pelo dono). Links do Auto Equity mesclados nos irmãos 002, 003, 004 (hub), 005 e 006. Teste mobile (Chromium Pixel 5 e WebKit iPhone 13) nos 3 sites no ar: sem rolagem horizontal, campos ≥16px, link no rodapé. Aviso no console: o Cloudflare injeta o beacon de Web Analytics e a CSP (`script-src 'self' https://cloud.umami.is`) o bloqueia (inofensivo; vale igual no 006). Sitemap enviado em 20/11/2026 no Search Console (propriedade de domínio datalabglobal.com) e no Bing Webmaster (aceito para processamento); falta só acompanhar a indexação. As frases "Nada publicado" abaixo são do estado de 19/11.

## Estado (19/11/2026)
- Construído e testado LOCALMENTE (pytest 115 verdes; `testar_navegador.py`, `testar_aleatorio.py` e `testar_amort_quitar.py` com 0 falha em Chromium e WebKit). `git init` local com commit inicial. **Nada publicado**: sem repositório no GitHub, sem push, sem Cloudflare, sem IndexNow, sem Umami.
- Tela de teste enviada ao dono: `auto-equity-teste-v1.html` (só a home; links para as outras páginas viram `#`). **Dono APROVOU a tela em 19/11/2026.** Publicação ainda não pedida: só publicar com ordem explícita e link do parceiro confirmado.
- NÃO verificado: link do parceiro (provisório); se o formulário do parceiro aceita pré-preenchimento; prazo máximo, mínimo e teto reais; texto jurídico (alienação fiduciária de bem móvel, busca e apreensão, quitação antecipada) sem revisão jurídica; iPhone/Safari físico; `varredura_dispositivos.py` rodou com os mesmos achados genéricos do 006 (rótulos pequenos como "alvos de toque", e o Playwright-WebKit não tira print de página inteira com DPR 3 por passar de 32767 px) — não comparado linha a linha com o 006; a data "19/11/2026" em `/atualizacoes` é a de criação, ajustar na publicação; o texto de `/atualizacoes` descreve a primeira versão.
- Antes de publicar: confirmar link, decidir `UMAMI_ID`, criar repo `rldelfino/pseo-simulador-autoequity`, dar acesso do app Cloudflare ao repo, Pages com saída `paginas_seo`, domínio `autoequity.datalabglobal.com`, linkar no hub e nos rodapés dos irmãos (006 já tem o link do Auto Equity? não: acrescentar), Search Console/Bing/IndexNow.

## Revisão geral de 20/11/2026 (pedido do dono)
- Números: conta conferida por testes (pytest, navegador, aleatório Chromium+WebKit, 0 falha); taxas do BCB conferidas ao vivo. Taxa média do parceiro para veículo (1,39%) reconferida em 20/11/2026, igual.
- Menos informação: o simulador de "pagar a mais" (valor extra por mês, amortização única, gráfico por momento, dicas) ficou recolhido em `<details id="det-amsim">`; a parte 1 ("Os juros vêm primeiro") e a tabela por blocos continuam visíveis. Cortou cerca de 2.700 px da home no celular. Os testes que mexem nesses campos abrem o bloco antes.
- SEO: privacidade e termos agora `noindex,follow` e fora do sitemap (texto padrão quase igual nos três simuladores; `SEM_INDICE` no gerador); schema `WebApplication` na home; títulos de sobre/privacidade/termos distintos por produto. Textos do Auto Equity reescritos (a similaridade de 5-gramas com o Home Equity caiu de 0,50 para 0,29 na home e ficou abaixo de 0,40 nas demais páginas indexáveis).
- Rodapé: links cruzados entre Home Equity, Auto Equity e Condomínio.
- Console: o Cloudflare injeta o beacon de Web Analytics (zona datalabglobal.com, "Automatic setup") e a CSP o bloqueia; é só ruído no console, não afeta o uso. Para limpar: ou liberar `static.cloudflareinsights.com` na CSP, ou desligar o setup automático no Cloudflare (decisão do dono).
