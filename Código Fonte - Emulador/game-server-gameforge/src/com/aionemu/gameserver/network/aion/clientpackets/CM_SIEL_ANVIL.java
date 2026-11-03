package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.ArrayList;
import java.util.List;
import java.util.HashSet;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.craft.SielAnvilService;

/** Classic 5.0 C_SPECIAL_CRAFT, decoded 0x108 / wire 0x1FA. */
public class CM_SIEL_ANVIL extends AionClientPacket {
	private int recipeId;
	private Map<Integer, Long> materials;
	private boolean valid;
	private int groupIndex;
	private int quantity;
	private List<Integer> selectedObjects;
	private String invalidReason;

	public CM_SIEL_ANVIL(int opcode, Set<State> states) { super(opcode, states); }

	@Override
	protected void readImpl() {
		valid = false;
		recipeId = 0;
		groupIndex = 0;
		quantity = 0;
		invalidReason = "truncated header";
		materials = new LinkedHashMap<>(); // packet prototypes are shallow-cloned
		selectedObjects = new ArrayList<>();
		if (getRemainingBytes() < 13)
			return;
		recipeId = readD();
		groupIndex = readD();
		int selectedCount = readUH();
		invalidReason = "selected equipment vector length";
		if (selectedCount > 19 || getRemainingBytes() < selectedCount * 4 + 3)
			return;
		for (int i = 0; i < selectedCount; i++)
			selectedObjects.add(readD());
		int size = readUH();
		invalidReason = "ordinary material vector length";
		if (size > 19 || getRemainingBytes() != size * 8 + 1)
			return;
		boolean distinct = true;
		for (int i = 0; i < size; i++) {
			int id = readD();
			long count = Integer.toUnsignedLong(readD());
			if (id <= 0 || count == 0 || materials.put(id, count) != null)
				distinct = false;
		}
		quantity = readUC();
		invalidReason = !distinct ? "duplicate, zero or invalid ordinary material"
			: groupIndex < 0 ? "invalid group" : quantity == 0 ? "zero quantity"
			: size == 0 && selectedCount == 0 ? "empty materials"
			: selectedObjects.stream().anyMatch(id -> id <= 0) ? "invalid selected object id"
			: new HashSet<>(selectedObjects).size() != selectedCount ? "duplicate selected object id" : null;
		valid = invalidReason == null;
	}

	@Override
	protected void runImpl() {
		var player = getConnection().getActivePlayer();
		if (player != null) {
			if (!valid)
				org.slf4j.LoggerFactory.getLogger(CM_SIEL_ANVIL.class).warn(
					"Siel Anvil invalid request: player={}, recipe={}, group={}, quantity={}, reason={}, materials={}, selectedObjects={}, remainingBytes={}",
					player.getObjectId(), recipeId, groupIndex, quantity, invalidReason, materials, selectedObjects, getRemainingBytes());
			SielAnvilService.start(player, recipeId, groupIndex, quantity, valid ? materials : Map.of(), valid ? selectedObjects : List.of());
		}
	}
}
