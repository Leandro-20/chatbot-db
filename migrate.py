#!/usr/bin/env python3
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGEN = BASE_DIR
DB_PATH = os.path.join(BASE_DIR, "tienda.db")

POLITICAS = [
    ("devoluciones", "Politica de devoluciones",
     "Aceptamos devoluciones dentro de los 30 dias corridos desde la fecha de entrega. "
     "El producto debe estar sin uso, con embalaje original, manuales, accesorios y factura. "
     "No admiten devolucion: software con licencia activada, productos personalizados o con signos de mal uso. "
     "Proceso: solicitar con numero de pedido, validamos en 48 horas habiles, coordinamos retiro, "
     "y reembolsamos por el mismo medio de pago en 5 a 10 dias habiles."),
    ("garantias", "Garantias",
     "Todos los productos tienen 12 meses de garantia contra defectos de fabricacion. "
     "Las computadoras tienen 24 meses y los monitores 18 meses. "
     "No cubre: golpes, caidas, liquidos, sobretension electrica, reparaciones de terceros no autorizados, "
     "ni desgaste normal (baterias despues de 6 meses). "
     "Reclamo: contactar con numero de pedido o factura, describir la falla con fotos o video. "
     "Evaluamos en 72 horas habiles. Reparacion estimada: 7 a 15 dias habiles."),
    ("envios", "Envios",
     "Capital y alrededores: 24 a 48 horas habiles. Interior: 3 a 7 dias habiles. "
     "Pedidos antes de las 14:00 se despachan el mismo dia habil. "
     "Envio gratis desde $50000; si no, $4990 capital y $7990 interior. Retiro en sucursal sin costo. "
     "Todo envio incluye tracking por email. Retiro: lunes a viernes 9:00 a 18:00, sabados 9:00 a 13:00."),
    ("faq_pagos", "Medios de pago",
     "Aceptamos tarjetas de credito y debito, transferencia bancaria y efectivo para retiros en sucursal. "
     "Con tarjeta de credito hasta 12 cuotas sin interes segun promociones vigentes. "
     "Emitimos factura fiscal: consumidor final o empresa con datos fiscales."),
    ("faq_pedido", "Consultar estado de pedido",
     "Para consultar un pedido necesitas el numero (formato PED-001). "
     "Preguntale a este asistente indicando tu numero y te informa el estado: procesando, enviado o entregado."),
    ("faq_contacto", "Contacto y horarios",
     "Atencion: lunes a viernes 9:00 a 18:00, sabados 9:00 a 13:00. "
     "Email ayuda@mitienda.com, telefono 0800-123-4567. Fuera de horario dejanos tu consulta."),
]

SCHEMA = """
DROP TABLE IF EXISTS pedido_items;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS politicas;
DROP TABLE IF EXISTS movimientos;

CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    disponible INTEGER NOT NULL
);

CREATE TABLE pedidos (
    id TEXT PRIMARY KEY,
    cliente TEXT NOT NULL,
    email TEXT NOT NULL,
    total REAL NOT NULL,
    estado TEXT NOT NULL,
    fecha_pedido TEXT NOT NULL,
    fecha_envio TEXT,
    fecha_entrega TEXT,
    tracking TEXT,
    motivo_cancelacion TEXT
);

CREATE TABLE pedido_items (
    pedido_id TEXT NOT NULL REFERENCES pedidos(id),
    producto_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio REAL NOT NULL
);

CREATE TABLE politicas (
    clave TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    contenido TEXT NOT NULL
);

CREATE TABLE movimientos (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    accion TEXT NOT NULL,
    detalle TEXT NOT NULL
);
"""


def main():
    with open(os.path.join(ORIGEN, "productos.json"), encoding="utf-8") as f:
        productos = json.load(f)["productos"]
    with open(os.path.join(ORIGEN, "pedidos.json"), encoding="utf-8") as f:
        pedidos = json.load(f)["pedidos"]

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(SCHEMA)

    for p in productos:
        cur.execute(
            "INSERT INTO productos VALUES (?,?,?,?,?,?,?)",
            (p["id"], p["nombre"], p["categoria"], p["precio"],
             p["stock"], p["descripcion"], int(p["disponible"])),
        )

    for p in pedidos:
        cur.execute(
            "INSERT INTO pedidos VALUES (?,?,?,?,?,?,?,?,?,?)",
            (p["id"], p["cliente"], p["email"], p["total"], p["estado"],
             p["fecha_pedido"], p.get("fecha_envio"), p.get("fecha_entrega"),
             p.get("tracking"), p.get("motivo_cancelacion")),
        )
        for it in p["productos"]:
            cur.execute(
                "INSERT INTO pedido_items VALUES (?,?,?,?,?)",
                (p["id"], it["id"], it["nombre"], it["cantidad"], it["precio"]),
            )

    cur.executemany("INSERT INTO politicas VALUES (?,?,?)", POLITICAS)
    con.commit()

    n_prod = cur.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    n_ped = cur.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    n_pol = cur.execute("SELECT COUNT(*) FROM politicas").fetchone()[0]
    con.close()
    print(f"OK: {n_prod} productos, {n_ped} pedidos, {n_pol} politicas en tienda.db")


if __name__ == "__main__":
    main()
