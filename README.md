# My Portfolio

制作物・技術記事・職務経歴・学習記録を、  
時系列で確認できるポートフォリオサイトです。

これまで取り組んだ事実を一か所に集約し、  
自分自身と閲覧者が経験の流れを確認できる場所として開発しています。

## 公開URL

https://freelance-blog.onrender.com/

## 制作期間

2026.05.28〜現在

2026年7月にVersion 1として公開内容を整理し、  
現在は新しい実績の追加と保守を中心に運用しています。

## 使用技術

### サーバーサイド

- Python
- FastAPI
- SQLAlchemy
- Jinja2

### データベース

- SQLite

### フロントエンド

- HTML
- CSS
- JavaScript

### 外部連携

- WordPress REST API
- Googleスプレッドシート

### 開発・公開環境

- Docker
- Git
- GitHub
- Render

## 概要

FastAPIを使用して開発したポートフォリオサイトです。

以下の4カテゴリーを、時系列で掲載しています。

- 制作物
- 技術記事
- 職務経歴
- 学習記録

過度な自己PRを行うのではなく、  
これまで取り組んだ内容を事実として蓄積し、  
閲覧者が判断できる形で提示することを目的としています。

## 主な機能

- 制作物管理（CRUD）
- 技術記事管理（CRUD）
- 職務経歴管理（CRUD）
- 学習記録の表示
- ログイン機能
- ユーザー権限管理
- 年による絞り込み
- カテゴリーによる絞り込み
- タグによる絞り込み
- ページネーション
- レスポンシブ対応
- WordPress REST APIとの同期処理
- Renderへのデプロイ

## WordPress REST API連携

Googleスプレッドシートに登録した対象記事のURLをもとに、  
WordPress REST APIから記事情報を取得する処理を実装しています。

取得した記事情報を整形し、  
My Portfolioのデータベースに対して、以下の処理を行います。

- 未登録の記事を新規登録する
- 登録済みの記事を更新する
- WordPress側に存在しない対象記事を削除する
- 更新が不要な記事をスキップする

現在、公開環境ではWordPress同期機能を停止しています。

そのため、公開サイトに掲載されている技術記事は、  
WordPressから自動更新されません。

## 開発履歴

### 2026.05.28

FastAPIとSQLAlchemyを使用し、  
ポートフォリオサイトの開発を開始しました。

記事管理、データベース接続、  
Routerの分割など、基盤となる処理を実装しました。

### 2026.05.30

制作物のCRUD機能を実装しました。

制作物の詳細表示、技術タグ、サムネイル表示などを追加しました。

### 2026.05.31

ログイン機能と権限管理を実装しました。

権限を持つユーザーだけが、  
コンテンツを登録・編集できる構成にしました。

### 2026.06.02

技術記事と職務経歴のCRUD機能を実装しました。

一覧表示、詳細表示、ページネーションなどを追加しました。

### 2026.06.03

Renderへデプロイしました。

本番環境向けの設定調整と、  
公開後に確認した不具合の修正を行いました。

### 2026.06.11

WordPress REST APIを使用した記事同期処理を実装しました。

Googleスプレッドシートに登録した対象記事URLからslugを取得し、  
WordPressの記事情報を取得する構成にしました。

取得した情報を整形し、  
My Portfolioのデータベースへ  
新規登録・更新・削除する処理を実装しました。

### 2026.06.14

制作物のソート機能と、  
技術記事のタグ分類機能を実装しました。

コンテンツを探しやすい画面へ改善しました。

### 2026.07

ポートフォリオの目的を、  
自己PRを中心としたサイトから、  
実績を事実として蓄積するデータベースへ見直しました。

制作物、技術記事、職務経歴、学習記録を、  
一つのタイムラインで確認できる構成へ変更しました。

## ローカル環境の起動方法

### 1. リポジトリを取得する

```bash
git clone <リポジトリのURL>
cd my-portfolio
```

### 2. 仮想環境を作成する

プロジェクトのディレクトリ内に、`.venv`という名前で仮想環境を作成します。

```bash
python3 -m venv .venv
```

### 3. 仮想環境を有効化する

macOSまたはLinuxでは、以下を実行します。

```bash
source .venv/bin/activate
```

有効化されると、ターミナルの先頭に`(.venv)`と表示されます。

### 4. 使用中のPythonを確認する

以下のコマンドで、実際に使用されているPythonを確認します。

```bash
python -c "import sys; print(sys.executable)"
```

次のように、プロジェクト内の`.venv`が表示されれば問題ありません。

```text
/Users/ユーザー名/.../my-portfolio/.venv/bin/python
```

あわせて、以下のコマンドでも確認できます。

```bash
which python
```

### 5. 必要なライブラリをインストールする

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. 開発サーバーを起動する

```bash
python -m uvicorn app.main:app --reload
```

`uvicorn`を直接実行せず、`python -m uvicorn`とすることで、  
現在有効になっている仮想環境のPythonから起動します。

### 7. ブラウザからアクセスする

開発サーバーの起動後、以下のURLへアクセスします。

http://127.0.0.1:8000/

## ローカル環境で起動できない場合

### Pythonが仮想環境へ切り替わらない場合

仮想環境を有効化した後、使用中のPythonを確認します。

```bash
python -c "import sys; print(sys.executable)"
```

次のように、プロジェクト内の仮想環境が表示されれば問題ありません。

```text
/Users/ユーザー名/.../my-portfolio/.venv/bin/python
```

以下のように、pyenvのshimなど、プロジェクト外のPythonが表示される場合は、仮想環境が正しく有効になっていません。

```text
/Users/ユーザー名/.pyenv/shims/python
```

その場合は、一度仮想環境を終了します。

```bash
deactivate
```

既存の仮想環境を削除します。

```bash
rm -rf .venv
```

仮想環境を作り直して、有効化します。

```bash
python3 -m venv .venv
source .venv/bin/activate
```

再度、使用中のPythonを確認します。

```bash
python -c "import sys; print(sys.executable)"
```

プロジェクト内の`.venv/bin/python`が表示されたら、必要なライブラリをインストールします。

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

開発サーバーを起動します。

```bash
python -m uvicorn app.main:app --reload
```

`uvicorn`を直接実行するのではなく、`python -m uvicorn`とすることで、現在使用しているPython環境から起動できます。