#!/usr/bin/env bash
# Cria o banco do login server e importa o schema.
#
#   bash scripts/setup_db.sh                 # usa root e pergunta a senha
#   DB_USER=root DB_PASS=segredo bash scripts/setup_db.sh
#
# A senha nao e passada na linha de comando do mysql de proposito -- ali ela ficaria visivel para
# qualquer processo da maquina. Vai por MYSQL_PWD.
set -euo pipefail
cd "$(dirname "$0")/.."

DB_NAME=${DB_NAME:-al_server_ls}
DB_USER=${DB_USER:-root}
DB_HOST=${DB_HOST:-localhost}

if [ -z "${DB_PASS:-}" ]; then
    read -rsp "senha do MariaDB para '$DB_USER': " DB_PASS
    echo
fi
export MYSQL_PWD="$DB_PASS"

run() { mysql -u "$DB_USER" -h "$DB_HOST" "$@"; }

echo "conferindo acesso..."
run -e "SELECT VERSION();" >/dev/null

echo "criando o banco '$DB_NAME'..."
run -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8 COLLATE utf8_general_ci;"

echo "importando o schema..."
run "$DB_NAME" < server/AL-Login/sql/al_server_ls.sql

echo
echo "tabelas em $DB_NAME:"
run "$DB_NAME" -e "SHOW TABLES;"

# O database.properties do repo ainda tem a senha antiga; avisa em vez de reescrever sozinho.
if ! grep -q "database.password = $DB_PASS" server/AL-Login/config/network/database.properties; then
    echo
    echo "ATENCAO: server/AL-Login/config/network/database.properties ainda aponta para outra senha."
    echo "         ajuste 'database.password' antes de subir o servidor."
fi
