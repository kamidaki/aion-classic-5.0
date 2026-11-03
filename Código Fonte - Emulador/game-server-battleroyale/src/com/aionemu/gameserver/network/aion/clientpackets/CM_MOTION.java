package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * "Change motion" of the motion tab (Classic 5.0, decoded opcode 0x04F).
 * <p>
 * Layout from the official capture motion.pcapng (2026-09-29), 9 changes of 6 bytes: [C 4][H count][count x (H motionId, C slot)].
 * Motion id 0 clears the slot: <tt>04 01 00 00 00 02</tt> turns off the run motion, <tt>04 01 00 02 00 02</tt> sets it again to motion 2.
 *
 * @author Lost Academy Team & Durak
 */
public class CM_MOTION extends AionClientPacket {

	private int[] motionIds;
	private int[] motionTypes;

	public CM_MOTION(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readC(); // 4
		int count = Math.min(readUH(), getRemainingBytes() / 3);
		motionIds = new int[count];
		motionTypes = new int[count];
		for (int i = 0; i < count; i++) {
			motionIds[i] = readUH();
			motionTypes[i] = readUC();
		}
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		for (int i = 0; i < motionIds.length; i++)
			player.getMotions().setActive(motionIds[i], motionTypes[i]);
	}
}
