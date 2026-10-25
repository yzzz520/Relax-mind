import re

from ..vad import compute_vad
from .base import AnalysisResult


EMOTION_DIMENSIONS = (
    "喜悦",
    "期待",
    "平静",
    "温暖",
    "悲伤",
    "焦虑",
    "疲惫",
    "孤独",
)

KEYWORD_RULES = (
    (("面试", "工作", "offer"), "面试"),
    (("雨", "湿", "冷"), "潮湿"),
    (("累", "疲", "困"), "疲惫"),
    (("挂", "失败", "拒"), "挫败"),
    (("家", "想", "一个人"), "想家"),
    (("紧张", "睡", "焦虑"), "焦虑"),
    (("开心", "拿下", "成功"), "喜悦"),
)
FALLBACK_KEYWORDS = ("情绪", "此刻", "难以名状")

SAMPLES = (
    {
        "emotions": {
            "喜悦": 3,
            "期待": 18,
            "平静": 20,
            "温暖": 10,
            "悲伤": 78,
            "焦虑": 62,
            "疲惫": 80,
            "孤独": 55,
        },
        "keywords": ["面试", "下雨", "退堂鼓", "潮湿", "撑住"],
        "fineLabels": ["挫败", "无力", "被否定", "潮湿", "撑不住"],
        "comment": (
            "面试挂了，外面还下着雨——这两件事今天一起来了，"
            "难怪你觉得累。\n"
            "别灰心，这场雨总会停的。听听这首 Lo-fi，就当是我陪着你。"
        ),
    },
    {
        "emotions": {
            "喜悦": 88,
            "期待": 85,
            "平静": 35,
            "温暖": 70,
            "悲伤": 5,
            "焦虑": 10,
            "疲惫": 15,
            "孤独": 0,
        },
        "keywords": ["offer", "终于", "松一口气"],
        "fineLabels": ["狂喜", "被肯定", "释然", "想哭", "值得"],
        "comment": (
            "拿到 offer 了，想大喊一声也很正常。\n"
            "有些开心是需要被放大的，让这首歌陪你一起喊出来。"
        ),
    },
    {
        "emotions": {
            "喜悦": 10,
            "期待": 30,
            "平静": 60,
            "温暖": 25,
            "悲伤": 58,
            "焦虑": 25,
            "疲惫": 40,
            "孤独": 82,
        },
        "keywords": ["异地", "夜晚", "想家", "窗外"],
        "fineLabels": ["想家", "空落", "挂念", "安静", "独自"],
        "comment": (
            "一个人在外地，晚上想起家来是躲不掉的。\n"
            "这首民谣不吵，就让它陪着你待一会儿。"
        ),
    },
    {
        "emotions": {
            "喜悦": 5,
            "期待": 45,
            "平静": 10,
            "温暖": 15,
            "悲伤": 30,
            "焦虑": 88,
            "疲惫": 70,
            "孤独": 35,
        },
        "keywords": ["答辩", "失眠", "紧张", "明天"],
        "fineLabels": ["紧张", "心跳", "怕搞砸", "硬撑", "失眠"],
        "comment": (
            "明天要答辩，紧张到睡不着，这说明你很在乎。\n"
            "别硬扛，先让节奏慢下来，再慢慢睡。"
        ),
    },
    {
        "emotions": {
            "喜悦": 40,
            "期待": 30,
            "平静": 82,
            "温暖": 75,
            "悲伤": 0,
            "焦虑": 5,
            "疲惫": 10,
            "孤独": 5,
        },
        "keywords": ["阳光", "被子", "安静", "暖"],
        "fineLabels": ["松弛", "满足", "安心", "慢下来", "踏实"],
        "comment": (
            "挺好的，这样安静的一刻值得被记住。"
            "让这段旋律陪你把这份松弛多留一会儿。"
        ),
    },
)


def select_sample(text: str) -> dict:
    normalized = text.lower()
    if re.search(r"阳光|晒|舒服|安静|慢慢", normalized):
        return SAMPLES[4]
    if re.search(r"offer|拿下|成功|开心", normalized):
        return SAMPLES[1]
    if re.search(r"紧张|睡|答辩|焦虑", normalized):
        return SAMPLES[3]
    if re.search(r"家|一个人|想", normalized):
        return SAMPLES[2]
    return SAMPLES[0]


def extract_keywords(text: str) -> list[str]:
    normalized = text.lower()
    matched = [
        keyword
        for terms, keyword in KEYWORD_RULES
        if any(term in normalized for term in terms)
    ][:3]
    if not matched:
        return list(FALLBACK_KEYWORDS)
    for keyword in FALLBACK_KEYWORDS:
        if len(matched) >= 2:
            break
        if keyword not in matched:
            matched.append(keyword)
    return matched


class MockAnalyzer:
    async def analyze(self, text: str) -> AnalysisResult:
        sample = select_sample(text)
        valence, arousal = compute_vad(sample["emotions"])
        return AnalysisResult(
            emotions=dict(sample["emotions"]),
            valence=valence,
            arousal=arousal,
            keywords=list(sample["keywords"]),
            fine_labels=list(sample["fineLabels"]),
            comment=str(sample["comment"]),
        )
