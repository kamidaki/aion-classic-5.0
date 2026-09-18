package com.aionemu.gameserver.services;

import java.util.Locale;
import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.controllers.observer.ItemUseObserver;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.ClassicItemSystemsData.EnchantRule;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CLASSIC_ENCHANT_ANIMATION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/** Classic 5.0 essence enchanting, with costs and transitions from client_enchant_count_prob. */
public final class ClassicEnchantService {
	private ClassicEnchantService() {}

	public static void enchant(Player player, Item stone, Item target) {
		if (player == null || player.isDead() || player.isTrading() || !player.isSpawned()
			|| stone == null || target == null || stone == target || !stone.getItemTemplate().isEnchantEssence()
			|| target.getItemTemplate().isNoEnchant()) return;
		EnchantRule rule = DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant(target.getItemTemplate().getEnchantGroup(), target.getEnchantLevel());
		if (rule == null || !owns(player, stone, target) || !hasMaterials(player, stone, rule)) return;
		String quality = target.getItemTemplate().getItemQuality().name().toLowerCase(Locale.ROOT);
		if (quality.equals("legendary")) quality = "legend";
		Integer gap = DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getGap(target.getEnchantLevel() < 10 ? 1 : 2,
			stone.getItemTemplate().getLevel() - target.getItemTemplate().getLevel(), quality);
		if (gap == null) return; // missing canonical data must not invent a success chance
		int probability = Math.clamp(gap + rule.probability, 0, 1000);
		player.getController().cancelUseItem();
		if (player.isCasting()) player.getController().cancelCurrentSkill(null);
		java.util.concurrent.atomic.AtomicBoolean active = new java.util.concurrent.atomic.AtomicBoolean(true);
		ItemUseObserver observer = new ItemUseObserver() {
			@Override public void abort() {
				if (!active.compareAndSet(true, false)) return;
				player.getController().cancelTask(TaskId.ITEM_USE);
				player.getObserveController().removeObserver(this);
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ENCHANT_ITEM_CANCELED(target.getL10n()));
				PacketSendUtility.broadcastPacketAndReceive(player, new SM_CLASSIC_ENCHANT_ANIMATION(player, stone, 0, 1));
			}
		};
		player.getObserveController().attach(observer);
		PacketSendUtility.broadcastPacketAndReceive(player, new SM_CLASSIC_ENCHANT_ANIMATION(player, stone, 5000, 0));
		player.getController().addTask(TaskId.ITEM_USE, ThreadPoolManager.getInstance().schedule(() -> {
			if (!active.compareAndSet(true, false)) return;
			player.getObserveController().removeObserver(observer);
			synchronized (player.getInventory()) {
				if (!player.isDead() && player.isSpawned() && !player.isTrading() && owns(player, stone, target)
					&& target.getEnchantLevel() == rule.before && hasMaterials(player, stone, rule)) {
					boolean paid = rule.component == ItemId.KINAH
						? player.getInventory().tryDecreaseKinah(rule.cost)
						: player.getInventory().decreaseByItemId(rule.component, rule.cost);
					if (paid && player.getInventory().decreaseByObjectId(stone.getObjectId(), rule.stones)) {
						boolean success = Rnd.get(1, 1000) <= probability;
						EnchantService.setEnchantLevel(player, target, success ? rule.success : rule.failure);
						PacketSendUtility.sendPacket(player, success
							? SM_SYSTEM_MESSAGE.STR_ENCHANT_ITEM_SUCCEED(target.getL10n())
							: SM_SYSTEM_MESSAGE.STR_ENCHANT_ITEM_FAILED(target.getL10n()));
					}
				}
			}
			PacketSendUtility.broadcastPacketAndReceive(player, new SM_CLASSIC_ENCHANT_ANIMATION(player, stone, 0, 1));
		}, 5000));
	}

	private static boolean owns(Player player, Item stone, Item target) {
		return player.getInventory().getItemByObjId(stone.getObjectId()) == stone
			&& (player.getInventory().getItemByObjId(target.getObjectId()) == target
				|| player.getEquipment().getEquippedItemByObjId(target.getObjectId()) == target);
	}
	private static boolean hasMaterials(Player player, Item stone, EnchantRule rule) {
		return stone.getItemCount() >= rule.stones && (rule.component == ItemId.KINAH
			? player.getInventory().getKinah() >= rule.cost
			: player.getInventory().getItemCountByItemId(rule.component) >= rule.cost);
	}
}
