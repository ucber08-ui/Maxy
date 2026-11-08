# Maxy — AI trading signals ilovasi
Grafik (EMA, MACD, RSI, Bollinger, 15m/1h/1d) + yangiliklar (Google News + ixtiyoriy Claude tahlili) -> SOTIB OL / SOT / KUT + SL/TP.
Veb-ilova (telefonda "Bosh ekranga qo'shish" bilan ilova kabi o'rnatiladi). Telegram shart emas.

## Ishga tushirish
    pip install -r requirements.txt
    uvicorn server:app --host 0.0.0.0 --port 8000
Brauzerda: http://localhost:8000  (ixtiyoriy: ANTHROPIC_API_KEY o'rnating)

## Internetga chiqarish
Render / Railway / Fly.io ga shu repo'ni ulang (Procfile tayyor). Start: `uvicorn server:app --host 0.0.0.0 --port $PORT`.

## Sozlash
Hamma narsa `config.yaml` da: brend (Maxy), aktivlar, vaznlar, chegara, bozor soatlari. Logo: `assets/logo.png`.
Backtest: `python main.py backtest`. `main.py` (ixtiyoriy Telegram) hali ishlaydi.

## Ogohlik
Foyda kafolatlanmaydi. Avval backtest va demo. Moliyaviy maslahat emas.
