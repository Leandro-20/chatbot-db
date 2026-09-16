# Chatbot DB - Ventas y Atencion al Cliente

Ollama custom + SQLite, sin RAG. Productos, pedidos y politicas
se consultan en vivo con tool calling. Nada se inventa.

## Requisitos
- Ollama instalado y corriendo
- Python 3 instalado (sqlite3 viene incluido)
- Modelo qwen3:8b descargado

## Instalacion

```bash
cd chatbot-db
./build.sh
```

Esto migra los datos a `tienda.db` y crea el modelo `chatbot-db`.

## Comandos

### Chat interactivo
```bash
python3 chat.py
```

### Pregunta rapida
```bash
python3 chat.py "Que laptops tienen?"
python3 chat.py "Cual es el estado del pedido PED-002?"
python3 chat.py "Cual es el plazo de devolucion?"
```

### Correr los tests
```bash
python3 test_db.py
```

### Re-migrar datos (si cambian los JSON origen)
```bash
python3 migrate.py
```

## Operaciones de escritura

Toda escritura pide confirmacion: el bot muestra un RESUMEN,
pregunta "¿Confirmas?" y solo ejecuta ante un si explicito.
"No" o ambiguedad cancela sin escribir. Todo queda en auditoria
(tabla `movimientos`).

```bash
python3 chat.py "Agrega el Parlante X200, audio, 59.99, parlante portatil, stock 20"
# bot: muestra resumen y pide confirmacion -> responder "si"

python3 chat.py "Suma 5 unidades al stock del producto 1"
python3 chat.py "Desactiva el producto 11"   # baja logica, reversible
python3 chat.py "Reactiva el producto 11"
```

Validaciones automaticas: precio > 0, stock resultante >= 0,
categoria valida, sin nombres duplicados. Sin borrado fisico.

## Archivos

| Archivo | Funcion |
|---------|---------|
| `Modelfile` | Modelo chatbot-db con prompt + politicas |
| `migrate.py` | Crea tienda.db desde los JSON locales |
| `productos.json` | Catalogo de productos (fuente de la DB) |
| `pedidos.json` | Pedidos (fuente de la DB) |
| `db_api.py` | 15 funciones contra SQLite (10 lectura + 5 escritura + auditoria) |
| `chat.py` | Chat con tool calling (15 tools) |
| `test_db.py` | 14 tests automaticos |
| `tienda.db` | Base SQLite (generada, no se commitea) |

## Agregar datos

- **Productos/pedidos**: edita `productos.json` / `pedidos.json` y corre `migrate.py` (o cargalos directo en la DB)
- **Politicas**: `INSERT INTO politicas` o edita `POLITICAS` en `migrate.py` y re-migra
- **Prompt**: edita `Modelfile` y ejecuta `./build.sh`
