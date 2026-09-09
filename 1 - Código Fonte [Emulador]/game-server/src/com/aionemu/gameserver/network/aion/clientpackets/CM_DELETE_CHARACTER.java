package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.configs.main.SecurityConfig;
import com.aionemu.gameserver.dao.PlayerPasskeyDAO;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.CharacterPasskey.ConnectType;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CHARACTER_SELECT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DELETE_CHARACTER;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.AccountService;
import com.aionemu.gameserver.services.LegionService;
import com.aionemu.gameserver.services.player.PlayerService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_DELETE_CHARACTER extends AionClientPacket {

	@SuppressWarnings("unused")
	private int playOk2;
	/**
	 * ObjectId of character that should be deleted.
	 */
	private int chaOid;

	public CM_DELETE_CHARACTER(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		playOk2 = readD();
		chaOid = readD();
	}

	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CM_DELETE_CHARACTER.class);

	@Override
	protected void runImpl() {
		Account account = getConnection().getAccount();
		if (account == null) {
			log.warn("CM_DELETE_CHARACTER: Account e null!");
			return;
		}

		log.debug("CM_DELETE_CHARACTER: Recebido pedido de delecao: playOk2={}, chaOid={}", playOk2, chaOid);

		PlayerAccountData playerAccData = account.getPlayerAccountData(chaOid);
		if (playerAccData == null) {
			// Suporte a inversao de campos no 5.0 Classic (chaOid enviado antes de playOk2)
			playerAccData = account.getPlayerAccountData(playOk2);
			if (playerAccData != null) {
				int tmp = chaOid;
				chaOid = playOk2;
				playOk2 = tmp;
				log.warn("CM_DELETE_CHARACTER: Inversao detectada: chaOid ajustado para {}", chaOid);
			}
		}

		if (playerAccData == null) {
			log.warn("CM_DELETE_CHARACTER: Personagem nao encontrado na conta {} para chaOid={} ou playOk2={}",
					account.getId(), chaOid, playOk2);
			return;
		}

		if (LegionService.getInstance().getLegionMember(playerAccData.getPlayerCommonData()) != null) {
			sendPacket(SM_SYSTEM_MESSAGE.STR_GUILD_DISPERSE_STAYMODE_CANCEL_1());
			return;
		}
		boolean isDeleted = PlayerService.deletePlayer(playerAccData);
		AccountService.invalidateCache(account.getId());
		if (isDeleted) {
			account.removePlayerAccountData(chaOid);
			sendPacket(new SM_DELETE_CHARACTER(chaOid, 0));
			log.info("CM_DELETE_CHARACTER: O personagem {} foi deletado imediatamente.", chaOid);
		} else {
			sendPacket(new SM_DELETE_CHARACTER(chaOid, playerAccData.getDeletionTimeInSeconds()));
			log.info("CM_DELETE_CHARACTER: O personagem {} foi marcado para delecao com timer.", chaOid);
			PlayerService.scheduleCharacterDeletion(getConnection(), chaOid, playerAccData.getDeletionDate().getTime());
		}
	}
}
