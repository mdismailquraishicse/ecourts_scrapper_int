import re
import time
from PIL import Image
# import requests
import pytesseract
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.ui import Select


cause_list_id= "leftPaneMenuCL"
close_btn_cl_class= "btn-close"
crn = "MHAU019999992015"

chrome= Chrome()
chrome.get("https://services.ecourts.gov.in/ecourtindia_v6/")
time.sleep(1)
cause_list= chrome.find_element(By.ID, cause_list_id)
cause_list.click()
# close_btn= chrome.find_element(By.CLASS_NAME, close_btn_cl_class)
# close_btn.click()
try:
    wait = WebDriverWait(chrome, 10)
    close_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class,'btn-close')]")
        )
    )
    close_btn.click()
    print("Popup closed!")
except Exception as e:
    print("Close button not clickable:", e)

# DROP DOWN STATE
dropdown = chrome.find_element(By.ID, "sess_state_code")
select= Select(dropdown)
options= select.options
time.sleep(2)
for opt in options:
    print(opt.text, " --> ", opt.get_attribute("value"))
time.sleep(2)
# SELECT THE STATE
select.select_by_visible_text("West Bengal")
print("stated selected")
time.sleep(5)
# DROPDOWN DIST
try:
    district_dropdown = WebDriverWait(chrome, 10).until(
        EC.presence_of_element_located((By.ID, "sess_dist_code"))
    )
    district_select = Select(district_dropdown)

    # Get district options (skip default "Select district")
    district_options = [
        opt.text.strip()
        for opt in district_select.options
        if opt.get_attribute("value") != "0"
    ]

    print("Districts in West Bengal:")
    for district in district_options:
        print("-", district)

# SELECT DIST
    district_select.select_by_visible_text("Paschim Bardhaman")
    print("district selected")
    time.sleep(5)
except Exception as e:
    print("District dropdown not found:", e)
# COURT COMPLEX
try:
    # Wait for court complex dropdown to appear
    court_complex_dropdown = WebDriverWait(chrome, 10).until(
        EC.presence_of_element_located((By.ID, "court_complex_code"))
    )
    court_complex_select = Select(court_complex_dropdown)

    # ✅ Option 1: Select by visible text
    court_complex_select.select_by_visible_text("ASANSOL COURT COMPLEX")
    print("Selected: ASANSOL COURT COMPLEX")

    # ✅ (Optional) Small delay to let JS load dependent data
    time.sleep(2)

except Exception as e:
    print("Court complex dropdown not found or option not selectable:",e)
    
# crn_input= chrome.find_element(By.ID, "cino")
# crn_input.clear()
# crn_input.send_keys(crn)
# captcha_element= chrome.find_element(By.ID, "captcha_image")
# captcha_element.screenshot("captcha.png")
# x="fcaptcha_code"
# captcha= Image.open("captcha.png")
# captcha_text= pytesseract.image_to_string(captcha).strip()
# cleaned_captcha= re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
# print(cleaned_captcha)
# f_captcha= chrome.find_element(By.ID, "fcaptcha_code")
# f_captcha.clear()
# f_captcha.send_keys(cleaned_captcha)
# submit= chrome.find_element(By.ID, "searchbtn")
# submit.click()
# time.sleep(10)
chrome.quit()
