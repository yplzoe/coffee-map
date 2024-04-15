import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError


class MongoDB:
    def __init__(self, host=None, port=27017, uri=None):
        if uri:
            self.client = MongoClient(uri)
        else:
            self.client = MongoClient(host, port)

    def insert_list(self, database_name, collection_name, data):
        """insert data into MongoDB collection

        Args:
            database_name (str): name of the mongoDB database
            collection_name (str): name of the collection within database
            data (_type_): List of dictionaries representing the data to insert
        """
        db = self.client[database_name]
        collection = db[collection_name]
        try:
            result = collection.insert_many(data)
            print("complete insert list, insert_id: ", result.inserted_ids[0])
        except BulkWriteError as e:
            for error in e.details['writeErrors']:
                print(f"Error: {error['errmsg']}")

    def close_connection(self):
        self.client.close()
