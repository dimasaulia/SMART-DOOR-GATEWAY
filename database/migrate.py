import scheme

database = scheme.db

def create_tables():
    with database:
        database.create_tables([scheme.Credential, scheme.Gateway, scheme.Node, scheme.Card])

create_tables()