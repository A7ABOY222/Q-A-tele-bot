import json
import logging
import os
import random
import asyncio
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Questions ─────────────────────────────────────────────────────────────────
QUESTIONS: list[dict] = json.loads(
    Path("questions.json").read_text(encoding="utf-8")
)
logger.info(f"Loaded {len(QUESTIONS)} questions")

# ── Leaderboard (persisted to leaderboard.json) ───────────────────────────────
LB_PATH = Path("leaderboard.json")


def load_leaderboard() -> dict:
    if LB_PATH.exists():
        try:
            return json.loads(LB_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_leaderboard(lb: dict) -> None:
    try:
        LB_PATH.write_text(
            json.dumps(lb, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to save leaderboard: {e}")


leaderboard: dict = load_leaderboard()


def record_score(user_id: int, name: str, s: dict) -> bool:
    """Save quiz result; returns True if it's a new personal best."""
    total = s["correct"] + s["incorrect"]
    if total == 0:
        return False
    pct = round(s["correct"] / total * 100)
    uid = str(user_id)
    existing = leaderboard.get(uid)
    is_new_best = not existing or s["correct"] > existing["best_correct"] or (
        s["correct"] == existing["best_correct"] and pct > existing["best_pct"]
    )
    leaderboard[uid] = {
        "user_id": user_id,
        "name": name,
        "best_correct": s["correct"] if is_new_best else existing["best_correct"],
        "best_total": total if is_new_best else existing["best_total"],
        "best_pct": pct if is_new_best else existing["best_pct"],
        "games_played": (existing["games_played"] if existing else 0) + 1,
        "all_time_correct": (existing["all_time_correct"] if existing else 0) + s["correct"],
    }
    save_leaderboard(leaderboard)
    return is_new_best


def top_text() -> str:
    if not leaderboard:
        return "📋 هێشتا کەس تۆمار نەکردووە. /quiz بکە و یەکەمین بە!"
    ranked = sorted(
        leaderboard.values(),
        key=lambda e: (-e["best_correct"], -e["best_pct"]),
    )
    medals = ["🥇", "🥈", "🥉"]
    rows = []
    for i, e in enumerate(ranked[:10]):
        rank = medals[i] if i < 3 else f"{i + 1}\\."
        rows.append(
            f"{rank} *{e['name']}*\n"
            f"    ✅ {e['best_correct']}/{e['best_total']} — {e['best_pct']}% \\| 🎮 {e['games_played']} یاری"
        )
    return "🏆 *سەرەوەی ١٠ یاریزانی باشترین*\n\n" + "\n\n".join(rows)


# ── Sessions (in-memory) ──────────────────────────────────────────────────────
sessions: dict[int, dict] = {}


def get_session(user_id: int) -> dict:
    if user_id not in sessions:
        sessions[user_id] = {
            "active": False,
            "shuffled": [],
            "current_index": 0,
            "correct": 0,
            "incorrect": 0,
            "waiting": False,
            "current_opts": None,
        }
    return sessions[user_id]


# ── Helpers ───────────────────────────────────────────────────────────────────
def stats_text(s: dict) -> str:
    total = s["correct"] + s["incorrect"]
    pct = round(s["correct"] / total * 100) if total > 0 else 0
    return (
        "📊 *ئەنجامەکانت*\n\n"
        f"❓ کۆی پرسیارەکان: *{total}*\n"
        f"✅ وەڵامی دروست: *{s['correct']}*\n"
        f"❌ وەڵامی هەڵە: *{s['incorrect']}*\n"
        f"🎯 ڕێژەی سەرکەوتن: *{pct}%*"
    )


def question_keyboard(opts: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"A: {opts['A']}", callback_data="ans_A"),
            InlineKeyboardButton(f"B: {opts['B']}", callback_data="ans_B"),
        ],
        [
            InlineKeyboardButton(f"C: {opts['C']}", callback_data="ans_C"),
            InlineKeyboardButton(f"D: {opts['D']}", callback_data="ans_D"),
        ],
        [InlineKeyboardButton("⏹ وەستان", callback_data="stop_quiz")],
    ])


def result_keyboard(opts: dict, chosen: str, answer: str) -> InlineKeyboardMarkup:
    letters = ["A", "B", "C", "D"]
    btns = []
    for letter in letters:
        text = opts[letter]
        if text == answer:
            label = f"✅ {letter}: {text}"
        elif letter == chosen:
            label = f"❌ {letter}: {text}"
        else:
            label = f"{letter}: {text}"
        btns.append(InlineKeyboardButton(label, callback_data=f"done_{letter}"))
    return InlineKeyboardMarkup([[btns[0], btns[1]], [btns[2], btns[3]]])


async def send_question(context: ContextTypes.DEFAULT_TYPE, chat_id: int, s: dict) -> None:
    q = s["shuffled"][s["current_index"]]
    vals = list(q["options"].values())
    random.shuffle(vals)
    opts = {"A": vals[0], "B": vals[1], "C": vals[2], "D": vals[3]}
    s["current_opts"] = opts
    s["waiting"] = True

    num = s["current_index"] + 1
    total = len(s["shuffled"])
    text = (
        f"📚 *پرسیار {num} لە {total}*\n"
        f"🏷 {q['category']} \\| {q['difficulty']}\n\n"
        f"{q['question']}"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="MarkdownV2",
        reply_markup=question_keyboard(opts),
    )


def user_name(user) -> str:
    return " ".join(filter(None, [user.first_name, user.last_name]))


# ── Command handlers ──────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_session(update.effective_user.id)
    msg = (
        f"سڵاو {update.effective_user.first_name}\\! 👋\n\n"
        f"بخێرهاتی بۆ *کویزی زمانی کوردی* 🎓\n\n"
        f"{len(QUESTIONS)} پرسیاری کوردی لەم بۆتەدا هەیە\\.\n\n"
        f"فەرمانەکان:\n"
        f"/quiz — دەستپێکردنی کویز\n"
        f"/stats — بینینی ئەنجامەکانت\n"
        f"/top — لیستی باشترین یاریزانان\n"
        f"/stop — وەستاندنی کویز"
    )
    if s["active"]:
        msg += "\n\n⚡ کویزێکت هەیە\\. /quiz بکە بۆ بەردەوامبوون\\."
    await update.message.reply_text(msg, parse_mode="MarkdownV2")


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_session(update.effective_user.id)
    if not s["active"]:
        shuffled = QUESTIONS.copy()
        random.shuffle(shuffled)
        s.update({
            "active": True,
            "shuffled": shuffled,
            "current_index": 0,
            "correct": 0,
            "incorrect": 0,
            "waiting": False,
            "current_opts": None,
        })
        await update.message.reply_text(
            f"🚀 کویز دەستپێدەکات\\! {len(shuffled)} پرسیار لەبەردەستتدا\\.\n\nبە سەرکەوتنی\\! 💪",
            parse_mode="MarkdownV2",
        )
    else:
        await update.message.reply_text("▶️ بەردەوامبوون\\.\\.\\.", parse_mode="MarkdownV2")
    await send_question(context, update.effective_chat.id, s)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_session(update.effective_user.id)
    if s["correct"] + s["incorrect"] == 0:
        await update.message.reply_text(
            "هێشتا پرسیارێکت وەڵام نەداوە\\. /quiz بکە بۆ دەستپێکردن\\.",
            parse_mode="MarkdownV2",
        )
        return
    await update.message.reply_text(stats_text(s), parse_mode="Markdown")


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(top_text(), parse_mode="MarkdownV2")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    s = get_session(uid)
    if not s["active"] and s["correct"] + s["incorrect"] == 0:
        await update.message.reply_text(
            "کویزێک دەستپێنەکردووە\\. /quiz بکە بۆ دەستپێکردن\\.",
            parse_mode="MarkdownV2",
        )
        return
    s["active"] = False
    s["waiting"] = False
    is_new_best = record_score(uid, user_name(update.effective_user), s)
    msg = f"⏹ کویز وەستا\\.\n\n{stats_text(s)}\n\n/quiz بکە بۆ کویزێکی نوێ\\."
    if is_new_best:
        msg += "\n\n🏆 *تۆماری تازەی کەسیت داناوە\\!*"
    await update.message.reply_text(msg, parse_mode="MarkdownV2")


# ── Callback handlers ─────────────────────────────────────────────────────────
async def on_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    s = get_session(uid)

    if not s["active"] or not s["waiting"]:
        await query.message.reply_text(
            "تکایە /quiz بکە بۆ دەستپێکردنی کویز\\.", parse_mode="MarkdownV2"
        )
        return

    chosen = query.data[-1]          # last char: A / B / C / D
    q = s["shuffled"][s["current_index"]]
    opts = s["current_opts"]
    is_correct = opts[chosen] == q["answer"]
    s["waiting"] = False

    if is_correct:
        s["correct"] += 1
    else:
        s["incorrect"] += 1

    # Update buttons in-place
    try:
        await query.edit_message_reply_markup(
            reply_markup=result_keyboard(opts, chosen, q["answer"])
        )
    except Exception:
        pass

    # Result message
    if is_correct:
        await query.message.reply_text(
            f"✅ *دروستە\\!*\n\n{stats_text(s)}", parse_mode="MarkdownV2"
        )
    else:
        correct_letter = next(l for l in ["A", "B", "C", "D"] if opts[l] == q["answer"])
        await query.message.reply_text(
            f"❌ *ئەشتباەیە\\!*\n\nوەڵامی دروست: *{correct_letter}: {q['answer']}*\n\n{stats_text(s)}",
            parse_mode="MarkdownV2",
        )

    s["current_index"] += 1

    if s["current_index"] >= len(s["shuffled"]):
        s["active"] = False
        is_new_best = record_score(uid, user_name(query.from_user), s)
        msg = f"🏁 *کویز تەواو بوو\\!*\n\n{stats_text(s)}\n\n/quiz بکە بۆ دووبارەکردنەوە\\."
        if is_new_best:
            msg += "\n\n🏆 *تۆماری تازەی کەسیت داناوە\\!*"
        await query.message.reply_text(msg, parse_mode="MarkdownV2")
        return

    await asyncio.sleep(0.8)
    await send_question(context, query.message.chat_id, s)


async def on_stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    s = get_session(uid)
    s["active"] = False
    s["waiting"] = False
    is_new_best = record_score(uid, user_name(query.from_user), s)
    msg = f"⏹ کویز وەستا\\.\n\n{stats_text(s)}\n\n/quiz بکە بۆ کویزێکی نوێ\\."
    if is_new_best:
        msg += "\n\n🏆 *تۆماری تازەی کەسیت داناوە\\!*"
    await query.message.reply_text(msg, parse_mode="MarkdownV2")


async def on_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer("بەرپرسی تۆمارکراوە")


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CallbackQueryHandler(on_answer, pattern=r"^ans_[ABCD]$"))
    app.add_handler(CallbackQueryHandler(on_stop_quiz, pattern=r"^stop_quiz$"))
    app.add_handler(CallbackQueryHandler(on_done, pattern=r"^done_[ABCD]$"))

    logger.info("Bot started — polling Telegram…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
