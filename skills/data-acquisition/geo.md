---
name: data-acquisition/geo
description: 地图、地理位置、POI搜索、路线规划、周边设施。高德地图API（免费注册）+ 无key备选方案。支持地理编码/逆地理编码/驾车/步行/公交路线。
---

# 地图与地理数据

## 工具优先级

| 数据类型 | 首选 | 备选 |
|--------|------|------|
| POI搜索 | 高德地图API | playwright搜索 |
| 地理编码（地址→坐标） | 高德地图API | nominatim（免费无key） |
| 逆地理编码（坐标→地址） | 高德地图API | nominatim |
| 路线规划 | 高德地图API | playwright高德网页 |
| 周边设施 | 高德地图API | playwright |
| 行政区划 | 高德地图API | 国家统计局代码库 |

## 高德地图 API（免费注册，每日5000次）

```python
# 注册：https://lbs.amap.com/
# 免费额度：5000次/天，基础服务全免费
# 配置到 ~/.hermes/config.yaml: amap_key

import urllib.request, json
from urllib.parse import quote

AMAP_KEY = "your_key_here"

def amap_geocode(address, city=""):
    """地址 → 经纬度坐标"""
    params = f"address={quote(address)}&key={AMAP_KEY}"
    if city:
        params += f"&city={quote(city)}"
    url = f"https://restapi.amap.com/v3/geocode/geo?{params}"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1" and data["geocodes"]:
        g = data["geocodes"][0]
        lng, lat = g["location"].split(",")
        return {
            "address": g["formatted_address"],
            "province": g["province"],
            "city": g["city"],
            "district": g["district"],
            "lng": float(lng),
            "lat": float(lat),
            "level": g["level"],
        }

def amap_regeo(lng, lat):
    """经纬度 → 详细地址"""
    url = f"https://restapi.amap.com/v3/geocode/regeo?location={lng},{lat}&key={AMAP_KEY}&extensions=all"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1":
        r = data["regeocode"]
        return {
            "address": r["formatted_address"],
            "province": r["addressComponent"]["province"],
            "city": r["addressComponent"]["city"],
            "district": r["addressComponent"]["district"],
            "street": r["addressComponent"]["streetNumber"].get("street", ""),
            "number": r["addressComponent"]["streetNumber"].get("number", ""),
        }

def amap_poi_search(keyword, city, page=1, page_size=20):
    """POI搜索：餐厅/酒店/医院/学校/商场等"""
    url = (f"https://restapi.amap.com/v3/place/text"
           f"?keywords={quote(keyword)}&city={quote(city)}&offset={page_size}"
           f"&page={page}&key={AMAP_KEY}&extensions=all")
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1":
        pois = []
        for p in data.get("pois", []):
            lng, lat = p["location"].split(",") if "," in p.get("location","0,0") else ("0","0")
            pois.append({
                "name": p["name"],
                "type": p["type"],
                "address": p["address"],
                "tel": p.get("tel", ""),
                "rating": p.get("biz_ext", {}).get("rating", ""),
                "cost": p.get("biz_ext", {}).get("cost", ""),
                "lng": float(lng),
                "lat": float(lat),
                "distance": p.get("distance", ""),
            })
        return pois

def amap_around(lng, lat, keyword, radius=1000):
    """周边搜索：以某坐标为中心搜索周边POI"""
    url = (f"https://restapi.amap.com/v3/place/around"
           f"?location={lng},{lat}&keywords={quote(keyword)}&radius={radius}"
           f"&key={AMAP_KEY}&extensions=base&offset=20")
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1":
        return [{"name": p["name"], "distance": p.get("distance",""), "address": p["address"]}
                for p in data.get("pois", [])]

def amap_route_drive(origin_lng, origin_lat, dest_lng, dest_lat):
    """驾车路线规划"""
    url = (f"https://restapi.amap.com/v3/direction/driving"
           f"?origin={origin_lng},{origin_lat}&destination={dest_lng},{dest_lat}"
           f"&key={AMAP_KEY}&extensions=base")
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1":
        route = data["route"]["paths"][0]
        return {
            "distance_m": int(route["distance"]),
            "duration_s": int(route["duration"]),
            "distance_km": round(int(route["distance"]) / 1000, 1),
            "duration_min": round(int(route["duration"]) / 60, 0),
            "tolls": route.get("tolls", "0"),
            "steps": len(route["steps"]),
        }

def amap_weather(city):
    """高德天气查询（无需和风key）"""
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={quote(city)}&key={AMAP_KEY}&extensions=all"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1":
        lives = data.get("lives", [{}])[0]
        forecasts = data.get("forecasts", [{}])[0].get("casts", [])
        return {
            "city": lives.get("city"),
            "weather": lives.get("weather"),
            "temperature": lives.get("temperature"),
            "wind_direction": lives.get("winddirection"),
            "wind_power": lives.get("windpower"),
            "humidity": lives.get("humidity"),
            "forecast": [
                {"date": f["date"], "day": f["dayweather"],
                 "night": f["nightweather"], "high": f["daytemp"], "low": f["nighttemp"]}
                for f in forecasts
            ]
        }
```

## 无key备选：Nominatim（OpenStreetMap，完全免费）

```python
def nominatim_geocode(address, country="cn"):
    """OpenStreetMap地理编码，无需key"""
    url = f"https://nominatim.openstreetmap.org/search?q={quote(address)}&countrycodes={country}&format=json&limit=3"
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-agent/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if data:
        r = data[0]
        return {
            "display_name": r["display_name"],
            "lat": float(r["lat"]),
            "lng": float(r["lon"]),
            "type": r.get("type", ""),
        }

def nominatim_regeo(lat, lng):
    """OpenStreetMap逆地理编码"""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-agent/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return data.get("display_name", "")
```

## 行政区划数据

```python
def get_districts(province="", city=""):
    """获取行政区划列表（高德API）"""
    keywords = province or city or "中国"
    url = f"https://restapi.amap.com/v3/config/district?keywords={quote(keywords)}&subdistrict=2&key={AMAP_KEY}"
    data = json.loads(urllib.request.urlopen(url, timeout=10).read())
    if data["status"] == "1":
        return data.get("districts", [])
```

## 地理数据工作流

```
场景1：选址分析
1. amap_geocode("目标地址") → 获取坐标
2. amap_around(lng, lat, "竞争对手品牌", radius=2000) → 周边竞品密度
3. amap_around(lng, lat, "地铁站", radius=500) → 交通便利性
4. amap_around(lng, lat, "写字楼", radius=1000) → 目标客群密度
5. 综合评分输出选址建议

场景2：竞品门店分布
1. amap_poi_search("竞品品牌名", city="上海") → 全市门店列表
2. 统计各区门店数量 → 密度热力图数据
3. 对比我方门店分布 → 找空白市场

场景3：物流/配送规划
1. amap_geocode(仓库地址) → 起点坐标
2. amap_geocode(客户地址) → 终点坐标
3. amap_route_drive(起点, 终点) → 距离/时间/过路费
4. 批量计算多个配送点 → 优化路线
```
