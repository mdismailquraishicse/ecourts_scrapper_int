import argparse
import json
import os
import time
from datetime import datetime
from selenium import webdriver


BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

driver = webdriver.Chrome()
driver.get(BASE_URL)
time.sleep(3)