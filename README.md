# EZ-Web 自动签到工具

## 项目简介

EZ-Web 自动签到工具是一个基于 Python 的自动化脚本，用于 M-SEC 网站的每日自动签到。该工具支持验证码自动识别、定时任务执行，并提供钉钉和邮件通知功能。

## 功能特性

- 🤖 **自动签到**: 自动完成 M-SEC 网站的每日签到任务
- 🔍 **验证码识别**: 集成云码平台 API，自动识别登录验证码
- ⏰ **定时执行**: 支持北京时间每天早上 9 点自动执行
- 📱 **钉钉通知**: 签到结果实时推送到钉钉群
- 📧 **邮件通知**: 支持邮件方式发送签到报告
- 📊 **积分查询**: 自动查询并显示当日获得积分和总积分
- 📝 **日志记录**: 详细的日志记录，便于问题排查

## 安装依赖

```bash
pip install requests schedule pytz apscheduler loguru
```

## 配置说明
### 1. 验证码识别 API 申请
访问 云码平台 注册账号并获取 API Token。 

申请地址：https://console.jfbym.com/register/TG97164

### 2. 配置文件设置
编辑 config/config.ini 文件，填入相应的配置信息：

```
[dingding] (可选)
dingding_secret = 你的钉钉机器人密钥
dingding_access_token = 你的钉钉机器人访问令牌
dingding_userid = 你的钉钉用户ID

[EMAIL] (可选)
email_sender = 发件人邮箱地址
email_pass = 邮箱授权码（非登录密码）
receiver_email = 收件人邮箱地址

[EZ_WEB] (必须)
username = M-SEC网站用户名 # 账户地址：https://msec.nsfocus.com/
password = M-SEC网站密码

[jfbym] (必须)
Token = 云码平台API Token #  申请地址：https://console.jfbym.com/register/TG97164
```
### 配置项说明 钉钉配置
- dingding_secret : 钉钉机器人的加签密钥
- dingding_access_token : 钉钉机器人的 Webhook 访问令牌
- dingding_userid : 需要 @ 的钉钉用户ID 邮件配置
- email_sender : 发件人邮箱（建议使用163邮箱）
- email_pass : 邮箱授权码（需要在邮箱设置中开启SMTP服务并获取授权码）
- receiver_email : 接收通知的邮箱地址 网站登录配置
- username : M-SEC 网站的登录用户名
- password : M-SEC 网站的登录密码 验证码识别配置
- Token : 在云码平台申请的 API Token
## 项目结构
```
ez-web_sign_in/
├── README.md              # 项目说明文档
├── config/
│   └── config.ini         # 配置文件
├── sign_in.py             # 主程序文件
├── push_ddmail.py         # 钉钉和邮件推送模块
├── dark_log.py            # 日志记录模块
└── log_/                  # 日志文件目录（运行时
自动创建）
```
## 使用方法
脚本默认运行在定时任务模式，脚本第一次执行时候，会执行签到，后面是会在每天北京时间早上 9 点自动执行签到任务。启动后会持续运行，等待预定时间执行。

```
nohup python3 sign_in.py &
```
启动成功后，您会看到类似以下的提示信息：

```
任务已设定，将在每天北京时间 09:00 执行。当前时间: 
2025-01-XX XX:XX:XX
```
## 通知功能
脚本执行完成后会自动发送通知，包含以下信息：

- 登录状态
- 签到结果
- 积分查询结果
- 执行时间
通知方式：

1. 钉钉通知 : 发送到配置的钉钉群 （可选）
2. 邮件通知 : 发送到配置的邮箱（可选）
## 日志说明
- 日志文件保存在 log_/ 目录下
- 按日期自动分割，格式为 YYYY-MM-DD.log
- 包含详细的执行过程和错误信息
## 注意事项
1. 配置文件安全 : 请妥善保管配置文件，避免泄露账号密码等敏感信息
2. 网络环境 : 确保运行环境能够正常访问目标网站和相关API
3. 验证码识别 : 云码平台为付费服务，请确保账户余额充足
4. 邮箱设置 : 使用163邮箱时需要开启SMTP服务并使用授权码而非登录密码
5. 持续运行 : 定时任务模式需要保持脚本持续运行
## 故障排除
1. 验证码识别失败 : 检查云码平台Token是否正确，账户余额是否充足
2. 登录失败 : 检查用户名密码是否正确
3. 通知发送失败 : 检查钉钉机器人配置或邮箱配置是否正确
4. 定时任务不执行 : 确保脚本持续运行，检查系统时间是否正确
## 许可证
本项目仅供学习和个人使用，请遵守相关网站的使用条款。
