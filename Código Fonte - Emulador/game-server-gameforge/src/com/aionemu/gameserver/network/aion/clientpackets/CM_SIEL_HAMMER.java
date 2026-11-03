package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.craft.SielHammerService;

/** C_ITEM_CRUSH, captured decoded 0xFF / wire 0x1F5. H count, (D objectId, Q quantity). */
public class CM_SIEL_HAMMER extends AionClientPacket {
	private Map<Integer, Long> selected;
	private boolean valid;
	public CM_SIEL_HAMMER(int opcode, Set<State> states) { super(opcode, states); }
	@Override
	protected void readImpl() {
		valid = false;
		selected = new LinkedHashMap<>(); // prototypes are shallow-cloned
		if (getRemainingBytes() < 2) return;
		int count = readUH();
		if (count < 1 || count > 20 || getRemainingBytes() != count * 12) return;
		boolean distinct = true;
		for (int i = 0; i < count; i++) {
			int objectId = readD();
			long quantity = readQ();
			// Object ids are unsigned on the wire: captured 0xC03FB271 is a valid Java negative int.
			if (objectId == 0 || quantity <= 0 || selected.put(objectId, quantity) != null) distinct = false;
		}
		valid = distinct;
	}
	@Override
	protected void runImpl() {
		var player = getConnection().getActivePlayer();
		if (player != null) {
			if (!valid) org.slf4j.LoggerFactory.getLogger(CM_SIEL_HAMMER.class).warn(
				"Siel Hammer invalid request: player={}, selected={}, remainingBytes={}", player.getObjectId(), selected, getRemainingBytes());
			SielHammerService.start(player, valid ? selected : Map.of());
		}
	}
}
