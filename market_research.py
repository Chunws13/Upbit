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

            diff_info = ma_flow_info["close"].diff()
            
            gain = (diff_info.where(diff_info > 0, 0)).rolling(window=14).mean().shift(1)
            loss = (-diff_info.where(diff_info < 0, 0)).rolling(window=14).mean().shift(1)
            ma_flow_info["rsi"] = 100 - (100 / (1 + (gain / loss)))

            predict_price = regression_actual(ma_flow_info)
            open_price = ma_flow_info["open"].iloc[-1]
            predict_profit = (predict_price - open_price) / open_price * 100
            
            if predict_profit > 0:
                if len(bull_market) < invest_number:
                    heapq.heappush(bull_market, [predict_price, ticker])
                    continue
                
                if predict_price > bull_market[0][0]:
                    heapq.heappop(bull_market)
                    heapq.heappush(bull_market, [predict_price, ticker])
    
    result = []            
    while bull_market:
        predict_profit, ticker = heapq.heappop(bull_market)
        result.append(ticker)
            
    return result


def regression_actual(learning_data):
    learning_data.dropna(inplace=True)

    train_data = learning_data.iloc[:-1]
    latest_data = learning_data.iloc[-1]
    
    independent = train_data[["open", "ma5", "ma20", "rsi"]]
    dependent = train_data["close"]
    
    ind_train, ind_test, de_train, de_test = train_test_split(independent, dependent, test_size=0.2, random_state=40)
    
    model = LinearRegression()
    
    model.fit(ind_train.values, de_train.values)
    latest_info = latest_data[["open", "ma5", "ma20", "rsi"]].values.reshape(1, -1)
    predict = model.predict(latest_info)

    # print("Predict : ", predict[-1])
    return predict[-1]


def regression_test(learning_data): # 모델 테스트
    learning_data.dropna(inplace=True)

    independent = learning_data[["open", "ma5", "ma20", "rsi"]]
    dependent = learning_data["close"]
    
    ind_train, ind_test, de_train, de_test = train_test_split(independent, dependent, test_size=0.2, random_state=40)

    model = LinearRegression()

    model.fit(ind_train, de_train)
    predict = model.predict(ind_test)

    result = pandas.DataFrame({'Actual': de_test, "Predic": map(int, predict)})
    result["diff_number"] = result["Predic"] - result["Actual"]
    result["diff"] = abs(result["Predic"] - result["Actual"]) / result["Actual"] * 100

    plt.figure(figsize=(8, 6))
    plt.boxplot(result["diff"])
    plt.title('Difference between Actual and Predicted (%)')
    plt.xlabel('Bitcoin')
    plt.ylabel('Difference')
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
   check_bull_market(target_date=datetime.datetime.now(), invest_number=1)
   