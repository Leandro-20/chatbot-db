#!/usr/bin/env python3
import unicodedata
from chat import chat
from migrate import main as migrar
import db_api

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
resultados = []


def norm(texto):
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def test(nombre, pregunta, validador):
    print(f"\nTEST: {nombre}")
    print(f"  Pregunta: \"{pregunta}\"")
    respuesta, _ = chat(pregunta)
    print(f"  Respuesta: {respuesta[:200]}...")
    if validador(respuesta):
        print(f"  {PASS}")
        resultados.append(True)
    else:
        print(f"  {FAIL}")
        resultados.append(False)


def test_doble_turno(nombre, msg1, msg2, validador):
    print(f"\nTEST: {nombre}")
    print(f"  Turno 1: \"{msg1}\"")
    resp1, historial = chat(msg1)
    print(f"  Respuesta 1: {resp1[:150]}...")
    print(f"  Turno 2: \"{msg2}\"")
    resp2, _ = chat(msg2, historial)
    print(f"  Respuesta 2: {resp2[:150]}...")
    if validador(resp1, resp2):
        print(f"  {PASS}")
        resultados.append(True)
    else:
        print(f"  {FAIL}")
        resultados.append(False)


def main():
    print("Reseteando DB a estado semilla...")
    migrar()
    print("=" * 50)
    print("  TESTS DEL CHATBOT DB")
    print("=" * 50)

    test(
        "DB: buscar producto (laptops)",
        "Que laptops tienen?",
        lambda r: "laptop" in norm(r) and ("1299" in r or "899" in r)
    )

    test(
        "DB: stock agotado",
        "El mouse inalambrico tiene stock?",
        lambda r: "mouse" in norm(r) and ("agotado" in norm(r) or "sin stock" in norm(r) or "0" in r or "no disponible" in norm(r))
    )

    test(
        "DB: estado de pedido",
        "Cual es el estado del pedido PED-002?",
        lambda r: "enviado" in norm(r) or "trk-789456123" in norm(r)
    )

    test(
        "Politica: devoluciones",
        "Cual es el plazo de devolucion?",
        lambda r: "30" in r and "dia" in norm(r)
    )

    test(
        "Politica: garantias",
        "Que garantia tienen los monitores?",
        lambda r: "18" in r and "mes" in norm(r)
    )

    test(
        "Politica: pagos",
        "Aceptan tarjeta en cuotas?",
        lambda r: "tarjeta" in norm(r) and "cuota" in norm(r)
    )

    test(
        "Sin cobertura (no inventa)",
        "Cuanto cuesta el envio a Espana?",
        lambda r: any(x in norm(r) for x in [
            "no tengo", "no cuento", "no dispongo", "desconozco",
            "no contamos", "no incluye", "no realizamos", "no hacemos",
            "contacta", "consultanos", "dentro del pa", "no ofrecemos",
        ])
    )

    test(
        "Tema fuera de alcance",
        "Cuentame un chiste",
        lambda r: "solo soy un asistente" in norm(r) or "solo puedo" in norm(r)
    )

    def hay_producto(nombre):
        res = db_api.buscar_producto(nombre)
        return res.get("productos", [None])[0] if "productos" in res else None

    def hay_auditoria(accion, texto):
        import sqlite3, os
        con = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tienda.db"))
        rows = con.execute("SELECT detalle FROM movimientos WHERE accion = ?", (accion,)).fetchall()
        con.close()
        return any(texto.lower() in r[0].lower() for r in rows)

    test_doble_turno(
        "Alta con confirmacion",
        "Agrega el producto Parlante Bluetooth X200, categoria audio, precio 59.99, "
        "descripcion parlante portatil con bluetooth, stock 20",
        "si, confirmo la operacion",
        lambda r1, r2: (
            (lambda p: p is not None and p["precio"] == 59.99 and p["stock"] == 20)
            (hay_producto("Parlante Bluetooth X200"))
            and hay_auditoria("alta", "Parlante Bluetooth X200")
        )
    )

    test_doble_turno(
        "Stock: sumar con confirmacion",
        "Suma 5 unidades al stock del producto 1",
        "si, confirmo",
        lambda r1, r2: db_api.obtener_producto(1)["producto"]["stock"] == 20
    )

    print("\nTEST: Validacion rechaza precio negativo (unitario)")
    res = db_api.agregar_producto("Producto Malo", "audio", -50, "descripcion")
    if "error" in res and hay_producto("Producto Malo") is None:
        print(f"  {PASS}")
        resultados.append(True)
    else:
        print(f"  {FAIL}")
        resultados.append(False)

    n_antes = db_api.resumen_ventas()["total_productos_catalogo"]
    test_doble_turno(
        "Cancelacion: 'no' no escribe nada",
        "Agrega el producto Cafetera Express Pro, categoria audio, precio 89.99, "
        "descripcion cafetera electrica, stock 4",
        "no, cancela la operacion",
        lambda r1, r2: (
            hay_producto("Cafetera Express Pro") is None
            and db_api.resumen_ventas()["total_productos_catalogo"] == n_antes
        )
    )

    test_doble_turno(
        "Baja logica con confirmacion",
        "Desactiva el producto 11",
        "si, confirmo",
        lambda r1, r2: (
            (lambda p: p["disponible"] is False) (db_api.obtener_producto(11)["producto"])
            and hay_auditoria("baja", "11")
        )
    )

    print("\n" + "=" * 50)
    pasaron = sum(resultados)
    total = len(resultados)
    print(f"  RESULTADO: {pasaron}/{total} TESTS PASARON {PASS if pasaron == total else FAIL}")
    print("=" * 50)


if __name__ == "__main__":
    main()
