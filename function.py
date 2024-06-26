import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from twstock import Stock
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import date2num
from statistics import mean
import time
from datetime import date
from datetime import datetime
from selenium import webdriver
from tqdm import tqdm


def qualify_stock(stock_id, year, month):
    try:
        stock = Stock(stock_id)
        print('0')
        data = stock.fetch_from(year-1, month)
        print('1')
        df = pd.DataFrame(data)
        close_list = df['close'].tolist()
        [macd, diff, Hist] = MACD(close_list[:200])
        print('2')
        macd_std = np.std(macd)
        if macd_std > 0:
            return True
        else:
            return False
    except:
        print(f'stock {stock_id} may not exist')
        return False


def past_synthesis(stock_id, year, month, print_log=False, plotting=False):
    stock = Stock(stock_id)
    data = stock.fetch_from(year, month)
    df = pd.DataFrame(data)
    close_list = df['close'].tolist()
    time_tap = df['date'].tolist()
    volumn = df['capacity'].tolist()

    # vol_intervals = volumn_profile(df, 30, time_tap[0], time_tap[-1])

    [macd, diff, Hist] = MACD(close_list)

    Ema100_line = EMA_cal(100, close_list)
    Ema5_line = EMA_cal(5, close_list)

    [center_line_1, up_line_1, down_line_1] = Bollin_Band_cal(
        close_list, 50, 1.2)

    Bollin_mask = [center_line_1, up_line_1, down_line_1]

    [obv_line, MA_obv_line] = OBV_calculation(close_list, volumn)

    start_point_list = []
    start_time_list = []
    start_idx_list = []
    end_point = 0
    end_time = 0
    ready_start_flag_1 = 0
    start_flag1 = 0
    start_flag2 = 0
    start_flag3 = 0
    start_flag4 = 0
    end_flag1 = 0
    end_flag2 = 0
    end_flag3 = 0
    end_flag4 = 0
    consol_flag = False
    consol_max_cnt = 15
    consol_cnt = 0
    pending_flag = 0

    reward_record = []
    time_stamp = []
    consol_decision = np.zeros(len(macd))
    macd_std = np.std(macd)
    for idx in range(30, len(macd)):
        # Consolidation decision
        # ========================================================================================================
        # buy condition
        macd_std = np.std(macd[:idx])
        thr_1 = macd_std/2
        # print(thr_1)
        if ready_start_flag_1 == 0 and (Hist[idx-2] < Hist[idx-1]) and (Hist[idx-1] < Hist[idx]) and (abs(macd[idx-1]) < thr_1) and (abs(macd[idx]) < thr_1):   # case 1
            if (start_time_list == []):
                ready_start_flag_1 = 1
            elif (time_tap[idx]-start_time_list[-1]).days > 14:
                ready_start_flag_1 = 1
            if print_log:
                print('case 1', end=' ')
                print(time_tap[idx])

        if (ready_start_flag_1 and ready_start_flag_1 <= 3) or pending_flag:   # 3 transaction days pending
            if (macd[idx-2] < macd[idx-1]) and (macd[idx-1] < macd[idx]) and (diff[idx-1] < diff[idx]) and (diff[idx-2] < diff[idx-1]) and (Hist[idx-2] < Hist[idx-1]) and (Hist[idx-1] < Hist[idx]):
                start_flag1 = 1
            else:
                start_flag1 = 0

            if Ema5_line[idx] >= Ema100_line[idx]:
                start_flag2 = 1
            else:
                start_flag2 = 0

            if (obv_line[idx] > MA_obv_line[idx]):
                start_flag3 = 1
            else:
                start_flag3 = 0

            if start_flag1 and start_flag2 and start_flag3:
                start_point_list.append(close_list[idx])
                start_time_list.append(time_tap[idx])
                start_idx_list.append(idx)
                ready_start_flag_1 = 0
                start_flag1 = 0
                start_flag2 = 0
                start_flag3 = 0
                pending_flag = 0
            elif (diff[idx-1] < macd[idx-1]) and (diff[idx] < macd[idx]) and (Hist[idx-1] < Hist[idx]) and (abs(macd[idx-1]) < thr_1) and (abs(macd[idx]) < thr_1):
                ready_start_flag_1 = 1
            else:
                ready_start_flag_1 = ready_start_flag_1 + 1

            if pending_flag:
                if (macd[idx] < 0) and (diff[idx] < 0):
                    pending_flag = 0
        else:
            ready_start_flag_1 = 0                        # transaction days expired

        # ========================================================================================================
        # sell condition
        if (len(start_point_list) > 0):
            # stop loss point==========================================
            for idx_s, start_point in enumerate(start_point_list):
                if close_list[idx] < start_point - 2*(up_line_1[start_idx_list[idx_s]] - center_line_1[start_idx_list[idx_s]]):
                    end_flag1 = 1
                    break
            # consolidation============================================
            if consol_flag == True:
                # end_flag1 = 1
                end_flag2 = 1
                end_flag3 = 1
            # preferred sell condition=================================
            # if close_list[idx] < up_line_1[idx] and (diff[idx] > 0):
            #     end_flag1 = 1
            if (obv_line[idx-1] < MA_obv_line[idx-1]) and (obv_line[idx] < MA_obv_line[idx]):
                end_flag4 = 1

            # =========================================================
            if end_flag1 + end_flag4:
                end_point = close_list[idx]
                end_time = time_tap[idx]
                for idx_s in range(len(start_point_list)):
                    reward_record.append(end_point-start_point_list[idx_s])
                    time_stamp.append(
                        (start_time_list[idx_s], end_time, start_point_list[idx_s], end_point))
                start_point_list = []
                start_time_list = []
                end_point = 0
                end_flag1 = 0
                end_flag4 = 0

                if (macd[idx] > 0) and (diff[idx] > 0):
                    pending_flag = 1
                else:
                    pending_flag = 0
        # ========================================================================================================

    for idx_s in range(len(start_point_list)):
        reward_record.append(close_list[idx-1]-start_point_list[idx_s])
        time_stamp.append(
            (start_time_list[idx_s], time_tap[idx-1], start_point_list[idx_s], close_list[idx-1]))
    consol_date = []
    tmp = []
    pre_ele = 0
    for idx, element in enumerate(consol_decision):
        if pre_ele == 0 and element == 1:
            tmp.append(time_tap[idx])
        elif pre_ele == 1 and element == 0:
            tmp.append(time_tap[idx])
            consol_date.append(tmp)
            tmp = []
        pre_ele = element

    if plotting:
        fig, axs = plt.subplots(3)
        axs[0].plot(time_tap, close_list, label='close')
        axs[0].plot(time_tap, Bollin_mask[1],
                    label='BL up', linestyle='dashed')
        axs[0].plot(time_tap, Bollin_mask[2],
                    label='BL down', linestyle='dashed')
        for data in time_stamp:
            axs[0].plot(data[0], data[2], marker='o', markersize=3, color='r')
            axs[0].plot(data[1], data[3], marker='o', markersize=3, color='g')
        for date_set in consol_date:
            axs[0].axvspan(date_set[0], date_set[1],
                           facecolor='pink', alpha=0.2)
            axs[1].axvspan(date_set[0], date_set[1],
                           facecolor='pink', alpha=0.2)
        # axs[0].legend()
        axs[1].bar(time_tap, Hist)
        axs[1].plot(time_tap, macd, label='macd')
        axs[1].plot(time_tap, diff, label='diff')
        axs[1].legend()
        axs[2].plot(time_tap, obv_line, label='obv')
        axs[2].plot(time_tap, MA_obv_line, label='ma_obv')
        axs[2].legend()
        plt.show()

    return [reward_record, time_stamp, Bollin_mask, consol_date]


def volumn_profile(df, percentage, start_date, end_date):

    df = df[df['date'] >= start_date]
    df_target = df[df['date'] <= end_date]
    TTick = df_target['date'].tolist()
    capacity = df_target['capacity'].tolist()
    high_point = df_target['high'].tolist()
    highest_point = max(df_target['high'])
    low_point = df_target['low'].tolist()
    lowest_point = min(df_target['low'])
    vol_intervals = []
    dis = highest_point-lowest_point
    total_num = int(dis*100)
    count_record = np.zeros(total_num)

    for idx in range(len(TTick)):
        per_num = capacity[idx]/(high_point[idx]-low_point[idx])
        start_count = int((low_point[idx]-lowest_point)*100)
        end_count = int((high_point[idx]-lowest_point)*100)
        for idx_1 in range(start_count, end_count):
            count_record[idx_1] = count_record[idx_1] + per_num

    keep = True
    level = 0
    target_volumn = int(sum(count_record)*percentage/100)
    max_count = max(count_record)
    step = int(max_count/100)

    while (sum(count_record) > target_volumn):
        count_record = [((count-step) > 0)*(count-step)
                        for count in count_record]
        level = level+1

    count_record = [count > 0 for count in count_record]

    plt.plot(count_record)
    plt.show()
    return count_record


def figure_plot(stock_id, year, month):
    [reward, time_stamp, Bollin_mask, consol_date] = past_synthesis(
        stock_id, year, month, print_log=False)
    print(reward)
    print(time_stamp)
    stock = Stock(stock_id)
    data = stock.fetch_from(year, month)
    df = pd.DataFrame(data)

    time_tap = df['date'].tolist()
    volumn = df['capacity'].tolist()
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD(close_list)
    [obv_line, MA_obv_line] = OBV_calculation(close_list, volumn)

    # ema7 = EMA_cal(7,close_list)
    # bottom_line = EMA_cal(25, close_list)

    fig, axs = plt.subplots(3)
    axs[0].plot(time_tap, close_list, label='close')
    axs[0].plot(time_tap, Bollin_mask[1], label='BL up', linestyle='dashed')
    axs[0].plot(time_tap, Bollin_mask[2], label='BL down', linestyle='dashed')
    for data in time_stamp:
        axs[0].plot(data[0], data[2], marker='o', markersize=3, color='r')
        axs[0].plot(data[1], data[3], marker='o', markersize=3, color='g')
    for date_set in consol_date:
        axs[0].axvspan(date_set[0], date_set[1], facecolor='pink', alpha=0.2)
        axs[1].axvspan(date_set[0], date_set[1], facecolor='pink', alpha=0.2)
    # axs[0].legend()
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

        target_table = look_up_table[1]
        raw_list = target_table.findAll('nobr')
        corp_list = []
        for idx in range(len(raw_list)):
            if (idx % 3 == 0) and (raw_list[idx] not in id_list):
                corp_list.append(raw_list[idx].text)
        Corp_dict[ETF_id] = corp_list
        Corp_df = pd.DataFrame(dict([(k, pd.Series(v))
                               for k, v in Corp_dict.items()]))
    return Corp_df


def Update_potential_stock():
    f = open('high_level_control.txt', 'r')
    update_flag = False
    Today = date.today()
    Today = Today.strftime("%Y/%m/%d")
    try:
        ETF_df = pd.read_csv('ETF_list_record.csv')
        Update_date = datetime.strptime(ETF_df['Update date'][0], '%Y/%m/%d')
        Update_date = Update_date.strftime("%Y/%m/%d")
        if (Update_date != Today):
            ETF_df = pd.DataFrame([Today], columns=['Update date'])
            update_flag = True
    except:
        ETF_df = pd.DataFrame([Today], columns=['Update date'])
        update_flag = True

    etf_list = []
    corp_list = []
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
