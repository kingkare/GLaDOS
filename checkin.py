import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 从环境变量中读取配置信息
cookie = os.environ.get("GLADOS_COOKIE")
tg_token = os.environ.get("TG_BOT_TOKEN")
tg_chat_id = os.environ.get("TG_CHAT_ID")

def send_tg_message(text):
    """发送 Telegram 消息通知"""
    if not tg_token or not tg_chat_id:
        print("未配置 Telegram 机器人信息，跳过推送。")
        return
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": tg_chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"发送 Telegram 通知失败: {e}")

def translate_message(code, msg):
    """将 GLaDOS 返回的状态码与提示翻译为中文"""
    msg_str = str(msg).lower()
    
    # code == 1 或包含 repeat/already 表示重复签到
    if code == 1 or "repeat" in msg_str or "already" in msg_str:
        return "今日已完成签到，请明天再来！"
    elif code == 0:
        return "今日签到成功，已记录积分！"
    elif "not logged in" in msg_str or "cookie" in msg_str or "forbidden" in msg_str:
        return "Cookie 已失效或未登录，请重新获取并更新 Secrets。"
    else:
        return str(msg)

def get_user_status(domain, headers):
    """查询当前登录的账号与剩余会员天数，并计算到期日期（仅年月日）"""
    status_url = f"https://{domain}/api/user/status"
    email = "未知"
    expire_info = "未知"
    
    try:
        res = requests.get(status_url, headers=headers, timeout=10)
        data = res.json()
        if data.get("code") == 0:
            user_data = data.get("data", {})
            email = user_data.get("email", "未知")
            
            left_days_raw = user_data.get("leftDays")
            if left_days_raw is not None:
                left_days = float(left_days_raw)
                days_int = int(left_days)
                
                # 设置北京时间时区 (UTC+8)
                tz_utc8 = timezone(timedelta(hours=8))
                now_beijing = datetime.now(tz_utc8)
                
                # 计算到期日期（仅保留年月日 %Y-%m-%d）
                expire_date = now_beijing + timedelta(days=left_days)
                expire_str = expire_date.strftime("%Y-%m-%d")
                
                expire_info = f"{expire_str} (共 {days_int} 天)"
    except Exception as e:
        print(f"获取账号状态失败: {e}")
        
    return email, expire_info

def glados_checkin():
    if not cookie:
        send_tg_message("❌ <b>GLaDOS 签到失败</b>\n\n原因: 未配置 GLADOS_COOKIE 环境变量")
        return

    domains = ["glados.rocks", "glados.network", "glados.cloud", "glados.one"]
    checkin_success = False
    code = -1
    raw_message = ""
    email = "未知"
    expire_info = "未知"

    for domain in domains:
        checkin_url = f"https://{domain}/api/user/checkin"
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/console/checkin"
        }
        
        for token_str in ["glados.network", "glados.one", domain]:
            payload = {"token": token_str}
            try:
                response = requests.post(checkin_url, headers=headers, json=payload, timeout=15)
                data = response.json()
                
                if "code" in data:
                    checkin_success = True
                    code = data.get("code", -1)
                    raw_message = data.get("message", "无返回信息")
                    # 获取登录账号邮箱和到期日期
                    email, expire_info = get_user_status(domain, headers)
                    break
            except Exception:
                continue
        if checkin_success:
            break

    if checkin_success:
        # 结合状态码 code 和提示文字做中文翻译
        cn_message = translate_message(code, raw_message)
        
        msg_text = (
            f"✅ <b>GLaDOS 签到通知</b>\n\n"
            f"<b>登录账号:</b> <code>{email}</code>\n"
            f"<b>状态信息:</b> {cn_message}\n"
            f"<b>会员到期时间:</b> <code>{expire_info}</code>"
        )
    else:
        msg_text = "❌ <b>GLaDOS 签到失败</b>\n\n请求超时或 Cookie 已失效，请检查。"

    print(msg_text)
    send_tg_message(msg_text)

if __name__ == "__main__":
    glados_checkin()
