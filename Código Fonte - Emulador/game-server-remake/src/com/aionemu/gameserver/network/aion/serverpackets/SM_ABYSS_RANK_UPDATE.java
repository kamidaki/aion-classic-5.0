package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
// TODO Rename
public class SM_ABYSS_RANK_UPDATE extends AionServerPacket {

	private final int action;
	private final int objectId;
	private final int value;

	public SM_ABYSS_RANK_UPDATE(int action, Player player) {
		this(action, player.getObjectId(), switch (action) {
			case 0 -> player.getAbyssRank().getRank().getId(); // Abyss rank change
			case 1 -> player.getCurrentTeamId(); // Team objectId
			case 2 -> player.isMentor() ? 1 : 0; // Mentor status change
			default -> 0;
		});
	}

	private SM_ABYSS_RANK_UPDATE(int action, int objectId, int value) {
		this.action = action;
		this.objectId = objectId;
		this.value = value;
	}

	/**
	 * Saida do mundo: o oficial manda [C 0][D obj][D 0] antes do S_ASK_QUIT_RESULT, tanto indo para a selecao quanto para a tela de edicao
	 * (subida-1-60 e aionlook.pcapng).
	 */
	public static SM_ABYSS_RANK_UPDATE onLeaveWorld(int objectId) {
		return new SM_ABYSS_RANK_UPDATE(0, objectId, 0);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(action);
		writeD(objectId);
		if (action <= 2)
			writeD(value);
	}

}
