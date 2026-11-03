package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x15C, missões da Legion (login, criação e entrada): [D agora][D 0][H n], e para cada missão (68 b) seguida das ações (65 b cada):
 *
 * <pre>
 * missão: [C 3][Q instância][D missão][8 b 0][C período][C 0][C 1][25 b 0][Q início do período][Q última atualização][C 0][H ações]
 * ação:   [Q instância][D ação][Q instância da missão][C 3][C tipo][C estado][D progresso][21 b 0][Q início do período][Q atualização][C 0]
 * </pre>
 *
 * Conferido nos 25 pacotes das capturas (sobra 0 em todos). Período 1 diária, 2 semanal, 7 retorno; estado 1 = em andamento.
 * PENDENTE_DE_COMPROVACAO: o estado de uma ação já concluída neste pacote (nenhum login com ação concluída); usa-se o 2 do S 0x15D.
 */
public class SM_LEGION_MISSION_LIST extends AionServerPacket {

	public record Action(long instanceId, int actionId, int typeCode, boolean complete, int progress, long lastUpdate) {}

	public record Mission(long instanceId, int missionId, int periodCode, long periodStart, long lastUpdate, List<Action> actions) {}

	private final int now;
	private final List<Mission> missions;

	public SM_LEGION_MISSION_LIST(int now, List<Mission> missions) {
		this.now = now;
		this.missions = missions;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(now);
		writeD(0);
		writeH(missions.size());
		for (Mission mission : missions) {
			writeC(3);
			writeQ(mission.instanceId());
			writeD(mission.missionId());
			writeB(new byte[8]);
			writeC(mission.periodCode());
			writeC(0);
			writeC(1);
			writeB(new byte[25]);
			writeQ(mission.periodStart());
			writeQ(mission.lastUpdate());
			writeC(0);
			writeH(mission.actions().size());
			for (Action action : mission.actions()) {
				writeQ(action.instanceId());
				writeD(action.actionId());
				writeQ(mission.instanceId());
				writeC(3);
				writeC(action.typeCode());
				writeC(action.complete() ? 2 : 1);
				writeD(action.progress());
				writeB(new byte[21]);
				writeQ(mission.periodStart());
				writeQ(action.lastUpdate());
				writeC(0);
			}
		}
	}
}
