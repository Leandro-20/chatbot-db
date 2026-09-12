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

## Archivos

| Archivo | Funcion |
|---------|---------|
| `Modelfile` | Modelo chatbot-db con prompt + politicas |
| `migrate.py` | Crea tienda.db desde los JSON de chatbot-ollama |
| `db_api.py` | 10 funciones de consulta contra SQLite |
| `chat.py` | Chat con tool calling (10 tools) |
| `test_db.py` | 8 tests automaticos |
| `tienda.db` | Base SQLite (generada, no se commitea) |

## Agregar datos

- **Productos/pedidos**: cargalos en la DB (o actualiza los JSON origen y corre `migrate.py`)
- **Politicas**: `INSERT INTO politicas` o edita `POLITICAS` en `migrate.py` y re-migra
- **Prompt**: edita `Modelfile` y ejecuta `./build.sh`
