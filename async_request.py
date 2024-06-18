import aiohttp, asyncio
import pandas, pyupbit
import datetime

def data_format(response_data):
    ticker_data = {"date": [], "open": [], "close": [], "low": [], "high": [], "volume": []}

    for data in response_data[::-1]:
        ticker_data["date"] += [data["candle_date_time_kst"]]
        ticker_data["open"] += [data["opening_price"]]
        ticker_data["close"] += [data["trade_price"]]
        ticker_data["low"] += [data["low_price"]]
        ticker_data["high"] += [data["high_price"]]
        ticker_data["volume"] += [data["candle_acc_trade_volume"]]

    df = pandas.DataFrame(ticker_data)
    df['date'] = pandas.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df


async def fetch_price(session, ticker, date):
    url = f"https://api.upbit.com/v1/candles/days"
    params = {
        'market': ticker,
        'to': date.strftime("%Y-%m-%dT%H:%M:%S"),
        'count': 200
    }

    async with session.get(url, params=params) as response:
        data = await response.json()

        if response.status == 429:
            await asyncio.sleep(1)
            return await fetch_price(session, ticker, date)
        
        # print(data)
        data_frame = data_format(data)
        return [ticker, data_frame]
    

async def fetch_prices(tickers, end_date):
    async with aiohttp.ClientSession() as session:
        tasks = []
        dictionary_info = {}

        for ticker in tickers:
            tasks.append(fetch_price(session, ticker, end_date))

        prices = await asyncio.gather(*tasks)
        for price in prices:
            dictionary_info[price[0]] = price[1]

        return dictionary_info

def get_ticekr_info(target_date):
    tickers = pyupbit.get_tickers("KRW")
    tickers_info = asyncio.run(fetch_prices(tickers, target_date))
    return tickers_info

if __name__ == "__main__":
    start = datetime.datetime.now()
    tickers_info = get_ticekr_info(datetime.datetime(2024, 6, 19))
    for ticker in tickers_info:
        print(ticker, tickers_info[ticker].iloc[-1])
    end = datetime.datetime.now()

    print(f"running time: {end - start}")
