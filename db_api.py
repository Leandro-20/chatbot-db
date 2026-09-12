import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tienda.db")


def _con():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _prod(row):
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "categoria": row["categoria"],
        "precio": row["precio"],
        "stock": row["stock"],
        "descripcion": row["descripcion"],
        "disponible": bool(row["disponible"]),
    }


def buscar_producto(nombre):
    con = _con()
    like = f"%{nombre.lower()}%"
    rows = con.execute(
        "SELECT * FROM productos WHERE LOWER(nombre) LIKE ? OR LOWER(descripcion) LIKE ?",
        (like, like),
    ).fetchall()
    con.close()
    resultados = [_prod(r) for r in rows]
    if not resultados:
        return {"error": f"No encontre productos con '{nombre}'"}
    return {"productos": resultados, "total": len(resultados)}


def productos_por_categoria(categoria):
    con = _con()
    rows = con.execute(
        "SELECT * FROM productos WHERE LOWER(categoria) LIKE ?",
        (f"%{categoria.lower()}%",),
    ).fetchall()
    cats = [r["categoria"] for r in con.execute("SELECT DISTINCT categoria FROM productos").fetchall()]
    con.close()
    resultados = [_prod(r) for r in rows]
    if not resultados:
        return {"error": f"No hay productos en '{categoria}'", "categorias_disponibles": sorted(set(cats))}
    return {"productos": resultados, "total": len(resultados), "categoria": categoria}


def obtener_producto(producto_id):
    con = _con()
    row = con.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    con.close()
    if row is None:
        return {"error": f"Producto con ID {producto_id} no encontrado"}
    return {"producto": _prod(row)}


def verificar_stock(producto_id):
    con = _con()
    row = con.execute("SELECT nombre, stock, disponible FROM productos WHERE id = ?", (producto_id,)).fetchone()
    con.close()
    if row is None:
        return {"error": f"Producto con ID {producto_id} no encontrado"}
    disponible = bool(row["disponible"])
    return {
        "producto": row["nombre"],
        "stock": row["stock"],
        "disponible": disponible,
        "mensaje": f"Hay {row['stock']} unidades disponibles" if disponible else "Agotado",
    }


def productos_disponibles():
    con = _con()
    rows = con.execute("SELECT * FROM productos WHERE disponible = 1").fetchall()
    con.close()
    disponibles = [_prod(r) for r in rows]
    return {"productos": disponibles, "total": len(disponibles)}


def productos_agotados():
    con = _con()
    rows = con.execute("SELECT * FROM productos WHERE disponible = 0").fetchall()
    con.close()
    agotados = [_prod(r) for r in rows]
    return {"productos": agotados, "total": len(agotados)}


def _pedido(con, pedido_id):
    row = con.execute("SELECT * FROM pedidos WHERE UPPER(id) = ?", (pedido_id.upper(),)).fetchone()
    if row is None:
        return None
    pedido = dict(row)
    items = con.execute(
        "SELECT producto_id AS id, nombre, cantidad, precio FROM pedido_items WHERE pedido_id = ?",
        (pedido["id"],),
    ).fetchall()
    pedido["productos"] = [dict(i) for i in items]
    return pedido


def buscar_pedido(pedido_id):
    con = _con()
    pedido = _pedido(con, pedido_id)
    con.close()
    if pedido is None:
        return {"error": f"Pedido {pedido_id} no encontrado"}
    return {"pedido": pedido}


def pedidos_por_cliente(nombre_cliente):
    con = _con()
    rows = con.execute(
        "SELECT id FROM pedidos WHERE LOWER(cliente) LIKE ?",
        (f"%{nombre_cliente.lower()}%",),
    ).fetchall()
    resultados = [_pedido(con, r["id"]) for r in rows]
    con.close()
    if not resultados:
        return {"error": f"No encontre pedidos para '{nombre_cliente}'"}
    return {"pedidos": resultados, "total": len(resultados), "cliente": nombre_cliente}


def resumen_ventas():
    con = _con()
    total_ventas = con.execute(
        "SELECT COALESCE(SUM(total),0) FROM pedidos WHERE estado != 'cancelado'"
    ).fetchone()[0]
    total_pedidos = con.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    por_estado = {r["estado"]: r["n"] for r in
                  con.execute("SELECT estado, COUNT(*) AS n FROM pedidos GROUP BY estado").fetchall()}
    total_productos = con.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    con.close()
    return {
        "total_ventas": total_ventas,
        "total_pedidos": total_pedidos,
        "pedidos_por_estado": por_estado,
        "total_productos_catalogo": total_productos,
    }


def obtener_politica(clave):
    con = _con()
    row = con.execute("SELECT clave, titulo, contenido FROM politicas WHERE clave = ?",
                      (clave.lower(),)).fetchone()
    claves = [r["clave"] for r in con.execute("SELECT clave FROM politicas").fetchall()]
    con.close()
    if row is None:
        return {"error": f"No hay politica '{clave}'", "claves_disponibles": claves}
    return {"politica": dict(row)}
