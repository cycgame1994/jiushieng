import asyncio
import aiohttp
import random
from typing import Optional, Dict
from datetime import datetime

# 代理IP获取接口
PROXY_API_URL = "https://share.proxy.qg.net/get?key=BCAA9684&distinct=true"

# 代理认证信息
PROXY_USERNAME = "BCAA9684"
PROXY_PASSWORD = "37235174D5F3"

# 代理切换间隔（秒）
PROXY_SWITCH_INTERVAL = 55

# 代理获取失败重试间隔（秒）
PROXY_RETRY_INTERVAL = 5


class ProxyManager:
    """代理管理器"""
    
    def __init__(self):
        self.current_proxy: Optional[str] = None
        self.proxy_lock = asyncio.Lock()
        self.last_switch_time = 0
        self.proxy_failed = False
        self.is_working_hours_callback = None  # 工作时间内检查回调
        
    async def get_proxy_from_api(self) -> Optional[str]:
        """从API获取代理IP"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_API_URL, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("code") == "SUCCESS" and data.get("data"):
                            proxy_data = data["data"][0]
                            server = proxy_data.get("server")
                            if server:
                                # 格式：http://username:password@server
                                proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{server}"
                                print(f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取代理成功: {server}")
                                return proxy_url
                    print(f"⚠️ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 代理API返回异常: status={resp.status}")
        except Exception as e:
            print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取代理失败: {e}")
        return None
    
    def set_working_hours_callback(self, callback):
        """设置工作时间内检查回调函数"""
        self.is_working_hours_callback = callback
    
    async def get_proxy(self, force_refresh: bool = False) -> Optional[str]:
        """获取当前代理，如果需要则刷新（只在工作时间内获取）"""
        # 如果不在工作时间内，返回None，不获取代理
        if self.is_working_hours_callback and not self.is_working_hours_callback():
            return None
        
        async with self.proxy_lock:
            current_time = asyncio.get_event_loop().time()
            
            # 如果代理失败或需要强制刷新，立即获取新代理
            if self.proxy_failed or force_refresh:
                # 再次检查是否在工作时间内
                if self.is_working_hours_callback and not self.is_working_hours_callback():
                    return None
                    
                self.current_proxy = await self.get_proxy_from_api()
                if self.current_proxy:
                    self.last_switch_time = current_time
                    self.proxy_failed = False
                else:
                    # 获取失败，等待3秒后重试（只在工作时间内）
                    if self.is_working_hours_callback and self.is_working_hours_callback():
                        await asyncio.sleep(PROXY_RETRY_INTERVAL)
                        return await self.get_proxy(force_refresh=True)
                return self.current_proxy
            
            # 检查是否需要切换代理（每55秒）
            if self.current_proxy is None or (current_time - self.last_switch_time) >= PROXY_SWITCH_INTERVAL:
                # 再次检查是否在工作时间内
                if self.is_working_hours_callback and not self.is_working_hours_callback():
                    return None
                    
                self.current_proxy = await self.get_proxy_from_api()
                if self.current_proxy:
                    self.last_switch_time = current_time
                    self.proxy_failed = False
                else:
                    # 获取失败，等待3秒后重试（只在工作时间内）
                    if self.is_working_hours_callback and self.is_working_hours_callback():
                        await asyncio.sleep(PROXY_RETRY_INTERVAL)
                        return await self.get_proxy(force_refresh=True)
            
            return self.current_proxy
    
    def mark_proxy_failed(self):
        """标记当前代理失败"""
        self.proxy_failed = True
        print(f"⚠️ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 代理请求失败，将在{PROXY_RETRY_INTERVAL}秒后重新获取")


# 全局代理管理器实例
proxy_manager = ProxyManager()
