import pyupbit, heapq, time, datetime, math, pandas
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from async_request import get_ticekr_info
    
def add_indicators(ma_flow_info):
    ma_flow_info["ma5"] = ma_flow_info["close"].ewm(span=5, adjust=False).mean().shift(1)
    ma_flow_info["ma20"] = ma_flow_info["close"].ewm(span=20, adjust=False).mean().shift(1)
    
    ma_flow_info["volume7"] = ma_flow_info["volume"].rolling(window=7, min_periods=7).mean().shift(1)

    diff_info = ma_flow_info["close"].diff()
    
    gain = (diff_info.where(diff_info > 0, 0)).rolling(window=14).mean().shift(1)
    loss = (-diff_info.where(diff_info < 0, 0)).rolling(window=14).mean().shift(1)
    ma_flow_info["rsi"] = 100 - (100 / (1 + (gain / loss)))
    
    ma_flow_info['ema12'] = ma_flow_info['close'].ewm(span=12, adjust=False).mean().shift(1)
    ma_flow_info['ema26'] = ma_flow_info['close'].ewm(span=26, adjust=False).mean().shift(1)
    ma_flow_info['macd'] = ma_flow_info['ema12'] - ma_flow_info['ema26']
    ma_flow_info['macd_signal'] = ma_flow_info['macd'].ewm(span=9, adjust=False).mean().shift(1)
    ma_flow_info['macd_hist'] = ma_flow_info['macd'] - ma_flow_info['macd_signal']

    return ma_flow_info
    
def check_bull_market(target_date, invest_number): # 16 seconds
    ticker_list = get_ticekr_info(target_date + datetime.timedelta(days=1))
    bull_market = []
    for ticker in ticker_list:
        ma_flow_info = ticker_list[ticker]
        
        if ma_flow_info is None or len(ma_flow_info) < 180:
            continue
        
        ma_flow_info = add_indicators(ma_flow_info)
        predict_high, predict_low, predict_close, r2 = regression_actual(ma_flow_info)

        open = ma_flow_info["open"].iloc[-1]
        predict_profit = (predict_high - predict_low) / predict_low * 100
        
        if len(bull_market) < invest_number:
            heapq.heappush(bull_market, [r2, predict_low, predict_high, predict_close, open, ticker])
            continue
        
        if r2 > bull_market[0][0]:
            heapq.heappop(bull_market)
            heapq.heappush(bull_market, [r2, predict_low, predict_high, predict_close, open, ticker])
                
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
    model.fit(ind_train.values, de_train.values)

    ### 사전 평가 - 정확도 확인
    pred_data = model.predict(ind_test.values)

    r2 = r2_score(de_test, pred_data)

    ### 당일 종가 예측
    latest_info = latest_data[features].values.reshape(1, -1)
    predict = model.predict(latest_info)
    
    return [predict[0][1], predict[0][2], predict[0][0], r2]


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
    
    
    accuracy = ([predict[0][0]] - predict[0][2]) / predict[0][2]
    
    return [predict[0][1], predict[0][2], predict[0][0], accuracy]


if __name__ == "__main__":
   results = check_bull_market(target_date=datetime.datetime(2024,6,24), invest_number=5)
   for result in results:
       print(result, results[result])