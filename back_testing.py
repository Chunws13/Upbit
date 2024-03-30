import pyupbit, re, time, datetime, math
from market_research import check_bull_market
from investment_strategy import target_buy_amount
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
        self.duration = []

        self.start_seed = seed
        self.end_seed = seed

        self.revenu_count = 0
        self.loss_count = 0

        self.max_revenu_ratio = -math.inf
        self.max_loss_ratio = math.inf

        self.coin_history = {}
        self.error = 0
        self.start_date = datetime.datetime.now()

        for day in range(duration, 0, -1):
            self.duration.append(self.start_date - datetime.timedelta(days=day) - datetime.timedelta(days=180))
        
    def simulate(self):
        for day in self.duration:
            message = f"----- {day.year}-{day.month}-{day.day} 투자 시뮬레이션 -----"
            testing_bot.send_message(message)

            coin_list = check_bull_market(day, 5) # 상승장 코인 검색
            check_win = self.end_seed

            if len(coin_list) == 0:
                testing_bot.send_message("오늘은 투자 할 대상이 없습니다.")
            
            for coin in coin_list:
                coin_seed = int(self.end_seed / len(coin_list))
                after_coin_seed = 0

                target_buy = target_buy_amount(coin = coin, target_date = day)

                if math.isnan(target_buy):
                    self.error += 1
                    testing_bot.send_message("목표 매수가 불러오기 에러")
                    continue

                self.end_seed -= coin_seed

                if coin not in self.coin_history:
                    self.coin_history[coin] = 0

                time.sleep(0.5)
                chart = pyupbit.get_ohlcv_from(ticker = coin, fromDatetime = day - datetime.timedelta(days=1), to = day)
                
                invest_status = False
                
                if chart is None:
                    self.error += 1
                    self.end_seed += coin_seed
                    
                    testing_bot.send_message(str(coin_list) + " 중 " + coin + "차트 불러오기 에러")
                    print(chart)
                    continue
                    
                high_price = int(chart["high"].iloc[-1])
                close_price = int(chart["close"].iloc[-1])

                # message = f"{coin}\n목표가: {round(target_buy, 2):2,} \n최고가: {round(high_price,2):2,}\n종료가: {round(close_price,2):2,}"
                # testing_bot.send_message(message)

                if chart["high"].iloc[-1] >= target_buy:
                    invest_status = True

                    variance =  (chart["close"].iloc[-1] - target_buy) / target_buy
                    
                    after_coin_seed = coin_seed + coin_seed * variance

                    testing_bot.send_message(f"{coin} 수익: {int(after_coin_seed - coin_seed):2,}")

                self.end_seed += after_coin_seed if invest_status else coin_seed
                self.coin_history[coin]  += after_coin_seed - coin_seed if invest_status else after_coin_seed
                
            total_variance = round((self.end_seed - check_win) / check_win * 100, 2)
            self.max_revenu_ratio = max(self.max_revenu_ratio, total_variance)
            self.max_loss_ratio = min(self.max_loss_ratio, total_variance)

            if check_win > self.end_seed:
                self.revenu_count += 1
            
            elif check_win < self.end_seed :
                self.loss_count += 1

            message = f"투자 결과: {int(check_win):2,} => {int(self.end_seed):2,} ({ round((self.end_seed - check_win) / check_win * 100, 2)}%)\n"
            testing_bot.send_message(message)
            
        testing_bot.send_message("----- 백테스팅 결과 -----")
        testing_bot.send_message(f"테스트 기간: {self.duration[0]} ~ {self.duration[-1]}")
        testing_bot.send_message("코인 별 수익 내역")
        
        for history in self.coin_history:
            time.sleep(0.5)
            if self.coin_history[history] != 0:
                testing_bot.send_message(f"{history} : {int(self.coin_history[history]):2,}")
        
        testing_bot.send_message(f"테스트 기간: {len(self.duration)}일 \n수익 기간: {self.revenu_count}일 \n손실 기간: {self.loss_count}일")
        testing_bot.send_message(f"\n최대 수익률: {self.max_revenu_ratio:2,}% \n최저 수익률: {self.max_loss_ratio:2,}% \n")
        testing_bot.send_message(f"시작 금액 : {self.start_seed:2,} \n마감 금액 : {int(self.end_seed):2,}")
        testing_bot.send_message(f"수익률: {round((self.end_seed - self.start_seed) / self.start_seed * 100, 2):2,}%")

if __name__ == "__main__":
    setting = Back_Testing(100000, 365)
    setting.simulate()
    
    
