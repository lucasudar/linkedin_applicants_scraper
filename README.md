# LinkedIn Applicant Scraper

This project is a LinkedIn applicant scraping tool built using Python and Selenium. It automates the process of logging into LinkedIn, navigating to a specific job posting, collecting applicant data (name, location, email, phone, and profile link), and saving this data into a CSV file.

## Features

- **Login to LinkedIn**: The scraper can log into LinkedIn using provided credentials.
- **Navigate to Job Postings**: Once logged in, it navigates to a specified job URL to collect applicant data.
- **Collect Applicant Data**: For each applicant, it gathers key details such as:
  - Name
  - Location
  - Email
  - Phone number
  - LinkedIn profile link
- **Handle Pagination**: The scraper handles pagination and processes all applicants across multiple pages.
- **Save to CSV**: After collecting data, it saves the information into a CSV file for further analysis or processing.

## Requirements

Before running the scraper, ensure that you have the following dependencies installed:

- Python 3.x
- `pip` (Python package installer)

You can install the necessary Python packages using the following command:

```bash
pip install -r requirements.txt
```

Setup and Configuration
1.	Clone the Repository:
    Clone this project to your local machine:
```bash
git clone https://github.com/lucasudar/linkedin_applicants_scraper.git
```
2.	Configure LinkedIn Credentials:
    Create a configuration file app-config.properties with your LinkedIn credentials and job URL.
    Example app-config.properties file:
```bash
username=your_linkedin_username
password=your_linkedin_password
url=https://www.linkedin.com/jobs/view/job-id
```
3. Setup your env.
4. Run script.