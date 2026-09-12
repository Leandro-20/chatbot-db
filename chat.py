#!/usr/bin/env python3
import requests
import json
import sys
from db_api import (
    buscar_producto,
    productos_por_categoria,
    obtener_producto,
    verificar_stock,
    productos_disponibles,
    productos_agotados,
    buscar_pedido,
    pedidos_por_cliente,
    resumen_ventas,
    obtener_politica,
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "chatbot-db"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_producto",
            "description": "Busca productos por nombre o descripcion",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "Nombre o descripcion del producto a buscar"
                    }
                },
                "required": ["nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "productos_por_categoria",
            "description": "Lista todos los productos de una categoria",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": "Nombre de la categoria (ej: computadoras, monitores, perifericos, audio, almacenamiento, redes, impresoras)"
                    }
                },
                "required": ["categoria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_producto",
            "description": "Obtiene los detalles de un producto por su ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "producto_id": {
                        "type": "integer",
                        "description": "ID numerico del producto"
                    }
                },
                "required": ["producto_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verificar_stock",
            "description": "Verifica la disponibilidad y stock de un producto",
            "parameters": {
                "type": "object",
                "properties": {
                    "producto_id": {
                        "type": "integer",
                        "description": "ID numerico del producto"
                    }
                },
                "required": ["producto_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "productos_disponibles",
            "description": "Lista todos los productos que estan disponibles en stock",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "productos_agotados",
            "description": "Lista los productos que estan agotados",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_pedido",
            "description": "Busca un pedido por su ID y muestra su estado",
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {
                        "type": "string",
                        "description": "ID del pedido (ej: PED-001)"
                    }
                },
                "required": ["pedido_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pedidos_por_cliente",
            "description": "Busca todos los pedidos de un cliente por su nombre",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {
                        "type": "string",
                        "description": "Nombre del cliente"
                    }
                },
                "required": ["nombre_cliente"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_ventas",
            "description": "Muestra un resumen de ventas totales, pedidos por estado y metricas del catalogo",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_politica",
            "description": "Obtiene el texto de una politica de la tienda (devoluciones, garantias, envios o FAQs). Usala para preguntas sobre condiciones, plazos o medios de pago",
            "parameters": {
                "type": "object",
                "properties": {
                    "clave": {
                        "type": "string",
                        "description": "Clave de la politica (ej: devoluciones, garantias, envios, faq_pagos, faq_pedido, faq_contacto)"
                    }
                },
                "required": ["clave"]
            }
        }
    }
]

TOOL_MAP = {
    "buscar_producto": buscar_producto,
    "productos_por_categoria": productos_por_categoria,
    "obtener_producto": obtener_producto,
    "verificar_stock": verificar_stock,
    "productos_disponibles": productos_disponibles,
    "productos_agotados": productos_agotados,
    "buscar_pedido": buscar_pedido,
    "pedidos_por_cliente": pedidos_por_cliente,
    "resumen_ventas": resumen_ventas,
    "obtener_politica": obtener_politica,
}


def ejecutar_tool(tool_name, arguments):
    if tool_name in TOOL_MAP:
        func = TOOL_MAP[tool_name]
        if arguments:
            return func(**arguments)
        return func()
    return {"error": f"Herramienta '{tool_name}' no disponible"}


def chat(mensaje, historial=None):
    if historial is None:
        historial = []

    historial.append({"role": "user", "content": mensaje})

    payload = {
        "model": MODEL,
        "messages": historial,
        "tools": TOOLS,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        message = data["message"]

        if "tool_calls" in message and message["tool_calls"]:
            historial.append(message)

            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                arguments = tool_call["function"].get("arguments", {})
                print(f"  [Usando herramienta: {func_name}]")
                resultado = ejecutar_tool(func_name, arguments)
                historial.append({
                    "role": "tool",
                    "content": json.dumps(resultado, ensure_ascii=False)
                })

            payload2 = {
                "model": MODEL,
                "messages": historial,
                "tools": TOOLS,
                "stream": False,
            }
            response2 = requests.post(OLLAMA_URL, json=payload2, timeout=120)
            response2.raise_for_status()
            data2 = response2.json()
            respuesta = data2["message"]["content"]
        else:
            respuesta = message["content"]

        historial.append({"role": "assistant", "content": respuesta})
        return respuesta, historial

    except requests.exceptions.ConnectionError:
        return "Error: No se pudo conectar a Ollama. Asegurate de que este corriendo.", historial
    except Exception as e:
        return f"Error: {e}", historial


def main():
    print("=" * 50)
    print("  CHATBOT DB - VENTAS Y ATENCION AL CLIENTE")
    print("  Modelo: qwen3:8b + SQLite | 'salir' para terminar")
    print("=" * 50)
    print()

    historial = []

    while True:
        try:
            usuario = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego!")
            break

        if not usuario:
            continue
        if usuario.lower() in ("salir", "exit", "quit"):
            print("Hasta luego!")
            break

        respuesta, historial = chat(usuario, historial)
        print(f"Bot: {respuesta}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mensaje = " ".join(sys.argv[1:])
        respuesta, _ = chat(mensaje)
        print(respuesta)
    else:
        main()
