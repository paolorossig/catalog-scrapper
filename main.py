import json
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By

import config


class SaveData:
    def __init__(self, data, file_name, base_url):
        self.data = data
        self.file_name = file_name
        self.base_url = base_url
        report = {
            "title": self.file_name,
            "date": self.get_now(),
            "base_url": self.base_url,
            "data": self.data,
        }
        print("Creating report...")
        with open(f"reports/{file_name}.json", "w") as f:
            json.dump(report, f)
        print("Report created!")

    @staticmethod
    def get_now():
        now = datetime.now()


class Scrapper:
    def __init__(self, base_url):
        self.base_url = base_url
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        options.add_argument("--window-size=1080,920")
        self.driver = webdriver.Chrome(config.DRIVER_PATH, chrome_options=options)

    def run(self, max_iters=None):
        print("Starting scrapper...")
        print(f"Looking at {self.base_url} for categories...")
        category_links = self.get_category_links()
        if not category_links:
            print("No categories found!")
            return
        print(f"Found {len(category_links)} category links!")

        data = {}
        iters = 0
        for link in category_links:
            if iters == max_iters:
                break
            iters += 1

            self.driver.get(link)
            print(f"Looking at {link} for products...")

            page = 0
            result = True
            product_links = []
            while result:
                page += 1
                print(f"Looking at page {page}...")
                product_links.extend(self.get_product_links())
                result, next_element = self.has_next_products_page()
                if result:
                    next_element.click()
                    time.sleep(1)
            if not product_links:
                print("No products found!")
                return
            print(f"Found {len(product_links)} product links!")
            data[link] = product_links

        self.driver.quit()
        return data

    def get_category_links(self):
        self.driver.get(self.base_url)
        menu_element = self.driver.find_element(By.CLASS_NAME, "menu")
        menu_element.click()
        super_element = self.driver.find_element(By.CLASS_NAME, "main-category")
        super_element.click()
        result_list = self.driver.find_element(by=By.CLASS_NAME, value="categories")
        links = []
        try:
            results = result_list.find_elements(by=By.XPATH, value=".//div/div/a")
            links = [link.get_attribute("href") for link in results]
        except Exception as e:
            print("Didn't get any categories")
            print(e)
        return links

    def get_product_links(self):
        result_list = self.driver.find_element(by=By.CLASS_NAME, value="items")
        links = []
        try:
            results = result_list.find_elements(
                by=By.XPATH, value=".//ul/li/section/div/a"
            )
            links = [link.get_attribute("href") for link in results]
        except Exception as e:
            print("Didn't get any products")
            print(e)
        return links

    def has_next_products_page(self):
        next_element = self.driver.find_element(
            By.CLASS_NAME, "Pagination"
        ).find_element(by=By.CLASS_NAME, value="next")
        classes_next_button = next_element.get_attribute("class").split()
        return "disabled" not in classes_next_button, next_element

    @staticmethod
    def get_main_route(url):
        return url.split("/")[3]

    @staticmethod
    def unstructure_product_route(route):
        route_values = route.split("-")
        brand_name = route_values.pop(0)
        product_retailer_id = route_values.pop()
        product_name = " ".join(route_values)
        return brand_name, product_retailer_id, product_name


if __name__ == "__main__":
    scrapper = Scrapper(config.BASE_URL)
    data = scrapper.run(max_iters=config.MAX_ITERS)
    SaveData(data, config.FILE_NAME, config.BASE_URL)
