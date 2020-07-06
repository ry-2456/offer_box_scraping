# -*- coding: utf-8 -*-
import re
import csv
import pprint
import requests
from requests_html import HTMLSession
# from urllib import request
from bs4 import BeautifulSoup

# from browser_manipulator import *
# from date_checker import *

def scraping(html):
    soup = BeautifulSoup(html, "html.parser")
    # items = soup.find_all("section", attrs={"class": "p-result"})
    items = soup.main.find_all("section", attrs={"class": "p-result"}, recursive=False)
    # items = [item for item in items if item.find("h2", attrs={"class": "p-result_title"})]
    print(len(items))
    print(type(soup.main.section))

    base = "https://xn--pckua2a7gp15o89zb.com{}"
    for item in items:
        print(item.a["href"])
        print(len(item.a["href"]))
        url = base.format(item.a["href"])
        print(len(url))
        print(url.strip())
        print(requests.get(url).status_code)
        # print(requests.get(base.format(item.a["href"])).status_code)
    # それぞれの求人取り出す

def scraping1(html):
    # set BeautifulSoup インスタンスの作成
    soup = BeautifulSoup(html, "html.parser") 

    # 求人のhead, body, footを取得する
    kyujin_heads = soup.find_all("tr", attrs={"class", "kyujin_head"})
    kyujin_bodys = soup.find_all("tr", attrs={"class", "kyujin_body"})
    kyujin_foots = soup.find_all("tr", attrs={"class", "kyujin_foot"})

    # 受付年月日のdateオブジェクトを取得
    # reception_date_list = get_reception_date(html)

    # kyujin_footsを詳細ボタンを持っているものに絞り込む
    kyujin_foots = [elem for elem in kyujin_foots if elem.find("a") is not None]

    occupations = []   # 職種
    companies = []     # 会社の名前
    offer_numbers = [] # 求人番号
    # locations = []     # 勤務地
    # urls = []          # 会社のホームページURL

    # 職種を取得
    for head in kyujin_heads:
        occupations.append(head.find("tr").find_all("td")[1].div.string)

    # 会社名, 求人番号を取得
    for body in kyujin_bodys:
        body_row = body.find_all("tr")
        for i in range(len(body_row)):
            table_data = body_row[i].find_all("td")  # 全テーブルデータを取得
            row_name = table_data[0].string          # データの名称を取得
            if row_name is None: continue
            if row_name == "事業所名":
                # div中に<br>タグがある場合に対処
                # <div>株式会社イメージ<br>福岡支店</div>
                # この場合table_data[0].div.contentsでdiv直下の
                # テキストをlistで取得. listの要素をスペース区切りで連結する
                comp_name = table_data[1].div.string
                if comp_name is None:
                    comp_name = " ".join(
                        [elem for elem in table_data[1].div.contents if elem.__class__.__name__ == "NavigableString"]) 
                companies.append(comp_name)
            elif row_name == "求人番号":
                offer_numbers.append(table_data[1].div.string)

    # 事業所名を公開していない会社を取り除く
    for i, comp_name in enumerate(companies):
        if "公開していません" in comp_name:
            occupations[i] = None
            companies[i] = None
            offer_numbers[i] = None

    # Noneを削除
    occupations = [elem for elem in occupations if elem is not None]
    companies = [elem for elem in companies if elem is not None]
    offer_numbers = [elem for elem in offer_numbers if elem is not None]

    return (companies, occupations, offer_numbers)

def read_html(full_path):
    "full_pathで指定された、ファイルを読み込みその中身を返す"
    with open(full_path) as f:
        return f.read()

def write_joboffer_info(full_path, companies, occupations, offer_numbers):
    # companies     : 会社の名前のリスト
    # occupations   : 職種
    # offer_numbers : 求人番号
    lines = []

    for comp, occup, off_num in zip(companies, occupations, offer_numbers):
        lines.append([comp, occup, off_num])

    with open(full_path, mode="a") as f:
        writer = csv.writer(f)
        writer.writerows(lines) 

def main(full_path):
    # vimの画面からブラウザへ
    switch_window()
    for i in range(10//30+1):
        print("###### {} ######".format(i+1))
        # html取得
        html = get_html()
        # htmlのページを閉じる
        del_tab()
        # スクレイピングを行う
        comp_names, occups, offer_nums = scraping(html)
        # csvファイルに書き込み
        write_joboffer_info(full_path, comp_names, occups, offer_nums)
        # 次のページヘ
        go_next_page()
        time.sleep(1)

def test(full_path):  
    for i in range(5):
        print("###### {} ######".format(i+1))
        html = get_html()
        # htmlのページを閉じる
        del_tab()
        # スクレイピングを行う
        comp_names, occups, offer_nums = scraping(html)
        # csvファイルに書き込み
        write_joboffer_info(full_path, comp_names, occups, offer_nums)
        # 次のページへ
        go_next_page()
        time.sleep(1)

if __name__ == "__main__":
    session = HTMLSession()
    base_url = "https://xn--pckua2a7gp15o89zb.com/adv/?keyword=web%E3%82%A8%"\
    "E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2&area=%E5%A4%A7%E9%98%AA%E5%BA%9C%20o"\
    "r%3A%E5%85%B5%E5%BA%AB%E7%9C%8C%20or%3A%E4%BA%AC%E9%83%BD%E5%BA%9C%20or%3"\
    "A%E6%BB%8B%E8%B3%80%E7%9C%8C&pg={}"

    res = session.get(base_url.format(1))
    res.render.html()
    p = re.compile("/jb/[a-z0-9]{32}")
    result = p.findall(res.text)
    print(result)
    for r in result:
        print(r)
    print(len(result))
