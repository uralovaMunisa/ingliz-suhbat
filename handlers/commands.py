from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.database import Database
from handlers.keyboards import get_level_keyboard, get_goal_keyboard, get_topic_keyboard


async def level_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (
        "📊 **Choose your English level:**\n\n"
        "• **A1** - Beginner: Basic words, simple sentences\n"
        "• **A2** - Elementary: Everyday expressions, past/future\n"
        "• **B1** - Intermediate: Natural conversation, common idioms\n"
        "• **B2** - Upper-Intermediate: Fluent, varied vocabulary\n"
        "• **C1** - Advanced: Rich vocabulary, complex topics"
    )
    try:
        await update.message.reply_text(text, reply_markup=get_level_keyboard(), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(text, reply_markup=get_level_keyboard())


async def topic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = "💡 **Choose a conversation topic to explore together:**"
    await update.message.reply_text(text, reply_markup=get_topic_keyboard())


async def strict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    db: Database = context.bot_data["db"]
    await db.update_user(update.effective_user.id, correction_mode="strict")
    msg = (
        "🎯 **Strict Mode Activated!**\n\n"
        "I will now pay close attention to every detail, including grammar, prepositions, "
        "punctuation, and capitalization."
    )
    try:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(msg)


async def relax_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    db: Database = context.bot_data["db"]
    await db.update_user(update.effective_user.id, correction_mode="relax")
    msg = (
        "☕ **Relaxed Mode Activated!**\n\n"
        "I will only correct major mistakes that block understanding, so you can focus on fluency and fun!"
    )
    try:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(msg)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    db: Database = context.bot_data["db"]
    await db.clear_chat_history(update.effective_user.id)
    await db.reset_message_count(update.effective_user.id)
    msg = "🧹 **Conversation memory cleared!**\n\nWe have a fresh start. What would you like to talk about today?"
    try:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(msg)


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    user = await db.get_user(user_id) or {}

    mistakes = await db.get_recent_mistakes(user_id, limit=5)
    vocabulary = await db.get_recent_vocabulary(user_id, limit=5)

    name = user.get("name", "Friend")
    level = user.get("level", "B1")
    goal = user.get("goal", "Daily conversation")
    mode = user.get("correction_mode", "standard")

    lines = [
        f"📋 **Learning Summary for {name}** 🌟",
        f"• **Level:** {level}",
        f"• **Goal:** {goal}",
        f"• **Correction Mode:** {mode.capitalize()}\n"
    ]

    if mistakes:
        lines.append("✏️ **Recent Mistakes Reviewed:**")
        for m in mistakes:
            lines.append(f"• ❌ {m['original_text']} → ✅ {m['corrected_text']}")
            lines.append(f"  💡 {m['explanation']}")
        lines.append("")
    else:
        lines.append("✏️ **Recent Mistakes:** No mistakes recorded yet! Keep chatting! 👏\n")

    if vocabulary:
        lines.append("📚 **New Words & Phrases Learned:**")
        for v in vocabulary:
            lines.append(f"• **{v['phrase']}**: {v['definition']}")
            if v.get("example"):
                lines.append(f"  *Example:* {v['example']}")
    else:
        lines.append("📚 **Vocabulary:** No new words logged yet. Ask Emma about new expressions!")

    text = "\n".join(lines)
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(text)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    db: Database = context.bot_data["db"]
    gemini = context.bot_data["gemini"]
    user_id = update.effective_user.id

    user = await db.get_user(user_id) or {}
    mistakes = await db.get_recent_mistakes(user_id, limit=10)

    wait_msg = await update.message.reply_text("🎲 Preparing a custom 5-question quiz for you...")

    quiz_text = await gemini.generate_quiz(user, mistakes)
    try:
        await wait_msg.edit_text(quiz_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await wait_msg.edit_text(quiz_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = (
        "🤖 **Emma - English Conversation Tutor Commands**\n\n"
        "• /start - Start onboarding & setup\n"
        "  *(Botni qayta boshlash va sozlash)*\n"
        "• /level - Change your English level (A1-C1)\n"
        "  *(Ingliz tili darajasini tanlash)*\n"
        "• /topic - Get 3 conversation topic ideas\n"
        "  *(Suhbat uchun mavzu tanlash)*\n"
        "• /quiz - 5-question quiz based on your mistakes\n"
        "  *(Xatolaringiz asosida mini-test topshirish)*\n"
        "• /summary - View your mistakes and new words\n"
        "  *(Xatolaringiz va yangi so'zlar hisoboti)*\n"
        "• /strict - Strict mode: correct every single mistake\n"
        "  *(Qattiqqo'l rejim: barcha xatolar va tinish belgilari tuzatiladi)*\n"
        "• /relax - Relaxed mode: correct only major mistakes\n"
        "  *(Erkin rejim: faqat ma'noga ta'sir qiladigan xatolar tuzatiladi)*\n"
        "• /reset - Clear conversation memory\n"
        "  *(Suhbat xotirasini tozalash)*\n"
        "• /help - Show this guide\n"
        "  *(Yordam xabarini ko'rsatish)*\n\n"
        "🎙️ **Tip:** You can send **voice messages**! Emma will transcribe what you say and give you pronunciation and grammar feedback."
    )
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(text)

