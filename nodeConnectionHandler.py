import json
from database.scheme import Node
from datetime import datetime


class CustomException(Exception):
    """ my custom exception class """


def updateNodeOnlineTime(payload):
    sourceObj = json.loads(payload)
    try:
        # Memeriksa apakah node tersimpan di database
        nodeShortId = sourceObj["source"].replace("NODE-", "")
        node = Node.get_or_none(Node.shortId == nodeShortId)
        if node == None:
            raise CustomException("Ruangan Tidak Ditemukan")
        current_date = datetime.now()
        iso_time = current_date
        node.lastOnline = iso_time.isoformat()
        node.save()
        resp = {
            "success": True,
            "type": "connectionping",
            "message": f"New Online Set To {iso_time}",
        }
        return (json.dumps(resp))
    except CustomException as ex:
        resp = {
            "success": False,
            "type": "connectionping",
            "message": str(ex),
        }
        return (json.dumps(resp))
