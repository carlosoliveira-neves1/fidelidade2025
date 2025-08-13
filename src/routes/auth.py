# src/routes/auth.py
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta
import secrets

from src.models.user import db
from src.models.auth import Usuario, RoleEnum

auth_bp = Blueprint("auth", __name__)

# -------- decorators --------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Não autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper

def roles_required(*roles: tuple[str]):
    want = set(roles)
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            uid = session.get("user_id")
            role = session.get("role")
            if not uid:
                return jsonify({"error": "Não autenticado"}), 401
            if role not in want:
                return jsonify({"error": "Sem permissão"}), 403
            return f(*args, **kwargs)
        return wrapper
    return deco

# -------- rotas --------
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Informe usuário e senha"}), 400

    u = Usuario.query.filter(Usuario.username.ilike(username)).first()
    if not u or not u.check_password(password) or not u.ativo:
        return jsonify({"error": "Credenciais inválidas"}), 401

    session.clear()
    session["user_id"] = u.id
    session["role"] = u.role.value if u.role else None
    session["nome"] = u.nome

    return jsonify({"ok": True, "user": u.to_dict()})

@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@auth_bp.route("/auth/me", methods=["GET"])
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"authenticated": False}), 200
    u = Usuario.query.get(uid)
    if not u:
        session.clear()
        return jsonify({"authenticated": False}), 200

    # compat: devolve tanto em 'user' quanto campos raiz (role/permissoes)
    payload = {
        "authenticated": True,
        "user": u.to_dict(),
        "role": u.role.value if u.role else None,
        "permissoes": u.permissoes or {},
    }
    return jsonify(payload)

# -------- Esqueci minha senha (token simples salvo em permissoes.reset) --------
@auth_bp.route("/auth/forgot", methods=["POST"])
def forgot():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error":"username obrigatório"}), 400

    u = Usuario.query.filter_by(username=username).first()
    # sempre 200 para não vazar existência
    if not u:
        return jsonify({"ok": True})

    perms = u.permissoes or {}
    tok = secrets.token_hex(3).upper()            # 6 chars ex: A1B2C3
    exp = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

    perms["reset"] = {"token": tok, "exp": exp}
    u.permissoes = perms
    db.session.commit()

    # Sem email: retornamos o token na resposta para teste
    return jsonify({"ok": True, "token": tok, "exp_minutes": 15})

@auth_bp.route("/auth/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    token = (data.get("token") or "").strip().upper()
    newpwd = data.get("new_password") or data.get("senha")

    if not (username and token and newpwd):
        return jsonify({"error":"username, token e new_password são obrigatórios"}), 400

    u = Usuario.query.filter_by(username=username).first()
    if not u:
        return jsonify({"error":"Dados inválidos"}), 400

    perms = u.permissoes or {}
    reset = perms.get("reset") or {}
    if not reset:
        return jsonify({"error":"Token inválido/expirado"}), 400

    if token != (reset.get("token") or "").upper():
        return jsonify({"error":"Token inválido"}), 400

    try:
        exp = datetime.fromisoformat(reset.get("exp"))
        if datetime.utcnow() > exp:
            return jsonify({"error":"Token expirado"}), 400
    except Exception:
        return jsonify({"error":"Token inválido"}), 400

    u.set_password(newpwd)
    perms.pop("reset", None)
    u.permissoes = perms
    db.session.commit()
    return jsonify({"ok": True})
