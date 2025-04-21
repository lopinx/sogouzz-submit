# -*- coding: utf-8 -*-
__author__ = "https://github.com/lopinx"
# =================================================================================================
# 添加调试模式启动： 
# "Google Chrome": 必须先结束已存在的Chrome浏览器进程后再开启， 
# Windows：chrome.exe --headless --remote-debugging-port=39222
# Linux/MacOS:  chrome --headless --remote-debugging-port=39222
# chrome --headless --remote-debugging-port=0 # 随机分配一个可用端口
#  启动 -> 访问"http://localhost:39222/json/version" -> 获取以下JSON数据中的"webSocketDebuggerUrl"
"""
``` json
{
    "Browser": "Chrome/135.0.7049.85",
    "Protocol-Version": "1.3",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "V8-Version": "13.5.212.10",
    "WebKit-Version": "537.36 (@1e112499da812a1dde62101ed601dcb93024aaff)",
    "webSocketDebuggerUrl": "ws://localhost:39222/devtools/browser/6842b2f4-1219-44d9-836d-fc5fdf65a74b"
}
```
"""
# "Microsoft Edge": 必须先结束已存在的Edge浏览器进程后再开启
# Windows：msedge.exe --headless --remote-debugging-port=39333
# Linux/MacOS:  msedge --headless --remote-debugging-port=39333
# msedge --headless --remote-debugging-port=0 # 随机分配一个可用端口
#  启动 -> 访问"http://localhost:39333/json/version" -> 获取以下JSON数据中的"webSocketDebuggerUrl"
# https://learn.microsoft.com/zh-cn/microsoft-edge/devtools-protocol-chromium/
"""
``` json
{
    "Browser": "Chrome/135.0.7049.85",
    "Protocol-Version": "1.3",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "V8-Version": "13.5.212.10",
    "WebKit-Version": "537.36 (@1e112499da812a1dde62101ed601dcb93024aaff)",
    "webSocketDebuggerUrl": "ws://localhost:39333/devtools/browser/6842b2f4-1219-44d9-836d-fc5fdf65a74b"
}
```
"""
# =================================================================================================
# (项目新建)安装依赖：uv add playwright ddddocr pyjson5
# (项目重建)同步依赖：uv sync 
# =================================================================================================
# playwright 浏览器自动化框架
# 安装浏览器驱动Chromium, Firefox, WebKit，不添加参数则为全部
# uv python -m playwright install chromium
# playwright codegen  #开启录制
# 使用 launch：当需要直接控制浏览器生命周期（如自动化测试）时，优先使用 launch。
# playwright.chromium.launch(headless=False) # 直接启动新浏览器实例
# 使用 CDP 连接：当需要连接已有浏览器实例（如复用登录状态、远程调试）时，通过 connect_over_cdp 连接。
# playwright.chromium.connect_over_cdp("ws://localhost:9222") # 连接已运行浏览器实例
# browser = p.chromium.launch(channel="chrome"，headless=False)
# browser = p.chromium.launch(channel="msedge"，headless=False)
# browser = p.firefox.launch(headless=False)
# browser = p.webkit.launch(headless=False)
# =================================================================================================
# 运行前步骤：
# 1. 安装并启动 Lightpanda 服务(CentOS)：
"""
``` bash
sudo yum install -y libappindicator-gtk3 liberation-fonts \
&& curl -L -o lightpanda https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux \
&& sudo mv lightpanda /usr/local/bin/ \
&& sudo chmod a+x /usr/local/bin/lightpanda \
&& echo 'export LIGHTPANDA_DISABLE_TELEMETRY=true' | sudo tee -a /etc/profile && sudo sh -c 'source /etc/profile' \
&& nohup lightpanda serve --host 0.0.0.0 --port 9222 > /dev/null 2>&1 & exit
```
"""
# 2. 升级setuptools：uv pip install setuptools -U
# 3. 安装依赖：uv sync
# 4. 安装驱动：uv run python -m playwright install chromium
# 5. 运行程序：uv run python main.py
# =================================================================================================
import asyncio
import logging
import random
import re
from pathlib import Path
# import threading
from typing import List
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
# from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import ddddocr
import psutil
import pyjson5 as json
import websockets
from playwright.async_api import async_playwright


OCR = ddddocr.DdddOcr(show_ad=False)
WorkDIR = Path(__file__).resolve().parent
# 读取配置文件dev.json,config.json分别为开发和生产环境
_env = WorkDIR / ('dev.json' if (WorkDIR / 'dev.json').exists() else 'config.json')
config = json.load(_env.open('r', encoding='utf-8'))
# 日志记录配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - L%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def wslink() -> List[str]:
    """获取本地调试链接"""
    urls = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if name := proc.info['name'].lower():
            # 进程名称过滤（Chrome/Edge/Chromium）
            if not re.match(r'^(chrome|edge|msedge|chromium)(\.exe)?$', name, re.IGNORECASE) and len(name) > 1:
                continue
        try:
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            if '--remote-debugging-port=' not in cmdline:
                continue
            port_match = re.search(r'--remote-debugging-port=(\d+)', cmdline)
            if not port_match:
                continue
            port = int(port_match.group(1))
            if port == 0:
                for conn in proc.net_connections():
                    if conn.status == 'LISTEN' and 1024 <= (port := conn.laddr.port) <= 65535:
                        break
            try:
                req = Request(f"http://localhost:{port}/json/version", headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=1) as r:
                    if ws := json.loads(r.read().decode()).get('webSocketDebuggerUrl'):
                        urls.append(ws)
            except (URLError, HTTPError, ValueError, TimeoutError, TypeError):
                continue      
        except (psutil.Error, AttributeError, ValueError, KeyError):
            continue
    return list(set(urls))

async def captcha(page: str, captcha_selector: str, input_selector: str, OCR: any) -> None:
    """处理验证码的通用函数"""
    if await page.locator(captcha_selector).is_visible():
        await page.wait_for_timeout(1000)
        captcha_obj = page.locator(captcha_selector)
        captcha_code = OCR.classification(await captcha_obj.screenshot(type='png'))
        await page.fill(input_selector, captcha_code)
        await page.wait_for_timeout(1000)
    else:
        logging.warning("❌ 验证码元素未找到，可能是页面加载不完全或验证码元素不存在。")

async def login(page: str, site: dict, OCR: any) -> bool:
    """处理登录逻辑"""
    _login = False
    if await page.locator('//a[@class="logout"]').is_visible(timeout=180000):
        _login = True
        logging.info(f"✅ 【无需登录】，因为已经登录过了！")
    else:
        await page.wait_for_timeout(1000)
        await page.click('//a[@class="login"]')
        await page.wait_for_timeout(1000)
        await page.fill('//input[@type="text" and @placeholder="平台账号"]', site['username'])
        await page.fill('//input[@type="password" and @placeholder="登陆密码"]', site['password'])
        await page.wait_for_timeout(1000)
        for attempt in range(config.get('captcha', 3)):
            try:
                await captcha(
                    page, 
                    '//*[@class="code_img"]/img',
                    '//input[@type="text" and @placeholder="验证码"]',
                    OCR
                )
            except Exception as e:
                logging.error(f"❌ 验证码处理失败：{str(e)}")
                continue
            await page.wait_for_timeout(1000)
            await page.click('//a[@class="btn-login"]')
            await page.wait_for_timeout(1000)
            if await page.locator('//a[@class="logout"]').is_visible(timeout=180000):
                _login = True
                logging.info(f"✅ 【第 {attempt+1} 次】登录成功！")
                break
            else:
                await page.click('//a[@class="code_img"]')
                await page.wait_for_timeout(1000)
                continue
    return _login

async def urls(sitemap: str) -> list:
    """从sitemap中获取URL列表"""
    _links, urls = "", []
    for attempt in range(config.get('captcha', 3)):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'}
            request = Request(sitemap, headers=headers)
            with urlopen(request) as resp:
                _links = resp.read().decode('utf-8')
            break
        except URLError as e:
            logging.error(f"❌ 无法获取Sitemap: {str(e)}")
            continue

    if '<?xml' in _links[:100]:
        if '<urlset' in _links or '<sitemapindex' in _links:
            if '<sitemapindex' in _links:
                mapurls = re.findall(r'<loc>\s*(.*?)\s*</loc>', _links)
                urls = []
                for su in mapurls:
                    try:
                        with urlopen(su) as resp:
                            _sublinks = resp.read().decode('utf-8')
                        urls.extend(re.findall(r'<loc>\s*(.*?)\s*</loc>', _sublinks))
                    except URLError:
                        continue
            else:
                urls = re.findall(r'<loc>\s*(.*?)\s*</loc>', _links)
        elif '<rss' in _links or '<feed' in _links:
            urls = re.findall(r'<link>\s*(https?://.*?)\s*</link>', _links)
            if not urls:
                urls.extend(re.findall(r'<link[^>]+href="(https?://[^"]+)"', _links))
                urls.extend(re.findall(r'<link[^>]+rel="alternate"[^>]+href="(https?://[^"]+)"', _links))
    else:
        if '<!DOCTYPE html' in _links[:100] or '<html' in _links[:100]:
            _baseUrl = urlparse(sitemap).scheme + '://' + urlparse(sitemap).netloc
            urls = re.findall(r'<a\s+href=["\'](https?://[^"\']+)["\']', _links, re.IGNORECASE)
            # 补全相对链接并且过滤非本域名的链接
            urls = [urljoin(_baseUrl, url) if not urlparse(url).netloc else url for url in urls]
            urls = [url for url in urls if urlparse(url).netloc == urlparse(_baseUrl).netloc]
        else:
            urls = [url.strip() for url in _links.splitlines() if url.strip()]
    # 剔除首页链接
    urls = list(dict.fromkeys(url for url in urls if not url.endswith('/') and not urlparse(url).path == ''))
    return urls

async def submit(page: str, _batch: list, site: dict, OCR: any, _index: int) -> bool:
    """提交URL批次"""
    _submit, _box = False, False
    domain = urlparse(site['sitemap']).netloc
    for attempt in range(config.get('captcha', 3)):
        try:
            await page.click('//div[contains(@class,"website_box")]')
            _box = True
            break
        except Exception as e:
            if 'Page.click: Timeout' in str(e):
                await page.evaluate("""() => {
                    const hideElements = (selectors) => {
                        selectors.forEach(selector => {
                            const el = document.querySelector(selector);
                            if (el) el.style.display = 'none';
                        });
                    };
                    hideElements(['.mask_bg', '.pop_del_area']);
                }""")
                element = page.locator("//div[contains(@class,'website_box')]")
                await element.wait_for(state="visible", timeout=10000)
                await element.evaluate("elem => elem.click()")
                _box = True
                break
            else:
                logging.error(f"❌ 点击元素失败：{str(e)}")
                await page.wait_for_timeout(1000)
                continue
    if not _box:
        logging.error(f"❌ 无法找到元素，可能是页面加载不完全或元素不存在。")
        return False

    await page.wait_for_timeout(1000)
    await page.fill('//input[contains(@type,"text") and @class="search_input"]', domain)
    await page.wait_for_timeout(1000)
    await page.click(f"//li[contains(@class, 'select_item') and normalize-space()='{domain}']")
    await page.wait_for_timeout(1000)
    await page.fill('//div[@class="form-control"]//textarea', '\n'.join(_batch))
    await page.wait_for_timeout(1000)
    for attempt in range(config.get('captcha', 3)):
        try:
            await captcha(
                page,
                '//*[@class="form-control verification"]//img',
                '//*[@class="form-control verification"]//input[@type="text"]',
                OCR
            )
        except Exception as e:
            logging.error(f"❌ 验证码处理失败：{str(e)}")
            continue
        await page.wait_for_timeout(1000)
        await page.click('//a[@class="btn_add"]')
        await page.wait_for_timeout(1000)
        if await page.locator('//a[@class="btn_pop"]').is_visible(timeout=180000):
            await page.click('//a[@class="btn_pop"]')
            await page.wait_for_timeout(1000)
            _submit = True
            logging.info(f"✅ 【第 {_index + 1} 批 - 第 {attempt+1} 次】，推送 {len(_batch)} 条URL 成功！")
            break
        else:
            await page.click('//*[@class="form-control verification"]//img')
            await page.wait_for_timeout(1000)
            continue
    return _submit

async def main(site: dict) -> bool:
    # 读取日志并过滤已处理的URL
    try:
        urls_list = await urls(site['sitemap'])
        if not urls_list:
            logging.error("❌ 未能从提供的源获取URL")
            return False
        
        _cps = []
        try:
            with open(WorkDIR / f'{urlparse(site['sitemap']).netloc}.log', 'r') as f:
                lines = f.read().splitlines()
                _cps = [int(line.strip()) for line in lines if line.strip().isdigit()]
        except FileNotFoundError:
            logging.warning("⚠️ 日志文件不存在，将重新处理所有URL")

        urls_list = [url for idx, url in enumerate(urls_list) if idx not in _cps]
        if not urls_list:
            logging.error("❌ 所有URL均已处理，退出程序")
            return False
    except URLError as e:
        logging.error(f"❌ 无法获取: {str(e)}")
        return False
    try:
        async with async_playwright() as playwright:
            # 浏览器的参数
            _cargs = {
                "viewport": {"width": 1440, "height": 900},     # 设置浏览器窗口大小
                "screen": {"width": 1920, "height": 1080},      # 设置屏幕分辨率
                "ignore_https_errors": True,                    # 忽略https错误
                "java_script_enabled": True,                    # 启用JavaScript
                "locale": "zh-CN",                              # 设置语言环境
                "timezone_id": "Asia/Shanghai",                 # 设置时区
                # "geolocation": {"longitude": 116.40387, "latitude": 39.91435, "accuracy": 100},   # 设置地理位置
                "permissions": ["notifications"],               # 设置权限: 通知
                "bypass_csp": True,                             # 绕过 CSP（Content Security Policy）
                "accept_downloads": True,                       # 允许下载
                "user_agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
            }
            
            # 筛选可用WS链接
            ws_link = []
            if cdp := config.get("cdpserver"):
                for url in cdp:
                    try:
                        async with websockets.connect(url, open_timeout=5) as ws:
                            await ws.ping()
                            await ws.close()
                            ws_link.append(url)
                    except: 
                        continue
            else:
                ws_link.extend(await wslink())
            
            if ws_link:
                _ws = random.choice(ws_link)
            else:
                logging.error("❌ 未找到可用CDP服务器，将使用本地浏览器")
                return False

            # 连接到浏览器        
            try:
                browser = await playwright.chromium.connect_over_cdp(
                    _ws, 
                    timeout=180000,
                    slow_mo=500
                )
            except Exception as e:
                logging.error(f"❌ 无法连接到CDP服务器: {str(e)}")
                return False
            
            try:
                context = browser.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()
            except (IndexError, TypeError, Exception) as e:
                context = await browser.new_context(**_cargs)
                page = await context.new_page()
            
            # 测试反反爬虫
            await page.goto('https://res.cdn.issem.cn', wait_until='networkidle', timeout=180000)
            
            # 登录站长平台
            await page.goto(config.get("backend"), wait_until='networkidle', timeout=180000)
            await page.wait_for_timeout(1000)
            if not await login(page, site, OCR):
                return False

            await page.goto(f"{config.get('backend')}index.php/sitelink/index", wait_until='networkidle', timeout=180000)
            
            # 分批处理链接
            # _size为每批次数量，batch为已完成批次，batches为总批次
            # _bacth为当前批次，_bTag为当前批次是否成功
            _size = 20
            batch, batches = set(), (len(urls_list) + _size - 1) // _size
            while len(batch) < batches:
                for _index, _start in enumerate(range(0, len(urls_list), _size)):
                    if _index in batch:
                        continue
                    _batch, _bTag = urls_list[_start:_start + _size], False     
                    for _ in range(config.get('captcha', 3)):
                        try:
                            if await submit(page, _batch, site, OCR, _index):
                                _bTag = True
                                batch.add(_index)
                                with open(WorkDIR / f'{urlparse(site['sitemap']).netloc}.log', 'a+') as f:
                                    for url in _batch:
                                        f.write(f"{url}\n")
                                break
                            await page.wait_for_timeout(1000)
                        except Exception as e:
                            await page.wait_for_timeout(1000)
                            continue 
                    if not _bTag:
                        logging.warning(f"⚠️ 第 {_index + 1} 批所有尝试均失败，将在下次循环重试")
                if len(batch) < batches:
                    logging.warning(f"⏳ 批次处理未完成：{len(batch)}/{batches}，准备开始新一轮重试...")
            return True
    except Exception as e:
        logging.error(f"❌ 发生错误：{str(e)}")
        return False
    finally:
        try:
            if 'page' in locals() and page:
                await page.close()
            if 'context' in locals() and context:
                await context.close()
            if 'browser' in locals() and browser and browser.is_connected():
                await browser.close()
        except Exception as e:
            logging.error(f"⚠️ 清理资源时出错：{str(e)}")


if __name__ == "__main__":
    while True:
        for site in config.get("websites"):
            if not site or not isinstance(site, dict):
                continue
            logging.info(asyncio.run(main(site)))