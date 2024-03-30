import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from twstock import Stock
import matplotlib.pyplot as plt

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

    df = pd.DataFrame(tds[1:],columns=['stock_code','stock_name'])
    df.to_csv('stock_index.csv', index=False)


def EMA_cal(N,record):  # return a list length=record.length
    ema_record = []
    for element in record:
        if ema_record==[]:
            ema_record.append(element)
        else:
            ema_record.append((2 * element + (N - 1) * ema_record[-1]) / (N + 1))
    return ema_record
    
def MACD(record):
    Ema26 = EMA_cal(26, record)
    Ema12 = EMA_cal(12, record)
    Diff = []
    for i in range(len(record)):
        Diff.append(Ema12[i]-Ema26[i])
    MACD_record = EMA_cal(9,Diff)
    Hist = []
    for i in range(len(record)):
        Hist.append(Diff[i]-MACD_record[i])
    return [MACD_record, Diff, Hist]