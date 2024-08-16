import pyupbit, os, datetime, time, ssl, certifi, traceback
from dotenv import load_dotenv
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
    
    # 9시가 되면 
    # 1. 보유한 코인을 모두 매도한다. -> self.coin 을 초기화한다.
    # 2. 잔고를 확인하고 최대 투자 개수를 파악한다. (최대 5개)
    # 2. 시장 조사를 실시한다. -> 투자 대상 코인 목록을 불러온다 {coint: {}}
    # 3. 시드는 total balance // 투자 코인 개수로 정한다.
    # 4. 코인 별 {target_price: int, realtime_price: int} 로 초기화 한다.
    # 5. 목표 코인에 대한 가격을 1초마다 확인한다.
    
    def __init__(self, access_key, secret_key):
        self.user = pyupbit.Upbit(access_key, secret_key)

        self.coin = db.asset.find_one({"title": "coin_asset"})["own"]

        self.today = datetime.datetime.now()
        self.budget = self.user.get_balance("KRW")
        self.investment_size = 5
        self.investment_amount = (self.budget // self.investment_size) // 10000 * 10000
        
        messanger.send_message(f"{self.today.year}년 {self.today.month}월 {self.today.day}일 자동 투자 매매 봇이 연결되었습니다.")
        
        if len(self.coin):
            messanger.send_message("현재 목표 코인 목록")

            for coin in self.coin:
                buy_price, sell_price = self.coin[coin]["buy_price"], self.coin[coin]["sell_price"]
                if self.coin[coin]["invest"]:
                    messanger.send_message(f"{coin} 매수가: {round(buy_price, 1)} 매도가: {round(sell_price, 1)} 보유중")
                
                else:
                    messanger.send_message(f"{coin} 매수가: {round(buy_price, 1)} 매도가: {round(sell_price, 1)} 투자 예정")

    def adjust_budget(self):
        self.budget = self.user.get_balance("KRW")
        self.investment_amount = (self.budget // self.investment_size) // 10000 * 10000
        messanger.send_message(f"잔고 : {self.budget} \n 개당 투자 금액: {self.investment_amount}")
        
        if self.budget <= 10000:
            return True
        
        # 1개당 투자 금액 계산
        # 개당 투자 금액이 2만원 미만이면 개수 줄임 (최소 1개)
        # 개당 투자 금액이 2만원 이상이면 개수 올림 (최대 5개)
        while self.budget // self.investment_size < 10000:
            if self.investment_size == 1:
                return False
            
            self.investment_size -= 1
        
        while self.budget // self.investment_size > 20000:
            if self.investment_size == 5:
                return False
            
            self.investment_size += 1
        
        return False
    
    def start_research(self, day):
        messanger.send_message(f"> {day.year}년 {day.month}월 {day.day}일 투자를 시작 합니다.")
        
        day = datetime.datetime(day.year, day.month, day.day)
        target_coin = check_bull_market(target_date = day, invest_number = self.investment_size) # 시장 조사, 상승 예상되는 코인만 반환됨
        
        if len(target_coin) == 0:
            messanger.send_message("오늘은 투자 대상 코인이 없습니다.")

        for coin in target_coin:
            high, low = target_coin[coin]["high"], target_coin[coin]["low"]
            self.coin[coin] = {"buy_price": low, "sell_price": high, "invest": False}
            db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})
            
            messanger.send_message(f"{coin}: 매수 지점: {round(low, 1):1,} 매도 지점: {round(high, 1):1,}")
            
        self.research_status = True
        
    def buy_coin(self, coin, realtime_price, budget):
        result =  self.user.buy_market_order(coin, budget)
        invest_price = budget

        if result is not None:
            self.coin[coin]["buy_price"] = realtime_price
            self.coin[coin]["invest"] = True
            self.coin[coin]["invest_price"] = invest_price * 0.9995
            
            db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})

            messanger.send_message(f">코인 매수: {coin}, 매수가: {round(realtime_price, 1)}, 매수액: {invest_price}")

    def sell_coin(self, coin, realtime_price, day):

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

                ### 투자 이력 갱신
                delta = 1
                history_db = db.history.find_one({"date": f"{day.year}-{day.month}-{day.day}"})
                while history_db is None:
                    day -= datetime.timedelta(days=delta)
                    delta -= 1
                    history_db = db.history.find_one({"date": f"{day.year}-{day.month}-{day.day}"})

                db.history.update_one({"date": f"{day.year}-{day.month}-{day.day}"}, 
                                    {"$set": {"profit": history_db["profit"] + profit}})

        return coin

    def delete_coin_info(self, coin):
        ### 코인 보유 목록 삭제
        del self.coin[coin]
        db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})

    def start(self):
        try:
            while True:
                if datetime.datetime.now().hour == 9 and datetime.datetime.now().minute == 1 and datetime.datetime.now().second <= 5:
                    delete_list = []
                    
                    for coin in self.coin:
                        realtime_price = pyupbit.get_current_price(coin)
                        coin_result = self.sell_coin(coin, realtime_price, self.today)
                        delete_list.append(coin_result)
                    
                    for delete in delete_list:
                        self.delete_coin_info(delete)

                    invest_stop_signal = self.adjust_budget()
                    
                    if invest_stop_signal:
                        messanger.send_message(f"최소 투자금액 미달 입니다. 현재 잔고: {round(self.budget, 2):2,}")
                        break
                        
                    ### 날짜 갱신, 수익 정보 초기화
                    self.today = datetime.datetime.now()

                    db_date = f"{self.today.year}-{self.today.month}-{self.today.day}"
                    history_db = db.history.find_one({"date": db_date})

                    if history_db is None:
                        today_history = {"date": db_date, "profit": 0}
                        db.history.insert_one(today_history)

                    self.start_research(day = self.today)

                delete_list = []
                for coin in self.coin:
                    try:
                        realtime_price = pyupbit.get_current_price(coin)
                    
                    except:
                        # 현재 가격 요청 에러 확인, 에러 발생시 한번 건너뛰기
                        continue

                    if self.coin[coin]["invest"]: # 투자 중 일 때
                        if realtime_price >= self.coin[coin]["sell_price"]:
                            sell_complete = self.sell_coin(coin, realtime_price, self.today)
                            delete_list.append(sell_complete)
                    
                    else: # 투자 전 일 때
                        if realtime_price <= self.coin[coin]["buy_price"]:
                            self.buy_coin(coin, realtime_price, self.investment_amount)

                    time.sleep(1)
                
                for delete in delete_list:
                    self.delete_coin_info(delete)

        except Exception as error:
            messanger.send_message(f"오류 발생으로 중단됩니다. \n{error} \n{traceback.print_exc()}")
        
if __name__ == "__main__":
    Upbit_User(access_key=access_key, secret_key=secret_key).start()
