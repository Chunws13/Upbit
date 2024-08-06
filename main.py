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
messanger = Message_Bot(token=slack_token, channel=slack_channel, ssl=ssl_context)

db = MongodbConntect("coin")

class Upbit_User:
    
    # 9시에 Make.com에서 Post 요청
    # 보유 코인 목록 조회 -> 개수 만큼 투자 대상에서 차감
    
    # 전일자 기준 매도 / 매수 기준을 충족했는지 확인 (MA5 vs MA20)
    # 충족 시 투자 실행
    
    def __init__(self, access_key, secret_key):
        self.user = pyupbit.Upbit(access_key, secret_key)

        self.coin = db.asset.find_one({"title": "coin_asset"})["own"]

        self.today = datetime.datetime.now()
        self.budget = self.user.get_balance("KRW")
        
        messanger.send_message(f"{self.today.year}년 {self.today.month}월 {self.today.day}일 자동 투자 매매 봇이 연결되었습니다.")
    
    def adjust_budget(self):
        # 판매 대상 코인을 모두 판매한 후에 실행
        # KRW 정보 최신화 / (투자 대상 - 투자 예정) = 개당 투자 금액
        # Return : seed
        self.budget = self.user.get_balance("KRW")
    
    def start_research(self, day):
        # 코인 별 매수/ 매도 의견 취합
        # Returns : {coin : Buy or Sell}

        day = datetime.datetime(day.year, day.month, day.day)
        target_coin = start_research(target_date = day)
        
        
    def buy_coin(self, coin, realtime_price, budget):
        result =  self.user.buy_market_order(coin, budget)
        invest_price = budget

        if result is not None:
            self.coin[coin]["buy_price"] = realtime_price
            self.coin[coin]["invest"] = True
            self.coin[coin]["invest_price"] = invest_price * 0.9995
            
            db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})

            messanger.send_message(f">코인 매수: {coin}, 매수가: {round(realtime_price, 1)}, 매수액: {invest_price}")

    def sell_coin(self, coin, realtime_price):

        if self.coin[coin]["invest"]:
            coin_amount = self.user.get_balance(coin)

            result = self.user.sell_market_order(coin, coin_amount)
            if result is not None:
                sell_market_price = (realtime_price * coin_amount) * 0.9995 
                profit = sell_market_price - self.coin[coin]["invest_price"]

                messanger.send_message(f">{coin} 판매금액: {round(sell_market_price, 1)} 수익: {round(profit, 1)}")

                ### 코인 투자 내역 갱신
                coin_db = db.coin.find_one({"name": coin})
                if coin_db is None:
                    coin_data = {"name": coin, "transaction": 1, "profit": profit}
                    db.coin.insert_one(coin_data)
                
                else:
                    db.coin.update_one({"name": coin}, 
                                    {"$set": {"transaction": coin_db["transaction"] + 1, 
                                                "profit": coin_db["profit"] + profit}})

        return coin


    def start(self):
        try:
            while True:
                if datetime.datetime.now().hour == 9 and datetime.datetime.now().minute == 0 and datetime.datetime.now().second <= 5:
                    
                    for coin in self.coin:
                        realtime_price = pyupbit.get_current_price(coin)
                        coin_result = self.sell_coin(coin, realtime_price, self.today)
                    

                    invest_stop_signal = self.adjust_budget()
                        
                    ### 날짜 갱신, 수익 정보 초기화
                    self.today = datetime.datetime.now()

                    db_date = f"{self.today.year}-{self.today.month}-{self.today.day}"

                    self.start_research(day = self.today)

                for coin in self.coin:
                    try:
                        realtime_price = pyupbit.get_current_price(coin)
                    
                    except:
                        # 현재 가격 요청 에러 확인, 에러 발생시 한번 건너뛰기
                        continue

                    if self.coin[coin]["invest"]: # 투자 중 일 때
                        if realtime_price >= self.coin[coin]["sell_price"]:
                            self.sell_coin(coin, realtime_price, self.today)
                    
                    else: # 투자 전 일 때
                        if realtime_price <= self.coin[coin]["buy_price"]:
                            self.buy_coin(coin, realtime_price, self.investment_amount)

                    time.sleep(1)

        except Exception as error:
            messanger.send_message(f"오류 발생으로 중단됩니다. \n{error} \n{traceback.print_exc()}")
        
if __name__ == "__main__":
    Upbit_User(access_key=access_key, secret_key=secret_key).check(["KRW-ETH"])
