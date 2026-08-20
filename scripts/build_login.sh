#!/usr/bin/env bash
# Compila AL-Commons + AL-Login e monta um diretorio pronto para rodar em build/login-server.
#
# Caminhos relativos de proposito: o javac aqui e um binario Windows e nao entende os caminhos
# no estilo /tmp do Git Bash. O AL ainda pede source="1.7" no build.xml, que o javac 21 recusa --
# por isso --release 8.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=build/login-server
rm -rf "$OUT"
mkdir -p "$OUT/classes" "$OUT/log"

libs() { ls "$1"/libs/*.jar 2>/dev/null | grep -v al-commons | tr '\n' ';'; }

echo "[1/4] compilando AL-Commons..."
find server/AL-Commons/src -name '*.java' > build/commons.txt
javac --release 8 -encoding UTF-8 -nowarn -cp "$(libs server/AL-Commons)" \
      -d "$OUT/classes" @build/commons.txt

echo "[2/4] compilando AL-Login..."
find server/AL-Login/src -name '*.java' > build/login.txt
javac --release 8 -encoding UTF-8 -nowarn -cp "$OUT/classes;$(libs server/AL-Login)" \
      -d "$OUT/classes" @build/login.txt

echo "[3/4] copiando libs e config..."
mkdir -p "$OUT/libs"
cp server/AL-Login/libs/*.jar "$OUT/libs/"
rm -f "$OUT/libs/al-commons.jar"          # usamos as classes recem-compiladas
cp server/libs-modern/*.jar "$OUT/libs/"  # JAXB: saiu do JDK no Java 11, ver server/deps/pom.xml
cp -r server/AL-Login/config "$OUT/config"
cp -r server/AL-Login/data "$OUT/data"    # o DAOManager compila os DAOs daqui no startup

echo "[4/4] gerando o runner..."
cat > "$OUT/run.sh" <<'RUN'
#!/usr/bin/env bash
# O Config le ./config/network, entao o cwd tem que ser esta pasta.
cd "$(dirname "$0")"
exec java -Xms64m -Xmx256m \
     -cp "classes;libs/*" \
     com.aionemu.loginserver.LoginServer "$@"
RUN
chmod +x "$OUT/run.sh"

echo
echo "pronto: $OUT"
echo "  subir com:  bash $OUT/run.sh"
