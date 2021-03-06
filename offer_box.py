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
from config import * 

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

def read_config(config_file_name):
    """
    scraping.cfgを読み込む
    """
    with open(config_file_name, 'r') as f:
        lines = f.readlines()
        base_url = lines[0].strip()
        column_order = lines[3].strip().split()
        keyword = lines[6].strip().split()
        area = []
        for l in lines[9:]:
            if not l.strip(): continue
            area.append(l.strip().split())

    return (base_url, column_order, keyword, area)

def make_request_url(base_url, delimter=" or:", **kwargs):
    """
    base_urlにGETパラメータを付け足したrequest_urlを返す 
    """
    req_url = base_url + '?'
    for i, key in enumerate(kwargs):
        if i > 0:
            req_url += '&'
        req_url += (key + '=' + delimter.join(kwargs[key]))
    return req_url

if __name__ == "__main__":
    while True:
        print("掲載日範囲選択 [1, 2, 3]のどれかを選択してください\n"
              "1: within 24 hours\n"
              "2: within 3 days\n"
              "3: within 7 days")
        updated_at = input("> ")
        if updated_at in ['1', '2', '3']: break

    base_url, column_order, keyword, area = read_config(SCRAPING_CONFIG_FILE_NAME)

    now = datetime.datetime.now().strftime("%Y%m%d")
    for prefs in area:

        print("scraping " + prefs[-1] + " ... ", end="", flush=True)
        
        pg = 1
        while True:
            req_url = make_request_url(base_url, 
                                       keyword=keyword,
                                       area=prefs[:-1],
                                       pg=str(pg))
            data = {"form[updatedAt]": updated_at,
                    "form[employType]":'1',
                    "feature":'1'}

            res = requests.post(req_url, data)
            
            time.sleep(1.0)
            if res.status_code != 200: break

            info = get_info(res.text)
            save_file_name = prefs[-1] + now + ".csv"
            write_info(info, os.path.join(DATA_SAVE_DIR, save_file_name), column_order)
            pg += 1
        print("Done", flush=True)
