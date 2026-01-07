from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lunar_python import Solar


GAN_ELEMENT = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

ZHI_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}


@dataclass(frozen=True)
class Pillar:
    gan: str
    zhi: str
    gan_element: str
    zhi_element: str

    @property
    def text(self) -> str:
        return f"{self.gan}{self.zhi}"


def _pillar_from_ganzhi(gan: str, zhi: str) -> Pillar:
    return Pillar(
        gan=gan,
        zhi=zhi,
        gan_element=GAN_ELEMENT.get(gan, "？"),
        zhi_element=ZHI_ELEMENT.get(zhi, "？"),
    )


def compute_bazi(dt: datetime) -> dict:
    """
    使用 lunar_python 以陽曆時間排四柱（年/月/日/時）。
    注意：此處不做真太陽時/時區校正（城市僅作為展示）。
    """
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    year = _pillar_from_ganzhi(ec.getYearGan(), ec.getYearZhi())
    month = _pillar_from_ganzhi(ec.getMonthGan(), ec.getMonthZhi())
    day = _pillar_from_ganzhi(ec.getDayGan(), ec.getDayZhi())
    time = _pillar_from_ganzhi(ec.getTimeGan(), ec.getTimeZhi())

    pillars = {"year": year, "month": month, "day": day, "time": time}

    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for p in pillars.values():
        if p.gan_element in counts:
            counts[p.gan_element] += 1
        if p.zhi_element in counts:
            counts[p.zhi_element] += 1

    total = sum(counts.values()) or 1
    perc = {k: round(v * 100 / total, 1) for k, v in counts.items()}

    day_master_gan = day.gan
    day_master_element = day.gan_element

    key = "".join([year.text, month.text, day.text, time.text])

    return {
        "key": key,
        "pillars": {
            "year": _pillar_dict(year),
            "month": _pillar_dict(month),
            "day": _pillar_dict(day),
            "time": _pillar_dict(time),
        },
        "dayMaster": {"gan": day_master_gan, "element": day_master_element},
        "fiveElements": {"counts": counts, "percent": perc},
    }


def _pillar_dict(p: Pillar) -> dict:
    return {
        "gan": p.gan,
        "zhi": p.zhi,
        "text": p.text,
        "ganElement": p.gan_element,
        "zhiElement": p.zhi_element,
    }

