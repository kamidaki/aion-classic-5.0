/**
 * This file is part of Aion-Lightning <aion-lightning.org>.
 *
 *  Aion-Lightning is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  Aion-Lightning is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details. *
 *  You should have received a copy of the GNU General Public License
 *  along with Aion-Lightning.
 *  If not, see <http://www.gnu.org/licenses/>.
 */


package com.aionemu.loginserver.network.aion.serverpackets;

import javax.crypto.SecretKey;

import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.ClassicProtocol;
import com.aionemu.loginserver.network.aion.LoginConnection;

/**
 * Primeiro pacote da conexao: entrega ao cliente o modulo RSA e a chave Blowfish da sessao.
 *
 * O layout do Classic 4.5 nao e o do retail. A chave Blowfish fica 4 bytes antes (0x95 em vez de
 * 0x99), o que abre espaco para o flag 0xFD em 0xA8 e para a versao do cliente em 0xA9. Errar esse
 * deslocamento e especialmente ingrato: o cliente aceita o SM_INIT em silencio e so falha depois,
 * quando nenhum pacote seguinte decripta.
 *
 * <pre>
 *   0x00         opcode 0x00
 *   0x01..0x04   session id
 *   0x05..0x08   protocol revision (0xC621)
 *   0x09..0x88   modulo RSA embaralhado (128 bytes)
 *   0x89..0x94   zeros (12 bytes)
 *   0x95..0xA4   chave Blowfish da sessao (16 bytes)
 *   0xA5..0xA7   zeros
 *   0xA8         flag que habilita o RSA (0xFD)
 *   0xA9..0xAC   versao do cliente: 04 05 00 00
 *   0xAD..0xB0   zeros -- padding ate 177 bytes, ver ClassicProtocol.INIT_PACKET_SIZE
 * </pre>
 */
public final class SM_INIT extends AionServerPacket {

    /**
     * Session Id of this connection
     */
    private final int sessionId;
    /**
     * public Rsa key that client will use to encrypt login and password that
     * will be send in RequestAuthLogin client packet.
     */
    private final byte[] publicRsaKey;
    /**
     * blowfish key for packet encryption/decryption.
     */
    private final byte[] blowfishKey;

    /**
     * Constructor
     *
     * @param client
     * @param blowfishKey
     */
    public SM_INIT(LoginConnection client, SecretKey blowfishKey) {
        this(client.getEncryptedModulus(), blowfishKey.getEncoded(), client.getSessionId());
    }

    /**
     * Creates new instance of <tt>SM_INIT</tt> packet.
     *
     * @param publicRsaKey Public RSA key
     * @param blowfishKey Blowfish key
     * @param sessionId Session identifier
     */
    private SM_INIT(byte[] publicRsaKey, byte[] blowfishKey, int sessionId) {
        super(0x00);
        this.sessionId = sessionId;
        this.publicRsaKey = publicRsaKey;
        this.blowfishKey = blowfishKey;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    protected void writeImpl(LoginConnection con) {
        writeD(sessionId);                              // 0x01
        writeD(0x0000c621);                             // 0x05 protocol revision
        writeB(publicRsaKey);                           // 0x09 modulo RSA embaralhado

        writeD(0x00);                                   // 0x89
        writeD(0x00);                                   // 0x8D
        writeD(0x00);                                   // 0x91

        writeB(blowfishKey);                            // 0x95 chave Blowfish da sessao

        writeC(0x00);                                   // 0xA5
        writeC(0x00);                                   // 0xA6
        writeC(0x00);                                   // 0xA7
        writeC(ClassicProtocol.INIT_RSA_ENABLE_FLAG);   // 0xA8
        writeC(ClassicProtocol.CLIENT_VERSION_MAJOR);   // 0xA9
        writeC(ClassicProtocol.CLIENT_VERSION_MINOR);   // 0xAA
        writeC(0x00);                                   // 0xAB
        writeC(0x00);                                   // 0xAC

        writeD(0x00);                                   // 0xAD padding ate INIT_PACKET_SIZE
    }
}
