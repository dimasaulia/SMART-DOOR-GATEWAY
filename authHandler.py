import bcrypt
import json
from database.scheme import Node, Card, AccessRole, Gateway


class CustomException(Exception):
    """ my custom exception class """


def cardAuth(payload):
    sourceObj = json.loads(payload)
    try:
        # Periksa Apakah Benar Gateway Tujuan Adalah Gateway ini
        gatewayDestination = sourceObj["destination"].replace("GATEWAY-", "")
        thisGateway = Gateway.get_by_id(1).shortId
        if gatewayDestination != thisGateway:
            raise CustomException("Wrong gateway destination")

        # Memeriksa apakah node tersimpan di database
        nodeShortId = sourceObj["source"].replace("NODE-", "")
        node = Node.get_or_none(Node.shortId == nodeShortId)
        if node == None:
            raise CustomException("Ruangan Tidak Ditemukan")

        # Cek Apakah Kartu Terdapat Di Database
        card = Card.get_or_none(Card.cardId == sourceObj["card"]["id"])
        if card == None:
            raise CustomException("Kartu tidak tersimpan di database")
        if card.isBanned:
            raise CustomException("Kartu Di-Banned")

        # Cek Apakah Kartu Memiliki Akses
        access = AccessRole.get_or_none(
            AccessRole.card == card.id, AccessRole.node == node.id)
        if access == None:
            raise CustomException("Kartu Tidak Memiliki Akses")

        if card.isTwoStepAuth:  # jika kartu mengaktifkan two step auth
            # Cek Pin Kartu Sama Dengan Yang Tersimpan Di Database Jika Kartu Tidak Mengakatifkan Two Step Auth
            if bcrypt.checkpw(sourceObj["card"]["pin"].encode("utf-8"), card.pin.encode("utf-8")):
                # Kirim Data Ke Node untuk Memeberi informasi jika kartu memiliki akses
                resp = {
                    "success": True,
                    "type": "auth",
                    "source": sourceObj["destination"],
                    "destination": sourceObj["source"],
                    "message": "Berhasil Membuka Ruangan"
                }
                return (json.dumps(resp))
            else:
                # jika kartu mematikan two step auth
                raise CustomException("ID dan Pin Kartu Tidak Tepat")

        if not card.isTwoStepAuth:  # jika kartu mematikan two step auth
            # Kirim Data Ke Node untuk Memeberi informasi jika kartu memiliki akses
            resp = {
                "success": True,
                "type": "auth",
                "source": sourceObj["destination"],
                "destination": sourceObj["source"],
                "message": "Berhasil Membuka Ruangan"
            }
            return (json.dumps(resp))

    except CustomException as ex:
        resp = {
            "success": False,
            "types": "auth",
            "message": str(ex),
            "source": sourceObj["destination"],
            "destination": sourceObj["source"],
        }
        return (json.dumps(resp))
