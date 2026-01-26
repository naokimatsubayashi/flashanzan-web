from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
import random

# 段級位データ（桁数=digits / 口数=terms / 秒数=seconds）
LEVELS = [
    {"name": "10級", "digits": 1, "terms": 4,  "seconds": 4},
    {"name": "9級",  "digits": 1, "terms": 6,  "seconds": 6},
    {"name": "8級",  "digits": 1, "terms": 8,  "seconds": 8},
    {"name": "7級",  "digits": 1, "terms": 10, "seconds": 10},
    {"name": "6級",  "digits": 2, "terms": 3,  "seconds": 3},
    {"name": "5級",  "digits": 2, "terms": 4,  "seconds": 4},
    {"name": "4級",  "digits": 2, "terms": 5,  "seconds": 5},
    {"name": "3級",  "digits": 2, "terms": 7,  "seconds": 7},
    {"name": "2級",  "digits": 2, "terms": 10, "seconds": 10},
    {"name": "1級",  "digits": 3, "terms": 5,  "seconds": 5},
    {"name": "初段",  "digits": 3, "terms": 7,  "seconds": 7},
    {"name": "二段",  "digits": 3, "terms": 10, "seconds": 10},
    {"name": "三段",  "digits": 3, "terms": 10, "seconds": 7},
    {"name": "四段",  "digits": 3, "terms": 10, "seconds": 5},
    {"name": "五段",  "digits": 3, "terms": 10, "seconds": 4.5},
    {"name": "六段",  "digits": 3, "terms": 10, "seconds": 4},
    {"name": "七段",  "digits": 3, "terms": 10, "seconds": 3.5},
    {"name": "八段",  "digits": 3, "terms": 10, "seconds": 3},
    {"name": "九段",  "digits": 3, "terms": 15, "seconds": 4},
    {"name": "十段",  "digits": 3, "terms": 15, "seconds": 3},
]

LEVEL_MAP = {x["name"]: x for x in LEVELS}


def home(request):
    # 段級位のボタン一覧ページ（select.html）
    return render(request, "core/select.html", {"levels": LEVELS})


def play(request, level):
    """
    クリックされたら即出題へ飛ばす（要望：ボタン押したら即出題）
    """
    if level not in LEVEL_MAP:
        return HttpResponseBadRequest("Invalid level")

    # セッション初期化
    request.session["level"] = level
    request.session["q_index"] = 1          # 1〜10
    request.session["correct_count"] = 0
    request.session["history"] = []         # [{q_index, correct_answer, user_answer, is_correct}]
    request.session.modified = True

    return redirect("quiz", level=level)


def _generate_one_question(level_conf):
    digits = level_conf["digits"]
    terms = level_conf["terms"]

    # digits桁の数字をterms個（符号は基本プラス）
    nums = [
        random.randint(10 ** (digits - 1), 10 ** digits - 1) if digits > 1 else random.randint(0, 9)
        for _ in range(terms)
    ]
    correct = sum(nums)
    return nums, correct


def quiz(request, level):
    """
    出題ページ（数字表示＋電卓入力）
    """
    if level not in LEVEL_MAP:
        return HttpResponseBadRequest("Invalid level")

    conf = LEVEL_MAP[level]
    q_index = int(request.session.get("q_index", 1))

    # 10問終わっていたら結果へ
    if q_index > 10:
        return redirect("result", level=level)

    # 1問分の数字列と正解を生成してセッションに保持
    nums, correct = _generate_one_question(conf)
    request.session["current_nums"] = nums
    request.session["current_correct"] = correct
    request.session["level"] = level
    request.session.modified = True

    return render(request, "core/quiz.html", {
        "level": level,
        "digits": conf["digits"],
        "terms": conf["terms"],
        "seconds": conf["seconds"],
        "q_index": q_index,
        "total": 10,
        "nums": nums,          # JSで順次表示
        # ※テンプレ側が {{ number }} を参照している場合でも落ちないよう空を渡す
        "number": "",
    })


def feedback(request, level):
    """
    1問解答後の「●×」画面（音もここで鳴らす）
    """
    if request.method != "POST":
        return redirect("quiz", level=level)

    if level not in LEVEL_MAP:
        return HttpResponseBadRequest("Invalid level")

    user_answer = request.POST.get("answer", "").strip()
    try:
        user_val = int(user_answer)
    except Exception:
        user_val = None

    correct = request.session.get("current_correct", None)
    q_index = int(request.session.get("q_index", 1))

    is_correct = (user_val is not None and correct is not None and user_val == int(correct))

    # 集計
    if is_correct:
        request.session["correct_count"] = int(request.session.get("correct_count", 0)) + 1

    history = request.session.get("history", [])
    history.append({
        "q_index": q_index,
        "correct_answer": int(correct) if correct is not None else None,
        "user_answer": user_answer,
        "is_correct": bool(is_correct),
    })
    request.session["history"] = history

    # 次へ
    request.session["q_index"] = q_index + 1
    request.session.modified = True

    return render(request, "core/feedback.html", {
        "level": level,
        "q_index": q_index,
        "total": 10,
        "correct_answer": int(correct) if correct is not None else "",
        "user_answer": user_answer,
        "is_correct": is_correct,
    })


def result(request, level):
    if level not in LEVEL_MAP:
        return HttpResponseBadRequest("Invalid level")

    correct_count = int(request.session.get("correct_count", 0))
    history = request.session.get("history", [])
    passed = correct_count >= 7

    # ★ 追加：テンプレが details を参照しても壊れないように両方渡す
    details = []
    for item in history:
        details.append({
            "no": item.get("q_index"),
            "user_answer": item.get("user_answer", ""),
            "correct_answer": item.get("correct_answer", ""),
            "is_correct": bool(item.get("is_correct", False)),
        })

    return render(request, "core/result.html", {
        "level": level,
        "correct_count": correct_count,
        "total": 10,
        "passed": passed,
        "history": history,     # 旧方式
        "details": details,     # 新方式（一覧表示用）
    })


def abort(request):
    """
    中断してトップへ
    """
    for k in ["level", "q_index", "correct_count", "history", "current_nums", "current_correct"]:
        if k in request.session:
            del request.session[k]
    request.session.modified = True
    return redirect("home")
