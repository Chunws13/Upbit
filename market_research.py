import pyupbit, re, heapq, time, datetime

def check_bull_market(target_date): # 16 seconds
    KRW_CHECKER = "KRW-"
    from_date = target_date - datetime.timedelta(days=7)

    ticker_list = pyupbit.get_tickers()
    bull_market = []

    for ticker in ticker_list:
        if re.match(KRW_CHECKER, ticker):
            ma_flow_info = pyupbit.get_ohlcv_from(ticker=ticker, fromDatetime=from_date, to=target_date)

            if ma_flow_info is not None:
                ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=1).mean().shift(1)
                
                if ma_flow_info["open"].iloc[-1] > ma_flow_info["ma5"].iloc[-1]:
                    bull_market.append(ticker)

            time.sleep(0.1)

    return bull_market

def select_coin_market(bull_market, target_date, invest_number): # 16 seconds
    investment_target = []
    from_date = target_date - datetime.timedelta(days=1)

    for bull in bull_market:
        volume_24H = pyupbit.get_ohlcv_from(ticker=bull, interval="minute60", fromDatetime=from_date, to=target_date)
        print(volume_24H)
        if volume_24H is not None:
            volume_sum = volume_24H["value"].sum()
            if len(investment_target) < invest_number:
                heapq.heappush(investment_target, [volume_sum, bull])
                continue

            if investment_target[0][0] < volume_sum:
                heapq.heappop(investment_target)
                heapq.heappush(investment_target, [volume_sum, bull])

        time.sleep(0.1)

    return investment_target

if __name__ == "__main__":
    select_coin_market(["KRW-BTC"], datetime.datetime.now(), 1)
