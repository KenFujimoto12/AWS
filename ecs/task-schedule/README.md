# バッチ処理をECSTaskで構築
### バッチ処理をECSのタスクスケジューリングで実行する手順です。
### タスクが失敗した場合、slackに通知するようにします。
###※ecs/batch/gettersを参照ください
###※スケジューリングタスクに渡すcredentialは専用のIAMユーザーのものを渡してください。

1. クラスターを作成する。
- ecs-cluster-batch.ymlをcloudformationで実行し、ECSクラスターを作成します。

2. スケジュールタスク用のタスク定義を作成する。
- ecs-taskdefinition-batch.ymlを実行して、スケジュールタスク用のタスク定義を作成します。
  - ログはcloudwatch logで管理します。
  - Fargateを指定しています。
  - 環境変数は媒体ごとに適宜変更してください。

3. lambda関数を保存するS3バケットを作成する
- 5.でアラームをslack通知するためのlambda関数をzip化してS3バケットに保存します
  - ecs-s3-bucket.ymlを実行しバケットを作成します
  - lambda-function/notify-batch-error-to-slack.pyをzipにして作成したバケットに保存します

4. slackへの通知環境を作る
- ecs-alarm-batchを実行して、スケジュールタスクのロググループ、メトリクス、アラーム、SNS、Lambdaを作成します。
  - メトリクスは10秒間各で、指定の文字(filter pattern)がログに残ったときにアラーム状態に遷移します。（アラームの状態は30秒でもとに戻ります)

5. スケジュールタスク実行イベントを作成する
- ecs-task-event.ymlを実行して、スケジュールタスク実行イベントを作成します。
  - 不要なイベントは適宜削除してください。
  - ❗subnetはプライベートを指定してください。(ルートテーブルにnat gatewayを登録します)
  - ❗Task DefinitionのARNを指定する際、リビジョンは指定しないでください。指定してしまうと最新のリビジョンが作成された際にそれを参照できません。

