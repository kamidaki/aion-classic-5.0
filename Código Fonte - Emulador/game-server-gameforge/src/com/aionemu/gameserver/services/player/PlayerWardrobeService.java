package com.aionemu.gameserver.services.player;

import java.util.Map;
import java.util.Objects;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.PlayerAppearanceDAO;
import com.aionemu.gameserver.dao.PlayerHairstyleDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dao.PlayerWardrobeDAO;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.Gender;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.model.templates.cosmeticitems.CosmeticItemTemplate;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.actions.DyeAction;
import com.aionemu.gameserver.model.templates.item.actions.AbstractItemAction;
import com.aionemu.gameserver.model.templates.item.actions.CosmeticItemAction;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UPDATE_PLAYER_APPEARANCE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_WARDROBE_DATA_UPDATED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_HAIRSTYLE_LOAD;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_HAIRSTYLE_SLOTS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_WARDROBE_INFO_UPDATED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_WARDROBE_LOAD;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.trade.PricesService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.idfactory.IDFactory;

/**
 * Wardrobe do Classic 5.0: o jogador registra itens (que somem do cubo e viram entradas), tinge e favorita as entradas, e aplica o visual de uma
 * entrada em qualquer item compatível, pagando kinah. Capturas 06_Sistemas_Novos_5.0 de 2026-09-21 14:56 (aplicar, remover visual, tingir,
 * favoritar) e 15:16 (registrar e apagar); 58 logins com o 0x122.
 * <p>
 * Valores do client_wardrobe_config 5.0. A cobrança passa pelo {@link PricesService}: o oficial cobrou 13.167 e 1.316 kinah pelos 10.000 e 1.000
 * da tabela.
 * <p>
 * A expansão de slot não tem captura oficial; opcode, corpo e resposta foram conferidos no cliente real (ver CM_USER_CLASSIC_WARDROBE_EXTEND e
 * SM_USER_CLASSIC_WARDROBE_INFO_UPDATED). A aba de cabelo (C 0xEB, S 0x177, 20 Quna) fica de fora.
 */
public class PlayerWardrobeService {

	private static final Logger log = LoggerFactory.getLogger(PlayerWardrobeService.class);

	/** change_skin_cost */
	public static final int CHANGE_SKIN_COST = 10000;
	/** remove_skin_cost */
	public static final int REMOVE_SKIN_COST = 1000;
	/** free_slot_num */
	public static final int FREE_SLOTS = 1;
	/** STR_UI_WARDROBE_EXTEND_MESSAGE_DEFAULT: um slot por vez, até 100. */
	public static final int MAX_SLOTS = 100;
	/** extend_quna */
	public static final int EXTEND_QUNA = 600;
	/** extend_item cash_extend_closet_01, extend_item_num 1 */
	public static final int EXTEND_ITEM_ID = 186000166;
	/** Forma de pagamento da expansão paga em Quna; o 2 é o item (nota da fonte 2.4: "use key in official = 01 00 02"). */
	public static final int PAYMENT_QUNA = 1;
	/** hairstyle_free_slot_num */
	public static final int HAIRSTYLE_FREE_SLOTS = 1;
	/** STR_UI_WARDROBE_EXTEND_MESSAGE_DEFAULT_HAIR: um slot por vez, até 100. */
	public static final int HAIRSTYLE_MAX_SLOTS = 100;
	/** hairstyle_extend_quna; o item (hairstyle_extend_item) é o mesmo cash_extend_closet_01, 1 por slot */
	public static final int HAIRSTYLE_EXTEND_QUNA = 600;

	// client_strings_msg 5.0
	private static final int MSG_CHANGE_SKIN_NO_TARGET_ITEM = 1300477; // STR_CHANGE_ITEM_SKIN_NO_TARGET_ITEM
	private static final int MSG_CHANGE_SKIN_NOT_CHANGABLE = 1300478; // STR_CHANGE_ITEM_SKIN_NOT_SKIN_CHANGABLE_ITEM
	private static final int MSG_CHANGE_SKIN_SUCCEED = 1300483; // STR_CHANGE_ITEM_SKIN_SUCCEED, capturada nas 3 aplicações
	private static final int MSG_UNCHANGE_SKIN_SUCCEED = 1400372; // STR_UNCHANGE_ITEM_SKIN_SUCCEED, capturada nas 2 remoções
	private static final int MSG_REGISTERED = 1401541; // STR_MSG_WARDROBE_COMPLETE_REGISTER_ITEM
	private static final int MSG_DELETED = 1401542; // STR_MSG_WARDROBE_DELETE_ITEM
	private static final int MSG_FAVORITE = 1401543; // STR_MSG_WARDROBE_FAVORITE_ITEM
	private static final int MSG_REGISTER_LACK_SLOT = 1401544; // STR_MSG_WARDROBE_CANNOT_REGISTER_LACK_SLOT
	private static final int MSG_REGISTER_CHANGED_SKIN = 1401545; // STR_MSG_WARDROBE_CANNOT_REGISTER_CHANGE_SKIN
	private static final int MSG_REGISTER_EXPIRE_ITEM = 1401546; // STR_MSG_WARDROBE_CANNOT_REGISTER_EXPIRE_ITEM
	private static final int MSG_REGISTER_CANNOT = 1401547; // STR_MSG_WARDROBE_CANNOT_REGISTER
	private static final int MSG_REGISTER_GENDER_RACE = 1401548; // STR_MSG_WARDROBE_CANNOT_REGISTER_DIF_GENDER_RACE
	private static final int MSG_REGISTER_EXPIRE_DYE = 1401549; // STR_MSG_WARDROBE_CANNOT_REGISTER_EXPIRE_DYED_ITEM
	private static final int MSG_REGISTER_EQUIPPED = 1401550; // STR_MSG_WARDROBE_CANNOT_REGISTER_EQUIPPED_ITEM
	private static final int MSG_EXPANDED = 1401551; // STR_MSG_WARDROBE_COMPLETE_EXPAND_SLOT
	private static final int MSG_EXPAND_MAX = 1401552; // STR_MSG_WARDROBE_CANNOT_EXPAND_MAX_SLOT
	private static final int MSG_EXPAND_NO_QUNA = 1401553; // STR_MSG_WARDROBE_CANNOT_EXPAND_NOT_ENOUGH_QUNA
	private static final int MSG_EXPAND_NO_ITEM = 1401554; // STR_MSG_WARDROBE_CANNOT_EXPAND_NOT_ENOUGH_ITEM
	private static final int MSG_HAIR_EXPANDED = 1403368; // STR_MSG_WARDROBE_COMPLETE_EXPAND_SLOT_HAIR
	private static final int MSG_HAIR_EXPAND_MAX = 1403369; // STR_MSG_WARDROBE_CANNOT_EXPAND_MAX_SLOT_HAIR
	private static final int MSG_HAIR_REGISTERED = 1403363; // STR_MSG_WARDROBE_COMPLETE_REGISTER_HAIR (%0 item)
	private static final int MSG_HAIR_DELETED = 1403364; // STR_MSG_WARDROBE_DELETE_ITEM_HAIR (%0 item)
	private static final int MSG_HAIR_LACK_SLOT = 1403367; // STR_MSG_WARDROBE_CANNOT_REGISTER_LACK_SLOT_HAIR
	private static final int MSG_HAIR_GENDER_RACE = 1403370; // STR_MSG_WARDROBE_CANNOT_REGISTER_DIF_GENDER_RACE_HAIR
	private static final int MSG_HAIR_CHANGE_GENDER = 1403371; // STR_MSG_WARDROBE_UI_CANNOT_USE_GENDER_RESTRICT_HAIR
	private static final int MSG_HAIR_CHANGE_SAME = 1403437; // STR_MSG_WARDROBE_CANNOT_CHANGE_HAIR_SAME_CONDITION
	/** change_hairstyle_quna */
	public static final int CHANGE_HAIRSTYLE_QUNA = 20;
	/** H do S 0x11B na troca de penteado (captura de 2026-09-21, 1 de 1). */
	private static final int QUNA_CODE_CHANGE_HAIR = 0x149;
	private static final int MSG_CHANGE_SAME = 1401555; // STR_MSG_WARDROBE_CANNOT_CHANGE_SKIN_SAME_CONDITION
	private static final int MSG_CHANGE_NO_KINAH = 1401556; // STR_MSG_WARDROBE_CANNOT_CHANGE_SKIN_NOT_ENOUGH_QINA
	private static final int MSG_REMOVE_NO_SKIN = 1401559; // STR_MSG_WARDROBE_CANNOT_REMOVE_NOT_CHANGED_SKIN
	private static final int MSG_REMOVE_NOT_WARDROBE = 1401560; // STR_MSG_WARDROBE_CANNOT_REMOVE_NOT_WARDROBE_SKIN
	private static final int MSG_DYE_NOT_DYEABLE = 1401563; // STR_MSG_WARDROBE_CANNOT_DYE_NOT_DYE_ITEM
	private static final int MSG_DYE_NOT_FOUND = 1401564; // STR_MSG_WARDROBE_CANNOT_DYE_NOT_IN_INVENTORY
	private static final int MSG_DYED = 1401565; // STR_MSG_WARDROBE_COMPLETE_DYE
	private static final int MSG_DYE_REMOVED = 1401566; // STR_MSG_WARDROBE_COMPLETE_REMOVE_DYE
	private static final int MSG_DYE_TEMPORARY = 1401567; // STR_MSG_WARDROBE_CANNOT_DYE_EXPIRE_DYEING_ITEM
	private static final int MSG_CHANGE_OTHER_TYPE = 1401573; // STR_MSG_WARDROBE_CHANGE_SKIN_NOT_ALLOW_CHANGE_FILTER
	private static final int MSG_REMOVE_NO_KINAH = 1401578; // STR_MSG_WARDROBE_CANNOT_REMOVE_SKIN_NOT_ENOUGH_GOLD
	private static final int MSG_CHANGE_GENDER = 1401579; // STR_MSG_WARDROBE_UI_CANNOT_USE_GENDER_RESTRICT_ITEM
	private static final int MSG_REGISTER_PACKED = 1403687; // STR_MSG_WARDROBE_CANNOT_REGISTER_PACK_ITEM

	/**
	 * Carrega as entradas ao montar o personagem. Se a leitura falhar, o guarda-roupa fica fora nesta sessão.
	 */
	public void onLoad(Player player) {
		try {
			player.setPlayerWardrobe(PlayerWardrobeDAO.load(player.getObjectId()));
		} catch (Exception e) {
			player.setPlayerWardrobe(null);
			log.error("Wardrobe: não foi possível carregar {}; o guarda-roupa fica fora nesta sessão", player.getName(), e);
		}
		try {
			player.setPlayerHairstyles(PlayerHairstyleDAO.load(player.getObjectId()));
		} catch (Exception e) {
			player.setPlayerHairstyles(null);
			log.error("Wardrobe: não foi possível carregar a lista de cabelo de {}; ela fica fora nesta sessão", player.getName(), e);
		}
	}

	/**
	 * S 0x177 do login: a lista de cabelo e os slots.
	 */
	public void onEnterWorldHairstyle(Player player) {
		synchronized (player) {
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_HAIRSTYLE_LOAD(player.getObjectId(),
				player.getPlayerHairstyles() == null ? null : player.getPlayerHairstyles().values(), HAIRSTYLE_FREE_SLOTS,
				getExtendedHairstyleSlots(player)));
		}
	}

	/**
	 * Penteado de um item pelo cosmético dele (item_template &lt;actions&gt;&lt;cosmetic&gt; + cosmetic_items type hair_type, ligados pelo
	 * fix_50_hair_cosmetic.py a partir do client_items e do client_cosmetic_item_info), ou null se o item não é de penteado.
	 */
	static CosmeticItemTemplate hairstyleOf(ItemTemplate template) {
		if (template == null || template.getActions() == null)
			return null;
		for (AbstractItemAction action : template.getActions().getItemActions()) {
			if (action instanceof CosmeticItemAction cosmetic) {
				CosmeticItemTemplate hair = DataManager.COSMETIC_ITEMS_DATA.getCosmeticItemsTemplate(cosmetic.getCosmeticName());
				return hair != null && "hair_type".equals(hair.getType()) ? hair : null;
			}
		}
		return null;
	}

	private static boolean isHairstyleUsableBy(Player player, CosmeticItemTemplate hair) {
		return hair.getRace() == player.getRace()
			&& ("ALL".equals(hair.getGenderPermitted()) || player.getGender().toString().equals(hair.getGenderPermitted()));
	}

	/**
	 * C 0xDE: o item de penteado sai do inventário (S 0x1C, motivo do registro do guarda-roupa), vira um registro novo da lista e o cliente recebe
	 * o S 0x178 ação 1 e a msg 1403363. Sem captura: a mesma ordem do registro do guarda-roupa (C 0xEE).
	 */
	public void registerHairstyle(Player player, int itemObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> hairstyles = player.getPlayerHairstyles();
			if (hairstyles == null || isBusy(player))
				return;
			Item item = player.getInventory().getItemByObjId(itemObjId);
			CosmeticItemTemplate hair = item == null ? null : hairstyleOf(item.getItemTemplate());
			int message = 0;
			if (hair == null)
				message = MSG_REGISTER_CANNOT;
			else if (!isHairstyleUsableBy(player, hair))
				message = MSG_HAIR_GENDER_RACE;
			else if (hairstyles.size() >= getHairstyleSlots(player))
				message = MSG_HAIR_LACK_SLOT;
			if (message != 0) {
				log.info("Wardrobe: registro de penteado recusado: player={}, item={}, mensagem={}", player.getName(), itemObjId, message);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
				return;
			}
			ItemTemplate template = item.getItemTemplate();
			if (!player.getInventory().decreaseByObjectId(itemObjId, 1, ItemUpdateType.DEC_WARDROBE_REGISTER))
				return;
			WardrobeEntry entry = new WardrobeEntry(IDFactory.getInstance().nextId(), template.getTemplateId(), null, false);
			hairstyles.put(entry.getObjectId(), entry);
			PlayerHairstyleDAO.add(player.getObjectId(), entry);
			InventoryDAO.store(player);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_HAIR_REGISTERED, name(template)));
			PacketSendUtility.sendPacket(player,
				new SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED(SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED.REGISTERED, player.getObjectId(), entry));
			log.info("Wardrobe: {} registrou o penteado {} (tipo {}, objeto {}) como {}", player.getName(), template.getTemplateId(), hair.getId(),
				itemObjId, entry.getObjectId());
		}
	}

	/**
	 * C 0xDF: tira o penteado da lista (S 0x178 ação 2 e msg 1403364). O cabelo atual do personagem fica.
	 */
	public void deleteHairstyle(Player player, int entryObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> hairstyles = player.getPlayerHairstyles();
			WardrobeEntry entry = hairstyles == null ? null : hairstyles.get(entryObjId);
			if (entry == null || !PlayerHairstyleDAO.delete(entry))
				return;
			hairstyles.remove(entryObjId);
			IDFactory.getInstance().releaseId(entryObjId);
			PacketSendUtility.sendPacket(player,
				new SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED(SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED.DELETED, player.getObjectId(), entry));
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_HAIR_DELETED, name(entry)));
			log.info("Wardrobe: {} apagou o penteado {} ({})", player.getName(), entryObjId, entry.getItemId());
		}
	}

	/**
	 * C 0xEB: aplica o penteado da lista por 20 Quna. Captura de 2026-09-21: S 0x11B (H 0x149, saldo) e msg 1401574 com os Quna, depois a
	 * atualização do personagem. O penteado continua na lista.
	 */
	public void changeHairstyle(Player player, int entryObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> hairstyles = player.getPlayerHairstyles();
			WardrobeEntry entry = hairstyles == null ? null : hairstyles.get(entryObjId);
			if (entry == null || isBusy(player))
				return;
			CosmeticItemTemplate hair = hairstyleOf(DataManager.ITEM_DATA.getItemTemplate(entry.getItemId()));
			if (hair == null)
				return;
			if (!isHairstyleUsableBy(player, hair)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_HAIR_CHANGE_GENDER));
				return;
			}
			if (player.getPlayerAppearance().getHair() == hair.getId()) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_HAIR_CHANGE_SAME));
				return;
			}
			if (!QunaService.spend(player, CHANGE_HAIRSTYLE_QUNA, QUNA_CODE_CHANGE_HAIR)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_EXPAND_NO_QUNA));
				return;
			}
			player.getPlayerAppearance().setHair(hair.getId());
			PlayerAppearanceDAO.store(player);
			player.getController().refreshOwnAppearance();
			log.info("Wardrobe: {} trocou o penteado para {} (entrada {})", player.getName(), hair.getId(), entryObjId);
		}
	}

	public static int getHairstyleSlots(Player player) {
		return Math.max(HAIRSTYLE_FREE_SLOTS, player.getCommonData().getHairstyleSlot());
	}

	static int getExtendedHairstyleSlots(Player player) {
		return getHairstyleSlots(player) - HAIRSTYLE_FREE_SLOTS;
	}

	/**
	 * C 0xEA: 1 slot da lista de cabelo, pago com 600 Quna (S 0x11B e msg 1401574) ou com 1 cash_extend_closet_01. Responde o S 0x179 com
	 * os slots e a msg 1403368 (sem captura: a mesma ordem da expansão do guarda-roupa).
	 */
	public void extendHairstyleSlots(Player player, int payment) {
		synchronized (player) {
			if (isBusy(player))
				return;
			int slots = getHairstyleSlots(player);
			int message = slots >= HAIRSTYLE_MAX_SLOTS ? MSG_HAIR_EXPAND_MAX : 0;
			if (message == 0 && payment == PAYMENT_QUNA && !QunaService.spend(player, HAIRSTYLE_EXTEND_QUNA, QunaService.CODE_NONE))
				message = MSG_EXPAND_NO_QUNA;
			else if (message == 0 && payment != PAYMENT_QUNA && !player.getInventory().decreaseByItemId(EXTEND_ITEM_ID, 1))
				message = MSG_EXPAND_NO_ITEM;
			if (message != 0) {
				log.info("Wardrobe: expansão de cabelo recusada: player={}, slots={}, pagamento={}, mensagem={}", player.getName(), slots, payment,
					message);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
				return;
			}
			player.getCommonData().setHairstyleSlot(slots + 1);
			PlayerWardrobeDAO.storeHairstyleSize(player.getObjectId(), slots + 1);
			InventoryDAO.store(player);
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_HAIRSTYLE_SLOTS(HAIRSTYLE_FREE_SLOTS, getExtendedHairstyleSlots(player)));
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_HAIR_EXPANDED));
			log.info("Wardrobe: {} expandiu a lista de cabelo para {} slots", player.getName(), slots + 1);
		}
	}

	/**
	 * S 0x122 do login, entre o 0x117 e o 0x138.
	 */
	public void onEnterWorld(Player player) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			if (wardrobe != null)
				PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_LOAD(getExtendedSlots(player), wardrobe.values()));
		}
	}

	public static int getSlots(Player player) {
		return Math.max(FREE_SLOTS, player.getCommonData().getWardrobeSlot());
	}

	static int getExtendedSlots(Player player) {
		return getSlots(player) - FREE_SLOTS;
	}

	/**
	 * C 0xEE. Oficial: S 0x1C do item (motivo 0x81), msg 1401541 com o nome do item e S 0x124 ação 1 com um objeto novo.
	 */
	public void registerItem(Player player, int itemObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			if (wardrobe == null || isBusy(player))
				return;
			Item item = player.getInventory().getItemByObjId(itemObjId);
			int message = checkRegister(player, wardrobe, itemObjId, item);
			if (message != 0) {
				log.info("Wardrobe: registro recusado: player={}, item={}, mensagem={}", player.getName(), itemObjId, message);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
				return;
			}
			ItemTemplate template = item.getItemTemplate();
			Integer color = item.getItemColor();
			if (!player.getInventory().decreaseByObjectId(itemObjId, 1, ItemUpdateType.DEC_WARDROBE_REGISTER))
				return;
			WardrobeEntry entry = new WardrobeEntry(IDFactory.getInstance().nextId(), template.getTemplateId(), color, false);
			wardrobe.put(entry.getObjectId(), entry);
			PlayerWardrobeDAO.addItem(player.getObjectId(), entry);
			InventoryDAO.store(player);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REGISTERED, name(template)));
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(SM_USER_CLASSIC_WARDROBE_DATA_UPDATED.REGISTERED, entry));
			log.info("Wardrobe: {} registrou {} (objeto {}) como {}", player.getName(), template.getTemplateId(), itemObjId, entry.getObjectId());
		}
	}

	/**
	 * @return 0 se o item pode ser registrado, ou a mensagem de recusa
	 */
	private static int checkRegister(Player player, Map<Integer, WardrobeEntry> wardrobe, int itemObjId, Item item) {
		if (item == null)
			return player.getEquipment().getEquippedItemByObjId(itemObjId) != null ? MSG_REGISTER_EQUIPPED : MSG_REGISTER_CANNOT;
		ItemTemplate template = item.getItemTemplate();
		if (template.getItemSlot() == 0 || !template.isArmor() && !template.isWeapon() || !item.isRemodelable())
			return MSG_REGISTER_CANNOT;
		if (item.getPackCount() > 0)
			return MSG_REGISTER_PACKED;
		if (item.getExpireTime() > 0)
			return MSG_REGISTER_EXPIRE_ITEM;
		if (item.getColorExpireTime() > 0)
			return MSG_REGISTER_EXPIRE_DYE;
		if (item.isSkinnedItem())
			return MSG_REGISTER_CHANGED_SKIN;
		if (!isUsableBy(player, template))
			return MSG_REGISTER_GENDER_RACE;
		if (wardrobe.size() >= getSlots(player))
			return MSG_REGISTER_LACK_SLOT;
		return 0;
	}

	/**
	 * C 0xEF. Oficial: S 0x124 ação 2 e msg 1401542, sem custo. O visual já aplicado em itens fica.
	 */
	public void deleteEntry(Player player, int entryObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			WardrobeEntry entry = wardrobe == null ? null : wardrobe.get(entryObjId);
			if (entry == null)
				return;
			if (!PlayerWardrobeDAO.deleteItem(player.getObjectId(), entry))
				return;
			wardrobe.remove(entryObjId);
			IDFactory.getInstance().releaseId(entryObjId);
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(SM_USER_CLASSIC_WARDROBE_DATA_UPDATED.DELETED, entry));
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_DELETED, name(entry)));
			log.info("Wardrobe: {} apagou a entrada {} ({})", player.getName(), entryObjId, entry.getItemId());
		}
	}

	/**
	 * C 0xF8. Oficial: S 0x1C da tinta (motivo 0x82), S 0x124 ação 3 com a cor nova e msg 1401565 [visual, tinta].
	 */
	public void dyeEntry(Player player, int entryObjId, int dyeObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			WardrobeEntry entry = wardrobe == null ? null : wardrobe.get(entryObjId);
			if (entry == null || entry.getItemSkinTemplate() == null || isBusy(player))
				return;
			Item dye = player.getInventory().getItemByObjId(dyeObjId);
			DyeAction action = dye == null || dye.getItemTemplate().getActions() == null ? null : dye.getItemTemplate().getActions().getDyeAction();
			int message = action == null ? MSG_DYE_NOT_FOUND : action.getMinutes() != null ? MSG_DYE_TEMPORARY
				: !entry.getItemSkinTemplate().isItemDyePermitted() ? MSG_DYE_NOT_DYEABLE : 0;
			if (message != 0) {
				log.info("Wardrobe: tinta recusada: player={}, entrada={}, tinta={}, mensagem={}", player.getName(), entryObjId, dyeObjId, message);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
				return;
			}
			ItemTemplate dyeTemplate = dye.getItemTemplate();
			if (!player.getInventory().decreaseByObjectId(dyeObjId, 1, ItemUpdateType.DEC_WARDROBE_DYE))
				return;
			entry.setColor(action.getColor());
			PlayerWardrobeDAO.updateItem(player.getObjectId(), entry);
			InventoryDAO.store(player);
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(SM_USER_CLASSIC_WARDROBE_DATA_UPDATED.DYED, entry));
			if (entry.getColor() == null)
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_DYE_REMOVED, name(entry)));
			else
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_DYED, name(entry), name(dyeTemplate)));
		}
	}

	/**
	 * C 0xF9. Oficial (marcando): S 0x124 ação 4 e msg 1401543. O cliente não tem mensagem para desmarcar.
	 */
	public void setFavorite(Player player, int entryObjId, boolean favorite) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			WardrobeEntry entry = wardrobe == null ? null : wardrobe.get(entryObjId);
			if (entry == null)
				return;
			entry.setLiked(favorite);
			PlayerWardrobeDAO.updateItem(player.getObjectId(), entry);
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(SM_USER_CLASSIC_WARDROBE_DATA_UPDATED.FAVORITE, entry));
			if (favorite)
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_FAVORITE, name(entry)));
		}
	}

	/**
	 * C 0xFA com uma entrada aplica o visual; com 0, tira. Nos dois casos o oficial manda o 0x1D do kinah (motivo 0xDF), o 0x1D do item e a
	 * mensagem com o nome do item alvo. Os dois alvos capturados estavam no cubo; item equipado também é aceito.
	 */
	public void changeSkin(Player player, int itemObjId, int entryObjId) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			if (wardrobe == null || isBusy(player))
				return;
			Item item = player.getInventory().getItemByObjId(itemObjId);
			if (item == null)
				item = player.getEquipment().getEquippedItemByObjId(itemObjId);
			if (item == null) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_CHANGE_SKIN_NO_TARGET_ITEM));
				return;
			}
			if (entryObjId == 0)
				removeSkin(player, item);
			else
				applySkin(player, item, wardrobe.get(entryObjId));
		}
	}

	private void applySkin(Player player, Item item, WardrobeEntry entry) {
		ItemTemplate skin = entry == null ? null : entry.getItemSkinTemplate();
		if (skin == null)
			return;
		ItemTemplate target = item.getItemTemplate();
		long cost = PricesService.getPriceForService(CHANGE_SKIN_COST, player.getRace());
		int message = 0;
		if (!item.isRemodelable())
			message = MSG_CHANGE_SKIN_NOT_CHANGABLE;
		else if (!isSameType(target, skin))
			message = MSG_CHANGE_OTHER_TYPE;
		else if (!isGenderUsable(player, skin))
			message = MSG_CHANGE_GENDER;
		else if (item.isWardrobeSkin() && item.getItemSkinTemplate() == skin && Objects.equals(item.getItemColor(), entry.getColor()))
			message = MSG_CHANGE_SAME;
		else if (player.getInventory().getKinah() < cost)
			message = MSG_CHANGE_NO_KINAH;
		if (message != 0) {
			log.info("Wardrobe: visual recusado: player={}, item={}, entrada={}, mensagem={}", player.getName(), item.getObjectId(),
				entry.getObjectId(), message);
			if (message == MSG_CHANGE_SAME)
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message, name(target), name(skin)));
			else if (message == MSG_CHANGE_SKIN_NOT_CHANGABLE)
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message, name(target)));
			else
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
			return;
		}
		if (!player.getInventory().tryDecreaseKinah(cost, ItemUpdateType.DEC_KINAH_WARDROBE))
			return;
		item.setItemSkinTemplate(skin);
		item.setWardrobeSkin(true);
		item.setItemColor(entry.getColor());
		item.setColorExpireTime(0);
		afterSkinChange(player, item, MSG_CHANGE_SKIN_SUCCEED);
		log.info("Wardrobe: {} aplicou {} (entrada {}) em {} por {} kinah", player.getName(), skin.getTemplateId(), entry.getObjectId(),
			item.getObjectId(), cost);
	}

	/**
	 * Tira o visual do Wardrobe: volta o visual do próprio item e sem tinta (o torso da captura tinha ff79cc antes e voltou sem cor).
	 */
	private void removeSkin(Player player, Item item) {
		long cost = PricesService.getPriceForService(REMOVE_SKIN_COST, player.getRace());
		if (!item.isSkinnedItem()) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REMOVE_NO_SKIN));
			return;
		}
		if (!item.isWardrobeSkin()) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REMOVE_NOT_WARDROBE));
			return;
		}
		if (!player.getInventory().tryDecreaseKinah(cost, ItemUpdateType.DEC_KINAH_WARDROBE)) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REMOVE_NO_KINAH, name(item.getItemTemplate())));
			return;
		}
		int oldSkin = item.getItemSkinTemplate().getTemplateId();
		item.setItemSkinTemplate(item.getItemTemplate());
		item.setItemColor(null);
		item.setColorExpireTime(0);
		afterSkinChange(player, item, MSG_UNCHANGE_SKIN_SUCCEED);
		log.info("Wardrobe: {} tirou o visual {} de {} por {} kinah", player.getName(), oldSkin, item.getObjectId(), cost);
	}

	private static void afterSkinChange(Player player, Item item, int message) {
		ItemPacketService.updateItemAfterInfoChange(player, item);
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message, name(item.getItemTemplate())));
		if (item.isEquipped())
			PacketSendUtility.broadcastPacket(player, new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()),
				true);
		InventoryDAO.store(player);
	}

	/**
	 * Expansão de 1 slot, paga com 600 Quna da conta (S 0x11B e msg 1401574 antes do 0x123) ou com 1 cash_extend_closet_01.
	 */
	public void extendSlots(Player player, int payment) {
		synchronized (player) {
			Map<Integer, WardrobeEntry> wardrobe = player.getPlayerWardrobe();
			if (wardrobe == null || isBusy(player))
				return;
			int slots = getSlots(player);
			int message = slots >= MAX_SLOTS ? MSG_EXPAND_MAX : 0;
			if (message == 0 && payment == PAYMENT_QUNA && !QunaService.spend(player, EXTEND_QUNA, QunaService.CODE_NONE))
				message = MSG_EXPAND_NO_QUNA;
			else if (message == 0 && payment != PAYMENT_QUNA && !player.getInventory().decreaseByItemId(EXTEND_ITEM_ID, 1))
				message = MSG_EXPAND_NO_ITEM;
			if (message != 0) {
				log.info("Wardrobe: expansão recusada: player={}, slots={}, pagamento={}, mensagem={}", player.getName(), slots, payment, message);
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
				return;
			}
			player.getCommonData().setWardrobeSlot(slots + 1);
			PlayerWardrobeDAO.storeSize(player.getObjectId(), slots + 1);
			InventoryDAO.store(player);
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_INFO_UPDATED(getExtendedSlots(player)));
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_EXPANDED));
			log.info("Wardrobe: {} expandiu para {} slots", player.getName(), slots + 1);
		}
	}

	/**
	 * Mesmo filtro da janela (cabeça, torso, mãos, pernas, pés, ombros, arma, escudo, asa): mesmo slot de equipamento, e arma só com o mesmo tipo
	 * de arma, como na remodelagem.
	 */
	static boolean isSameType(ItemTemplate target, ItemTemplate skin) {
		if (target.isWeapon() || skin.isWeapon())
			return target.isWeapon() && skin.isWeapon() && target.getItemGroup() == skin.getItemGroup();
		return target.getItemSlot() == skin.getItemSlot();
	}

	private static boolean isUsableBy(Player player, ItemTemplate template) {
		Race race = template.getRace();
		return (race == null || race == Race.PC_ALL || race == player.getRace()) && isGenderUsable(player, template);
	}

	private static boolean isGenderUsable(Player player, ItemTemplate template) {
		Gender gender = template.getUseLimits() == null ? null : template.getUseLimits().getGenderPermitted();
		return gender == null || gender == player.getGender();
	}

	private static boolean isBusy(Player player) {
		return player.isTrading() || player.hasStore();
	}

	private static DescriptionId name(ItemTemplate template) {
		return new DescriptionId(template.getNameId() * 2 + 1);
	}

	private static DescriptionId name(WardrobeEntry entry) {
		ItemTemplate template = entry.getItemSkinTemplate();
		return new DescriptionId(template == null ? 0 : template.getNameId() * 2 + 1);
	}

	public static PlayerWardrobeService getInstance() {
		return SingletonHolder.instance;
	}

	private static class SingletonHolder {

		protected static final PlayerWardrobeService instance = new PlayerWardrobeService();
	}
}
