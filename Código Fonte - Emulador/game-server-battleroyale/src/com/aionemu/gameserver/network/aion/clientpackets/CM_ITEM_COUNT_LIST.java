package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Pedido com uma lista de itens do inventário, comum ao Moreth (0x111) e ao Book of Legends (0xDC, 0xDD): [H n][n x (D objeto, Q quantidade)].
 * Objeto repetido, quantidade zero ou tamanho que não fecha com n invalidam o pedido inteiro.
 */
public abstract class CM_ITEM_COUNT_LIST extends AionClientPacket {

	private final int maxItems;
	private Map<Integer, Long> items;
	private String invalid;

	protected CM_ITEM_COUNT_LIST(int opcode, Set<State> validStates, int maxItems) {
		super(opcode, validStates);
		this.maxItems = maxItems;
	}

	@Override
	protected void readImpl() {
		items = new LinkedHashMap<>(); // protótipos são clonados raso
		invalid = "cabeçalho curto";
		if (getRemainingBytes() < 2)
			return;
		int n = readUH();
		invalid = "tamanho " + getRemainingBytes() + " para " + n + " itens";
		if (n == 0 || n > maxItems || getRemainingBytes() != n * 12)
			return;
		for (int i = 0; i < n; i++) {
			int objectId = readD();
			long count = readQ();
			if (count <= 0 || items.putIfAbsent(objectId, count) != null) {
				invalid = "item repetido ou vazio";
				return;
			}
		}
		invalid = null;
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		if (invalid != null)
			onInvalid(player, invalid);
		else
			handle(player, items);
	}

	/**
	 * @param items
	 *          objeto -> quantidade, na ordem do pedido
	 */
	protected abstract void handle(Player player, Map<Integer, Long> items);

	protected abstract void onInvalid(Player player, String reason);
}
