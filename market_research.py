import pyupbit, heapq, time, datetime, math, pandas
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from async_request import get_ticekr_info
    
def add_indicators(ma_flow_info):
    ma_flow_info["close"] = ma_flow_info["close"].shift(1)
    ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=5).mean()
    ma_flow_info["ma20"] = ma_flow_info["close"].rolling(window=20, min_periods=20).mean()

    return ma_flow_info
    
def start_research(target_date):
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-SOL", "KRW-XRP"]
    ticker_list = get_ticekr_info(target_date + datetime.timedelta(days=1), tickers)
    
    result = {}

    for ticker in ticker_list:
        coin_chart = ticker_list[ticker]    
        coin_chart_ma_flow = add_indicators(coin_chart)
        
        ma5, ma20 = coin_chart_ma_flow.iloc[-1]["ma5"], coin_chart_ma_flow.iloc[-1]["ma20"]
        
        opinion = "Buy" if ma5 >= ma20 else "Sell"
        separation = round((ma5 - ma20) / ma20 * 100, 2)

        investment_opinion = {"opinion" : opinion, "separation" : separation}
        result[ticker] = investment_opinion

    return result


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
   results = start_research(target_date=datetime.datetime(2024,8,6))
   for result in results:
       print(result, results[result])