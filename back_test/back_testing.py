import pyupbit, time, datetime, math, os, sys,ssl
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from market_research import check_bull_market
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

        self.revenu_count = 0
        self.loss_count = 0

        self.max_revenu_ratio = -math.inf
        self.max_loss_ratio = math.inf

        self.coin_history = {}
        self.error = 0
        self.start_date = datetime.datetime(2024, 7, 4)

        self.duration = []
        for day in range(duration, 0, -1):
            self.duration.append(self.start_date - datetime.timedelta(days=day))

        self.duration.append(self.start_date)

    def view_hour_chart(self, ticker, low, high, day):        
        low_index, high_index = math.inf, 0

        chart = pyupbit.get_ohlcv_from(ticker = ticker,
                                       fromDatetime = day , to = day + datetime.timedelta(days=1), 
                                       interval="minute60")
        
        for index in range(9, len(chart)):
            if chart["high"].iloc[index] >= high:
                high_index = max(high_index, index)
            
            if chart["low"].iloc[index] <= low:
                low_index = min(low_index, index)

        sequence = high_index > low_index
        return sequence
    
    def simulate(self):
        for day in self.duration:
            coin_list = check_bull_market(day, 5) # 상승장 코인 검색
            check_win = self.end_seed

            if len(coin_list) == 0:
                print("오늘은 투자 할 대상이 없습니다.")
            
            for coin in coin_list:
                coin_seed = int(self.end_seed / len(coin_list))
                after_coin_seed = 0
                
                pre_high, pre_low = coin_list[coin]["high"], coin_list[coin]["low"]

                self.end_seed -= coin_seed

                if coin not in self.coin_history:
                    self.coin_history[coin] = 0

                time.sleep(0.5)
                chart = pyupbit.get_ohlcv_from(ticker = coin, fromDatetime = day, to = day + datetime.timedelta(days=1))
                
                high_price = chart["high"].iloc[-1]
                low_price = chart["low"].iloc[-1]
                close_price = chart["close"].iloc[-1]

                invest_status = False
                if low_price <= pre_low:
                    invest_status = True
                    sequence = self.view_hour_chart(coin, pre_low, pre_high, day)
                
                if invest_status:
                    if sequence:
                        variance =  (pre_high - pre_low) / pre_low
                        
                    else:
                        variance =  (close_price - pre_low) / pre_low
                    
                    after_coin_seed = coin_seed + coin_seed * variance * 0.9995
                    
                self.end_seed += after_coin_seed if invest_status else coin_seed
                self.coin_history[coin]  += after_coin_seed - coin_seed if invest_status else after_coin_seed
                
                if invest_status:
                    print(coin, ":", coin_seed * variance * 0.9995)
                
                else:
                    print(coin, ":", 0)

            total_variance = round((self.end_seed - check_win) / check_win * 100, 2)
            self.max_revenu_ratio = max(self.max_revenu_ratio, total_variance)
            self.max_loss_ratio = min(self.max_loss_ratio, total_variance)

            if check_win < self.end_seed:
                self.revenu_count += 1
            
            elif check_win > self.end_seed :
                self.loss_count += 1

            message = f"{day} 투자 결과: {int(check_win):2,} => {int(self.end_seed):2,} ({ round((self.end_seed - check_win) / check_win * 100, 2)}%)\n"
            print(message)
            
        print("----- 백테스팅 결과 -----")
        print(f"테스트 기간: {len(self.duration)}일 \n수익 기간: {self.revenu_count}일 \n손실 기간: {self.loss_count}일")
        print(f"\n최대 수익률: {self.max_revenu_ratio:2,}% \n최저 수익률: {self.max_loss_ratio:2,}% \n")
        print(f"시작 금액 : {self.start_seed:2,} \n마감 금액 : {int(self.end_seed):2,}")
        print(f"수익률: {round((self.end_seed - self.start_seed) / self.start_seed * 100, 2):2,}%")

if __name__ == "__main__":
    setting = Back_Testing(1000000, 730)
    setting.simulate()
    
    