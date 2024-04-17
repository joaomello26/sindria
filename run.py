import logging
import requests
import re
import math
import sys
from bs4 import BeautifulSoup
from models.connection_options.connection import DBConnectionHandler
from models.repository.estuda_repository import EstudaRepository
from selenium_actions import SeleniumAutomation

def connect_to_database():
    db_handle = DBConnectionHandler()
    db_handle.connect_to_db()
    return db_handle.get_db_connection()

def get_soup(url):
    # Fetches and parses html content from a given url using BeautifulSoup.
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad HTTP responses
    except requests.RequestException as e:
        # Handle HTTP and other network-related errors
        logging.error(f'Error fetching URL {url}: {e}')
        return None
    
    soup = BeautifulSoup(response.text, 'lxml')
    if soup is not None:
        return soup
    else:
        # If lxml parsing results in an empty soup
        logging.error(f'Failed to get any content from {url}.')
        sys.exit(1)

def get_total_pages(soup):
    # Determines the total number of pages of exam database
    pagination_select = soup.find('li', class_='paginacao_paginas') 
    options = pagination_select.find_all('option')
    return int(options[-1].text)

def fetch_all_exams(base_url, total_pages):
    # Fetch all the exams in the site database
    exams = []

    for actual_page in range(1, total_pages + 1):
        page_soup = get_soup(f'{base_url}questoes_provas/?inicio={actual_page}')

        if not page_soup: # Check if soup is None and exit if true
            logging.error("Failed to get the exam database page content.")
            sys.exit(1)

        exams.extend(get_exam_elements(page_soup))

    return exams

def get_exam_elements(page_soup):
    return page_soup.find_all('div', class_='col-md-4 col-sm-6 col-xs-12')

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

def fetch_questions_for_exam(base_url, exam_id, exam_total_questions, bot):
    # Extract the html content of all exam pages
    questions_by_page = 6 # Site pattern
    exam_pages = math.ceil(exam_total_questions / questions_by_page)
    questions = []

    for page_number in range(1, exam_pages+1):
        # Use bot to extract questions topics and answer the questions to extract the correct answer
        page_url = f'{base_url}questoes/?prova={exam_id}&inicio={page_number}'
        bot.driver.get(page_url)

        bot.get_answers()
        bot.get_topics()
        page_content = bot.driver.page_source
        
        page_soup = BeautifulSoup(page_content, 'lxml')

        if not page_soup:
            logging.error('Failed to get questions content.')
            sys.exit(1)

        questions.extend(get_question_elements(page_soup))

    return questions

def get_question_elements(exam_page_soup):
    return exam_page_soup.find_all('div', id=re.compile('^d_questao'))

def assemble_question_content(question):    
    question_statemennt = get_question_statement(question)
    question_topics = get_question_topics(question)
    [question_alternatives, correct_aswer] = get_question_alternatives(question)
    [question_id, question_difficulty] = get_question_data(question)

    question_content = {
        'statement': question_statemennt,
        'topics': question_topics,
        'alternatives': question_alternatives,
        'correct_answer': correct_aswer,
        'difficulty_level': question_difficulty
    }

    return question_content, question_id

def get_question_topics(question):
    # Extract the question subject and related topics of the question
    tags_elements = question.find('ul', class_='list-tags')

    question_subject = tags_elements.find('li', class_='active').get_text(strip=True)

    topic_elements = tags_elements.find_all('a', target='_top')
    question_topics = []
    for topic in topic_elements:
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

    correct_answer_element = question.find('label', class_= re.compile(r"\bcerta\b"))

    # Iterate through each alternative element
    for index, alternative in enumerate(alternative_elements, start=1):
        alternative_data = {'position': '', 'text': '', 'images': []}
        alternative_data['position'] = chr(64 + index)

        # Extract the alternative's text if it's available
        alternative_text_tag = alternative.find('p')
        if alternative_text_tag:
            alternative_data['text'] = alternative_text_tag.get_text(strip=True)

        # Extract the alternative's image if it's available
        alternative_image_tags = alternative.find_all('img')
        if alternative_image_tags:
            for img_tag in alternative_image_tags:
                alternative_data['images'].append(img_tag['src'])

        # Extract the correct answer if it's case
        if alternative == correct_answer_element:
            correct_answer = alternative_data['position']

        alternatives.append(alternative_data)

    return alternatives, correct_answer

def get_question_data(question):
    # Extract the question data based on name pattern
    question_info = question.find('div', class_='panel-title-box').find('h3').text.split()

    question_id = question_info[2]
    question_difficulty = question_info[3]

    return question_id, question_difficulty

def get_question_statement(question):
    [question_prompt_text, question_query_text] = get_full_statement_text(question)

    # Extract full statement info
    question_prompt_statement = ''
    question_prompt_source = ''
    image_prompt_source = ''

    if question_prompt_text:
        for p_tag in question_prompt_text.find_all('p'):
            # If there's a <small> tag, separate it as the statement_source
            small_tag = p_tag.find('small')
            if small_tag:
                question_prompt_source = small_tag.get_text(strip=True)
            else:
                # If there's an <img> tag 
                if p_tag.find('img'):
                    image_prompt_source = question_prompt_text.find('img')['src']
                question_prompt_statement += p_tag.get_text(strip=True) + ' '

    question_prompt_statement = question_prompt_statement.strip()

    # Repeat the process to the query question
    question_query_statement = ''
    question_query_source = ''
    image_query_source = ''

    for p_tag in question_query_text.find_all('p'):
        # If there's a <small> tag, separate it as the prompt_source
        small_tag = p_tag.find('small')
        if small_tag:
            question_query_source = small_tag.get_text(strip=True)
        else:
            # If there's an <img> tag
            # Handle <img> tag if present
            if p_tag.find('img'):
                image_query_source = p_tag.find('img')['src']

            question_query_statement += p_tag.get_text(strip=True) + ' '

    question_query_statement = question_query_statement.strip()

    question_statement = {
        'prompt': {
            'text': question_prompt_statement,
            'source': question_prompt_source,
            'image': image_prompt_source
        },
        'query': {
            'text': question_query_statement,
            'source': question_query_source,
            'image': image_query_source
        },
    }

    return question_statement

def get_full_statement_text(question):
    question_prompt_text = question.find('div', class_='pergunta pergunta_base')
    question_query_text = question.find('div', class_='pergunta')

    # Fix when exists pormpt and query text
    if 'pergunta_base' in question_query_text.get('class', []):
        question_query_text = question_query_text.find_next_sibling('div', class_='pergunta')

    return question_prompt_text, question_query_text
    
def main():
    logging.info('Starting the web scraping process.')

    # Connect do Database
    db_connection = connect_to_database()
    estuda_repository = EstudaRepository(db_connection)

    base_url = 'https://app.estuda.com/'
    soup = get_soup(base_url + 'questoes_provas')

    if not soup: # Check if soup is None and exit if true
        logging.error('Failed to retrieve the initial page for scraping. Exiting program.')
        sys.exit(1) 

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

        logging.info(f'Extract all question from {exam_details['name']} {exam_details['year']} {exam_details['number']}successfull')

if __name__ == '__main__':
    main()
