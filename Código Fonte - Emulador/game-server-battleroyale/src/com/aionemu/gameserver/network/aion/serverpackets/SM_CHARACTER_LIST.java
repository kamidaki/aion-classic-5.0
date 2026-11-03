package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.ArrayList;
import java.util.List;

import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.CharacterBanInfo;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.PlayerSettings;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.services.AccountService;

/**
 * Classic 5.0 S_CHARACTER_LIST (opcode 0xC7 / 199): [C tipo][D playOk2][5 b][C n] e n personagens.
 * <p>
 * A lista vai em páginas de 6: a primeira página cheia com tipo 0, as seguintes com tipo 1 (12 personagens = 0 + 1 nas capturas de combate e
 * aumentariventario) e o resto (0 a 5) por último com tipo 2; sem página cheia, um tipo 0 vazio vai
 * antes. Em todas as capturas oficiais: 1, 2 e 4 personagens = 0 vazio + 2; 6 = 0 (6) + 2 vazio; 8, 9 e 10 = 0 (6) + 2 (resto). O emulador
 * mandava tudo num tipo 2 só, e com 8 personagens a tela de seleção mostrava 6.
 */
public class SM_CHARACTER_LIST extends AbstractPlayerInfoPacket {

	public static final int PAGE_SIZE = 6;

	private final int type;
	private final int playOk2;
	private final List<PlayerAccountData> entries;

	private SM_CHARACTER_LIST(int type, int playOk2, List<PlayerAccountData> entries) {
		this.type = type;
		this.playOk2 = playOk2;
		this.entries = entries;
	}

	/**
	 * Os pacotes da lista de personagens da conta, paginados como no oficial.
	 */
	public static List<SM_CHARACTER_LIST> of(Account account, int playOk2) {
		AccountService.removeDeletedCharacters(account);
		List<PlayerAccountData> all = account.getSortedAccountsList();
		List<SM_CHARACTER_LIST> packets = new ArrayList<>();
		int full = all.size() / PAGE_SIZE;
		for (int i = 0; i < full; i++)
			packets.add(new SM_CHARACTER_LIST(i == 0 ? 0 : 1, playOk2, all.subList(i * PAGE_SIZE, (i + 1) * PAGE_SIZE)));
		if (full == 0)
			packets.add(new SM_CHARACTER_LIST(0, playOk2, List.of()));
		packets.add(new SM_CHARACTER_LIST(2, playOk2, all.subList(full * PAGE_SIZE, all.size())));
		return packets;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);
		writeD(playOk2);
		writeB(new byte[5]);
		writeC(entries.size());
		for (PlayerAccountData playerData : entries) {
			CharacterBanInfo cbi = playerData.getCharBanInfo();
			writePlayerInfo(playerData, con);
			PlayerSettings settings = playerData.getPlayerSettings();
			writeH(settings != null ? settings.getDisplay() : 0);
			writeH(settings != null ? settings.getDeny() : 0);
			// entrada de 766 b como no oficial: o D 0 que vinha aqui deu lugar à data de criação no writePlayerInfo
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

