package com.aionemu.gameserver.services.item;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.skill.PlayerSkillEntry;
import com.aionemu.gameserver.model.templates.item.ItemSkillSet;
import com.aionemu.gameserver.network.aion.serverpackets.SM_INVENTORY_UPDATE_ITEM;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_SKILL_REASSIGN;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_SKILL_REASSIGN_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SKILL_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.SkillLearnService;
import com.aionemu.gameserver.services.player.QunaService;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Skill de equipamento do Classic 5.0 ("Assign Skill on Loot", diálogo Reassign), pelas capturas oficiais de 2026-09-14 e 2026-10-18.
 * <p>
 * A skill fica em {@link Item#getBuffSkill()} (coluna buff_skill), sai no D do offset 60 do bloco 0x0B e vale enquanto o item está
 * equipado:
 * <ul>
 * <li>equipar: S 0x2C com a msg 1403638 (nome do item, nome da skill);</li>
 * <li>desequipar: S 0x2D e a msg 1403639 com os mesmos dois nomes.</li>
 * </ul>
 * Reassign:
 * <ul>
 * <li>C 0x107 [D item]: 60 Quna (S 0x11B com H 0x15C, sem a msg 1401574), depois S 0x193 [item][atual][sorteada][0];</li>
 * <li>C 0x130 [D item][D escolha]: 0 recusa (msg 1403748, S 0x194 [item][atual][atual][0]); a sorteada troca (S 0x1D, msg 1403749,
 * S 0x194 [item][antiga][nova][0]).</li>
 * </ul>
 */
public final class ItemSkillService {

	private static final Logger log = LoggerFactory.getLogger(ItemSkillService.class);

	private static final int MSG_SKILL_ENABLED_EQUIPPED = 1403638;
	private static final int MSG_SKILL_DISABLED_UNEQUIPPED = 1403639; // STR_MSG_SKILL_FUNC_DISABLE_UNEQUIPED
	private static final int MSG_REASSIGN_CANCELED = 1403748; // STR_MSG_REIDENTIFY_SKILL_ENCHANT_SET_CANCELED
	private static final int MSG_REASSIGN_SUCCEED = 1403749; // STR_MSG_REIDENTIFY_SKILL_ENCHANT_SET_SUCCEED

	/** objId do jogador -> sorteio aguardando a escolha do C 0x130 */
	private static final Map<Integer, Pending> pending = new ConcurrentHashMap<>();

	private record Pending(int itemObjId, int skillId) {
	}

	private ItemSkillService() {
	}

	public static boolean isEquipmentSkillItem(Item item) {
		return DataManager.ITEM_SKILL_SET_DATA.getSkillSet(item.getItemId()) != null;
	}

	public static void onEquip(Player player, Item item) {
		int skillId = item.getBuffSkill();
		if (skillId == 0 || DataManager.SKILL_DATA.getSkillTemplate(skillId) == null)
			return;
		if (!player.getSkillList().addTemporarySkillSilently(player, skillId, 1))
			return;
		if (player.isSpawned()) {
			PlayerSkillEntry entry = player.getSkillList().getSkillEntry(skillId);
			PacketSendUtility.sendPacket(player, new SM_SKILL_LIST(entry, MSG_SKILL_ENABLED_EQUIPPED, itemDescription(item), skillDescription(skillId)));
		}
	}

	public static void onUnequip(Player player, Item item) {
		int skillId = item.getBuffSkill();
		if (skillId == 0 || !SkillLearnService.removeSkill(player, skillId))
			return;
		if (player.isSpawned())
			PacketSendUtility.sendPacket(player,
				new SM_SYSTEM_MESSAGE(MSG_SKILL_DISABLED_UNEQUIPPED, new DescriptionId(itemDescription(item)), new DescriptionId(skillDescription(skillId))));
	}

	/**
	 * C 0x107: cobra o Reassign e sorteia a skill que o jogador pode aceitar.
	 */
	public static void requestReassign(Player player, int itemObjId) {
		Item item = findItem(player, itemObjId);
		ItemSkillSet skillSet = item == null ? null : DataManager.ITEM_SKILL_SET_DATA.getSkillSet(item.getItemId());
		if (skillSet == null) {
			log.warn("Reassign: {} pediu o item {} sem conjunto de skill", player.getName(), itemObjId);
			return;
		}
		if (!QunaService.spend(player, skillSet.getQuna(), QunaService.CODE_ITEM_SKILL_REASSIGN, false)) {
			log.info("Reassign: {} sem {} Quna para o item {}", player.getName(), skillSet.getQuna(), item.getItemId());
			return;
		}
		int rolled = skillSet.roll();
		pending.put(player.getObjectId(), new Pending(itemObjId, rolled));
		PacketSendUtility.sendPacket(player, new SM_ITEM_SKILL_REASSIGN(itemObjId, item.getBuffSkill(), rolled));
	}

	/**
	 * C 0x130: 0 mantém a skill atual; a skill sorteada troca.
	 */
	public static void selectReassign(Player player, int itemObjId, int skillId) {
		Pending roll = pending.remove(player.getObjectId());
		Item item = findItem(player, itemObjId);
		if (roll == null || roll.itemObjId() != itemObjId || item == null) {
			log.warn("Reassign: {} escolheu {} no item {} sem sorteio pendente", player.getName(), skillId, itemObjId);
			return;
		}
		int oldSkillId = item.getBuffSkill();
		if (skillId != roll.skillId()) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REASSIGN_CANCELED, new DescriptionId(itemDescription(item))));
			PacketSendUtility.sendPacket(player, new SM_ITEM_SKILL_REASSIGN_RESULT(itemObjId, oldSkillId, oldSkillId));
			return;
		}
		boolean equipped = item.isEquipped();
		if (equipped)
			onUnequip(player, item);
		item.setBuffSkill(skillId);
		item.setPersistentState(PersistentState.UPDATE_REQUIRED);
		if (equipped)
			onEquip(player, item);
		PacketSendUtility.sendPacket(player, new SM_INVENTORY_UPDATE_ITEM(player, item));
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REASSIGN_SUCCEED, new DescriptionId(itemDescription(item))));
		PacketSendUtility.sendPacket(player, new SM_ITEM_SKILL_REASSIGN_RESULT(itemObjId, oldSkillId, skillId));
	}

	public static void onLogout(Player player) {
		pending.remove(player.getObjectId());
	}

	private static Item findItem(Player player, int itemObjId) {
		Item item = player.getInventory().getItemByObjId(itemObjId);
		return item != null ? item : player.getEquipment().getEquippedItemByObjId(itemObjId);
	}

	private static int itemDescription(Item item) {
		return item.getItemTemplate().getNameId() * 2 + 1;
	}

	private static int skillDescription(int skillId) {
		SkillTemplate template = DataManager.SKILL_DATA.getSkillTemplate(skillId);
		return template == null ? 0 : template.getL10nId() * 2 + 1;
	}
}
