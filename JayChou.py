from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import time
# select date
link = "https://tixcraft.com/activity/game/25_casty"
option = webdriver.ChromeOptions()
option.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=option)
driver.get(link)
outer_loop = True
while (outer_loop):
    if datetime.now().strftime('%Y-%m-%d %H:%M:%S') == '2024-10-23 01:13:00':
        start = time.time()
        time.sleep(0.1)
        driver.get(link)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        date_table = soup.find_all(
            "div", {"id": "gameList"})
        target_table = date_table[0]
        raw_list = target_table.findAll('tr')
        elements = raw_list[1].findAll('td')
        btn = elements[3].find('button')
        seat_link = btn.get('data-href')
        driver.get(seat_link)
        # select seat
        group = driver.find_element(By.ID, "group_0")
        seats = group.find_elements(By.TAG_NAME, "a")
        flag = True
        while flag:
            for seat in seats:
                try:
                    seat.click()
                    flag = False
                except:
                    pass
        # final stage
        ticket_box = driver.find_element(By.ID, "ticketPriceList")
        number = ticket_box.find_elements(By.TAG_NAME, "option")
        number[2].click()
        while True:
            try:
                driver.find_element(By.ID, "TicketForm_agree").click()
                break
            except:
                pass
        end = time.time()
        print(end-start)
        outer_loop = False
# driver.quit()
# seats[0].click()

# print(seats[0])


# id_list = []
# if look_up_table != []:
#     target_table = look_up_table[0]
#     raw_list = target_table.findAll('tr')
#     for line in raw_list:
#         elements = line.findAll('a')
#         id = elements[0].text
#         try:
#             id_num = int(id)
#             id_list.append(f'\'{id}')
#         except:
#             pass
# driver.quit()
