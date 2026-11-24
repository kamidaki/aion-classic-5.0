package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.PlayerPunishmentsDAO;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ABYSS_RANK_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_QUIT_RESPONSE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TARGET_SELECTED;
import com.aionemu.gameserver.services.player.PlayerLeaveWorldService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_QUIT extends AionClientPacket {

	/**
	 * if true, player wants to go to the character selection or plastic surgery screen.
	 */
	private boolean stayConnected;

	public CM_QUIT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		stayConnected = readC() == 1;
	}

	@Override
	protected void runImpl() {
		AionConnection con = getConnection();
		Player player = con.getActivePlayer();
		boolean charEditScreen = false;

		if (player != null) {
			if (con.getAccount() != null) {
				con.getAccount().setLastPlayerObjectId(player.getObjectId());
			}
			charEditScreen = player.getCommonData().isInEditMode();
			if (stayConnected) { // update char selection info
				player.getAccountData().setVisibleItems(player.getEquipment().getEquippedForAppearance());
				for (PlayerAccountData plAccData : con.getAccount().getPlayerAccDataList())
					plAccData.setCharBanInfo(PlayerPunishmentsDAO.getCharBanInfo(plAccData.getPlayerCommonData().getPlayerObjId()));
				// o oficial zera o S_ETC_STATUS e o alvo antes do S_ASK_QUIT_RESULT, para a selecao e para a tela de edicao
				// (subida-1-60 e aionlook.pcapng); o emulador mandava so o S_ASK_QUIT_RESULT
				sendPacket(SM_ABYSS_RANK_UPDATE.onLeaveWorld(player.getObjectId()));
				sendPacket(new SM_TARGET_SELECTED(null));
			}
			PlayerLeaveWorldService.leaveWorld(player);
		}
		LoggerFactory.getLogger(CM_QUIT.class).info("[QUIT] Conta {} saiu do mundo (player={}, ficaConectado={}, telaDeEdicao={})",
			con.getAccount() != null ? con.getAccount().getId() : "null", player != null ? player.getName() : "null", stayConnected, charEditScreen);

		if (stayConnected)
			sendPacket(new SM_QUIT_RESPONSE(charEditScreen));
		else
			con.close(new SM_QUIT_RESPONSE(charEditScreen)); // makes sure this packet will be sent before closing connection
	}
}
