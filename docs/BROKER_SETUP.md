# Broker Setup Guide

## MetaTrader 5 (MT5)

ORVO integrates with MT5 using the **official** `MetaTrader5` Python package
(https://pypi.org/project/MetaTrader5/), maintained by MetaQuotes themselves. This is
the real, supported way to programmatically trade on MT5 — there is no public "MT5 API"
independent of this package and a running terminal.

### Hard requirements (not ORVO limitations — MetaTrader5 package limitations)
- **Windows only.** The package wraps a native DLL that ships with the Windows MT5
  terminal. It does not work on macOS or Linux, including inside Docker containers,
  unless you run it under Wine (unsupported/unreliable) or a Windows VM.
- **A MetaTrader 5 terminal must be installed** on the same machine running ORVO's
  backend, and you must be able to log into your broker account from that terminal.
- **Your broker must support MT5** (most forex/CFD brokers do; check with yours).

### Steps
1. Install the MetaTrader 5 terminal from your broker (or from metatrader5.com) on a
   Windows machine.
2. Log into your account once inside the terminal itself to confirm your credentials
   and server name work.
3. On that same Windows machine, install ORVO's backend (see `docs/INSTALLATION.md`)
   and uncomment `MetaTrader5==5.0.4874` in `backend/requirements.txt`, then
   `pip install MetaTrader5`.
4. In ORVO, go to **Settings → Broker Connection**, enter your MT5 login, password,
   and server name (exactly as shown in the terminal's login window), and click Connect.
5. ORVO calls `mt5.initialize()` and `mt5.login()` for real — if it fails, the exact
   MT5 error is shown in the UI (e.g. wrong password, wrong server, terminal not found).
   Nothing is silently faked as "connected."

### Running ORVO on Linux/macOS but trading via MT5
Run ORVO's backend on a small Windows VPS instead (many providers offer these cheaply),
or keep ORVO on Linux for the web app and run a lightweight bridge service on a Windows
box that exposes MT5 over HTTP for ORVO to call — this is a common pattern but requires
you to build/host that bridge separately; it's outside what a single Python package can
solve.

## Alternative: brokers with a real REST API (cross-platform)

If you don't want to be tied to Windows, use a broker with a native HTTPS API instead:
- **OANDA** (forex/CFDs) — https://developer.oanda.com — free demo + live REST API
- **Alpaca** (US stocks/crypto) — https://alpaca.markets/docs — free REST API
- **Interactive Brokers** — has a REST/WebSocket gateway (more setup, very capable)

`backend/app/broker/mt5_connector.py` defines the connector interface
(`connect`, `place_order`, `close_order`, `modify_order`, `get_account_snapshot`).
To add one of these, create a sibling file (e.g. `oanda_client.py`) implementing the
same functions against that broker's real API, then extend `BrokerType` in
`backend/app/models.py` and the branching logic in `backend/app/routers/trading.py`
and `backend/app/routers/broker.py`. This is a genuine coding task (a few hours of
work) — not something that can be faked into working without real credentials either way.

## Credential security

Broker credentials you enter are encrypted at rest with Fernet symmetric encryption
(`backend/app/security.py`), using a key derived from your `SECRET_KEY`. They are
decrypted only in-memory when needed to reconnect. Treat `SECRET_KEY` itself as a secret —
if it leaks, encrypted credentials in the database can be decrypted.
