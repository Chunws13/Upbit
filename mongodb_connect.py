from pymongo import MongoClient
from dotenv import load_dotenv
import certifi, os

load_dotenv()
ca = certifi.where()

def MongodbConntect(collection):
    try:
        client = MongoClient(os.getenv("db_address"), tlsCAFile=ca)
        db = client[collection]
        
    except Exception as error:
        print(error) 

    else:
        return db
    
if __name__ == "__main__":
    print(MongodbConntect("coin"))
    