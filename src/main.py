import datetime
import time
import sys
import csv
import re
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains


class LinkedInApplicantScraper:
    def __init__(self, username: str, password: str, job_url: str):
        """
        Initialize the scraper with login credentials and job URL

        :param username: LinkedIn login username
        :param password: LinkedIn login password
        :param job_url: URL of the job posting
        """
        self.username = username
        self.password = password
        self.job_url = job_url

        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option(
            "useAutomationExtension", False)
        self.chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])

        # Initialize webdriver
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(
            service=self.service, options=self.chrome_options)

        # Wait timeout
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        """
        Log in to LinkedIn
        """
        try:
            # Navigate to LinkedIn login page
            self.driver.get('https://www.linkedin.com/login')

            # Wait for username field and enter credentials
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            username_field.send_keys(self.username)

            # Enter password
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)

            # Click login button
            login_btn = self.driver.find_element(
                By.CSS_SELECTOR, 'button[type="submit"]')
            login_btn.click()

            # Wait for login to complete
            self.wait.until(
                EC.url_contains('feed')
            )
            print("Successfully logged in to LinkedIn")

        except Exception as e:
            print(f"Login failed: {e}")
            raise

    def navigate_to_job_applicants(self):
        """
        Navigate to job applicants page
        """
        try:
            # Navigate to job URL
            self.driver.get(self.job_url)

            try:
                view_applicants_btn = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        '//button[contains(@class, "artdeco-button--secondary") and contains(span, "View applicants")]'
                    ))
                )
                view_applicants_btn.click()

                time.sleep(10)

            except Exception as e:
                print(f"First selector strategy failed: {e}")

            print("Navigated to applicants page")

            # Find all applicant list items
            applicant_list = self.wait.until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR, 'li.hiring-applicants__list-item'
                ))
            )

            return applicant_list

        except Exception as e:
            print(f"Failed to navigate to applicants: {e}")
            raise

    def process_applicants(self):
        """
        Process each applicant in the list
        """
        # Get the list of applicants
        applicant_list = self.navigate_to_job_applicants()

        # Collected data for all applicants
        all_applicants_data = []

        # Iterate through each applicant
        for index, applicant in enumerate(applicant_list, 1):
            try:
                # Scroll to the applicant to ensure it's in view
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", applicant)
                time.sleep(1)

                # Try multiple selector strategies
                try:
                    # First try: CSS selector
                    applicant_link = applicant.find_element(
                        By.CSS_SELECTOR, 'a.ember-view.hiring-applicants-list-item__link'
                    )
                except NoSuchElementException:
                    try:
                        # Fallback 1: XPath selector
                        applicant_link = applicant.find_element(
                            By.XPATH, './/a[contains(@class, "ember-view") and contains(@class, "hiring-applicants-list-item__link")]'
                        )
                    except NoSuchElementException:
                        # Fallback 2: More generic selector
                        applicant_link = applicant.find_element(
                            By.XPATH, './/a[contains(@class, "ember-view")]'
                        )

                # Click on the applicant link
                applicant_link.click()
                time.sleep(2)

                # Wait for applicant details to load
                self.wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, '.hiring-applicant-header'
                    ))
                )

                # Extract applicant details
                applicant_name = self.driver.find_element(
                    By.CSS_SELECTOR, '.hiring-applicant-header h1').text
                match = re.match(r"^(.*?)’s", applicant_name)
                if match:
                    applicant_name = match.group(1).strip()
                else:
                    applicant_name = "Unknown"
                location_element = self.driver.find_element(
                    By.CSS_SELECTOR, ".hiring-applicant-header .t-16:nth-of-type(2)")
                location = location_element.text.strip() if location_element else "Unknown location"

                # Find and click the "More" button
                more_button = self.driver.find_element(
                    By.XPATH, "//button[contains(@class, 'artdeco-dropdown__trigger') and contains(@class, 'artdeco-button--secondary')]"
                )
                more_button.click()

                # Wait for dropdown to load and extract email/phone
                self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, "//ul[@aria-live='polite']"
                    ))
                )

                email = self.driver.find_element(
                    By.XPATH, "//a[contains(@href, 'mailto:')]//span[not(contains(@class, 'a11y-text'))]"
                ).text
                phone_elements = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'hiring-applicant-header-actions__more-content-dropdown-item-info')]//span[not(contains(@class, 't-light'))]"
                )

                if len(phone_elements) >= 2:
                    phone = phone_elements[3].text.strip()
                else:
                    phone = "Phone number not found"

                # Save applicant data
                applicant_data = {
                    "name": applicant_name,
                    "location": location,
                    "email": email,
                    "phone": phone,
                }
                print(applicant_data)
                all_applicants_data.append(applicant_data)

                print(f"Processed applicant {index}: {applicant_name}")

                time.sleep(2)

            except Exception as applicant_error:
                print(f"Error processing applicant {index}: {applicant_error}")

        return all_applicants_data

    def navigate_to_job_applicants(self):
        """
        Navigate to job applicants page and prepare the list of applicants
        """
        try:
            # Navigate to job URL
            self.driver.get(self.job_url)

            # Wait for applicants view button and click
            view_applicants_btn = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//button[contains(@class, "artdeco-button--secondary") and contains(span, "View applicants")]'
                ))
            )
            view_applicants_btn.click()

            # Extended wait time to ensure page loads completely
            time.sleep(4)

            # Try multiple strategies to find applicant list
            try:
                # First try: CSS selector
                applicant_list = self.wait.until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, 'li.hiring-applicants__list-item'
                    ))
                )
            except TimeoutException:
                try:
                    # Fallback 1: XPath selector
                    applicant_list = self.wait.until(
                        EC.presence_of_all_elements_located((
                            By.XPATH, '//li[contains(@class, "hiring-applicants__list-item")]'
                        ))
                    )
                except TimeoutException:
                    # Fallback 2: Check if we're on the right page
                    print("Could not find applicant list. Checking page status.")

                    # Print current page source or URL for debugging
                    print("Current URL:", self.driver.current_url)
                    print("Page source snippet:",
                          self.driver.page_source[:1000])

                    raise Exception("Unable to locate applicant list")
            try:
                pagination_items = self.driver.find_elements(
                    By.CSS_SELECTOR, "li.artdeco-pagination__indicator.artdeco-pagination__indicator--number.ember-view"
                )

                # Get the last pagination item
                last_item = pagination_items[-1] if pagination_items else None

                if last_item:
                    # Find the page number inside the button -> span tag
                    page_number = last_item.find_element(By.CSS_SELECTOR, "button span").text
                    print(f"The last pagination page has number: {page_number}")
                else:
                    print("No pagination items found.")
            except Exception as e:
                print(f"Failed to find pagination items: {e}")

            print(f"Found {len(applicant_list)} applicants")
            return applicant_list

        except Exception as e:
            print(f"Failed to navigate to applicants: {e}")
            return []

    def run(self):
        """
        Main scraping workflow
        """
        try:
            self.login()

            # Process all applicants and collect their data
            all_applicants_data = self.process_applicants()

            # Save to CSV if data is collected
            if all_applicants_data:
                self.save_applicants_to_csv(all_applicants_data)
            else:
                print("No applicant data collected")

        except Exception as e:
            print(f"Scraping failed: {e}")

        finally:
            # Always close the browser
            self.driver.quit()


def main():
    # Load credentials from config (example)
    from jproperties import Properties

    configs = Properties()
    with open('../config/app-config.properties', 'rb') as config_file:
        configs.load(config_file)

    username = configs.get('username').data
    password = configs.get('password').data
    job_url = configs.get('url').data

    # Initialize and run scraper
    scraper = LinkedInApplicantScraper(username, password, job_url)
    scraper.run()


if __name__ == "__main__":
    main()
