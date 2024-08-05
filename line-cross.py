import pyupbit, re, time, datetime, math
from dotenv import load_dotenv
from message_bot import Message_Bot
import os, ssl, certifi

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
        self.start_date = datetime.datetime(2024, 8, 4)

        self.duration = []
        for day in range(duration, 0, -1):
            self.duration.append(self.start_date - datetime.timedelta(days=day))

        self.duration.append(self.start_date)
    
    def signal(self, ma5, ma20):
        if ma5 >= ma20:
            return "buy"
        
        elif ma5 <= ma20:
            return "sell"
        
        return "nothing"
    
    def simulate(self):
        for day in self.duration:
            print("===", day, "===")

            coin_list = ["KRW-SOL", "KRW-BTC", "KRW-ETH", "KRW-XRP"]
            
            for coin in coin_list:
                investing = 0
                for c in self.coin_info:
                    if self.coin_info[c]['amount'] != 0:
                        investing += 1

                coin_seed = int(self.end_seed // len(coin_list) - investing)

                if coin not in self.coin_history:
                    self.coin_history[coin] = 0

                if coin not in self.coin_info:
                    self.coin_info[coin] = {"buy_price": 0 , "amount": 0}

                time.sleep(0.5)
                chart = pyupbit.get_ohlcv_from(ticker = coin, fromDatetime = day - datetime.timedelta(days=60), to = day + datetime.timedelta(days=1))
                chart["close"] = chart["close"].shift(1)

                chart["ma5"] = chart["close"].rolling(window=5).mean()
                chart["ma20"] = chart["close"].rolling(window=20).mean()

                today_data = chart.iloc[-1]

                signal_check = self.signal(today_data["ma5"], today_data["ma20"])
                
                if signal_check == "buy" and self.coin_info[coin]["amount"] == 0:
                    print(f"{coin}코인 구매 : {today_data['open']}")

                    buy_info = {"buy_price": today_data["open"], "amount": coin_seed}
                    self.end_seed -= coin_seed
                    self.coin_info[coin] = buy_info
                
                elif signal_check == "sell" and self.coin_info[coin]["amount"] != 0:
                    profit = (1 - (today_data["open"] / self.coin_info[coin]["buy_price"])) * self.coin_info[coin]["amount"]

                    print(f"{coin}코인 판매, 판매가: {today_data['open']} 수익 : {profit}")
                    self.end_seed += (profit + self.coin_info[coin]["amount"])
                    self.coin_info[coin] = {'buy_price': 0, "amount": 0}
            
            for info in self.coin_info:
                print(f"{info} : {self.coin_info[info]}")

        for info in self.coin_info:
            self.end_seed += self.coin_info[info]["amount"]

        print("----- 백테스팅 결과 -----")
        print(f"테스트 기간: {len(self.duration)}일")
        print(f"시작 금액 : {self.start_seed:2,} \n마감 금액 : {int(self.end_seed):2,}")
        print(f"수익률: {round((self.end_seed - self.start_seed) / self.start_seed * 100, 2):2,}%")

if __name__ == "__main__":
    setting = Back_Testing(1000000, 1)
    setting.simulate()
    
    