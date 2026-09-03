package com.aionemu.gameserver.network.aion;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.network.Crypt;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteBuffer;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Rastreador de fio: registra todo pacote que entra e sai, na ordem real, com opcode e tamanho.
 *
 * Existe para responder uma pergunta so: em que ponto a nossa rajada de entrada no mundo diverge
 * da captura oficial. A saida vai para `log/wiretrace.log` num formato de campos separados por
 * `|`, feito para ser lido por script e comparado direto com o que o `aion_pcap.py` extrai da
 * captura -- os mesmos opcodes decodificados, o mesmo tamanho de payload, a mesma ordem.
 *
 * Alem do opcode e do tamanho, vai o inicio do payload em hexadecimal. Sem ele o rastro so
 * responde "mandamos o pacote?"; com ele responde tambem "mandamos com o conteudo certo?", que e
 * onde mora o defeito quando o opcode ja bate.
 *
 * Fica desligado por padrao (`gameserver.network.wiretrace`). Ligado, ele escreve uma linha por
 * pacote, o que e caro: e ferramenta de diagnostico, nao de producao.
 */
public final class WireTrace {

    private static final Logger log = LoggerFactory.getLogger("WIRETRACE_LOG");
    private static final AtomicLong SEQ = new AtomicLong();

    /** Quantos bytes de payload entram no rastro (`gameserver.network.wiretrace.bytes`). */
    private static int prefixo() {
        int n = NetworkConfig.WIRE_TRACE_BYTES;
        return n > 0 ? n : 32;
    }

    private static final char[] HEX = "0123456789abcdef".toCharArray();

    private WireTrace() {
    }

    public static boolean ativo() {
        return NetworkConfig.WIRE_TRACE;
    }

    /** Pacote recebido do cliente. `wireOp` e o opcode do fio, `decOp` o decodificado. */
    public static void cliente(AionConnection con, int wireOp, int decOp, int bytes, String classe, String hex) {
        if (!NetworkConfig.WIRE_TRACE) {
            return;
        }
        escreve("C", decOp, wireOp, bytes, classe, con, hex);
    }

    /** Pacote enviado ao cliente. `bytes` e o tamanho do payload, sem o cabecalho de 7 bytes. */
    public static void servidor(AionConnection con, int decOp, int bytes, String classe, String hex) {
        if (!NetworkConfig.WIRE_TRACE) {
            return;
        }
        escreve("S", decOp, Crypt.encodeOpcodec(decOp) & 0xFFFF, bytes, classe, con, hex);
    }

    /**
     * Le ate {@link #PREFIXO} bytes a partir de `inicio` sem mexer na posicao do buffer -- o
     * pacote ainda vai ser lido ou enviado depois desta chamada.
     */
    public static String hexDe(ByteBuffer buf, int inicio, int disponivel) {
        if (buf == null || disponivel <= 0) {
            return "";
        }
        int n = Math.min(prefixo(), Math.min(disponivel, buf.limit() - inicio));
        if (n <= 0) {
            return "";
        }
        char[] saida = new char[n * 2];
        for (int i = 0; i < n; i++) {
            int b = buf.get(inicio + i) & 0xFF;
            saida[i * 2] = HEX[b >>> 4];
            saida[i * 2 + 1] = HEX[b & 0x0F];
        }
        return new String(saida);
    }

    private static void escreve(String lado, int decOp, int wireOp, int bytes, String classe, AionConnection con,
        String hex) {
        try {
            log.info(String.format("%06d|%s|0x%04X|0x%04X|%d|%s|%s|%s|%s", SEQ.incrementAndGet(), lado, decOp, wireOp,
                bytes, classe, estado(con), jogador(con), hex == null ? "" : hex));
        } catch (Exception e) {
            // um rastreador nunca pode derrubar a rede que ele observa
        }
    }

    private static String estado(AionConnection con) {
        return con == null || con.getState() == null ? "-" : con.getState().toString();
    }

    private static String jogador(AionConnection con) {
        if (con == null || con.getActivePlayer() == null) {
            return "-";
        }
        String nome = con.getActivePlayer().getName();
        return nome == null || nome.isEmpty() ? "-" : nome;
    }
}
