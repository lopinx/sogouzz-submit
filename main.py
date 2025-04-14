# -*- coding: utf-8 -*-
__author__ = "https://github.com/lopinx"
# =================================================================================================
# 添加调试模式启动： 
# "Google Chrome": 必须先结束已存在的Chrome浏览器进程后再开启， chrome.exe --remote-debugging-port=39222
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
# "Microsoft Edge": 必须先结束已存在的Edge浏览器进程后再开启， msedge.exe --remote-debugging-port=39333
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
import random
import re
from pathlib import Path
from urllib.error import URLError,HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import websockets
import ddddocr
import pyjson5 as json
from playwright.async_api import async_playwright

OCR = ddddocr.DdddOcr(show_ad=False)
WorkDIR = Path(__file__).resolve().parent
# 读取配置文件dev.json,config.json分别为开发和生产环境
_env = WorkDIR / ('dev.json' if (WorkDIR / 'dev.json').exists() else 'config.json')
config = json.load(_env.open('r', encoding='utf-8'))


async def cdplink(start=1024, end=49151) -> str | None:
    """获取本地webSocketDebuggerUrl"""
    for port in range(start, end + 1):
        try:
            with urlopen(f"http://localhost:{port}/json/version", timeout=3) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read())
                    if 'webSocketDebuggerUrl' in data:
                        print(f"✅ 找到可用的CDP端口: {port}")
                        return data['webSocketDebuggerUrl']
        except (URLError, HTTPError):
            continue
    return None

async def captcha(page: str, captcha_selector: str, input_selector: str, OCR: any) -> None:
    """处理验证码的通用函数"""
    if await page.locator(captcha_selector).is_visible():
        await page.wait_for_timeout(1000)
        captcha_obj = page.locator(captcha_selector)
        captcha_code = OCR.classification(await captcha_obj.screenshot(type='png'))
        await page.fill(input_selector, captcha_code)
        await page.wait_for_timeout(1000)
    else:
        print("❌ 验证码元素未找到，可能是页面加载不完全或验证码元素不存在。")

async def login(page: str, site: dict, OCR: any) -> bool:
    """处理登录逻辑"""
    _login = False
    if await page.locator('//a[@class="logout"]').is_visible(timeout=180000):
        _login = True
        print(f"✅ 【无需登录】，因为已经登录过了！")
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
                # print(f"❌ 验证码处理失败：{str(e)}")
                continue
            await page.wait_for_timeout(1000)
            await page.click('//a[@class="btn-login"]')
            await page.wait_for_timeout(1000)
            if await page.locator('//a[@class="logout"]').is_visible(timeout=180000):
                _login = True
                print(f"✅ 【第 {attempt+1} 次】登录成功！")
                break
            else:
                await page.click('//a[@class="code_img"]')
                await page.wait_for_timeout(1000)
                continue
    return _login

async def urls(sitemap: str) -> list:
    """从sitemap中获取URL列表"""
    _links, urls = "", []
    # print(f"⏳ 正在获取sitemap: {sitemap}")
    for attempt in range(config.get('captcha', 3)):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'}
            request = Request(sitemap, headers=headers)
            with urlopen(request) as resp:
                _links = resp.read().decode('utf-8')
            # print(f'✅ 【第 {attempt+1} 次】，获取Sitemap成功!')
            break
        except URLError as e:
            print(f"❌ 无法获取Sitemap: {str(e)}")
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
    # print(f'🔍 共发现 {len(urls)} 个链接')
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
                # print(f"❌ 点击元素失败：{str(e)}")
                await page.wait_for_timeout(1000)
                continue
    if not _box:
        print(f"❌ 无法找到元素，可能是页面加载不完全或元素不存在。")
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
            # print(f"❌ 验证码处理失败：{str(e)}")
            continue
        await page.wait_for_timeout(1000)
        await page.click('//a[@class="btn_add"]')
        await page.wait_for_timeout(1000)
        if await page.locator('//a[@class="btn_pop"]').is_visible(timeout=180000):
            await page.click('//a[@class="btn_pop"]')
            await page.wait_for_timeout(1000)
            _submit = True
            print(f"✅ 【第 {_index + 1} 批 - 第 {attempt+1} 次】，推送 {len(_batch)} 条URL 成功！")
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
            print("❌ 未能从提供的源获取URL")
            return False
        
        _cps = []
        try:
            with open(WorkDIR / f'{urlparse(site['sitemap']).netloc}.log', 'r') as f:
                lines = f.read().splitlines()
                _cps = [int(line.strip()) for line in lines if line.strip().isdigit()]
        except FileNotFoundError:
            print("⚠️ 日志文件不存在，将重新处理所有URL")

        urls_list = [url for idx, url in enumerate(urls_list) if idx not in _cps]
        if not urls_list:
            print("❌ 所有URL均已处理，退出程序")
            return False
        print(f"🔍 共有 {len(urls_list)} 个URL待处理")
    except URLError as e:
        print(f"❌ 无法获取: {str(e)}")
        return False
    
    try:
        async with async_playwright() as playwright:
            # 浏览器的参数
            _UserAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
            _bargs = [
                '--no-sandbox', # 禁用沙盒
                '--incognito', # 无痕模式
                '--no-first-run',   # 禁用首次运行
                '--disable-enterprise-policy-fetching', # 禁用企业策略获取
                '--disable-hsts-preload',   # 禁用HSTS预加载
                '--ignore-certificate-errors',  # 禁用证书错误
                '--disable-logging',    # 禁用日志
                '--disable-extensions', # 禁用扩展
                '--disable-popup-blocking', # 禁用弹出框拦截
                # '--disable-notifications',  # 禁用通知
                '--disable-translate',  # 禁用翻译
                '--disable-blink-features=AutomationControlled',    # 禁用自动化控制
                '--disable-infobars',   # 禁用信息栏
                '--disable-dev-shm-usage',  # 禁用共享内存
                '--disable-background-networking',  # 禁用后台网络
                '--disable-default-apps',   # 禁用默认应用
                '--disable-sync',   # 禁用同步
                '--disable-web-security',   # 禁用WebRTC安全
                '--mixed-content=always-allow', # 允许运行不安全内容（不显示任何警告，运行所有）
                '--disable-features=IsolateOrigins',    # 禁用隔离源
                '--disable-site-isolation-trials',  # 禁用网站隔离实验功能
                '--disable-software-rasterizer',    # 禁用软件渲染器
                '--mute-audio', # 禁用音频
                '--disable-features=WebRtcHideLocalIpsWithMdns',  # 保留WebRTC功能但隐藏本地 IP
                '--disable-crash-reporter', # 禁用崩溃报告
                # '--disable-javascript',   # 禁用javascript
                f'--user-agent={_UserAgent}',
                '--window-size=1920,1080'
            ]
                        # 创建浏览器上下文并配置指纹,反反爬

                    # Define common context parameters
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
                "user_agent": _UserAgent                        # 用户代理
            }
            
            # 筛选可用WS链接
            ws_list = []
            for _wsl in config.get("cdpserver"):
                try:
                    async with websockets.connect(_wsl, timeout=2):
                        ws_list.append(_wsl)
                except:
                    pass
            if not ws_list and (_cdplink := await cdplink()):
                ws_list.append(_cdplink)
            
            if ws_list:
                _ws = random.choice(ws_list)

            # 连接到浏览器
            if _ws and config.get('headless', False):
                try:
                    browser = await playwright.chromium.connect_over_cdp(
                        _ws, 
                        timeout=180000,
                        slow_mo=500,
                        headers={'User-Agent': _UserAgent}
                    )
                except Exception as e:
                    print(f"❌ 无法连接到CDP服务器: {str(e)}")
                    return False
                
                try:
                    context = await browser.contexts[0]
                    page = context.pages[0] if context.pages else await context.new_page()
                except (IndexError, Exception) as e:
                    if any(_ in _ws for _ in ('chrome', 'msedge')):
                        context = await browser.new_context(**_cargs)
                    else:
                        context = await browser.new_context()
                    page = await context.new_page()
            else:
                browser = await playwright.chromium.launch(
                    headless=config.get('headless', False),
                    channel=config.get('engine', 'msedge'),
                    slow_mo=500,  # 增加每个操作时间到500毫秒
                    timeout=180000,  # 增加启动超时时间到30分钟
                    # proxy={"server": "socks5://127.0.0.1:1080", "username": "user", "password": "pass"}, #设置代理服务器（需包含 server、username、password）
                    # env={"HTTP_PROXY": "http://proxy:8080"}, # 设置环境变量设置
                    args=_bargs.extend(['--disable-gpu', '--disable-webgl', '--disable-features=WebGL']), # 加载浏览器参数
                )
                
                try:
                    context = await browser.new_context(**_cargs)
                    page = await context.new_page()
                    await page.add_init_script("""
                        (function() {
                            const getParameter = WebGLRenderingContext.prototype.getParameter;
                            WebGLRenderingContext.prototype.getParameter = function(p) {
                                const appleWebGLInfo = {
                                    37445: 'Apple Inc.',                        // 厂商（Vendor）
                                    37446: 'Apple A16 GPU',                     // 渲染器（Renderer，M2芯片）,M3芯片: 'Apple A16 GPU',M1芯片: 'Apple A14 GPU'
                                    37447: 'WebGL 2.1 (OpenGL ES 3.2)'          // 版本（Version）
                                };
                                return appleWebGLInfo[p] ?? getParameter(p);    // 未覆盖的参数返回原生值
                            };
                            HTMLCanvasElement.prototype.toBlob = function() {
                                return function() { return new Blob(); };       // 覆盖toBlob方法，返回空Blob
                            };
                        })();
                    """)
                except Exception as e:
                    print(f"❌ 无法创建浏览器上下文: {str(e)}")
                    return False
            
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
                    print(f"🔍 正在处理第 {_index + 1} 批，包含 {len(_batch)} 个URL")
                    for _ in range(config.get('captcha', 3)):
                        try:
                            print(f"🎯 第 {_+1} 次尝试提交...")
                            if await submit(page, _batch, site, OCR, _index):
                                _bTag = True
                                batch.add(_index)
                                print(f"✅ 第 {_index + 1} 批处理成功，当前完成 {len(batch)}/{batches} 批")
                                # 将已完成批次的URL追加保存到日志文件
                                with open(WorkDIR / f'{urlparse(site['sitemap']).netloc}.log', 'a+') as f:
                                    for url in _batch:
                                        f.write(f"{url}\n")
                                break
                            await page.wait_for_timeout(1000)
                        except Exception as e:
                            # print(f"❌ 提交出错：{str(e)}")
                            await page.wait_for_timeout(1000)
                            continue 
                    if not _bTag:
                        print(f"⚠️ 第 {_index + 1} 批所有尝试均失败，将在下次循环重试")
                if len(batch) < batches:
                    print(f"⏳ 批次处理未完成：{len(batch)}/{batches}，准备开始新一轮重试...")

            return True
    except Exception as e:
        print(f"❌ 发生错误：{str(e)}")
        return False
    finally:
        try:
            if 'page' in locals() and page:
                await page.close()
                print("✅ 页面已关闭")
            if 'context' in locals() and context:
                await context.close()
                print("✅ 上下文已关闭")
            if 'browser' in locals() and browser and browser.is_connected():
                print("✅ 浏览器已关闭")
                await browser.close()
        except Exception as e:
            print(f"⚠️ 清理资源时出错：{str(e)}")


if __name__ == "__main__":
    while True:
        for site in config.get("websites"):
            if not site or not isinstance(site, dict):
                continue
            print(asyncio.run(main(site)))