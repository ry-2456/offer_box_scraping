# -*- coding: utf-8 -*-
import re
import csv
import sys
import time
import pprint
import requests
# from urllib import request
from bs4 import BeautifulSoup


def read_url(f_name):
    " 求人ボックスのURLを読み込む"
    with open(f_name) as f:
        base_url = f.read()
        return base_url.strip()

def get_info(html):
    "会社名(name), 職種(job), 年収(pay), 勤務地(pay), 掲載元(source), 掲載日時(updated_at)"
    #soup = BeautifulSoup(html).main
    soup = BeautifulSoup(html, "html.parser")

    items = soup.find_all("section", attrs={"class": "s-placeSearch_parent"})
    info = [] # 求人情報の辞書を格納する

    for item in items:
        offer_dict = {}
        name_job = item.find("span", attrs={"class":"p-result_name"}).string.strip()
        if "｜" in name_job:
            job, name = name_job.split("｜")
        else:
            continue
        area       = item.find("li", attrs={"class":"p-result_area"})
        pay        = item.find("li", attrs={"class":"p-result_pay"})
        source     = item.find("p", attrs={"class":"p-result_source"})
        updated_at = item.find("p", attrs={"class":"p-result_updatedAt_hyphen"})

        if area is not None: 
            if area.string is not None:
                area = area.string.strip()

        if pay is not None: 
            if pay.string is not None:
                pay = pay.string.strip()

        if source is not None: 
            if source.string is not None:
                source = source.string.strip()

        if updated_at is not None: 
            if updated_at.string is not None:
                updated_at = updated_at.string.strip()

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
    
    with open(full_path, mode="a") as f:
        writer = csv.writer(f)
        writer.writerows(lines) 

def get_item_url(html):
    " htmlから企業それぞれの求人ページのURLを取り出し返す"

    soup = BeautifulSoup(html, "html.parser")
    items = soup.main.find_all(
        "section", attrs={"class": "p-result"}, recursive=False)
    domain = "https://xn--pckua2a7gp15o89zb.com{}"

    url_list = []
    for item in items:
        # 企業のURL取得
        url = domain.format(item.a["href"])
        # url_listに加える
        url_list.append(url)
    return url_list

def get_updated_at_by_hour(l):
    p = re.compile("(\d+).*")
    m = p.fullmatch(l[1]) # updated_atから数字と時間・日前を抜き出す

    if '日' in l[1]:
        updated_at = int(m.group(1)) * 24 # 日は時間に変換
    else:
        updated_at = int(m.group(1))      # 時間はそのまま

    return updated_at

def sort_by_date(full_path):
    "file_nameで指定されたcsvファイルを日付順でソートする"

    with open(full_path, mode="r") as f:
        reader = csv.reader(f)
        lines = [row for row in reader] # 2次元配列に変換

    # updated_atで昇順で並び替え
    lines.sort(key=get_updated_at_by_hour)

    # 
    with open(full_path, mode="w") as f:
        writer = csv.writer(f)
        writer.writerows(lines) 


def main(file_name):
    base_url = read_url("base_url.txt")
    page = 1

    while True:
        url = base_url + "&pg=" + str(page)
        res = requests.post(url, data={"form[updatedAt]":'2'})
        time.sleep(1.0)                  # 警察のお世話にならないように
        if res.status_code != 200: break # 表示するページがなくなったら抜ける

        info = get_info(res.text)
        write_info(info, full_path=file_name, 
            key_order=["source","updated_at","name","job","area","pay"])

        print(page)
        page += 1 # ページの更新

    page -= 1
    print(page)

    sort_by_date(file_name)
    
if __name__ == "__main__":
    if len(sys.argv) < 2: 
        file_name = input("input the file name > ")
    else:
        file_name = sys.argv[1]
    # sort_by_date(file_name)
    # sys.exit(0)
    main(file_name)
