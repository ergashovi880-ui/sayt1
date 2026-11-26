"""SQLite database and multi-niche seed data for BiznesAI CRM."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).resolve().parent / "biznes.db")))

NICHE_TEMPLATES: dict[str, dict[str, Any]] = {
    "salon": {
        "name": "Malika Beauty Studio",
        "niche": "salon",
        "niche_label": "Go'zallik saloni",
        "tagline": "Soch, tirnoq va yuz parvarishi bo'yicha professional xizmatlar",
        "hours": "Har kuni 09:00 - 21:00",
        "address": "Toshkent sh., Chilonzor tumani, Bunyodkor ko'chasi 12",
        "phone": "+998 90 123 45 67",
        "services": [
            ("Ayollar soch turmagi va ukladka", 180000, 60, "Yuvish, kesish va zamonaviy ukladka"),
            ("Manikur + Gel-lak qoplama", 150000, 90, "Mustahkam gel-lak va dizayn"),
            ("Yuz tozalash (Chistka)", 250000, 75, "Ultratovushli chuqur tozalash"),
            ("Kechki makiyaj", 320000, 80, "To'y va tadbirlar uchun professional makiyaj"),
        ],
    },
    "cafe": {
        "name": "Oshxona & Coffee House",
        "niche": "cafe",
        "niche_label": "Kafe va yetkazib berish",
        "tagline": "Issiq taomlar, maxsus qahva va tez yetkazib berish xizmati",
        "hours": "Har kuni 08:00 - 23:30",
        "address": "Toshkent sh., Yunusobod tumani, Amir Temur shoh ko'chasi 45",
        "phone": "+998 91 555 22 11",
        "services": [
            ("Katta Combo Set (2 kishilik)", 145000, 25, "2 ta burger, kartoshka fri va 2 ta ichimlik"),
            ("Toshkent Palov (1 porsiya)", 48000, 15, "Salat va non bilan issiq yetkazib beriladi"),
            ("Iced Latte + Kruassan", 52000, 10, "Yangi qovurilgan arabika va shokoladli kruassan"),
            ("Oilaviy Pitsa Assorti", 130000, 30, "40 sm katta pitsa va 1L ichimlik"),
        ],
    },
    "center": {
        "name": "Kelajak IT & Til Markazi",
        "niche": "center",
        "niche_label": "O'quv markazi",
        "tagline": "IELTS, Python dasturlash va dizayn kurslariga tez yozilish",
        "hours": "Dushanba - Shanba 09:00 - 20:00",
        "address": "Samarqand sh., Universitet xiyoboni 8",
        "phone": "+998 93 777 88 99",
        "services": [
            ("IELTS Intensive (oylik)", 650000, 120, "Haftasiga 3 kun 2 soatdan, mock testlar bilan"),
            ("Python & AI Dasturlash (oylik)", 850000, 120, "Noldan real loyihagacha amaliy kurs"),
            ("Grafik Dizayn & SMM (oylik)", 590000, 90, "Figma, Photoshop va kontent strategiya"),
            ("Bepul sinov darsi + daraja aniqlash", 0, 45, "Mentor bilan suhbat va individual reja"),
        ],
    },
}

PLANS: list[dict[str, Any]] = [
    {
        "id": "start",
        "name": "Start",
        "price_uzs": 199000,
        "period": "oyiga",
        "features": [
            "Tayyor buyurtma va bron sahifasi",
            "Oddiy CRM buyurtmalar ro'yxati",
            "Telegram/telefon orqali tezkor aloqa",
        ],
    },
    {
        "id": "pro",
        "name": "Biznes Pro",
        "price_uzs": 399000,
        "period": "oyiga",
        "popular": True,
        "features": [
            "24/7 AI Maslahatchi (o'zbek tilida)",
            "Cheksiz xizmat va buyurtma boshqaruvi",
            "Click / Payme onlayn to'lov integratsiyasi",
        ],
    },
    {
        "id": "vip",
        "name": "VIP Tarmoq",
        "price_uzs": 799000,
        "period": "oyiga",
        "features": [
            "Bir nechta filial va shaxsiy domen",
            "Maxsus AI prompt va analitika hisobotlari",
            "Shaxsiy texnik qo'llab-quvvatlash",
        ],
    },
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if needed and seed default business data."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS business_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                niche TEXT NOT NULL,
                niche_label TEXT NOT NULL,
                tagline TEXT NOT NULL,
                hours TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_uzs INTEGER NOT NULL,
                duration_min INTEGER NOT NULL DEFAULT 30,
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                service_id INTEGER,
                service_name TEXT NOT NULL,
                price_uzs INTEGER NOT NULL DEFAULT 0,
                preferred_time TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'yangi',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                amount_uzs INTEGER NOT NULL,
                business_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'kutilmoqda',
                invoice_code TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
            """
        )

        exists = conn.execute("SELECT COUNT(*) FROM business_profile").fetchone()[0]
        if exists == 0:
            seed_niche("salon", conn=conn)


def seed_niche(niche_key: str, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    """Switch the active demo business template and refresh sample services."""
    if niche_key not in NICHE_TEMPLATES:
        raise ValueError(f"Noma'lum yo'nalish: {niche_key}")

    tpl = NICHE_TEMPLATES[niche_key]
    own_conn = conn is None
    if own_conn:
        conn = get_conn()

    assert conn is not None
    try:
        conn.execute("DELETE FROM business_profile")
        conn.execute(
            """
            INSERT INTO business_profile (id, name, niche, niche_label, tagline, hours, address, phone)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tpl["name"],
                tpl["niche"],
                tpl["niche_label"],
                tpl["tagline"],
                tpl["hours"],
                tpl["address"],
                tpl["phone"],
            ),
        )
        conn.execute("DELETE FROM services")
        conn.executemany(
            "INSERT INTO services (name, price_uzs, duration_min, description) VALUES (?, ?, ?, ?)",
            tpl["services"],
        )

        order_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if order_count == 0:
            first_svc = tpl["services"][0]
            conn.execute(
                """
                INSERT INTO orders (customer_name, customer_phone, service_id, service_name, price_uzs, preferred_time, notes, status)
                VALUES (?, ?, 1, ?, ?, '15:00', 'Demo buyurtma', 'tasdiqlandi')
                """,
                ("Aziza Karimova", "+998 90 987 65 43", first_svc[0], first_svc[1]),
            )
        if own_conn:
            conn.commit()
    finally:
        if own_conn:
            conn.close()

    return get_state()


def get_state() -> dict[str, Any]:
    """Return full dashboard + storefront state."""
    with get_conn() as conn:
        profile_row = conn.execute("SELECT * FROM business_profile WHERE id = 1").fetchone()
        services = [dict(r) for r in conn.execute("SELECT * FROM services ORDER BY id ASC").fetchall()]
        orders = [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()]
        payments = [dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()]

    confirmed_revenue = sum(o["price_uzs"] for o in orders if o["status"] in ("tasdiqlandi", "bajarildi"))
    subscription_revenue = sum(p["amount_uzs"] for p in payments if p["status"] == "tolandi")

    return {
        "profile": dict(profile_row) if profile_row else {},
        "services": services,
        "orders": orders,
        "payments": payments,
        "plans": PLANS,
        "stats": {
            "total_orders": len(orders),
            "pending_orders": sum(1 for o in orders if o["status"] == "yangi"),
            "confirmed_revenue_uzs": confirmed_revenue,
            "subscription_revenue_uzs": subscription_revenue,
        },
    }


def add_service(name: str, price_uzs: int, duration_min: int, description: str) -> dict[str, Any]:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO services (name, price_uzs, duration_min, description) VALUES (?, ?, ?, ?)",
            (name.strip(), max(0, int(price_uzs)), max(5, int(duration_min)), description.strip()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM services WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def create_order(
    customer_name: str,
    customer_phone: str,
    service_id: int | None,
    preferred_time: str,
    notes: str = "",
) -> dict[str, Any]:
    with get_conn() as conn:
        service_name = "Umumiy maslahat"
        price_uzs = 0
        if service_id is not None:
            svc = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
            if svc:
                service_name = svc["name"]
                price_uzs = svc["price_uzs"]

        cur = conn.execute(
            """
            INSERT INTO orders (customer_name, customer_phone, service_id, service_name, price_uzs, preferred_time, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'yangi')
            """,
            (
                customer_name.strip(),
                customer_phone.strip(),
                service_id,
                service_name,
                price_uzs,
                preferred_time.strip() or "Kelishiladi",
                notes.strip(),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def update_order_status(order_id: int, status: str) -> dict[str, Any] | None:
    allowed = {"yangi", "tasdiqlandi", "bajarildi", "bekor"}
    if status not in allowed:
        raise ValueError("Noto'g'ri status")

    with get_conn() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return dict(row) if row else None


def get_plan(plan_id: str) -> dict[str, Any] | None:
    return next((p for p in PLANS if p["id"] == plan_id), None)


def create_payment(
    plan_id: str,
    provider: str,
    business_name: str,
    invoice_code: str,
) -> dict[str, Any]:
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError("Tarif topilmadi")

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO payments (plan_id, plan_name, provider, amount_uzs, business_name, status, invoice_code)
            VALUES (?, ?, ?, ?, ?, 'kutilmoqda', ?)
            """,
            (
                plan["id"],
                plan["name"],
                provider,
                plan["price_uzs"],
                business_name.strip() or "Yangi mijoz biznesi",
                invoice_code,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM payments WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def confirm_payment(payment_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        conn.execute("UPDATE payments SET status = 'tolandi' WHERE id = ?", (payment_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        return dict(row) if row else None
