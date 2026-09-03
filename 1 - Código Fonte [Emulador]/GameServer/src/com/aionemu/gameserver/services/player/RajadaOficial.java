package com.aionemu.gameserver.services.player;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.serverpackets.S_RAJADA_OFICIAL;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;

/**
 * Experimento: reproduz no fio os pacotes da entrada no mundo que a captura oficial traz e o
 * nosso servidor nao envia.
 *
 * Serve para separar duas hipoteses que a comparacao por tamanho nao separa. Se o cliente concluir
 * o carregamento com a rajada completa, o bloqueio e **falta** de pacote e da para bissectar a
 * lista ate achar qual; se nao mudar nada, o bloqueio esta no **conteudo** do que ja enviamos, e a
 * investigacao passa a ser outra.
 *
 * Os corpos vem de `data/diagnostico/rajada_oficial.txt`, gerado por
 * `6 - Ferramentas/extrai_rajada_oficial.py`. O objectId do personagem da captura e trocado pelo
 * do jogador real nas posicoes que o arquivo registra.
 *
 * **Nao e mecanismo de producao.** Fica desligado por padrao; quando um pacote provar ser
 * necessario, ele ganha uma classe de verdade e sai daqui.
 */
public final class RajadaOficial {

    private static final Logger log = LoggerFactory.getLogger(RajadaOficial.class);
    private static final String ARQUIVO = "./data/diagnostico/rajada_oficial.txt";

    private static List<Entrada> entradas;

    private RajadaOficial() {
    }

    private static final class Entrada {
        final int opcode;
        final byte[] corpo;
        final int[] posicoesDoObjectId;

        Entrada(int opcode, byte[] corpo, int[] posicoes) {
            this.opcode = opcode;
            this.corpo = corpo;
            this.posicoesDoObjectId = posicoes;
        }
    }

    public static void envia(AionConnection cliente, Player jogador) {
        if (!NetworkConfig.RAJADA_OFICIAL || cliente == null || jogador == null) {
            return;
        }
        List<Entrada> lista = carrega();
        if (lista.isEmpty()) {
            return;
        }
        int objectId = jogador.getObjectId();
        for (Entrada e : lista) {
            byte[] corpo = e.corpo.clone();
            for (int pos : e.posicoesDoObjectId) {
                corpo[pos] = (byte) objectId;
                corpo[pos + 1] = (byte) (objectId >>> 8);
                corpo[pos + 2] = (byte) (objectId >>> 16);
                corpo[pos + 3] = (byte) (objectId >>> 24);
            }
            cliente.sendPacket(new S_RAJADA_OFICIAL(e.opcode, corpo));
        }
        log.warn("[RAJADA] Reproduzidos {} pacotes da captura oficial para {} -- diagnostico,"
            + " desligar depois.", lista.size(), jogador.getName());
    }

    private static synchronized List<Entrada> carrega() {
        if (entradas != null) {
            return entradas;
        }
        List<Entrada> lidas = new ArrayList<Entrada>();
        File arquivo = new File(ARQUIVO);
        if (!arquivo.isFile()) {
            log.warn("[RAJADA] {} nao existe; gere com extrai_rajada_oficial.py", ARQUIVO);
            entradas = lidas;
            return entradas;
        }
        BufferedReader leitor = null;
        try {
            leitor = new BufferedReader(new InputStreamReader(new FileInputStream(arquivo),
                Charset.forName("UTF-8")));
            String linha;
            while ((linha = leitor.readLine()) != null) {
                linha = linha.trim();
                if (linha.isEmpty() || linha.startsWith("#")) {
                    continue;
                }
                String[] partes = linha.split(" +");
                if (partes.length < 2) {
                    continue;
                }
                int opcode = Integer.decode(partes[0]);
                byte[] corpo = hexParaBytes(partes[1]);
                int[] posicoes = new int[0];
                if (partes.length > 2 && !"-".equals(partes[2])) {
                    String[] campos = partes[2].split(",");
                    posicoes = new int[campos.length];
                    for (int i = 0; i < campos.length; i++) {
                        posicoes[i] = Integer.parseInt(campos[i]);
                    }
                }
                lidas.add(new Entrada(opcode, corpo, posicoes));
            }
            log.warn("[RAJADA] {} pacotes carregados de {}", lidas.size(), ARQUIVO);
        } catch (Exception e) {
            log.error("[RAJADA] Falha ao ler " + ARQUIVO, e);
            lidas.clear();
        } finally {
            if (leitor != null) {
                try {
                    leitor.close();
                } catch (IOException ignorado) {
                    // fechar o arquivo de diagnostico nao pode derrubar a entrada no mundo
                }
            }
        }
        entradas = lidas;
        return entradas;
    }

    private static byte[] hexParaBytes(String hex) {
        int n = hex.length() / 2;
        byte[] saida = new byte[n];
        for (int i = 0; i < n; i++) {
            saida[i] = (byte) Integer.parseInt(hex.substring(i * 2, i * 2 + 2), 16);
        }
        return saida;
    }
}
