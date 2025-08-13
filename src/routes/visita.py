# src/routes/visita.py

from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import or_
import re
from unicodedata import normalize as ucnorm

from src.models.user import (
    db,
    Cliente,
    Visita,
    Ponto,
    NivelEnum,
    LojaEnum,
)
from src.utils.permissions import (
    ensure_loja_allowed,
    filter_query_by_lojas,
)

visita_bp = Blueprint('visita', __name__)

# ============== Helpers / Normalizações ==============

ALLOWED_LOJAS = {"JABAQUARA", "INDIANOPOLIS", "MASCOTE", "TATUAPE", "PRAIA_GRANDE", "OSASCO"}

def _only_digits(s):
    return re.sub(r'\D', '', s or '')

def _get_param(name):
    if request.is_json:
        js = request.get_json(silent=True) or {}
        if name in js:
            return js.get(name)
    return request.form.get(name) or request.values.get(name)

def _normalize_key(s):
    s = (s or "").strip()
    s = ucnorm('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[\s\-]+', '_', s).upper()
    return s

_LOJA_SYNONYMS = {
    "CASA_DO_CIGANO_INDIANOPOLIS": "INDIANOPOLIS",
    "INDIANOPOLIS": "INDIANOPOLIS",

    "CASA_DO_CIGANO_LOJA_VL._MASCOTE": "MASCOTE",
    "VILA_MASCOTE": "MASCOTE",
    "VL._MASCOTE": "MASCOTE",
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

def _normalize_loja_for_enum(loja_raw):
    if not loja_raw:
        return None
    key = _normalize_key(loja_raw)
    val = _LOJA_SYNONYMS.get(key, key)
    return val if val in ALLOWED_LOJAS else None

# ========================= Regras de Pontuação =========================

def calcular_nivel_por_pontos(pontos):
    if pontos >= 1000:
        return NivelEnum.OURO
    elif pontos >= 500:
        return NivelEnum.PRATA
    else:
        return NivelEnum.BRONZE

def atualizar_pontos_cliente(cliente_id, valor_compra, loja=None):
    fator_pontuacao = 1.0
    pontos_compra = int(float(valor_compra) * fator_pontuacao)

    ponto = Ponto.query.filter_by(cliente_id=cliente_id).first()
    if not ponto:
        ponto = Ponto(
            cliente_id=cliente_id,
            pontos_acumulados=0,
            nivel_atual=NivelEnum.BRONZE
        )
        db.session.add(ponto)

    ponto.pontos_acumulados += pontos_compra
    ponto.nivel_atual = calcular_nivel_por_pontos(ponto.pontos_acumulados)
    ponto.data_atualizacao = datetime.utcnow()
    return pontos_compra

# ========================= Endpoints =========================

@visita_bp.route('/visitas', methods=['POST'])
def registrar_visita():
    """Registra uma nova visita e atualiza pontos (aceita JSON ou form)."""
    try:
        cliente_id = _get_param('cliente_id') or _get_param('clienteId') or _get_param('cliente')
        valor_compra = _get_param('valor_compra') or _get_param('valor') or _get_param('valorCompra')
        loja_raw     = _get_param('loja')
        cpf_raw      = _get_param('cpf') or _get_param('cliente_cpf') or _get_param('cpf_digitado')

        if not cliente_id and cpf_raw:
            cpf = _only_digits(cpf_raw)
            cli = Cliente.query.filter(Cliente.cpf == cpf).first()
            if cli:
                cliente_id = cli.id

        if not cliente_id or not valor_compra:
            return jsonify({'error': 'cliente_id e valor_compra são obrigatórios'}), 400

        try:
            cliente_id = int(cliente_id)
            valor_compra = float(valor_compra)
        except Exception:
            return jsonify({'error': 'Formato inválido para cliente_id/valor_compra'}), 400

        if valor_compra <= 0:
            return jsonify({'error': 'Valor da compra deve ser maior que zero'}), 400

        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        # Normaliza loja -> Enum + valida permissões de criação
        loja_enum = None
        if loja_raw:
            loja_norm = _normalize_loja_for_enum(loja_raw)
            if not loja_norm:
                return jsonify({'error': f'Loja inválida (recebido: {loja_raw}). Aceitas: {sorted(ALLOWED_LOJAS)}'}), 400

            ok, allowed = ensure_loja_allowed(loja_norm, "create")
            if not ok:
                return jsonify({'error': f'Usuário não tem permissão de CRIAR para a loja {loja_norm}. Permitidas: {sorted(allowed)}'}), 403

            try:
                loja_enum = LojaEnum[loja_norm]
            except KeyError:
                return jsonify({'error': f'Loja inválida (recebido: {loja_raw})'}), 400

        visita = Visita(
            cliente_id=cliente_id,
            valor_compra=valor_compra,
            loja=loja_enum,
            data_visita=datetime.utcnow()
        )
        db.session.add(visita)
        db.session.flush()

        pontos_ganhos = atualizar_pontos_cliente(cliente_id, valor_compra, loja_enum)
        db.session.commit()

        ponto = Ponto.query.filter_by(cliente_id=cliente_id).first()
        return jsonify({
            'visita': visita.to_dict(),
            'pontos_ganhos': pontos_ganhos,
            'pontos_totais': ponto.pontos_acumulados if ponto else 0,
            'nivel_atual': ponto.nivel_atual.value if ponto else 'Bronze'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@visita_bp.route('/visitas/cliente/<int:cliente_id>', methods=['GET'])
def listar_visitas_cliente(cliente_id):
    """Lista visitas do cliente, restrita às lojas permitidas (view)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        q = Visita.query.filter_by(cliente_id=cliente_id).order_by(Visita.data_visita.desc())
        q = filter_query_by_lojas(q, Visita.loja, "view")

        visitas = q.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'visitas': [v.to_dict() for v in visitas.items],
            'total': visitas.total,
            'pages': visitas.pages,
            'current_page': page,
            'cliente': cliente.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@visita_bp.route('/visitas/<int:visita_id>', methods=['GET'])
def obter_visita(visita_id):
    try:
        v = Visita.query.get_or_404(visita_id)
        return jsonify(v.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@visita_bp.route('/visitas/<int:visita_id>', methods=['PUT'])
def atualizar_visita(visita_id):
    """Atualiza visita: valida permissão de 'edit' para a loja alvo."""
    try:
        visita = Visita.query.get_or_404(visita_id)
        data = request.get_json(silent=True) or {}

        # Se alterar loja, valida permissão de edição na nova loja
        if 'loja' in data and data['loja']:
            loja_norm = _normalize_loja_for_enum(data['loja'])
            if not loja_norm:
                return jsonify({'error': 'Loja inválida'}), 400
            ok, allowed = ensure_loja_allowed(loja_norm, "edit")
            if not ok:
                return jsonify({'error': f'Sem permissão de EDITAR na loja {loja_norm}. Permitidas: {sorted(allowed)}'}), 403
            try:
                visita.loja = LojaEnum[loja_norm]
            except KeyError:
                return jsonify({'error': 'Loja inválida'}), 400

        valor_antigo = visita.valor_compra
        if 'valor_compra' in data:
            novo_valor = float(data['valor_compra'])
            if novo_valor <= 0:
                return jsonify({'error': 'Valor da compra deve ser maior que zero'}), 400
            visita.valor_compra = novo_valor

        if 'valor_compra' in data and valor_antigo != visita.valor_compra:
            diferenca = visita.valor_compra - valor_antigo
            atualizar_pontos_cliente(visita.cliente_id, diferenca, visita.loja)

        db.session.commit()
        return jsonify(visita.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@visita_bp.route('/visitas/<int:visita_id>', methods=['DELETE'])
def excluir_visita(visita_id):
    """Exclui visita: exige permissão de 'edit' (ou 'delete' se quiser separar)."""
    try:
        visita = Visita.query.get_or_404(visita_id)
        ok, allowed = ensure_loja_allowed(visita.loja.name if visita.loja else "", "edit")
        if not ok:
            return jsonify({'error': f'Sem permissão para excluir nesta loja. Permitidas: {sorted(allowed)}'}), 403

        atualizar_pontos_cliente(visita.cliente_id, -visita.valor_compra, visita.loja)
        db.session.delete(visita)
        db.session.commit()
        return jsonify({'message': 'Visita excluída com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@visita_bp.route('/pontos/cliente/<int:cliente_id>', methods=['GET'])
def obter_pontos_cliente(cliente_id):
    """Mantido sem filtro de loja (é agregado do cliente)."""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        ponto = Ponto.query.filter_by(cliente_id=cliente_id).first()
        if not ponto:
            ponto = Ponto(
                cliente_id=cliente_id,
                pontos_acumulados=0,
                nivel_atual=NivelEnum.BRONZE
            )
            db.session.add(ponto)
            db.session.commit()

        total_visitas = len(cliente.visitas)
        valor_total_compras = sum([v.valor_compra for v in cliente.visitas])

        return jsonify({
            'pontos': ponto.to_dict(),
            'total_visitas': total_visitas,
            'valor_total_compras': valor_total_compras,
            'cliente': cliente.to_dict()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@visita_bp.route('/relatorio/visitas', methods=['GET'])
def relatorio_visitas():
    """Relatório com filtro de data/loja + restrição por permissão de 'view'."""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim    = request.args.get('data_fim')
        loja_raw    = request.args.get('loja')

        q = Visita.query

        if data_inicio:
            di = datetime.fromisoformat(data_inicio)
            q = q.filter(Visita.data_visita >= di)

        if data_fim:
            df = datetime.fromisoformat(data_fim)
            q = q.filter(Visita.data_visita <= df)

        if loja_raw:
            # o usuário já será filtrado, mas se especificar loja, normalize
            loja_norm = _normalize_loja_for_enum(loja_raw)
            if not loja_norm:
                return jsonify({'error': 'Loja inválida'}), 400
            q = q.filter(Visita.loja == LojaEnum[loja_norm])

        # aplica restrição por permissão de visualização
        q = filter_query_by_lojas(q, Visita.loja, "view")

        visitas = q.order_by(Visita.data_visita.desc()).all()

        total_visitas = len(visitas)
        valor_total = sum([v.valor_compra for v in visitas])
        valor_medio = valor_total / total_visitas if total_visitas > 0 else 0

        return jsonify({
            'visitas': [v.to_dict() for v in visitas],
            'estatisticas': {
                'total_visitas': total_visitas,
                'valor_total': valor_total,
                'valor_medio': valor_medio
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================== Buscas de cliente ==============================

@visita_bp.route('/clientes/cpf/<cpf>', methods=['GET'])
def buscar_cliente_por_cpf(cpf):
    cliente = Cliente.query.filter_by(cpf=cpf).first()
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado'}), 404
    return jsonify(cliente.to_dict())

@visita_bp.route('/clientes/buscar', methods=['GET'])
def buscar_clientes():
    termo = (request.args.get('q') or '').strip()
    if not termo:
        return jsonify([])
    clientes = (Cliente.query
                .filter(or_(
                    Cliente.nome.ilike(f'%{termo}%'),
                    Cliente.cpf.ilike(f'%{termo}%')
                ))
                .limit(15)
                .all())
    return jsonify([c.to_dict() for c in clientes])
