package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_DELETE_GUILD_MEMBER (0x6F): [D objeto][C continua membro][D hora do logoff][D mensagem][S][S].
 * <p>
 * Na 5.0 o mesmo pacote avisa o logoff de quem continua na Legion: flag 1, hora da saída, sem mensagem e sem nomes (17 b, Kamidakii 22/09, 3 de 3).
 * Saída e expulsão (flag 0) seguem o layout da 4.8: PENDENTE_DE_COMPROVACAO, nenhuma captura tem uma.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_LEGION_LEAVE_MEMBER extends AionServerPacket {

	private String name;
	private String name1;
	private final int playerObjId;
	private final int msgId;
	private final boolean stillMember;
	private final int logoutEpochSeconds;

	public SM_LEGION_LEAVE_MEMBER(int msgId, int playerObjId, String name) {
		this(msgId, playerObjId, name, null);
	}

	public SM_LEGION_LEAVE_MEMBER(int msgId, int playerObjId, String name, String name1) {
		this(playerObjId, false, 0, msgId, name, name1);
	}

	private SM_LEGION_LEAVE_MEMBER(int playerObjId, boolean stillMember, int logoutEpochSeconds, int msgId, String name, String name1) {
		this.playerObjId = playerObjId;
		this.stillMember = stillMember;
		this.logoutEpochSeconds = logoutEpochSeconds;
		this.msgId = msgId;
		this.name = name;
		this.name1 = name1;
	}

	/**
	 * Logoff de um membro, para os outros membros online.
	 */
	public static SM_LEGION_LEAVE_MEMBER logout(LegionMember member) {
		return new SM_LEGION_LEAVE_MEMBER(member.getObjectId(), true, member.getLastOnlineEpochSeconds(), 0, null, null);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjId);
		writeC(stillMember ? 1 : 0);
		writeD(logoutEpochSeconds);
		writeD(msgId);
		writeS(name);
		writeS(name1);
	}
}
