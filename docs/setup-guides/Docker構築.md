## 1．Docker Desktopのインストール

<https://www.docker.com/ja-jp/products/docker-desktop/>

上記サイトでAMD64版をインストールします

![alt text](image/docker/docker-image-01.png)

ダウンロードしたインストーラを立ち上げ、デフォルトのチェックのままOKを押下しインストール

![alt text](image/docker/docker-image-02.png)

インストール完了

![alt text](image/docker/docker-image-03.png)

アカウントはスキップボタンで作成をスキップ

![alt text](image/docker/docker-image-04.png)

2．WSL Integrationの設定

ヘッダーの歯車→Resources→WSL Integrationタブに移動→\
Ubuntu2404-frontend-preview-envのトグルをONにする→画面右下「Apply＆Restart」を押下しDockerを再起動

![alt text](image/docker/docker-image-05.png)

## 3．インストールと設定の確認

Powershellを開く

下記コマンドを入力してUbuntuを起動

```null
wsl -d Ubuntu2404-frontend-preview-env
```

![alt text](image/docker/docker-image-06.png)


docker --versionでUbuntuにDockerがインストールされていることを確認

```null
docker --version
```

![alt text](image/docker/docker-image-07.png)


バージョンが表示されればDockerの準備は完了