from bs4 import BeautifulSoup
import requests
import re
import math

from models.connection_options.connection import DBConnectionHandler
from models.repository.estuda_repository import EstudaRepository

db_handle = DBConnectionHandler()
db_handle.coonect_to_db()
db_connection = db_handle.get_db_connection()
estuda_repository = EstudaRepository(db_connection)

base_url = 'https://app.estuda.com/'
    
html_text = requests.get(base_url + 'questoes_provas').text
soup = BeautifulSoup(html_text, 'lxml')

# Find the number of pages
pagination_select = soup.find('li', class_='paginacao_paginas') 
options = pagination_select.find_all('option')
total_pages = int(options[-1].text)

# Iterare through each page
for actual_page in range(1, total_pages + 1):
    page_html_text = requests.get(base_url + 'questoes_provas/?inicio=' + str(actual_page)).text
    page_soup = BeautifulSoup(page_html_text, 'lxml')

    # Find all exam elements
    exams = page_soup.find_all('div', class_='col-md-4 col-sm-6 col-xs-12')

    # Iterate through each exam
    for exam in exams:
        # Extract exam details
        exam_data = exam.find('span', class_='btn-block').text.split()
        exam_name = exam_data[0]
        exam_year = exam_data[1]

        # Extract the number of questions and page of each exam
        exam_total_questions = int(exam.find('strong').find_next('strong').text)
        exam_pages = math.ceil(exam_total_questions / 6)
        
        # Extract the exam id and create base url
        exam_relative_url = exam.find('a', class_='btn btn-success')['href']
        exam_number_id = re.search(r'prova=(\d+)&q', exam_relative_url).group(1)
        exam_base_url = base_url + 'questoes/?resolver=&prova=' + exam_number_id + '&inicio='

        # Iterate through each exam page
        for actual_exam_page in range(1, exam_pages + 1):
            exam_page_url = base_url + 'questoes/?resolver=&prova=' + exam_number_id + '&inicio=' + str(actual_exam_page)
            exam_page_html_text = requests.get(exam_page_url).text
            exam_page_soup = BeautifulSoup(exam_page_html_text, 'lxml')

            # Find all exam questions
            questions = exam_page_soup.find_all('div', id=re.compile('^d_questao'))       
        
            # Iterate through each question element
            for question in questions:
        
                # Extract the question name and diffiiculty
                question_info = question.find('div', class_='panel-title-box').find('h3').text.split()
                question_name = question_info[0] + ' ' + question_info[1]
                question_id = question_info[2]
                question_difficulty = question_info[3]

                # Extract full statement info
                question_prompt_text = question.find('div', class_='pergunta pergunta_base')
                question_query_text = question.find('div', class_='pergunta')

                # Fix when exists pormpt and query text
                if 'pergunta_base' in question_query_text.get('class', []):
                    question_query_text = question_query_text.find_next_sibling('div', class_='pergunta')

                # Initialize an empty string to hold the concatenated statement text
                question_prompt_statement = ""
                prompt_source = ""

                question_query_statement = ""
                query_source = ""

                # Find all <p> tags in prompt question and process their content
                if question_prompt_text:
                    for p_tag in question_prompt_text.find_all('p'):
                        # If there's a <small> tag, separate it as the prompt_source
                        small_tag = p_tag.find('small')
                        if small_tag:
                            prompt_source = small_tag.get_text(strip=True)
                        else:
                            # If there's an <img> tag or the paragraph is empty, skip it
                            if p_tag.find('img') or not p_tag.get_text(strip=True):
                                continue
                            question_prompt_statement += p_tag.get_text(strip=True) + ' '

                    question_prompt_statement = question_prompt_statement.strip()

                # Repeat the process to the query question
                for p_tag in question_query_text.find_all('p'):
                    # If there's a <small> tag, separate it as the prompt_source
                    small_tag = p_tag.find('small')
                    if small_tag:
                        query_source = small_tag.get_text(strip=True)
                    else:
                        # If there's an <img> tag or the paragraph is empty, skip it
                        if p_tag.find('img') or not p_tag.get_text(strip=True):
                            continue
                        question_query_statement += p_tag.get_text(strip=True) + ' '

                question_query_statement = question_query_statement.strip()

                # Extract the image source
                # Assuming there's only one <img> at the prompt and query
                if question_prompt_text:
                    image_prompt_tag = question_prompt_text.find('img')
                    image_prompt_source = image_prompt_tag['src'] if image_prompt_tag else ''
                else:
                    image_prompt_source = ''  # Ensure default is set if 'question_query_text' is None
                
                image_query_tag = question_query_text.find('img')
                image_query_source = image_query_tag['src'] if image_query_tag else ''

                # Extract the all alternatives info
                alternatives = question.find_all('div', class_='d-flex flex-row')
                all_alternatives = []

                # Iterate through each alternative element
                for index, alternative in enumerate(alternatives, start=1):
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

                    all_alternatives.append(alternative_data)
            
                question_data = {
                    "id": question_id,
                    "exam_details": {
                        "name": exam_name,
                        "year": exam_year,
                        "exam_type": "Multiple Choice",
                        "questions_number": exam_total_questions
                    },
                    "question_content": {
                        "statement": {
                            "prompt": {
                                "text": question_prompt_statement,
                                "image": image_prompt_source,
                                "source": prompt_source
                            },
                            "query": {
                                "text": question_query_statement,
                                "image": image_query_source,
                                "source": query_source
                            },
                        },
                        "alternatives": all_alternatives,
                        "difficulty_level": question_difficulty
                    }
                }

                estuda_repository.insert_document(question_data)
