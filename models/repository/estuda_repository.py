from typing import Dict

class EstudaRepository:
    def __init__(self, db_connection) -> None:
        self.__collection_name = "estuda"
        self.__db_connection = db_connection

    def insert_document(self, document: Dict) -> Dict:
        collection = self.__db_connection.get_collection(self.__collection_name)
        collection.insert_one(document)
