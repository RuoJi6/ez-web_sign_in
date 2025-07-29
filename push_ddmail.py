# coding:utf-8
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import logging.handlers
import inspect
import configparser
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dark_log import DarkLog


# logger.set_console_output(False) # 默认打印日志
class Dingdingmail:
    def __init__(self,dingdingmail_uuid):
        self.logger = DarkLog(dingdingmail_uuid)

    @staticmethod
    def get_config(value_name):
        """
        功能描述: 返回config/config.ini中配置文件对于值
        参数:
            value_name : 需要获取的字段名
        返回值:
        异常描述:
        调用演示:
            secret = self.get_config('secret')
        """
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        sections = config.sections()
        for section in sections:  # 循环[n+1]
            options = config.options(section)
            for option in options:  # 循环详细的字段
                value = config.get(section, option)
                if value_name == option:
                    return value

    def get_dingding(self, title_="", text_=""):
        """
        功能描述: 用于记录钉钉的通知
        参数:
            text_ : 钉钉通知内容
            title_ : 钉钉通知标题
        返回值:
            {"code": 404, "data": "配置文件为空,跳过钉钉通知"}
            {"code": 200, "data": dingding_}  返回钉钉状态码
            {"code": 500, "data": e}
        异常描述:
            {"code": 404, "data": "配置文件为空,跳过钉钉通知"}
            {"code": 200, "data": dingding_}  返回钉钉状态码
            {"code": 500, "data": e}
        调用演示:
            proxylog = ProxyLog()
            proxylog.get_dingding("测试标题", "这个是测试内容")
        """
        timestamp = str(round(time.time() * 1000))
        dingding_secret = self.get_config('dingding_secret')
        dingding_access_token = self.get_config('dingding_access_token')
        dingding_userid = self.get_config('dingding_userid')
        if dingding_secret == '' or dingding_access_token == '' or dingding_userid == '':
            self.logger.error(f"配置文件为空,跳过钉钉通知",True)
            return {"code": 404, "data": "配置文件为空,跳过钉钉通知"}
        secret_enc = dingding_secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, dingding_secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        url = f"https://oapi.dingtalk.com/robot/send?access_token={dingding_access_token}&timestamp={timestamp}&sign={sign}"
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title_,
                "text": f"@{dingding_userid}{text_}"
            },
            "at": {
                "atUserIds": [
                    dingding_userid
                ],
                "isAtAll": False
            }
        }
        try:
            dingding_ = requests.post(url, json=data).json()
            if dingding_["errcode"] == 300005 or dingding_["errcode"] == 310000:
                self.logger.error(dingding_,True)
                return {"code": 403, "data": dingding_}
            self.logger.info(f"Request title: {title_} text:{text_}",False)
            self.logger.info(f"Response {dingding_}",False)
            self.logger.info("dingding推送成功！")
            return {"code": 200, "data": dingding_}
        except Exception as e:
            self.logger.exception(f"dingding推送失败：{str(e)}",False)
            return {"code": 500, "data": e}


    def get_mail(self,subject_text,content_text,xlsx_file=None):
        """
        功能：发送邮件

        参数；
                subject_text: 邮件主题
                content_text: 邮件正文
                xlsx_file: xlsx文件的路径
        :return:
        """

        def send_email(sender, password, receiver, subject, content, xlsx_file_path):
            """
            使用163邮箱发送带有xlsx附件的邮件

            参数:
                sender: 发件人邮箱（163邮箱）
                password: 授权码（不是邮箱密码，需要在163邮箱设置中获取）
                receiver: 收件人邮箱，可以是字符串或列表
                subject: 邮件主题
                content: 邮件正文
                xlsx_file_path: xlsx文件的路径
            """
            # 创建邮件对象
            msg = MIMEMultipart()
            if isinstance(receiver, str):
                receiver = [email.strip() for email in receiver.split(",")]

            # 设置发件人、收件人和主题
            msg['From'] = sender
            if isinstance(receiver, list):
                msg['To'] = ','.join(receiver)
            else:
                msg['To'] = receiver
            msg['Subject'] = subject

            # 添加邮件正文
            msg.attach(MIMEText(content, 'html', 'utf-8'))

            # 添加xlsx附件
            if xlsx_file_path and os.path.exists(xlsx_file_path):
                with open(xlsx_file_path, 'rb') as f:
                    xlsx_part = MIMEApplication(f.read(), Name=os.path.basename(xlsx_file_path))

                # 设置附件头信息
                xlsx_part['Content-Disposition'] = f'attachment; filename="{os.path.basename(xlsx_file_path)}"'
                msg.attach(xlsx_part)
            elif xlsx_file_path:
                self.logger.warning(f"找不到指定的xlsx文件: {xlsx_file_path}, 邮件将不带附件发送。")


            # 连接163邮箱服务器并发送邮件
            try:
                server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 163邮箱使用SSL，端口465
                server.login(sender, password)  # 登录

                # 发送邮件
                if isinstance(receiver, list):
                    server.sendmail(sender, receiver, msg.as_string())
                else:
                    server.sendmail(sender, [receiver], msg.as_string())

                server.quit()  # 关闭连接
                self.logger.info(f"邮件发送成功!",True)
                return True
            except Exception as e:
                self.logger.exception(f"邮件发送失败: {str(e)}",False)
                return False
        email_sender = self.get_config('email_sender')
        email_pass = self.get_config('email_pass')
        receiver_email = self.get_config('receiver_email')
        if email_sender == '' or email_pass == '' or receiver_email == '':
            self.logger.error(f"配置文件为空,跳过邮件通知",True)
            return {"code": 404, "data": "配置文件为空,跳过邮件通知"}
        else:
            send_email(email_sender, email_pass, receiver_email, subject_text, content_text, xlsx_file)
        # if email_sender is not None and email_pass is not None and receiver_email is not None:
        #     send_email(email_sender,email_pass,receiver_email,subject_text,content_text,xlsx_file)
