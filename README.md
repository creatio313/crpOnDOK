# 高火力DOKでCyberRealistic Ponyを動作させるソース群

## ファイル内容
- Dockerfile：DOK上で動かすコンテナイメージの元ファイル。curlのアクセストークン部分をcivitaiで取得したアクセストークンに置換してください。
- docker-entrypoint.sh：Dockerのエントリーポイント。変更不要です。
- runner.py：GPU上で、CyberRealistic Ponyを動かすPythonスクリプトです。変更不要です。
- aifluxtest.ps1：Windows PowerShellから高火力DOKのAPIを呼び出し、画像生成タスクを作成します。使用時には各種認証情報を入力して下さい。第一引数にプロンプトを記述したcsvを配置して下さい。STEP数やbatch等のパラメータは適宜変更して下さい。
- imagePrompts.csv：CSVファイルのひな形です。ファイル名接頭辞、プロンプト、ネガティブプロンプトを記述します。

## 使用順序
### ファイル準備
- CivitaiのアクセストークンをDockerfileに貼り付けて下さい。
- さくらのクラウドホームで、高火力DOK向けのアクセスキーを作成し、aifluxtest.ps1に貼り付けて下さい。
- さくらのクラウドでコンテナレジストリを作成し、設定する予定のイメージ名（Docker imageのTag）をaifluxtest.ps1に貼り付けて下さい。
- 作成したコンテナレジストリにユーザーを作成、高火力DOKのページでそのレジストリ認証情報を登録し、発行されたIDをaifluxtest.ps1に貼り付けて下さい。
- さくらのオブジェクトストレージのバケット（石狩を推奨）で作成し、その認証情報と出力先バケット名を貼り付けて下さい。
### Docker image build & push
Docker imageをbuild、pushします。
さくらのクラウド石狩第3ゾーン・サーバーで2コア、4GB、SSD100GB、ubuntu最新LTSのスペックで動かした際は、ビルドにおよそ10分かかりました。
```sh
sudo docker build -t [コンテナレジストリ設定名].sakuracr.jp/[任意設定値]:latest .

sudo docker login [コンテナレジストリ設定名].sakuracr.jp/[任意設定値]
Username:コンテナレジストリのユーザー名
Password:コンテナレジストリのパスワード

sudo docker image push [コンテナレジストリ設定名].sakuracr.jp/[任意設定値]:latest
```
### 高火力DOKを呼ぶ
- csvファイルにファイル名接頭辞、プロンプト、ネガティブプロンプトを入力します。
- PowerShellの第一引数にcsvファイルのパスを付けて、実行して下さい。
- 高火力DOKの画面にタスクが登録されます。完了し次第、タスク詳細画面のアーティファクトか、オブジェクトストレージ（WinSCPを使った接続を推奨）から生成結果をダウンロードして下さい。

## ライセンス
複製改変再配布に制限はありません。

## 参考文献
https://knowledge.sakura.ad.jp/38718/
https://knowledge.sakura.ad.jp/39187/
