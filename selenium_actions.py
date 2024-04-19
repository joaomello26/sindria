import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
class SeleniumAutomation:
    def __init__(self, driver_path="C:/SeleniumDrivers", headless=False):
        self.driver = self.configure_driver(driver_path, headless)

    def __exit__(self):
        self.driver.quit()

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
    
    def navigate_to_page(self, url):
        try:
            self.driver.get(url)
            # logging.info(f'Successfully navigated to {url}')
        except Exception as e:
            logging.error(f'Failed to navigate to {url} due to {e}')

    def login(self):
        login_url = 'https://app.estuda.com/usuarios_login'
        email = 'alexdubugras@gmail.com'  
        password = 'sindria123'

        self.navigate_to_page(login_url)

        try:
            # Ensure the email input is clickable and ready for input
            email_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, 'siu_email'))
            )
            email_input.send_keys(email)  # Send email to the input field

            # Input password
            password_input = self.driver.find_element(By.NAME, 'siu_senha')
            password_input.send_keys(password)

            # Click the login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, '.btn.btn-info.btn-lg.btn-block.text-uppercase')
            login_button.click()

            logging.info('Login successful')
        except TimeoutException:
            logging.warning('Element not clickable within timeout period.')
        except NoSuchElementException:
            logging.error('Element not found on the page.')
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}')

    def get_page_source(self, url):
        self.navigate_to_page(url)
        time.sleep(3) # Wait for the page load

        return self.driver.page_source

    def clean_account(self):
        clean_account_url = 'https://app.estuda.com/usuarios_limpar'

        self.navigate_to_page(clean_account_url)

        try:
            # Ensure the check button is clickable
            check_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, 'limpar'))
            )
            check_box.click()

            # Click in the confirmation clean button
            clean_button_xpath = '//div[@class=\'panel-footer\']/button'
            clean_button = self.driver.find_element(By.XPATH, clean_button_xpath)
            clean_button.click()

            logging.info('Clean account successful')
        except TimeoutException:
            logging.warning('Element not clickable within timeout period.')
        except NoSuchElementException:
            logging.error('Element not found on the page.')
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}')
