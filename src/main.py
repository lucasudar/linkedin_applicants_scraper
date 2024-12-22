import time
import re
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


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
            self.driver.get('https://www.linkedin.com/login')

            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            username_field.send_keys(self.username)

            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)

            login_btn = self.driver.find_element(
                By.CSS_SELECTOR, 'button[type="submit"]')
            login_btn.click()

            self.wait.until(EC.url_contains('feed'))
            print("Successfully logged in to LinkedIn")
        except Exception as e:
            print(f"Login failed: {e}")
            raise

    def process_applicant(self, applicant):
        """
        Process a single applicant and return their details
        """
        try:
            applicant_link = applicant.find_element(
                By.XPATH, './/a[contains(@class, "ember-view")]')
            applicant_link.click()
            time.sleep(2)

            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.hiring-applicant-header')))

            applicant_name = self.driver.find_element(
                By.CSS_SELECTOR, '.hiring-applicant-header h1').text
            match = re.match(r"^(.*?)’s", applicant_name)
            applicant_name = match.group(1).strip() if match else "Unknown"

            location_element = self.driver.find_element(
                By.CSS_SELECTOR, ".hiring-applicant-header .t-16:nth-of-type(2)"
            )
            location = location_element.text.strip() if location_element else "Unknown location"

            more_button = self.driver.find_element(
                By.XPATH, "//button[contains(@class, 'artdeco-dropdown__trigger') and contains(@class, 'artdeco-button--secondary')]"
            )
            more_button.click()
            time.sleep(2)

            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//ul[@aria-live='polite']")))

            profile_link = self.driver.find_element(
                By.XPATH, '//a[contains(@class, "artdeco-button--tertiary")]'
            ).get_attribute("href")
            email_elements = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'mailto:')]//span[not(contains(@class, 'a11y-text'))]"
            )
            email = email_elements[0].text if email_elements else "Email not found"

            phone_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'hiring-applicant-header-actions__more-content-dropdown-item-info')]//span[not(contains(@class, 't-light'))]"
            )
            phone = phone_elements[3].text.strip() if len(
                phone_elements) >= 4 else "Phone number not found"

            return {
                "name": applicant_name,
                "location": location,
                "email": email,
                "phone": phone,
                "profile_link": profile_link,
            }
        except Exception as e:
            print(f"Error processing applicant: {e}")
            return None

    def navigate_and_process_applicants(self):
        """
        Navigate to the job applicants page, process applicants, and handle pagination
        """
        try:
            self.driver.get(self.job_url)

            view_applicants_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     '//button[contains(@class, "artdeco-button--secondary") and contains(span, "View applicants")]')
                )
            )
            view_applicants_btn.click()
            time.sleep(2)

            # delete query params from URL to unable filtering
            self.driver.get(self.driver.current_url.split("/?")[0])

            all_applicants_data = []

            try:
                pagination_items = self.driver.find_elements(
                    By.CSS_SELECTOR, "li.artdeco-pagination__indicator.artdeco-pagination__indicator--number.ember-view"
                )

                # Get the last pagination page number
                last_item = pagination_items[-1] if pagination_items else None
                total_pages = int(
                    last_item.find_element(By.CSS_SELECTOR, "button span").text
                ) if last_item else 1
                print(f"Total pages: {total_pages}")

            except Exception as e:
                print(f"Failed to determine pagination: {e}")
                total_pages = 1

            for page in range(1, total_pages + 1):
                print(f"Processing page {page}/{total_pages}")

                applicant_list = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'li.hiring-applicants__list-item'))
                )

                for applicant in applicant_list:
                    applicant_data = self.process_applicant(applicant)
                    if applicant_data:
                        all_applicants_data.append(applicant_data)

                # Navigate to the next page if not the last page
                if page < total_pages:
                    next_page_button = self.driver.find_element(
                        By.XPATH, f'//button[@aria-label="Page {page + 1}"]'
                    )
                    next_page_button.click()
                    time.sleep(3)

            return all_applicants_data
        except Exception as e:
            print(f"Error processing applicants: {e}")
            raise

    def save_applicants_to_csv(self, applicants_data, filename="applicants.csv"):
        """
        Save the collected applicant data into a CSV file

        :param applicants_data: List of applicant data (dictionaries)
        :param filename: Name of the CSV file
        """
        try:
            # Define CSV fieldnames (keys from the first applicant's dictionary)
            fieldnames = ["name", "location", "email", "phone", "profile_link"]

            # Open the CSV file in write mode
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                # Write the header row (field names)
                writer.writeheader()

                # Write the data rows
                for applicant in applicants_data:
                    writer.writerow(applicant)

            print(f"Applicant data has been successfully saved to {filename}")
        except Exception as e:
            print(f"Failed to save applicants data to CSV: {e}")

    def run(self):
        """
        Main scraping workflow
        """
        try:
            self.login()

            all_applicants_data = self.navigate_and_process_applicants()

            self.save_applicants_to_csv(all_applicants_data)

        except Exception as e:
            print(f"Scraping failed: {e}")

        finally:
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
