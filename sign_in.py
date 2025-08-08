import requests
import base64
import json
import configparser
import schedule
import time
from datetime import datetime
import pytz
from dark_log import DarkLog
from push_ddmail import Dingdingmail
from apscheduler.schedulers.blocking import BlockingScheduler



logger = DarkLog('ez-web_sign_in')
notifier = Dingdingmail('ez-web_sign_in')
class AutoQiandao:
    def __init__(self, username, password, yunma_token):
        self.username = username
        self.password = password
        self.results = []
        self.max_retries = 3  # 最大重试次数

        # M-SEC 网站的 URL
        self.MSEC_BASE_URL = "https://msec.nsfocus.com"
        self.CAPTCHA_URL = self.MSEC_BASE_URL + "/backend_api/account/captcha"
        self.LOGIN_URL = self.MSEC_BASE_URL + "/backend_api/account/login"
        self.POINT_URL = self.MSEC_BASE_URL + "/backend_api/point/common/get"
        self.CHECKIN_URL = self.MSEC_BASE_URL + "/backend_api/checkin/checkin"

        # 云码平台的 URL 和 Token
        self.YUNMA_URL = "http://api.jfbym.com/api/YmServer/customApi"
        self.YUNMA_TOKEN = yunma_token

        # 模拟浏览器的 Headers
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://msec.nsfocus.com",
            "Referer": "https://msec.nsfocus.com/auth/login",
        }

    def get_captcha(self):
        logger.info("正在获取验证码...")
        try:
            response = requests.post(self.CAPTCHA_URL, headers=self.HEADERS, json={})
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                captcha_id = data["data"]["id"]
                captcha_base64 = data["data"]["captcha"].split(",")[1]
                logger.info(f"获取验证码成功，ID: {captcha_id}")
                return captcha_id, captcha_base64
            elif data.get("status") == 429:
                logger.warning(f"遇到频率限制: {data}")
                time.sleep(30)  # 增加等待时间
                return None, None
            else:
                logger.error(f"获取验证码失败: {data}")
                time.sleep(10)
                return None, None
        except Exception as e:
            logger.exception(f"请求验证码时发生错误: {e}")
            return None, None

    def recognize_captcha(self, captcha_base64):
        logger.info("正在识别验证码...")
        payload = {"image": captcha_base64, "token": self.YUNMA_TOKEN, "type": "50103"}
        try:
            response = requests.post(self.YUNMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 10000:
                captcha_answer = data["data"]["data"]
                logger.info(f"验证码识别成功: {captcha_answer}")
                return captcha_answer
            else:
                logger.error(f"验证码识别失败: {data.get('msg')}")
                # self.results.append(f"验证码识别失败: {data.get('msg')}")
                return None
        except Exception as e:
            logger.exception(f"请求验证码识别时发生错误: {e}")
            # self.results.append(f"请求验证码识别时发生错误: {e}")
            return None

    def login(self, captcha_id, captcha_answer):
        logger.info("正在登录...")
        payload = {
            "username": self.username,
            "password": self.password,
            "captcha_id": captcha_id,
            "captcha_answer": captcha_answer
        }
        try:
            response = requests.post(self.LOGIN_URL, headers=self.HEADERS, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                token = data["data"]["token"]
                logger.info("-------> web登录成功！")
                self.results.append("-------> web登录成功！")
                return token
            else:
                logger.error(f"登录失败: {data}")
                self.results.append(f"登录失败: {data}")
                return None
        except Exception as e:
            logger.exception(f"登录时发生错误: {e}")
            self.results.append(f"登录时发生错误: {e}")
            return None

    def check_in(self, auth_token):
        logger.info("正在执行签到...")
        headers = self.HEADERS.copy()
        headers["Authorization"] = auth_token
        try:
            response = requests.post(self.CHECKIN_URL, headers=headers, json={})
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                logger.info("签到成功！")
                self.results.append("签到成功！")
            elif data.get("status") == 400 and data.get("message") == "签到失败" and data.get("data") == "今天已经签到过了":
                message = data.get('message', '未知错误')
                data = data.get('data', '')
                logger.error(f"错误: {message}，信息: {data}")
                self.results.append(f"错误: {message}，信息: {data}")
            else:
                message = data.get('message', '未知错误')
                logger.error(f"签到失败: {message}")
                self.results.append(f"签到失败: {message}")
        except Exception as e:
            logger.exception(f"签到时发生错误: {e}")
            self.results.append(f"签到时发生错误: {e}")

    def get_points(self, auth_token):
        logger.info("正在查询积分...")
        headers = self.HEADERS.copy()
        headers["Authorization"] = auth_token
        try:
            response = requests.post(self.POINT_URL, headers=headers, json={})
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                accrued = data["data"]["accrued"]
                total = data["data"]["total"]
                point_info = f"查询积分成功: 累计积分 {accrued}, 当前积分 {total}"
                logger.info(point_info)
                self.results.append(point_info)
            else:
                logger.error(f"查询积分失败: {data}")
                self.results.append(f"查询积分失败: {data}")
        except Exception as e:
            logger.exception(f"查询积分时发生错误: {e}")
            self.results.append(f"查询积分时发生错误: {e}")

    def run(self):
        retry_count = 0
        success = False
        
        while retry_count < self.max_retries and not success:
            retry_count += 1
            logger.info(f"开始第 {retry_count} 次尝试...")
            
            captcha_id, captcha_base64 = self.get_captcha()
            if captcha_id and captcha_base64:
                captcha_answer = self.recognize_captcha(captcha_base64)
                if captcha_answer:
                    auth_token = self.login(captcha_id, captcha_answer)
                    if auth_token:
                        self.check_in(auth_token)
                        self.get_points(auth_token)
                        success = True
                        break
                    else:
                        logger.warning(f"第 {retry_count} 次登录失败，准备重试...")
                        time.sleep(min(2 ** retry_count, 60))
                else:
                    logger.warning(f"验证码识别失败，准备重试...")
                    time.sleep(min(2 ** retry_count, 60))
            else:
                logger.warning(f"获取验证码失败，准备重试...")
                time.sleep(min(10 * retry_count, 120))
        
        if not success:
            logger.error(f"经过 {self.max_retries} 次尝试后仍然失败")
        
        # 发送通知
        summary_title = f"M-SEC 签到 - {self.username}"
        summary_content = "\n\n".join(self.results)
        notifier.get_dingding(summary_title, summary_content)
        notifier.get_mail(summary_title, summary_content.replace("\n\n", "<br>"))

def job():
    config = configparser.ConfigParser()
    config.read('config/config.ini')

    USERNAME = config.get('EZ_WEB', 'username')
    PASSWORD_ENCRYPTED = config.get('EZ_WEB', 'password')
    YUNMA_TOKEN = config.get('jfbym', 'Token')

    qiandao_task = AutoQiandao(USERNAME, PASSWORD_ENCRYPTED, YUNMA_TOKEN)
    qiandao_task.run()

if __name__ == "__main__":
    # 初始化调度器，强制使用北京时间（UTC+8）
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')


    @scheduler.scheduled_job('cron', hour=9, minute=0, timezone='Asia/Shanghai')  # 显式指定时区
    def scheduled_job():
        try:
            job()
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
            notifier.get_dingding("定时任务执行失败", f"任务执行失败: {e}")
            notifier.get_mail("定时任务执行失败", f"任务执行失败: {e}")


    # 获取当前北京时间（避免服务器时区影响）
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

    logger.info(f"ez - web 脚本初始化成功，任务已设定，将在每天北京时间 09:00 执行。当前时间: {beijing_time}")
    notifier.get_dingding("脚本初始化成功",
                          f"ez - web 脚本初始化成功 <br/> 任务已设定，将在每天北京时间 09:00 执行。当前时间: {beijing_time}")
    notifier.get_mail("ez - web 脚本初始化成功",
                      f"ez - web 脚本初始化成功 <br/> 任务已设定，将在每天北京时间 09:00 执行。当前时间: {beijing_time}")

    # 首次启动立即执行
    logger.info("脚本首次启动，立即执行一次签到任务...")
    try:
        job()
    except Exception as e:
        logger.error(f"首次任务执行失败: {e}")
        notifier.get_dingding("首次任务执行失败", f"首次任务执行失败: {e}")
        notifier.get_mail("首次任务执行失败", f"首次任务执行失败: {e}")
    logger.info("首次签到任务执行完成，开始等待定时任务...")

    # 启动调度器，并处理退出信号
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("定时任务已停止")
        notifier.get_dingding("定时任务已停止", "定时任务已停止")
        notifier.get_mail("定时任务已停止", "定时任务已停止")
