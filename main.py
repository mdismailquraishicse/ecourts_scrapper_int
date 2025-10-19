from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ecourt_scrapper import EcourtScrapper
import time
from selenium.webdriver.common.by import By
app = FastAPI()
ecourt_scrapper= EcourtScrapper()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def fetch_states_from_api():
    ecourt_scrapper.goto_home_page()
    ecourt_scrapper.nevigate_to_causelist_page()
    ecourt_scrapper.close_pop_up()
    # ecourt_scrapper.get_dropdown(name="West Bengal", flag=1)
    time.sleep(2)
    states= ecourt_scrapper.get_dropdown(flag=1)
    return states

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/get-states")
async def get_states():
    states = fetch_states_from_api()
    return JSONResponse({"states": states})

@app.get("/get-districts/{state}")
async def get_districts(state: str):
    ecourt_scrapper.select_from_dropdown(state)
    time.sleep(2)
    districs= ecourt_scrapper.get_dropdown(flag=2)
    return JSONResponse({"districts": districs})

@app.get("/get-complexes/{state}/{district}")
async def get_complexes(district: str):
    ecourt_scrapper.select_from_dropdown(district)
    time.sleep(2)
    complex_name= ecourt_scrapper.get_dropdown(flag=3)
    return JSONResponse({"complexes": complex_name})

@app.get("/get-courts/{state}/{district}/{complex_name}")
async def get_courts(complex_name: str):
    ecourt_scrapper.select_from_dropdown(complex_name)
    time.sleep(2)
    courts= ecourt_scrapper.get_dropdown(flag=4)
    return JSONResponse({"courts": courts})

@app.get("/submit-criminal/{state}/{district}/{complex_name}/{court}/{date_}")
async def submit_criminal(court:str, date_:str):
    ecourt_scrapper.select_from_dropdown(court)
    ecourt_scrapper.validate_date(date_)
    time.sleep(2)
    ecourt_scrapper.validate_date(date_)
    ecourt_scrapper.put_causelist_date(date_)
    time.sleep(2)
    for i in range(5):
        try:
            ecourt_scrapper.captcha_filler()
            ecourt_scrapper.click_on_button("criminal")
            time.sleep(2)
            df= ecourt_scrapper.get_table_content()
            df.to_json("result.json", index=False)
            break
        except:
            print("captcha wrong!")
            refresh_btn = ecourt_scrapper._driver.find_element(By.CLASS_NAME, "refresh-btn")
            refresh_btn.click()
            time.sleep(2)

@app.get("/submit-civil/{state}/{district}/{complex_name}/{court}")
async def submit_civil(court:str):
    ecourt_scrapper.select_from_dropdown(court)
    time.sleep(2)
    ecourt_scrapper.captcha_filler()
    ecourt_scrapper.click_on_button("civil")
