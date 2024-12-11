import datetime
import time
import sys
import csv
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
            view_applicants_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, 'artdeco-button__text'))
            )
            view_applicants_btn.click()

            print("Navigated to applicants page")

        except Exception as e:
            print(f"Failed to navigate to applicants: {e}")
            raise

    def extract_applicant_emails(self) -> List[str]:
        """
        Extract email addresses from applicants

        :return: List of extracted email addresses
        """
        emails = []
        try:
            # Find all applicant rows
            # (Replace 'your-applicant-row-class' with actual class)
            applicant_rows = self.driver.find_elements(
                By.CLASS_NAME, 'your-applicant-row-class'
            )

            for applicant in applicant_rows:
                try:
                    # Click on applicant to open details
                    # (Replace 'your-applicant-details-button-class' with actual class)
                    applicant.find_element(
                        By.CLASS_NAME, 'your-applicant-details-button-class'
                    ).click()

                    # Wait for More button and click
                    # (Replace 'your-more-button-class' with actual class)
                    more_btn = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.CLASS_NAME, 'your-more-button-class'))
                    )
                    more_btn.click()

                    # Find and extract email
                    # (Replace 'your-email-class' with actual class)
                    email_element = self.wait.until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, 'your-email-class'))
                    )
                    emails.append(email_element.text)

                except Exception as inner_e:
                    print(
                        f"Failed to extract email for an applicant: {inner_e}")

                # Optional: Add a small delay between applicants
                time.sleep(1)

            return emails

        except Exception as e:
            print(f"Failed to extract applicant emails: {e}")
            return emails

    def save_emails_to_csv(self, emails: List[str], filename: str = None):
        """
        Save extracted emails to a CSV file

        :param emails: List of email addresses
        :param filename: Optional filename, defaults to timestamped file
        """
        if not filename:
            filename = f'linkedin_applicants_{
                datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Email'])  # Header
            for email in emails:
                writer.writerow([email])

        print(f"Saved {len(emails)} emails to {filename}")

    def run(self):
        """
        Main scraping workflow
        """
        try:
            self.login()
            self.navigate_to_job_applicants()

            # Optional: Handle pagination if needed
            # (Replace 'your-pagination-class' with actual class)
            while True:
                emails = self.extract_applicant_emails()
                self.save_emails_to_csv(emails)

                try:
                    # Try to find and click next page button
                    next_page_btn = self.driver.find_element(
                        By.CLASS_NAME, 'your-pagination-class'
                    )
                    next_page_btn.click()
                    time.sleep(2)  # Wait for page to load
                except NoSuchElementException:
                    # No more pages
                    break

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
