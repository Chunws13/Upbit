import pyupbit, re, heapq, time, datetime, math, pandas
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt # 예측 결과 시각화

def check_bull_market(target_date, invest_number): # 16 seconds
    KRW_CHECKER = "KRW-"
    from_date = target_date - datetime.timedelta(days=180)

    ticker_list = pyupbit.get_tickers()
    bull_market = []
    for ticker in ticker_list:
        if re.match(KRW_CHECKER, ticker):
            ma_flow_info = pyupbit.get_ohlcv_from(ticker=ticker, fromDatetime=from_date, to=target_date)
            
            if ma_flow_info is None or len(ma_flow_info) < 180:
                continue

            ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=5).mean().shift(1)
            ma_flow_info["ma20"] = ma_flow_info["close"].rolling(window=20, min_periods=20).mean().shift(1)
            
            ma_flow_info["volume7"] = ma_flow_info["volume"].rolling(window=7, min_periods=7).mean().shift(1)

            diff_info = ma_flow_info["close"].diff()
            
            gain = (diff_info.where(diff_info > 0, 0)).rolling(window=14).mean().shift(1)
            loss = (-diff_info.where(diff_info < 0, 0)).rolling(window=14).mean().shift(1)
            ma_flow_info["rsi"] = 100 - (100 / (1 + (gain / loss)))
            
            predict_high, predict_low, accuracy = regression_actual(ma_flow_info)
            # print(ticker, ":", accuracy)
            predict_profit = (predict_high - predict_low) / predict_low * 100
            
            if accuracy > 0.6 and predict_profit > 0:
                if len(bull_market) < invest_number:
                    heapq.heappush(bull_market, [accuracy, predict_low, predict_high, ticker])
                    continue
                
                if predict_profit > bull_market[0][0]:
                    heapq.heappop(bull_market)
                    heapq.heappush(bull_market, [accuracy, predict_low, predict_high, ticker])
                
    result = {}  
    while bull_market:
        accuracy, predict_low, predict_high, ticker = heapq.heappop(bull_market)
        result[ticker] = {"high": predict_high, "low": predict_low}
            
    return result


def regression_actual(learning_data):
    learning_data.dropna(inplace=True)

    train_data = learning_data.iloc[:-1]
    latest_data = learning_data.iloc[-1]
    
    independent = train_data[["open", "ma5", "ma20", "rsi", "volume7"]]
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
    latest_info = latest_data[["open", "ma5", "ma20", "rsi", "volume7"]].values.reshape(1, -1)
    predict = model.predict(latest_info)
    
    accuracy = right_count / predict_count if predict_count > 0 else 0
    return [predict[0][1], predict[0][2], accuracy]


def regression_test(learning_data): # 모델 테스트
    learning_data.dropna(inplace=True)

    independent = learning_data[["open", "ma5", "ma20", "rsi", "volume7"]]
    dependent = learning_data[["close", "high"]]
    
    ind_train, ind_test, de_train, de_test = train_test_split(independent, dependent, test_size=0.2, random_state=40)

    model = LinearRegression()

    model.fit(ind_train, de_train)
    predict = model.predict(ind_test)
    print(predict)
    result = pandas.DataFrame({'open': ind_test['open'],'Actual': de_test["high"], "Predict": predict[:,1]})
    result["diff_number"] = result["Predict"] - result["Actual"]
    result["diff"] = abs(result["Predict"] - result["Actual"]) / result["Actual"] * 100

    # plt.figure(figsize=(8, 6))
    # plt.boxplot(result["diff"])
    # plt.title('Difference between Actual and Predicted (%)')
    # plt.xlabel('Bitcoin')
    # plt.ylabel('Difference')
    # plt.grid(True)
    # plt.show()
    
    right, total = 0, 0

    for index, r in result.iterrows():
        estimate = r["Predict"] - r["open"]
        real = r["Actual"] - r["open"]
        if estimate > 0:
            total += 1

        if estimate > 0 and real > 0:
            right += 1
    
    return right / total

if __name__ == "__main__":
   print(check_bull_market(target_date=datetime.datetime.now(), invest_number=5))