import logging
import re
from models.connection_options.connection import DBConnectionHandler
from selenium_actions import SeleniumAutomation
from models.repository.estuda_repository import EstudaRepository
from answer_fetcher import get_correct_answer
from estuda_scraper_api import EstudaScraperAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_database():
    db_handle = DBConnectionHandler()
    db_handle.connect_to_db()
    return db_handle.get_db_connection()

def update_correct_answers(db_connection):
    repository = EstudaRepository(db_connection)
    collection = repository.get_collection()

    # Initialize Selenium Automation to clear account to avoid reaching the limit of questions per day 
    bot = SeleniumAutomation()
    bot.login()

    total_requests = 0
    requests_limit = 400 # Site limit

    for document in collection.find():
        document_id = document['id'] 
        correct_answer = get_correct_answer(document_id)
        
        repository.update_document(
            document['_id'], 
            {'question_content.correct_answer': correct_answer}
        )

        total_requests += 1
        if total_requests == requests_limit:
            bot.clean_account()
            total_requests = 0


def main():
    logging.info('Starting the web scraping process.')

    # Connect do Database
    db_connection = connect_to_database()

    base_url = 'https://app.estuda.com/'

    # Get all exams and questions info    
    scraper_api = EstudaScraperAPI(db_connection, base_url)
    scraper_api.execute_fetching_multithreaded()

    update_correct_answers(db_connection)

if __name__ == '__main__':
    main()
