# src/models/auth.py
from datetime import datetime
import enum

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Index, text

from src.models.user import db  # reaproveita a instância do SQLAlchemy


class RoleEnum(enum.Enum):
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"
    ATENDENTE = "ATENDENTE"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    nome = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=False, nullable=True)

    # Autenticação e autorização
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum, name="roleenum"), nullable=False, default=RoleEnum.ATENDENTE)
    permissoes = db.Column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    # Status e auditoria
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Recuperação de senha
    reset_token = db.Column(db.String(128), nullable=True)
    reset_expires = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        # Índice para aceleração da busca por token de redefinição
        Index("ix_usuarios_reset_token", "reset_token", unique=True),
    )

    # -----------------------
    # Métodos utilitários
    # -----------------------
    def set_password(self, pwd: str) -> None:
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        return check_password_hash(self.password_hash, pwd)

    def to_dict(self) -> dict:
        """Não expõe password_hash nem tokens."""
        return {
            "id": self.id,
            "nome": self.nome,
            "username": self.username,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, RoleEnum) else str(self.role),
            "permissoes": self.permissoes or {},
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} username={self.username!r} role={self.role}>"
