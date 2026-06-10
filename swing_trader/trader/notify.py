import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from trader.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

ET = ZoneInfo("America/New_York")


def _send(text):
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}")


def notify_start():
    now = datetime.now(ET).strftime("%Y-%m-%d %H:%M ET")
    _send(f"🚀 <b>스윙 트레이더 시작</b>\n{now}")


def notify_market(mf):
    spy_emoji = "✅" if mf["spy_ok"] else "❌"
    vix_emoji = "✅" if mf["vix_ok"] else "❌"
    gate      = "✅ 진입 허용" if mf["market_ok"] else "❌ 진입 차단"

    msg = (
        f"📊 <b>시장 필터</b>\n"
        f"SPY  : ${mf['spy_price']} (200MA: ${mf['spy_ma']}) {spy_emoji}\n"
        f"VIX  : {mf['vix']} {vix_emoji}\n"
        f"결과 : {gate}"
    )
    _send(msg)


def notify_signals(signals):
    if not signals:
        _send("📭 매수 신호 없음")
        return
    lines = [f"📡 <b>매수 신호 {len(signals)}개</b>"]
    for s in signals:
        lines.append(
            f"  • <b>{s['ticker']}</b> ${s['close']} | "
            f"돌파 {s['breakout_pct']:+.2f}% | "
            f"스탑 ${s['stop_price']}"
        )
    _send("\n".join(lines))


def notify_exits(exit_list, sell_results):
    if not exit_list:
        _send("📭 청산 대상 없음")
        return
    lines = [f"📤 <b>청산 {len(exit_list)}건</b>"]
    status_map = {r["ticker"]: r["status"] for r in sell_results}
    for item in exit_list:
        status = status_map.get(item["ticker"], "?")
        emoji  = "✅" if status == "OK" else ("🔵" if status == "DRY_RUN" else "❌")
        lines.append(
            f"  {emoji} <b>{item['ticker']}</b> "
            f"${item['current_price']} | "
            f"스탑 ${item['stop_price']} | "
            f"손익 {item['pnl_pct']:+.2f}%"
        )
    _send("\n".join(lines))


def notify_buys(buy_results, portfolio_val, cash):
    if not buy_results:
        _send("📭 매수 주문 없음")
        return
    lines = [f"📥 <b>매수 {len(buy_results)}건</b>"]
    for r in buy_results:
        if r["status"] == "OK":
            emoji = "✅"
        elif r["status"] == "DRY_RUN":
            emoji = "🔵"
        elif r["status"] == "SKIP_CASH":
            emoji = "⛔"
        else:
            emoji = "❌"
        lines.append(
            f"  {emoji} <b>{r['ticker']}</b> "
            f"${r.get('notional', 0):,.0f}"
            + (f" | {r['error']}" if r.get("error") else "")
        )
    lines.append(f"\n💰 포트폴리오: ${portfolio_val:,.0f} | 현금: ${cash:,.0f}")
    _send("\n".join(lines))


def notify_error(e):
    _send(f"🚨 <b>오류 발생</b>\n{type(e).__name__}: {e}")


def notify_done(dry_run):
    mode = "🔵 DRY RUN" if dry_run else "🔴 LIVE"
    _send(f"✅ <b>완료</b> ({mode})")
