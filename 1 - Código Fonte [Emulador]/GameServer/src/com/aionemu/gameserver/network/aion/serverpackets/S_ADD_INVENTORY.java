package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.ItemStorage;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;

import java.util.List;

public class S_ADD_INVENTORY extends AionServerPacket
{
	private final List<Item> items;
	private final int size;
	private Player player;
	private ItemAddType addType;
	
	public S_ADD_INVENTORY(List<Item> items, Player player) {
		this.player = player;
		this.items = items;
		this.size = items.size();
		this.addType = ItemAddType.ITEM_COLLECT;
	}
	
	public S_ADD_INVENTORY(List<Item> items, Player player, ItemAddType addType) {
        this(items, player);
        this.addType = addType;
    }
	
	@Override
    protected void writeImpl(AionConnection con) {
		// TODO: Rework it, who knows where it could be bugged else.
		int mask = addType.getMask();
		if (addType == ItemAddType.ITEM_COLLECT) {
			// TODO: if size != 1, then it's buy item, should not specify any slot in other places then !!!
			if (size == 1 && items.get(0).getEquipmentSlot() != ItemStorage.FIRST_AVAILABLE_SLOT)
				mask = ItemAddType.PARTIAL_WITH_SLOT.getMask();
		}
		// Cabecalho de 8 bytes, medido nas nove amostras de S_ADD_INVENTORY da captura oficial
		// (subida-1-60, sessao 1): H(mascara) H(0) C(0) C(1) H(quantidade). Faltava o C(1), e o byte
		// a menos deslocava tudo o que vinha depois -- era o que derrubava o cliente ao pegar item
		// de loot e ao receber recompensa de quest.
		// Nas nove amostras a quantidade e sempre 1, entao elas nao separam "constante 1" de "copia
		// da quantidade". Se um dia um pacote com varios itens sair torto, e o primeiro palpite.
		writeH(mask);
		writeH(0);
		writeC(0);
		writeC(1);
		writeH(size); // number of entries
		for (Item item : items)
			writeItemInfo(item);
    }
	
	private void writeItemInfo(Item item) {
		ItemTemplate itemTemplate = item.getItemTemplate();
		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());
		// Sem bloco de nameId aqui: na captura o corpo vai direto do templateId para o ItemInfoBlob.
		// O writeNameId punha H(0x24) D(nameId) H(0) no meio, oito bytes que o cliente 5.0 nao le.
		ItemInfoBlob itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
		itemInfoBlob.writeMe(getBuf());

		writeH(item.isEquipped() ? 255 : item.getEquipmentSlot()); // FF FF equipment
		writeC(0x00);//isEquiped?
	}
}