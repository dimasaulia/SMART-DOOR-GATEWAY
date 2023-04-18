from database.scheme import Gateway, Node, Card

Card.create(node="bisGi", cardId='payloadObj["cardNumber"]', pin='payloadObj["cardPin"]').execute()
