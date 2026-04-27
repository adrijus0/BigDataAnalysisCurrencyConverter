# Flask API for currency conversion using the Frankfurter API
from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

FRANKFURTER_BASE = "https://api.frankfurter.app"


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "currency-converter"}), 200


@app.route("/currencies")
def currencies():
    try:
        resp = requests.get(f"{FRANKFURTER_BASE}/currencies", timeout=10)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch currencies from upstream", "detail": str(e)}), 502

    if not resp.ok:
        return jsonify({"error": "Failed to fetch currencies from upstream", "detail": resp.text}), 502

    return jsonify({"currencies": resp.json()}), 200


@app.route("/rates")
def rates():
    base = request.args.get("base")
    # don't call the API if base wasn't provided
    if not base:
        return jsonify({"error": "Missing required query parameter: base"}), 400

    try:
        resp = requests.get(f"{FRANKFURTER_BASE}/latest", params={"from": base}, timeout=10)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch rates from upstream", "detail": str(e)}), 502

    # 404 or 422 from frankfurter means bad currency code
    if not resp.ok:
        if resp.status_code in (404, 422):
            return jsonify({"error": "Invalid currency code", "detail": f"{base} is not a supported currency"}), 400
        return jsonify({"error": "Failed to fetch rates from upstream", "detail": resp.text}), 502

    data = resp.json()
    return jsonify({"base": data["base"], "date": data["date"], "rates": data["rates"]}), 200


@app.route("/convert")
def convert():
    # check all params are present before doing anything
    for param in ("amount", "from", "to"):
        if request.args.get(param) is None:
            return jsonify({"error": f"Missing required query parameter: {param}"}), 400

    raw_amount = request.args.get("amount")
    from_currency = request.args.get("from").upper()
    to_currency = request.args.get("to").upper()

    # make sure amount is actually a number and positive
    try:
        amount = float(raw_amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid amount: must be a positive number"}), 400

    # catch this before sending to the API, it doesn't handle same-currency well
    if from_currency == to_currency:
        return jsonify({"error": "from and to currencies must be different"}), 400

    try:
        resp = requests.get(
            f"{FRANKFURTER_BASE}/latest",
            params={"amount": amount, "from": from_currency, "to": to_currency},
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch conversion from upstream", "detail": str(e)}), 502

    if not resp.ok:
        if resp.status_code in (404, 422):
            # try to get the error message out of the response, but the body might not be JSON
            try:
                detail = resp.json().get("message", f"{from_currency} or {to_currency} is not a supported currency")
            except ValueError:
                detail = f"{from_currency} or {to_currency} is not a supported currency"
            return jsonify({"error": "Invalid currency code", "detail": detail}), 400
        return jsonify({"error": "Failed to fetch conversion from upstream", "detail": resp.text}), 502

    data = resp.json()
    result = data["rates"].get(to_currency)

    return jsonify({
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "result": result,
        "date": data["date"],
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
