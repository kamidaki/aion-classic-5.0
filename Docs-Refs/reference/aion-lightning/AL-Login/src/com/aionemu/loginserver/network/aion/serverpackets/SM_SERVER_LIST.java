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

import java.util.Collection;
import java.util.Map;

import com.aionemu.loginserver.GameServerInfo;
import com.aionemu.loginserver.GameServerTable;
import com.aionemu.loginserver.configs.Config;
import com.aionemu.loginserver.controller.AccountController;
import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.ClassicProtocol;
import com.aionemu.loginserver.network.aion.LoginConnection;

/**
 * Lista de servidores mostrada apos o login.
 *
 * Cada entrada tem 21 bytes, sendo o ultimo o bracket -- que o cliente compara com o valor passado
 * em {@code -cc:N} na linha de comando (0x842B1B). Uma entrada cujo bracket nao bate simplesmente
 * nao aparece na tela, sem erro nenhum.
 *
 * A secao de contagem de personagens tambem difere do retail: o cliente Classic le o short e ja
 * espera 1 byte por servidor, sem o byte intercalado que o retail enviava (0x843077).
 *
 * @author -Nemesiss-
 * @modified cura
 */
public class SM_SERVER_LIST extends AionServerPacket {

    public SM_SERVER_LIST() {
        super(0x04);
    }

    @Override
    protected void writeImpl(LoginConnection con) {
        Collection<GameServerInfo> servers = GameServerTable.getGameServers();
        Map<Integer, Integer> charactersCountOnServer = null;

        int accountId = con.getAccount().getId();
        //int accessLevel = con.getAccount().getAccessLevel();
        int maxId = 0;

        charactersCountOnServer = AccountController.getGSCharacterCountsFor(accountId);

        writeC(servers.size());// servers
        writeC(con.getAccount().getLastServer());// last server
        for (GameServerInfo gsi : servers) {
            if (gsi.getId() > maxId) {
                maxId = gsi.getId();
            }

            writeC(gsi.getId());// server id
            writeB(gsi.getIPAddressForPlayer(con.getIP())); // server IP
            writeD(gsi.getPort());// port
            writeC(0x00); // age limit
            writeC(0x01);// pvp=1
            writeH(gsi.getCurrentPlayers());// currentPlayers
            writeH(gsi.getMaxPlayers());// maxPlayers
            writeC(gsi.isOnline() ? 1 : 0);// ServerStatus, up=1
            writeD(ClassicProtocol.SERVER_BITS);// bit 10 marca servidor Classic
            writeC(Config.SERVER_BRACKET);// tem que casar com o -cc:N do cliente
        }

        writeH(maxId);

        for (int i = 1; i <= maxId; i++) {
            if (charactersCountOnServer.containsKey(i)) {
                writeC(charactersCountOnServer.get(i));
            } else {
                writeC(0);
            }
        }
    }
}
