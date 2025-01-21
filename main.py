import pyupbit, os, datetime, time, ssl, certifi, traceback
from dotenv import load_dotenv
from market_research import start_research
from mongodb_connect import MongodbConntect
from message_bot import Message_Bot

load_dotenv()

access_key = os.getenv("UPBIT_ACCESS_KEY")
secret_key= os.getenv("UPBIT_SCCRET_KEY")

slack_token = os.getenv("SLACK_TOKEN")
slack_channel = os.getenv("SLACK_LIVE_CHANNE")
ssl_context = ssl.create_default_context(cafile=certifi.where())
messenger = Message_Bot(token=slack_token, channel=slack_channel, ssl=ssl_context)

db = MongodbConntect("coin")

class Upbit_User:
    
    # 9시에 Make.com에서 Post 요청
    # 보유 코인 목록 조회 -> 개수 만큼 투자 대상에서 차감
    
    # 전일자 기준 매도 / 매수 기준을 충족했는지 확인 (MA5 vs MA20)
    # 충족 시 투자 실행
    
    def __init__(self, access_key, secret_key):
        self.user = pyupbit.Upbit(access_key, secret_key)
        self.today = datetime.datetime.now()

        messenger.send_message(f"{self.today.year}년 {self.today.month}월 {self.today.day}일 투자를 시작합니다.")
    
    def check_ticker_own(self, coin):
        result = self.user.get_balance(ticker=coin, verbose=True)
        return result if result != 0 else None
        
    def buy_coin(self, ticker, invest_amount):
        result =  self.user.buy_market_order(ticker, invest_amount)

        if result is not None:
            messenger.send_message(f">{ticker} 코인 매수, 매수액: {invest_amount:,}")

    def sell_coin(self, ticker, coin_amount, avg_buy_price):
        buy_price = avg_buy_price * coin_amount

        realtime_price = pyupbit.get_current_price(ticker)

        result = self.user.sell_market_order(ticker, coin_amount)

        if result is not None:
            sell_price = (realtime_price * coin_amount) * 0.9995 
            profit = sell_price - buy_price

            messenger.send_message(f">{ticker} 판매, 수익: {round(profit):,}")
            self.update_db(ticker, profit)

    def update_db(self, ticker, profit):
        ### 코인 투자 내역 갱신
        coin_db = db.coin.find_one({"name": ticker})
        if coin_db is None:
            coin_data = {"name": ticker, "transaction": 1, "profit": profit}
            db.coin.insert_one(coin_data)
        
        else:
            db.coin.update_one({"name": ticker}, 
                            {"$set": {"transaction": coin_db["transaction"] + 1, 
                                        "profit": coin_db["profit"] + profit}})
    
    def start(self, ticker_list):
        try:
            # 요청 받은 코인들의 투자 의견을 반환한다
            year, month, day = self.today.year, self.today.month, self.today.day

            tickers_opinion = start_research(datetime.datetime(year, month, day), ticker_list)

            for ticker in tickers_opinion: # 판매
                messenger.send_message(f"{ticker} 코인 의견 : {tickers_opinion[ticker]['opinion']} ({tickers_opinion[ticker]['inclination']}) ")

                ticker_info = self.check_ticker_own(ticker)

                if tickers_opinion[ticker]["opinion"] == "Sell" and ticker_info is not None:
                    amount, avg_buy_pirce = float(ticker_info["balance"]), float(ticker_info["avg_buy_price"])
                    self.sell_coin(ticker, amount, avg_buy_pirce)

                time.sleep(1)

            budget = self.user.get_balance("KRW")
            investment_size = 0
            
            for ticker in ticker_list: # 투자 예정인 코인 수
                check = self.check_ticker_own(ticker)
                if check is None:
                    investment_size += 1
                
                time.sleep(1)
            
            if investment_size != 0:
                invest_amount = ((budget // investment_size) // 10) * 10

                for ticker in tickers_opinion: # 구매
                    ticker_info = self.check_ticker_own(ticker)

                    if tickers_opinion[ticker]["opinion"] == "Buy" and ticker_info is None:
                        self.buy_coin(ticker, invest_amount)

                    time.sleep(1)

        except Exception as error:
            messenger.send_message(f"오류 발생으로 중단됩니다. \n{error} \n{traceback.print_exc()}")
        
if __name__ == "__main__":
    print(Upbit_User(access_key=access_key, secret_key=secret_key).check_ticker_own("KRW-BTC"))
