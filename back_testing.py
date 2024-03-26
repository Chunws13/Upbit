import pyupbit, re, time, datetime, math
from market_research import select_coin_market, check_bull_market
from investment_strategy import target_buy_amount

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

        self.start_date = datetime.datetime.now()

        for day in range(1, duration + 1):
            self.duration.append( self.start_date - datetime.timedelta(days=day))

    
    def simulate(self):
        for day in self.duration:
            bull_market = check_bull_market(day) # 상승장 코인 검색
            coin_list = select_coin_market(bull_market=bull_market, target_date=day, invest_number=1) # 거래량 기준 상위 n 개 선택
            



if __name__ == "__main__":
    setting = Back_Testing(100000, 1)
    setting.simulate()
    
    
