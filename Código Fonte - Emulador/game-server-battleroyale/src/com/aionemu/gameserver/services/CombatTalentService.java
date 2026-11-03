package com.aionemu.gameserver.services;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.ClassicItemSystemsData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.skill.PlayerSkillEntry;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.enums.ItemGroup;

/** Power Talent contributions imported from the official Classic 5.0 combat power rules. */
public final class CombatTalentService {
    private CombatTalentService() {}

    public static int calculateCombatPower(Player player) {
        if (player == null || !player.getCommonData().isDaeva()) return 0;
        ClassicItemSystemsData rules = DataManager.CLASSIC_ITEM_SYSTEMS_DATA;
        long total = rules.getPower("character_level", Integer.toString(player.getLevel()));
        for (Item item : player.getEquipment().getEquippedItems()) {
            if ((item.getEquipmentSlot() & ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask()) == 0)
                total += calculateItemPower(item);
        }
        for (PlayerSkillEntry skill : player.getSkillList().getAllSkills())
            total += rules.getPower("skill", Integer.toString(skill.getSkillId()));
        return (int) Math.min(Integer.MAX_VALUE, total);
    }

    public static int calculateItemPower(Item item) {
        if (item == null || item.getItemTemplate() == null) return 0;
        ItemTemplate template = item.getItemTemplate();
        if (template.isStigma() || template.getItemGroup() == ItemGroup.POWER_SHARDS) return 0;
        ClassicItemSystemsData rules = DataManager.CLASSIC_ITEM_SYSTEMS_DATA;
        int total = basePower(template, rules)
            + rules.getPower("enchant_count", Integer.toString(item.getEnchantLevel()));
        if (item.hasManaStones())
            for (ManaStone stone : item.getItemStones()) total += stonePower(stone);
        if (item.hasFusionedItem()) {
            total += basePower(item.getFusionedItemTemplate(), rules);
            if (item.hasFusionStones())
                for (ManaStone stone : item.getFusionStones()) total += stonePower(stone);
        }
        return total;
    }

    private static int basePower(ItemTemplate template, ClassicItemSystemsData rules) {
        if (template == null) return 0;
        String quality = template.getItemQuality().name().toLowerCase(java.util.Locale.ROOT);
        if (quality.equals("legendary")) quality = "legend";
        if (quality.equals("mythic")) quality = "divinity";
        return template.getCombatPower() + rules.getPower("item_quality", quality)
            + rules.getPower("item_level", Integer.toString(template.getLevel()));
    }

    private static int stonePower(ManaStone stone) {
        ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(stone.getItemId());
        return template == null ? 0 : template.getCombatPower();
    }
}
