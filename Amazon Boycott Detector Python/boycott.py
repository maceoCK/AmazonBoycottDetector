from bs4 import BeautifulSoup
import requests
from consts import HEADERS

class BoycottDetector:
    def __init__(self):
        self.boycottList = self.createBoycottList()
        self.personal_boycott_list = set()  # Initialize an empty set for the personal boycott list

    def createBoycottList(self):
        URL = "https://www.ethicalconsumer.org/ethicalcampaigns/boycotts"

        try:
            ethicalConsumerBoycott = requests.get(URL, headers=HEADERS)
            ethicalConsumerBoycott.raise_for_status()  # Raise an exception if there's an HTTP error
            ethicalBoycottSoup = BeautifulSoup(ethicalConsumerBoycott.content, "html.parser")
            boycott_items = ethicalBoycottSoup.find_all("div", class_="tile boycott")

            titles = [item.h3.text.strip() for item in boycott_items]
            return titles
        except requests.exceptions.RequestException as e:
            print("Error fetching boycott list:", e)
            return None

    def load_personal_boycott_list(self, file_path):
        try:
            with open(file_path, "r") as file:
                for line in file:
                    company = line.strip()
                    self.personal_boycott_list.add(company)
        except FileNotFoundError:
            print("Personal boycott list file not found. Creating a new one.")
        except Exception as e:
            print("Error loading personal boycott list:", e)

    def add_to_personal_boycott_list(self, company):
        self.personal_boycott_list.add(company)

    def save_personal_boycott_list(self, file_path):
        try:
            with open(file_path, "w") as file:
                for company in self.personal_boycott_list:
                    file.write(company + "\n")
        except Exception as e:
            print("Error saving personal boycott list:", e)
