package com.aionemu.gameserver.services.item;

import java.util.Collections;
import java.util.Objects;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class ItemPacketService {

	/**
	 * Motivo da atualização de item. No S_CHANGE_ITEM_DESC (0x1D) de blob completo, a 5.0 fecha com [D motivo][C 0].
	 * <p>
	 * Os tipos confirmados aparecem nas capturas oficiais no mesmo contexto; o número no comentário é quantos 0x1D trazem o motivo
	 * (278 com trailer, todas as capturas). Os outros herdaram a máscara da 4.8, sem prova na 5.0, e o trailer deles vai 0. Onde as
	 * duas pontas foram capturadas, o motivo repete o cabeçalho do S_ADD_INVENTORY da mesma ação (0x19, 0x50, 0x7A e 0x11C).
	 */
	public enum ItemUpdateType {
		EQUIP_UNEQUIP(-1, false, false), // internal usage only
		CHARGE(-2, false, false), // internal usage only
		POLISH_CHARGE(-3, false, false), // internal usage only

		STATS_CHANGE(0, true, true), // 44: equipamento depois de enchant, manastone, godstone, fusão e login
		INC_ITEM_MERGE(0x01, true, true), // 14: pilhas juntadas pelo C 0xB5
		INC_KINAH_MERGE(0x05, true, true), // 1: kinah do armazém para o cubo pelo C 0xB5
		DEC_ITEM_SPLIT(0x06, true, true), // 9: pilha dividida pelo C 0xB5, inclusive kinah do cubo para o armazém
		DEC_ITEM_USE(0x16, true, true), // 102: uso (C 0x2D), caixa aberta (C 0xA9), godstone encaixada
		DEC_STIGMA_USE(0, true, true), // 31: fragmento de estigma gasto ao equipar ou trocar de página (a 4.8 mandava 0x17)
		INC_ITEM_COLLECT(0x19, true, true), // 9: loot (C 0x6B)
		DEC_KINAH_BUY(0x1D, true, true), // 3: compra na loja (C 0x33)
		INC_KINAH_SELL(0x20, true, true), // 1: venda na loja (C 0x33)
		DEC_ITEM_BUY(0x44, true, true), // 2: moeda-item paga na compra (C 0x33, ações 14 e 15)
		DEC_KINAH_MANASTONE_CLEAR(0x4A, true, true), // 2: remoção de manastone pelo menu (C 0x5A tipo 3), 20.000 por pedra
		DEC_KINAH_FLY(0x4B, true, true), // 15: teleporte (C 0xFFFD ou 0x5C)
		INC_ITEM_DECOMPOSE(0x50, true, true), // 1: recompensa de caixa somada a uma pilha
		DEC_KINAH_CUBE(0x5A, true, true), // 2: expansão do cubo
		INC_NPSHOP_GOODS(0x7A, true, true), // 1: resgate do Black Cloud Mail (C 0x9E)
		DEC_KINAH_SOUL_HEALER(0xE6, true, true), // 10: cura de alma (C 0x32 da pergunta 909382)
		DEC_SIEL_ANVIL_MATERIAL(0x115, true, true), // 1: material gasto no Siel Anvil (C 0x108)
		DEC_KINAH_ENCHANT(0x118, true, true), // 2: taxa do enchant (C 0x5A tipo 1) e do Siel Anvil
		DEC_KINAH_GODSTONE_CLEAR(0x11A, true, true), // 1: remoção de godstone pelo menu (C 0x10B)
		INC_MANASTONE_CLEAR(0x11C, true, true), // 4: manastone devolvida pela remoção (C 0x5A tipo 3)
		DEC_KINAH_GLOBAL_TRADE_FEE(0x9C, true, true), // 2: taxa de registro na Auction House (C 0x117)
		DEC_KINAH_GLOBAL_TRADE_BUY(0x13C, true, true), // 2: compra na Auction House (C 0x116)
		INC_KINAH_GLOBAL_TRADE_COLLECT(0x13D, true, true), // 1: receita recebida da Auction House (C 0x102)
		DEC_ITEM_COMPOSE_MATERIAL(0x11D, true, true), // 1: material gasto no Altar of Transcendence (C 0x154), também no 0x1C
		DEC_KINAH_ITEM_COMPOSE(0x120, true, true), // 2: taxa do Altar of Transcendence (C 0x154)

		DEC_KINAH(0, true, false), // gasto de kinah sem motivo capturado; o oficial usa um por serviço, e 0x1D só na compra
		DEC_ITEM_SPLIT_MOVE(0x0A, true, false), // move to other storage with split
		PUT(0x13, true, false), // from other storage
		DEC_ITEM_CRUSH(0x110, true, false), // motivo do S_REMOVE_INVENTORY do hammer; 0x1D do hammer não foi capturado
		INC_KINAH_COLLECT(0x1A, true, false),
		INC_ITEM_BUY(0x1C, true, false), // buying from npc
		INC_PLAYER_EXCHANGE_GET_BACK(0x23, true, false),
		PUT_TO_EXCHANGE(0x25, true, false),
		INC_KINAH_QUEST(0x32, true, false),
		DEC_KINAH_LEARN(0x49, true, false), // craft skill learn
		INC_CASH_ITEM(0x50, true, false), // event items, for exchange
		INC_ITEM_REPURCHASE(0x51, true, false),
		DEC_PET_FOOD(0x5E, true, false),
		INC_PASSPORT_ADD(0x8A, true, false),
		INC_COMBAT_TALENT_REWARD(0xEB, true, false), // cabeçalho do S_ADD_INVENTORY da recompensa; 0x1D não capturado
		INC_CRUSH_RESULT(0x112, true, false), // cabeçalho do S_ADD_INVENTORY do hammer; 0x1D não capturado
		INC_ITEM_COMPOSE(0x11E, true, false); // cabeçalho do S_ADD_INVENTORY do Altar; resultado somado a pilha (0x1D) não capturado

		private final int mask;
		private final boolean sendable;
		private final boolean confirmed;

		ItemUpdateType(int mask, boolean sendable, boolean confirmed) {
			this.mask = mask;
			this.sendable = sendable;
			this.confirmed = confirmed;
		}

		public int getMask() {
			return mask;
		}

		public boolean isSendable() {
			return sendable;
		}

		/**
		 * Motivo do trailer [D motivo][C 0] do S_CHANGE_ITEM_DESC: a máscara, se confirmada em captura 5.0; senão 0.
		 */
		public int getReason() {
			return confirmed ? mask : 0;
		}

		public static ItemUpdateType getKinahUpdateTypeFromAddType(ItemAddType itemAddType, boolean isIncrease) {
			if (!isIncrease)
				return ItemUpdateType.DEC_KINAH_BUY;
			return switch (itemAddType) {
				case BUY -> ItemUpdateType.INC_KINAH_SELL;
				case ITEM_COLLECT -> ItemUpdateType.INC_KINAH_COLLECT;
				case QUEST_WORK_ITEM -> ItemUpdateType.INC_KINAH_QUEST;
				default -> ItemUpdateType.INC_KINAH_MERGE;
			};
		}
	}

	public static enum ItemAddType {
		SERVER_GENERATED(0x00), // Banquest Table, Extract Enchanment stones, Remodel, Armfusion
		CRUSH_RESULT(0x112), // official S_ADD_INVENTORY Hammer reward header
		PARTIAL_WITH_SLOT(0x07), // partial content of slot
		ALL_SLOT(0x13), // All warehouses/pets
		ITEM_COLLECT(0x19), // Drop, Gather
		BUY(0x1C),
		PLAYER_EXCHANGE_GET(0x21),
		PLAYER_EXCHANGE_GET_BACK(0x23),
		PLAYER_STORE(0x2B),
		CRAFTED_ITEM(0x2D),
		BROKER_BUY(0x2E),
		BROKER_RETURN(0x2F),
		QUEST_REWARD_ITEM(0x30),
		QUEST_WORK_ITEM(0x35),
		QUEST_WORK_ITEM2(0x36),
		MAIL(0x36),
		SURVEY(0x40),
		DECOMPOSABLE(0x50), // also Guestbloom
		COMBAT_TALENT_REWARD(0xEB), // official Combat Talent milestone reward
		NPSHOP_GOODS(0x7A), // Black Cloud Mail: cabeçalho [D 0x7A][C 0][C 1] do S_ADD_INVENTORY (captura oficial, 3 de 3)
		GLOBAL_TRADE_BUY(0x98), // Auction House: item comprado (C 0x116), cabeçalho [D 0x98][C 0][C 1] nas capturas (3 de 3)
		GLOBAL_TRADE_CANCEL(0x9E), // Auction House: item de volta pelo cancelamento (C 0x100), cabeçalho [D 0x9E][C 0][C 1] (2 de 2)
		ITEM_COMPOSE(0x11E), // Altar of Transcendence: resultado da fusão (C 0x154), cabeçalho [D 0x11E][C 0][C 1] (2 de 2)
		REPURCHASE(0x51);

		private final int mask;

		ItemAddType(int mask) {
			this.mask = mask;
		}

		public int getMask() {
			return mask;
		}
	}

	public enum ItemDeleteType {
		DEFAULT(0),
		SPLIT(0x04),
		MOVE(0x14),
		DISCARD(0x15),
		USE(0x17),
		SELL(0x1F),
		QUEST_COMPLETE(0x31),
		QUEST_START(0x34),
		DECOMPOSE(0x66),
		CRUSH(0x110),
		GLOBAL_TRADE_REGISTER(0x0C), // S_REMOVE_INVENTORY do item anunciado na Auction House (C 0x117)
		ITEM_COMPOSE(0x11D), // S_REMOVE_INVENTORY do material do Altar (C 0x154), mesmo motivo do 0x1D
		REGISTER(0x78),
		PUT_TO_EXCHANGE(0x26);

		private final int mask;

		ItemDeleteType(int mask) {
			this.mask = mask;
		}

		public int getMask() {
			return mask;
		}

		public static ItemDeleteType fromUpdateType(ItemUpdateType updateType) {
			return switch (updateType) {
				case DEC_ITEM_SPLIT -> SPLIT;
				case DEC_ITEM_USE, DEC_ITEM_BUY, DEC_SIEL_ANVIL_MATERIAL -> USE;
				case DEC_ITEM_CRUSH -> CRUSH;
				case DEC_ITEM_COMPOSE_MATERIAL -> ITEM_COMPOSE;
				case DEC_ITEM_SPLIT_MOVE -> MOVE;
				default -> DEFAULT;
			};
		}

		public static ItemDeleteType fromQuestStatus(QuestStatus questStatus) {
			return switch (questStatus) {
				case START -> QUEST_START;
				case COMPLETE -> QUEST_COMPLETE;
				default -> DEFAULT;
			};
		}
	}

	public static void updateItemAfterInfoChange(Player player, Item item) {
		PacketSendUtility.sendPacket(player, new SM_INVENTORY_UPDATE_ITEM(player, item));
	}

	public static void updateItemAfterInfoChange(Player player, Item item, ItemUpdateType updateType) {
		PacketSendUtility.sendPacket(player, new SM_INVENTORY_UPDATE_ITEM(player, item, updateType));
	}

	public static void updateItemAfterEquip(Player player, Item item) {
		PacketSendUtility.sendPacket(player, new SM_INVENTORY_UPDATE_ITEM(player, item, ItemUpdateType.EQUIP_UNEQUIP));
	}

	public static void sendItemPacket(Player player, StorageType storageType, Item item, ItemUpdateType updateType) {
		if (item.getItemCount() <= 0 && !item.getItemTemplate().isKinah()) {
			sendItemDeletePacket(player, storageType, item, ItemDeleteType.fromUpdateType(updateType));
		} else {
			sendItemUpdatePacket(player, storageType, item, updateType);
		}
	}

	/**
	 * Item will be deleted from UI slot
	 */
	public static void sendItemDeletePacket(Player player, StorageType storageType, Item item, ItemDeleteType deleteType) {
		if (Objects.requireNonNull(storageType) == StorageType.CUBE) {
			PacketSendUtility.sendPacket(player, new SM_DELETE_ITEM(item.getObjectId(), deleteType));
		} else {
			PacketSendUtility.sendPacket(player, new SM_DELETE_WAREHOUSE_ITEM(storageType.getId(), item.getObjectId(), deleteType));
		}
		// Hammer refreshes the cube after the result and rewards, as in the official capture.
		// Refreshing while its selected input disappears makes the client treat the dialog as interrupted.
		if (deleteType != ItemDeleteType.CRUSH)
			PacketSendUtility.sendPacket(player, SM_CUBE_UPDATE.cubeSize(storageType, player));
	}

	/**
	 * Item will be updated in UI slot (stacked items)
	 */
	@SuppressWarnings("fallthrough")
	public static void sendItemUpdatePacket(Player player, StorageType storageType, Item item, ItemUpdateType updateType) {
		switch (storageType) {
			case CUBE:
				PacketSendUtility.sendPacket(player, new SM_INVENTORY_UPDATE_ITEM(player, item, updateType));
				break;
			case LEGION_WAREHOUSE:
				if (item.getItemTemplate().isKinah()) {
					PacketSendUtility.sendPacket(player, new SM_LEGION_EDIT(0x04, player.getLegion()));
					break;
				}
			default:
				PacketSendUtility.sendPacket(player, new SM_WAREHOUSE_UPDATE_ITEM(player, item, storageType.getId(), updateType));
		}
	}

	public static void sendStorageUpdatePacket(Player player, StorageType storageType, Item item) {
		sendStorageUpdatePacket(player, storageType, item, ItemAddType.ITEM_COLLECT);
	}

	/**
	 * New item will be displayed in storage
	 */
	@SuppressWarnings("fallthrough")
	public static void sendStorageUpdatePacket(Player player, StorageType storageType, Item item, ItemAddType addType) {
		switch (storageType) {
			case CUBE:
				PacketSendUtility.sendPacket(player, new SM_INVENTORY_ADD_ITEM(Collections.singletonList(item), player, addType));
				break;
			case LEGION_WAREHOUSE:
				if (item.getItemTemplate().isKinah()) {
					PacketSendUtility.sendPacket(player, new SM_LEGION_EDIT(0x04, player.getLegion()));
					break;
				}
			default:
				PacketSendUtility.sendPacket(player, new SM_WAREHOUSE_ADD_ITEM(item, storageType.getId(), player, addType));
		}
		if (addType != ItemAddType.CRUSH_RESULT)
			PacketSendUtility.sendPacket(player, SM_CUBE_UPDATE.cubeSize(storageType, player));
	}

	public static void sendItemUnlockPacket(Player player, Item item) {
		StorageType storageType = StorageType.getStorageTypeById(item.getItemLocation());
		if (storageType != null)
			sendStorageUpdatePacket(player, storageType, item, ItemAddType.ALL_SLOT);
	}
}
