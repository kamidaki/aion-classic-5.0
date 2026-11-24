package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x173 (4 b): nível da sinergia de encantamento ("Current Synergy Level"), [D soma dos encantamentos dos itens equipados com
 * accumulated_enchant_effect]. Sem ele o cliente mostra N/A. Nas capturas oficiais (508 pacotes), o valor muda pelo encantamento do item a
 * cada equipar/desequipar (+8/-8, -10, troca 35 -> 43) e sobe item a item no login. Antes se chamava SM_EQUIP_SLOT_UPDATE e nunca era
 * enviado.
 */
public class SM_ENCHANT_SYNERGY extends AionServerPacket {

	private final int enchantSum;

	public SM_ENCHANT_SYNERGY(int enchantSum) {
		this.enchantSum = enchantSum;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(enchantSum);
	}
}
