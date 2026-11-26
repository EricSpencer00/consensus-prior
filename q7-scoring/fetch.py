"""Fetch resolved Polymarket 'Bitcoin above ___ on <date>?' events (read-only public API)
plus Coinbase hourly BTC-USD candles. Writes data/markets.csv and data/btc_hourly.csv."""
import csv, datetime as dt, json, re, sys, time, urllib.request

GAMMA = "https://gamma-api.polymarket.com/events?slug="
CLOB = "https://clob.polymarket.com/prices-history"
CB = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
START, END = dt.date(2025, 7, 15), dt.date(2025, 11, 30)
LEAD_H = 24  # forecast made this many hours before resolution


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-script"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 + 2 * i)
    raise RuntimeError(url)


def ts(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def markets():
    rows = []
    d = START
    while d <= END:
        slug = f"bitcoin-above-on-{d.strftime('%B').lower()}-{d.day}"
        ev = get(GAMMA + slug)
        d += dt.timedelta(days=1)
        if not ev or not ev[0]["endDate"].startswith(str(d.year)):
            print("skip", slug, file=sys.stderr); continue
        e = ev[0]
        t_res = ts(e["endDate"]); t_fc = t_res - LEAD_H * 3600
        for m in e["markets"]:
            if not m.get("closed") or m.get("umaResolutionStatus") != "resolved":
                continue
            prices = json.loads(m["outcomePrices"])
            if prices not in (["1", "0"], ["0", "1"]):
                continue
            k = re.search(r"above \$([\d,.]+)([kK]?)", m["question"])
            if not k:
                continue
            strike = float(k.group(1).replace(",", "")) * (1000 if k.group(2) else 1)
            yes_tok = json.loads(m["clobTokenIds"])[0]
            h = get(f"{CLOB}?market={yes_tok}&startTs={t_fc - 6*3600}&endTs={t_fc}&fidelity=10")["history"]
            if not h:
                continue
            rows.append(dict(date=e["endDate"][:10], t_res=t_res, t_fc=t_fc,
                             strike=strike,
                             p_mkt=h[-1]["p"], p_mkt_ts=h[-1]["t"], y=int(prices[0] == "1")))
        print(slug, len(rows), file=sys.stderr)
    return rows


def candles():
    out = {}
    t0 = dt.datetime.combine(START - dt.timedelta(days=40), dt.time(), dt.timezone.utc)
    t1 = dt.datetime.combine(END + dt.timedelta(days=2), dt.time(), dt.timezone.utc)
    while t0 < t1:
        t2 = min(t0 + dt.timedelta(hours=300), t1)
        for c in get(f"{CB}?granularity=3600&start={t0.isoformat()}&end={t2.isoformat()}"):
            out[c[0]] = c[4]  # open-time -> close
        t0 = t2; time.sleep(0.3)
    return sorted(out.items())


if __name__ == "__main__":
    rows = markets()
    with open("data/markets.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open("data/btc_hourly.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_open", "close"]); w.writerows(candles())
