# -*- coding: utf-8 -*-
import re
import os
import csv
import datetime
import glob
import sys
import time
import pprint
import requests
from bs4 import BeautifulSoup
url_dir = "url_dir"
data_dir = "data_dir"


def read_url(f_name):
    " 求人ボックスのURLを読み込む"
    # with open(f_name, encoding="utf-8") as f:
    with open(f_name, encoding="utf-8") as f:
        base_url = f.read()
        return base_url.strip()

# 既知の会社を管理する
seen = []

def get_info(html):
    """会社名(name), 職種(job), 年収(pay), 勤務地(pay), 掲載元(source), 掲載日時(updated_at)"""

    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("section", attrs={"class": "s-placeSearch_parent"})

    info = [] # 求人情報の辞書を格納する

    for item in items:
        offer_dict = {}

        name       = item.find("p", attrs={"class":"p-result_company"})
        job        = item.find("span", attrs={"class":"p-result_name"})
        area       = item.find("li", attrs={"class":"p-result_area"})
        pay        = item.find("li", attrs={"class":"p-result_pay"})
        source     = item.find("p", attrs={"class":"p-result_source"})
        updated_at = item.find("p", attrs={"class":"p-result_updatedAt_hyphen"})

        # 会社名が非公開の場合はskip
        if name: name = name.text.strip()
        else: continue

        # 既知の会社はskip
        if name in seen: continue
        seen.append(name)

        job        = job.text.strip() if job else "公開していません"
        area       = area.text.strip() if area else "公開していません"
        pay        = pay.text.strip() if pay else "公開していません"
        source     = source.text.strip() if source else "公開していません"
        updated_at = updated_at.text.strip() if updated_at else "公開していません"

        offer_dict["name"]      = name
        offer_dict["job"]       = job
        offer_dict["area"]      = area
        offer_dict["pay"]       = pay
        offer_dict["source"]    = source
        offer_dict["updated_at"] = updated_at

        info.append(offer_dict)

    return info

def write_info(info, full_path, key_order):
    "infoは辞書が要素のリスト"
    "key_orderの何列目に何を書き込むか指定する ['name', 'job',,,]"
    lines = []
    for each_info in info:
        l = [each_info[key] for key in key_order]
        lines.append(l)
    
    with open(full_path, mode="a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(lines) 

def get_updated_at_by_hour(l):
    p = re.compile("(\d+).*")
    m = p.fullmatch(l[1]) # updated_atから数字と時間・日前を抜き出す

    if m is None: return 24*7

    if '日' in l[1]:
        updated_at = int(m.group(1)) * 24 # 日は時間に変換
    else:
        updated_at = int(m.group(1))      # 時間はそのまま

    return updated_at

def sort_by_date(full_path):
    """
    file_nameで指定されたcsvファイルを日付順でソートする
    """
    with open(full_path, mode="r", encoding='utf-8') as f:
        reader = csv.reader(f)
        lines = [row for row in reader] # 2次元配列に変換

    # updated_atで昇順で並び替え
    lines.sort(key=get_updated_at_by_hour)

    with open(full_path, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(lines) 


def main(file_name, url_name, updated_at):
    """
    スクレイピングを行い取得したデータを保存する

    Parameters
    ----------
    file_name : str
        保存するファイル名 (e.g. osaka_kyoto_hyogo_siga.csv)
    url_name: str
        urlが書かれたファイル名(e.g. kansai_url.txt)
    updated_at : str
        求人掲載日の範囲(1: 24時間以内  2: 3日以内  3: 7日以内)
    """

    base_url = read_url(url_name)
    page = 1

    while True:
        url = base_url + "&pg=" + str(page)
        res = requests.post(url, data={"form[updatedAt]": updated_at    # 1=>24時間以内 2=>3日以内 3=>7日以内
                                     , "form[employType]":'1'}) # 1=>正社員
        time.sleep(1.0)                  # 警察のお世話にならないように
        if res.status_code != 200: break # 表示するページがなくなったら抜ける

        info = get_info(res.text)
        write_info(info, full_path=file_name, 
            key_order=["name","job","area","pay","updated_at","source"])

        # print(page)
        page += 1 # ページの更新
    
    sort_by_date(file_name)

def job():
    # 掲載日時範囲の選択
    while True:
        print("掲載日範囲選択 [1, 2, 3]のどれかを選択してください\n"
              "1: within 24 hours\n"
              "2: within 3 days\n"
              "3: within 7 days")
        updated_at = input("> ")
        if updated_at in ['1', '2', '3']: break

    # urlが書かれたファイルの読み込み
    url_list = glob.glob(os.path.join(url_dir, "*_url.txt"))
    url_list = [os.path.basename(d) for d in url_list]

    for u in url_list:
        print("* " + u)

    while True:
        yn = input("上記のurlすべてについてスクレイピングしますか? y or n > ")
        if yn in ["y", "n"]: break
    
    # すべてのURLについてスクレイピングを行う
    if yn == 'y':
        now = datetime.datetime.now().strftime("%Y%m%d")
        for u in url_list:
            url_name = os.path.join(url_dir, u)
            file_name = os.path.join(data_dir, u.split("_")[0]) + now + ".csv"

            print("scraping " + u + " ... ", end="", flush=True)
            main(file_name, url_name, updated_at)
            print("Done", flush=True)

def read_config(config_file_name):
    """
    以下のフォーマットのconfigファイルを読み込む
    url
    ---
    keyword
    key1 key2 
    ---
    area
    pref1 pref2 csv_file_name1
    pref3 pref4 csv_file_name2
    """
    with open(config_file, 'r') as f:
        lines = f.readlines()
        base_url = lines[0].strip()
        keyword = lines[3].strip().split()
        area = []
        for l in lines[6:]:
            if not l.strip(): continue
            area.append(l.strip().split())

    return (base_url, keyword, area)
if __name__ == "__main__":
    job()
