import threading
import logging
import re
from scraping_utils import get_soup, fetch_exams, fetch_questions_for_exam, element_to_dict
from selenium_actions import SeleniumAutomation
from models.repository.estuda_repository import EstudaRepository

class EstudaScraperAPI:
    def __init__(self, db_connection, base_url):
        self.repository = EstudaRepository(db_connection)
        self.base_url = base_url
        self.total_pages = self.get_total_pages()

    def get_total_pages(self):
        # Determines the total number of pages of exam database
        soup = get_soup(self.base_url + 'questoes_provas')

        pagination_select = soup.find('li', class_='paginacao_paginas') 
        options = pagination_select.find_all('option')
        return int(options[-1].text)

    def execute_fetching_multithreaded(self):
        logging.info('Starting fetch multithread')

        # Assigns a page to each thread
        threads_count = 1 #self.total_pages
        threads = []
        
        for i in range(threads_count):
            start_page = 10 + i
            end_page = start_page + 1

            thread = threading.Thread(target=self.execute_fetching_batch, args=(start_page, end_page))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def execute_fetching_batch(self, start_page, end_page):
        exams = fetch_exams(self.base_url, start_page, end_page)
        logging.info(f'Fetch exams from page {start_page} successfull')

        # Initialize Selenium Automation
        bot = SeleniumAutomation()

        # Iterate through each exam to extract details and questions
        for exam in exams:
            exam_details = self.get_exam_details(exam)
            exam_id = self.get_exam_id(exam)

            exam_total_questions = exam_details['questions_number']
            questions = fetch_questions_for_exam(self.base_url, exam_id, exam_total_questions, bot)
            
            for question in questions:
                [question_content, question_id] = self.assemble_question_content(question)
                question_data = {
                    'id': question_id,
                    'exam_details': exam_details,
                    'question_content': question_content
                }

                self.repository.insert_document(question_data)

            logging.info(f'Extract all question from {exam_details['name']} {exam_details['year']} {exam_details['number']} successfull')

    def get_exam_details(self, exam):
        # Extract exam details based on the name pattern
        exam_data = exam.find('span', class_='btn-block').get_text(strip=True)
        
        data_pattern = r'^([\w]+) (\d{4})(?:/(\d+))?(?:\s+.*)?$'
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

    def get_exam_id(self, exam):
        # Extract the exam id based on the url pattern
        exam_relative_url = exam.find('a', class_='btn btn-success')['href']
        exam_id = re.search(r'prova=(\d+)&q', exam_relative_url).group(1)

        return exam_id
    
    def assemble_question_content(self, question):    
        question_statemennt = self.get_question_statement(question) 
        question_topics = self.get_question_topics(question)
        question_alternatives = self.get_question_alternatives(question)
        [question_id, question_difficulty] = self.get_question_data(question)

        question_content = {
            'statement': question_statemennt,
            'topics': question_topics,
            'alternatives': question_alternatives,
            'correct_answer': '',
            'difficulty_level': question_difficulty
        }

        return question_content, question_id

    def get_question_statement(self, question):
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

    def get_question_topics(self, question):
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

    def get_question_alternatives(self, question):
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

    def get_question_data(self, question):
        # Extract the question data based on name pattern
        question_info = question.find('div', class_='panel-title-box').find('h3').text.split()

        question_id = question_info[2]
        question_difficulty = question_info[3]

        return question_id, question_difficulty
