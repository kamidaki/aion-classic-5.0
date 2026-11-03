package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RESTORE_CHARACTER;
import com.aionemu.gameserver.services.AccountService;
import com.aionemu.gameserver.services.player.PlayerService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_RESTORE_CHARACTER extends AionClientPacket {

	/**
	 * PlayOk2 - we dont care...
	 */
	@SuppressWarnings("unused")
	private int playOk2;
	/**
	 * ObjectId of character that deletion should be canceled
	 */
	private int chaOid;

	/**
	 * Constructs new instance of <tt>CM_RESTORE_CHARACTER </tt> packet
	 * 
	 * @param opcode
	 */
	public CM_RESTORE_CHARACTER(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		playOk2 = readD();
		chaOid = readD();
	}

	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CM_RESTORE_CHARACTER.class);

	@Override
	protected void runImpl() {
		Account account = getConnection().getAccount();
		if (account == null) {
			log.warn("[RESTORE_CHARACTER] account e null!");
			return;
		}

		log.info("[RESTORE_CHARACTER] Recebido pedido de restauracao: playOk2={}, chaOid={}", playOk2, chaOid);

		PlayerAccountData pad = account.getPlayerAccountData(chaOid);
		if (pad == null) {
			pad = account.getPlayerAccountData(playOk2);
			if (pad != null) {
				int tmp = chaOid;
				chaOid = playOk2;
				playOk2 = tmp;
				log.info("[RESTORE_CHARACTER] Inversao detectada: chaOid ajustado para {}", chaOid);
			}
		}

		boolean success = pad != null && PlayerService.cancelPlayerDeletion(pad);
		if (success) {
			AccountService.invalidateCache(account.getId());
		}
		sendPacket(new SM_RESTORE_CHARACTER(chaOid, success));
		log.info("[RESTORE_CHARACTER] Personagem {} restaurado com sucesso={}", chaOid, success);
	}
}
