import os
import json
import re


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    dates = []
    for name in os.listdir(root):
        if date_re.match(name):
            path = os.path.join(root, name, f"portfolio_snapshot_{name}.json")
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r") as f:
                    snap = json.load(f)
                nl = float(snap.get("net_liquidation", snap.get("portfolio_value", 0.0)))
                dates.append((name, nl))
            except Exception:
                pass

    dates.sort(key=lambda x: x[0])
    results_dir = os.path.join(root, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Net liquidation CSV
    with open(os.path.join(results_dir, "net_liquidation.csv"), "w") as f:
        f.write("date,net_liquidation\n")
        for d, v in dates:
            f.write(f"{d},{v}\n")

    # Try to write a PNG if matplotlib exists
    try:
        import matplotlib.pyplot as plt
        import datetime as _dt

        dts = [_dt.datetime.strptime(d, "%Y-%m-%d") for d, _ in dates]
        vals = [v for _, v in dates]
        if dts:
            plt.figure(figsize=(10, 4))
            plt.plot(dts, vals, lw=1.8)
            plt.grid(True, alpha=0.3)
            plt.title("Net Liquidation")
            plt.xlabel("Date")
            plt.ylabel("Net Liq")
            plt.tight_layout()
            plt.savefig(os.path.join(results_dir, "net_liquidation.png"))
            plt.close()
    except Exception:
        pass

    # Top gainers/losers on latest observation per ticker
    latest = {}
    for name, _ in dates:
        path = os.path.join(root, name, f"portfolio_snapshot_{name}.json")
        try:
            with open(path, "r") as f:
                snap = json.load(f)
            port = snap.get("portfolio", {})
            for t, info in port.items():
                qty = float(info.get("totalAmount", 0))
                if qty <= 0:
                    continue
                last = float(info.get("last_price", 0))
                entry = float(info.get("entry_price", 0)) or last
                # Keep latest date entry
                if t not in latest or name > latest[t]["date"]:
                    latest[t] = {"date": name, "qty": qty, "last": last, "entry": entry}
        except Exception:
            pass

    items = []
    for t, data in latest.items():
        entry = data["entry"]
        last = data["last"]
        ret = (last / entry - 1.0) if entry > 0 else 0.0
        items.append((t, ret, entry, last, data["qty"]))

    items.sort(key=lambda x: x[1], reverse=True)
    gainers = items[:20]
    losers = sorted(items, key=lambda x: x[1])[:20]

    with open(os.path.join(results_dir, "top_gainers.csv"), "w") as f:
        f.write("ticker,return,entry,last,qty\n")
        for t, r, e, l, q in gainers:
            f.write(f"{t},{r},{e},{l},{q}\n")

    with open(os.path.join(results_dir, "top_losers.csv"), "w") as f:
        f.write("ticker,return,entry,last,qty\n")
        for t, r, e, l, q in losers:
            f.write(f"{t},{r},{e},{l},{q}\n")

    print("Wrote:")
    print(" - results/net_liquidation.csv")
    print(" - results/net_liquidation.png (if matplotlib available)")
    print(" - results/top_gainers.csv")
    print(" - results/top_losers.csv")


if __name__ == "__main__":
    main()


