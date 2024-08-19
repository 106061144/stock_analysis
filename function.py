import warnings
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from twstock import Stock
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import date2num
from statistics import mean
import time
from datetime import date
from datetime import datetime
from selenium import webdriver
from tqdm import tqdm
import os
import yfinance as yf


def Update_potential_stock(from_offline, from_online, category=['all']):
    corp_list = []
    Today = date.today()
    Today = Today.strftime("%Y/%m")
    if from_offline:
        f = open('high_level_control.txt', 'r')
        update_flag = False
        if os.path.exists('ETF_list_record.csv'):
            ETF_df = pd.read_csv('ETF_list_record.csv')
            Update_date = datetime.strptime(ETF_df['Update date'][0], '%Y/%m')
            Update_date = Update_date.strftime("%Y/%m")
            if (Update_date != Today):
                ETF_df = pd.DataFrame([Today], columns=['Update date'])
                update_flag = True
        else:
            ETF_df = pd.DataFrame([Today], columns=['Update date'])
            update_flag = True

        etf_list = []
        for line in f.readlines():
            if 'ETF' in line:   # ETF Constituent
                for word in line.split()[1:]:
                    if ',' in word:
                        word = word[:-1]
                    etf_list.append(word)
                    if (not update_flag) and (word not in ETF_df.columns):
                        ETF_df = pd.DataFrame(
                            [Today], columns=['Update date'])
                        update_flag = True
                if update_flag:

                    etf_df = ETF_list(etf_list)
                    ETF_df = pd.concat([ETF_df, etf_df], axis=1)
                    ETF_df.to_csv('ETF_list_record.csv', index=False)
                for etf in etf_list:
                    for i in ETF_df[etf]:
                        try:
                            if str(int(i)) not in corp_list:
                                corp_list.append(str(int(i)))
                        except:
                            continue
            elif 'stock' in line:
                for word in line.split()[1:]:
                    if ',' in word:
                        word = word[:-1]
                    if word not in corp_list:
                        corp_list.append(word)
    if from_online:
        update_dict = {"Update date": [Today]}
        update_flag = False
        if os.path.exists('Online_list_record.csv'):
            df = pd.read_csv('Online_list_record.csv')
            Update_date = datetime.strptime(df['Update date'][0], '%Y/%m')
            Update_date = Update_date.strftime("%Y/%m")
            if (Update_date != Today):
                update_flag = True
        else:
            update_flag = True

        if update_flag:
            print('Stock category is out-of-date, need to update!')
            all_cat_df = Parse_all_category_stocks()
            links = all_cat_df['link'].values
            cats = all_cat_df['Category'].values
            for idx, link in enumerate(links):
                stocks = Parse_certain_category_stocks(link)
                update_dict[str(cats[idx])] = stocks
            df = pd.DataFrame(dict([(key, pd.Series(value))
                              for key, value in update_dict.items()]))
            df.to_csv('Online_list_record.csv', index=False)
        if 'all' not in category:
            for item in category:
                if item in list(df.keys()):
                    corp_list.extend(list(df[item].values))
        else:
            for item in list(df.keys())[1:]:
                corp_list.extend(list(df[item].values))

    corp_list = list(set(corp_list))
    return corp_list


def Parse_all_category_stocks():
    root_url = 'https://goodinfo.tw/tw/StockList.asp'
    option = webdriver.ChromeOptions()
    option.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=option)
    driver.get(root_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    look_up_table = soup.find_all(
        "table", {"id": "MENU1"})
    all_urls = []
    if look_up_table != []:
        target_table = look_up_table[0]
        all_lines = target_table.findAll('tr')
        for line in all_lines[2:10]:
            urls = line.findAll('a')
            for url in urls:
                name = url.text
                link = url.get('href')
                all_urls.append([name, 'https://goodinfo.tw'+link])
    Category, link = zip(*all_urls)
    df = pd.DataFrame(data={'Category': Category, 'link': link})
    driver.quit()

    return df


def Parse_certain_category_stocks(link):
    option = webdriver.ChromeOptions()
    option.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=option)
    driver.get(link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    look_up_table = soup.find_all(
        "table", {"id": "tblStockList"})
    id_list = []
    if look_up_table != []:
        target_table = look_up_table[0]
        raw_list = target_table.findAll('tr')
        for line in raw_list:
            elements = line.findAll('a')
            id = elements[0].text
            try:
                id_num = int(id)
                id_list.append(f'\'{id}')
            except:
                pass
    driver.quit()
    return id_list


def to_sell(stock_id, start_date, buy_day, buy_point):
    try:
        data = yf.Ticker(stock_id+'.TW')
        df = data.history(start=start_date)
        close_list = df['Close'].tolist()
        volumn = df['Volume'].tolist()
        time_tap = df.index
    except:
        tqdm.write(f'Stock {stock_id} doesn\'t exist')
        return [0, 0, 0]

    if len(close_list) < 10:
        try:
            stock = Stock(stock_id)
            date_split = start_date.split('-')
            data = stock.fetch_from(int(date_split[0]), int(date_split[1]))
            df = pd.DataFrame(data)
            close_list = df['close'].tolist()
            volumn = df['capacity'].tolist()
            time_tap = df['date'].tolist()
            tqdm.write(f'no problem')
        except:
            tqdm.write(f'Stock {stock_id} parse fail')
            return [0, 0, 0]
    for tt_idx, tt in enumerate(time_tap):
        tt = tt.strftime("%Y-%m-%d")
        if tt == buy_day:
            start_idx = tt_idx
            break

    [obv_line, MA_obv_line] = OBV_calculation(close_list, volumn)
    [center_line_1, up_line_1, down_line_1] = Bollin_Band_cal(
        close_list, 50, 1.2)
    end_point = 0
    end_time = 0
    end_flag1 = 0
    end_flag4 = 0
    for idx in range(start_idx, len(close_list)):
        # stop loss point==========================================
        if close_list[idx] < buy_point - 2*(up_line_1[start_idx] - center_line_1[start_idx]):
            end_flag1 = 1
        # 獲利點
        if (obv_line[idx-1] < MA_obv_line[idx-1]) and (obv_line[idx] < MA_obv_line[idx]):
            end_flag4 = 1
        # =========================================================
        if end_flag1 + end_flag4:
            end_point = close_list[idx]
            end_time = time_tap[idx]
            break
    # ========================================================================================================
    return [end_point, end_time]


def to_buy_main(stock_list, DB_start_date='2024-04-01', add_new=False):
    start_date = DB_start_date
    candidates = []
    if not add_new:
        print('Don\'t analyze new stock')
    if os.path.exists('parse_record.csv'):
        print('----------------')
        parse_df = pd.read_csv('parse_record.csv')
        yf_list = list(parse_df['yfinance'].values)
        tw_list = list(parse_df['twstock'].values)
    else:
        _dict = dict.fromkeys(['yfinance', 'twstock'])
        _dict['yfinance'] = []
        _dict['twstock'] = []
        parse_df = pd.DataFrame(_dict)
        yf_list = []
        tw_list = []
    new_yf = []
    new_tw = []
    for stock_id in tqdm(stock_list):

        if not pd.isna(stock_id):
            if stock_id[0] == '\'':
                stock_id = stock_id[1:]
            buy_info = [0, 0, 0, 0]
            try:
                buy_info = to_buy(stock_id, start_date,
                                  yf_list, tw_list, add_new)
            except:
                pass
            if buy_info[1] == 1:  # new yf
                new_yf.append(stock_id)
            elif buy_info[1] == 2:  # new yf
                new_tw.append(stock_id)
            if buy_info[0]:
                candidates.append(buy_info[2:])
    if new_yf != [] or new_tw != []:
        yf_list.extend(new_yf)
        tw_list.extend(new_tw)
        parse_dict = {'yfinance': yf_list, 'twstock': tw_list}
        parse_df = pd.DataFrame(dict([(key, pd.Series(value))
                                      for key, value in parse_dict.items()]))
        parse_df.to_csv('parse_record.csv', index=False)

    if candidates == []:
        print('no appropriate stock')
    else:
        df = pd.DataFrame(candidates)
        rename_dic = {0: "id", 1: "close value"}
        df = df.rename(rename_dic, axis=1)
        df = df.sort_values(by="close value")
        df.insert(0, "Update date", date.today())
        df.to_csv('Buy_Result.csv', index=False)
        print(df)


def to_buy(stock_id, start_date, yf_list, tw_list, add_new):
    found = False
    check = 0
    if yf_list != []:
        if int(stock_id) in yf_list:
            try:
                found = True
                data = yf.Ticker(stock_id+'.TW')
                df = data.history(start=start_date)
                close_list = df['Close'].tolist()
                volumn = df['Volume'].tolist()
            except:
                pass
    if tw_list != []:
        if int(stock_id) in tw_list:
            try:
                found = True
                stock = Stock(stock_id)
                date_split = start_date.split('-')
                data = stock.fetch_from(int(date_split[0]), int(date_split[1]))
                df = pd.DataFrame(data)
                close_list = df['close'].tolist()
                volumn = df['capacity'].tolist()
            except:
                pass
    if not found:  # new stock or stock doesn't exist
        if add_new:
            try:
                data = yf.Ticker(stock_id+'.TW')
                df = data.history(start=start_date)
                close_list = df['Close'].tolist()
                volumn = df['Volume'].tolist()
                check = 1
            except:
                close_list = []
                tqdm.write(f'Stock {stock_id} doesn\'t exist')
                # return [0, 0, 0, 0]
            if len(close_list) < 10:
                try:
                    stock = Stock(stock_id)
                    date_split = start_date.split('-')
                    data = stock.fetch_from(
                        int(date_split[0]), int(date_split[1]))
                    df = pd.DataFrame(data)
                    close_list = df['close'].tolist()
                    volumn = df['capacity'].tolist()
                    tqdm.write(f'data found')
                    check = 2
                except:
                    tqdm.write(f'Stock {stock_id} parse fail')
                    return [0, 0, 0, 0]
        else:
            return [0, 0, 0, 0]
    # if len(close_list) == 0:
    #    return [0, 0, 0, 0]
    Ema60_line = EMA_cal(60, close_list)
    Ema5_line = EMA_cal(5, close_list)
    [macd, diff, Hist] = MACD_calculation(close_list)
    [obv_line, MA_obv_line] = OBV_calculation(close_list, volumn)
    macd_std = np.std(macd)

    start_point_list = []
    start_time_list = []
    ready_start_flag_1 = 0
    start_flag1 = 0
    start_flag2 = 0
    start_flag3 = 0
    start_point_list = []
    start_time_list = []
    for idx in range(len(macd)-2, len(macd)):
        # buy condition
        macd_std = np.std(macd[:idx])

        # macd: 慢線, diff: 快線
        if (macd[idx] - macd[idx-1] > macd[idx-1] - macd[idx-2]) and ((macd[idx-1] - macd[idx-2]) >= (macd[idx-2] - macd[idx-3])) and (diff[idx-1] < diff[idx]) and (Hist[idx-2] < Hist[idx-1]) and (Hist[idx-1] < Hist[idx]) and (Hist[idx-1] <= 0) and (abs(macd[idx-1]) < macd_std) and (abs(macd[idx]) < macd_std):
            start_flag1 = 1
        else:
            start_flag1 = 0

        if Ema5_line[idx] >= Ema60_line[idx]:
            start_flag2 = 1
        else:
            start_flag2 = 0

        if (obv_line[idx] > MA_obv_line[idx]):
            start_flag3 = 1
        else:
            start_flag3 = 0

        if mean(volumn[idx-7:idx]) > 300*1000 and volumn[idx] > 200*1000:
            start_flag4 = 1
        else:
            start_flag4 = 0

        if (start_flag1 + start_flag2 + start_flag3 + start_flag4 == 4):
            start_point_list.append(close_list[idx])
            start_flag1 = 0
            start_flag2 = 0
            start_flag3 = 0
            start_flag4 = 0

    return ((len(start_point_list) > 0), check, stock_id, close_list[-1])


def figure_plot(stock_id, year, month):

    stock = Stock(stock_id)
    data = stock.fetch_from(year, month)
    df = pd.DataFrame(data)

    time_tap = df['date'].tolist()
    volumn = df['capacity'].tolist()
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD_calculation(close_list)
    [obv_line, MA_obv_line] = OBV_calculation(close_list, volumn)
    [center_line_1, up_line_1, down_line_1] = Bollin_Band_cal(
        close_list, 50, 1.2)
    # ema7 = EMA_cal(7,close_list)
    # bottom_line = EMA_cal(25, close_list)

    fig, axs = plt.subplots(3)
    axs[0].plot(time_tap, close_list, label='close')
    axs[0].plot(time_tap, up_line_1, label='BL up', linestyle='dashed')
    axs[0].plot(time_tap, down_line_1, label='BL down', linestyle='dashed')
    axs[1].bar(time_tap, Hist)
    axs[1].plot(time_tap, macd, label='macd')
    axs[1].plot(time_tap, diff, label='diff')
    axs[1].legend()
    axs[2].plot(time_tap, obv_line, label='obv')
    axs[2].plot(time_tap, MA_obv_line, label='ma_obv')
    axs[2].legend()
    plt.show()

    return


def OBV_calculation(close_list, volumn):
    MA_days = 25
    obv_line = []
    MA_obv_line = []
    for idx in range(len(close_list)):
        if idx == 0:
            MA_obv_line.append(volumn[0])
            obv_line.append(volumn[0])
        else:
            if (close_list[idx] > close_list[idx-1]):
                obv_line.append(obv_line[idx-1] + volumn[idx])
            elif (close_list[idx] < close_list[idx-1]):
                obv_line.append(obv_line[idx-1] - volumn[idx])
            else:
                obv_line.append(obv_line[idx-1])
            if idx < MA_days:
                MA_obv_line.append(mean(obv_line))
            else:
                MA_obv_line.append(mean(obv_line[idx-MA_days:idx]))

    return [obv_line, MA_obv_line]


def ETF_list(ETF_id_list):
    id_list = []
    option = webdriver.ChromeOptions()
    option.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=option)
    driver.get(
        'https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=0050')
    time.sleep(2)
    Corp_dict = {el: 0 for el in ETF_id_list}
    for ETF_id in ETF_id_list:
        driver.get(
            'https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID='+ETF_id)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        look_up_table = soup.find_all(
            "table", {"class": "p4_2 row_bg_2n row_mouse_over"})
        if look_up_table != []:
            target_table = look_up_table[1]
            raw_list = target_table.findAll('nobr')
            corp_list = []
            for idx in range(len(raw_list)):
                if (idx % 3 == 0) and (raw_list[idx] not in id_list):
                    corp_list.append(raw_list[idx].text)
            Corp_dict[ETF_id] = corp_list
        else:
            print(f'cannot find ETF number {ETF_id}')
    Corp_df = pd.DataFrame(dict([(k, pd.Series(v))
                                 for k, v in Corp_dict.items()]))
    return Corp_df


def Create_stock_index_table():
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "lxml")
    tr = soup.findAll('tr')

    tds = []
    for raw in tr:
        data = [td.get_text() for td in raw.findAll("td")]
        if len(data) == 7:
            data1 = data[0].split("\u3000")
            tds.append(data1)

    df = pd.DataFrame(tds[1:], columns=['stock_code', 'stock_name'])
    df.to_csv('stock_index.csv', index=False)


def MA_cal(N, record):  # return a list length=record.length
    ma_record = []
    ma_record_sum = []
    for idx, element in enumerate(record):
        if ma_record == []:
            ma_record_sum.append(element)
            ma_record.append(element)
        else:
            if idx < N:
                tmp = ma_record_sum[-1] + element
                ma_record_sum.append(tmp)
                ma_record.append(tmp/(idx+1))
            else:
                tmp = ma_record_sum[-1] - record[idx-N] + element
                ma_record_sum.append(tmp)
                ma_record.append(tmp/N)
    return ma_record


def EMA_cal(N, record):  # return a list length=record.length
    ema_record = []
    for element in record:
        if ema_record == []:
            ema_record.append(element)
        else:
            ema_record.append(
                (2 * element + (N - 1) * ema_record[-1]) / (N + 1))
    return ema_record


def MACD_calculation(record):
    Ema26 = EMA_cal(26, record)
    Ema12 = EMA_cal(12, record)
    Diff = []
    for i in range(len(record)):
        Diff.append(Ema12[i]-Ema26[i])
    MACD_record = EMA_cal(9, Diff)
    Hist = []
    for i in range(len(record)):
        Hist.append(Diff[i]-MACD_record[i])
    return [MACD_record, Diff, Hist]


def Bollin_Band_cal(record, ma_N, std_num):
    Ma20_line = MA_cal(ma_N, record)
    Up_line = []
    Down_line = []
    for idx, element in enumerate(record):
        if idx < ma_N:
            STD = np.std(record[:idx])
        else:
            STD = np.std(record[(idx-ma_N):idx])
        Up_line.append(Ma20_line[idx] + std_num * STD)  # 1.5 std
        Down_line.append(Ma20_line[idx] - std_num * STD)  # 1.5 std

    return [Ma20_line, Up_line, Down_line]


def qualify_stock(stock_id, year, month):
    try:
        stock = Stock(stock_id)
        data = stock.fetch_from(year-1, month)
        df = pd.DataFrame(data)
        close_list = df['close'].tolist()
        [macd, diff, Hist] = MACD_calculation(close_list[:200])
        macd_std = np.std(macd)
        if macd_std > 1:
            return True
        else:
            return False
    except:
        print(f'stock {stock_id} may not exist')
        return False
