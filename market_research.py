import pyupbit, re, heapq, time, datetime, math

def check_bull_market(target_date, invest_number): # 16 seconds
    KRW_CHECKER = "KRW-"
    from_date = target_date - datetime.timedelta(days=21)

    ticker_list = pyupbit.get_tickers()
    bull_market = []

    for ticker in ticker_list:
        if re.match(KRW_CHECKER, ticker):
            ma_flow_info = pyupbit.get_ohlcv_from(ticker=ticker, fromDatetime=from_date, to=target_date)
            
            if ma_flow_info is None:
                continue

            ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=1).mean().shift(1)
            ma_flow_info["ma20"] = ma_flow_info["close"].rolling(window=20, min_periods=1).mean().shift(1)

            upward_trend = ma_flow_info["ma5"].iloc[-1] >= ma_flow_info["ma20"].iloc[-1]
            bull_check = ma_flow_info["open"].iloc[-1] > ma_flow_info["ma5"].iloc[-1]
            
            diff_info = ma_flow_info["close"].diff()
            
            gain = (diff_info.where(diff_info > 0, 0)).rolling(window=7).mean().shift(1)
            loss = (-diff_info.where(diff_info < 0, 0)).rolling(window=7).mean().shift(1)

            rsi_data_frame = 100 - (100 / (1 + (gain / loss)))
            rsi = rsi_data_frame.iloc[-1]
            
            if math.isnan(rsi):
                continue

            if bull_check and upward_trend:
                if len(bull_market) < invest_number:
                    heapq.heappush(bull_market, [-rsi, ticker])
                    continue

                if -rsi > bull_market[0][0]:
                    heapq.heappush(bull_market, [-rsi, ticker])
                    heapq.heappop(bull_market)

            time.sleep(0.1)

    result = []

    while bull_market:
        rsi, ticker = heapq.heappop(bull_market)
        result.append(ticker)

    return result

def select_coin_market(bull_market, target_date, invest_number): # 16 seconds
    investment_target = []
    from_date = target_date - datetime.timedelta(days=1)

    for bull in bull_market:
        volume_24H = pyupbit.get_ohlcv_from(ticker=bull, interval="minute60", fromDatetime=from_date, to=target_date)
        # print(volume_24H)
        if volume_24H is not None:
            volume_sum = volume_24H["value"].sum()
            if len(investment_target) < invest_number:
                heapq.heappush(investment_target, [volume_sum, bull])
                continue

            if investment_target[0][0] < volume_sum:
                heapq.heappop(investment_target)
                heapq.heappush(investment_target, [volume_sum, bull])
        
        time.sleep(0.1)
    
    result = []
    while investment_target:
        total_price, coin_name = heapq.heappop(investment_target)
        result.append(coin_name)

    return result

if __name__ == "__main__":
    # test_coin_list = check_bull_market(datetime.datetime.now(),2)
    # print(test_coin_list)
    # test_invest_coint = select_coin_market(bull_market=test_coin_list, target_date=datetime.datetime.now(), invest_number=2)
    # print(test_invest_coint)
    pass