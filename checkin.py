import os
import requests
import json

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

def get_left_days(domain, headers):
    """查询当前剩余会员天数"""
    status_url = f"https://{domain}/api/user/status"
    try:
        res = requests.get(status_url, headers=headers, timeout=10)
        data = res.json()
        if data.get("code") == 0:
            left_days = data.get("data", {}).get("leftDays")
            if left_days is not None:
                return str(left_days).split('.')[0]
    except Exception as e:
        print(f"获取剩余天数失败: {e}")
    return "未知"

def glados_checkin():
    if not cookie:
        send_tg_message("❌ <b>GLaDOS 签到失败</b>\n\n原因: 未配置 GLADOS_COOKIE 环境变量")
        return

    # 兼容备用域名列表，防止单一域名被墙或失效
    domains = ["glados.rocks", "glados.network", "glados.cloud", "glados.one"]
    
    checkin_success = False
    result_message = ""
    left_days = "未知"

    for domain in domains:
        checkin_url = f"https://{domain}/api/user/checkin"
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/console/checkin"
        }
        
        # 尝试不同的 token 匹配
        for token_str in ["glados.network", "glados.one", domain]:
            payload = {"token": token_str}
            try:
                response = requests.post(checkin_url, headers=headers, json=payload, timeout=15)
                data = response.json()
                
                if "code" in data:
                    checkin_success = True
                    result_message = data.get("message", "无返回文字")
                    # 签到交互成功后，获取剩余天数
                    left_days = get_left_days(domain, headers)
                    break
            except Exception:
                continue
        if checkin_success:
            break

    if checkin_success:
        msg_text = (
            f"✅ <b>GLaDOS 签到通知</b>\n\n"
            f"<b>状态信息:</b> <code>{result_message}</code>\n"
            f"<b>剩余会员天数:</b> <code>{left_days} 天</code>"
        )
    else:
        msg_text = "❌ <b>GLaDOS 签到失败</b>\n\n请求超时或 Cookie 已失效，请检查。"

    print(msg_text)
    send_tg_message(msg_text)

if __name__ == "__main__":
    glados_checkin()
