from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import date

from lunar_python import Solar


GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CTRL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


THEME = {
    "木": {
        "label": "成長/學習/人脈",
        "yes_templates": [
            "過去 5 年內，你是否有明顯的學習/考證/進修或技能轉向？",
            "過去 5 年內，你是否出現過人際圈擴張、結識關鍵貴人的機會？",
        ],
        "no_templates": [
            "過去 5 年內，你是否大多維持原本步調，較少主動學新東西或換跑道？",
        ],
        "tips": [
            "主動學習、建立作品集/證照會放大運勢紅利。",
            "與其硬拚，不如先把基礎功練穩、拉長線。",
        ],
    },
    "火": {
        "label": "曝光/名聲/情緒動能",
        "yes_templates": [
            "過去 5 年內，你是否有一段時間特別忙、事情密集、需要被看見或上台出面？",
            "過去 5 年內，你是否更在意自我表達、社群曝光或職場能見度？",
        ],
        "no_templates": [
            "過去 5 年內，你是否偏低調，較少主動爭取曝光或舞台？",
        ],
        "tips": [
            "把「可被看見」做成可複用的系統：履歷、作品、案例、社群內容。",
            "情緒與睡眠是火的開關，先穩住作息再談衝刺。",
        ],
    },
    "土": {
        "label": "穩定/資產/責任壓力",
        "yes_templates": [
            "過去 5 年內，你是否有搬家/裝修/買賣房車或更在意資產配置？",
            "過去 5 年內，你是否承擔更多家庭/組織責任，壓力感上升？",
        ],
        "no_templates": [
            "過去 5 年內，你是否較少涉及房產/長期承諾類的大決策？",
        ],
        "tips": [
            "用預算與現金流管理，把安全感落地成數字。",
            "別把所有責任一肩扛，建立可交付/可委派的流程。",
        ],
    },
    "金": {
        "label": "規則/財務/決斷與斷捨離",
        "yes_templates": [
            "過去 5 年內，你是否有明顯的「斷捨離」：結束一段關係/合作/工作或砍掉一個方向？",
            "過去 5 年內，你是否更重視制度、合約、績效或財務紀律？",
        ],
        "no_templates": [
            "過去 5 年內，你是否多半隨遇而安，較少做果斷切割或規則化管理？",
        ],
        "tips": [
            "金旺靠紀律出成果：合約、流程、KPI、記帳都會很加分。",
            "該收口就收口：少做多成，比多線並進更順。",
        ],
    },
    "水": {
        "label": "變動/流動/旅行與思考",
        "yes_templates": [
            "過去 5 年內，你是否有頻繁出差、跨城市移動、或生活節奏明顯變動？",
            "過去 5 年內，你是否經歷過一段「想很多」或方向不確定、需要重新定位的時期？",
        ],
        "no_templates": [
            "過去 5 年內，你是否大多在同一環境，變動不算大？",
        ],
        "tips": [
            "把變動變成優勢：建立可搬移的能力（語言、工具、遠端/跨域技能）。",
            "用寫作/記錄整理思緒，水才不會變成焦慮。",
        ],
    },
}


@dataclass(frozen=True)
class VerificationQuestion:
    id: str
    text: str
    expected_yes: bool
    rationale: str


def _rng_from_key(key: str) -> random.Random:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    seed = int(h[:16], 16)
    return random.Random(seed)


def _missing_and_excess(counts: dict[str, int]) -> tuple[list[str], list[str]]:
    missing = [e for e, c in counts.items() if c == 0]
    # 「偏旺」簡化：>=3 視為偏旺（共 8 個位置：四柱*2）
    excess = [e for e, c in counts.items() if c >= 3]
    return missing, excess


def generate_verification_questions(chart: dict, today: date) -> list[VerificationQuestion]:
    key = chart["key"]
    counts = chart["fiveElements"]["counts"]
    dm_element = chart["dayMaster"]["element"]
    missing, excess = _missing_and_excess(counts)

    rng = _rng_from_key(key + f":{today.isoformat()}")

    candidates: list[VerificationQuestion] = []

    # 1) 依五行缺/旺提問（訊號相對強）
    for e in missing:
        t = rng.choice(THEME[e]["yes_templates"])
        candidates.append(
            VerificationQuestion(
                id=f"miss_{e}",
                text=t,
                expected_yes=True,
                rationale=f"五行偏缺（{e}），近年遇到補{e}的年份/情境時，常以對應主題事件呈現。",
            )
        )
    for e in excess:
        t = rng.choice(THEME[e]["yes_templates"])
        candidates.append(
            VerificationQuestion(
                id=f"excess_{e}",
                text=t,
                expected_yes=True,
                rationale=f"五行偏旺（{e}），過去數年容易在對應領域出現強烈感受或事件。",
            )
        )

    # 2) 依日主強弱（簡化）
    dm_count = counts.get(dm_element, 0)
    avg = sum(counts.values()) / 5
    dm_is_weak = dm_count <= avg
    if dm_is_weak:
        # 弱：更需要支援（同元素/生我）
        support = [dm_element, _generator_of(dm_element)]
        e = rng.choice(support)
        t = rng.choice(THEME[e]["yes_templates"])
        candidates.append(
            VerificationQuestion(
                id=f"dm_support_{e}",
                text=t,
                expected_yes=True,
                rationale=f"日主偏弱，遇到{e}相關主題時，往往是推動你前進的關鍵事件。",
            )
        )
    else:
        # 強：更常出現斷捨離/規則化/輸出
        e = rng.choice(["金", _output_of(dm_element)])
        t = rng.choice(THEME[e]["yes_templates"])
        candidates.append(
            VerificationQuestion(
                id=f"dm_output_{e}",
                text=t,
                expected_yes=True,
                rationale=f"日主偏強，近年更容易在{e}的主題上做取捨與輸出。",
            )
        )

    # 3) 補一題「反向」降低全 YES 的僵硬感
    # 選一個中庸元素做否定預期
    neutral_pool = [e for e in ["木", "火", "土", "金", "水"] if e not in missing and e not in excess]
    if neutral_pool:
        e = rng.choice(neutral_pool)
        t = rng.choice(THEME[e]["no_templates"])
        candidates.append(
            VerificationQuestion(
                id=f"neutral_no_{e}",
                text=t,
                expected_yes=False,
                rationale=f"{e}較中性，通常不會以強事件主導過去 5 年。",
            )
        )

    rng.shuffle(candidates)
    # 固定輸出 5 題（不足則補題）
    questions = candidates[:5]
    while len(questions) < 5:
        e = rng.choice(["木", "火", "土", "金", "水"])
        t = rng.choice(THEME[e]["yes_templates"])
        questions.append(
            VerificationQuestion(
                id=f"fill_{e}_{len(questions)}",
                text=t,
                expected_yes=bool(rng.getrandbits(1)),
                rationale="補題：用於校準你的生活主題。",
            )
        )

    return questions


def build_future_fortune(chart: dict, start_year: int, years: int, match_score: float) -> dict:
    counts = chart["fiveElements"]["counts"]
    dm_element = chart["dayMaster"]["element"]
    dm_count = counts.get(dm_element, 0)
    avg = sum(counts.values()) / 5
    dm_is_weak = dm_count <= avg

    beneficial = set()
    caution = set()
    if dm_is_weak:
        beneficial.update([dm_element, _generator_of(dm_element)])
        caution.add(_controller_of(dm_element))
    else:
        beneficial.update([_controller_of(dm_element), _output_of(dm_element)])
        caution.add(_generator_of(dm_element))

    timeline = []
    for y in range(start_year, start_year + years):
        y_ele = _year_element(y)
        if y_ele in beneficial:
            level = "順勢"
        elif y_ele in caution:
            level = "保守"
        else:
            level = "平穩"
        timeline.append(
            {
                "year": y,
                "yearElement": y_ele,
                "level": level,
                "advice": _year_advice(y_ele, level),
            }
        )

    missing, excess = _missing_and_excess(counts)
    focus = []
    if missing:
        focus.append(f"五行偏缺：{'、'.join(missing)}（建議刻意補足其對應生活策略）")
    if excess:
        focus.append(f"五行偏旺：{'、'.join(excess)}（建議用規則/節奏把能量導向成果）")
    if not focus:
        focus.append("五行分佈較平均，屬於「靠選擇」比「靠運」更明顯的命格。")

    confidence = "高" if match_score >= 0.8 else "中" if match_score >= 0.6 else "低"

    tips = []
    # 給 1-2 個最關鍵元素建議（缺的優先，否則旺的）
    for e in (missing + excess)[:2]:
        tips.extend(THEME[e]["tips"][:1])
    if not tips:
        tips.append("把目標拆成季度里程碑，穩定複利會比短線爆發更有效。")

    return {
        "confidence": confidence,
        "matchScore": round(match_score, 3),
        "summary": {
            "dayMasterElement": dm_element,
            "dayMasterStrength": "偏弱" if dm_is_weak else "偏強",
            "focus": focus,
            "tips": tips,
        },
        "timeline": timeline,
        "note": "此為八字與五行的簡化推演，用於自我反思與規劃；不構成醫療、法律或投資建議。",
    }


def _generator_of(e: str) -> str:
    # 生我：找誰生 e
    for k, v in GEN.items():
        if v == e:
            return k
    return "？"


def _output_of(e: str) -> str:
    # 我生：e 生成什麼
    return GEN.get(e, "？")


def _controller_of(e: str) -> str:
    # 克我：找誰克 e（CTRL[k]=被 k 所克）
    for k, v in CTRL.items():
        if v == e:
            return k
    return "？"


def _year_element(year: int) -> str:
    # 以每年 2/15（立春後）取該年的年干五行，避免跨年邊界
    solar = Solar.fromYmd(year, 2, 15)
    gan = solar.getLunar().getEightChar().getYearGan()
    # Gan -> Element
    if gan in ("甲", "乙"):
        return "木"
    if gan in ("丙", "丁"):
        return "火"
    if gan in ("戊", "己"):
        return "土"
    if gan in ("庚", "辛"):
        return "金"
    if gan in ("壬", "癸"):
        return "水"
    return "？"


def _year_advice(ele: str, level: str) -> str:
    base = THEME.get(ele, {}).get("label", "")
    if level == "順勢":
        return f"{base}偏旺，適合主動出擊、做決策、擴張影響力。"
    if level == "保守":
        return f"{base}帶來壓力測試，適合守成、控風險、先補短板再加速。"
    return f"{base}屬於可控變量年，重點在選對方向並保持節奏。"

