/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;

import java.util.Collections;
import java.util.List;

/**
 * @author kosyachok
 * @author -Nemesiss-
 */
public class S_ADD_WAREHOUSE extends AionServerPacket {

	private int warehouseType;
	private List<Item> items;
	private Player player;
	private ItemAddType addType;

	public S_ADD_WAREHOUSE(Item item, int warehouseType, Player player) {
		this.player = player;
		this.warehouseType = warehouseType;
		this.items = Collections.singletonList(item);
		this.addType = ItemAddType.ALL_SLOT;
	}

	public S_ADD_WAREHOUSE(Item item, int warehouseType, Player player, ItemAddType addType) {
        this(item, warehouseType, player);
        this.addType = addType;
    }

	@Override
    protected void writeImpl(AionConnection con) {
        writeC(warehouseType);
        // Cabecalho proprio, sem o C(1) do S_ADD_INVENTORY. Nao ha amostra deste pacote em
        // nenhuma captura, entao o C(1) entrou aqui por analogia e foi exatamente o byte que
        // derrubava o cliente ao guardar item: com ele o corpo ficava com 56 bytes contra os
        // 55 do S_ADD_INVENTORY equivalente, que o mesmo cliente aceita na retirada.
        // O S_LOAD_WAREHOUSE ja mostrava que os pacotes de warehouse tem cabecalho proprio.
        writeH(addType.getMask());
        writeH(0);
        writeC(0);
        writeH(items.size());
        for (Item item : items)
            writeItemInfo(item);
    }

	private void writeItemInfo(Item item) {
		ItemTemplate itemTemplate = item.getItemTemplate();
		
		writeD(item.getObjectId());
		writeD(itemTemplate.getTemplateId());
		// Sem writeC(0) e sem o bloco writeNameId: a 5.0 vai do templateId direto para o
		// ItemInfoBlob. Eram nove bytes a mais por item, e o cliente lia o 0x0024 do nameId
		// como tamanho do blob -- dai a quantidade errada e a janela fechando sozinha.
		// Mesmo defeito que o S_LOAD_INVENTORY ja tinha corrigido e que o S_ADD_INVENTORY
		// carregava ate a captura mostrar o layout certo.

		ItemInfoBlob itemInfoBlob = ItemInfoBlob.getFullBlob(player, item);
		itemInfoBlob.writeMe(getBuf());

		writeH((int) (item.getEquipmentSlot() & 0xFFFF));
		// Byte final do bloco de item. Faltava, e no S_LOAD_WAREHOUSE do login isso e um byte a
		// menos POR ITEM -- com dez itens o corpo desanda dez bytes e o cliente morre. Medido no
		// fio: o S_ADD_INVENTORY que funciona termina em "0f 00 ff ff 00" e este terminava em
		// "0f 00 ff ff".
		writeC(0);
	}
}
