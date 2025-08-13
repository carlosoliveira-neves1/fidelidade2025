# src/routes/admin.py
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from unicodedata import normalize as ucnorm

from src.routes.auth import login_required, roles_required
from src.models.user import db
from src.models.auth import Usuario, RoleEnum

admin_bp = Blueprint("admin", __name__)

# -----------------------------
# Normalização de lojas
# -----------------------------
ALLOWED_LOJAS = {"JABAQUARA", "INDIANOPOLIS", "MASCOTE", "TATUAPE", "PRAIA_GRANDE", "OSASCO"}

def _normalize_key(s: str) -> str:
    s = (s or "").strip()
    s = ucnorm("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
    s = s.replace(".", "")
    import re
    s = re.sub(r"[\s\-]+", "_", s).upper()
    return s

_LOJA_SYNONYMS = {
    "CASA_DO_CIGANO_INDIANOPOLIS": "INDIANOPOLIS",
    "INDIANOPOLIS": "INDIANOPOLIS",

    "CASA_DO_CIGANO_LOJA_VL__MASCOTE": "MASCOTE",
    "CASA_DO_CIGANO_LOJA_VL_MASCOTE": "MASCOTE",
    "VILA_MASCOTE": "MASCOTE",
    "VL__MASCOTE": "MASCOTE",
    "VL_MASCOTE": "MASCOTE",
    "MASCOTE": "MASCOTE",

    "CASA_DO_CIGANO_MEGA_LOJA": "JABAQUARA",
    "MEGA_LOJA": "JABAQUARA",
    "JABAQUARA": "JABAQUARA",

    "CASA_DO_CIGANO_PRAIA_GRANDE": "PRAIA_GRANDE",
    "PRAIA_GRANDE": "PRAIA_GRANDE",

    "CASA_DO_CIGANO_TATUAPE": "TATUAPE",
    "TATUAPE": "TATUAPE",

    "OSASCO": "OSASCO",
}

def _normalize_loja(loja_raw: str):
    if not loja_raw:
        return None
    key = _normalize_key(loja_raw)
    val = _LOJA_SYNONYMS.get(key, key)
    return val if val in ALLOWED_LOJAS else None

def _sanitize_permissoes(payload: dict) -> dict:
    """
    Espera algo como:
    {
      "lojas": [
        {"label":"INDIANOPOLIS","view":true,"create":false,"edit":false},
        {"label":"JABAQUARA","view":true}
      ]
    }
    Retorna:
    {"lojas": {"INDIANOPOLIS":{"view":true,"create":false,"edit":false}, "JABAQUARA":{"view":true,"create":false,"edit":false}}}
    """
    lojas_cfg = {}
    items = (payload or {}).get("lojas") or []
    for item in items:
        rotulo = _normalize_loja(item.get("label"))
        if not rotulo:
            continue
        lojas_cfg[rotulo] = {
            "view": bool(item.get("view", False)),
            "create": bool(item.get("create", False)),
            "edit": bool(item.get("edit", False)),
        }
    return {"lojas": lojas_cfg}

# -----------------------------
# Auxiliares simples
# -----------------------------
def _roles_set():
    return {r.value for r in RoleEnum}

# -----------------------------
# Endpoints de administração
# -----------------------------

@admin_bp.route("/admin/roles", methods=["GET"])
@login_required
@roles_required("ADMIN")
def roles_list():
    return jsonify(sorted(_roles_set()))

@admin_bp.route("/admin/users", methods=["GET"])
@login_required
@roles_required("ADMIN")
def list_users():
    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    qry = Usuario.query
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(Usuario.nome.ilike(like),
                             Usuario.username.ilike(like),
                             Usuario.email.ilike(like)))
    pg = qry.order_by(Usuario.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "users": [u.to_dict() for u in pg.items],
        "total": pg.total,
        "pages": pg.pages,
        "current_page": page
    })

@admin_bp.route("/admin/users/<int:uid>", methods=["GET"])
@login_required
@roles_required("ADMIN")
def get_user(uid):
    u = Usuario.query.get_or_404(uid)
    return jsonify(u.to_dict())

@admin_bp.route("/admin/users", methods=["POST"])
@login_required
@roles_required("ADMIN")
def create_user():
    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip() or None
    role = (data.get("role") or "ATENDENTE").upper().strip()
    senha = data.get("senha") or data.get("password")

    if not nome or not username or not senha:
        return jsonify({"error": "nome, username e senha são obrigatórios"}), 400
    if role not in _roles_set():
        return jsonify({"error": f"role inválido. Use: {sorted(_roles_set())}"}), 400
    if Usuario.query.filter_by(username=username).first():
        return jsonify({"error": "username já existe"}), 400

    u = Usuario(nome=nome, username=username, email=email, role=RoleEnum(role))
    u.set_password(senha)
    db.session.add(u)
    db.session.commit()
    return jsonify(u.to_dict()), 201

@admin_bp.route("/admin/users/<int:uid>", methods=["PUT"])
@login_required
@roles_required("ADMIN")
def update_user(uid):
    u = Usuario.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}

    if "nome" in data:
        v = (data["nome"] or "").strip()
        if v:
            u.nome = v

    if "username" in data:
        newu = (data["username"] or "").strip()
        if newu and newu != u.username:
            if Usuario.query.filter_by(username=newu).first():
                return jsonify({"error": "username já existe"}), 400
            u.username = newu

    if "email" in data:
        u.email = (data["email"] or "").strip() or None

    if "role" in data:
        r = (data["role"] or "").upper().strip()
        if r in _roles_set():
            u.role = RoleEnum(r)

    if "ativo" in data:
        u.ativo = bool(data["ativo"])

    if data.get("senha") or data.get("password"):
        u.set_password(data.get("senha") or data.get("password"))

    db.session.commit()
    return jsonify(u.to_dict())

@admin_bp.route("/admin/users/<int:uid>", methods=["DELETE"])
@login_required
@roles_required("ADMIN")
def delete_user(uid):
    u = Usuario.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"ok": True})

# -------- Permissões por loja --------

@admin_bp.route("/admin/users/<int:uid>/permissoes", methods=["GET"])
@login_required
@roles_required("ADMIN")
def get_user_permissions(uid):
    u = Usuario.query.get_or_404(uid)
    perms = u.permissoes or {}
    # Garante formato consistente no retorno
    lojas = perms.get("lojas") or {}
    # transforma em lista amigável ao front
    out = []
    for label, flags in lojas.items():
        if label in ALLOWED_LOJAS:
            out.append({
                "label": label,
                "view": bool(flags.get("view", False)),
                "create": bool(flags.get("create", False)),
                "edit": bool(flags.get("edit", False)),
            })
    return jsonify({
        "lojas": out,
        "allowed_labels": sorted(ALLOWED_LOJAS),
    })

@admin_bp.route("/admin/users/<int:uid>/permissoes", methods=["PUT"])
@login_required
@roles_required("ADMIN")
def set_user_permissions(uid):
    u = Usuario.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    new_perms = _sanitize_permissoes(data)
    u.permissoes = new_perms
    db.session.commit()
    return jsonify(u.to_dict())
