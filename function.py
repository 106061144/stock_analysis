import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from twstock import Stock
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import date2num


def past_synthesis(stock_id, year, month, print_log=False):
    stock = Stock(stock_id)
    data = stock.fetch_from(year, month)
    df = pd.DataFrame(data)
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD(close_list)
    macd_std = np.std(macd)
    thr_1 = macd_std  # case 1
    print('thr_1 = ', end=' ')
    print(thr_1)
    thr_2 = macd_std*1.5    # case 2
    Ema25_line = EMA_cal(25, close_list)

    [center_line_1, up_line_1, down_line_1] = Bollin_Band_cal(
        close_list, 50, 1.2)
    [center_line_2, up_line_2, down_line_2] = Bollin_Band_cal(
        close_list, 20, 1.5)

    start_point_list = []
    start_time_list = []
    end_point = 0
    end_time = 0
    ready_start_flag_1 = 0
    ready_start_flag_2 = 0
    end_flag1 = 0
    end_flag2 = 0
    end_flag3 = 0
    consol_flag = False
    consol_max_cnt = 15
    consol_cnt = 0
    Bollin_mask = [center_line_1, up_line_1, down_line_1]
    reward_record = []
    time_stamp = []
    consol_decision = np.zeros(len(macd))
    for idx in range(30, len(macd)):
        # Consolidation decision
        # Design core: it is hard to enter Bollinger band, but also hard to escape Bollin band
        if consol_flag:
            Bollin_mask[0][idx] = Bollin_mask[0][idx-1]
            Bollin_mask[1][idx] = Bollin_mask[1][idx-1]
            Bollin_mask[2][idx] = Bollin_mask[2][idx-1]
            # breakout condition
            if close_list[idx] > Bollin_mask[1][idx] or close_list[idx] < Bollin_mask[2][idx]:
                consol_flag = False
                consol_cnt = consol_cnt - 1
                if print_log:
                    print('consol turn off')

        else:
            if close_list[idx] <= up_line_1[idx] and close_list[idx] >= down_line_1[idx]:
                consol_cnt = consol_cnt + 1
                if consol_cnt == consol_max_cnt:
                    half_BW = up_line_2[idx] - center_line_2[idx]
                    Bollin_mask[0][idx] = center_line_2[idx]
                    Bollin_mask[1][idx] = Bollin_mask[0][idx] + half_BW
                    Bollin_mask[2][idx] = Bollin_mask[0][idx] - half_BW
                    if close_list[idx] <= Bollin_mask[1][idx] and close_list[idx] >= Bollin_mask[2][idx]:
                        consol_flag = True
                    else:
                        consol_cnt = consol_cnt - 3
                    if print_log:
                        print('consol turn on')
            else:
                consol_cnt = consol_cnt - 3
                if consol_cnt < 0:
                    consol_cnt = 0
        if consol_flag:
            consol_decision[idx] = 1
        # ========================================================================================================
        # buy condition
        if ready_start_flag_1 == 0 and (diff[idx-1] < macd[idx-1]) and (diff[idx] < macd[idx]) and (Hist[idx-1] < Hist[idx]) and (abs(macd[idx-1]) < thr_1) and (abs(macd[idx]) < thr_1):   # case 1
            ready_start_flag_1 = 1
            if print_log:
                print('case 1', end=' ')
                print(df['date'][idx])
        elif (diff[idx-1] < macd[idx-1]) and (diff[idx] >= macd[idx]) and (diff[idx] < 0) and (abs(macd[idx-1]) < thr_2) and (abs(macd[idx]) < thr_2):  # case 2
            ready_start_flag_2 = 0  # unable ready_start_flag_2
            if print_log:
                print('case 2', end=' ')
                print(df['date'][idx])

        if ready_start_flag_1 and ready_start_flag_1 <= 3:   # 8 transaction days pending
            if (macd[idx-1] < macd[idx]) and (diff[idx-1] < diff[idx]) and (diff[idx-2] < diff[idx-1]) and consol_flag == False:
                start_point_list.append(df['close'][idx])
                start_time_list.append(df['date'][idx])
                ready_start_flag_1 = 0
            elif (diff[idx-1] < macd[idx-1]) and (diff[idx] < macd[idx]) and (Hist[idx-1] < Hist[idx]) and (abs(macd[idx-1]) < thr_1) and (abs(macd[idx]) < thr_1):
                ready_start_flag_1 = 1
            else:
                ready_start_flag_1 = ready_start_flag_1 + 1
        else:
            ready_start_flag_1 = 0                        # transaction days expired

        if ready_start_flag_2 and ready_start_flag_2 <= 10:  # 2 weeks transaction days pending
            if (macd[idx-1] < macd[idx]) and (diff[idx-1] < diff[idx]) and (diff[idx-2] < diff[idx-1]) and consol_flag == False:
                if diff[idx] > 0 and close_list[idx] > Ema25_line[idx]:
                    start_point_list.append(df['close'][idx])
                    start_time_list.append(df['date'][idx])
                    ready_start_flag_2 = 0
            else:
                ready_start_flag_2 = ready_start_flag_2 + 1
        else:
            ready_start_flag_2 = 0
        # ========================================================================================================
        # sell condition
        if (len(start_point_list) > 0):
            # stop loss point

            if close_list[idx] < Ema25_line[idx] and (diff[idx] > 0):
                end_flag1 = 1
            if Hist[idx] <= 0:
                end_flag2 = 1
            if close_list[idx] <= Bollin_mask[2][idx]:
                end_flag3 = 1

            if end_flag1 * end_flag2 * end_flag3:
                end_point = df['close'][idx]
                end_time = df['date'][idx]
                for idx_s in range(len(start_point_list)):
                    reward_record.append(end_point-start_point_list[idx_s])
                    time_stamp.append(
                        (start_time_list[idx_s], end_time, start_point_list[idx_s], end_point))
                start_point_list = []
                start_time_list = []
                end_point = 0
                end_flag1 = 0
                end_flag2 = 0
                end_flag3 = 0
        # ========================================================================================================

    for idx_s in range(len(start_point_list)):
        reward_record.append(df['close'][idx-1]-start_point_list[idx_s])
        time_stamp.append(
            (start_time_list[idx_s], df['date'][idx-1], start_point_list[idx_s], end_point))
    consol_date = []
    pre_ele = 0
    for idx, element in enumerate(consol_decision):
        tmp = []
        if pre_ele == 0 and element == 1:
            tmp.append(df['date'][idx])
        elif pre_ele == 1 and element == 0:
            tmp.append(df['date'][idx])
            consol_date.append(tmp)
            tmp = []
        pre_ele = element

    return [reward_record, time_stamp, Bollin_mask, consol_date]


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
    f = open('high_level_control.txt', 'r')
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


def MACD(record):
    Ema26 = EMA_cal(30, record)
    Ema12 = EMA_cal(16, record)
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
