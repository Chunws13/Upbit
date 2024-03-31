import pyupbit, os, datetime, math, time, ssl, certifi
from dotenv import load_dotenv
from investment_strategy import target_buy_amount
from market_research import check_bull_market
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
    def __init__(self, access_key, secret_key):
        self.user = pyupbit.Upbit(access_key, secret_key)
        self.coin = db.asset.find_one({"title": "coin_asset"})

        self.research_status = False # 시장 분석 완료 여부

    # 9시가 되면 
    # 1. 보유한 코인을 모두 매도한다. -> self.coin 을 초기화한다.
    # 2. 시장 조사를 실시한다. -> 투자 대상 코인 목록을 불러온다 {coint: {}}
    # 3. 코인 별 {target_price: int, invest_status: False} 로 초기화 한다.
    # 4. 목표 코인에 대한 가격을 1초마다 확인한다.
    # 5. 시드는 total balance // 투자 코인 개수로 정한다.
    # 5. 목표 매수가에 도달하면 구매한다. -> invest_status: True 로 변경한다.
    #  ----------------------------- 보류 --------------------------
    def test(self):
        return self.coin
    
    def start_research(self, day):
        messanger.send_message(f"{day.year}년 {day.month}월 {day.day}일 투자를 시작 합니다.")
        target_coin = check_bull_market(target_date = day, invest_number = 5) # 시장 조사
        for coin in target_coin:
            target_price = target_buy_amount(coin = coin, target_date = day)
            
            if math.isnan(target_price) or target_price >= target_coin[coin]: 
                # 목표가에 오류가 있거나 예상 마감 가격이 진입 가격보다 낮을 때, 미 투자               
                continue

            self.coin[coin] = {"target_price": target_price, "invest_status": False}
        self.research_status = True
        
        if len(target_coin) == 0:
            messanger.send_message("오늘은 투자 대상이 없습니다.")
        
        else:
            messanger.send_message("-- 코인 별 목표 가격 안내 --")
            for coin in self.coin:
                messanger.send_message(f"{coin}: {self.coin[coin]}")
                time.sleep(0.5)
        

    def scan_coin_price(self, target_coin, budget):
        coin_price = pyupbit.get_current_price(target_coin)

        for coin in coin_price:
            if self.coin[coin]["invest_status"] == False and self.coin[coin] <= coin_price[coin]:
                user.buy_market_order(coin, budget) # 시장가 매수
                self.coin[coin]["invest_status"] = True # 코인 투자 완료
            
            time.sleep(0.5)
    
    def sell_coin(self):
        own_coin = self.user.get_balances()
        for own in own_coin:
            print(own)
        return

    def start(self):
        while True:
            if int(datetime.datetime.now().strptime("%H")) == 9 and self.research_status == False:
                today = datetime.datetime.now()

                target_coin = self.start_research(day = today)
                budget = self.balance // len(target_coin)
                invest_complete = self.scan_coin_price(target_coin=target_coin, budget=budget)


if __name__ == "__main__":
    user = Upbit_User(access_key=access_key, secret_key=secret_key)
    print(user.test()["own"])
    # print(db.memo.find({"title": "coin_asset"}))