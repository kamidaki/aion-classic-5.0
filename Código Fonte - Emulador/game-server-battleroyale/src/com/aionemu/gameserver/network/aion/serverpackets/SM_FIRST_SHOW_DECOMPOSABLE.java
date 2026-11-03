package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Janela de escolha de uma caixa selectable (S_DISASSEMBLY_ITEMLIST, 0x104 na 5.0). Layout das tres listas da subida 1-60 oficial
 * (caixas wrap_newc_supply_enchant_*): [D obj][D 0][D 1][D 0][C n] e, por opcao, [C indice][D item][D qtd][C 0][C 0][C 15][C 1].
 * O cliente responde com C_SELECT_DISASSEMBLY_ITEM trazendo o indice.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_FIRST_SHOW_DECOMPOSABLE extends AionServerPacket {

	public record Option(int itemId, int count) {}

	private final int objectId;
	private final int count;
	private final List<Option> options;

	public SM_FIRST_SHOW_DECOMPOSABLE(int objectId, List<Option> options) {
		this(objectId, 1, options);
	}

	public SM_FIRST_SHOW_DECOMPOSABLE(int objectId, int count, List<Option> options) {
		this.objectId = objectId;
		this.count = Math.max(1, count);
		this.options = options.size() > 255 ? options.subList(0, 255) : options;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeD(0);
		writeD(count);
		writeD(0);
		writeC(options.size());
		int index = 0;
		for (Option option : options) {
			writeC(index++);
			writeD(option.itemId());
			writeD(option.count());
			writeC(0);
			writeC(0);
			writeC(15);
			writeC(1);
		}
	}

}
