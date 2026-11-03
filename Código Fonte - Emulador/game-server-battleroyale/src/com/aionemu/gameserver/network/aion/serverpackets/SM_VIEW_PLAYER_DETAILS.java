package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.ArrayList;
import java.util.List;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;

/**
 * Itens equipados de outro jogador (S 0x40), em dois caminhos:
 * <ul>
 * <li>View Detail, C 0x6C [D objeto] (captura outros2 2026-09-22 09:41, 3 x S 0x40 com 11/12/7 itens): cabeçalho com C 0x0B (o mesmo com
 * alvos de classes diferentes, capturas de 22/09 e 20/10) e a lista inclui as pedras de estigma (140xxxxxx);</li>
 * <li>lupa do ranking, C 0x133 (06_Sistemas_Novos 2026-10-20 02:17 e 02:23, depois do S 0x02): C 0x10 e sem as pedras de estigma (20 itens).
 * O D do cabeçalho é o objeto sem o byte alto (0x2E13AFA9 vai como 0x0013AFA9); os ids do emulador já cabem em 24 bits.</li>
 * </ul>
 * Item [D 0][D template][blob completo], sem o nameId (como no inventário do 5.0), em pacotes de até 8192 b (7.891, 7.992 e 4.558 b no
 * oficial). O dono do item não é lido pelas entradas do blob, então serve também para jogador offline.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_VIEW_PLAYER_DETAILS extends AionServerPacket {

	public static final int SOURCE_VIEW_DETAIL = 0x0B;
	public static final int SOURCE_RANKING = 0x10;

	private static final int HEADER_SIZE = 4 + 1 + 2; // [D objeto][C origem][H itens]

	private final int objectId;
	private final int source;
	private final List<Item> items;

	private SM_VIEW_PLAYER_DETAILS(int objectId, int source, List<Item> items) {
		this.objectId = objectId;
		this.source = source;
		this.items = items;
	}

	/**
	 * View Detail (C 0x6C): equipamento com as pedras de estigma.
	 */
	public static List<SM_VIEW_PLAYER_DETAILS> of(Player target) {
		return of(target.getObjectId(), SOURCE_VIEW_DETAIL, target.getEquipment().getEquippedItems());
	}

	/**
	 * Os pacotes com os itens divididos como no oficial.
	 */
	public static List<SM_VIEW_PLAYER_DETAILS> of(int objectId, int source, List<Item> equippedItems) {
		List<SM_VIEW_PLAYER_DETAILS> packets = new ArrayList<>();
		List<Item> page = new ArrayList<>();
		int size = HEADER_SIZE;
		for (Item item : equippedItems) {
			int itemSize = 4 + 4 + 2 + ItemInfoBlob.getFullBlob(null, item).size();
			if (!page.isEmpty() && size + itemSize > MAX_USABLE_PACKET_BODY_SIZE) {
				packets.add(new SM_VIEW_PLAYER_DETAILS(objectId, source, page));
				page = new ArrayList<>();
				size = HEADER_SIZE;
			}
			page.add(item);
			size += itemSize;
		}
		packets.add(new SM_VIEW_PLAYER_DETAILS(objectId, source, page));
		return packets;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeC(source);
		writeH(items.size());
		for (Item item : items) {
			writeD(0);
			writeD(item.getItemTemplate().getTemplateId());
			ItemInfoBlob.getFullBlob(null, item).writeMe(getBuf());
		}
	}
}
