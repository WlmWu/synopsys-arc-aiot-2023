# synopsys-arc-aiot-2023 group7
Continued the development of the project from https://github.com/Dynacloud-Co/synopsys-arc-aiot-2023
## 系統需求
- Python 版本：3.7 或更高版本
- 作業系統：MacOS 、 Linux

## 安裝指南
1. 複製遠端 GitHub Repo
```shell!
git clone https://github.com/WlmWu/synopsys-arc-aiot-2023.git
```
2. 安裝相關程式庫：
```shell!
pip3 install --upgrade pip
pip3 --no-cache-dir install -r requirements.txt
```
3. 更改 Authorization Token
```shell!
# Replace APP_AUTH_TOKEN with the random string in the dynacloud/config.
APP_AUTH_TOKEN=$(openssl rand -hex 40)
sed -i "s/APP_AUTH_TOKEN = '.*'/APP_AUTH_TOKEN = '$APP_AUTH_TOKEN'/" ./dynacloud/config.py
```
4. 更改發信帳號之 Google App Password
```python!
# In speaker_recognizion/config.py
GMAIL_APP_PASSWORD = '%_put_your_auth_token_here_%'
```

## 使用指南
### 執行方式
- 執行 API
```shell!
export FLASK_APP=main.py
flask run --reload --debugger --host 0.0.0.0 --port 8080
```
- 註冊新員工
```shell!
python -m speaker_recognition.recognizer -n path/to/new/audios
```

### API Docs
可參考 demo.py 之 `send_test_audio()`或執行 demo.py 測試：
```python!
python demo.py -f path/to/wav/testing -i your.vm.ip
```
#### 音訊辨識
<details>
  <summary><code>POST</code><code><b>/recognition</b></code></summary>

##### Headers
> | key           | value                  | description                             |
> |---------------|------------------------|-----------------------------------------|
> | Authorization | Bearer $APP_AUTH_TOKEN | Please provide the authorization token. |

##### Parameters
> | name  |  type    | data type  | description             |
> |-------|----------|------------|-------------------------|
> | audio | required | audio file | wav  |

##### Responses
> | http code | content-type        | response            | description |
> |-----------|---------------------|---------------------|-------------|
> | `200`     | `application/json`  | `{"EID": [...]}`   | OK          |
> | `4xx`     | `application/json`  | `{"errors": [...]}` | ClientError |
> | `5xx`     | `application/json`  | `{"errors": [...]}` | ServerError |

##### Example Response
聲音無法識別：
```json!
{
  "EID": "unknown"
}
```
聲音識別成功則為職員 ID，如識別為 ID 1 號：
```json!
{
  "EID": "1"
}
```
</details>

#### 資料庫瀏覽
<details>
  <summary><code>GET</code><code><b>/database</b></code></summary>

##### Headers
> | key           | value                  | description                             |
> |---------------|------------------------|-----------------------------------------|
> | Authorization | Bearer $APP_AUTH_TOKEN | Please provide the authorization token. |

##### Responses
> | http code | content-type        | response            | description |
> |-----------|---------------------|---------------------|-------------|
> | `200`     | `text/html`  |  index.html  | OK          |
> | `4xx`     | `application/json`  | `{"errors": [...]}` | ClientError |
> | `5xx`     | `application/json`  | `{"errors": [...]}` | ServerError |

</details>

