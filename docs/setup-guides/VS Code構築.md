## 1．拡張機能「Dev-Containers」、「WSL」をインストール

VSCodeを起動し、以下の拡張機能をインストールします

![image](image/vscode/vscode-image-01.png)
![image](image/vscode/vscode-image-02.png)

2．WSLからVSCodeを起動

PowerShellを開き、以下のコマンドを入力していきます

\
Ubuntuを起動

```auto
wsl -d Ubuntu2404-dk-ssec
```

Ubuntu上にクローンしたリポジトリのディレクトリに移動する

```auto
cd /home/comthink/git/nct-dk-ssec
```

VSCodeを起動

```auto
code .
```

![image](019abed983a179778d25e97215205ac6/image.png)

VSCodeが起動したらCtrl＋Shift＋Pを押下し、コマンドパレットを開く

「devcontainers」と入力して「キャッシュなしでコンテナをリビルド」を押下![image](019abed983a179778d25e97215205ac6/RebuildContainer.png)

コンテナのビルドが開始し、完了すると下記画面同様bc_PropertyManagementフォルダがワークスペースとして読み込まれる\
※ビルドには数分かかる\
※ビルドのログを表示した場合や、ターミナルを表示していなかった場合、Ctrl+Shift+@で表示する

![image](019abed983a179778d25e97215205ac6/image.png)


## 3. ビルドの成否確認

VSCodeのターミナルから、下記コマンドを実行して実行環境が整っているかを確認

```auto
java --version 
node -v
mvn -v
```

## 4. バージョンが確認できれば完了

![image](019abed983a179778d25e97215205ac6/image.png)

