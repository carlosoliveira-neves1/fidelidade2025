# seed_admin.py
from src.main import app
from src.models.auth import Usuario, RoleEnum, db
from werkzeug.security import generate_password_hash

ADMIN_USER  = "admin"
ADMIN_PASS  = "Admin@123"
ADMIN_NAME  = "Administrador"
ADMIN_EMAIL = "admin@megaloja.local"

with app.app_context():
    # tenta achar por username
    u = Usuario.query.filter_by(username=ADMIN_USER).first()

    if not u:
        # cria vazio e seta atributo por atributo (evita __init__ custom ignorar kwargs)
        u = Usuario()
        u.username = ADMIN_USER
        try:
            u.role = RoleEnum.ADMIN
        except Exception:
            u.role = "ADMIN"
        u.ativo = True
        db.session.add(u)

    # garante os campos obrigatórios SEMPRE
    if hasattr(u, "nome"):
        u.nome = ADMIN_NAME
    if hasattr(u, "email"):
        u.email = ADMIN_EMAIL
    if hasattr(u, "password_hash"):
        u.password_hash = generate_password_hash(ADMIN_PASS)
    if hasattr(u, "permissoes") and (u.permissoes in (None, "", {})):
        u.permissoes = {}

    db.session.commit()
    print("OK: usuário admin pronto. Login: admin / Senha: Admin@123")
