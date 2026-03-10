import pyupbit
import pandas as pd
import datetime
import time

def run_final_refined_backtest():
    # 1. 설정: 종목별 차등 K값 및 비중 설정
    # 전략: BTC는 비중을 높이고(50%) K값을 낮춰(0.4) 안정적 추세 추종
    # 알트 메이저는 K값을 높여(0.6) 노이즈를 걸러냄
    strategy_config = {
        "KRW-BTC": {"k": 0.4, "weight": 0.5},   # 시드의 50%
        "KRW-ETH": {"k": 0.6, "weight": 0.16},  # 약 16.6%
        "KRW-XRP": {"k": 0.6, "weight": 0.17},  # 약 16.6%
        "KRW-SOL": {"k": 0.6, "weight": 0.17}   # 약 16.6%
    }
    
    tickers = list(strategy_config.keys())
    fee = 0.0011 
    initial_budget = 1000000
    current_budget = initial_budget
    duration_days = 365

    print(f"데이터 수집 중... ({duration_days}일)")
    df_dict = {}
    for ticker in tickers:
        df = pyupbit.get_ohlcv(ticker, interval="day", count=duration_days + 1)
        if df is not None:
            df_dict[ticker] = df
        time.sleep(0.1)

    # 시작일 (어제 데이터가 있는 날부터)
    all_dates = df_dict["KRW-BTC"].index[1:]
    daily_stats = []

    print(f"최종 전략 백테스팅 시작... (기간: {len(all_dates)}일)")

    for i in range(1, len(df_dict["KRW-BTC"])):
        date = df_dict["KRW-BTC"].index[i]
        total_profit_day = 0
        
        day_report = f"[{date.strftime('%Y-%m-%d')}] "
        
        for ticker in tickers:
            df = df_dict[ticker]
            if date not in df.index: continue
            
            # 전략 파라미터 로드
            k = strategy_config[ticker]["k"]
            weight = strategy_config[ticker]["weight"]
            investment_amount = current_budget * weight
            
            # 전일 데이터
            prev_high = df['high'].iloc[i-1]
            prev_low = df['low'].iloc[i-1]
            prev_range = prev_high - prev_low
            
            # 당일 데이터
            today_open = df['open'].iloc[i]
            today_high = df['high'].iloc[i]
            today_close = df['close'].iloc[i]
            
            target_price = today_open + prev_range * k
            
            if today_high >= target_price:
                # 수익률 계산
                profit_rate = (today_close / target_price) - 1 - fee
                profit = investment_amount * profit_rate
                total_profit_day += profit
                day_report += f"{ticker}({profit_rate*100:.1f}%) "
            else:
                day_report += f"{ticker}(No) "
        
        current_budget += total_profit_day
        day_report += f"| Day: {total_profit_day:,.0f} | Bal: {current_budget:,.0f}"
        daily_stats.append(day_report)

    # 결과 요약
    final_profit_rate = (current_budget - initial_budget) / initial_budget * 100
    
    report = []
    report.append("==========================================")
    report.append("     최종 최적화 전략 1년 백테스팅 결과")
    report.append("==========================================")
    report.append(f"테스트 기간: {all_dates[0].strftime('%Y-%m-%d')} ~ {all_dates[-1].strftime('%Y-%m-%d')}")
    report.append(f"전략 설정:")
    report.append(f" - BTC: K=0.4, 비중 50%")
    report.append(f" - ETH/XRP/SOL: K=0.6, 비중 각 16.6%")
    report.append(f"시작 금액: {initial_budget:,.0f} KRW")
    report.append(f"종료 금액: {current_budget:,.0f} KRW")
    report.append(f"누적 수익률: {final_profit_rate:.2f}%")
    report.append("------------------------------------------")
    report.append("최근 10일 요약:")
    for line in daily_stats[-10:]:
        report.append(line)
    
    with open("back_test/backtest_result_final_optimized.txt", "w", encoding="utf-8") as f:
        for line in report:
            f.write(line + "\n")
        f.write("\n--- 상세 내역 ---\n")
        for line in daily_stats:
            f.write(line + "\n")

    return "\n".join(report)

if __name__ == "__main__":
    summary = run_final_refined_backtest()
    print(summary)
