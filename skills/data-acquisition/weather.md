---
name: data-acquisition/weather
description: 天气预报、气候数据、空气质量AQI。wttr.in（免费无需key）、和风天气API（免费注册）、中国环境监测总站AQI。支持全球城市。
---

# 天气与环境数据

## 工具优先级

| 数据类型 | 首选 | 备选 |
|--------|------|------|
| 实时天气/预报 | wttr.in（无需key） | 和风天气API |
| 空气质量AQI | aqicn.org API | 中国环境监测总站 |
| 历史气候 | 和风天气API | wttr.in |
| 灾害预警 | 中国气象局 | 和风天气 |

## wttr.in（免费，无需注册，直接用）

```python
import urllib.request, json

def get_weather(city, lang="zh"):
    """获取城市天气，无需API key"""
    # 中文城市名需要URL编码
    from urllib.parse import quote
    url = f"https://wttr.in/{quote(city)}?format=j1&lang={lang}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())

        current = data["current_condition"][0]
        weather = data["weather"][0]

        return {
            "city": city,
            "temp_c": current["temp_C"],
            "feels_like_c": current["FeelsLikeC"],
            "humidity": current["humidity"],
            "wind_kmph": current["windspeedKmph"],
            "wind_dir": current["winddir16Point"],
            "description": current["weatherDesc"][0]["value"],
            "visibility_km": current["visibility"],
            "uv_index": current["uvIndex"],
            # 今日预报
            "today_max_c": weather["maxtempC"],
            "today_min_c": weather["mintempC"],
            "sunrise": weather["astronomy"][0]["sunrise"],
            "sunset": weather["astronomy"][0]["sunset"],
        }
    except Exception as e:
        return {"error": str(e)}

# 3天预报
def get_forecast(city, days=3):
    from urllib.parse import quote
    url = f"https://wttr.in/{quote(city)}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        forecast = []
        for day in data["weather"][:days]:
            forecast.append({
                "date": day["date"],
                "max_c": day["maxtempC"],
                "min_c": day["mintempC"],
                "avg_c": day["avgtempC"],
                "hourly": [
                    {
                        "time": h["time"],
                        "temp_c": h["tempC"],
                        "desc": h["weatherDesc"][0]["value"],
                        "rain_mm": h["precipMM"],
                        "chance_rain": h["chanceofrain"],
                    }
                    for h in day["hourly"]
                ],
            })
        return forecast
    except Exception as e:
        return {"error": str(e)}

# 使用示例
w = get_weather("北京")
print(f"{w['city']}: {w['temp_c']}°C，{w['description']}，湿度{w['humidity']}%，风速{w['wind_kmph']}km/h")
print(f"今日 {w['today_min_c']}~{w['today_max_c']}°C，日出{w['sunrise']} 日落{w['sunset']}")
```

## 空气质量 AQI（aqicn.org，免费token）

```python
# 免费token申请：https://aqicn.org/data-platform/token/
# 申请后填入下方 TOKEN

AQI_TOKEN = "your_token_here"  # 配置到 ~/.hermes/config.yaml: aqi_token

def get_aqi(city):
    """获取城市实时AQI和PM2.5"""
    from urllib.parse import quote
    url = f"https://api.waqi.info/feed/{quote(city)}/?token={AQI_TOKEN}"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=10).read())
        if data["status"] == "ok":
            d = data["data"]
            iaqi = d.get("iaqi", {})
            return {
                "city": city,
                "aqi": d["aqi"],
                "level": _aqi_level(d["aqi"]),
                "pm25": iaqi.get("pm25", {}).get("v", "N/A"),
                "pm10": iaqi.get("pm10", {}).get("v", "N/A"),
                "o3": iaqi.get("o3", {}).get("v", "N/A"),
                "no2": iaqi.get("no2", {}).get("v", "N/A"),
                "co": iaqi.get("co", {}).get("v", "N/A"),
                "updated": d["time"]["s"],
            }
    except Exception as e:
        return {"error": str(e)}

def _aqi_level(aqi):
    if aqi <= 50: return "优"
    if aqi <= 100: return "良"
    if aqi <= 150: return "轻度污染"
    if aqi <= 200: return "中度污染"
    if aqi <= 300: return "重度污染"
    return "严重污染"

# 无token时用中国环境监测总站（playwright）
def get_aqi_cnemc(city):
    """中国环境监测总站AQI（无需token）"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://air.cnemc.cn:18007/", timeout=15000)
        page.wait_for_timeout(3000)
        # 搜索城市
        page.fill('input[placeholder*="城市"]', city)
        page.wait_for_timeout(2000)
        data = page.evaluate("""() => {
            const aqi = document.querySelector('.aqi-value, .AQI')?.innerText?.trim() || '';
            const level = document.querySelector('.aqi-level, .quality')?.innerText?.trim() || '';
            const pm25 = document.querySelector('.pm25-value, [data-type="PM2.5"]')?.innerText?.trim() || '';
            return {aqi, level, pm25};
        }""")
        browser.close()
        return data
```

## 和风天气 API（免费注册，每日1000次）

```python
# 注册：https://id.heweather.com/
# 免费额度：1000次/天，实时天气+7天预报+逐小时+空气质量

QWEATHER_KEY = "your_key_here"  # 配置到 ~/.hermes/config.yaml: qweather_key

def qweather_now(location):
    """和风天气实时数据（需key）"""
    url = f"https://devapi.qweather.com/v7/weather/now?location={location}&key={QWEATHER_KEY}&lang=zh"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["code"] == "200":
        n = data["now"]
        return {
            "temp": n["temp"], "feels_like": n["feelsLike"],
            "text": n["text"], "wind_dir": n["windDir"],
            "wind_scale": n["windScale"], "humidity": n["humidity"],
            "precip": n["precip"], "vis": n["vis"],
            "cloud": n["cloud"], "dew": n["dew"],
        }

def qweather_7d(location):
    """7天预报"""
    url = f"https://devapi.qweather.com/v7/weather/7d?location={location}&key={QWEATHER_KEY}&lang=zh"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    return data.get("daily", [])

def qweather_air(location):
    """实时空气质量"""
    url = f"https://devapi.qweather.com/v7/air/now?location={location}&key={QWEATHER_KEY}&lang=zh"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    return data.get("now", {})
```

## 气象灾害预警（中国气象局，无需key）

```python
def get_weather_warning(province=""):
    """获取气象灾害预警信息"""
    url = "https://www.nmc.cn/rest/findAlarm"
    if province:
        url += f"?province={province}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.nmc.cn/"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        warnings = []
        for item in (data.get("data") or [])[:20]:
            warnings.append({
                "title": item.get("title", ""),
                "type": item.get("type", ""),
                "level": item.get("level", ""),
                "province": item.get("province", ""),
                "city": item.get("city", ""),
                "time": item.get("issuetime", ""),
            })
        return warnings
    except Exception as e:
        return [{"error": str(e)}]
```

## 天气数据工作流

```
场景：活动/出行/供应链天气决策

1. 获取目标城市天气：
   get_weather("<城市>")  → 实时温度/风速/降水

2. 获取3天预报：
   get_forecast("<城市>", days=3)  → 逐日最高/最低/降水概率

3. 检查空气质量：
   get_aqi("<城市>")  → AQI/PM2.5/污染等级

4. 检查灾害预警：
   get_weather_warning("<省份>")  → 暴雨/台风/高温预警

5. 输出决策建议：
   - 户外活动：AQI<100 + 无降水 + 风力<4级 → 适宜
   - 物流运输：关注暴雨/大雪/大风预警
   - 农业/供应链：关注极端天气对产区影响
```
