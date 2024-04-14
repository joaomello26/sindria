import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configure_driver():
    os.environ['PATH'] += "C:/SeleniumDrivers"
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def login(driver, url, email, password):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, 'siu_email'))
    )
    driver.find_element(By.NAME, 'siu_email').send_keys(email)
    driver.find_element(By.NAME, 'siu_senha').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, '.btn.btn-info.btn-lg.btn-block.text-uppercase').click()

def click_elements(driver, elements_xpath):
    elements = driver.find_elements(By.XPATH, elements_xpath)
    for element in elements:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        element.click()

def main():
    driver = configure_driver()
    login_url = 'https://app.estuda.com/usuarios_login'
    email = 'alexdubugras@gmail.com'  
    password = 'sindria123'  

    login(driver, login_url, email, password)

    driver.get('https://app.estuda.com/questoes/?prova=9123&q=&cat=')

    alternative_xpath = '//div[@class=\'respostas form form-group\']/label'
    answer_button_xpath = '//div[@class=\'respostas form form-group\']/button'

    click_elements(driver, alternative_xpath)
    click_elements(driver, answer_button_xpath)
    
    input("Press Enter to quit the session...")
    driver.quit()

if __name__ == "__main__":
    main()
