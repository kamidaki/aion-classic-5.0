package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.clientpackets.CM_CHARACTER_EDIT;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_PLASTIC_SURGERY extends AionServerPacket {

	/**
	 * Abre a tela: 1 com ticket, 2 sem (previa; o oficial manda 2 para conta sem ticket, aionlook.pcapng). Com 1 em resposta ao C_EDIT_CHARACTER o
	 * cliente refez a abertura (C 0x1A x2 + C_ASK_QUIT, 30/09 23:02), entao 1 e 2 sao abertura. 0 como resultado e hipotese: e o unico
	 * S_ do Game.dll para a edicao, como o S_CREATE/DELETE/RESTORE_CHARACTER sao os unicos dos seus pares.
	 */
	private static final int OPEN_WITH_TICKET = 1, OPEN_PREVIEW = 2, EDIT_RESULT = 0;

	private final int playerObjId;
	private final int mode;
	private final boolean isGenderSwitch;

	public SM_PLASTIC_SURGERY(Player player, boolean isGenderSwitch) {
		this(player.getObjectId(), CM_CHARACTER_EDIT.checkOrRemoveTicket(player, isGenderSwitch, false) ? OPEN_WITH_TICKET : OPEN_PREVIEW, isGenderSwitch);
	}

	private SM_PLASTIC_SURGERY(int playerObjId, int mode, boolean isGenderSwitch) {
		this.playerObjId = playerObjId;
		this.mode = mode;
		this.isGenderSwitch = isGenderSwitch;
	}

	public static SM_PLASTIC_SURGERY editResult(int playerObjId, boolean isGenderSwitch) {
		return new SM_PLASTIC_SURGERY(playerObjId, EDIT_RESULT, isGenderSwitch);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjId);
		writeC(mode);
		writeC(isGenderSwitch ? 1 : 0);
	}
}
