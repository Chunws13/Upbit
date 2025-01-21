import os, ssl, certifi, sys, datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from market_research import volatility_breakout, research_by_trade_price
from message_bot import Message_Bot

load_dotenv()

ssl_context = ssl.create_default_context(cafile=certifi.where())

token = os.getenv("SLACK_TOKEN")
channel = os.getenv("SLACK_BACK_TESTING_CHANNEL")

testing_bot = Message_Bot(token=token, channel=channel, ssl = ssl_context)

class Back_Testing:
    def __init__(self, seed, duration):
        self.start_seed = seed
        self.end_seed = seed

        self.coin_info = {}
        self.coin_history = {}

        self.error = 0
        self.start_date = datetime.datetime(2025, 1, 20)

        self.duration = []
        for day in range(duration, 0, -1):
            self.duration.append(self.start_date - datetime.timedelta(days=day))

        self.duration.append(self.start_date)
    
    def simulate(self):
        # coin_list = ["KRW-BTC", "KRW-SOL", "KRW-ETH", "KRW-XRP"]
        
        # for coin in coin_list:
        #     if coin not in self.coin_history:
        #             self.coin_history[coin] = 0

        #     if coin not in self.coin_info:
        #         self.coin_info[coin] = {"buy_price": 0 , "amount": 0}
        
        for day in self.duration:
            print("===", day, "===")
            coin_list = ["KRW-BTC", "KRW-SOL", "KRW-XRP", "KRW-ETH"]
            # coin_list = research_by_trade_price(day, 10)
            
            for coin in coin_list:
                if coin not in self.coin_history:
                        self.coin_history[coin] = 0

            if coin not in self.coin_info:
                self.coin_info[coin] = {"buy_price": 0 , "amount": 0}
            
            coin_seed = int(self.end_seed // len(coin_list))
            
            for coin in coin_list:
                profit_ratio = volatility_breakout(day + datetime.timedelta(hours=9), [coin])
                
                if profit_ratio != 0:
                    profit = round(coin_seed * profit_ratio)
                    after_invest = coin_seed + profit
                    
                    print(f"{coin} : 수익 {profit:,}")
                    self.end_seed += (profit)
                
                    self.coin_history[coin] += profit
            
            # for info in self.coin_history:
            #     print(f"{info} : {self.coin_history[info]:,}")
            
            print("KRW : ", f"{round(self.end_seed):,} ")
            
            print('')
            
        for info in self.coin_info:
            self.end_seed += self.coin_info[info]["amount"]

        print("----- 백테스팅 결과 -----")
        print(f"테스트 기간: {len(self.duration)}일")
        print(f"시작 금액 : {self.start_seed:2,} \n마감 금액 : {int(self.end_seed):2,}")
        print(f"수익률: {round((self.end_seed - self.start_seed) / self.start_seed * 100, 2):2,}%")
        for coin in self.coin_history:
            print(coin, f"{round(self.coin_history[coin]):,}")

if __name__ == "__main__":
    setting = Back_Testing(1000000, 0)
    setting.simulate()
    
    