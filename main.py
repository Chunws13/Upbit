import pyupbit, os, datetime, math, time, requests, uuid, jwt
from dotenv import load_dotenv
from investment_strategy import target_buy_amount
from market_research import check_bull_market
from message_bot import Message_Bot

load_dotenv()

access_key = os.getenv("UPBIT_ACCESS_KEY")
secret_key= os.getenv("UPBIT_SCCRET_KEY")

class Upbit_User:
    def __init__(self, access_key, secret_key):
        self.user = pyupbit.Upbit(access_key, secret_key)

        self.balance = self.user.get_balance()
        self.coin = {}

        self.research_status = False # 시장 분석 완료 여부

    # 9시가 되면 
    # 1. 보유한 코인을 모두 매도한다. -> self.coin 을 초기화한다.
    # 2. 시장 조사를 실시한다. -> 투자 대상 코인 목록을 불러온다 {coint: {}}
    # 3. 코인 별 {target_price: int, invest_status: False} 로 초기화 한다.
    # 4. 목표 코인에 대한 가격을 1초마다 확인한다.
    # 5. 시드는 total balance // 투자 코인 개수로 정한다.
    # 5. 목표 매수가에 도달하면 구매한다. -> invest_status: True 로 변경한다.
    #  ----------------------------- 보류 --------------------------
        
    def start_research(self, day):

        target_coin = check_bull_market(target_date = day, invest_number = 5) # 시장 조사
        for coin in target_coin:
            target_price = target_buy_amount(coin = coin, target_date = day)
            
            if math.isnan(target_price): # 코인 상장일이 5일 미만인 경우, 미 투자
                continue

            self.coin[coin] = {"target_price": target_price, "invest_status": False}
        
        self.research_status = True
        return target_coin

    def scan_coin_price(self, target_coin, budget):
        coin_price = pyupbit.get_current_price(target_coin)

        invest_complete = True # 모든 코인을 투자할 때 까지 검색

        for coin in coin_price:
            if self.coin[coin]["invest_status"] == False and self.coin[coin] <= coin_price[coin]:
                user.buy_market_order(coin, budget) # 시장가 매수
                self.coin[coin]["invest_status"] = True # 코인 투자 완료
                invest_complete = False
            
            time.sleep(0.5)

        return invest_complete
    
    def sell_coin(self):

        return


    def start(self):

        if int(datetime.datetime.now().strptime("%H")) == 9 and self.research_status == False:
            today = datetime.datetime.now()

            target_coin = self.start_research(day = today)
            budget = self.balance // len(target_coin)

            invest_complete = False

            while invest_complete: # 모든 코인 투자시 True else False
                invest_complete = self.scan_coin_price(target_coin=target_coin, budget=budget)



if __name__ == "__main__":
    # user = Upbit_User(access_key=access_key, secret_key=secret_key)
    user = pyupbit.Upbit(access_key, secret_key)
    
    server_url = "https://api.upbit.com"
    
    payload = {
    'access_key': access_key,
    'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, secret_key)
    authorization = 'Bearer {}'.format(jwt_token)
    headers = {
    'Authorization': authorization,
    }

    res = requests.get(server_url + '/v1/accounts', headers=headers)
    print(res.json())
    # print(user.get_balances())