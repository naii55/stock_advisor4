from flask import Flask, render_template, request, send_file
import yfinance as yf
import csv
import pandas as pd
from io import StringIO

app = Flask(__name__)
latest_results = []

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")

        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        dividend = info.get("dividendYield")
        sector = info.get("sector", "ไม่ระบุ")
        market_cap = info.get("marketCap")
        pb = info.get("priceToBook")
        beta = info.get("beta")
        current_price = info.get("currentPrice")

        summary = []

        if pe and pe < 15:
            summary.append("✅ P/E ต่ำ (ราคายังไม่แพง)")
        elif pe and pe > 25:
            summary.append("⚠️ P/E สูง (อาจแพง)")

        if roe and roe > 0.15:
            summary.append("✅ ROE สูง (บริหารดี)")
        elif roe:
            summary.append("⚠️ ROE ต่ำ")

        if dividend and dividend > 0.03:
            summary.append("✅ ปันผลสูง")
        else:
            summary.append("ℹ️ ปันผลต่ำ")

        result = {
            "symbol": ticker,
            "sector": sector,
            "pe": pe,
            "roe": f"{roe * 100:.2f}%" if roe else "N/A",
            "dividend": f"{dividend * 100:.2f}%" if dividend else "N/A",
            "market_cap": f"{market_cap:,}" if market_cap else "N/A",
            "pb": pb,
            "beta": beta,
            "current_price": f"{current_price:.2f}" if current_price else "N/A",
            "summary": summary,
            "history": hist["Close"].round(2).to_dict()
        }

        return result

    except Exception as e:
        return {
            "symbol": ticker,
            "sector": "ไม่พบข้อมูล",
            "pe": "N/A",
            "roe": "N/A",
            "dividend": "N/A",
            "market_cap": "N/A",
            "pb": "N/A",
            "beta": "N/A",
            "current_price": "N/A",
            "summary": [f"❌ เกิดข้อผิดพลาด: {e}"],
            "history": {}
        }

@app.route("/", methods=["GET", "POST"])
def index():
    global latest_results
    results = []
    tickers = []

    if request.method == "POST":
        mode = request.form.get("mode")
        sector_filter = request.form.get("sector", "").strip()

        if mode == "manual":
            tickers = request.form["tickers"].split(",")
            tickers = [t.strip().upper() for t in tickers if t.strip()]
        elif mode == "all":
            with open("all_stocks.csv", newline='') as f:
                reader = csv.reader(f)
                tickers = [row[0].strip().upper() for row in reader if row]

        for ticker in tickers:
            result = analyze_stock(ticker)
            if not sector_filter or sector_filter.lower() in result["sector"].lower():
                results.append(result)

        latest_results = results

    return render_template("index.html", results=results)

@app.route("/export")
def export_csv():
    global latest_results
    df = pd.DataFrame(latest_results)
    csv_data = df.to_csv(index=False)

    return send_file(
        StringIO(csv_data),
        mimetype="text/csv",
        download_name="stock_results.csv",
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True)
