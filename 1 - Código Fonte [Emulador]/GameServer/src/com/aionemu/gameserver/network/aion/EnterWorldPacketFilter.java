package com.aionemu.gameserver.network.aion;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Filtro de diagnostico: descarta opcodes escolhidos enquanto o jogador ainda nao fez spawn.
 *
 * Existe para uma pergunta so: a entrada no mundo trava porque mandamos alguma coisa que o
 * servidor oficial nao manda? A comparacao com as capturas (`6 - Ferramentas/compara_enterworld.py`)
 * lista os opcodes que so nos enviamos; jogando essa lista aqui da para conferir sem tocar nos oito
 * servicos que os originam, e sem recompilar a cada tentativa -- o que permite bissectar a lista
 * trocando uma linha de `network.properties`.
 *
 * Vazio por padrao. Nao e mecanismo de producao: quando o culpado aparecer, a correcao e no
 * servico que envia o pacote, e esta lista volta a ficar vazia.
 */
public final class EnterWorldPacketFilter {

    private static final Logger log = LoggerFactory.getLogger(EnterWorldPacketFilter.class);

    private static Set<Integer> opcodes = Collections.emptySet();
    private static String lidoDe;

    private EnterWorldPacketFilter() {
    }

    /** `true` se este pacote deve ser descartado agora. */
    public static boolean descarta(AionServerPacket pacote, Player jogador) {
        Set<Integer> lista = lista();
        if (lista.isEmpty() || jogador == null || jogador.isSpawned()) {
            return false;
        }
        return lista.contains(pacote.getOpcode());
    }

    /** Le a configuracao na primeira chamada e a cada mudanca do texto configurado. */
    private static Set<Integer> lista() {
        String bruto = NetworkConfig.ENTER_WORLD_FILTER;
        if (bruto == null) {
            bruto = "";
        }
        if (bruto.equals(lidoDe)) {
            return opcodes;
        }
        Set<Integer> novos = new HashSet<Integer>();
        for (String parte : bruto.split(",")) {
            String texto = parte.trim();
            if (texto.isEmpty()) {
                continue;
            }
            try {
                novos.add(Integer.decode(texto));
            } catch (NumberFormatException e) {
                log.warn("Opcode invalido no filtro de entrada no mundo: '{}'", texto);
            }
        }
        lidoDe = bruto;
        opcodes = novos;
        if (!novos.isEmpty()) {
            log.warn("Filtro de diagnostico ativo: {} opcodes serao descartados antes do spawn.",
                novos.size());
        }
        return opcodes;
    }
}
