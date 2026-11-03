package com.aionemu.gameserver.services;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.configs.main.MembershipConfig;
import com.aionemu.gameserver.controllers.observer.ItemUseObserver;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.templates.item.Stigma;
import com.aionemu.gameserver.model.templates.item.Stigma.RequiredSkillGroup;
import com.aionemu.gameserver.model.templates.item.Stigma.StigmaKind;
import com.aionemu.gameserver.model.templates.item.Stigma.StigmaSkill;
import com.aionemu.gameserver.model.templates.item.enums.ItemGroup;
import com.aionemu.gameserver.network.aion.serverpackets.SM_INVENTORY_UPDATE_ITEM;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_USAGE_ANIMATION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.skillengine.model.SkillLearnTemplate;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * Classic 5.0 stigma rules, measured on the official Stigma/Stigma2 captures and the EU 3.7 patch notes:
 * <ul>
 * <li>12 slots per page: normal area (bits 20-25) and greater area (bits 27-32); a greater stigma only fits the greater area, normal and meta
 * stigmas fit anywhere</li>
 * <li>equipping consumes the stone's shards, event shards first; removing is free</li>
 * <li>a greater stigma needs one skill of each required group granted by another equipped stone, and a stone that is still required cannot
 * be removed</li>
 * <li>the stone teaches exactly its gain skills</li>
 * </ul>
 *
 * @author Lost Academy Team & Durak
 */
public class StigmaService {

	private static final Logger log = LoggerFactory.getLogger(StigmaService.class);

	private static final int STIGMA_SHARD = 141000001;
	private static final int EVENT_STIGMA_SHARD = 141000002;

	/**
	 * Validates a stigma equip request before the item is moved. Non-stigma items are always accepted here.
	 */
	public static boolean checkEquip(Player player, Item item, long slot) {
		if (item.getItemTemplate().getItemGroup() != ItemGroup.STIGMA)
			return true;
		Stigma stigma = item.getItemTemplate().getStigma();
		if (stigma == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_CANNOT_EQUIP_STONE());
			return false;
		}
		if (stigma.getKind() == StigmaKind.GREATER && !ItemSlot.isAdvancedStigma(slot)) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_TOO_HIGH_STONE_RANK_FOR_SLOT(item.getL10n()));
			return false;
		}
		List<Item> equippedStigmas = player.getEquipment().getEquippedItemsAllStigma();
		for (Item equipped : equippedStigmas) {
			if (equipped.getEquipmentSlot() == slot) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_SLOT_IS_NOT_OPENED());
				return false;
			}
			Stigma equippedStigma = equipped.getItemTemplate().getStigma();
			if (equipped.getItemId() == item.getItemId()
				|| equippedStigma != null && stigma.getGainSkills().stream().anyMatch(s -> equippedStigma.grantsSkill(s.skillId()))) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_STIGMA_ALREADY_EQUIP_STONE());
				return false;
			}
		}
		if (!hasRequiredSkills(stigma, item, equippedStigmas, null)) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_TO_EQUIP_STONE_LEARN_PRESKILL(item.getL10n()));
			return false;
		}
		if (getShardCount(player) < stigma.getShard()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_CANNT_EQUIP_STONE_OUT_OF_AVAILABLE_STIGMA_POINT(String.valueOf(stigma.getShard())));
			return false;
		}
		return true;
	}

	/**
	 * Called after the stone was moved into its slot (official order: S 0x1D with the slot, then S 0x2C with the skills, then the shard count).
	 */
	public static void onEquip(Player player, Item item) {
		Stigma stigma = item.getItemTemplate().getStigma();
		if (stigma == null)
			return;
		addStigmaSkills(player, stigma, item.getEnchantLevel());
		consumeShards(player, stigma.getShard());
	}

	public static int getStigmaSlotIndex(long mask) {
		if (mask >= (1L << 20) && mask <= (1L << 25)) {
			return Long.numberOfTrailingZeros(mask) - 20; // 0..5 (regular stigmas)
		}
		if (mask >= (1L << 27) && mask <= (1L << 32)) {
			return Long.numberOfTrailingZeros(mask) - 20; // 7..12 (greater stigmas: bit 27 -> slot 7, bit 32 -> slot 12)
		}
		return 0;
	}

	public static long getStigmaSlotMask(int slotIndex) {
		if (slotIndex >= 0 && slotIndex <= 5) {
			return 1L << (20 + slotIndex);
		}
		if (slotIndex >= 7 && slotIndex <= 12) {
			return 1L << (20 + slotIndex);
		}
		if (slotIndex >= 6 && slotIndex <= 11) {
			return 1L << (27 + (slotIndex - 6));
		}
		return 0;
	}

	public static long findFreeStigmaSlot(Player player, boolean isGreater) {
		java.util.Set<Long> usedSlots = new java.util.HashSet<>();
		for (Item eq : player.getEquipment().getEquippedItemsAllStigma()) {
			usedSlots.add(eq.getEquipmentSlot());
		}

		if (!isGreater) {
			for (int i = 0; i < 6; i++) {
				long mask = 1L << (20 + i);
				if (!usedSlots.contains(mask))
					return mask;
			}
		}
		for (int i = 0; i < 6; i++) {
			long mask = 1L << (27 + i);
			if (!usedSlots.contains(mask))
				return mask;
		}
		return 0;
	}

	/**
	 * Validates a player's request to remove a stone: it is refused while another equipped stone still needs one of its skills.
	 */
	public static boolean checkUnequip(Player player, Item item) {
		if (item.getItemTemplate().getStigma() == null)
			return true;
		List<Item> equippedStigmas = player.getEquipment().getEquippedItemsAllStigma();
		for (Item other : equippedStigmas) {
			Stigma otherStigma = other.getItemTemplate().getStigma();
			if (other == item || otherStigma == null || otherStigma.getRequiredSkillGroups().isEmpty())
				continue;
			if (hasRequiredSkills(otherStigma, other, equippedStigmas, null) && !hasRequiredSkills(otherStigma, other, equippedStigmas, item)) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_CANT_UNEQUIP_STONE_FOR_AFTERSKILL(item.getL10n(), other.getL10n()));
				return false;
			}
		}
		return true;
	}

	public static void onPlayerLogin(Player player) {
		if (player.hasPermission(MembershipConfig.STIGMA_AUTOLEARN)) {
			for (int level = 20; level <= player.getLevel(); level++) {
				for (SkillLearnTemplate template : DataManager.SKILL_TREE_DATA.getTemplatesFor(player.getPlayerClass(), level, player.getRace())) {
					if (template.isStigma())
						SkillLearnService.learnTemporarySkill(player, template.getSkillId(), template.getSkillLevel());
				}
			}
			return;
		}

		for (Item item : player.getEquipment().getEquippedItemsAllStigma()) {
			Stigma stigma = item.getItemTemplate().getStigma();
			String problem = null;
			if (stigma == null)
				problem = "has no Classic 5.0 stigma data";
			else if (!item.getItemTemplate().isClassSpecific(player.getPlayerClass()))
				problem = "is not for his class";
			else if (stigma.getKind() == StigmaKind.GREATER && !ItemSlot.isAdvancedStigma(item.getEquipmentSlot()))
				problem = "is a greater stigma outside the greater stigma slots";
			if (problem != null) {
				player.getEquipment().unEquipItem(item.getObjectId(), false);
				log.warn("Unequipped stigma " + item.getItemId() + " of " + player + " on login: it " + problem);
			}
		}
		List<Item> equippedStigmas = player.getEquipment().getEquippedItemsAllStigma();
		for (Item item : equippedStigmas) {
			if (!hasRequiredSkills(item.getItemTemplate().getStigma(), item, equippedStigmas, null)) {
				player.getEquipment().unEquipItem(item.getObjectId(), false);
				log.warn("Unequipped stigma " + item.getItemId() + " of " + player + " on login: its required stigma skills are not equipped");
			}
		}
		for (Item item : player.getEquipment().getEquippedItemsAllStigma())
			addStigmaSkills(player, item.getItemTemplate().getStigma(), item.getEnchantLevel());
	}

	public static boolean isEquipped(Player player, int itemId) {
		if (player.getEquipment().getEquippedItemsByItemId(itemId) != null)
			return player.getEquipment().getEquippedItemsByItemId(itemId).size() > 0;
		return false;
	}

	public static boolean isEquipped(Player player, int neededCount, int... itemIds) {
		int equippedCount = 0;
		for (int itemId : itemIds)
			if (isEquipped(player, itemId))
				equippedCount += 1;
		return equippedCount == neededCount;
	}

	/**
	 * @param ignored
	 *          - stone treated as not equipped (the one the player wants to remove), may be null
	 * @return True if each required skill group of the stigma is satisfied by another equipped stone.
	 */
	private static boolean hasRequiredSkills(Stigma stigma, Item self, List<Item> equippedStigmas, Item ignored) {
		for (RequiredSkillGroup group : stigma.getRequiredSkillGroups()) {
			boolean satisfied = equippedStigmas.stream()
				.filter(other -> other != self && other != ignored && other.getItemTemplate().getStigma() != null)
				.flatMap(other -> other.getItemTemplate().getStigma().getGainSkills().stream())
				.anyMatch(skill -> group.skillIds().contains(skill.skillId()) && skill.level() >= group.level());
			if (!satisfied)
				return false;
		}
		return true;
	}

	private static long getShardCount(Player player) {
		return player.getInventory().getItemCountByItemId(EVENT_STIGMA_SHARD) + player.getInventory().getItemCountByItemId(STIGMA_SHARD);
	}

	private static void consumeShards(Player player, long count) {
		for (int shardId : new int[] { EVENT_STIGMA_SHARD, STIGMA_SHARD }) { // event shards are consumed first (client STR_STIGMA_CONFIRM_EQUIP)
			for (Item shard : player.getInventory().getItemsByItemId(shardId)) {
				if (count <= 0)
					return;
				long taken = Math.min(count, shard.getItemCount());
				player.getInventory().decreaseItemCount(shard, taken, ItemUpdateType.DEC_STIGMA_USE);
				count -= taken;
			}
		}
	}

	public static void chargeStigma(Player player, Item stigma, Item chargeStone) {
		Stigma stigmaInfo = stigma.getItemTemplate().getStigma();
		if (stigma.getItemId() != chargeStone.getItemId() || chargeStone.getEnchantLevel() > 0 || stigma.getEnchantLevel() >= 10)
			return;
		if (!stigma.isStigmaChargeable())
			return;

		final boolean isSuccess = Rnd.chance() < Math.max(25, 100 - (stigma.getEnchantLevel() * 10));

		final int parentItemId = stigma.getItemId();
		final int parentObjectId = stigma.getObjectId();
		PacketSendUtility.broadcastPacket(player,
			new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), parentObjectId, chargeStone.getObjectId(), parentItemId, 5000, 0, 0), true);
		final ItemUseObserver observer = new ItemUseObserver() {

			@Override
			public void abort() {
				player.getController().cancelTask(TaskId.ITEM_USE);
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_CANCELED());
				PacketSendUtility.broadcastPacket(player,
					new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), parentObjectId, chargeStone.getObjectId(), parentItemId, 0, 2, 0), true);
				player.getObserveController().removeObserver(this);
			}
		};
		player.getObserveController().attach(observer);
		player.getController().addTask(TaskId.ITEM_USE, ThreadPoolManager.getInstance().schedule(new Runnable() {

			@Override
			public void run() {
				player.getObserveController().removeObserver(observer);
				PacketSendUtility.broadcastPacket(player,
					new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), parentObjectId, parentItemId, 0, isSuccess ? 1 : 2, 1), true);
				if (!player.getInventory().decreaseByObjectId(chargeStone.getObjectId(), 1, ItemPacketService.ItemUpdateType.DEC_STIGMA_USE))
					return;
				if (!isSuccess) {
					if (stigma.isEquipped())
						player.getEquipment().unEquipItem(stigma.getObjectId());
					player.getInventory().decreaseByObjectId(stigma.getObjectId(), 1, ItemPacketService.ItemUpdateType.DEC_STIGMA_USE);
					PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_STIGMA_ENCHANT_FAIL(stigma.getL10n()));
				} else {
					stigma.setEnchantLevel(stigma.getEnchantLevel() + 1);
					if (stigma.isEquipped()) {
						removeStigmaSkills(player, stigma, false);
						addStigmaSkills(player, stigmaInfo, stigma.getEnchantLevel());
					}
					PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_STIGMA_ENCHANT_SUCCESS(stigma.getL10n()));
					PacketSendUtility.sendPacket(player, new SM_INVENTORY_UPDATE_ITEM(player, stigma));
					if (stigma.getPersistentState() != PersistentState.DELETED) {
						stigma.setPersistentState(PersistentState.UPDATE_REQUIRED);
						if (stigma.isEquipped())
							player.getEquipment().setPersistentState(PersistentState.UPDATE_REQUIRED);
						else
							player.getInventory().setPersistentState(PersistentState.UPDATE_REQUIRED);
					}
				}
			}

		}, 5000));
	}

	private static void addStigmaSkills(Player player, Stigma stigma, int enchantLevel) {
		for (StigmaSkill skill : stigma.getGainSkills())
			SkillLearnService.learnTemporarySkill(player, skill.skillId(), skill.level() + enchantLevel);
	}

	/**
	 * Removes the skills taught by the stone (official order after S 0x1D: the "cannot use" message, then S 0x2D, for each skill).
	 */
	public static void removeStigmaSkills(Player player, Item stigmaItem, boolean notifyPlayer) {
		Stigma stigma = stigmaItem.getItemTemplate().getStigma();
		if (stigma == null)
			return;
		for (StigmaSkill skill : stigma.getGainSkills()) {
			if (!player.getSkillList().isSkillPresent(skill.skillId()))
				continue;
			SkillTemplate template = DataManager.SKILL_DATA.getSkillTemplate(skill.skillId());
			if (notifyPlayer && template != null && template.getL10n() != null)
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_STIGMA_YOU_CANNOT_USE_THIS_SKILL_AFTER_UNEQUIP_STIGMA_STONE(template.getL10n()));
			SkillLearnService.removeSkill(player, skill.skillId());
		}
	}
}
