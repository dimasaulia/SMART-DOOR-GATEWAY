import pika
import json
import os
from datetime import datetime
from database.scheme import Gateway, Node, Card, AccessRole
from variable import *
# GET INFO ABOUT DEVICE
availableGateway = Gateway.get_by_id(1)
gatewayShortId = availableGateway.shortId

RABIT_SETTINGS = {
    "protocol": "amqp",
    "hostname": "172.29.233.187",
    "port": 5672,
    "vhost": "0.0.0.0",
    "exchange": "smartdoor",
    "queues": ["smartdoorgateway"],
}

credential = pika.PlainCredentials("smartdoor","t4np454nd1")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(RABIT_SETTINGS["hostname"],RABIT_SETTINGS["port"],"0.0.0.0",credential))

channel = connection.channel()

channel.exchange_declare(
    exchange=RABIT_SETTINGS["exchange"], exchange_type='direct')

result = channel.queue_declare(
    RABIT_SETTINGS["queues"][0], exclusive=False, durable=True)
queue_name = result.method.queue

print(' [*amqp]: Waiting for logs. To exit press CTRL+C ')
print(f" [!amqp]: PID={os.getpid()}")
Variable.setSyncPid(os.getpid())

channel.queue_bind(exchange=RABIT_SETTINGS["exchange"],
                   queue=queue_name, routing_key=f"setup.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"],
                   queue=queue_name, routing_key=f"reset.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"], queue=queue_name,
                   routing_key=f"setuproom.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"], queue=queue_name,
                   routing_key=f"resetroom.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"], queue=queue_name,
                   routing_key=f"removeroom.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"],
                   queue=queue_name, routing_key=f"addcard.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"], queue=queue_name,
                   routing_key=f"removecard.{gatewayShortId}.gateway")
channel.queue_bind(exchange=RABIT_SETTINGS["exchange"], queue=queue_name,
                   routing_key=f"updatecard.{gatewayShortId}.gateway")

node_DB = Node.select().dicts()
devices = []


def callback(ch, method, properties, body):
    action = method.routing_key.split(".")[0]
    payloadObj = json.loads(body)

    if action == "addcard":
        print(" [!amqp]: NEW CARD HAS BEEND ADDED")
        node = Node.get(Node.shortId == payloadObj["duid"])
        try:
            card = Card.get(Card.cardId == payloadObj["cardNumber"])
        except:
            card = Card.create(cardId=payloadObj["cardNumber"], pin=payloadObj["cardPin"],
                               isTwoStepAuth=payloadObj["isTwoStepAuth"], cardStatus=payloadObj["cardStatus"], isBanned=payloadObj["isBanned"])

        AccessRole.create(card=card, node=node)

        availableGateway.lastSync = payloadObj["createdAt"]
        availableGateway.save()

    if action == "removecard":
        print(" [!amqp]: REMOVE CARD")
        node = Node.get(Node.shortId == payloadObj["duid"])
        try:
            card = Card.get(Card.cardId == payloadObj["cardNumber"])
            AccessRole.delete().where(AccessRole.node == node.id,
                                      AccessRole.card == card.id).execute()
        except:
            print(" [!amqp]: CANT FIND CARD")
        availableGateway.lastSync = payloadObj["createdAt"]
        availableGateway.save()

    if action == "updatecard":
        print(" [!amqp]: UPDATE CARD")
        Card.update(cardId=payloadObj["cardNumber"], pin=payloadObj["cardPin"], isTwoStepAuth=payloadObj["isTwoStepAuth"],
                    cardStatus=payloadObj["cardStatus"], isBanned=payloadObj["isBanned"]).where(Card.cardId == payloadObj["cardNumber"]).execute()

    if action == "setuproom":
        Node.update(buildingName=payloadObj["name"]).where(
            Node.shortId == payloadObj["device_id"]).execute()

    if action == "resetroom":
        node = Node.get(Node.shortId == payloadObj["device_id"])
        AccessRole.delete().where(AccessRole.node_id == node.id).execute()
        Node.update(buildingName=None, lastOnline=None).where(
            Node.shortId == payloadObj["device_id"]).execute()

    if action == "removeroom":
        Node.delete().where(Node.shortId == payloadObj["device_id"]).execute()

    if action == "setup":  # setup gateway
        availableGateway.name = payloadObj["name"]
        availableGateway.lastSync = payloadObj["createdAt"]
        availableGateway.save()

    if action == "reset":  # reset gateway
        availableGateway.name = None
        availableGateway.lastSync = None
        availableGateway.save()
        Node.delete().execute()

    print(" [!amqp]: %r:%r" % (method.routing_key, body))


channel.basic_consume(
    queue=RABIT_SETTINGS["queues"][0], on_message_callback=callback, auto_ack=True)

channel.start_consuming()
