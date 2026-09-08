package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.CharacterBanInfo;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.PlayerSettings;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.services.AccountService;

/**
 * Classic 5.0 S_CHARACTER_LIST (opcode 0xC7 / 199)
 */
public class SM_CHARACTER_LIST extends AbstractPlayerInfoPacket {

	private final int unk;
	private final int playOk2;

	public SM_CHARACTER_LIST(int playOk2) {
		this(2, playOk2);
	}

	public SM_CHARACTER_LIST(int unk, int playOk2) {
		this.unk = unk;
		this.playOk2 = playOk2;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(unk);
		writeD(playOk2);
		writeB(new byte[5]);
		if (unk == 0) {
			writeC(0);
		} else if (unk == 2) {
			Account account = con.getAccount();
			AccountService.removeDeletedCharacters(account);
			writeC(account.size());

			for (PlayerAccountData playerData : account.getSortedAccountsList()) {
				CharacterBanInfo cbi = playerData.getCharBanInfo();
				writePlayerInfo(playerData, con);
				PlayerSettings settings = playerData.getPlayerSettings();
				writeH(settings != null ? settings.getDisplay() : 0);
				writeH(settings != null ? settings.getDeny() : 0);
				writeD(0);
				writeQ(playerData.hasUnreadMail() ? 1 : 0);
				writeQ(0);
				writeB(new byte[100]);
				writeD(0);
				writeD(0);
				writeB(new byte[12]);
				if (cbi != null && cbi.getEnd() > System.currentTimeMillis() / 1000) {
					writeD((int) cbi.getStart());
					writeD((int) cbi.getEnd());
					writeS(cbi.getReason());
				} else {
					writeD(0);
					writeD(0);
					writeH(0);
				}
			}
		}
	}
}

