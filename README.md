# 🤖 Bot de Gastos Personales (Telegram)

Bot de Telegram para registrar y analizar gastos personales con IA. Usa PostgreSQL en Neon como base de datos y Claude AI para análisis mensuales inteligentes.

---

## Características

- **Registro rápido** — envía `Café 100` o `100 gasolina` y listo
- **Categorización automática** — detecta comida, transporte, salud, entretenimiento y más
- **Resumen mensual** — total, promedio diario y lista completa
- **Análisis con IA** — Claude examina tus patrones y da recomendaciones concretas
- **Base de datos en la nube** — Neon PostgreSQL (free tier, sin pausas)
- **Deploy en Railway** — siempre activo, sin configuración de servidor

---

## Requisitos previos

- Python 3.11+
- Cuenta en [Neon](https://neon.tech) (gratuita)
- Cuenta en [Railway](https://railway.app) (gratuita)
- Token de bot de Telegram (via @BotFather)
- API Key de [Anthropic](https://console.anthropic.com)

---

## Instalación local

### 1. Clonar y entrar al proyecto

```bash
git clone <tu-repo>
cd gastos_bot
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y rellena los tres valores:

```env
TELEGRAM_BOT_TOKEN=123456789:AABBcc...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://usuario:contraseña@host/basededatos?sslmode=require
```

#### Cómo obtener cada valor

**TELEGRAM_BOT_TOKEN**
1. Abre Telegram y busca `@BotFather`
2. Envía `/newbot` y sigue los pasos
3. Copia el token que te entregue

**ANTHROPIC_API_KEY**
1. Ve a [console.anthropic.com](https://console.anthropic.com/settings/keys)
2. Crea una API key y cópiala

**DATABASE_URL**
1. Ve a [console.neon.tech](https://console.neon.tech)
2. Crea un proyecto nuevo (cualquier nombre, región más cercana a ti)
3. En el Dashboard, busca **Connection Details**
4. Selecciona **Connection string** → modo **psycopg2**
5. Cópiala (formato: `postgresql://...?sslmode=require`)

### 4. Ejecutar localmente

```bash
python bot.py
```

La tabla `expenses` se crea automáticamente al iniciar.

---

## Deploy en Railway

### 1. Crear repositorio en GitHub

```bash
git init
git add .
git commit -m "feat: bot de gastos inicial"
git remote add origin https://github.com/tu-usuario/gastos-bot.git
git push -u origin main
```

### 2. Crear proyecto en Railway

1. Ve a [railway.app](https://railway.app) e inicia sesión con GitHub
2. Haz clic en **New Project → Deploy from GitHub repo**
3. Selecciona tu repositorio
4. Railway detectará el `Procfile` automáticamente

### 3. Configurar variables de entorno en Railway

En el panel de tu proyecto:
1. Ve a la pestaña **Variables**
2. Agrega las tres variables:
   - `TELEGRAM_BOT_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL`

### 4. Verificar el deploy

- Ve a la pestaña **Deployments** y confirma que el build fue exitoso
- En **Logs** deberías ver: `Bot iniciado. Esperando mensajes...`
- Abre Telegram, busca tu bot y envía `/start`

---

## Uso del bot

| Mensaje / Comando | Descripción |
|---|---|
| `Café 100` | Registra gasto: Café, $100 |
| `100 gasolina` | Registra gasto: gasolina, $100 |
| `Pizza $250` | Registra gasto: Pizza, $250 |
| `$45.50 transporte` | Registra gasto: transporte, $45.50 |
| `/resumen` | Todos los gastos del mes actual |
| `/categorias` | Totales por categoría con barras de progreso |
| `/historial` | Últimos 10 gastos registrados |
| `/analisis` | Análisis inteligente con Claude AI |
| `/borrar 42` | Elimina el gasto con ID 42 |
| `/ayuda` | Muestra este mensaje de ayuda |

---

## Categorías automáticas

El bot detecta la categoría según palabras clave en la descripción:

| Emoji | Categoría | Ejemplos |
|---|---|---|
| 🍔 | Comida | café, pizza, restaurant, almuerzo |
| ⛽ | Transporte | gasolina, uber, metro, taxi |
| 🛒 | Supermercado | walmart, costco, mercado, verduras |
| 💊 | Salud | farmacia, doctor, gym, vitaminas |
| 🎬 | Entretenimiento | netflix, cine, concierto, bar |
| 👕 | Ropa | zapatos, camisa, zara |
| 🏠 | Hogar | renta, luz, agua, internet |
| 📚 | Educación | curso, libro, udemy |
| 📱 | Servicios | celular, seguro, suscripción |
| 📦 | Otro | todo lo demás |

---

## Estructura del proyecto

```
gastos_bot/
├── bot.py           # Bot principal + todos los handlers
├── database.py      # Módulo PostgreSQL (Neon)
├── ai_analyzer.py   # Integración con Claude AI
├── requirements.txt # Dependencias Python
├── Procfile         # Comando de inicio para Railway
├── .env.example     # Plantilla de variables de entorno
├── .gitignore       # Excluye .env y archivos sensibles
└── README.md        # Esta guía
```

---

## Solución de problemas

**El bot no responde**
- Verifica que `TELEGRAM_BOT_TOKEN` sea correcto
- Revisa los logs en Railway → Deployments

**Error de base de datos**
- Verifica que `DATABASE_URL` incluya `?sslmode=require` al final
- Confirma que el proyecto en Neon esté activo (no pausado)

**El análisis de IA falla**
- Verifica que `ANTHROPIC_API_KEY` comience con `sk-ant-`
- Asegúrate de tener créditos disponibles en tu cuenta de Anthropic
