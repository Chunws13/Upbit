import pyupbit, os
from dotenv import load_dotenv

load_dotenv()

accekey = os.getenv("UPBIT_ACCESS_KEY")
secretkey= os.getenv("UPBIT_SCCRET_KEY")

print(accekey)
print(secretkey)
