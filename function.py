import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from twstock import Stock
import matplotlib.pyplot as plt


def past_synthesis(stock_id):
    stock = Stock(stock_id)
    data = stock.fetch_from(2022, 1)
    df = pd.DataFrame(data)
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD(close_list)
    bottom_line = EMA_cal(30, close_list)
    start_point = 0
    start_time = 0
    end_point = 0
    end_time = 0
    ready_start_flag = 0
    ready_end_flag = 0
    reward_record = []
    time_stamp = []
    for idx in range(1, len(macd)):
        if (diff[idx-1] < macd[idx-1]) and (diff[idx] < macd[idx]) and (macd[idx-1] < 3) and (macd[idx] < 3):
            if (Hist[idx-1] < macd[idx-1]) and (Hist[idx] >= macd[idx]):
                ready_start_flag = 1
        if ready_start_flag and ready_start_flag < 4:
            if diff[idx-1] <= diff[idx]:
                start_point = df['close'][idx]
                start_time = df['date'][idx]
                ready_start_flag = 0
            else:
                ready_start_flag = ready_start_flag + 1
        else:
            ready_start_flag = 0

        if (start_point > 0) and (diff[idx-1] > macd[idx-1]) and (diff[idx] > macd[idx]) and (macd[idx-1] > 0) and (macd[idx] > 0):
            if (Hist[idx-1] > macd[idx-1]) and (Hist[idx] <= macd[idx]):
                ready_end_flag = 1
        if ready_end_flag:
            if close_list[idx] < bottom_line[idx]:
                end_point = df['close'][idx]
                end_time = df['date'][idx]
                reward_record.append(end_point-start_point)
                time_stamp.append((start_time, end_time))
                start_point = 0
                end_point = 0
                ready_end_flag = 0
            else:
                ready_end_flag = ready_end_flag + 1
        else:
            ready_end_flag = 0

    if start_point > 0:
        reward_record.append(df['close'][idx-1]-start_point)
        time_stamp.append((start_time, df['date'][idx-1]))
    return [reward_record, time_stamp]


def ETF_list(ETF_id_list):
    id_list = []
    for ETF_id in ETF_id_list:
        url = 'https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID='+ETF_id
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        look_up_table = soup.find_all(
            "table", {"class": "p4_2 row_bg_2n row_mouse_over"})
        target_table = look_up_table[1]
        raw_list = target_table.findAll('nobr')
        for idx in range(len(raw_list)):
            if (idx % 3 == 0) and (raw_list[idx] not in id_list):
                id_list.append(raw_list[idx].text)
    return id_list


def Update_potential_stock():
    f = open('./high_level_control.txt', 'r')
    etf_list = []
    corp_list = []
    for line in f.readlines():
        if 'ETF' in line:   # ETF Constituent
            for word in line.split()[1:]:
                if ',' in word:
                    word = word[:-1]
                etf_list.append(word)
            corp_list.extend(ETF_list(etf_list))
        elif 'stock' in line:
            for word in line.split()[1:]:
                if ',' in word:
                    word = word[:-1]
                if word not in corp_list:
                    corp_list.append(word)
    return corp_list


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


def EMA_cal(N, record):  # return a list length=record.length
    ema_record = []
    for element in record:
        if ema_record == []:
            ema_record.append(element)
        else:
            ema_record.append(
                (2 * element + (N - 1) * ema_record[-1]) / (N + 1))
    return ema_record


def MACD(record):
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
