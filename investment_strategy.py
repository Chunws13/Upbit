import pyupbit, datetime

def target_buy_amount(coin, target_date):
    from_date = target_date - datetime.timedelta(days=42)
    coin_data = pyupbit.get_ohlcv_from(ticker=coin, fromDatetime=from_date, to=target_date)

    coin_data['noise'] = 1 - abs(coin_data['open'] - coin_data['close']) / (coin_data['high'] - coin_data['low'])
    coin_data['noise_ma_20'] = coin_data['noise'].rolling(window=20).mean().shift(1)

    coin_data['variance_ragne'] = coin_data['high'] - coin_data['low']
    coin_data['target_price'] = coin_data['open'] + coin_data['variance_ragne'].shift(1) * coin_data['noise_ma_20']
    
    return coin_data['target_price'].iloc[-1]


if __name__ == "__main__":
    print(target_buy_amount("KRW-BTC"))
    print(pyupbit.get_current_price("KRW-BTC"))