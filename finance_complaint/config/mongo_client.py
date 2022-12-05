import pymongo
import os
import certifi
from finance_complaint.constant import env_var

ca = certifi.where()
DATABASE_NAME = "finance-complaint-db"


class MongodbClient:
    client = None

    def __init__(self, database_name=DATABASE_NAME) -> None:
        if MongodbClient.client is None:
            MongodbClient.client = pymongo.MongoClient(env_var.mongo_db_url, tlsCAFile=ca)
        self.client = MongodbClient.client
        self.database = self.client[database_name]
        self.database_name = database_name
