from fastapi import FastAPI
from pydantic import BaseModel
from main import Upbit_User
import os

app = FastAPI()

class Coin_list(BaseModel):
    coin_list : list


@app.post("/coin")
def coin_trade(coin_list:Coin_list):
    coin_list = coin_list.coin_list

    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SCCRET_KEY")

    mywallet = Upbit_User(access_key, secret_key)
    for coin in coin_list:
        mywallet.check(coin)

    return
