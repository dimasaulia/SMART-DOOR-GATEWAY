from variable import Variable
from datetime import datetime, timedelta, timezone

current_date = datetime.now()
Variable.setNodeLastOnlineTime("qhx6y", current_date.isoformat())
# Variable.setResponseTimeLog("qhx6y", "128,197,900,")
# print(Variable.getResponseTimeLog("qhx6y"))
# Variable.reSetResponseTimeLog("qhx6y")
print(Variable.getNodeLastOnlineTime("qhx6y"))