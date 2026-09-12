#!/usr/bin/env python3
import unicodedata
from chat import chat

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


def main():
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
            "contacta", "consultanos",
        ])
    )

    test(
        "Tema fuera de alcance",
        "Cuentame un chiste",
        lambda r: "solo soy un asistente" in norm(r) or "solo puedo" in norm(r)
    )

    print("\n" + "=" * 50)
    pasaron = sum(resultados)
    total = len(resultados)
    print(f"  RESULTADO: {pasaron}/{total} TESTS PASARON {PASS if pasaron == total else FAIL}")
    print("=" * 50)


if __name__ == "__main__":
    main()
