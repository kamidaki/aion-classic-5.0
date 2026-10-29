package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x195 (sem nome na tabela de registro do Game.dll 5.0): barra da coleta de objeto com ui craft_ui_always, resposta ao C 0x131.
 * <p>
 * 5.0 oficial (Balic Treasury.pcapng, 29/10, 802959 Blood Drana Products): [D estado][D progresso][D 700][D 1200], 16 bytes. Estado 0 abre a
 * barra (progresso 0), 1 avança, 3 = sucesso com 10000. Os dois últimos campos foram 700 e 1200 nos 7 pacotes.
 */
public class SM_COLLECT_OBJECT_PROGRESS extends AionServerPacket {

	public static final int START = 0, PROGRESS = 1, SUCCESS = 3;
	public static final int MAX_PROGRESS = 10000;

	private final int state;
	private final int progress;

	public SM_COLLECT_OBJECT_PROGRESS(int state, int progress) {
		this.state = state;
		this.progress = progress;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(state);
		writeD(progress);
		writeD(700);
		writeD(1200);
	}
}
