"""Main HTTP server for BiznesAI CRM & Uzbek SaaS MVP."""

from __future__ import annotations

import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import ai_helper
import db
import payments

STATIC_DIR = Path(__file__).resolve().parent / "static"


class BiznesHandler(BaseHTTPRequestHandler):
    """Serves static frontend assets and JSON API endpoints."""

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _serve_static(self, rel_path: str) -> None:
        clean = "index.html" if rel_path in ("", "/") else rel_path.lstrip("/")
        target = (STATIC_DIR / clean).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
            self._send_json({"error": "Sahifa topilmadi"}, HTTPStatus.NOT_FOUND)
            return

        mime_type, _ = mimetypes.guess_type(str(target))
        content = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime_type or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._send_json(db.get_state())
            return
        if path == "/api/health":
            self._send_json({"ok": True})
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            data = self._read_json()
        except json.JSONDecodeError:
            self._send_json({"error": "Noto'g'ri JSON formati"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            if path == "/api/niche":
                niche = str(data.get("niche", "")).strip()
                self._send_json(db.seed_niche(niche))
                return

            if path == "/api/services":
                name = str(data.get("name", "")).strip()
                if not name:
                    self._send_json({"error": "Xizmat nomi majburiy"}, HTTPStatus.BAD_REQUEST)
                    return
                service = db.add_service(
                    name=name,
                    price_uzs=int(data.get("price_uzs", 0)),
                    duration_min=int(data.get("duration_min", 30)),
                    description=str(data.get("description", "")),
                )
                self._send_json({"service": service, "state": db.get_state()}, HTTPStatus.CREATED)
                return

            if path == "/api/orders":
                customer_name = str(data.get("customer_name", "")).strip()
                customer_phone = str(data.get("customer_phone", "")).strip()
                if not customer_name or not customer_phone:
                    self._send_json(
                        {"error": "Ism va telefon raqami majburiy"}, HTTPStatus.BAD_REQUEST
                    )
                    return
                raw_svc = data.get("service_id")
                service_id = int(raw_svc) if raw_svc not in (None, "") else None
                order = db.create_order(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    service_id=service_id,
                    preferred_time=str(data.get("preferred_time", "")),
                    notes=str(data.get("notes", "")),
                )
                self._send_json({"order": order, "state": db.get_state()}, HTTPStatus.CREATED)
                return

            if path == "/api/chat":
                message = str(data.get("message", "")).strip()
                if not message:
                    self._send_json({"error": "Xabar bo'sh bo'lmasin"}, HTTPStatus.BAD_REQUEST)
                    return
                reply = ai_helper.generate_ai_reply(message, db.get_state())
                self._send_json(reply)
                return

            if path == "/api/payments/checkout":
                plan_id = str(data.get("plan_id", "pro")).strip()
                provider = str(data.get("provider", "click")).strip()
                business_name = str(data.get("business_name", "")).strip()
                plan = db.get_plan(plan_id)
                if not plan:
                    self._send_json({"error": "Tarif topilmadi"}, HTTPStatus.BAD_REQUEST)
                    return

                checkout = payments.build_checkout(
                    provider=provider,
                    amount_uzs=plan["price_uzs"],
                    plan_id=plan_id,
                    business_name=business_name,
                )
                payment = db.create_payment(
                    plan_id=plan_id,
                    provider=checkout["provider"],
                    business_name=business_name,
                    invoice_code=checkout["invoice_code"],
                )
                self._send_json(
                    {
                        "payment": payment,
                        "checkout_url": checkout["checkout_url"],
                        "mode": checkout["mode"],
                        "state": db.get_state(),
                    },
                    HTTPStatus.CREATED,
                )
                return

            if path == "/api/payments/confirm":
                payment_id = int(data.get("payment_id", 0))
                updated = db.confirm_payment(payment_id)
                if not updated:
                    self._send_json({"error": "To'lov topilmadi"}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json({"payment": updated, "state": db.get_state()})
                return

            self._send_json({"error": "Endpoint topilmadi"}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/orders/"):
            try:
                order_id = int(path.rsplit("/", 1)[-1])
                data = self._read_json()
                status = str(data.get("status", "")).strip()
                updated = db.update_order_status(order_id, status)
                if not updated:
                    self._send_json({"error": "Buyurtma topilmadi"}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json({"order": updated, "state": db.get_state()})
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"error": "Endpoint topilmadi"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


def run_server() -> None:
    db.init_db()
    default_host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    host = os.environ.get("HOST", default_host)
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), BiznesHandler)
    print(f"BiznesAI CRM ishga tushdi: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer to'xtatildi.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
