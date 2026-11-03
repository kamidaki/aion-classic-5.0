package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.HashSet;
import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.globaltrade.GlobalTradeService;

/**
 * C_GLOBAL_TRADE_LIST, decodificado 0x114 (cru 0x1EE). 26 pacotes nas capturas: 13 bytes, ou 69 na busca por nome.
 * <p>
 * [C ordem][H página][D categoria][C moeda][C][H][H n][n x D itemId]. Os 4 bytes da moeda até antes do n voltam iguais no fim do cabeçalho
 * do S_GLOBAL_TRADE_LIST. Na busca o cliente resolve o texto e manda os itemIds; a categoria vem junto, mas a resposta traz 0.
 */
public class CM_GLOBAL_TRADE_LIST extends AionClientPacket {

	private static final int MAX_SEARCH_ITEMS = 2000;

	private int sort;
	private int page;
	private int category;
	private byte[] tail;
	private Set<Integer> itemIds;
	private boolean valid;

	public CM_GLOBAL_TRADE_LIST(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemIds = new HashSet<>(); // protótipos são clonados raso
		valid = false;
		if (getRemainingBytes() < 13)
			return;
		sort = readUC();
		page = readUH();
		category = readD();
		tail = readB(4);
		int count = readUH();
		if (count > MAX_SEARCH_ITEMS || getRemainingBytes() != count * 4)
			return;
		for (int i = 0; i < count; i++)
			itemIds.add(readD());
		valid = true;
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		if (!valid) {
			LoggerFactory.getLogger(CM_GLOBAL_TRADE_LIST.class).warn("C_GLOBAL_TRADE_LIST inválido de {}", player.getName());
			return;
		}
		GlobalTradeService.getInstance().sendList(player, sort, page, category, GlobalTradeCurrency.of(tail[0]), tail, itemIds);
	}
}
