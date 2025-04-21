<p align="center">
  <a href="https://github.com/lopinx/sogouzz-submit" target="_blank"><img src="https://cdn.lightpanda.io/assets/images/logo/lpd-logo.png" alt="Logo" height=170></a>
</p>

<h1 align="center">搜狗站长链接自动化提交</h1>

<p align="center"><a href="https://lightpanda.io/">Sogou AutoLink Submission Tool</a></p>

<div align="center">

[![SogouzzSubmit](https://img.shields.io/github/stars/lopinx/sogouzz-submit)](https://github.com/lopinx/sogouzz-submit)
[![Playwright](https://img.shields.io/github/stars/lightpanda-io/browser)](https://github.com/microsoft/playwright-python)
[![Ddddocr](https://img.shields.io/github/stars/sml2h3/ddddocr)](https://github.com/sml2h3/ddddocr)

</div>


``` python
# -*- coding: utf-8 -*-
__author__ = "https://github.com/lopinx"
# =================================================================================================
# 添加调试模式启动： 
# "Google Chrome": 必须先结束已存在的Chrome浏览器进程后再开启， 
# Windows：chrome.exe --headless --remote-debugging-port=39222
# Linux/MacOS:  chrome --headless --remote-debugging-port=39222
# chrome --headless --remote-debugging-port=0 # 随机分配一个可用端口
#  启动 -> 访问"http://localhost:39222/json/version" -> 获取以下JSON数据中的"webSocketDebuggerUrl"
# "Microsoft Edge": 必须先结束已存在的Edge浏览器进程后再开启
# Windows：msedge.exe --headless --remote-debugging-port=39333
# Linux/MacOS:  msedge --headless --remote-debugging-port=39333
# msedge --headless --remote-debugging-port=0 # 随机分配一个可用端口
#  启动 -> 访问"http://localhost:39333/json/version" -> 获取以下JSON数据中的"webSocketDebuggerUrl"
# https://learn.microsoft.com/zh-cn/microsoft-edge/devtools-protocol-chromium/
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
# 2. 升级setuptools：uv pip install setuptools -U
# 3. 安装依赖：uv sync
# 4. 安装驱动：uv run python -m playwright install chromium
# 5. 运行程序：uv run python main.py
# =================================================================================================
```

### 依赖环境

``` bash
SAST v0.1.0
├── ddddocr v1.5.6
│   ├── numpy v2.2.4
│   ├── onnxruntime v1.21.0
│   │   ├── coloredlogs v15.0.1
│   │   │   └── humanfriendly v10.0
│   │   │       └── pyreadline3 v3.5.4
│   │   ├── flatbuffers v25.2.10
│   │   ├── numpy v2.2.4
│   │   ├── packaging v24.2
│   │   ├── protobuf v6.30.2
│   │   └── sympy v1.13.3
│   │       └── mpmath v1.3.0
│   ├── opencv-python-headless v4.11.0.86
│   │   └── numpy v2.2.4
│   └── pillow v11.1.0
└── playwright v1.51.0
    ├── greenlet v3.1.1
    └── pyee v12.1.1
        └── typing-extensions v4.13.1
```

### 配置文档：

``` json
{
    "websites": [
        {
            "username": "lopins",
            "password": "lk=Ls:+8>)?!ap/D",
            "sitemap": "https://bug.wenyix.cn/sitemap.xml"
        },
        {
            "username": "lopins",
            "password": "lk=Ls:+8>)?!ap/D",
            "sitemap": "https://www.kundabc.com/sitemap.xml"  
        }
    ],
    "backend": "https://zhanzhang.sogou.com/",
    "captcha": 10,
    "cdpserver": "wss://cloud.lightpanda.io/ws?token=5341furiqax9ltwz0bp2ecogvsnykmdh687j7okg2fnq1fsat8qk7x31gog98kps",
    "readme": "配置文件简洁易懂！captcha为验证码最大尝试次数，headless为true时是CDP服务器模式，headless为false时是launch实例模式！",
}
```

### CDP服务器：

- [lightpanda-io/browser](https://github.com/lightpanda-io/browser)

- [browserless/browserless](https://github.com/browserless/browserless)

### LICENSE

[MIT](LICENSE)