import logging
import re
from models.connection_options.connection import DBConnectionHandler
from models.repository.estuda_repository import EstudaRepository
from selenium_actions import SeleniumAutomation
from answer_fetcher import get_correct_answer
from scraping_utils import get_soup, fetch_all_exams, fetch_questions_for_exam, element_to_dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_database():
    db_handle = DBConnectionHandler()
    db_handle.connect_to_db()
    return db_handle.get_db_connection()

def get_total_pages(soup):
    # Determines the total number of pages of exam database
    pagination_select = soup.find('li', class_='paginacao_paginas') 
    options = pagination_select.find_all('option')
    return int(options[-1].text)

def get_exam_details(exam):
    # Extract exam details based on the name pattern
    exam_data = exam.find('span', class_='btn-block').get_text(strip=True)
    
    data_pattern = r'^([a-zA-Z ]+) (\d{4})(?:/(\d+))?(?:\s+.*)?$'
    match = re.search(data_pattern, exam_data.strip())

    questions_number = int(exam.find('strong').find_next('strong').text)

    exam_details = {
        'name': match.group(1).strip(), 
        'year': int(match.group(2)),
        'number': int(match.group(3)) if match.group(3) else '',
        'exam_type': 'Multiple Choice',
        'questions_number' : questions_number
    }

    return exam_details

def get_exam_id(exam):
    # Extract the exam id based on the url pattern
    exam_relative_url = exam.find('a', class_='btn btn-success')['href']
    exam_id = re.search(r'prova=(\d+)&q', exam_relative_url).group(1)

    return exam_id

def assemble_question_content(question):    
    question_statemennt = get_question_statement(question) 
    question_topics = get_question_topics(question)
    question_alternatives = get_question_alternatives(question)
    [question_id, question_difficulty] = get_question_data(question)
    correct_answer = get_correct_answer(question_id)

    question_content = {
        'statement': question_statemennt,
        'topics': question_topics,
        'alternatives': question_alternatives,
        'correct_answer': correct_answer,
        'difficulty_level': question_difficulty
    }

    return question_content, question_id

def get_question_statement(question):
    statement_div_class = 'panel-body panel-body-perguntas highlighter-context'
    statement_div = question.find('div', class_=re.compile(f'^{statement_div_class}'))
    
    statement_elements = ''
    if (statement_div != None):  
        statement_elements = statement_div.find_all('p')

    # Transform html into dict
    question_statement = []
    for element in statement_elements:
        element_dict = element_to_dict(element)
        question_statement.append(element_dict)

    return question_statement

def get_question_topics(question):
    # Extract the question subject and related topics of the question
    tags_elements = question.find('ul', class_='list-tags')

    topic_elements = tags_elements.find_all('a', target='_top')

    question_subject = topic_elements[0].get_text(strip=True) # First topic is the subject of the question

    question_topics = []
    for topic in topic_elements[1:]:
        question_topics.append(topic.get_text(strip=True))

    question_topics = {
        'subject': question_subject,
        'path': {'tree': question_topics}
    }

    return question_topics

def get_question_alternatives(question):
    label_class = 'check btn-block d-flex justify-content-between'

    alternative_elements = question.find_all('label', class_=re.compile(f'^{label_class}'))
    alternatives = []

    # Iterate through each alternative element
    for index, alternative in enumerate(alternative_elements, start=1):
        alternative_data = {'position': '', 'text': []}
        alternative_data['position'] = chr(64 + index)

        alternative_elements = alternative.find_all('p')

        # Transform html into dict
        alternative_text = []
        for element in alternative_elements:
            element_dict = element_to_dict(element)
            alternative_text.append(element_dict)  

        alternative_data['text'] = alternative_text
        alternatives.append(alternative_data)

    return alternatives

def get_question_data(question):
    # Extract the question data based on name pattern
    question_info = question.find('div', class_='panel-title-box').find('h3').text.split()

    question_id = question_info[2]
    question_difficulty = question_info[3]

    return question_id, question_difficulty

def main():
    logging.info('Starting the web scraping process.')

    # Connect do Database
    db_connection = connect_to_database()
    estuda_repository = EstudaRepository(db_connection)

    base_url = 'https://app.estuda.com/'
    soup = get_soup(base_url + 'questoes_provas')

    total_pages = get_total_pages(soup)

    # Initialize Selenium Automation
    bot = SeleniumAutomation()
    bot.login()

    exams = fetch_all_exams(base_url, total_pages)
    logging.info('Fetch exams successfull')
        
    # Iterate through each exam to extract details and questions
    for exam in exams:
        exam_details = get_exam_details(exam)
        exam_id = get_exam_id(exam)

        exam_total_questions = exam_details['questions_number']
        questions = fetch_questions_for_exam(base_url, exam_id, exam_total_questions, bot)
        
        for question in questions:
            [question_content, question_id] = assemble_question_content(question)
            question_data = {
                'id': question_id,
                'exam_details': exam_details,
                'question_content': question_content
            }
            estuda_repository.insert_document(question_data)

            if not question_content['statement'] or question_content['correct_answer'] == '':
                logging.debug(question_id)

        logging.info(f'Extract all question from {exam_details['name']} {exam_details['year']} {exam_details['number']}successfull')
        bot.clean_account()

if __name__ == '__main__':
    main()
