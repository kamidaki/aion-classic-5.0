#!/usr/bin/env bash
# Baixa em server/libs-modern as dependencias que sairam do JDK depois do Java 8.
# Precisa de rede. Os jars ficam versionados, para o build seguir funcionando offline.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=server/libs-modern
mkdir -p "$OUT"

mvn -q -f server/deps/pom.xml dependency:copy-dependencies \
    -DoutputDirectory="$(pwd)/$OUT" \
    -DincludeScope=runtime

echo "jars em $OUT:"
ls -1 "$OUT"
