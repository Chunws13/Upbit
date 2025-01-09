import pyupbit, heapq, time, datetime, math, pandas
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from async_request_price import get_ticekr_info
from async_request_volume import get_ticekr_volume_info
    
def add_indicators(ma_flow_info):
    # 이동평균 지수를 구하는 함수
    ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=5).mean()
    ma_flow_info["ma20"] = ma_flow_info["close"].rolling(window=20, min_periods=20).mean()

    return ma_flow_info

def make_opinion(coin_chart):
    # 골든 / 데드 크로스 구하는 함수
    pre_ma5, pre_ma20 = coin_chart.iloc[-2]["ma5"], coin_chart.iloc[-2]["ma20"]
    ma5, ma20 = coin_chart.iloc[-1]["ma5"], coin_chart.iloc[-1]["ma20"]
    
    price = coin_chart.iloc[-1]["close"]
    inclination = round((ma5 - ma20) / ma20 * 100, 2)
    opinion = "Hold"

    if pre_ma5 < pre_ma20 and ma5 >= ma20:
        opinion = "Buy"
    
    elif pre_ma5 > pre_ma20 and ma5 <= ma20:
        opinion = "Sell"
    
    investment_opinion = {"opinion": opinion, "inclination": inclination, "price": price}
    
    return investment_opinion


def start_research(target_date, tickers, minutes=None):
    ticker_list = get_ticekr_info(target_date, tickers, minutes)
    
    result = {}

    for ticker in ticker_list:
        coin_chart = ticker_list[ticker]

        if coin_chart is None or len(coin_chart) < 21:
            continue

        coin_chart_ma_flow = add_indicators(coin_chart)
        result[ticker] = make_opinion(coin_chart_ma_flow)
    
    return result

def research_by_trade_price(target_date, amount):
    all_tickers = pyupbit.get_tickers("KRW")
    
    tickers_data = get_ticekr_info(target_date, all_tickers, 60)
    target_list = []

    for ticker in tickers_data: # 거래량 계산
        trade_price = tickers_data[ticker]['trade_price'].tail(24).sum()
        
        heapq.heappush(target_list, [trade_price, ticker])

        if len(target_list) > amount:
            heapq.heappop(target_list)

    target_tickers = [ ticker for trade_price, ticker in target_list ]
    
    target_tickers.reverse()
    return target_tickers

def regression_actual(learning_data):
    learning_data.dropna(inplace=True)

    train_data = learning_data.iloc[:-1]
    latest_data = learning_data.iloc[-1]
    
    features = ["open", "ma5", "ma20", "rsi", "volume7", "macd", "macd_signal", "macd_hist"]

    independent = train_data[features]
    dependent = train_data[["close", "high", "low"]]
    
    ind_train, ind_test, de_train, de_test = train_test_split(independent, dependent, test_size=0.2, random_state=40)
    
    model = LinearRegression()
    model.fit(ind_train.values, de_train.values)

    ### 사전 평가 - 정확도 확인
    pred_data = model.predict(ind_test.values)

    r2 = r2_score(de_test, pred_data)

    ### 당일 종가 예측
    latest_info = latest_data[features].values.reshape(1, -1)
    predict = model.predict(latest_info)
    
    return [predict[0][1], predict[0][2], predict[0][0], r2]


if __name__ == "__main__":
#    tickers = ["KRW-BTC"]
   target_date = datetime.datetime(2025, 1, 9) + datetime.timedelta(hours=9)
   
#    print(pyupbit.get_ohlcv("KRW-BTC", interval="minute10", count=21, to=target_date))
   research_by_trade_price(target_date, 10)
    