# 内容
Trusted Advisorで検出された、コストが掛かりすぎているかもしれないAWSサービスと、そのサービスで予想される削減コストをslackに通知します。

# 事前準備
- 対象のAWSアカウントにAssume Roleを作成します<br>
他のAWSアカウントのTrusted Advisor情報を取得するために、そのアカウントにAssume Role を作成します。

- AWSアカウントIDをSecrets Managerに保存しましょう。<br>
lambda内で他のAWSアカウントのアカウントIDを取得する処理があるので、Secrets Managerに保存します

例）
```
{
  "accoun-ids": {
    "account name": "xxxxxxxxxxxx",
    "account name": "xxxxxxxxxxxx"
  }
}
```
