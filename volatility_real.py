import pyupbit, os, datetime, time, ssl, certifi, traceback
from dotenv import load_dotenv
from market_research import volatility_breakout
from mongodb_connect import MongodbConntect
from message_bot import Message_Bot
import pytz
import requests

load_dotenv()

access_key = os.getenv("UPBIT_ACCESS_KEY")
secret_key= os.getenv("UPBIT_SECRET_KEY")

slack_token = os.getenv("SLACK_TOKEN")
slack_channel = os.getenv("SLACK_LIVE_CHANNE")
ssl_context = ssl.create_default_context(cafile=certifi.where())
messanger = Message_Bot(token=slack_token, channel=slack_channel, ssl=ssl_context)

db = MongodbConntect("coin")
KST = pytz.timezone('Asia/Seoul')

STRATEGY_CONFIG = {
    "KRW-BTC": {"k": 0.4, "weight": 0.5},   # 비트코인 비중 50%, K=0.4
    "KRW-ETH": {"k": 0.6, "weight": 0.16},  # 이더리움 비중 16%, K=0.6
    "KRW-XRP": {"k": 0.6, "weight": 0.17},  # 리플 비중 17%, K=0.6
    "KRW-SOL": {"k": 0.6, "weight": 0.17}   # 솔라나 비중 17%, K=0.6
}

def get_kst_now():
    return datetime.datetime.now(KST)

class Upbit_User:
    
    # 9시가 되면 
    # 1. 보유한 코인을 모두 매도한다. -> self.coin 을 초기화한다.
    # 2. 잔고를 확인하고 최대 투자 개수를 파악한다. (최대 10개)
    # 2. 시장 조사를 실시한다. -> 투자 대상 코인 목록을 불러온다 {coint: {}}
    # 3. 시드는 total balance // 투자 코인 개수로 정한다.
    # 4. 코인 별 {target_price: int, realtime_price: int} 로 초기화 한다.
    # 5. 목표 코인에 대한 가격을 1초마다 확인한다.
    
    def __init__(self, access_key, secret_key):
        print(f"[DEBUG] Access Key: {access_key[:10] if access_key else 'None'}...")
        print(f"[DEBUG] Secret Key: {secret_key[:10] if secret_key else 'None'}...")
        self.user = pyupbit.Upbit(access_key, secret_key)

        self.coin = db.asset.find_one({"title": "coin_asset"})["own"]

        self.today = get_kst_now()
        self.budget = self.user.get_balance("KRW")
        print(f"server time : {datetime.datetime.now()}")
        print(f"KST : {get_kst_now()}")
        
        print(f"[DEBUG] Budget from API: {self.budget}")

        response = requests.get('https://icanhazip.com')
        public_ip = response.text.strip()

        print(f"✅ 현재 Out Bound IP 주소: {public_ip}")
        # API 응답 에러 확인
        try:
            balances = self.user.get_balances()
            print(f"[DEBUG] API Response: {balances}")

            if balances is None:
                raise ValueError("API 응답이 None입니다. API 키 권한 또는 네트워크를 확인하세요.")

            actual_cash = self.user.get_balance("KRW")
            self.budget = actual_cash * 0.99 # 수수료/슬리피지 대비 1% 예약
            print(f"[DEBUG] KRW Balance: {actual_cash}, Investment Budget: {self.budget}")

        except Exception as e:
            print(f"[ERROR] API 호출 실패: {e}")
            raise

        if self.budget is None:
            self.budget = 0
            print("[WARNING] KRW 잔고가 0이거나 조회되지 않았습니다.")
            
        # 초기 메시지 및 설정
        messanger.send_message(f"{self.today.year}년 {self.today.month}월 {self.today.day}일 자동 투자 매매 봇이 연결되었습니다.")
        messanger.send_message("--- 최종 최적화 전략 적용 (BTC 하중 + K값 차등) ---")
        
        if len(self.coin):
            messanger.send_message("현재 목표 코인 목록")

            for coin in self.coin:
                buy_price = self.coin[coin]["buy_price"]
                if self.coin[coin]["invest"]:
                    messanger.send_message(f"{coin} 매수가: {round(buy_price, 1)} 보유중")
                
                else:
                    messanger.send_message(f"{coin} 매수가: {round(buy_price, 1)} 투자 예정")

    def adjust_budget(self):
        actual_cash = self.user.get_balance("KRW")
        self.budget = actual_cash * 0.99 # 수수료/슬리피지 대비 1% 예약
        messanger.send_message(f"현재 총 잔고 : {actual_cash:,.0f} KRW (투자 예산: {self.budget:,.0f} KRW)")
        
        if self.budget <= 10000:
            return True
        
        return False
    
    def start_research(self, day):
        messanger.send_message(f"> {day.year}년 {day.month}월 {day.day}일 투자를 시작 합니다.")
        print(f"> {day.year}년 {day.month}월 {day.day}일 투자를 시작 합니다.")
        
        day = datetime.datetime(day.year, day.month, day.day) + datetime.timedelta(hours=9)
        # 1년 백테스팅 기반 최적 설정 적용
        target_coin = list(STRATEGY_CONFIG.keys())

        for coin in target_coin:
            k = STRATEGY_CONFIG[coin]["k"]
            target_price = volatility_breakout(day, [coin], k=k)
            self.coin[coin] = {"buy_price": target_price, "invest": False}
            db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})
            
            messanger.send_message(f"{coin}: [K={k}] 매수 목표가: {round(target_price, 1):1,}")
            
        self.research_status = True
        
    def buy_coin(self, coin, realtime_price, budget):
        result =  self.user.buy_market_order(coin, budget)
        invest_price = budget

        if result is not None:
            self.coin[coin]["buy_price"] = realtime_price
            self.coin[coin]["invest"] = True
            
            db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})

            messanger.send_message(f">코인 매수: {coin}, 매수가: {round(realtime_price, 1)}, 매수액: {invest_price}")

    def sell_coin(self, coin):
        coin_amount = self.user.get_balance(coin)
        self.user.sell_market_order(coin, coin_amount)
        return coin

    def delete_coin_info(self, coin):
        ### 코인 보유 목록 삭제
        del self.coin[coin]
        db.asset.update_one({"title": "coin_asset"}, {"$set": {"own": self.coin}})

    def start(self):
        try:
            while True:
                if get_kst_now().hour == 9 and get_kst_now().minute == 0 and get_kst_now().second <= 5:
                    delete_list = []
                    
                    for coin in self.coin:
                        coin_result = self.sell_coin(coin)
                        delete_list.append(coin_result)
                    
                    for delete in delete_list:
                        self.delete_coin_info(delete)

                    invest_stop_signal = self.adjust_budget()
                    
                    if invest_stop_signal:
                        messanger.send_message(f"최소 투자금액 미달 입니다. 현재 잔고: {round(self.budget, 2):2,}")
                        break
                        
                    ### 날짜 갱신, 수익 정보 초기화
                    self.today = get_kst_now()

                    self.start_research(day = self.today)

                for coin in self.coin:
                    try:
                        realtime_price = pyupbit.get_current_price(coin)
                    
                    except:
                        # 현재 가격 요청 에러 확인, 에러 발생시 한번 건너뛰기
                        continue

                    if self.coin[coin]["invest"]: # 투자 중 일 때
                        continue
                    
                    else: # 투자 전 일 때
                        if realtime_price >= self.coin[coin]["buy_price"]:
                            # 종목별 가중치 적용 투자금 계산
                            weight = STRATEGY_CONFIG[coin]["weight"]
                            current_invest_amount = ((self.budget * weight) // 1000) * 1000
                            self.buy_coin(coin, realtime_price, current_invest_amount)

                    time.sleep(0.2)

        except Exception as error:
            messanger.send_message(f"오류 발생으로 중단됩니다. \n{error} \n{traceback.print_exc()}")
        
if __name__ == "__main__":
    Upbit_User(access_key=access_key, secret_key=secret_key).start()
