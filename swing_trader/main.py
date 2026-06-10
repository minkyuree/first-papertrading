import sys
from trader import notify
from trader.data import fetch_price_data, compute_indicators, get_market_filter
from trader.signals import scan_buy_signals
from trader.orders import get_positions, check_trailing_stops, execute_sells, execute_buys

DRY_RUN = True   # GitHub Actions에서 False로 바꾸면 실제 paper trading 주문 실행


def main():
    print("=" * 50)
    print("🚀 스윙 트레이더 시작")
    print("=" * 50)

    notify.notify_start()

    try:
        # ── 1) 데이터 & 지표 ──────────────────────────────
        price_data = fetch_price_data()
        indicators = compute_indicators(price_data)

        # ── 2) 시장 필터 ──────────────────────────────────
        print("\n📊 시장 상태 확인")
        mf = get_market_filter()
        print(f"SPY ${mf['spy_price']} / 200MA ${mf['spy_ma']} → {'✅' if mf['spy_ok'] else '❌'}")
        print(f"VIX {mf['vix']} → {'✅' if mf['vix_ok'] else '❌'}")
        print(f"시장 필터: {'✅ 허용' if mf['market_ok'] else '❌ 차단'}")
        notify.notify_market(mf)

        # ── 3) 현재 포지션 조회 ───────────────────────────
        print("\n📋 포지션 조회")
        positions_df = get_positions()
        if not positions_df.empty:
            print(positions_df[["ticker", "avg_cost", "current_price", "pnl_pct"]].to_string(index=False))
        else:
            print("보유 포지션 없음")

        # ── 4) 트레일링 스탑 체크 & 청산 ─────────────────
        print("\n🔍 트레일링 스탑 체크")
        exit_list    = check_trailing_stops(indicators, positions_df)
        sell_results = execute_sells(exit_list, dry_run=DRY_RUN)
        notify.notify_exits(exit_list, sell_results)

        # ── 5) 매수 신호 스캔 & 주문 ─────────────────────
        print("\n📡 매수 신호 스캔")
        signals = scan_buy_signals(indicators, mf["market_ok"])
        notify.notify_signals(signals)

        print("\n📥 매수 주문")
        buy_results, portfolio_val, cash = execute_buys(
            signals, positions_df, dry_run=DRY_RUN
        )
        notify.notify_buys(buy_results, portfolio_val, cash)

        # ── 6) 완료 ───────────────────────────────────────
        print("\n✅ 완료")
        notify.notify_done(DRY_RUN)

    except Exception as e:
        print(f"\n🚨 오류: {e}")
        notify.notify_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
