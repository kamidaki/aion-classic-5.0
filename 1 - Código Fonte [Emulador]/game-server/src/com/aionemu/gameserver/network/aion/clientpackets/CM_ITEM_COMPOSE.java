package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.item.ItemComposeService;

/**
 * C_START_ITEM_COMPOSE provável, decodificado 0x154 (cru 0x22E): fusão no Altar of Transcendence, aberto pelo quick menu, sem NPC.
 * <p>
 * Captura (2 de 2, 19 bytes): [D receita][H n][n x (D itemId, D quantidade)][D 0][C quantidade de fusões], com n = 1 e 6 itens. Com n = 1
 * o mesmo corpo também lê como [n x (D itemId, Q quantidade)][C], então os dois tamanhos são aceitos.
 */
public class CM_ITEM_COMPOSE extends AionClientPacket {

	private static final int MAX_MATERIAL_TYPES = 64;

	private int recipeId;
	private Map<Integer, Long> materials;
	private int quantity;
	private String invalid;

	public CM_ITEM_COMPOSE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		materials = new LinkedHashMap<>(); // protótipos são clonados raso
		invalid = "cabeçalho curto";
		if (getRemainingBytes() < 7)
			return;
		recipeId = readD();
		int n = readUH();
		int remaining = getRemainingBytes();
		boolean wideCount = remaining != n * 8 + 5 && remaining == n * 12 + 1;
		invalid = "tamanho " + remaining + " para " + n + " materiais";
		if (n == 0 || n > MAX_MATERIAL_TYPES || !wideCount && remaining != n * 8 + 5)
			return;
		for (int i = 0; i < n; i++) {
			int itemId = readD();
			long count = wideCount ? readQ() : Integer.toUnsignedLong(readD());
			if (itemId <= 0 || count <= 0 || materials.merge(itemId, count, Long::sum) != count) {
				invalid = "material repetido ou vazio";
				return;
			}
		}
		if (!wideCount)
			readD();
		quantity = readUC();
		invalid = quantity == 0 ? "quantidade 0" : null;
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		if (invalid != null) {
			LoggerFactory.getLogger(CM_ITEM_COMPOSE.class).warn("Altar: pedido inválido de {} (receita {}): {}", player.getName(), recipeId, invalid);
			ItemComposeService.reject(player, recipeId, 0);
			return;
		}
		ItemComposeService.start(player, recipeId, materials, quantity);
	}
}
