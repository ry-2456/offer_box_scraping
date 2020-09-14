# 求人ボックススクレイピングプログラム
### 実行手順
1. ```pip install -r requirements.txt```で必要なライブラリをインストール.
2. url_dirフォルダにhoge_url.txtを用意し，そこに求人ボックスで職業と働く場所を指定した時に
   作られるURLを貼り付ける
3. ```$ python offer_box.py```で実行する．
   取得した求人情報の保存ファイル名ははurlファイルによる．例えばurlのファイル名がhoge_url.txtの場合は
   hoge日付.csvとなり，data_dirに保存される．
