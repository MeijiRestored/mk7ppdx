import json
import math
import os
import re
import time
from datetime import datetime
from html import unescape
from typing import Dict, Any, Callable, Optional

import redis
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, redirect, url_for, request
from scrapy import Selector

from config import Config
from util import get_abbr_name, rgb_to_hex, get_color, get_country_id, hex_to_rgb, get_std_color, get_std_name, \
    parse_time, format_time, extract_pid

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")

if app.config["USE_REDIS"]:
    redis_client = redis.StrictRedis(
        host=app.config["REDIS_HOST"],
        port=app.config["REDIS_PORT"],
        db=app.config["REDIS_DB"],
        decode_responses=True
    )
else:
    redis_client = None

BASE_URL = "https://www.mariokart64.com/mk7/"


def process_profile(body, pid):
    if "No player matches player id" in body:
        return {"notfound": True}

    sel = Selector(text=body)

    # Extract player name and country
    info_table = sel.xpath('//table[.//tr/td[normalize-space(.)="Who & Where"]]/following-sibling::table[1]')
    player_name = info_table.xpath('.//tr[td[1][normalize-space(.)="Player\'s Name"]]/td[2]/text()').get(
        default='').strip()
    country = info_table.xpath('.//tr[td[1][normalize-space(.)="Country"]]/td[2]/text()').get(default='').strip()

    totaltime = 0

    # Initialize root-level data
    data = {
        "notfound": False,
        "name": player_name,
        "country": country,
        "courses": {},
        "rankings": {},
        "af": 0,
        "totaltime": "",
        "prsravg": 0,
        "arr": 0,
        "arrname": "",
        "nbtimes": 0,
    }

    # Iterate through each even ID from 0 to 62
    for cid in range(0, 63, 2):
        # Default entry structure
        entry = {
            "hastime": False,
            "name": "",
            "abbrname": "",
            "time": "",
            "rank": 0,
            "prsr": 0.0,
            "srdelta": 0.0,
            "std": 0,
            "stdname": "",
            "date": ""
        }

        # Locate the <tr> containing the first <a href='coursec.php?cid=cid'>
        tr = sel.xpath(f"//tr[td/a[starts-with(@href, 'coursec.php?cid={cid}')]][1]")
        if tr:
            # Extract fields
            name = tr.xpath("td[1]/a/text()").get(default="").strip()
            time_text = tr.xpath("td[2]/text()").get(default="").strip()

            if time_text != "NT":
                onmouse = tr.xpath("td[2]/a/@onmouseover").get()
                onmouse = unescape(onmouse)
                delta_text = ""
                m = re.search(r"([+\-])(\d+):(\d+\.\d+)", onmouse)
                if m:
                    sign, mins_str, secs_str = m.groups()
                    minutes = int(mins_str)
                    seconds = float(secs_str)

                    total = minutes * 60 + seconds

                    if sign == '-':
                        total = -total

                    # format as s.mmm (always three decimal places)
                    delta_text = f"{total:.3f}"

                time = tr.xpath("td[2]/a/text()").get(default="").strip()
                rank_text = tr.xpath("td[4]/text()").get(default="0").strip()
                prsr_text = tr.xpath("td[5]/text()").get(default="0").strip().rstrip('%')
                std_text = tr.xpath("td[6]/text()").get(default="0").strip().split('/')[0].strip()
                date = tr.xpath("td[7]/text()").get(default="").strip()

                abbrname = get_abbr_name(name)

                # Convert to appropriate types
                try:
                    rank = int(rank_text)
                except ValueError:
                    rank = 0
                try:
                    delta = float(delta_text)
                except ValueError:
                    delta = 0.0
                try:
                    prsr = float(prsr_text)
                except ValueError:
                    prsr = 0.0
                try:
                    std = int(std_text)
                except ValueError:
                    std = 0

                stdname = get_std_name(std)

                # Update entry
                entry.update({
                    "hastime": True,
                    "name": name,
                    "abbrname": abbrname,
                    "time": time,
                    "delta": delta,
                    "rank": rank,
                    "prsr": prsr,
                    "std": std,
                    "stdname": stdname,
                    "date": date
                })

                data["nbtimes"] += 1
                data["af"] += rank
                data["prsravg"] += prsr
                data["arr"] += std
                totaltime += parse_time(time)
            else:
                abbrname = get_abbr_name(name)

                entry.update({
                    "hastime": False,
                    "name": name,
                    "abbrname": abbrname,
                })
        data["courses"][str(cid)] = entry

    data["totaltime"] = format_time(totaltime)
    data["af"] = math.ceil((data["af"] / data["nbtimes"]) * 10_000) / 10_000
    data["prsravg"] = math.floor((data["prsravg"] / data["nbtimes"]) * 10_000) / 10_000
    data["arr"] = math.ceil((data["arr"] / data["nbtimes"]) * 10_000) / 10_000
    data["arrname"] = get_std_name(data["arr"])

    if data["nbtimes"] == 32:
        rankings_entry = {
            "af": get_af_ranking(pid),
            "arr": get_arr_ranking(pid),
            "ttime": get_ttime_ranking(pid),
            "prsr": get_prsr_ranking(pid)
        }

        data["rankings"] = rankings_entry

    return data


def _process_rankings(
    body: str,
    *,
    score_parser: Callable[[str], Any],
    change_parser: Optional[Callable[[str], float]] = None,
    trend_calculator: Optional[Callable[[float], str]] = None,
    score_col: int = 6,
    change_col: int = 7,
) -> Dict[str, Dict[str, Any]]:
    """
    A generic routine to parse ranking tables.

    Parameters
    ----------
    body : str
        Raw HTML body containing the ranking table.
    score_parser : Callable[[str], Any]
        Function that converts the score column text to the desired datatype.
    change_parser : Optional[Callable[[str], float]]
        Function that converts the change column text to float. If None,
        no `change` field will be extracted.
    trend_calculator : Optional[Callable[[float], str]]
        Function that maps a numeric change value to a trend string.
        Ignored if `change_parser` is None.
    score_col : int, default 6
        1‑based column index for the score.
    change_col : int, default 7
        1‑based column index for the change.

    Returns
    -------
    dict
        Mapping of player id (`pid` as str) to ranking info.
    """
    sel = Selector(text=body)
    rankings: Dict[str, Dict[str, Any]] = {}

    rows = sel.xpath("//table[tr/th[normalize-space(.)='Rank']]/tr[position()>1]")
    for row in rows:
        rank_text = row.xpath("td[1]/text()").get(default="").strip()
        name = row.xpath("td[2]/text()").get(default="").strip()
        pid_href = row.xpath("td[3]/a/@href").get(default="")
        pid = extract_pid(pid_href)
        country = row.xpath("td[4]/text()").get(default="").strip()
        code = get_country_id(country)

        # Extract and parse score
        score_raw = row.xpath(f"td[{score_col}]/text()").get(default="").strip()
        try:
            score = score_parser(score_raw)
        except Exception:
            score = 0.0 if change_parser else score_raw  # fallback

        # Extract and parse change (if requested)
        change = None
        if change_parser is not None:
            change_raw = row.xpath(f"td[{change_col}]/text()").get(default="").strip()
            try:
                change = change_parser(change_raw)
            except Exception:
                change = 0.0

        # Validate rank
        try:
            rank = int(rank_text)
        except ValueError:
            continue

        # Build record
        record: Dict[str, Any] = {
            "rank": rank,
            "name": name,
            "country": country,
            "code": code,
            "score": score,
        }

        if change_parser is not None:
            record["change"] = change
            trend = (
                trend_calculator(change) if trend_calculator is not None else "equal"
            )
            record["trend"] = trend

        rankings[str(pid)] = record

    return rankings


def process_af_rankings(body: str):
    return _process_rankings(
        body,
        score_parser=lambda s: float(s) if s else 0.0,
        change_parser=lambda s: float(s) if s else 0.0,
        trend_calculator=lambda c: "down" if c > 0 else "up" if c < 0 else "equal",
    )


def process_arr_rankings(body: str):
    return _process_rankings(
        body,
        score_parser=lambda s: float(s.split(" ")[0]) if s else 0.0,
        change_parser=lambda s: float(s) if s else 0.0,
        trend_calculator=lambda c: "down" if c > 0 else "up" if c < 0 else "equal",
    )


def process_ttime_rankings(body: str):
    return _process_rankings(
        body,
        score_parser=lambda s: s,
        change_parser=None,  # TTIME tables have no change column
        trend_calculator=None,
        score_col=5,  # Score is in column 5 for TTIME
    )


def process_prsr_rankings(body: str):
    return _process_rankings(
        body,
        score_parser=lambda s: float(s.replace("%", "")) if s else 0.0,
        change_parser=lambda s: float(s.replace("%", "")) if s else 0.0,
        trend_calculator=lambda c: "down" if c < 0 else "up" if c > 0 else "equal",
    )


@app.template_filter('date_color')
def date_color_filter(date_str, min_date_str, max_date_str, fmt="%Y-%m-%d"):
    GRADIENT_STOPS = [
        (0.00, (128, 0, 0)),
        (0.33, (128, 82, 0)),
        (0.66, (128, 128, 0)),
        (1.00, (0, 128, 0)),
    ]

    dt = datetime.strptime(date_str, fmt)
    dt0 = datetime.strptime(min_date_str, fmt)
    dt1 = datetime.strptime(max_date_str, fmt)
    span = (dt1 - dt0).total_seconds() or 1.0
    pos = (dt - dt0).total_seconds() / span
    pos = max(0.0, min(1.0, pos))

    # find which two stops pos straddles
    for i in range(len(GRADIENT_STOPS) - 1):
        t0, c0 = GRADIENT_STOPS[i]
        t1, c1 = GRADIENT_STOPS[i + 1]
        if t0 <= pos <= t1:
            local = (pos - t0) / (t1 - t0)
            r = int(c0[0] + (c1[0] - c0[0]) * local)
            g = int(c0[1] + (c1[1] - c0[1]) * local)
            b = int(c0[2] + (c1[2] - c0[2]) * local)
            return rgb_to_hex((r, g, b))

    # fallback (shouldn't happen)
    return rgb_to_hex(GRADIENT_STOPS[-1][1])


@app.template_filter('rank_color')
def rank_color_filter(value):
    try:
        return get_color(float(value))
    except Exception:
        return "#2caf00"


@app.template_filter('contrast_color')
def contrast_color_filter(hex_color: str) -> str:
    """
    Given a background hex color, return either '#000000' or '#ffffff'
    depending on which has better contrast.
    """
    r, g, b = hex_to_rgb(hex_color)
    # compute relative luminance (0 = black … 1 = white)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    # light backgrounds (lum > 0.5) get black text; dark get white
    return '#000000' if lum > 0.5 else '#ffffff'


@app.template_filter('std_color')
def std_color_filter(value):
    return get_std_color(value)


@app.template_filter('retro_format')
def retro_format_filter(value: str):
    return value.replace('Retro', '<span class="retroText"><span class="bigger">R</span>ETRO</span>')


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/profile/')
def find_player():
    ipid = request.args.get("invalidpid", "0")

    try:
        ipid = int(ipid)
    except Exception:
        ipid = 0

    return render_template("findplayer.html", ipid=ipid)


def fetch_and_cache_rankings(endpoint, cache_key, process_function, pid):
    if app.config["USE_REDIS"] and redis_client:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)

            if pid == -1:
                return data
            return data.get(str(pid))

    try:
        response = requests.get(BASE_URL + endpoint)
        response.raise_for_status()

        data = process_function(response.text)

        # Store in cache
        if app.config["USE_REDIS"] and redis_client:
            redis_client.setex(cache_key, app.config["CACHE_EXPIRY_SECONDS"], json.dumps(data))

        if pid == -1:
            return data
        return data.get(str(pid))

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


def get_af_ranking(pid):
    return fetch_and_cache_rankings("afc.php?full=on", "mk7ppex:rankings:af", process_af_rankings, pid)


def get_arr_ranking(pid):
    return fetch_and_cache_rankings("arrc.php?full=on", "mk7ppex:rankings:arr", process_arr_rankings, pid)


def get_ttime_ranking(pid):
    return fetch_and_cache_rankings("totaltimec.php?full=on", "mk7ppex:rankings:ttime", process_ttime_rankings, pid)


def get_prsr_ranking(pid):
    return fetch_and_cache_rankings("prsrc.php?full=on", "mk7ppex:rankings:prsr", process_prsr_rankings, pid)


@app.route('/profile/<int:pid>', methods=['GET'])
def profile(pid):
    start = time.perf_counter()
    cache_key = f"mk7ppex:profile:{pid}"
    got_cached = False
    data = {}

    try:
        # Query the cache
        if app.config["USE_REDIS"] and redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                got_cached = True

        if not got_cached:
            # Fetch if not in cache
            response = requests.get(BASE_URL + "profile.php?pid=" + str(pid))
            response.raise_for_status()

            data = process_profile(response.text, pid)

            # Store in cache
            if app.config["USE_REDIS"] and redis_client:
                redis_client.setex(cache_key, app.config["CACHE_EXPIRY_SECONDS"], json.dumps(data))

        if data["notfound"]:
            return redirect(url_for('find_player') + "?invalidpid=" + str(pid))

        code = get_country_id(data["country"])

        fmt = "%Y-%m-%d"
        dates = [
            datetime.strptime(course["date"], fmt)
            for course in data["courses"].values() if course["hastime"]
        ]
        min_date = min(dates).strftime(fmt)
        max_date = datetime.now().strftime(fmt)

        cur_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + datetime.now().astimezone().tzname()

        return render_template('profile.html', data=data, pid=pid,
                               min_date=min_date, max_date=max_date, country_code=code,
                               load_time=math.ceil((time.perf_counter() - start) * 1000) / 1000, cur_date=cur_date)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500


@app.route('/leaderboard/af/', methods=['GET'])
def af_leaderboard():
    start = time.perf_counter()
    data = get_af_ranking(-1)

    cur_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + datetime.now().astimezone().tzname()

    print(data)

    return render_template('af_board.html', data=data,
                           load_time=math.ceil((time.perf_counter() - start) * 1000) / 1000, cur_date=cur_date)


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"])
