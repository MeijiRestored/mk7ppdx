import math
import re


def get_abbr_name(track):
    abbrs = {
        "Toad Circuit": "TC",
        "Daisy Hills": "DH",
        "Cheep Cheep Lagoon": "CCL",
        "Shy Guy Bazaar": "SGB",
        "Wuhu Loop": "WL",
        "Mario Circuit": "MC",
        "Music Park": "MP",
        "Rock Rock Mountain": "RRM",
        "Piranha Plant Slide": "PPS",
        "Wario Shipyard": "WS",
        "Neo Bowser City": "NBC",
        "Maka Wuhu": "MW",
        "DK Jungle": "DKJ",
        "Rosalina's Ice World": "RIW",
        "Bowser's Castle": "BC",
        "Rainbow Road": "RR",
        "Retro Luigi Raceway": "rLR",
        "Retro Bowser Castle 1": "rBC1",
        "Retro Mushroom Gorge": "rMG",
        "Retro Luigi's Mansion": "rLM",
        "Retro Koopa Troopa Beach": "rKTB",
        "Retro Mario Circuit 2": "rMC2",
        "Retro Coconut Mall": "rCM",
        "Retro Waluigi Pinball": "rWP",
        "Retro Kalimari Desert": "rKD",
        "Retro DK Pass": "rDKP",
        "Retro Daisy Cruiser": "rDC",
        "Retro Maple Treeway": "rMT",
        "Retro Koopa Cape": "rKC",
        "Retro Dino Dino Jungle": "rDDJ",
        "Retro Airship Fortress": "rAF",
        "Retro Rainbow Road": "rRR"
    }

    return abbrs[track]


def get_color(value: float) -> str:
    thresholds = {
        500: "#b2ff5c",
        400: "#ffff5c",
        300: "#ffc447",
        200: "#ff8a55",
        150: "#ff595c",
        100: "#ff4dac",
        50: "#e25eff",
        25: "#984bff",
        10: "#524bff",
        1: "#ff0000"
    }
    other_color = "#2caf00"

    try:
        v = float(value)
    except (TypeError, ValueError):
        return other_color

    if v < 1 or v > 500:
        return other_color

    if v == 1:
        return thresholds[1]

    if v in thresholds:
        r, g, b = hex_to_rgb(thresholds[v])
        r_d = int(r * 0.65)
        g_d = int(g * 0.65)
        b_d = int(b * 0.65)

        return rgb_to_hex((r_d, g_d, b_d))


    # Sort thresholds descending to find correct range
    sorted_thresholds = sorted(thresholds.keys(), reverse=True)
    for i in range(len(sorted_thresholds) - 1):
        upper = sorted_thresholds[i]
        lower = sorted_thresholds[i + 1]
        if lower < v < upper:
            base_hex = thresholds[upper]
            span = upper - lower
            ratio = ((v - lower) / span) * 0.35

            r, g, b = hex_to_rgb(base_hex)
            r_d = int(r * (1 - ratio))
            g_d = int(g * (1 - ratio))
            b_d = int(b * (1 - ratio))

            return rgb_to_hex((r_d, g_d, b_d))

    return other_color  # fallback (shouldn't happen)


def get_country_id(country_name: str) -> str:
    country_code_map = {
        "Australia": "au",
        "Austria": "at",
        "Belgium": "be",
        "Brazil": "br",
        "Bulgaria": "bg",
        "Cameroon": "cm",
        "Canada": "ca",
        "Colombia": "co",
        "Finland": "fi",
        "France": "fr",
        "Germany": "de",
        "Greece": "gr",
        "Ireland": "ie",
        "Israel": "il",
        "Italy": "it",
        "Japan": "jp",
        "Latvia": "lv",
        "Luxembourg": "lu",
        "Malaysia": "my",
        "Mexico": "mx",
        "Netherlands": "nl",
        "New Zealand": "nz",
        "Norway": "no",
        "Panama": "pa",
        "Philippines": "ph",
        "Poland": "pl",
        "Portugal": "pt",
        "Russia": "ru",
        "Singapore": "sg",
        "South Africa": "za",
        "South Korea": "kr",
        "Spain": "es",
        "Sweden": "se",
        "Switzerland": "ch",
        "UK": "gb",
        "USA": "us",
        "Unknown": "un",
    }

    code = country_code_map.get(country_name)
    if code:
        return code
    else:
        return "un"


def get_std_color(value):
    value = math.ceil(value)

    scale = {
        0: "#ffd700",
        1: "#8df5ff",
        2: "#87e7f0",
        3: "#73d7e1",
        4: "#6cc8d2",
        5: "#24d200",
        6: "#24c300",
        7: "#24b400",
        8: "#1ea500",
        9: "#864ce9",
        10: "#7a4bdc",
        11: "#7343cd",
        12: "#6941be",
        13: "#c70104",
        14: "#b90104",
        15: "#a90104",
        16: "#9b0104",
        17: "#3a9ca7",
        18: "#3c909b",
        19: "#38818c",
        20: "#28737d",
        21: "#c86d00",
        22: "#b95d00",
        23: "#ab5a00",
        24: "#9b5100",
        25: "#ffc6ff",
        26: "#f0b7f0",
        27: "#dfaadf",
        28: "#d29fd2",
        29: "#c8c8c8",
        30: "#b8b8b8",
        31: "#a9a9a9",
        32: "#9a9a9a",
    }

    other_color = "#fdfdfd"

    if 0 <= value <= 32:
        return scale[value]
    else:
        return other_color


def get_std_name(value):

    value = math.ceil(value)

    names = {
        0: "God",
        1: "Myth A",
        2: "Myth B",
        3: "Myth C",
        4: "Myth D",
        5: "Titan A",
        6: "Titan B",
        7: "Titan C",
        8: "Titan D",
        9: "King A",
        10: "King B",
        11: "King C",
        12: "King D",
        13: "Hero A",
        14: "Hero B",
        15: "Hero C",
        16: "Hero D",
        17: "Exp A",
        18: "Exp B",
        19: "Exp C",
        20: "Exp D",
        21: "Adv A",
        22: "Adv B",
        23: "Adv C",
        24: "Adv D",
        25: "Int A",
        26: "Int B",
        27: "Int C",
        28: "Int D",
        29: "Beg A",
        30: "Beg B",
        31: "Beg C",
        32: "Beg D"
    }

    if 0 <= value <= 32:
        return names[value]
    else:
        return "noobz"


def hex_to_rgb(hexstr: str):
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def parse_time(time_str: str) -> float:
    match = re.match(r"(\d+)'(\d+)\"(\d+)", time_str)

    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        milliseconds = int(match.group(3))

        total_seconds = minutes * 60 + seconds + milliseconds / 1000

        return total_seconds

    else:
        raise ValueError("Invalid time format")


def format_time(total_seconds: float) -> str:
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
    return f"{minutes}'{seconds:02}\"{milliseconds:03}"


def extract_pid(pid_href: str) -> int:
    """
    Safely extract a numeric `pid` from a hyperlink.
    Returns 0 if the pid is missing or invalid.
    """
    if "pid=" in pid_href:
        try:
            return int(pid_href.split("pid=")[1])
        except ValueError:
            pass
    return 0

