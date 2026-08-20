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

import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.ClassicProtocol;
import com.aionemu.loginserver.network.aion.LoginConnection;
import com.aionemu.loginserver.network.aion.SessionKey;

/**
 * Confirma o login e libera o cliente para a tela de selecao de servidor.
 *
 * O tamanho e o mesmo do retail (77 bytes); o que muda sao tres campos que o retail deixava
 * zerados e que o cliente Classic 4.5 confere: as flags de conta em 0x10, a assinatura em 0x20 e
 * o aceite dos Termos de Servico em 0x30. Ver {@link ClassicProtocol} para o que cada um destrava.
 *
 * @author -Nemesiss-
 */
public class SM_LOGIN_OK extends AionServerPacket {

    /**
     * accountId is part of session key - its used for security purposes
     */
    private final int accountId;
    /**
     * loginOk is part of session key - its used for security purposes
     */
    private final int loginOk;

    /**
     * Constructs new instance of <tt>SM_LOGIN_OK</tt> packet.
     *
     * @param key session key
     */
    public SM_LOGIN_OK(SessionKey key) {
        super(0x03);
        this.accountId = key.accountId;
        this.loginOk = key.loginOk;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    protected void writeImpl(LoginConnection con) {
        writeD(accountId);                              // 0x00
        writeD(loginOk);                                // 0x04
        writeD(0x00);                                   // 0x08
        writeD(0x00);                                   // 0x0C
        writeD(ClassicProtocol.ACCOUNT_FLAGS);          // 0x10
        writeD(ClassicProtocol.ACCOUNT_FLAGS);          // 0x14
        writeD(ClassicProtocol.ACCOUNT_FLAGS);          // 0x18
        writeD(ClassicProtocol.ACCOUNT_FLAGS);          // 0x1C
        writeC(ClassicProtocol.LOGIN_OK_SIGNATURE_0);   // 0x20
        writeC(ClassicProtocol.LOGIN_OK_SIGNATURE_1);   // 0x21
        writeC(0x00);                                   // 0x22
        writeC(0x00);                                   // 0x23
        writeD(0x00);                                   // 0x24
        writeD(0x00);                                   // 0x28
        writeD(0x00);                                   // 0x2C
        writeD(ClassicProtocol.TOS_ACCEPTED);           // 0x30
        writeB(new byte[0x19]);                         // 0x34..0x4C
    }
}
