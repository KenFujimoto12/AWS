# リソース類

## 【必要なAWSリソース】

- CodeBuild(build, update service)

- CodePipeline

## 各リソースのIAMロール

- Artifacts Store用のS3バケット

- 通知用のAWS SNS, cloudwatch event, lambda

## 【実行するcloudformationリソースymlファイル】

- codepipeline.yml

- codepipeline-status-notification.yml

# 事前準備

## S3バケット作成



- アクセストークンをsecret managerで管理

アクセストークンをsecert managerで保存して、codepipeline.yml内でDynamic References(yml表記法)を使って、ymlファイル内で値を取得します。

※先にkmsで専用のキーを作成して、そのキーで暗号化して保存してください。

- サービス媒体側のソースでaws-cliを用いてS3アクセスしているため、専用のS3アクセスユーザーを作成する。(codepipelineのUpdateServiceステージで環境変数として渡す用)


- 通知用のlambda関数をzip化してS3バケットに保存します。


# 手順

サービス媒体側で以下のファイルを用意します。

codepipeline/buildspe.yml  → Dockerfileを元にイメージを作り、ECRにpushします。

Dockerfile 

codepipeline/updatespec.yml  →  ECRのイメージを参照するようにサービスを更新します。

codepipeline/update_taskdefinition.sh → サービスを更新する際に参照するタスク定義を作成します。


2. codepipeline環境を作成する

### ecs-codepipeline.ymlをcloudformationにて実行します。

- sourceステージ → 必要なソースコードを取得します

- buildステージ → ビルドを行います

- update serviceステージ → 新しいタスク定義を作成して、ECSサービスを更新します

- deployステージ → 指定のクラスターに新しいタスクをデプロイします

※パラメーター値は媒体に合わせて入力してください。

※codepipelineステージも媒体ごとに合わせてください


※注意

ソースステージで複数ソースを指定するとcodepipelineが2回動きます。

原因はわかりません。

3. codepipelineのステータス通知環境を作成する。

codepipeline-status-notification.ymlをcloudformationにて実行します。

※パラメーター値は媒体に合わせて入力してください


# サポート

## 【デプロイ後に新しいタスクが作成されない問題を解決する】

### AMIによってストレージ領域に制限があり、その制限を超えている可能性がある

https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/CannotCreateContainerError.html

(Amazon ECS-optimized Amazon Linux AMIであればDocker によるイメージとメタデータの保存用に 22 GiB のボリュームの制限がある)

### 作成されたイメージのサイズは小さくしよう

無駄なパッケージはインストールしない。

Dockerfile内ではマルチステージビルドを用いていて、かなりイメージサイズは小さくなります。

### エージェント設定でイメージとコンテナーのライフサイクルは短くしよう

https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/ecs-agent-config.html

インスタンスにSSH接続

ecsエージェントの必要な設定値(etc/ecs/ecs.config)

ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=30mECS_IMAGE_CLEANUP_INTERVAL=30m

反映のさせかた

```
$ sudo start ecs
$ sudo stop ecs
```

### 緊急で対応したい場合

対象のインスタンスにssh接続

```
$ docker ps -a 
$ docker rm {statusがexitedのコンテナID}
$ docker images -a
$ docker rmi {参照されていないイメージID}

```

不要なイメージが削除され新しいタスクが作成できるようになる

## 【参考】

codepipelineについてはここにすべて書いてあります。

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/reference-pipeline-structure.html

ビルドアクション特有の変数の名前空間を作成して、他のステージで用いる

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/reference-variables.html

codepipelineステージ内のEnvironmentVariablesはjsonで表記する

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/action-reference-CodeBuild.html