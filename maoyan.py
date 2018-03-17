from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import *
import pymongo
import re

browser = webdriver.Chrome()
#browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
#browser.set_window_size(1400, 900)
wait = WebDriverWait(browser, 10)
client = pymongo.MongoClient(MONGO_RUL, MONGO_PORT)
db = client[MONGO_DB]
collection = db[MONGO_TABLE]
def search():
    browser.get("https://www.taobao.com")
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        input.send_keys('美食')
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        return total.text
    except TimeoutException:
        return search()

def next_page(page_num):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_num)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_num))
        )
        get_product()
    except TimeoutException:
        next_page(page_num)

def get_product():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.m-itemlist .items .item')))
    html = browser.page_source
    doc = BeautifulSoup(html, 'lxml')
    items = doc.select('.m-itemlist .items .item')
    for item in items:
        goods_img = item.select_one('.pic img.J_ItemPic.img')['src']
        goods_price = item.select_one('.ctx-box .price strong').get_text()
        goods_title = item.select_one('.ctx-box a.J_ClickStat').get_text()
        shop_name = item.select('.ctx-box .shop .shopname > span')[1].get_text()
        collection.insert({
            'goods_img': goods_img,
            'goods_price': goods_price,
            'goods_title': goods_title,
            'shop_name': shop_name
        })
if __name__ == '__main__':
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total + 1):
        next_page(i)
    client.close()
    browser.close()