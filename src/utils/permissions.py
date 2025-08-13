# src/utils/permissions.py
from typing import Iterable, Set
from flask import session

from src.models.auth import Usuario, RoleEnum
from src.models.user import LojaEnum

# Todas as lojas válidas (nomes do Enum)
ALL_LOJAS: Set[str] = {e.name for e in LojaEnum}

def current_user() -> Usuario | None:
    """Retorna o usuário logado (ou None)."""
    uid = session.get("user_id")
    if not uid:
        return None
    return Usuario.query.get(uid)

def _norm_list(xs: Iterable[str] | None) -> Set[str]:
    if not xs:
        return set()
    normed = set()
    for v in xs:
        name = str(v or "").strip().upper().replace("-", "_").replace(" ", "_")
        if name:
            normed.add(name)
    return normed

def lojas_allowed(action: str) -> Set[str]:
    """
    Conjunto de lojas permitidas para a ação ('view' | 'create' | 'edit').
    ADMIN tem acesso a todas.
    """
    user = current_user()
    if not user:
        return set()
    if user.role == RoleEnum.ADMIN:
        return set(ALL_LOJAS)

    perms = user.permissoes or {}
    lojas_cfg = perms.get("lojas") or {}
    lst = lojas_cfg.get(action) or []
    allowed = _norm_list(lst)
    # garante que só retorne lojas válidas do Enum
    return allowed & ALL_LOJAS

def ensure_loja_allowed(loja_name: str, action: str) -> tuple[bool, Set[str]]:
    """
    Checa se a loja (nome do Enum, ex.: 'INDIANOPOLIS') está permitida para a ação.
    Retorna (ok, allowed_set).
    """
    allowed = lojas_allowed(action)
    if not allowed:
        return False, allowed
    return loja_name in allowed, allowed

def filter_query_by_lojas(query, column, action: str):
    """
    Restringe uma query por lojas permitidas (para não-admins).
    'column' é a coluna Enum (ex.: Visita.loja).
    """
    user = current_user()
    if not user or user.role == RoleEnum.ADMIN:
        return query

    allowed = lojas_allowed(action)
    if not allowed:
        # nenhuma loja -> resultado vazio
        return query.filter(False)

    enum_vals = [LojaEnum[name] for name in allowed]
    return query.filter(column.in_(enum_vals))
