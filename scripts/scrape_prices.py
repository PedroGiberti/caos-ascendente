#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robô de preços — Caos Ascendente (ME04) / mercado BR.

Puxa 1 página do Deck Certo (HTML puro, sem JS, sem anti-bot) e extrai o preço
em R$ das 122 cartas do set. Gera/atualiza prices.json na raiz do repositório.

Só usa biblioteca padrão do Python (nada de pip install).
Roda sozinho pelo GitHub Action em .github/workflows/prices.yml.

Fonte: https://deckcerto.com/pokemon-tcg/todas-cartas-caos-ascendente/
Preço = "versão comum (Normal)" praticada no mercado brasileiro.
"""

import json
import re
import sys
import datetime
import urllib.request

URL = "https://deckcerto.com/pokemon-tcg/todas-cartas-caos-ascendente/"
OUT = "prices.json"
MIN_CARDS = 100  # se vier menos que isso, algo quebrou — aborta sem sobrescrever

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 "
      "caos-ascendente-tracker/1.0 (coleção pessoal)")


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    return raw.decode("utf-8", "replace")


def parse_prices(html):
    # tira as tags e normaliza espaços -> vira texto corrido
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    prices = {}
    # padrão estável: "NNN/086 R$ X,XX" (aceita milhar com ponto: 1.234,56)
    for m in re.finditer(r"(\d{3})\s*/\s*086\s*R\$\s*([\d.]*\d,\d{2})", text):
        num = m.group(1)
        val = float(m.group(2).replace(".", "").replace(",", "."))
        # mantém o primeiro (a galeria lista cada carta uma vez)
        prices.setdefault(num, val)
    return prices


def main():
    try:
        html = fetch(URL)
    except Exception as e:
        print("ERRO ao baixar a fonte:", e, file=sys.stderr)
        return 1

    prices = parse_prices(html)
    if len(prices) < MIN_CARDS:
        print("ERRO: só %d cartas parseadas (esperado ~122). "
              "O layout da fonte pode ter mudado — prices.json NÃO foi alterado."
              % len(prices), file=sys.stderr)
        return 1

    out = {
        "_updated": datetime.date.today().isoformat(),
        "_source": "deckcerto.com",
        "_note": "preco versao comum (Normal), mercado BR em R$",
        "prices": dict(sorted(prices.items())),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("OK: %d precos salvos em %s (atualizado %s)"
          % (len(prices), OUT, out["_updated"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
