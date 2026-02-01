import asyncio
import json
import random
from datetime import datetime
from typing import Optional
import requests  # 只用于钉钉
from curl_cffi.requests import AsyncSession
from proxy import proxy_manager




# ================== 基础配置 ==================

BASE_URL = "https://ztmen.jussyun.com/cyy_gatewayapi/show/pub/v3"

# 钉钉机器人
webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=bdc3b8bd0e3ebdb39df90bf67acbbf405d04b60065db1dfe37c6c8e938f52221"
webhook_url2 = "https://oapi.dingtalk.com/robot/send?access_token=61cb96708c2543536319fff172477490cfc3cccb703fa73a0d168786928054f8"

# 轮询间隔
INTERVAL = 15

# 请求计数器（用于日志）
request_counters = {}
request_counters_lock = asyncio.Lock()

# User-Agent 列表（随机切换，使用最新版本）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
]



# ================== 数据结构 ==================

shows = {
    "a_platinum": {
        "show_id": "6931340104da960001241d03",
        "sessions": {
            "三日票": "693134024996310001245614",
        }
    },
    "a": {
        "show_id": "693133c84996310001244e59",
        "sessions": {
            "三日票": "693133c904da960001241609",
            "周五": "693133c904da9600012415de",
            "周六": "693133c904da9600012415f4",
            "周日": "693133c904da9600012415bd",
        }
    },
    "b": {
        "show_id": "693132f64996310001244995",
        "sessions": {
            "三日票": "693132f74996310001244a25",
            "周五": "693132f749963100012449d9",
            "周六": "693132f74996310001244a13",
            "周日": "693132f74996310001244a25",
        }
    },
    "h": {
        "show_id": "6931529204da960001255be6",
        "sessions": {
            "三日票": "69315294499631000125956e",
            "周五": "69315294499631000125957e",
            "周六": "693152944996310001259557",
            "周日": "693152944996310001259593",
        }
    },
    "k": {
        "show_id": "693152ad04da960001255d56",
        "sessions": {
            "三日票": "693152ae04da960001255dd3",
            "周五": "693152ae04da960001255de9",
            "周六": "693152ae04da960001255d91",
            "周日": "693152ae04da960001255db8",
        }
    },
    "e": {
        "show_id": "693152c604da960001255ee5",
        "sessions": {
            "三日票": "693152c74996310001259825",
        }
    },
    "c": {
        "show_id": "693153534996310001259a9f",
        "sessions": {
            "三日票": "6931535304da960001256187",
        }
    }
}


# ================== URL 构造 ==================

def dynamic_url(show_id, session_id):
    return (
        f"{BASE_URL}/show/{show_id}"
        f"/show_session/{session_id}"
        f"/seat_plans_dynamic_data"
        "?src=WEB&channelId=&terminalSrc=WEB&lang=en"
    )


def static_url(show_id, session_id):
    return (
        f"{BASE_URL}/show/{show_id}"
        f"/show_session/{session_id}"
        f"/seat_plans_static_data"
        "?src=WEB&channelId=&terminalSrc=WEB&lang=en"
    )


def get_random_headers(show_id):
    """生成随机浏览器请求头（每次请求都使用不同的User-Agent）"""
    user_agent = random.choice(USER_AGENTS)
    
    # 根据User-Agent判断平台
    if "Windows" in user_agent:
        platform = '"Windows"'
        sec_ch_ua = '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"'
    elif "Macintosh" in user_agent:
        platform = '"macOS"'
        sec_ch_ua = '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"'
    else:
        platform = '"Linux"'
        sec_ch_ua = '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"'
    
    return {
        "accept": "application/json, text/plain, */*",
        "access-token": "",
        "channel-id": "",
        "content-type": "application/json;charset=UTF-8",
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform,
        "terminal-src": "WEB",
        "user-agent": user_agent,
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://ztmen.jussyun.com",
    }


# ================== 钉钉 ==================

def send_dingdingbot(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"{msg}\n⏰ {timestamp}\n"

    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }

    headers = {"Content-Type": "application/json"}

    try:
        requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=5)
        requests.post(webhook_url2, data=json.dumps(payload), headers=headers, timeout=5)
        print("✓ 钉钉通知发送成功")
    except Exception as e:
        print("❌ 钉钉发送失败:", e)


# ================== 核心请求（dynamic + static） ==================

async def request_one_session(
    session: AsyncSession,
    ticket_type: str,
    show_id: str,
    session_id: str,
    proxy: Optional[str] = None
):
    # ---------- dynamic ----------
    request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 每次请求都使用随机的请求头
        headers = get_random_headers(show_id)
        
        # 构建请求参数
        request_kwargs = {
            "headers": headers,
            "timeout": 10
        }
        if proxy:
            # curl_cffi使用proxy参数，格式：http://username:password@host:port
            request_kwargs["proxy"] = proxy
        
        resp = await session.get(dynamic_url(show_id, session_id), **request_kwargs)
        
        if resp.status_code != 200:
            # 如果是403等错误，可能是代理问题
            if resp.status_code in [403, 429]:
                proxy_manager.mark_proxy_failed()
            print(f"⚠️ [{request_time}] 类型: {ticket_type} | 状态码: {resp.status_code}")
            return
        # 只有状态码为200时才解析JSON
        dynamic_json = resp.json()
        
        # 只有请求成功后才统计次数
        async with request_counters_lock:
            if ticket_type not in request_counters:
                request_counters[ticket_type] = 0
            request_counters[ticket_type] += 1
            cumulative_count = request_counters[ticket_type]
        
        print(f"🔍 [{request_time}] 类型: {ticket_type} | 累积请求: {cumulative_count}")
    except Exception as e:
        # 请求异常，可能是代理问题
        proxy_manager.mark_proxy_failed()
        print(f"❌ [{request_time}] 类型: {ticket_type} | 错误: {e}")
        return

    
    seat_plan_ids = [
        p["seatPlanId"]
        for p in dynamic_json.get("data", {}).get("seatPlans", [])
        if p.get("canBuyCount", 0) > 0
    ]

    if not seat_plan_ids:
        return

    # ---------- static ----------
    try:
        # 每次请求都使用随机的请求头
        headers = get_random_headers(show_id)
        
        # 构建请求参数
        request_kwargs = {
            "headers": headers,
            "timeout": 10
        }
        if proxy:
            # curl_cffi使用proxy参数，格式：http://username:password@host:port
            request_kwargs["proxy"] = proxy
        
        resp = await session.get(static_url(show_id, session_id), **request_kwargs)
        if resp.status_code != 200:
            # 如果是403等错误，可能是代理问题
            if resp.status_code in [403, 429]:
                proxy_manager.mark_proxy_failed()
            print(f"⚠️ static status {resp.status_code} for {ticket_type} {session_id}")
            return
        # 只有状态码为200时才解析JSON
        static_json = resp.json()
    except Exception as e:
        # 请求异常，可能是代理问题
        proxy_manager.mark_proxy_failed()
        print(f"❌ static error {ticket_type}: {e}")
        return

    static_map = {
        p["seatPlanId"]: p["seatPlanName"].split("/")[0].strip()
        for p in static_json.get("data", {}).get("seatPlans", [])
    }

    seat_names = [
        static_map.get(pid)
        for pid in seat_plan_ids
        if static_map.get(pid)
    ]

    if not seat_names:
        return

    msg = (
        f"票档: {ticket_type}\n"
        f"🎫 有票提醒\n"
        f"座位:\n" +
        "\n".join(f"- {name}" for name in seat_names)
    )

    send_dingdingbot(msg)


# ================== ticket_type 任务 ==================

async def monitor_ticket_type(ticket_type, info):
    show_id = info["show_id"]
    sessions = info["sessions"]

    async with AsyncSession(impersonate="chrome") as session:
        print(f"🚀 start monitor: {ticket_type}")

        while True:
            try:
                # 获取代理（每55秒自动切换）
                proxy = await proxy_manager.get_proxy()
                
                for session_id in sessions.values():
                    await request_one_session(
                        session,
                        ticket_type,
                        show_id,
                        session_id,
                        proxy
                    )
                    # 随机延迟，防限流（0.3-0.8秒）
                    await asyncio.sleep(random.uniform(0.3, 0.8))

                # 随机延迟，避免固定间隔（INTERVAL的80%-120%）
                sleep_time = random.uniform(INTERVAL * 0.8, INTERVAL * 1.2)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                print(f"❌ {ticket_type} error:", e)
                # 如果出错，标记代理失败
                proxy_manager.mark_proxy_failed()
                await asyncio.sleep(random.randint(5, INTERVAL))


# ================== 主入口 ==================

async def main():
    tasks = [
        asyncio.create_task(monitor_ticket_type(ticket_type, info))
        for ticket_type, info in shows.items()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
