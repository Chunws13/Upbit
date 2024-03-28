import pyupbit, re, heapq, time, datetime, math, pandas
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression


def check_bull_market(target_date, invest_number): # 16 seconds
    KRW_CHECKER = "KRW-"
    from_date = target_date - datetime.timedelta(days=180)

    ticker_list = pyupbit.get_tickers()
    bull_market = []
    ticker_list = ["KRW-BTC"]
    for ticker in ticker_list:
        if re.match(KRW_CHECKER, ticker):
            ma_flow_info = pyupbit.get_ohlcv_from(ticker=ticker, fromDatetime=from_date, to=target_date)
            
            if ma_flow_info is None:
                continue

            ma_flow_info["ma5"] = ma_flow_info["close"].rolling(window=5, min_periods=5).mean().shift(1)
            ma_flow_info["ma20"] = ma_flow_info["close"].rolling(window=20, min_periods=20).mean().shift(1)

            diff_info = ma_flow_info["close"].diff()
            
            gain = (diff_info.where(diff_info > 0, 0)).rolling(window=14).mean().shift(1)
            loss = (-diff_info.where(diff_info < 0, 0)).rolling(window=14).mean().shift(1)
            ma_flow_info["rsi"] = 100 - (100 / (1 + (gain / loss)))

            print(ticker, len(ma_flow_info))
            regression_analysis(ma_flow_info)

    return 

def regression_analysis(learning_data): # 1ms under

    learning_data.dropna(inplace=True)

    independent = learning_data[["open", "ma5", "ma20", "rsi"]]
    dependent = learning_data["close"]


def regression_actual(independent, dependent):
    pass


def regression_test(independent, dependent):
    ind_train, ind_test, de_train, de_test = train_test_split(independent, dependent, test_size=0.2, random_state=40)

    model = LinearRegression()

    model.fit(ind_train, de_train)
    predict = model.predict(ind_test)

    result = pandas.DataFrame({'Actual': de_test, "Predic": map(int, predict)})
    result["diff_number"] = result["Predic"] - result["Actual"]
    result["diff"] = abs(result["Predic"] - result["Actual"]) / result["Actual"] * 100

    print(result["diff"].mean(), result["diff"].max(), result["diff"].min(), result["diff_number"].sum(), model.coef_)


if __name__ == "__main__":
   check_bull_market(target_date=datetime.datetime.now(), invest_number=1)
   pass