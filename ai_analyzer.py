import os
import httpx
from datetime import datetime

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-opus-4-6"


async def analyze_expenses(
    month_name: str,
    month_expenses: list,
    category_totals: list,
    historical_monthly_avg: float,
) -> str:
    if not month_expenses:
        return "No hay gastos registrados este mes para analizar."

    month_total = sum(float(e["amount"]) for e in month_expenses)

    # Days elapsed so far in the month (at least 1 to avoid division by zero)
    today = datetime.now()
    days_elapsed = max(today.day, 1)
    daily_avg = month_total / days_elapsed

    # Category breakdown for this month
    categories_text = "\n".join(
        f"  - {r['category'].capitalize()}: ${float(r['total']):,.2f} ({int(r['count'])} gastos)"
        for r in category_totals
    ) or "  Sin datos"

    # Top 5 individual expenses this month
    top_month = sorted(month_expenses, key=lambda e: float(e["amount"]), reverse=True)[:5]
    top_text = "\n".join(
        f"  {i + 1}. {e['description']} — ${float(e['amount']):,.2f} ({e['category']})"
        for i, e in enumerate(top_month)
    )

    prompt = f"""Eres un asesor financiero personal hispanohablante. \
Analiza los siguientes datos de gastos del mes de {month_name} y proporciona \
un análisis útil, concreto y motivador.

--- DATOS DEL MES ---
Total gastado: ${month_total:,.2f}
Días transcurridos: {days_elapsed}
Promedio diario actual: ${daily_avg:,.2f}
Promedio mensual histórico: ${historical_monthly_avg:,.2f}
Total de gastos registrados: {len(month_expenses)}

Desglose por categoría:
{categories_text}

Top 5 gastos del mes:
{top_text}
--- FIN DE DATOS ---

Responde EXCLUSIVAMENTE en español usando estas secciones con sus emojis exactos:

📊 *Resumen*
(2-3 oraciones resumiendo el panorama general del mes)

💡 *Patrones*
(Identifica 2-3 patrones o tendencias observables en los gastos)

⚠️ *Áreas de atención*
(1-2 categorías o hábitos que merecen revisión)

✅ *Lo que va bien*
(1-2 aspectos positivos o logros en el control de gastos)

🎯 *Recomendaciones*
(Exactamente 3 acciones concretas y realizables para el próximo mes)
"""

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]
