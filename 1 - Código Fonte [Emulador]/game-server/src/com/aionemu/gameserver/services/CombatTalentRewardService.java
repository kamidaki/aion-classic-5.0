package com.aionemu.gameserver.services;

import com.aionemu.gameserver.dao.CombatTalentRewardDAO;
import com.aionemu.gameserver.dataholders.ClassicItemSystemsData.CombatRewardRule;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_TALENT_REWARDS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_TALENT_REWARD_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CUBE_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.utils.PacketSendUtility;

/** Official Classic 5.0 Combat Talent milestone rewards. */
public final class CombatTalentRewardService {

	private static final ItemUpdatePredicate REWARD_ADD = new ItemUpdatePredicate(ItemAddType.COMBAT_TALENT_REWARD,
		ItemUpdateType.INC_COMBAT_TALENT_REWARD);

	private CombatTalentRewardService() {
	}

	public static void sendProgress(Player player) {
		if (player != null)
			PacketSendUtility.sendPacket(player, new SM_COMBAT_TALENT_REWARDS(player, CombatTalentRewardDAO.loadClaimedMask(player)));
	}

	public static void claim(Player player, int rewardId) {
		if (player == null || !player.isSpawned() || player.isDead() || player.isTrading() || rewardId < 1 || rewardId > 32)
			return;
		CombatRewardRule reward = DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getCombatReward(rewardId);
		if (reward == null || CombatTalentService.calculateCombatPower(player) < reward.goal)
			return;
		ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(reward.item);
		if (template == null)
			return;

		Storage inventory = player.getInventory();
		synchronized (inventory) {
			if (!hasSpace(inventory, template, reward.amount)) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_UI_INVENTORY_FULL());
				return;
			}
			if (!CombatTalentRewardDAO.claim(player, rewardId))
				return;
			try {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_COMBAT_POWER_REWARD_GET(template.getNameId(), reward.amount));
				PacketSendUtility.sendPacket(player, new SM_COMBAT_TALENT_REWARD_UPDATE(rewardId, true));
				long remaining = ItemService.addItem(player, reward.item, reward.amount, false, REWARD_ADD);
				if (remaining != 0)
					throw new IllegalStateException("Could not add " + remaining + " of reward item " + reward.item);
			} catch (RuntimeException e) {
				CombatTalentRewardDAO.unclaim(player, rewardId);
				PacketSendUtility.sendPacket(player, new SM_COMBAT_TALENT_REWARD_UPDATE(rewardId, false));
				throw e;
			}
			int mask = CombatTalentRewardDAO.loadClaimedMask(player);
			PacketSendUtility.sendPacket(player, new SM_COMBAT_TALENT_REWARDS(player, mask));
			PacketSendUtility.sendPacket(player, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, player));
		}
	}

	private static boolean hasSpace(Storage inventory, ItemTemplate template, long amount) {
		if (!template.isStackable())
			return amount <= inventory.getFreeSlots(template.getExtraInventoryId());
		long freeInStacks = 0;
		for (Item item : inventory.getItemsByItemId(template.getTemplateId()))
			freeInStacks += Math.max(0, template.getMaxStackCount() - item.getItemCount());
		long remaining = Math.max(0, amount - freeInStacks);
		long requiredSlots = (remaining + template.getMaxStackCount() - 1) / template.getMaxStackCount();
		return requiredSlots <= inventory.getFreeSlots(template.getExtraInventoryId());
	}
}
