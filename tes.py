from variable import Variable
from datetime import datetime, timedelta, timezone
from logHandler import setup_logging
current_date = datetime.now()
Variable.setNodeLastOnlineTime("qhx6y", current_date.isoformat())
Variable.setResponseTimeLog("qhx6y", "128,197,900,")
# print(Variable.getResponseTimeLog("qhx6y"))
# Variable.reSetResponseTimeLog("Aq5iG")
# Variable.reSetResponseTimeLog("qhx6y")
# print(Variable.getNodeLastOnlineTime("qhx6y"))
# Variable.setAuthenticationResponseLog("qhx6y", {"cardNumber": "90baac20","duid":"qhx61y","isSuccess":True, "time":current_date.isoformat()})
# Variable.reSetAuthenticationResponseLog("qhx6y")
# Variable.reSetAuthenticationResponseLog("qhx6y")
# Variable.reSetAuthenticationResponseLog("Aq5iG")
# print(Variable.getAuthenticationResponseLog("qhx6y"))

from util import sendRoomHistory
import threading
print("Start send request")
# args ==> cardNumber="90baac20",duid="qhx6y",isSuccess=True,
# requestToServer = threading.Thread(target=sendRoomHistory, args=("90baac20","qhx6y",True,))
# requestToServer.start()
# sendRoomHistory(cardNumber="90baac20",duid="qhx6y",isSuccess=True)
# print("Finish")
# requestToServer.join()


# Set up the logger
# logger = setup_logging()

# Example usage
# logger.debug("Debug message")
# logger.info("[AUTH] - Info message")
# logger.warning("Warning message")
# logger.error("Error message")
# logger.critical("Critical message")