<p align="center">
  <a href="https://github.com/lopinx/sogouzz-submit" target="_blank"><img src="https://cdn.lightpanda.io/assets/images/logo/lpd-logo.png" alt="Logo" height=170></a>
</p>

<h1 align="center">搜狗站长链接自动化提交</h1>

<p align="center"><a href="https://github.com/lopinx/sogouzz-submit">Sogou AutoLink Submission Tool</a></p>

<div align="center">

[![SogouzzSubmit](https://img.shields.io/github/stars/lopinx/sogouzz-submit)](https://github.com/lopinx/sogouzz-submit)
[![Playwright](https://img.shields.io/github/stars/lightpanda-io/browser)](https://github.com/microsoft/playwright-python)
[![Ddddocr](https://img.shields.io/github/stars/sml2h3/ddddocr)](https://github.com/sml2h3/ddddocr)

</div>

---

### 快速上手

- 1. 安装并启动 Lightpanda 服务或者本地开启Debugger模式（Win+R）： 

``` bash
curl -L -o lightpanda https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux \
&& sudo mv lightpanda /usr/local/bin/ \
&& sudo chmod a+x /usr/local/bin/lightpanda \
&& echo 'export LIGHTPANDA_DISABLE_TELEMETRY=true' | sudo tee -a /etc/profile && sudo sh -c 'source /etc/profile' \
&& nohup lightpanda serve --host 0.0.0.0 --port 9222 > /dev/null 2>&1 & exit
```

``` powershell
# Windows Desktop开启Chrome浏览器Debugger模式
chrome.exe --headless=new --remote-debugging-port=39222
# Windows Desktop开启Edge浏览器Debugger模式
msedge.exe --headless=new --remote-debugging-port=39333
# Linux Desktop开启Chrome浏览器Debugger模式
google-chrome --headless=new --remote-debugging-port=39222
# Linux Desktop开启Edge浏览器Debugger模式
microsoft-edge --headless=new --remote-debugging-port=39333
```

- 2. 安装依赖：`uv sync`

- 3. 运行程序：`uv run python main.py`

- 4. 打包EXE：`uv run pyinstaller main.spec`

### 项目版本

``` python
# -*- coding: utf-8 -*-
__author__ = "https://github.com/lopinx"
__version__ = "1.1.0"
# =====================================================================================================================
```

### 环境模块

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
    "cdpserver": ["wss://cloud.lightpanda.io/ws?token=5341furiqax9ltwz0bp2ecogvsnykmdh687j7okg2fnq1fsat8qk7x31gog98kps"],
    "readme": "配置文件简洁易懂！captcha为验证码最大尝试次数，cdpserver为CDP服务器地址",
}
```

### CDP服务器

- [lightpanda-io/browser](https://github.com/lightpanda-io/browser)

- [CDP服务器申请](https://lightpanda-io)

### 许可协议

[MIT](LICENSE)