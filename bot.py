import os
import re
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import database
import ai_analyzer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS = {
    "comida": [
        "café", "cafe", "pizza", "taco", "tacos", "burger", "hamburguesa",
        "comida", "restaurant", "restaurante", "sushi", "pasta", "pollo",
        "carne", "desayuno", "almuerzo", "cena", "lunch", "snack", "helado",
        "pan", "tortilla", "tamales", "torta", "burritos", "antojitos",
        "quesadillas", "enchiladas", "pozole", "birria", "barbacoa",
        "galletas", "papas", "frituras", "botanas", "dulces", "chocolate",
    ],
    "transporte": [
        "gasolina", "uber", "taxi", "metro", "camion", "camión", "bus",
        "gasolinera", "estacionamiento", "caseta", "lyft", "didi",
        "combustible", "peaje", "bici", "moto",
    ],
    "supermercado": [
        "super", "walmart", "chedraui", "soriana", "costco", "mercado",
        "verduras", "frutas", "abarrotes", "bodega", "aurrera", "sam's",
        "sams", "la comer", "comercial",
    ],
    "salud": [
        "farmacia", "medicamento", "medicina", "doctor", "consulta",
        "hospital", "dentista", "gym", "gimnasio", "vitaminas", "analisis",
        "análisis", "laboratorio", "optometrista", "psicólogo", "psicologo",
    ],
    "entretenimiento": [
        "netflix", "spotify", "cine", "pelicula", "película", "juego",
        "videojuego", "concierto", "evento", "bar", "fiesta", "disney",
        "hbo", "prime", "youtube", "twitch", "steam", "xbox", "playstation",
    ],
    "ropa": [
        "ropa", "zapatos", "tenis", "camisa", "pantalon", "pantalón",
        "vestido", "zara", "h&m", "shein", "boutique",
    ],
    "hogar": [
        "renta", "luz", "agua", "internet", "gas", "limpieza", "mueble",
        "electrodomestico", "electrodoméstico", "ferreteria", "ferretería",
        "mantenimiento", "plomero", "electricista", "pintura",
    ],
    "educacion": [
        "curso", "libro", "escuela", "universidad", "colegio", "taller",
        "clase", "udemy", "coursera", "platzi", "capacitacion", "capacitación",
    ],
    "servicios": [
        "telefono", "teléfono", "celular", "seguro", "banco", "comision",
        "comisión", "suscripcion", "suscripción", "streaming", "icloud",
        "google", "amazon", "microsoft",
    ],
}

CATEGORY_EMOJIS = {
    "comida": "🍔",
    "transporte": "⛽",
    "supermercado": "🛒",
    "salud": "💊",
    "entretenimiento": "🎬",
    "ropa": "👕",
    "hogar": "🏠",
    "educacion": "📚",
    "servicios": "📱",
    "otro": "📦",
}

MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

SHORT_MONTHS = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}


def detect_category(description: str) -> str:
    text = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "otro"


def parse_expense(text: str):
    """
    Supports:
      "Café 100"          description then amount
      "100 gasolina"      amount then description
      "Pizza $250"        description then $amount
      "$45.50 transporte" $amount then description
    Returns (description, amount) or (None, None).
    """
    text = text.strip()

    # Description first, then amount (with optional $)
    match = re.match(r"^(.+?)\s+\$?(\d+(?:[.,]\d{1,2})?)$", text)
    if match:
        description = match.group(1).strip()
        amount = float(match.group(2).replace(",", "."))
        return description, amount

    # Amount first (with optional $), then description
    match = re.match(r"^\$?(\d+(?:[.,]\d{1,2})?)\s+(.+)$", text)
    if match:
        amount = float(match.group(1).replace(",", "."))
        description = match.group(2).strip()
        return description, amount

    return None, None


def format_date(iso_date: str) -> str:
    dt = datetime.fromisoformat(iso_date)
    return f"{dt.day} {SHORT_MONTHS[dt.month]}"


def progress_bar(value: float, max_value: float, length: int = 10) -> str:
    if max_value <= 0:
        return "░" * length
    filled = round((value / max_value) * length)
    filled = max(0, min(filled, length))
    return "█" * filled + "░" * (length - filled)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

HELP_TEXT = """
👋 *JudeBot para Registro de Gastos Personales*

Registra un gasto enviando un mensaje como:
• `Café 100`
• `100 gasolina`
• `Pizza $250`
• `$45.50 transporte`

*Comandos disponibles:*
/resumen — Gastos del mes actual con total y promedio
/categorias — Totales por categoría con barras de progreso
/historial — Últimos 10 gastos registrados
/analisis — Análisis inteligente con IA (Claude)
/borrar <id> — Eliminar un gasto por su ID
/ayuda — Mostrar este mensaje

_Categorías detectadas automáticamente:_
🍔 Comida · ⛽ Transporte · 🛒 Supermercado · 💊 Salud
🎬 Entretenimiento · 👕 Ropa · 🏠 Hogar · 📚 Educación
📱 Servicios · 📦 Otro
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    description, amount = parse_expense(text)

    if description is None or amount is None or amount <= 0:
        await update.message.reply_text(
            "No pude entender ese gasto. 🤔\n"
            "Prueba con: `Café 100` o `100 gasolina`",
            parse_mode="Markdown",
        )
        return

    category = detect_category(description)
    emoji = CATEGORY_EMOJIS[category]

    expense_id = database.add_expense(description, amount, category)

    await update.message.reply_text(
        f"✅ *{description}* — ${amount:,.2f}\n"
        f"🏷️ Categoría: {emoji} {category.capitalize()}\n"
        f"🆔 ID: `{expense_id}`",
        parse_mode="Markdown",
    )


async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    expenses = database.get_expenses_by_month(now.year, now.month)
    month_name = MONTH_NAMES[now.month]

    if not expenses:
        await update.message.reply_text(
            f"📭 No hay gastos registrados en {month_name} {now.year}."
        )
        return

    total = sum(float(e["amount"]) for e in expenses)
    daily_avg = total / max(now.day, 1)

    lines = [
        f"📅 *Resumen de {month_name} {now.year}*\n",
        f"💰 Total: ${total:,.2f}",
        f"📊 Promedio diario: ${daily_avg:,.2f}",
        f"📝 Gastos registrados: {len(expenses)}\n",
        "_Gastos del mes (más recientes primero):_",
    ]

    for e in expenses:
        emoji = CATEGORY_EMOJIS.get(e["category"], "📦")
        date_str = format_date(e["date"])
        lines.append(
            f"`{e['id']:>4}` [{date_str}] {e['description']} — ${float(e['amount']):,.2f} {emoji}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    totals = database.get_totals_by_category(now.year, now.month)
    month_name = MONTH_NAMES[now.month]

    if not totals:
        await update.message.reply_text(
            f"📭 No hay gastos registrados en {month_name} {now.year}."
        )
        return

    grand_total = sum(float(r["total"]) for r in totals)
    lines = [f"🗂️ *Categorías — {month_name} {now.year}*\n"]

    for r in totals:
        cat = r["category"]
        total = float(r["total"])
        count = int(r["count"])
        pct = (total / grand_total * 100) if grand_total > 0 else 0
        emoji = CATEGORY_EMOJIS.get(cat, "📦")
        bar = progress_bar(total, grand_total)

        lines.append(
            f"{emoji} *{cat.capitalize()}*\n"
            f"`{bar}` {pct:.1f}%\n"
            f"  ${total:,.2f} · {count} gasto{'s' if count != 1 else ''}\n"
        )

    lines.append(f"💰 *Total: ${grand_total:,.2f}*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expenses = database.get_last_expenses(10)

    if not expenses:
        await update.message.reply_text("📭 No hay gastos registrados todavía.")
        return

    lines = ["📋 *Últimos 10 gastos*\n"]
    for e in expenses:
        emoji = CATEGORY_EMOJIS.get(e["category"], "📦")
        date_str = format_date(e["date"])
        lines.append(
            f"`{e['id']:>4}` [{date_str}] {e['description']}\n"
            f"       {emoji} {e['category'].capitalize()} — ${float(e['amount']):,.2f}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loading_msg = await update.message.reply_text(
        "🤖 Analizando tus gastos con IA... un momento ⏳"
    )

    now = datetime.now()
    month_name = f"{MONTH_NAMES[now.month]} {now.year}"
    month_expenses = database.get_expenses_by_month(now.year, now.month)
    category_totals = database.get_totals_by_category(now.year, now.month)
    summary = database.get_all_expenses_summary()

    try:
        analysis = await ai_analyzer.analyze_expenses(
            month_name=month_name,
            month_expenses=month_expenses,
            category_totals=category_totals,
            historical_monthly_avg=summary["monthly_avg"],
        )
        await loading_msg.delete()
        await update.message.reply_text(
            f"🤖 *Análisis de {month_name}*\n\n{analysis}",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.error("Error calling AI: %s", exc)
        await loading_msg.delete()
        await update.message.reply_text(
            "❌ No se pudo obtener el análisis de IA. "
            "Verifica tu ANTHROPIC_API_KEY e intenta de nuevo."
        )


async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Uso: `/borrar <id>`\nEjemplo: `/borrar 42`\n\n"
            "Consulta los IDs con /historial o /resumen.",
            parse_mode="Markdown",
        )
        return

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número entero.")
        return

    deleted = database.delete_expense(expense_id)
    if deleted:
        await update.message.reply_text(f"🗑️ Gasto `#{expense_id}` eliminado correctamente.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ No se encontró ningún gasto con ID `{expense_id}`.", parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    database.init_db()
    logger.info("Base de datos inicializada.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("categorias", categorias))
    app.add_handler(CommandHandler("historial", historial))
    app.add_handler(CommandHandler("analisis", analisis))
    app.add_handler(CommandHandler("borrar", borrar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
