from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# from main import Upbit_User
from volatility_real import Upbit_User
import os, threading, time, asyncio

app = FastAPI()

class Coin_list(BaseModel):
    coin_list : list

tasks = {}
loop_control = {}

class Request(BaseModel):
    id : str

@app.post("/coin")
def coin_trade():
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SCCRET_KEY")

    mywallet = Upbit_User(access_key, secret_key)
    
    mywallet.start()

    return "Coin invest Start"