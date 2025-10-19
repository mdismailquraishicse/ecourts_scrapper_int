# Import libraries
import re
import time
import pytesseract
from PIL import Image
import pandas as pd
from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class EcourtScrapper:
    def __init__(self):
        self._crn = None
        self._home_page_url= "https://services.ecourts.gov.in/ecourtindia_v6/"
        self._cause_list_id= "leftPaneMenuCL"
        self._close_btn_cl_class= "btn-close"
        self._close_btn_xpath= "//button[contains(@class,'btn-close')]"
        self._state_id= "sess_state_code"
        self._dist_id= "sess_dist_code"
        self._court_complex_id= "court_complex_code"
        self._court_name_id= "CL_court_no"
        self._pop_up_x= "//button[contains(@class,'btn-close')]"
        self._captcha_id= "captcha_image"
        self._court_name_id= "CL_court_no"
        self._causelist_captcha_id_to_fill= "cause_list_captcha_code"
        self._criminal_path= "//button[@onclick=\"submit_causelist('cri')\"]"
        self._civil_path= "//button[@onclick=\"submit_causelist('civ')\"]"
        self._causelist_datefill_id= "causelist_date"
        self._disp_table_id= "dispTable"
        self._driver= Chrome()
        
    def goto_home_page(self):
        self._driver.get(self._home_page_url)
        print("successfully nevigated to homepage!")

    def nevigate_to_causelist_page(self):
        cause_list= self._driver.find_element(By.ID, self._cause_list_id)
        cause_list.click()

    def close_pop_up(self):
        try:
            wait = WebDriverWait(self._driver, 10)
            close_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, self._close_btn_xpath)
                )
            )
            close_btn.click()
            print("Popup closed!")
        except Exception as e:
            print("Close button not clickable:", e)

    def get_dropdown(self, name= "West Bengal", flag=1):
        if flag==1:
            dropdown = self._driver.find_element(By.ID, self._state_id)
        elif flag==2:
            dropdown = self._driver.find_element(By.ID, self._dist_id)
        elif flag==3:
            dropdown = self._driver.find_element(By.ID, self._court_complex_id)
        elif flag==4:
            dropdown = self._driver.find_element(By.ID, self._court_name_id)
        else:
            print("Invalid flag: must be between 1-4.")
            return False
        select= Select(dropdown)
        options= select.options
        for opt in options:
            # print(opt.text, " --> ", opt.get_attribute("value"))
            pass
        # select states/distirct
        select.select_by_visible_text(name)
        print(f"selected {name}")

    def captcha_filler(self):
        captcha_element= self._driver.find_element(By.ID, self._captcha_id)
        captcha_element.screenshot("captcha.png")
        captcha= Image.open("captcha.png")
        captcha_text= pytesseract.image_to_string(captcha).strip()
        cleaned_captcha= re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
        print(cleaned_captcha)
        f_captcha= self._driver.find_element(By.ID, self._causelist_captcha_id_to_fill)
        f_captcha.clear()
        f_captcha.send_keys(cleaned_captcha)
        return True

    def click_on_button(self, case_type:str="criminal"):
        if case_type:
            if case_type.lower() == "criminal":
                xpath= self._criminal_path
            elif case_type.lower() == "civil":
                xpath= self._civil_path
        btn = self._driver.find_element(By.XPATH, xpath)
        btn.click()
        print("form submitted successfully!")

    def validate_date(self, date_:str=None):
        try:
            if date_:
                datetime.strptime(date_, "%d-%m-%Y")
                print("date validated successfully!")
                return True
        except:
            print("date format validation failed!")
            raise ValueError("Invalid date format, expected DD-MM-YYYY")

    def put_causelist_date(self, date_:str=None):
        try:
            if date_:
                date_field= self._driver.find_element(By.ID, self._causelist_datefill_id)
                date_field.clear()
                date_field.send_keys(date_)
                print("cause list date has been filled!")
        except Exception as e:
            print(f"Something went wrong!")
            print(e)

    def get_table_content(self):
        data_list = []
        try:
            try:
                table = self._driver.find_element(By.ID, self._disp_table_id)
            except NoSuchElementException:
                print("Table unavailable!")
                return "Table not found"
    
            rows = table.find_elements(By.TAG_NAME, "tr")[2:]
    
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) >= 4:
                    sr_no = cols[0].text.strip()
    
                    case_text = cols[1].text.strip()
                    case_number = case_text.split("\n")[-1]
    
                    party_name = cols[2].text.replace("\n", " ").strip()
                    advocate = cols[3].text.strip()
    
                    data_list.append({
                        "sr_no": sr_no,
                        "case_number": case_number,
                        "party_name": party_name,
                        "advocate": advocate
                    })
            df= pd.DataFrame(data_list)
            print("The extracted causelists are:")
            print(df.head())
            return df
        except Exception as e:
            print("Error while scraping:", e)
            return None
        
    def pipeline_couselist(self):
        self.goto_home_page()
        self.nevigate_to_causelist_page()
        self.close_pop_up()
        # Select state
        self.get_dropdown(name="West Bengal", flag=1)
        time.sleep(2)
        # Select district
        self.get_dropdown(name="Paschim Bardhaman", flag=2)
        time.sleep(2)
        # Select court complex
        self.get_dropdown(name="ASANSOL COURT COMPLEX", flag=3)
        time.sleep(2)
        # Select court name
        self.get_dropdown(name="9-Indrani Gupta-CJM", flag=4)
        time.sleep(2)
        # Fill date
        self.validate_date(date_="21-10-2025")
        self.put_causelist_date(date_="21-10-2025")
        time.sleep(2)
        # fill captcha
        self.captcha_filler()
        time.sleep(2)
        # Submit form
        self.click_on_button(case_type="criminal")
        time.sleep(2)
        # Get causelist
        df= self.get_table_content()
        df.to_json("cause_list.json",index=False)
if __name__=="__main__":
    ecourts_scrapper= EcourtScrapper()
    ecourts_scrapper.pipeline_couselist()