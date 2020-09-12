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
    with open(f_name, encoding="utf-8") as f:
        base_url = f.read()
        return base_url.strip()

# 既知の会社を管理する
seen = []

def get_info(html):
    "会社名(name), 職種(job), 年収(pay), 勤務地(pay), 掲載元(source), 掲載日時(updated_at)"

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

        if job: job = job.text.strip()
        else: job = "公開していません"

        if area: area = area.text.strip()
        else: area = "公開していません"

        if pay: pay = pay.text.strip()
        else: pay = "公開していません"

        if source: source = source.text.strip()
        else: source = "公開していません"

        if updated_at: updated_at = updated_at.text.strip()
        else: updated_at = "公開していません"

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

    if m is None: return 24*7

    if '日' in l[1]:
        updated_at = int(m.group(1)) * 24 # 日は時間に変換
    else:
        updated_at = int(m.group(1))      # 時間はそのまま

    return updated_at

def sort_by_date(full_path):
    "file_nameで指定されたcsvファイルを日付順でソートする"

    with open(full_path, mode="r", encoding='utf-8') as f:
        reader = csv.reader(f)
        lines = [row for row in reader] # 2次元配列に変換

    # updated_atで昇順で並び替え
    lines.sort(key=get_updated_at_by_hour)

    with open(full_path, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(lines) 


def main(file_name, url_name):
    base_url = read_url(url_name)
    page = 1

    while True:
        url = base_url + "&pg=" + str(page)
        res = requests.post(url, data={"form[updatedAt]":'1'    # 1=>24時間以内 2=>3日以内 3=>7日以内
                                     , "form[employType]":'1'}) # 1=>正社員
        time.sleep(1.0)                  # 警察のお世話にならないように
        if res.status_code != 200: break # 表示するページがなくなったら抜ける

        info = get_info(res.text)
        write_info(info, full_path=file_name, 
            # key_order=["source","updated_at","name","job","area","pay"])
            key_order=["name","job","area","pay","updated_at","source"])

        print(page)
        page += 1 # ページの更新

    page -= 1
    print(page)

    sort_by_date(file_name)
    
if __name__ == "__main__":
    url_name = input("input the url name > ")
    file_name = input("input the file name > ")
    main(file_name, url_name)
