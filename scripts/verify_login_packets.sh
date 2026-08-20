#!/usr/bin/env bash
# Monta SM_INIT e SM_LOGIN_OK pelo caminho real do codigo e confere os offsets que o Game.dll testa.
# Nao precisa de banco nem de cliente rodando.
#
# Usa caminhos relativos de proposito: o javac aqui e um binario Windows e nao entende os caminhos
# no estilo /tmp que o mktemp do Git Bash devolve.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=build/verify
rm -rf "$OUT"
mkdir -p "$OUT"

libs() { ls "$1"/libs/*.jar 2>/dev/null | grep -v al-commons | tr '\n' ';'; }

echo "compilando AL-Commons..."
find server/AL-Commons/src -name '*.java' > "$OUT/commons.txt"
javac --release 8 -encoding UTF-8 -nowarn -cp "$(libs server/AL-Commons)" \
      -d "$OUT/commons" @"$OUT/commons.txt"

echo "compilando AL-Login..."
find server/AL-Login/src -name '*.java' > "$OUT/login.txt"
javac --release 8 -encoding UTF-8 -nowarn -cp "$OUT/commons;$(libs server/AL-Login)" \
      -d "$OUT/login" @"$OUT/login.txt"

echo "compilando a verificacao..."
CP="$OUT/login;$OUT/commons;$(libs server/AL-Login)"
javac -encoding UTF-8 -nowarn -cp "$CP" -d "$OUT/test" server/AL-Login/test/VerifyLoginPackets.java

echo
java -cp "$CP;$OUT/test" VerifyLoginPackets
