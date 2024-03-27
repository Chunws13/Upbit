import pyupbit, datetime, time
from market_research import check_bull_market

def target_buy_amount(coin, target_date):
    from_date = target_date - datetime.timedelta(days=10)
    try:
        coin_data = pyupbit.get_ohlcv_from(ticker=coin, fromDatetime=from_date, to=target_date)
        time.sleep(0.5)
        coin_data['noise'] = 1 - abs(coin_data['open'] - coin_data['close']) / (coin_data['high'] - coin_data['low'])
        coin_data['noise_ma_20'] = coin_data['noise'].rolling(window=5).mean().shift(1)

        coin_data['variance_ragne'] = coin_data['high'] - coin_data['low']
        coin_data['target_price'] = coin_data['open'] + coin_data['variance_ragne'].shift(1) * coin_data['noise_ma_20']
        
        target_price = coin_data['target_price'].iloc[-1]

        return target_price
    
    except:
        print(coin, coin_data)
        return None


if __name__ == "__main__":
    # print(target_buy_amount(coin = "KRW-BTC", target_date= datetime.datetime.now()))
    # print(pyupbit.get_current_price("KRW-BTC"))
    day = datetime.datetime(2023, 9, 29)
    coin = ["KRW-ONT", "KRW-ELF"]
    
    print(target_buy_amount("KRW-ONT", day))