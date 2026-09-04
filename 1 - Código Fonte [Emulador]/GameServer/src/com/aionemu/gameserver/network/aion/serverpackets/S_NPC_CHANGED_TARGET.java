package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.utils.MathUtil;


public class S_NPC_CHANGED_TARGET extends AionServerPacket {

	private VisibleObject visibleObject;
	private int targetObjectId;
	private int heading;

	public S_NPC_CHANGED_TARGET(VisibleObject visibleObject) {
		this.visibleObject = visibleObject;
		if (visibleObject.getTarget() != null) {
			this.targetObjectId = visibleObject.getTarget().getObjectId();
			// O ultimo byte e a direcao em que o objeto passa a olhar, ou seja a dele para o alvo --
			// nao a direcao do alvo. Conferido na captura oficial (subida-1-60, sessao 1, indice
			// 534): o NPC 730137 em (1655.94, 1400.75) olhando para o jogador em (1657.80, 1401.13)
			// da angulo 11.55 graus, heading 3, exatamente o byte do fio.
			this.heading = MathUtil.convertDegreeToHeading(
				MathUtil.calculateAngleFrom(visibleObject, visibleObject.getTarget())) & 0xFF;
		}
		else {
			this.targetObjectId = 0;
			this.heading = visibleObject.getHeading();
		}
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(visibleObject.getObjectId());
		writeD(targetObjectId);
		writeC(heading);
	}
}
