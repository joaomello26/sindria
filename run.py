from bs4 import BeautifulSoup
import requests
import re
import math
from models.connection_options.connection import DBConnectionHandler
from models.repository.estuda_repository import EstudaRepository
from selenium_actions import SeleniumAutomation

def connect_to_database():
    db_handle = DBConnectionHandler()
    db_handle.connect_to_db()
    return db_handle.get_db_connection()

def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'lxml')

def get_total_pages(soup):
    pagination_select = soup.find('li', class_='paginacao_paginas') 
    options = pagination_select.find_all('option')
    return int(options[-1].text)

def get_exam_elements(page_soup):
    return page_soup.find_all('div', class_='col-md-4 col-sm-6 col-xs-12')

def fetch_exam_details(exam):
    # Extract exam details
    exam_details = {
        'name': '', 
        'year': '', 
        'exam_type': 'Multiple Choice',
        'questions_number': 0
    }
    exam_data = exam.find('span', class_='btn-block').text.split()

    exam_details['name'] = exam_data[0]
    exam_details['year'] = exam_data[1]
    exam_details['questions_number'] = int(exam.find('strong').find_next('strong').text)

    # Get exam id
    exam_relative_url = exam.find('a', class_='btn btn-success')['href']
    exam_id = re.search(r'prova=(\d+)&q', exam_relative_url).group(1)

    return exam_details, exam_id

def fetch_questions_for_exam(base_url, exam_id, exam_total_questions, bot):
    questions_by_page = 6
    exam_pages = math.ceil(exam_total_questions / questions_by_page)
    questions = []

    # Iterate through each exam page
    for page_number in range(1, exam_pages+1):
        # Use bot to answer the questions and extract the correct_answer
        page_url = f'{base_url}questoes/?prova={exam_id}&inicio={page_number}'
        bot.driver.get(page_url)
        page_content = bot.get_answers()
        
        page_soup = BeautifulSoup(page_content, 'lxml')
        questions.extend(get_question_elements(page_soup))

    return questions

def get_question_elements(exam_page_soup):
    return exam_page_soup.find_all('div', id=re.compile('^d_questao'))

def extract_question_content(question):    
    [question_id, question_difficulty] = extract_question_data(question)

    question_statemennt = extract_question_statement(question)

    [question_alternatives, correct_aswer] = extract_question_alternatives(question)

    question_content = {
        'statement': question_statemennt,
        'alternatives': question_alternatives,
        'correct_answer': correct_aswer,
        'difficulty_level': question_difficulty
    }

    return question_content, question_id

def extract_question_alternatives(question):
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

def extract_question_data(question):
    question_info = question.find('div', class_='panel-title-box').find('h3').text.split()

    question_id = question_info[2]
    question_difficulty = question_info[3]

    return question_id, question_difficulty

def extract_question_statement(question):
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
    # Connect do Database
    db_connection = connect_to_database()
    estuda_repository = EstudaRepository(db_connection)

    base_url = 'https://app.estuda.com/'
    soup = get_soup(base_url + 'questoes_provas')
    total_pages = get_total_pages(soup)

    # Initialize Selenium Automation
    bot = SeleniumAutomation()
    bot.login()
    
    # Iterate through each page of the exams list
    for actual_page in range(1, total_pages + 1):
        page_soup = get_soup(f'{base_url}questoes_provas/?inicio={actual_page}')
        exams = get_exam_elements(page_soup)
        
        # Iterate through each exam to fetch details and questions
        for exam in exams:
            [exam_details, exam_id] = fetch_exam_details(exam)

            exam_total_questions = exam_details['questions_number']
            questions = fetch_questions_for_exam(base_url, exam_id, exam_total_questions, bot)
            
            for question in questions:
                [question_content, question_id] = extract_question_content(question)
                question_data = {
                    'id': question_id,
                    'exam_details': exam_details,
                    'question_content': question_content
                }
                estuda_repository.insert_document(question_data)

if __name__ == '__main__':
    main()
