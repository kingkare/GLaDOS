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

def translate_message(msg):
    """将 GLaDOS 返回的英文状态翻译为中文"""
    msg_str = str(msg)
    if "Today's observation logged" in msg_str or "Checkin OK" in msg_str:
        return "今日签到成功，已记录积分！"
    elif "Checkin repeat" in msg_str or "already" in msg_str.lower():
        return "今日已完成签到，请明天再来！"
    elif "Please try again" in msg_str:
        return "请求频繁，请稍后再试。"
    elif "Not Logged In" in msg_str or "cookie" in msg_str.lower():
        return "Cookie 已失效，请重新获取并更新 Secrets。"
    else:
        return msg_str  # 未知的英文直接原样返回

def get_user_status(domain, headers):
    """查询当前剩余会员天数并计算到期时间（北京时间）"""
    status_url = f"https://{domain}/api/user/status"
    try:
        res = requests.get(status_url, headers=headers, timeout=10)
        data = res.json()
        if data.get("code") == 0:
            left_days_raw = data.get("data", {}).get("leftDays")
            if left_days_raw is not None:
                left_days = float(left_days_raw)
                days_int = int(left_days)
                
                # 设置北京时间时区 (UTC+8)
                tz_utc8 = timezone(timedelta(hours=8))
                now_beijing = datetime.now(tz_utc8)
                
                # 计算精确到期时间
                expire_date = now_beijing + timedelta(days=left_days)
                expire_str = expire_date.strftime("%Y-%m-%d %H:%M")
                
                return f"{expire_str} (共 {days_int} 天)"
    except Exception as e:
        print(f"获取状态失败: {e}")
    return "未知"

def glados_checkin():
    if not cookie:
        send_tg_message("❌ <b>GLaDOS 签到失败</b>\n\n原因: 未配置 GLADOS_COOKIE 环境变量")
        return

    domains = ["glados.rocks", "glados.network", "glados.cloud", "glados.one"]
    checkin_success = False
    raw_message = ""
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
                    raw_message = data.get("message", "无返回信息")
                    # 签到成功或重复签到后，获取剩余天数和计算到期时间
                    expire_info = get_user_status(domain, headers)
                    break
            except Exception:
                continue
        if checkin_success:
            break

    if checkin_success:
        # 进行中文翻译
        cn_message = translate_message(raw_message)
        
        msg_text = (
            f"✅ <b>GLaDOS 签到通知</b>\n\n"
            f"<b>状态信息:</b> {cn_message}\n"
            f"<b>会员到期时间:</b> <code>{expire_info}</code>"
        )
    else:
        msg_text = "❌ <b>GLaDOS 签到失败</b>\n\n请求超时或 Cookie 已失效，请检查。"

    print(msg_text)
    send_tg_message(msg_text)

if __name__ == "__main__":
    glados_checkin()
