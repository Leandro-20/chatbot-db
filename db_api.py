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


CATEGORIAS = ["computadoras", "monitores", "perifericos", "audio",
              "almacenamiento", "impresoras", "redes"]


def _log(con, accion, detalle):
    con.execute("INSERT INTO movimientos (accion, detalle) VALUES (?, ?)", (accion, detalle))


def _validar_producto(nombre, categoria, precio, descripcion, stock=0):
    nombre = (nombre or "").strip()
    if not nombre:
        return "El nombre no puede estar vacio"
    categoria = (categoria or "").strip().lower()
    if categoria not in CATEGORIAS:
        return f"Categoria invalida '{categoria}'. Valididas: {', '.join(CATEGORIAS)}"
    try:
        precio = float(precio)
    except (TypeError, ValueError):
        return f"Precio invalido '{precio}'"
    if precio <= 0:
        return f"Precio invalido '{precio}': debe ser mayor a 0"
    try:
        stock = int(stock)
    except (TypeError, ValueError):
        return f"Stock invalido '{stock}'"
    if stock < 0:
        return f"Stock invalido '{stock}': no puede ser negativo"
    if not (descripcion or "").strip():
        return "La descripcion no puede estar vacia"
    return None


def agregar_producto(nombre, categoria, precio, descripcion, stock=0):
    error = _validar_producto(nombre, categoria, precio, descripcion, stock)
    if error:
        return {"error": error}
    con = _con()
    dup = con.execute("SELECT id FROM productos WHERE LOWER(nombre) = ?",
                      (nombre.strip().lower(),)).fetchone()
    if dup:
        con.close()
        return {"error": f"Ya existe un producto con ese nombre (ID {dup['id']})"}
    cur = con.execute(
        "INSERT INTO productos (nombre, categoria, precio, stock, descripcion, disponible)"
        " VALUES (?,?,?,?,?,?)",
        (nombre.strip(), categoria.strip().lower(), float(precio),
         int(stock), descripcion.strip(), 1 if int(stock) > 0 else 0),
    )
    nuevo_id = cur.lastrowid
    _log(con, "alta", f"Producto {nuevo_id} '{nombre.strip()}' creado")
    con.commit()
    row = con.execute("SELECT * FROM productos WHERE id = ?", (nuevo_id,)).fetchone()
    con.close()
    return {"producto": _prod(row), "mensaje": f"Producto creado con ID {nuevo_id}"}


def actualizar_producto(producto_id, nombre=None, categoria=None, precio=None,
                        descripcion=None, disponible=None):
    con = _con()
    row = con.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        con.close()
        return {"error": f"Producto con ID {producto_id} no encontrado"}
    anterior = _prod(row)
    cambios = {}
    if nombre is not None:
        nombre = nombre.strip()
        if not nombre:
            con.close()
            return {"error": "El nombre no puede estar vacio"}
        dup = con.execute(
            "SELECT id FROM productos WHERE LOWER(nombre) = ? AND id != ?",
            (nombre.lower(), producto_id)).fetchone()
        if dup:
            con.close()
            return {"error": f"Ya existe otro producto con ese nombre (ID {dup['id']})"}
        cambios["nombre"] = nombre
    if categoria is not None:
        categoria = categoria.strip().lower()
        if categoria not in CATEGORIAS:
            con.close()
            return {"error": f"Categoria invalida '{categoria}'. Valididas: {', '.join(CATEGORIAS)}"}
        cambios["categoria"] = categoria
    if precio is not None:
        try:
            precio = float(precio)
        except (TypeError, ValueError):
            con.close()
            return {"error": f"Precio invalido '{precio}'"}
        if precio <= 0:
            con.close()
            return {"error": f"Precio invalido '{precio}': debe ser mayor a 0"}
        cambios["precio"] = precio
    if descripcion is not None:
        descripcion = descripcion.strip()
        if not descripcion:
            con.close()
            return {"error": "La descripcion no puede estar vacia"}
        cambios["descripcion"] = descripcion
    if disponible is not None:
        cambios["disponible"] = 1 if disponible else 0
    if not cambios:
        con.close()
        return {"error": "No indicaste ningun campo a modificar"}
    con.execute(
        f"UPDATE productos SET {', '.join(f'{k} = ?' for k in cambios)} WHERE id = ?",
        (*cambios.values(), producto_id),
    )
    _log(con, "modificacion", f"Producto {producto_id}: {', '.join(cambios)}")
    con.commit()
    row = con.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    con.close()
    return {"anterior": anterior, "producto": _prod(row)}


def actualizar_stock(producto_id, cantidad, modo="fijar"):
    con = _con()
    row = con.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        con.close()
        return {"error": f"Producto con ID {producto_id} no encontrado"}
    if modo not in ("fijar", "sumar", "restar"):
        con.close()
        return {"error": f"Modo invalido '{modo}'. Usa: fijar, sumar o restar"}
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        con.close()
        return {"error": f"Cantidad invalida '{cantidad}'"}
    anterior = row["stock"]
    nuevo = cantidad if modo == "fijar" else anterior + cantidad if modo == "sumar" else anterior - cantidad
    if nuevo < 0:
        con.close()
        return {"error": f"Stock resultante invalido ({nuevo}): no puede ser negativo"}
    disponible = 1 if nuevo > 0 else 0
    con.execute("UPDATE productos SET stock = ?, disponible = ? WHERE id = ?",
                (nuevo, disponible, producto_id))
    _log(con, "stock", f"Producto {producto_id}: {anterior} -> {nuevo} (modo {modo})")
    con.commit()
    con.close()
    return {
        "producto": row["nombre"],
        "stock_anterior": anterior,
        "stock": nuevo,
        "disponible": bool(disponible),
        "mensaje": f"Stock actualizado: {anterior} -> {nuevo}",
    }


def desactivar_producto(producto_id):
    con = _con()
    row = con.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        con.close()
        return {"error": f"Producto con ID {producto_id} no encontrado"}
    con.execute("UPDATE productos SET disponible = 0 WHERE id = ?", (producto_id,))
    _log(con, "baja", f"Producto {producto_id} '{row['nombre']}' desactivado (soft)")
    con.commit()
    con.close()
    return {"producto": row["nombre"], "disponible": False,
            "mensaje": "Producto desactivado. Sigue en la base y se puede reactivar."}


def reactivar_producto(producto_id):
    con = _con()
    row = con.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        con.close()
        return {"error": f"Producto con ID {producto_id} no encontrado"}
    con.execute("UPDATE productos SET disponible = 1 WHERE id = ?", (producto_id,))
    _log(con, "reactivacion", f"Producto {producto_id} '{row['nombre']}' reactivado")
    con.commit()
    con.close()
    return {"producto": row["nombre"], "disponible": True, "mensaje": "Producto reactivado."}
