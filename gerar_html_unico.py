"""Gera um ÚNICO arquivo HTML (CSS, fontes, calculo.js, simulador.js e menu.js embutidos) a partir de paginas_seo/, para o dono abrir a tela de teste sem servidor.

Só a home vai no arquivo: links para as outras páginas viram "#" (elas só existem no site publicado). O Umami é removido (a tela de teste não mede nada).
Uso: python gerar_html_unico.py [saida.html]   (padrão: auto-equity-teste-v1.html na pasta do projeto)
"""
import base64
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, "paginas_seo")


def ler(nome):
    with open(os.path.join(PASTA, nome), encoding="utf-8") as f:
        return f.read()


def gerar():
    h = ler("index.html")
    css = ler("styles.css")

    def fonte(m):
        with open(os.path.join(PASTA, m.group(1).lstrip("/")), "rb") as f:
            return "url(data:font/woff2;base64," + base64.b64encode(f.read()).decode() + ")"

    css = re.sub(r"url\(['\"]?(/?fonts/[^)'\"]+)['\"]?\)", fonte, css)
    h = re.sub(r'<link rel="preload"[^>]*>', "", h)
    h = re.sub(r'<link rel="stylesheet" href="/styles.css[^"]*">', lambda m: "<style>" + css + "</style>", h)
    h = re.sub(r'<script defer src="https://cloud.umami.is[^>]*></script>', "", h)
    for js in ("calculo.js", "simulador.js", "menu.js"):
        c = ler(js)
        h = re.sub(r'<script( defer)? src="/' + js + r'[^"]*"></script>', lambda m: "<script>" + c.replace("</script", "<\\/script") + "</script>", h)
    h = h.replace('href="/#simulador"', 'href="#simulador"')
    h = re.sub(r'<link rel="(icon|apple-touch-icon|canonical|alternate)"[^>]*>', "", h)
    h = re.sub(r'href="/(?!/)[^"]*"', 'href="#"', h)  # páginas internas: só existem no site publicado
    return h


if __name__ == "__main__":
    saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "auto-equity-teste-v1.html")
    html = gerar()
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(saida, len(html), "bytes")
