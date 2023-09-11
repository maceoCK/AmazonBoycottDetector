import sys
import os
from PyQt5 import QtWidgets
from selenium import webdriver
from bs4 import BeautifulSoup
from boycott import BoycottDetector
from consts import HEADERS

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Boycott Detector")
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.url_label = QtWidgets.QLabel("Amazon Product URL:")
        self.layout.addWidget(self.url_label)

        self.url_input = QtWidgets.QLineEdit()
        self.layout.addWidget(self.url_input)

        self.check_button = QtWidgets.QPushButton("Check Product")
        self.check_button.clicked.connect(self.check_product)
        self.layout.addWidget(self.check_button)

        self.result_text = QtWidgets.QTextEdit()
        self.result_text.setReadOnly(True)
        self.layout.addWidget(self.result_text)

        # Add a button for adding to the personal boycott list
        self.add_to_boycott_button = QtWidgets.QPushButton("Add to Boycott List")
        self.add_to_boycott_button.clicked.connect(self.add_to_boycott_list)
        self.layout.addWidget(self.add_to_boycott_button)
        self.add_to_boycott_button.hide()  # Initially hide the button

        self.load_personal_boycott_list()  # load the personal boycott list

    def check_product(self):
        url = self.url_input.text()

        try:
            # Initialize a Selenium WebDriver (e.g., Chrome)
            driver = webdriver.Chrome()
            driver.get(url)

            # Wait for the page to load (you may need to customize the wait time)
            driver.implicitly_wait(10)

            # Get the page source after JavaScript execution
            page_source = driver.page_source

            amazonSoup = BeautifulSoup(page_source, "html.parser")
            detector = BoycottDetector()

            productTitleElement = amazonSoup.find("h1", attrs={"id": "title", "class": "a-size-large a-spacing-none"})
            productMakerElement = amazonSoup.find("tr", class_="a-spacing-small po-brand")

            productTitle = productTitleElement.text.strip() if productTitleElement else "Unknown Product"
            productMaker = productMakerElement.text.strip() if productMakerElement else "Unknown Maker"

            boycotted = False

            if detector.boycottList:
                for product in detector.boycottList:
                    if productMaker[8:].lower() == product.lower():
                        result_text = f"{productTitle} is on the boycott list because {productMaker[8:]} makes it.\nTo find out more visit https://www.ethicalconsumer.org/ethicalcampaigns/boycotts"
                        boycotted = True
                        self.add_to_boycott_button.show()  # Show the button to add to personal boycott list
                        break
            if not boycotted:
                # Check if the company is in the personal boycott list
                if productMaker in self.boycott_list:
                    result_text = f"{productTitle} is on the boycott list because {productMaker} (personal boycott list) makes it.\nTo find out more visit https://www.ethicalconsumer.org/ethicalcampaigns/boycotts"
                    boycotted = True
                    self.add_to_boycott_button.show()  # Show the button to add to personal boycott list

            if not boycotted:
                result_text = f"{productTitle} is not on the boycott list because {productMaker} does not have an active boycott."
                self.add_to_boycott_button.hide()  # Hide the button if not boycotted

            # Call the get_product_country function using self
            country = self.get_product_country(amazonSoup)
            if country:
                result_text += f"\nThis product was made in {country}."
                if country == "China":
                    result_text += "\n\nWARNING: This product was made in China. It is possible that it was made with forced labor. Some people have decided to boycott all products made in China because of this. Find out more here: https://www.ethicalconsumer.org/boycotts/boycotts-list"
            else:
                result_text += "\n\nWARNING: Unable to check the country of origin. This product may have been made in an unsafe working environment. It is possible that it was made with forced labor. Some people have decided to boycott all products made in China because of this. Find out more here: https://www.ethicalconsumer.org/boycotts/boycotts-list"

            self.result_text.setPlainText(result_text)
            
        except Exception as e:
            self.result_text.setPlainText(f"Error: {str(e)}")
            self.add_to_boycott_button.hide()  # Hide the button on error

        finally:
            driver.quit()  # Close the WebDriver



    def get_product_country(self, amazonSoup):
        try:
            # Find the list item (li) containing "Country of Origin"
            country_element = amazonSoup.find("li", text="Country of Origin")
            if country_element:
                # Extract the country information from the next sibling ul
                ul_element = country_element.find_next("ul", class_="a-unordered-list")
                if ul_element:
                    # Find the span containing the country name
                    country_span = ul_element.find("span", class_="a-list-item")
                    if country_span:
                        return country_span.text.strip()
        except Exception as e:
            print("Error while checking product country:", e)

        return None
    
    def load_personal_boycott_list(self):
        self.boycott_list = set()  # Initialize the boycott_list as an empty set
        try:
            with open("personal_boycott_list.txt", "r") as file:
                for line in file:
                    company = line.strip()
                    self.boycott_list.add(company)
        except FileNotFoundError:
            print("Personal boycott list file not found.")
        except Exception as e:
            print("Error loading personal boycott list:", e)

    def add_to_boycott_list(self):
        # Get the text from the result text
        result_text = self.result_text.toPlainText()

        # Check if the company information is found in the result text
        if "because" in result_text:
            # Extract the company name
            start_index = result_text.index("because") + len("because")
            end_index = result_text.find(" makes it.")
            if end_index == -1:
                end_index = result_text.find(" does not have an active boycott.")

            if end_index != -1:
                productMaker = result_text[start_index:end_index].strip()
                
                # Check if the company is already in the personal boycott list
                if productMaker not in self.boycott_list:
                    self.boycott_list.add(productMaker[8:])

                    # Save the personal boycott list to a text file
                    with open("personal_boycott_list.txt", "w") as file:
                        for company in self.boycott_list:
                            file.write(company + "\n")

                    # Notify the user that the company has been added to the personal boycott list
                    QtWidgets.QMessageBox.information(self, "Added to Boycott List", f"{productMaker[8:]} has been added to your personal boycott list.")
                else:
                    # Notify the user that the company is already boycotted
                    QtWidgets.QMessageBox.information(self, "Already Boycotted", f"{productMaker[8:]} is already in your personal boycott list.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Unable to extract company name from the result text.")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Company information not found in the result text.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
