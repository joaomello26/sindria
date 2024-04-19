import math
import re
import logging
import requests
import sys
from bs4 import BeautifulSoup, NavigableString

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

def fetch_exams(base_url, start_page, end_page):
    # Fetch all the exams in the site database
    exams = []

    for actual_page in range(start_page, end_page):
        page_soup = get_soup(f'{base_url}questoes_provas/?inicio={actual_page}')

        if not page_soup: # Check if soup is None and exit if true
            logging.error("Failed to get the exam database page content.")
            sys.exit(1)

        exams.extend(get_exam_elements(page_soup))

    return exams

def get_exam_elements(page_soup):
    return page_soup.find_all('div', class_='col-md-4 col-sm-6 col-xs-12')

def fetch_questions_for_exam(base_url, exam_id, exam_total_questions, bot):
    # Extract the html content of all exam pages
    questions_by_page = 6 # Site pattern
    exam_pages = math.ceil(exam_total_questions / questions_by_page)
    questions = []

    # Extract html content of each exam page
    for page_number in range(1, exam_pages+1):
        page_url = f'{base_url}questoes/?prova={exam_id}&inicio={page_number}'

        page_source = bot.get_page_source(page_url)
        page_soup = BeautifulSoup(page_source, 'lxml')

        if not page_soup:
            logging.error('Failed to get exam page content.')
            sys.exit(1)

        questions.extend(get_question_elements(page_soup))

    return questions

def get_question_elements(exam_page_soup):
    return exam_page_soup.find_all('div', id=re.compile('^d_questao'))

def element_to_dict(element):
    """
    Function to convert html element to a dictionary
    Uses to save the statement and alternative structure into MongoDB
    """
    element_dict = {
        'tag': element.name,
        'content': []
    }
    
    for child in element.children:
        if isinstance(child, NavigableString):
            # Directly append strings
            element_dict['content'].append(str(child))
        else:
            # For tags, create a dictionary of tag name, attributes, and string content (if any)
            child_dict = {'tag': child.name}
            # Check if the child is an image, since it doesn't contain text
            if child.name == 'img':
                child_dict['atributes'] = child.attrs
            else:
                child_dict['text'] = child.get_text()

            element_dict['content'].append(child_dict)
    
    return element_dict
