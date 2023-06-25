from dotenv import load_dotenv
import os
import jwt
from database.scheme import Credential

load_dotenv()
datas = Credential.select().dicts()
API_ID = ""
API_KEY = ""
HOST = os.getenv("HOST")
HTTP_SERVER = f"http://{HOST}:8000"
AMQP_HOST = os.getenv("AMQP_HOST")
AMQP_PORT = os.getenv("AMQP_PORT")
AMQP_USER = os.getenv("AMQP_USER")
AMQP_PASSWORD = os.getenv("AMQP_PASSWORD")


if (len(datas)):
    API_ID = datas[0]["apiID"]
    API_KEY = datas[0]["apiKey"]

header = {
    "Content-Type": "application/json",
    "x-api-id": API_ID
}

header["x-api-secret"] = jwt.encode(
    {
        "api-id": API_ID,
        "api-key": API_KEY,
    },
    API_KEY,
    algorithm="HS256"
)
