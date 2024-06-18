import pyupbit, re, heapq, time, datetime, math, pandas
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from retrying import retry

@retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
def call_ticker_chart(ticker, start, end):
    chart = pyupbit.get_ohlcv_from(ticker=ticker, fromDatetime=start, to=end)
    if chart is None:
        raise

    return chart

def safe_call_ticker_chart(ticker, start, end):
    try:
        return call_ticker_chart(ticker, start, end)
    
    except:
        return None
    
def check_bull_market(target_date, invest_number): # 16 seconds
    KRW_CHECKER = "KRW-"
    from_date = target_date - datetime.timedelta(days=180)

    ticker_list = pyupbit.get_tickers()
    bull_market = []
    for ticker in ticker_list:
        if re.match(KRW_CHECKER, ticker):
            ma_flow_info = safe_call_ticker_chart(ticker, from_date, target_date + datetime.timedelta(days=1))
            
            if ma_flow_info is None or len(ma_flow_info) < 180:
                continue
            
            ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=5).mean().shift(1)
            ma_flow_info["ma20"] = ma_flow_info["close"].rolling(window=20, min_periods=20).mean().shift(1)
            
            ma_flow_info["volume7"] = ma_flow_info["volume"].rolling(window=7, min_periods=7).mean().shift(1)

            diff_info = ma_flow_info["close"].diff()
            
            gain = (diff_info.where(diff_info > 0, 0)).rolling(window=14).mean().shift(1)
            loss = (-diff_info.where(diff_info < 0, 0)).rolling(window=14).mean().shift(1)
            ma_flow_info["rsi"] = 100 - (100 / (1 + (gain / loss)))
            
            ma_flow_info['ema12'] = ma_flow_info['close'].ewm(span=12, adjust=False).mean()
            ma_flow_info['ema26'] = ma_flow_info['close'].ewm(span=26, adjust=False).mean()
            ma_flow_info['macd'] = ma_flow_info['ema12'] - ma_flow_info['ema26']
            ma_flow_info['macd_signal'] = ma_flow_info['macd'].ewm(span=9, adjust=False).mean()
            ma_flow_info['macd_hist'] = ma_flow_info['macd'] - ma_flow_info['macd_signal']

            predict_high, predict_low, predict_close, accuracy = regression_actual(ma_flow_info)
            
            open = ma_flow_info["open"].iloc[-1]
            predict_profit = (predict_high - predict_low) / predict_low * 100
            
            if accuracy > 0.6:
                if len(bull_market) < invest_number:
                    heapq.heappush(bull_market, [accuracy, predict_low, predict_high, predict_close, open, ticker])
                    continue
                
                if predict_profit > bull_market[0][0]:
                    heapq.heappop(bull_market)
                    heapq.heappush(bull_market, [accuracy, predict_low, predict_high, predict_close, open, ticker])
                
    result = {}  
    while bull_market:
        accuracy, predict_low, predict_high, predict_close, open, ticker = heapq.heappop(bull_market)
        result[ticker] = {"open": open, "high": predict_high, "low": predict_low, "close": predict_close, "arc": accuracy}

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
    
    ### 사전 평가 - 정확도 확인
    model.fit(ind_train.values, de_train.values)
    estimate = model.predict(ind_test.values)
    
    estimate_data = pandas.DataFrame({"open": ind_test["open"], "close": de_test["close"], 
                                      "predict_close": estimate[:, 0], "predict_high": estimate[:, 1], "predict_low": estimate[:, 2]})
    
    right_count, predict_count = 0, 0
    for index, data in estimate_data.iterrows():
        if data["predict_close"] - data["open"] > 0:
            predict_count += 1

        if data["predict_close"] - data["open"] > 0 and data["close"] - data["open"] > 0:
            right_count += 1

    ### 당일 종가 예측
    latest_info = latest_data[features].values.reshape(1, -1)
    predict = model.predict(latest_info)
    
    accuracy = right_count / predict_count if predict_count > 0 else 0
    # accuracy = ([predict[0][1]] - predict[0][2]) / predict[0][2]
    
    return [predict[0][1], predict[0][2], predict[0][0], accuracy]


def regression_test(learning_data): # 모델 테스트
    learning_data.dropna(inplace=True)

    train_data = learning_data.iloc[:-1]
    latest_data = learning_data.iloc[-1]
    
    features = ["open", "ma5", "ma20","rsi", "volume7", "macd", "macd_signal", "macd_hist"]

    independent = train_data[features]
    dependent = train_data[["close", "high", "low"]]
    
    ind_train, ind_test, de_train, de_test = train_test_split(independent, dependent, test_size=0.2, random_state=40)

    model = RandomForestRegressor(n_estimators=100, random_state=42)

    model.fit(ind_train.values, de_train.values)
    
    latest_info = latest_data[features].values.reshape(1, -1)
    predict = model.predict(latest_info)
    
    # accuracy = right_count / predict_count if predict_count > 0 else 0
    accuracy = ([predict[0][0]] - predict[0][2]) / predict[0][2]
    
    return [predict[0][1], predict[0][2], predict[0][0], accuracy]


if __name__ == "__main__":
   results = check_bull_market(target_date=datetime.datetime(2024,6,20), invest_number=5)
   for result in results:
       print(result, results[result])