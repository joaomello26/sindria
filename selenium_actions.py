import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
class SeleniumAutomation:
    def __init__(self, driver_path="C:/SeleniumDrivers", headless=False):
        self.driver = self.configure_driver(driver_path, headless)

    def __exit__(self):
        self.quit()

    def configure_driver(self, driver_path, headless):
        os.environ['PATH'] += driver_path
        options = Options()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    def login(self):
        login_url = 'https://app.estuda.com/usuarios_login'
        email = 'alexdubugras@gmail.com'  
        password = 'sindria123'

        self.driver.get(login_url)

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'siu_email'))
        )
        self.driver.find_element(By.NAME, 'siu_email').send_keys(email)
        self.driver.find_element(By.NAME, 'siu_senha').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, '.btn.btn-info.btn-lg.btn-block.text-uppercase').click()

    def click_elements(self, elements_xpath):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, elements_xpath)))
        elements = self.driver.find_elements(By.XPATH, elements_xpath)
        for element in elements:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            element.click()

    def get_answers(self):
        alternative_xpath = '//div[@class=\'respostas form form-group\']/label[1]'
        answer_button_xpath = '//div[@class=\'respostas form form-group\']/button'

        self.click_elements(alternative_xpath)
        self.click_elements(answer_button_xpath)

        time.sleep(5) # Wait for the page load

        return self.driver.page_source
