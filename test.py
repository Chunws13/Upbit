import pyupbit, os, datetime, time, ssl, certifi, traceback
from dotenv import load_dotenv
if __name__ == "__main__":

    load_dotenv()
    access_key = os.getenv("UPBIT_ACCESS_KEY", None)
    secret_key= os.getenv("UPBIT_SECRET_KEY", None)
    print(access_key)
    user = pyupbit.Upbit(access_key, secret_key)
    
    print(user.get_balance("KRW"))