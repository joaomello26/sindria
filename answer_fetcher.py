import requests
import logging

COOKIES = {
    '_gcl_au': '1.1.1109738901.1712798303',
    '_tt_enable_cookie': '1',
    '_ttp': '0pabkc3XYIr6SdBoHlcAR0jZN2J',
    'cconsent': '{"version":1,"categories":{"necessary":{"wanted":true},"optional":{"wanted":true}},"services":["estuda","kustomer","analytics","intercom","sumo","hotjar","mautic","facebook","lomadee"]}',
    '__gads': 'ID=2e58a9798f67eb61:T=1712974028:RT=1712974028:S=ALNI_Mbgq1H_r_YrQpyt3oBM-CMPZ7-Chw',
    '__gpi': 'UID=00000a1c9c35a411:T=1712974028:RT=1712974028:S=ALNI_MY-Z9rdgdDQJsnZS7sqzREX3SrgYg',
    '__eoi': 'ID=d8431ea969744e4f:T=1712974028:RT=1712974028:S=AA-Afja5DjJz1_FvhcnUByWLz1KG',
    'usuario_cid': '1',
    'usuario_plano': 'premium+med',
    'prism_612835046': '96e34258-0070-40a1-aa34-4cf3d2c6cc62',
    '_gid': 'GA1.2.1773449048.1713191028',
    '_fbp': 'fb.1.1713316842211.281484939',
    'lmd_orig': 'organic',
    'lmd_traf': 'organic-1713333638112',
    'PHPSESSID': '7bf5338d455f06fe2778efd21c55c049',
    '_clck': 'p42e4u%7C2%7Cfl1%7C0%7C1562',
    'activecampaign_enviar': 'sim',
    '_ga_E0B5CVS8QL': 'GS1.2.1713459351.9.1.1713460364.0.0.0',
    '_ga_8EQEGP3C38': 'GS1.1.1713459350.11.1.1713460367.56.0.778939301',
    'usuario': '11568195',
    'usuario_chave': '5a6920f9b9394caaffb5bc823c0e9fa9',
    '_gat_UA-153603-31': '1',
    '_ga_4V70M1VTMB': 'GS1.1.1713459157.28.1.1713462042.50.0.1957324093',
    '_ga': 'GA1.1.1066286805.1712798305',
    '_clsk': 'kahq9y%7C1713462043364%7C13%7C1%7Ci.clarity.ms%2Fcollect',
}

HEADERS = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://app.estuda.com',
    'priority': 'u=1, i',
    'referer': 'https://app.estuda.com/questoes/',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

DATA = {
    'resposta': '0',
    'resposta_discursiva': '',
    'resolver': '',
    'prova': '',
    'inicio': '',
    'trilha_estudo_conteudo': '',
    'max_itens': '0',
    'ignorar_questoes': '',
    'tipo_questao': '',
    'q': '',
    'cat': '',
    'dificuldade[]': '',
}

def make_post_request(question_id):
    params = {
        'acao': 'questoes_resposta',
        'id': question_id,
        'tempo': '180',
        'resolver': ''
    }

    response = requests.post('https://app.estuda.com/apps/api/', params=params, cookies=COOKIES, headers=HEADERS, data=DATA)
    return response

def get_correct_answer(question_id):
    response = make_post_request(question_id)
    
    correct_answer = response.json()['questoes_resposta'][0]['resposta']

    if not correct_answer:
        logging.info(f'Don\'t get correct answer of question: {question_id}')
        return ''
    else:
        # Transform number into letter (+64) considering that counting starts at 0 (+1)
        return chr(int(correct_answer) + 65)

    