package com.aionemu.gameserver.services;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemQuality;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;

import java.util.List;

/**
 * Combat Talent / Power Score calculation service for Classic 5.0.
 * Calculates player combat power based on equipped items, enchant levels,
 * quality, socketed manastones, fusioned weapons, and character level.
 *
 * @author Lost Academy Team & Durak
 */
public class CombatTalentService {

	/**
	 * Calculates the total combat talent / power score of a player.
	 *
	 * @param player The player
	 * @return total combat talent score
	 */
	public static int calculateCombatPower(Player player) {
		if (player == null || player.getEquipment() == null) {
			return 0;
		}

		int totalPower = 0;
		List<Item> equippedItems = player.getEquipment().getEquippedItems();
		if (equippedItems != null) {
			for (Item item : equippedItems) {
				if (item == null || item.getItemTemplate() == null) {
					continue;
				}
				totalPower += calculateItemPower(item);
			}
		}

		// Base power from player level (20 points per level)
		totalPower += player.getLevel() * 20;

		return totalPower;
	}

	/**
	 * Calculates the combat power contribution of a single item.
	 *
	 * @param item The item
	 * @return combat power points
	 */
	public static int calculateItemPower(Item item) {
		if (item == null) {
			return 0;
		}

		ItemTemplate template = item.getItemTemplate();
		if (template == null) {
			return 0;
		}

		int power = 0;

		// 1. Base power from item level (level 1 to 75)
		int itemLevel = template.getLevel();
		power += itemLevel * 10;

		// 2. Bonus from Item Quality / Rarity
		ItemQuality quality = template.getItemQuality();
		if (quality != null) {
			power += switch (quality) {
				case JUNK -> 0;
				case COMMON -> 20;
				case RARE -> 50;
				case LEGEND, LEGENDARY -> 150;
				case UNIQUE -> 250;
				case EPIC -> 400;
				case MYTHIC -> 600;
			};
		}

		// 3. Enchant Level bonus (exponential curve matching official rule: +15 = ~842)
		int enchant = item.getEnchantLevel();
		if (enchant > 0) {
			power += (int) (enchant * 30 + Math.pow(enchant, 1.8) * 4);
		}

		// 4. Manastones socketed (35 points each)
		if (item.hasManaStones()) {
			power += item.getItemStones().size() * 35;
		}

		// 5. Fusioned item power and fusion stones
		if (item.hasFusionedItem()) {
			ItemTemplate fusedTemplate = item.getFusionedItemTemplate();
			if (fusedTemplate != null) {
				power += (fusedTemplate.getLevel() * 5);
				if (fusedTemplate.getItemQuality() != null) {
					power += switch (fusedTemplate.getItemQuality()) {
						case LEGEND, LEGENDARY -> 75;
						case UNIQUE -> 125;
						case EPIC -> 200;
						case MYTHIC -> 300;
						default -> 20;
					};
				}
			}
			if (item.hasFusionStones()) {
				power += item.getFusionStones().size() * 25;
			}
		}

		// 6. Idian stone bonus (50 points)
		if (item.getIdianStone() != null) {
			power += 50;
		}

		return power;
	}
}
