import pyupbit, datetime, time, numpy
from market_research import check_bull_market

def target_buy_amount(coin, target_date):
    
    try:
        from_date = target_date - datetime.timedelta(days=10)
        coin_data = None
        while coin_data is None:
            coin_data = pyupbit.get_ohlcv_from(ticker=coin, fromDatetime=from_date, to=target_date)
            time.sleep(0.5)
        
        coin_data['noise'] = 1 - abs(coin_data['open'] - coin_data['close']) / (coin_data['high'] - coin_data['low'])
        coin_data['noise_ma_5'] = coin_data['noise'].rolling(window=5).mean().shift(1)
        
        coin_data['variance_range'] = coin_data['high'] - coin_data['low']
        coin_data['target_price'] = coin_data['open'] + coin_data['variance_range'].shift(1) * coin_data['noise_ma_5']
        
        target_price = coin_data['target_price'].iloc[-1]

        return target_price
    
    except:
        return numpy.nan


if __name__ == "__main__":
    day = datetime.datetime(2023, 10, 1)
    coin_list = ["KRW-MLK", "KRW-STX"]

    test_invest_coint = check_bull_market(target_date=day, invest_number=4)
    for c in test_invest_coint:
        print(c, target_buy_amount(coin=c, target_date=day))
        # print(test_invest_coint)
    