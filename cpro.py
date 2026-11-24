# ==============================================================================
# ARCHIVO: cpro.py
# ROL: MÓDULO DE COTIZACIONESPRO (App hija del gateway)
# DESCRIPCIÓN: Base de datos SQLite real para CotizacionesPro.
#              Guarda cotizaciones, itinerarios, clientes, catálogo y ajustes
#              como documentos JSON dentro de la base 'cpro' del gateway.
# ==============================================================================

import json
import time
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from sqlalchemy import text
from database import get_db_session

cpro_bp = Blueprint('cpro_bp', __name__)

APP_SLUG = 'cpro'

DDL = """
CREATE TABLE IF NOT EXISTS cpro_doc (
    store VARCHAR(40) NOT NULL,
    doc_id VARCHAR(120) NOT NULL,
    data TEXT NOT NULL,
    updated INTEGER NOT NULL,
    PRIMARY KEY (store, doc_id)
)
"""


def _session():
    """Sesión a la base SQLite de CotizacionesPro, creando la tabla si falta."""
    session = get_db_session(APP_SLUG)
    session.execute(text(DDL))
    session.commit()
    return session


@cpro_bp.route('/api/cpro/ping', methods=['GET', 'OPTIONS'])
@cross_origin()
def cpro_ping():
    """Salud del módulo + conteo de documentos por store."""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    session = None
    try:
        session = _session()
        rows = session.execute(
            text("SELECT store, COUNT(*) FROM cpro_doc GROUP BY store")
        ).fetchall()
        return jsonify({
            "status": "ok",
            "app": "cpro",
            "db": "sqlite",
            "stores": {r[0]: r[1] for r in rows}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@cpro_bp.route('/api/cpro/all', methods=['GET', 'OPTIONS'])
@cross_origin()
def cpro_all():
    """Descarga toda la base: {store: {doc_id: data}}"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    session = None
    try:
        session = _session()
        rows = session.execute(
            text("SELECT store, doc_id, data FROM cpro_doc")
        ).fetchall()
        out = {}
        for store, doc_id, data in rows:
            out.setdefault(store, {})[doc_id] = json.loads(data)
        return jsonify({"status": "ok", "data": out})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@cpro_bp.route('/api/cpro/put', methods=['POST', 'OPTIONS'])
@cross_origin()
def cpro_put():
    """Guarda/actualiza un documento. Body: {store, id, data}"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    session = None
    try:
        body = request.get_json(force=True)
        store = str(body.get('store', ''))[:40]
        doc_id = str(body.get('id', ''))[:120]
        if not store or doc_id == '':
            return jsonify({"error": "store e id requeridos"}), 400
        payload = json.dumps(body.get('data'), ensure_ascii=False)
        session = _session()
        session.execute(text(
            "INSERT INTO cpro_doc (store, doc_id, data, updated) VALUES (:s, :i, :d, :u) "
            "ON CONFLICT(store, doc_id) DO UPDATE SET data=:d, updated=:u"
        ), {"s": store, "i": doc_id, "d": payload, "u": int(time.time())})
        session.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@cpro_bp.route('/api/cpro/del', methods=['POST', 'OPTIONS'])
@cross_origin()
def cpro_del():
    """Elimina un documento. Body: {store, id}"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    session = None
    try:
        body = request.get_json(force=True)
        session = _session()
        session.execute(
            text("DELETE FROM cpro_doc WHERE store = :s AND doc_id = :i"),
            {"s": str(body.get('store', ''))[:40], "i": str(body.get('id', ''))[:120]}
        )
        session.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@cpro_bp.route('/api/cpro/bulk', methods=['POST', 'OPTIONS'])
@cross_origin()
def cpro_bulk():
    """Importación masiva (respaldo). Body: {store: {doc_id: data}}.
    Reemplaza TODO el contenido de los stores incluidos."""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    session = None
    try:
        body = request.get_json(force=True) or {}
        data = body.get('data', body)
        if not isinstance(data, dict):
            return jsonify({"error": "Formato inválido"}), 400
        session = _session()
        now = int(time.time())
        n = 0
        for store, docs in data.items():
            if not isinstance(docs, dict):
                continue
            s = str(store)[:40]
            session.execute(text("DELETE FROM cpro_doc WHERE store = :s"), {"s": s})
            for doc_id, doc in docs.items():
                session.execute(text(
                    "INSERT INTO cpro_doc (store, doc_id, data, updated) VALUES (:s, :i, :d, :u)"
                ), {"s": s, "i": str(doc_id)[:120], "d": json.dumps(doc, ensure_ascii=False), "u": now})
                n += 1
        session.commit()
        return jsonify({"status": "ok", "imported": n})
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


print("[OK] CotizacionesPro (cpro) — módulo SQLite cargado")
