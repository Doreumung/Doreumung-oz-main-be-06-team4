import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

user = "Mozilla/5.0 (IPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15(KHTML, like Gecko) CriOS/80.0.3987.95 Mobile/15E148 Safari/604.1"

options_ = Options()
options_.add_argument(f"user-agent={user}")
options_.add_experimental_option("detach", True)
options_.add_experimental_option("excludeSwitches", ["enable-logging"])


# 크롬 드라이버 매니저를 자동으로 설치되도록 실행시키는 코드
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options_)

url = "https://map.naver.com/p/search/제주도/"
driver.get(url)
time.sleep(0.5)

# driver.current_url 현재 주소를 확인할 수 있음
if driver.current_url != url:
    driver.get(url)

# a태그를 활용하여 웹페이지의 하이퍼 링크를 식별한다
driver.find_element(By.CSS_SELECTOR, ".input_search").send_keys("자연")
driver.find_element(By.CSS_SELECTOR, ".input_search").send_keys(Keys.ENTER)
time.sleep(0.5)
driver.find_elements(By.CSS_SELECTOR, "#moreBtn")[1].click()
time.sleep(0.5)

html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

items = soup.select("#_chartList .list_item")

for i in items:
    rank = i.select_one(".ranking_num")
    title = i.select_one(".title.ellipsis")
    singer = i.select_one(".name.ellipsis")

    print(f"순위 : {rank.text}")
    print(f"제목 : {title.text.strip()}")
    print(f"가수 : {singer.text}")
    print()

driver.quit()
