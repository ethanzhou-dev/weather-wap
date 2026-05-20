import os
import re
import requests
from requests.adapters import HTTPAdapter
import requests_cache
import concurrent.futures
from flask import Flask, request, Response, redirect, url_for, send_file
from markupsafe import escape
import urllib.parse
from datetime import datetime
from flask_compress import Compress

app = Flask(__name__)
app.config["COMPRESS_ALGORITHM"] = ["gzip", "deflate"]
Compress(app)

http_session = requests_cache.CachedSession(
    "/tmp/weather_cache", backend="sqlite", expire_after=1800, stale_if_error=True
)
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
http_session.mount("http://", adapter)
http_session.mount("https://", adapter)


cities_db = {
    "北京": ["北京"],
    "天津": ["天津"],
    "河北": [
        "石家庄",
        "唐山",
        "秦皇岛",
        "邯郸",
        "邢台",
        "保定",
        "张家口",
        "承德",
        "沧州",
        "廊坊",
        "衡水",
    ],
    "山西": [
        "太原",
        "大同",
        "阳泉",
        "长治",
        "晋城",
        "朔州",
        "晋中",
        "运城",
        "忻州",
        "临汾",
        "吕梁",
    ],
    "内蒙古": [
        "呼和浩特",
        "包头",
        "乌海",
        "赤峰",
        "通辽",
        "鄂尔多斯",
        "呼伦贝尔",
        "巴彦淖尔",
        "乌兰察布",
        "兴安盟",
        "锡林郭勒盟",
        "阿拉善盟",
    ],
    "辽宁": [
        "沈阳",
        "大连",
        "鞍山",
        "抚顺",
        "本溪",
        "丹东",
        "锦州",
        "营口",
        "阜新",
        "辽阳",
        "盘锦",
        "铁岭",
        "朝阳",
        "葫芦岛",
    ],
    "吉林": ["长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边"],
    "黑龙江": [
        "哈尔滨",
        "齐齐哈尔",
        "鸡西",
        "鹤岗",
        "双鸭山",
        "大庆",
        "伊春",
        "佳木斯",
        "七台河",
        "牡丹江",
        "黑河",
        "绥化",
        "大兴安岭",
    ],
    "上海": ["上海"],
    "江苏": [
        "南京",
        "无锡",
        "徐州",
        "常州",
        "苏州",
        "南通",
        "连云港",
        "淮安",
        "盐城",
        "扬州",
        "镇江",
        "泰州",
        "宿迁",
    ],
    "浙江": [
        "杭州",
        "宁波",
        "温州",
        "嘉兴",
        "湖州",
        "绍兴",
        "金华",
        "衢州",
        "舟山",
        "台州",
        "丽水",
    ],
    "安徽": [
        "合肥",
        "芜湖",
        "蚌埠",
        "淮南",
        "马鞍山",
        "淮北",
        "铜陵",
        "安庆",
        "黄山",
        "滁州",
        "阜阳",
        "宿州",
        "六安",
        "亳州",
        "池州",
        "宣城",
    ],
    "福建": ["福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
    "江西": [
        "南昌",
        "景德镇",
        "萍乡",
        "九江",
        "新余",
        "鹰潭",
        "赣州",
        "吉安",
        "宜春",
        "抚州",
        "上饶",
    ],
    "山东": [
        "济南",
        "青岛",
        "淄博",
        "枣庄",
        "东营",
        "烟台",
        "潍坊",
        "济宁",
        "泰安",
        "威海",
        "日照",
        "临沂",
        "德州",
        "聊城",
        "滨州",
        "菏泽",
    ],
    "河南": [
        "郑州",
        "开封",
        "洛阳",
        "平顶山",
        "安阳",
        "鹤壁",
        "新乡",
        "焦作",
        "濮阳",
        "许昌",
        "漯河",
        "三门峡",
        "南阳",
        "商丘",
        "信阳",
        "周口",
        "驻马店",
        "济源",
    ],
    "湖北": [
        "武汉",
        "黄石",
        "十堰",
        "宜昌",
        "襄阳",
        "鄂州",
        "荆门",
        "孝感",
        "荆州",
        "黄冈",
        "咸宁",
        "随州",
        "恩施",
        "仙桃",
        "潜江",
        "天门",
        "神农架",
    ],
    "湖南": [
        "长沙",
        "株洲",
        "湘潭",
        "衡阳",
        "邵阳",
        "岳阳",
        "常德",
        "张家界",
        "益阳",
        "郴州",
        "永州",
        "怀化",
        "娄底",
        "湘西",
    ],
    "广东": [
        "广州",
        "深圳",
        "珠海",
        "汕头",
        "韶关",
        "佛山",
        "江门",
        "湛江",
        "茂名",
        "肇庆",
        "惠州",
        "梅州",
        "汕尾",
        "河源",
        "阳江",
        "清远",
        "东莞",
        "中山",
        "潮州",
        "揭阳",
        "云浮",
    ],
    "广西": [
        "南宁",
        "柳州",
        "桂林",
        "梧州",
        "北海",
        "防城港",
        "钦州",
        "贵港",
        "玉林",
        "百色",
        "贺州",
        "河池",
        "来宾",
        "崇左",
    ],
    "海南": [
        "海口",
        "三亚",
        "三沙",
        "儋州",
        "五指山",
        "琼海",
        "文昌",
        "万宁",
        "东方",
        "定安",
        "屯昌",
        "澄迈",
        "临高",
        "白沙",
        "昌江",
        "乐东",
        "陵水",
        "保亭",
        "琼中",
    ],
    "重庆": ["重庆"],
    "四川": [
        "成都",
        "自贡",
        "攀枝花",
        "泸州",
        "德阳",
        "绵阳",
        "广元",
        "遂宁",
        "内江",
        "乐山",
        "南充",
        "眉山",
        "宜宾",
        "广安",
        "达州",
        "雅安",
        "巴中",
        "资阳",
        "阿坝",
        "甘孜",
        "凉山",
    ],
    "贵州": [
        "贵阳",
        "六盘水",
        "遵义",
        "安顺",
        "毕节",
        "铜仁",
        "黔西南",
        "黔东南",
        "黔南",
    ],
    "云南": [
        "昆明",
        "曲靖",
        "玉溪",
        "保山",
        "昭通",
        "丽江",
        "普洱",
        "临沧",
        "楚雄",
        "红河",
        "文山",
        "西双版纳",
        "大理",
        "德宏",
        "怒江",
        "迪庆",
    ],
    "西藏": ["拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里"],
    "陕西": [
        "西安",
        "铜川",
        "宝鸡",
        "咸阳",
        "渭南",
        "延安",
        "汉中",
        "榆林",
        "安康",
        "商洛",
    ],
    "甘肃": [
        "兰州",
        "嘉峪关",
        "金昌",
        "白银",
        "天水",
        "武威",
        "张掖",
        "平凉",
        "酒泉",
        "庆阳",
        "定西",
        "陇南",
        "临夏",
        "甘南",
    ],
    "青海": ["西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西"],
    "宁夏": ["银川", "石嘴山", "吴忠", "固原", "中卫"],
    "新疆": [
        "乌鲁木齐",
        "克拉玛依",
        "吐鲁番",
        "哈密",
        "昌吉",
        "博尔塔拉",
        "巴音郭楞",
        "阿克苏",
        "克孜勒苏",
        "喀什",
        "和田",
        "伊犁",
        "塔城",
        "阿勒泰",
        "石河子",
        "阿拉尔",
        "图木舒克",
        "五家渠",
        "北屯",
        "铁门关",
        "双河",
        "可克达拉",
        "昆玉",
    ],
    "香港": ["香港"],
    "澳门": ["澳门"],
    "台湾": [
        "台北",
        "新北",
        "桃园",
        "台中",
        "台南",
        "高雄",
        "基隆",
        "新竹",
        "嘉义",
        "苗栗",
        "彰化",
        "南投",
        "云林",
        "屏东",
        "宜兰",
        "花莲",
        "台东",
        "澎湖",
        "金门",
        "连江",
    ],
}


def get_aqi_data(city_name):
    WAQI_TOKEN = os.environ.get("WAQI_TOKEN")
    if not WAQI_TOKEN:
        return "未配置Token"

    url = f"https://api.waqi.info/feed/{urllib.parse.quote(city_name)}/?token={WAQI_TOKEN}"

    try:
        response = http_session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                aqi_val = data["data"].get("aqi")

                if isinstance(aqi_val, int) or (
                    isinstance(aqi_val, str) and aqi_val.isdigit()
                ):
                    aqi = int(aqi_val)
                    if aqi <= 50:
                        level = "优"
                    elif aqi <= 100:
                        level = "良"
                    elif aqi <= 150:
                        level = "轻度污染"
                    elif aqi <= 200:
                        level = "中度污染"
                    elif aqi <= 300:
                        level = "重度污染"
                    else:
                        level = "严重污染"
                    return f"{aqi} ({level})"
    except requests.RequestException:
        pass

    return "未知"


def get_future_aqi_data(city_name, target_date):
    """
    获取 WAQI 接口中特定日期的 PM2.5 (AQI) 预报数据
    """
    WAQI_TOKEN = os.environ.get("WAQI_TOKEN")
    if not WAQI_TOKEN:
        return "未配置Token"
    url = f"https://api.waqi.info/feed/{urllib.parse.quote(city_name)}/?token={WAQI_TOKEN}"

    try:
        response = http_session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                forecast_daily = (
                    data.get("data", {}).get("forecast", {}).get("daily", {})
                )
                pm25_forecasts = forecast_daily.get("pm25", [])

                for day_data in pm25_forecasts:
                    if day_data.get("day") == target_date:
                        aqi_val = day_data.get("avg")

                        if aqi_val is not None:
                            aqi = int(aqi_val)
                            if aqi <= 50:
                                level = "优"
                            elif aqi <= 100:
                                level = "良"
                            elif aqi <= 150:
                                level = "轻度污染"
                            elif aqi <= 200:
                                level = "中度污染"
                            elif aqi <= 300:
                                level = "重度污染"
                            else:
                                level = "严重污染"
                            return f"{aqi} ({level})"
    except Exception:
        pass

    return "暂无预报"


def generate_xhtml_response(title, body_content):
    xhtml_str = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.0//EN" "http://www.wapforum.org/DTD/xhtml-mobile10.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head>
    <title>{title}</title>
    <link rel="apple-touch-icon" href="/speeddial-icon.png" />
    <link rel="icon" type="image/png" sizes="128x128" href="/speeddial-icon.png" />
    <link rel="shortcut icon" href="/favicon.ico" type="image/x-icon" />
    <meta http-equiv="Cache-Control" content="max-age=0" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0, user-scalable=yes" />
    <style type="text/css">
        body {{ background-color: whitesmoke; color: black; margin: 0; padding: 0; }}
        a {{ color: darkblue; text-decoration: none; }}
        a:visited {{ color: darkblue; }}
        a:hover {{ text-decoration: underline; }}
        .header {{ background-color: #3B5998; color: white; padding: 4px 6px; font-weight: bold; }}
        .content {{ padding: 6px; line-height: 1.5; }}
        .content b {{ color: black; }}
        hr {{ border: 0; border-bottom: 1px solid silver; margin: 6px 0; }}
        select, input {{ border: 1px solid silver; background-color: white; margin-top: 4px; }}
        input[type="submit"] {{ background-color: gainsboro; border: 1px solid silver; padding: 2px 6px; }}
        .nav {{ background-color: gainsboro; padding: 6px; border-top: 1px solid silver; text-align: center; }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>"""
    mimetype = request.accept_mimetypes.best_match(
        [
            "text/html",
            "application/vnd.wap.xhtml+xml",
            "application/xhtml+xml",
        ]
    )

    if not mimetype:
        mimetype = "text/html"

    return Response(xhtml_str, mimetype=mimetype)


@app.route("/favicon.ico")
def favicon():
    if os.path.exists("favicon.ico"):
        response = send_file("favicon.ico", mimetype="image/x-icon")
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        return response
    return "", 404


@app.route("/speeddial-icon.png")
def speeddial_icon():
    if os.path.exists("speeddial-icon.png"):
        response = send_file("speeddial-icon.png", mimetype="image/png")
        response.headers["Cache-Control"] = "public, max-age=604800"
        return response
    return "", 404


@app.route("/")
def index():
    """首页：选择省份 (新增Cookie记忆跳转)"""
    clear = request.args.get("clear")
    if clear != "1":
        saved_city = request.cookies.get("saved_city")
        if saved_city:
            return redirect(url_for("weather", city=saved_city))

    options = "".join([f'<option value="{p}">{p}</option>' for p in cities_db.keys()])
    body = f"""
    <div class="header">天气查询</div>
    <div class="content">
        请选择省份:<br/>
        <form action="/city" method="get">
            <select name="prov">
                {options}
            </select><br/>
            <input type="submit" value="下一步" />
        </form>
    </div>
    """

    resp = generate_xhtml_response("天气预报", body)

    if clear == "1":
        resp.set_cookie("saved_city", "", expires=0)

    return resp


@app.route("/city")
def city():
    """第二页：选择城市"""
    prov = request.args.get("prov")
    if not prov or prov not in cities_db:
        return redirect("/")

    options = "".join([f'<option value="{c}">{c}</option>' for c in cities_db[prov]])
    body = f"""
    <div class="header">天气查询</div>
    <div class="content">
        已选省份: <b>{escape(prov)}</b><hr/>
        请选择城市:<br/>
        <form action="/weather" method="get">
            <select name="city">
                {options}
            </select><br/>
            <input type="submit" value="查询天气" />
        </form>
    </div>
    """
    return generate_xhtml_response(f"{prov} - 选市", body)


@app.route("/weather")
def weather():
    """第三页：展示天气文字 (新增写Cookie，并修改返回按钮)"""
    city = request.args.get("city")
    if not city:
        return redirect("/")

    safe_city = escape(city)

    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=zh-cn"
    is_success = False

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_weather = executor.submit(
                http_session.get, url, headers=headers, timeout=10
            )
            future_aqi = executor.submit(get_aqi_data, city)

            response = future_weather.result()
            aqi_text = future_aqi.result()

        if response.status_code == 200:
            response.encoding = "utf-8"
            data = response.json()

            if not data.get("current_condition") or not data.get("weather"):
                return generate_xhtml_response(
                    "提示",
                    "<div class='content'>天气接口返回异常数据，请稍后再试。</div>",
                )

            current = data["current_condition"][0]
            today = data["weather"][0]

            desc = "未知"
            for k in ("lang_zh-cn", "lang_zh", "lang_xx", "weatherDesc"):
                val_list = current.get(k)
                if val_list and isinstance(val_list, list) and "value" in val_list[0]:
                    desc = val_list[0]["value"]
                    break

            temp = current["temp_C"]
            humidity = current["humidity"]
            wind_kmh = current["windspeedKmph"]
            feels_like = current["FeelsLikeC"]
            visibility = current["visibility"]
            max_temp = today["maxtempC"]
            min_temp = today["mintempC"]
            uv_index = today.get("uvIndex", "未知")

            astronomy = today["astronomy"][0]
            sunrise = astronomy.get("sunrise", "未知")
            sunset = astronomy.get("sunset", "未知")
            wind_dir = current.get("winddir16Point", "")
            pressure = current.get("pressure", "未知")
            cloudcover = current.get("cloudcover", "未知")
            precip = current.get("precipMM", "0.0")

            try:
                current_t = int(temp)
                max_t = int(max_temp)
                min_t = int(min_temp)

                if current_t > max_t:
                    max_temp = str(current_t)
                if current_t < min_t:
                    min_temp = str(current_t)
            except ValueError:
                pass

            result_text = (
                f'<div class="header">[{safe_city}实时天气]</div>'
                f'<div class="content">'
                f"概况: <b>{escape(desc)}</b><br/>"
                f"温度: <b>{min_temp}~{max_temp}℃</b><br/>"
                f"当前: <b>{temp}℃</b> (体感 {feels_like}℃)"
                f"<hr/>"
                f"空气质量: {aqi_text}<br/>"
                f"湿度: {humidity}%<br/>"
                f"降水: {precip} mm<br/>"
                f"云量: {cloudcover}%<br/>"
                f"气压: {pressure} hPa<br/>"
                f"风向风速: {escape(wind_dir)} {wind_kmh} km/h<br/>"
                f"能见度: {visibility} km<br/>"
                f"紫外线: {uv_index}"
                f"<hr/>"
                f"日出: {sunrise}<br/>"
                f"日落: {sunset}<br/>"
            )

            result_text += "<hr/><b>[ 未来两天预报 ]</b><br/>"
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

            for day_data in data.get("weather", [])[1:]:
                date_str = day_data.get("date", "")

                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    weekday_str = weekdays[dt.weekday()]
                    short_date = date_str[5:]
                except Exception:
                    weekday_str = ""
                    short_date = date_str

                link_url = url_for("weather_detail", city=city, date=date_str)

                result_text += f'&gt; <a href="{escape(link_url)}">{weekday_str}({short_date})</a><br/>'

            result_text += "</div>"

            is_success = True
        else:
            result_text = f'<div class="content">查询失败: 服务器返回状态码 {response.status_code}，请稍后再试。</div>'

    except Exception as e:
        result_text = (
            '<div class="content">系统错误: 连接天气服务器超时或网络异常。</div>'
        )

    body = f"""
    {result_text}
    <div class="nav">
        <a href="/?clear=1">[更换城市]</a>
    </div>
    """

    resp = generate_xhtml_response("查询结果", body)

    if is_success:
        resp.set_cookie(
            "saved_city", city, max_age=2592000, httponly=True, samesite="Lax"
        )

    return resp


@app.route("/weather_detail")
def weather_detail():
    """展示某天的详细天气"""
    city = request.args.get("city")
    target_date = request.args.get("date")

    if not city or not target_date:
        return redirect("/")

    safe_city = escape(city)
    safe_date = escape(target_date)

    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=zh-cn"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_weather = executor.submit(
                http_session.get, url, headers=headers, timeout=10
            )
            future_aqi = executor.submit(get_future_aqi_data, city, target_date)

            response = future_weather.result()
            future_aqi_text = future_aqi.result()

        if response.status_code == 200:
            response.encoding = "utf-8"
            data = response.json()

            target_data = None
            for day in data.get("weather", []):
                if day.get("date") == target_date:
                    target_data = day
                    break

            if target_data:
                max_temp = target_data["maxtempC"]
                min_temp = target_data["mintempC"]
                uv_index = target_data.get("uvIndex", "未知")

                astronomy = target_data["astronomy"][0]
                sunrise = astronomy.get("sunrise", "未知")
                sunset = astronomy.get("sunset", "未知")

                hourly_list = target_data.get("hourly", [])
                if len(hourly_list) > 4:
                    hourly = hourly_list[4]
                elif len(hourly_list) > 0:
                    hourly = hourly_list[0]
                else:
                    return generate_xhtml_response(
                        "提示",
                        "<div class='content'>未获取到该日期的时段详情数据。</div>",
                    )
                desc = "未知"
                for k in ("lang_zh-cn", "lang_zh", "lang_xx", "weatherDesc"):
                    val_list = hourly.get(k)
                    if val_list and isinstance(val_list, list) and "value" in val_list[0]:
                        desc = val_list[0]["value"]
                        break

                feels_like = hourly.get("FeelsLikeC", "未知")
                humidity = hourly.get("humidity", "未知")
                wind_kmh = hourly.get("windspeedKmph", "未知")
                visibility = hourly.get("visibility", "未知")

                wind_dir = hourly.get("winddir16Point", "")
                pressure = hourly.get("pressure", "未知")
                cloudcover = hourly.get("cloudcover", "未知")
                precip = hourly.get("precipMM", "0.0")
                chance_of_rain = hourly.get("chanceofrain", "未知")

                result_text = (
                    f'<div class="header">[{safe_city} {safe_date[5:]} 预报]</div>'
                    f'<div class="content">'
                    f"概况: <b>{escape(desc)}</b><br/>"
                    f"温度: <b>{min_temp}~{max_temp}℃</b><br/>"
                    f"降雨概率: {chance_of_rain}%"
                    f"<hr/>"
                    f"空气质量: {future_aqi_text}<br/>"
                    f"湿度: {humidity}%<br/>"
                    f"降水: {precip} mm<br/>"
                    f"云量: {cloudcover}%<br/>"
                    f"气压: {pressure} hPa<br/>"
                    f"风向风速: {escape(wind_dir)} {wind_kmh} km/h<br/>"
                    f"能见度: {visibility} km<br/>"
                    f"紫外线: {uv_index}"
                    f"<hr/>"
                    f"日出: {sunrise}<br/>"
                    f"日落: {sunset}"
                    f"</div>"
                )
            else:
                result_text = '<div class="content">未找到该日期的天气数据。</div>'
        else:
            result_text = f'<div class="content">查询失败: 服务器返回状态码 {response.status_code}，请稍后再试。</div>'
    except Exception as e:
        result_text = '<div class="content">系统错误: 连接天气服务器超时。</div>'

    body = f"""
    {result_text}
    <div class="nav">
        <a href="{url_for('weather', city=city)}">[返回今天天气]</a><br/>
        <br/>
        <a href="/?clear=1">[更换查询城市]</a>
    </div>
    """
    return generate_xhtml_response("天气详情", body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
