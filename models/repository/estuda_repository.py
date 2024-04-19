from typing import Dict

class EstudaRepository:
    def __init__(self, db_connection) -> None:
        self.__collection_name = "estuda"
        self.__db_connection = db_connection

    def insert_document(self, document: Dict) -> Dict:
        collection = self.get_collection()
        collection.insert_one(document)
    
    def get_collection(self):
        return self.__db_connection.get_collection(self.__collection_name)

    def update_correct_answer(self, document_id, update_data: Dict):
        collection = self.get_collection()
        collection.update_one({'_id': document_id}, {'$set': update_data})
        