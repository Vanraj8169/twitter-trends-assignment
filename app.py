import datetime
from bson import ObjectId
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from flask import Flask, render_template, jsonify
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
TWITTER_URL = "https://x.com/login"

# MongoDB Setup
client = MongoClient(os.getenv('MONGO_URI'))
db = client.twitter_trends
collection = db.trends

def store_in_mongodb(trending_topics):
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
         "trend1": trending_topics[0],
        "trend2": trending_topics[1],
        "trend3": trending_topics[2],
        "trend4": trending_topics[3],
        "trend5": trending_topics[4],
        "end_time": end_time
    }
    collection.insert_one(data)
    return data

def fetching_trends():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url=TWITTER_URL)
    time.sleep(5)
    # Entering username
    driver.find_element(By.XPATH,
                        value='/html/body/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[4]/label/div/div[2]/div/input').send_keys(
        TWITTER_USERNAME, Keys.ENTER)
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(
        TWITTER_PASSWORD, Keys.ENTER)
    time.sleep(5)
    driver.get(url='https://x.com/explore/tabs/for-you')
    time.sleep(10)
    trending_topics = driver.find_elements(By.XPATH,
                                           value="//span[@class='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3']")
    scraped_data = [topic.text.strip() for topic in trending_topics]
    # Initialize an empty list to store trending topics
    trending_topics = [topic for topic in scraped_data if '#' in topic]
    store_in_mongodb(trending_topics[:5])

def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['POST'])
def run_script():
    fetching_trends()
    return jsonify({"message": "Script ran successfully"})

@app.route('/get-trends', methods=['GET'])
def get_trends():
    latest_trend = collection.find_one(sort=[('_id', -1)])
    if latest_trend:
        latest_trend['_id'] = convert_objectid(latest_trend['_id'])
    return jsonify(latest_trend if latest_trend else {})


