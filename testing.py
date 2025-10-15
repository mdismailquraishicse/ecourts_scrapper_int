import re
import time
from PIL import Image
# import requests
import pytesseract
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By

crn = "MHAU019999992015"
chrome= Chrome()
chrome.get("https://services.ecourts.gov.in/ecourtindia_v6/")
time.sleep(1)
crn_input= chrome.find_element(By.ID, "cino")
crn_input.clear()
crn_input.send_keys(crn)
captcha_element= chrome.find_element(By.ID, "captcha_image")
captcha_element.screenshot("captcha.png")
x="fcaptcha_code"
captcha= Image.open("captcha.png")
captcha_text= pytesseract.image_to_string(captcha).strip()
cleaned_captcha= re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
print(cleaned_captcha)
f_captcha= chrome.find_element(By.ID, "fcaptcha_code")
f_captcha.clear()
f_captcha.send_keys(cleaned_captcha)
submit= chrome.find_element(By.ID, "searchbtn")
submit.click()
time.sleep(10)
chrome.quit()
