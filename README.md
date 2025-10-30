# How to configure SSH in Github and WSL

- Generate a New SSH Key with a custom file name.

```
ssh-keygen -t ed25519 -C "tarek82mmm@yahoo.com" -f ~/.ssh/id_ed25519_yahoo
```
- Add Your SSH Key to the SSH Agent
```
nano ~/.ssh/config
>>
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_yahoo
  IdentitiesOnly yes
```


- Test the connection
```
ssh -T git@github.com
```
-------------------------------------------
- notice: file://quality-test.json working properly.
```
aws codepipeline list-pipelines
```
```
aws codepipeline create-pipeline --cli-input-json file://quality-gate-test.json
```

# Update the current
```
aws codepipeline update-pipeline --cli-input-json file://quality-test.json

aws codepipeline update-pipeline --cli-input-json file://quality-gate-test.json
```

Tip: To capture your current pipeline as a file, run
aws codepipeline update-pipeline --cli-input-json file://quality-test.json
