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
- Testes (CI): `python -m pytest -q` (115). Python x JS via Node: `tests/test_calculo_js.py`, `test_amortizar_antes.py`, `test_amortizacao_quitacao.py`.
- Fora do CI (Playwright, Chromium + WebKit): `python testar_navegador.py` (ponta a ponta, desktop e celular), `python testar_aleatorio.py` (8 sessões × 70 passos contra `calculo.py`), `python testar_amort_quitar.py` (amortização por blocos, "pagar antes", quitar dívida), `python varredura_dispositivos.py`.
- Ícones/og-image (âmbar): `python gerar_icones.py`. Taxas do BCB: `python etl_taxas.py`. HTML único de teste: `python gerar_html_unico.py` (gera `auto-equity-teste-v1.html`, ignorado pelo git).

## Fatos do produto (conferidos em 18/11/2026, página pública do parceiro)
- Libera **até 80% do valor do veículo** (`LTV_MAX`). Taxa: **"média" de 1,39% a.m.** no gráfico do parceiro (`TAXA_PARCEIRO_AM`); é média divulgada, NÃO "a partir de". **Sem IPCA**: parcela fixa (Price), SAC opcional na mesma taxa (o parceiro não confirmou se oferece).
- Veículo de consórcio não entra; caminhões, vans e ônibus só em algumas instituições; idade, modelo, km e conservação mudam o valor; não vende sem acertar com o credor; atraso leva à retomada.
- BCB: 29976 (garantia real, mistura imóvel e veículo, só na nota "E se a taxa for maior?"), 20742/20741/22022 (dívidas caras, a.a.). O IPCA (13522) saiu de `taxas_referencia.py` e do CSV.
- Cenário padrão: veículo R$ 100.000, receber R$ 50.000, 48 meses → R$ 1.434/mês, total R$ 68.855 (juros R$ 18.855).
- Páginas: home + como-funciona, garantia-do-veiculo, custos-alem-dos-juros, auto-equity-ou-outro-credito, quando-nao-vale-a-pena, taxas-de-referencia, metodologia, dados-abertos, sobre, atualizacoes, privacidade, termos. Domínio previsto: https://autoequity.datalabglobal.com. Chave IndexNow nova em `indexnow.py` (pública por desenho).

## Limites "A CONFIRMAR" (NÃO são regra do parceiro, ficam em constantes de `calculo.py` e saem em `calculo.js`)
O parceiro não publica prazo máximo, crédito mínimo nem teto de crédito. A tela usa, conservadoramente: prazo **6 a 60 meses** (`PRAZO_MIN_MESES`/`PRAZO_MAX_MESES`), crédito mínimo **R$ 5.000** (`RECEBER_MIN`), teto **R$ 200.000** (`CREDITO_MAX`), veículo de R$ 15.000 a R$ 2.000.000, taxa da proposta digitada de 0,5% a 6% a.m. (`TAXA_PROPRIA_MIN/MAX`), passo de R$ 1.000. O site diz isso na home (faixa de condições), em `/metodologia`, em `/como-funciona` e no FAQ. Se o dono obtiver os valores reais do parceiro, trocar só as constantes e rodar os testes.

## Diferenças em relação ao 006
- Prazo em **meses** (lista suspensa 6–60, digitável, controle deslizante); link compartilhável usa `veiculo`, `saldo`, `receber`, `prazo` (meses), `conforto`, `sistema`, `taxa` (sem `ipca`).
- Amortização e gráficos por **blocos de 6 meses** (`calculo.amortizacao_periodos`, `PERIODO_MESES`), tabela com coluna "Meses" ("1 a 6", "7 a 12"…). "Pagar antes": o valor único é aplicado depois da N-ª parcela (slider em meses, 0 a prazo−1).
- Taxa da proposta: digitada como está (sem caixa "inclui IPCA").
- Seções reaproveitadas do 006: faixa de 3 números, Raio-X (com regra da renda), pagar antes, tabela de taxas por modalidade, comparativo, quitar dívida cara, FAQ.

## Estado (19/11/2026)
- Construído e testado LOCALMENTE (pytest 115 verdes; `testar_navegador.py`, `testar_aleatorio.py` e `testar_amort_quitar.py` com 0 falha em Chromium e WebKit). `git init` local com commit inicial. **Nada publicado**: sem repositório no GitHub, sem push, sem Cloudflare, sem IndexNow, sem Umami.
- Tela de teste enviada ao dono: `auto-equity-teste-v1.html` (só a home; links para as outras páginas viram `#`).
- NÃO verificado: link do parceiro (provisório); se o formulário do parceiro aceita pré-preenchimento; prazo máximo, mínimo e teto reais; se o parceiro oferece SAC; texto jurídico (alienação fiduciária de bem móvel, busca e apreensão, quitação antecipada) sem revisão jurídica; iPhone/Safari físico; `varredura_dispositivos.py` rodou com os mesmos achados genéricos do 006 (rótulos pequenos como "alvos de toque", e o Playwright-WebKit não tira print de página inteira com DPR 3 por passar de 32767 px) — não comparado linha a linha com o 006; a data "19/11/2026" em `/atualizacoes` é a de criação, ajustar na publicação; o texto de `/atualizacoes` descreve a primeira versão.
- Antes de publicar: confirmar link, decidir `UMAMI_ID`, criar repo `rldelfino/pseo-simulador-autoequity`, dar acesso do app Cloudflare ao repo, Pages com saída `paginas_seo`, domínio `autoequity.datalabglobal.com`, linkar no hub e nos rodapés dos irmãos (006 já tem o link do Auto Equity? não: acrescentar), Search Console/Bing/IndexNow.
