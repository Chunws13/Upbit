import pyupbit
import os, pandas
from dotenv import load_dotenv

load_dotenv()

accekey = os.getenv("UPBIT_ACCESS_KEY")
secretkey= os.getenv("UPBIT_SCCRET_KEY")

user = pyupbit.Upbit(accekey, secretkey)
print(user.get_balances())

chart = pyupbit.get_ohlcv()
chart['high_low_range'] = chart['high'] - chart['low']
chart['volatility'] = chart['high_low_range'].rolling(window=20).mean()

# 노이즈 계산 ( 1- 절대값(시가 - 종가) / (고가 - 저가) )
chart['noise'] = 1 - abs(chart['open'] - chart['close']) / (chart['high'] - chart['low'])
# 노이즈 20일 평균
chart['noise_ma20'] = chart['noise'].rolling(window=20).mean().shift(1)

print(chart)