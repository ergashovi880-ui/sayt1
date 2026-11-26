# BiznesAI CRM — Mahalliy bizneslar uchun AI + Buyurtma SaaS

Bu loyiha O'zbekistondagi mahalliy bizneslarga (go'zallik salonlari, kafelar, o'quv markazlari, klinikalar) **oylik obunaga sotish uchun** tayyorlangan MVP platforma.

## Nimalar tayyor?
1. **Mijoz sayti (Demo)**: 3 xil tayyor biznes shabloni (Salon, Kafe, O'quv markazi), xizmatlar katalogi va onlayn buyurtma formasi.
2. **24/7 AI Maslahatchi**: O'zbek tilida mijoz savollariga javob beradi (`GEMINI_API_KEY` berilsa haqiqiy Gemini API ishlaydi, berilmasa lokal aqlli rejim avtomatik ishlaydi).
3. **Admin CRM**: Buyurtmalarni ko'rish, statusini o'zgartirish (`yangi` -> `tasdiqlandi` -> `bajarildi`), yangi xizmat qo'shish va daromad statistikasini kuzatish (`SQLite` bazada saqlanadi).
4. **Daromad & Tariflar (Click / Payme)**: 199 000 / 399 000 / 799 000 so'm oylik tariflar uchun invoice va Click/Payme checkout URL yaratuvchi modul (`payments.py`).

## Ishga tushirish
Qo'shimcha kutubxona o'rnatish shart emas (Python 3 standart kutubxonasida ishlaydi):

```bash
cd /Users/a1234/biznes-ai-crm
python3 app.py
```

Brauzerda oching: `http://127.0.0.1:8080`

Haqiqiy Gemini AI yoqish uchun:
```bash
export GEMINI_API_KEY="sizning_kalitingiz"
python3 app.py
```

## Internetga chiqarish (bepul Render / Railway deploy)
Loyiha `render.yaml`, `Procfile` va `requirements.txt` fayllari bilan tayyorlangan:
1. GitHub'da yangi repository oching va ushbu papkani yuklang (`git remote add origin ... && git push -u origin main`).
2. [Render.com](https://render.com) ga kiring -> **New +** -> **Blueprint** (yoki **Web Service**) -> GitHub repongizni tanlang.
3. Render avtomatik `python3 app.py` ni ishga tushiradi va sizga `https://biznes-ai-crm.onrender.com` kabi umumiy havola beradi.

## Qanday qilib bundan real daromad qilish mumkin?
1. **Deploy qiling**: Yuqoridagi qadam bilan umumiy havola oling (doimiy ma'lumotlar saqlanishi uchun VPS yoki Render Disk ulab `DB_PATH` ko'rsating).
2. **Mijoz toping**: Instagram/2GIS orqali o'z shahringizdagi 30 ta salon, kafe yoki o'quv markaziga yozing va shu sayt demosini ko'rsating.
3. **Obuna soting**: Har bir ulangan biznes uchun alohida ma'lumot kiritib, oyiga 199 000 – 499 000 so'm abonent to'lovi oling.
4. **Click / Payme ulang**: Click/Payme merchant kabinetidan ID olib `CLICK_MERCHANT_ID`, `CLICK_SERVICE_ID`, `PAYME_MERCHANT_ID` o'zgaruvchilariga qo'ying.
