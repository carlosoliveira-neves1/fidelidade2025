# Sistema de Fidelidade - Integração com Amazon RDS

Este projeto foi configurado para funcionar com banco de dados PostgreSQL, tanto local quanto na Amazon RDS.

## Configuração do Banco de Dados

### Banco Local (Desenvolvimento)
Para usar o banco local PostgreSQL:
```bash
cp .env.local .env
```

### Amazon RDS (Produção)
Para usar o banco Amazon RDS:
```bash
cp .env.production .env
```

**Importante**: Certifique-se de que o Security Group do RDS permite conexões na porta 5432.

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
pip install psycopg2-binary
```

2. Configure o arquivo .env com as credenciais do banco

3. Inicialize as tabelas:
```bash
python3 -c "
from src.main import app, db
with app.app_context():
    db.create_all()
    print('Tabelas criadas!')
"
```

## Execução

```bash
python3 src/main.py
```

O servidor estará disponível em: http://localhost:5000

## API de Clientes

### Criar Cliente
```bash
curl -X POST http://localhost:5000/api/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "cpf": "12345678901",
    "nome": "João Silva",
    "telefone": "11999999999",
    "email": "joao@email.com",
    "sem_email": false
  }'
```

### Listar Clientes
```bash
curl http://localhost:5000/api/clientes
```

### Buscar Cliente por CPF
```bash
curl http://localhost:5000/api/clientes/buscar-cpf/12345678901
```

## Estrutura do Banco

O sistema cria automaticamente as seguintes tabelas:
- `clientes` - Dados dos clientes
- `pontos` - Sistema de pontuação
- `visitas` - Histórico de visitas
- `campanhas` - Campanhas de fidelidade
- `produtos` - Catálogo de produtos
- `brindes` - Brindes disponíveis
- `resgates` - Histórico de resgates

## Troubleshooting

### Erro de Conexão com RDS
Se houver erro de conexão com o Amazon RDS:

1. Verifique se o Security Group permite conexões na porta 5432
2. Confirme se o banco está ativo e acessível
3. Teste as credenciais

### Usar Banco Local
Para desenvolvimento, use o banco local:
```bash
sudo systemctl start postgresql
cp .env.local .env
python3 src/main.py
```

