import time, datetime, heapq
from dotenv import load_dotenv
from market_research import start_research, research_by_trade_price
from message_bot import Message_Bot
import os, ssl, certifi

load_dotenv()

ssl_context = ssl.create_default_context(cafile=certifi.where())

token = os.getenv("SLACK_TOKEN")
channel = os.getenv("SLACK_BACK_TESTING_CHANNEL")

testing_bot = Message_Bot(token=token, channel=channel, ssl = ssl_context)

class Back_Testing:
    def __init__(self, seed, start, end):
        self.start_seed = seed
        self.end_seed = seed

        self.coin_info = {}
        self.coin_history = {}
        
        self.start = start
        self.end = end
    
    def select_coin(self, tickers_opinion):
        result = []

        for ticker in tickers_opinion:
            ticker_info = tickers_opinion[ticker]
            if ticker_info["opinion"] != "Buy":
                continue
            
            inclination, price = ticker_info["inclination"], ticker_info["price"]

            heapq.heappush(result, [-inclination, price, ticker])

        if result:
            return result[0]
        
        else:
            return None

    def simulate(self, limit_value):
        while self.start <= self.end:
            print("===", self.start, "===", ":", f"{round(self.end_seed):,}\n")
            
            # 보유중인 코인의 매수 결정
            for ticker in self.coin_info:
                ticker_opinion = start_research(self.start  + datetime.timedelta(hours=9), [ticker], 60)
                opinion, price = ticker_opinion[ticker]["opinion"], ticker_opinion[ticker]["price"]
                
                if opinion == "Buy" and self.coin_info[ticker]["amount"] == 0:
                    print(f"{ticker} 코인 구매, 단가 : {price:,}  구매액 : {round(coin_seed):,}")
                    self.coin_info[ticker] = {"price": price, "amount": coin_seed}
                    self.end_seed -= coin_seed

                if opinion == "Sell" and self.coin_info[ticker]["amount"] != 0:
                    profit = ((price / self.coin_info[ticker]["price"]) - 1) * self.coin_info[ticker]["amount"]
                    print(f"{ticker} 코인 판매, 판매가 : {price:,}, 수익: {round(profit):,}")
                    self.end_seed += (profit  + self.coin_info[ticker]["amount"])
                    self.coin_info[ticker] = {"price": 0, "amount": 0}

            # 새로운 투자 대상을 불러오기
            new_tickers = research_by_trade_price(self.start, limit_value)

            # 투자 대상에서 제외되었고
            # 투자 중이 아닌 코인은 제외
            delete_list = []

            for ticker in self.coin_info:
                if ticker not in new_tickers and self.coin_info[ticker]['amount'] == 0:
                    delete_list.append(ticker)
            
            for delete in delete_list:
                print(f"{delete} 코인 제외")
                del self.coin_info[delete]

            # 10개 까지 추가.
            for ticker in new_tickers:
                if ticker not in self.coin_info:
                    print(f"{ticker} 코인 추가")
                    self.coin_info[ticker] = {"price": 0, "amount": 0}

                if len(self.coin_info) == limit_value:
                    break
            
            investing = 0

            for ticker in self.coin_info:
                if self.coin_info[ticker]['amount'] != 0:
                    investing += 1

            coin_seed = int(self.end_seed // (limit_value - investing)) if investing != limit_value else 0
            
            middle = 0
            for coin in self.coin_info:
                middle += self.coin_info[coin]["amount"]
                print(coin, f"{round(self.coin_info[coin]['amount']):,}")
            
            middle += self.end_seed

            print(f"중간 계 : {round(middle):,}")
            print()
            self.start += datetime.timedelta(minutes=60)
            time.sleep(1)

        for coin in self.coin_info:
            self.end_seed += self.coin_info[coin]["amount"]

        print("----- 백테스팅 결과 -----")
        print(f"시작 금액 : {self.start_seed:2,} \n마감 금액 : {int(self.end_seed):2,}")
        print(f"수익률: {round((self.end_seed - self.start_seed) / self.start_seed * 100, 2):2,}%")

if __name__ == "__main__":
    target = datetime.datetime(2025, 1, 7)
    setting = Back_Testing(1000000, target - datetime.timedelta(days=10), target)
    setting.simulate(10)
    
    