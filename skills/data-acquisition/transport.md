---
name: data-acquisition/transport
description: 火车余票/时刻表（12306公开接口）、航班查询（航旅纵横/FlightAware）、快递物流追踪（快递100）。出行规划与物流监控。
---

# 交通与物流数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| 火车余票/时刻表 | 12306 | 公开API（无需登录） |
| 航班实时状态 | 航旅纵横 | playwright headless |
| 航班查询 | FlightAware | playwright headless |
| 快递追踪 | 快递100 | API（免费注册） |
| 快递追踪 | 快递鸟 | API（免费注册） |
| 实时路况 | 高德地图API | geo.md中已有 |

## 12306 火车查询（公开接口，无需登录）

```python
import urllib.request, json
from urllib.parse import quote
from datetime import datetime

# 站名代码映射（常用城市）
STATION_CODES = {
    "北京": "BJP", "北京南": "VNP", "北京西": "BXP", "北京东": "BOP",
    "上海": "SHH", "上海虹桥": "AOH", "上海南": "SNH",
    "广州": "GZQ", "广州南": "IZQ",
    "深圳": "SZQ", "深圳北": "IOQ",
    "杭州": "HZH", "杭州东": "HGH",
    "南京": "NJH", "南京南": "NKH",
    "成都": "CDW", "成都东": "ICW",
    "武汉": "WHN", "西安": "XAY", "西安北": "EAY",
    "重庆": "CQW", "重庆北": "CUW",
    "天津": "TJP", "天津南": "TIP",
    "郑州": "ZZF", "郑州东": "ZAF",
    "济南": "JNK", "济南西": "JPK",
    "长沙": "CSQ", "长沙南": "CWQ",
    "沈阳": "SYT", "沈阳北": "SNT",
    "哈尔滨": "HBB", "哈尔滨西": "HEH",
    "长春": "CCT", "大连": "DLT", "大连北": "DQT",
    "青岛": "QDK", "青岛北": "QIK",
    "厦门": "XMS", "厦门北": "XBQ",
    "福州": "FZS", "福州南": "FYS",
    "昆明": "KMM", "昆明南": "KOM",
    "贵阳": "GYW", "贵阳北": "GIW",
    "南宁": "NNZ", "南宁东": "NNZ",
    "合肥": "HFF", "合肥南": "HGF",
    "南昌": "NCG", "南昌西": "NHG",
    "石家庄": "SJP", "太原": "TYV", "太原南": "TTV",
    "兰州": "LZJ", "兰州西": "LXJ",
    "乌鲁木齐": "WLJ",
}

def query_trains(from_city, to_city, date=None):
    """
    查询两城市间火车班次和余票
    注意：12306接口需要JS动态token，必须用playwright真实浏览器
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    from_code = STATION_CODES.get(from_city, from_city)
    to_code = STATION_CODES.get(to_city, to_city)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        # 先访问首页触发 cookie/token 初始化
        page.goto("https://kyfw.12306.cn/otn/leftTicket/init", timeout=20000)
        page.wait_for_timeout(2000)
        # 直接调用接口（此时已有合法 cookie）
        url = (f"https://kyfw.12306.cn/otn/leftTicket/query"
               f"?leftTicketDTO.train_date={date}"
               f"&leftTicketDTO.from_station={from_code}"
               f"&leftTicketDTO.to_station={to_code}"
               f"&purpose_codes=ADULT")
        resp = page.evaluate(f"""async () => {{
            const r = await fetch('{url}', {{
                headers: {{
                    'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
                    'X-Requested-With': 'XMLHttpRequest',
                }}
            }});
            return await r.json();
        }}""")
        browser.close()

    trains = []
    for item in (resp or {}).get("data", {}).get("result", []):
            parts = item.split("|")
            if len(parts) < 32:
                continue
            trains.append({
                "train_no": parts[3],
                "from_station": parts[6],
                "to_station": parts[7],
                "depart_time": parts[8],
                "arrive_time": parts[9],
                "duration": parts[10],
                "business_seat": parts[32] or "-",  # 商务座
                "first_class": parts[31] or "-",    # 一等座
                "second_class": parts[30] or "-",   # 二等座
                "sleeper_hard": parts[28] or "-",   # 硬卧
                "sleeper_soft": parts[23] or "-",   # 软卧
                "hard_seat": parts[29] or "-",      # 硬座
                "no_seat": parts[26] or "-",        # 无座
            })
    return trains

def filter_trains(trains, train_type=None, has_seat=True):
    """筛选车次"""
    result = trains
    if train_type:
        # G=高铁, D=动车, K=快车, T=特快, Z=直达
        result = [t for t in result if t["train_no"].startswith(train_type)]
    if has_seat:
        result = [t for t in result if any(
            v not in ["-", "无", "0", ""] for v in
            [t["second_class"], t["first_class"], t["hard_seat"], t["sleeper_hard"]]
        )]
    return result

# 使用示例
trains = query_trains("北京南", "上海虹桥", "2025-06-01")
g_trains = filter_trains(trains, train_type="G")
for t in g_trains[:5]:
    print(f"{t['train_no']} {t['depart_time']}→{t['arrive_time']} ({t['duration']}) "
          f"二等:{t['second_class']} 一等:{t['first_class']}")
```

## 航班查询（playwright）

```python
from playwright.sync_api import sync_playwright

def query_flights_variflight(from_city, to_city, date):
    """航班查询 - 飞常准（variflight.com）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        url = f"https://www.variflight.com/flight/{from_city}-{to_city}.html?AE71649A58c45=1&date={date}"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)

        flights = page.evaluate("""() => {
            const rows = document.querySelectorAll('.flight-list .flight-item, .flt-list .flt-item');
            return [...rows].slice(0, 30).map(row => ({
                flight_no: row.querySelector('.flt-no, .flight-no')?.innerText?.trim() || '',
                airline: row.querySelector('.airline-name, .airline')?.innerText?.trim() || '',
                depart_time: row.querySelector('.depart-time, .dep-time')?.innerText?.trim() || '',
                arrive_time: row.querySelector('.arrive-time, .arr-time')?.innerText?.trim() || '',
                depart_airport: row.querySelector('.depart-airport, .dep-airport')?.innerText?.trim() || '',
                arrive_airport: row.querySelector('.arrive-airport, .arr-airport')?.innerText?.trim() || '',
                status: row.querySelector('.flight-status, .status')?.innerText?.trim() || '',
                punctuality: row.querySelector('.punctuality, .on-time')?.innerText?.trim() || '',
            }));
        }""")
        browser.close()
        return [f for f in flights if f["flight_no"]]

def get_flight_status(flight_no, date=None):
    """查询单个航班实时状态"""
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://www.variflight.com/flight/no/{flight_no}.html?date={date}"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)
        status = page.evaluate("""() => ({
            flight_no: document.querySelector('.flight-no')?.innerText?.trim() || '',
            status: document.querySelector('.flight-status')?.innerText?.trim() || '',
            depart_time: document.querySelector('.dep-time')?.innerText?.trim() || '',
            arrive_time: document.querySelector('.arr-time')?.innerText?.trim() || '',
            depart_airport: document.querySelector('.dep-airport')?.innerText?.trim() || '',
            arrive_airport: document.querySelector('.arr-airport')?.innerText?.trim() || '',
            delay_reason: document.querySelector('.delay-reason')?.innerText?.trim() || '',
        })""")
        browser.close()
        return status
```

## 快递物流追踪（快递100，免费注册）

```python
# 注册：https://www.kuaidi100.com/openapi/applyapi.shtml
# 免费额度：每日100次查询

import hashlib, time

KUAIDI100_KEY = "your_key"      # 配置到 ~/.hermes/config.yaml
KUAIDI100_CUSTOMER = "your_customer"

# 快递公司代码
COURIER_CODES = {
    "顺丰": "shunfeng", "圆通": "yuantong", "中通": "zhongtong",
    "申通": "shentong", "韵达": "yunda", "百世": "baishitongda",
    "京东": "jd", "邮政EMS": "ems", "德邦": "debangwuliu",
    "极兔": "jtexpress", "菜鸟": "cainiao",
}

def track_package(courier_name, tracking_no):
    """快递物流追踪"""
    import urllib.parse
    courier_code = COURIER_CODES.get(courier_name, courier_name.lower())
    param = json.dumps({"com": courier_code, "num": tracking_no, "phone": "", "from": "", "to": "", "resultv2": "1"})
    sign = hashlib.md5(f"{param}{KUAIDI100_KEY}{KUAIDI100_CUSTOMER}".encode()).hexdigest().upper()

    data = urllib.parse.urlencode({
        "customer": KUAIDI100_CUSTOMER,
        "sign": sign,
        "param": param,
    }).encode()

    req = urllib.request.Request(
        "https://poll.kuaidi100.com/poll/query.do",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    result = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if result.get("status") == "200":
        return {
            "status": result.get("state"),
            "status_text": {"0":"在途","1":"揽收","2":"疑难","3":"签收","4":"退签","5":"派件","6":"退回","7":"转单"}.get(result.get("state",""), "未知"),
            "last_update": result["data"][0]["time"] if result.get("data") else "",
            "last_location": result["data"][0]["context"] if result.get("data") else "",
            "history": result.get("data", [])[:10],
        }
    return {"error": result.get("message", "查询失败")}

# 无key时用playwright抓取快递100网页
def track_package_web(tracking_no, courier_code="auto"):
    """快递追踪（无需key，playwright）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://www.kuaidi100.com/chaxun?com={courier_code}&nu={tracking_no}"
        page.goto(url, timeout=15000)
        page.wait_for_timeout(4000)
        result = page.evaluate("""() => {
            const items = document.querySelectorAll('.track-list li, .transit-list li');
            return [...items].slice(0, 10).map(item => ({
                time: item.querySelector('.time, .date')?.innerText?.trim() || '',
                content: item.querySelector('.content, .info')?.innerText?.trim() || '',
            }));
        }""")
        browser.close()
        return result
```

## 交通数据工作流

```
场景1：出差行程规划
1. query_trains("北京南", "上海虹桥", "2025-06-01")
   → 筛选高铁G字头 + 有二等座
   → 输出：班次/时间/余票

2. query_flights_variflight("北京", "上海", "2025-06-01")
   → 对比航班时间/准点率

3. 综合建议：高铁 vs 飞机（时间/价格/准点率对比）

场景2：物流监控
1. track_package("顺丰", "SF1234567890")
   → 实时位置 + 预计到达

场景3：供应链延误预警
1. 批量查询多个快递单号
2. 识别异常（超时未更新/疑难件）
3. 输出预警列表
```
