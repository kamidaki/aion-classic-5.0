package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Dec 0x00AB, fio 0x022B, sem corpo. O cliente manda em pares a cada troca de cena (logo depois do S_ASK_QUIT_RESULT e da entrada no mundo).
 * O oficial nao responde: nas capturas aionlook e subida-1-60 o S 0x8D so vem depois do C 0x0004. Ficava no CM_PING, que mandava SM_PONG
 * em AUTHED (tela de edicao e selecao) e contava o intervalo como ping de 180 s, gerando o falso "possibly using time/speed hack".
 */
public class CM_CLIENT_STAGE_CHANGE extends AionClientPacket {

	public CM_CLIENT_STAGE_CHANGE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
	}

	@Override
	protected void runImpl() {
	}
}
