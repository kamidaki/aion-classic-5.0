package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Registro de penteado comum ao S 0x177 (lista) e ao S 0x178 (ação), 28 b, no formato do leitor do Game.dll (0x8D89E0 e 0x8D8BB0): [D
 * objeto][Q][D dono][D item][C favorito][C][H][D].
 * <p>
 * Captura de 2026-09-21: objeto c081b22e, Q 842, dono = o personagem, item 169800480, 0, 1, 0, 0. A lista do cliente só guarda objeto, item,
 * favorito, o H e o último D, e o S 0x177 só aceita o registro com o 2º C = 1 (0x8CC654). O Q e o dono não são lidos; o Q vai 0 por falta de
 * prova do que é.
 */
public abstract class AbstractHairstylePacket extends AionServerPacket {

	protected final void writeHairstyle(int ownerObjectId, WardrobeEntry entry) {
		writeD(entry.getObjectId());
		writeQ(0);
		writeD(ownerObjectId);
		writeD(entry.getItemId());
		writeC(entry.isLiked() ? 1 : 0);
		writeC(1);
		writeH(0);
		writeD(0);
	}
}
