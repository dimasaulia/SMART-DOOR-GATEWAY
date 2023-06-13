import random
import string
import requests
from datetime import datetime
from secret.secret import HTTP_SERVER, header
from variable import Variable

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def sendRoomHistory(cardNumber,duid,isSuccess):
    try:
        resp = requests.post(f"{HTTP_SERVER}/api/v1/gateway/device/h/history",
                            json={"cardNumber": cardNumber,"duid":duid,"isSuccess":isSuccess}, headers=header)
        if (resp.status_code == 200):
            print("Success create room history")
        if (resp.status_code != 200):
            print("Server Offline, History Buffer to log")
            current_date = datetime.now()
            Variable.setAuthenticationResponseLog(duid, {"cardNumber": cardNumber,"duid":duid,"isSuccess":isSuccess,"time":current_date.isoformat()})
    except:
        print("Server Offline, History Buffer to log")
        current_date = datetime.now()
        Variable.setAuthenticationResponseLog(duid, {"cardNumber": cardNumber,"duid":duid,"isSuccess":isSuccess,"time":current_date.isoformat()})