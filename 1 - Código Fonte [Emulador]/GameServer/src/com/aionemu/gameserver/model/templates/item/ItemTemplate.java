package com.aionemu.gameserver.model.templates.item;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.items.ItemMask;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.VisibleObjectTemplate;
import com.aionemu.gameserver.model.templates.item.actions.ItemActions;
import com.aionemu.gameserver.model.templates.itemset.ItemSetTemplate;
import com.aionemu.gameserver.model.templates.stats.ModifiersTemplate;
import com.aionemu.gameserver.world.zone.ZoneName;

import org.apache.commons.lang.StringUtils;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;
import java.util.List;

@XmlAccessorType(XmlAccessType.NONE)
@XmlType(namespace = "", name = "ItemTemplate")
public class ItemTemplate extends VisibleObjectTemplate {
	@XmlAttribute(name = "id", required = true)
	@XmlID
	private String id;

	private int itemId;

	@XmlElement(name = "modifiers", required = false)
	protected ModifiersTemplate modifiers;

	@XmlElement(name = "actions", required = false)
	protected ItemActions actions;

	@XmlAttribute(name = "mask")
	private int mask;

	@XmlAttribute(name = "category")
	private ItemCategory category = ItemCategory.NONE;

	@XmlAttribute(name = "slot")
	private int itemSlot;

	@XmlAttribute(name = "equipment_type")
	private EquipType equipmentType = EquipType.NONE;

	@XmlAttribute(name = "weapon_boost")
	private int weaponBoost;

	@XmlAttribute(name = "price")
	private int price;

	@XmlAttribute(name = "abyss_point")
	private int abyssPoint;

	@XmlAttribute(name = "max_stack_count")
	private int maxStackCount = 1;

	@XmlAttribute(name = "level")
	private int level;

	@XmlAttribute(name = "quality")
	private ItemQuality itemQuality;

	@XmlAttribute(name = "item_type")
	private ItemType itemType;

	@XmlAttribute(name = "weapon_type")
	private WeaponType weaponType;

	@XmlAttribute(name = "armor_type")
	private ArmorType armorType;

	@XmlAttribute(name = "attack_type")
	private ItemAttackType attackType;

	@XmlAttribute(name = "attack_gap")
	private float attackGap;

	@XmlAttribute(name = "desc")
	private String description;

	@XmlAttribute(name = "option_slot_bonus")
	private int optionSlotBonus;

	@XmlAttribute(name = "bonus_apply")
	private String bonusApply;

	@XmlAttribute(name = "no_enchant")
	private boolean noEnchant;

	@XmlAttribute(name = "dye")
	private boolean itemDyePermitted;

	@XmlAttribute(name = "race")
	private Race race = Race.PC_ALL;

	@XmlAttribute(name = "return_world")
	private int returnWorldId;

	@XmlAttribute(name = "return_alias")
	private String returnAlias;

	@XmlElement(name = "godstone")
	private GodstoneInfo godstoneInfo;

	@XmlElement(name = "stigma")
	private Stigma stigma;

	@XmlAttribute(name = "name")
	private String name;

	@XmlAttribute(name = "restrict")
	private String restrict;

	@XmlAttribute(name = "restrict_max")
	private String restrictMax;

	@XmlAttribute(name = "tag")
	private String tag;

	@XmlTransient
	private int[] restricts;

	@XmlTransient
	private byte[] restrictsMax;

	@XmlAttribute(name = "m_slots")
	private int manastoneSlots;

	@XmlAttribute(name = "temp_exchange_time")
	protected int temExchangeTime;

	@XmlAttribute(name = "expire_time")
	protected int expireTime;

	@XmlElement(name = "weapon_stats")
	protected WeaponStats weaponStats;

	@XmlAttribute(name = "activate_count")
	private int activationCount;

	@XmlAttribute(name = "func_pet_id")
	private int funcPetId;

	@XmlElement(name = "tradein_list")
	protected TradeinList tradeinList;

	@XmlElement(name = "acquisition")
	private Acquisition acquisition;

	@XmlElement(name = "improve")
	private Improvement improvement;

	@XmlElement(name = "uselimits")
	private ItemUseLimits useLimits = new ItemUseLimits();

	@XmlElement(name = "purchable")
	private ItemPurchableLimits purchableLimits = new ItemPurchableLimits();

	@XmlElement(name = "inventory")
	private ExtraInventory extraInventory;

	@XmlTransient
	private boolean isQuestUpdateItem;

	private static final WeaponStats emptyWeaponStats = new WeaponStats();

	/**
	 * @param u
	 * @param parent
	 */
	void afterUnmarshal(Unmarshaller u, Object parent) {
		setItemId(Integer.parseInt(id));
		if (restrict != null) {
			String[] parts = restrict.split("[,\\s]+");
			restricts = new int[Math.max(parts.length, 30)];
			for (int i = 0; i < parts.length; i++) {
				restricts[i] = Integer.parseInt(parts[i]);
			}
		}
		if (restrictMax != null) {
			String[] partsMax = restrictMax.split("[,\\s]+");
			restrictsMax = new byte[Math.max(partsMax.length, 30)];
			for (int i = 0; i < partsMax.length; i++) {
				restrictsMax[i] = Byte.parseByte(partsMax[i]);
			}
		}
		if (weaponStats == null) {
			weaponStats = emptyWeaponStats;
		}
	}

	public byte getMaxLevelRestrict(Player player) {
		if (restrictMax != null && restrictsMax != null) {
			byte restrictId = player.getPlayerClass().getClassId();
			if (restrictId < restrictsMax.length) {
				byte restrictLevel = restrictsMax[restrictId];
				return player.getLevel() <= restrictLevel ? 0 : restrictLevel;
			}
		}
		return 0;
	}

	public String getId() {
		return id;
	}

	public int getMask() {
		return mask;
	}

	public ItemCategory getCategory() {
		return category;
	}

	public int getItemSlot() {
		return itemSlot;
	}

	/**
	 * @param playerClass
	 * @return
	 */
	public boolean isClassSpecific(PlayerClass playerClass) {
		if (restricts == null)
			return false;
		int idx = playerClass.ordinal();
		boolean related = idx < restricts.length && restricts[idx] > 0;
		if (!related && !playerClass.isStartingClass()) {
			int startIdx = PlayerClass.getStartingClassFor(playerClass).ordinal();
			related = startIdx < restricts.length && restricts[startIdx] > 0;
		}
		return related;
	}

	/**
	 * @param playerClass
	 * 
	 * @return
	 */
	public int getRequiredLevel(PlayerClass playerClass) {
		if (restricts == null)
			return -1;
		int idx = playerClass.ordinal();
		if (idx >= restricts.length)
			return -1;
		int requiredLevel = restricts[idx];
		if (requiredLevel == 0) {
			return -1;
		} else {
			return requiredLevel;
		}
	}

	public List<StatFunction> getModifiers() {
		if (modifiers != null) {
			return modifiers.getModifiers();
		}
		return null;
	}

	public ItemActions getActions() {
		return actions;
	}

	public EquipType getEquipmentType() {
		return equipmentType;
	}

	public int getPrice() {
		return price;
	}

	public int getAbyssPoint() {
		return abyssPoint;
	}

	public int getLevel() {
		return level;
	}

	public ItemQuality getItemQuality() {
		return itemQuality;
	}

	public ItemType getItemType() {
		return itemType;
	}

	public WeaponType getWeaponType() {
		return weaponType;
	}

	public ArmorType getArmorType() {
		return armorType;
	}

	@Override
	public int getNameId() {
		try {
			int val = Integer.parseInt(description);
			return val;
		} catch (NumberFormatException nfe) {
			return 0;
		}
	}

	public long getMaxStackCount() {
		if (isKinah()) {
			if (CustomConfig.ENABLE_KINAH_CAP) {
				return CustomConfig.KINAH_CAP_VALUE;
			} else {
				return Long.MAX_VALUE;
			}
		}
		return maxStackCount;
	}

	public ItemAttackType getAttackType() {
		return attackType;
	}

	public float getAttackGap() {
		return attackGap;
	}

	public int getOptionSlotBonus() {
		return optionSlotBonus;
	}

	public String getBonusApply() {
		return bonusApply;
	}

	public boolean isNoEnchant() {
		return noEnchant;
	}

	public boolean isItemDyePermitted() {
		return itemDyePermitted;
	}

	public Race getRace() {
		return race;
	}

	public int getWeaponBoost() {
		return weaponBoost;
	}

	public boolean isWeapon() {
		return equipmentType == EquipType.WEAPON;
	}

	public boolean isArmor() {
		return equipmentType == EquipType.ARMOR;
	}

	public boolean isKinah() {
		return itemId == ItemId.KINAH.value();
	}

	public boolean isStigma() {
		return itemId >= 140000001 && itemId <= 140000999;
	}

	public boolean isManaStone() {
		return category == ItemCategory.MANASTONE;
	}

	public boolean isMedal() {
		return category == ItemCategory.MEDALS;
	}

	public boolean isAbyssItem() {
		return itemType == ItemType.ABYSS;
	}

	public void setItemId(int itemId) {
		this.itemId = itemId;
	}

	/**
	 * @return id of the associated ItemSetTemplate or null if none
	 */
	public ItemSetTemplate getItemSet() {
		return DataManager.ITEM_SET_DATA.getItemSetTemplateByItemId(itemId);
	}

	/**
	 * Checks if the ItemTemplate belongs to an item set
	 */
	public boolean isItemSet() {
		return getItemSet() != null;
	}

	public GodstoneInfo getGodstoneInfo() {
		return godstoneInfo;
	}

	@Override
	public String getName() {
		return name != null ? name : StringUtils.EMPTY;
	}

	@Override
	public int getTemplateId() {
		return itemId;
	}

	public int getReturnWorldId() {
		return returnWorldId;
	}

	public String getReturnAlias() {
		return returnAlias;
	}

	public Stigma getStigma() {
		return stigma;
	}

	public int getManastoneSlots() {
		return manastoneSlots;
	}

	public boolean hasLimitOne() {
		return (getMask() & ItemMask.LIMIT_ONE) == ItemMask.LIMIT_ONE;
	}

	public boolean isTradeable() {
		return (getMask() & ItemMask.TRADEABLE) == ItemMask.TRADEABLE;
	}

	public boolean isCanFuse() {
		return (getMask() & ItemMask.CAN_COMPOSITE_WEAPON) == ItemMask.CAN_COMPOSITE_WEAPON;
	}

	public boolean canExtract() {
		return (getMask() & ItemMask.CAN_SPLIT) == ItemMask.CAN_SPLIT;
	}

	public boolean isSoulBound() {
		return (getMask() & ItemMask.SOUL_BOUND) == ItemMask.SOUL_BOUND;
	}

	public boolean isBreakable() {
		return (getMask() & ItemMask.BREAKABLE) == ItemMask.BREAKABLE;
	}

	public boolean isDeletable() {
		return (getMask() & ItemMask.DELETABLE) == ItemMask.DELETABLE;
	}

	public boolean isTwoHandWeapon() {
		if (!isWeapon() || weaponType == null) {
			return false;
		}
		return weaponType.getRequiredSlots() == 2;
	}

	public static WeaponStats getDefaultWeaponStats(WeaponType weaponType) {
		if (weaponType == null) {
			return emptyWeaponStats;
		}
		switch (weaponType) {
			case DAGGER_1H:
			case _1H_DAGGER:
				return new WeaponStats(1, 2, 1200, 100, 750, 750, 240, 0, 1500, 1, 0);
			case SWORD_1H:
			case _1H_SWORD:
				return new WeaponStats(1, 2, 1400, 50, 750, 800, 240, 0, 1500, 2, 0);
			case MACE_1H:
			case _1H_MACE:
				return new WeaponStats(1, 2, 1500, 50, 700, 800, 240, 0, 1500, 1, 0);
			case GUN_1H:
			case _1H_GUN:
				return new WeaponStats(1, 2, 1100, 50, 750, 0, 240, 0, 20000, 1, 0);
			case _1H_GAUNTLET:
				return new WeaponStats(1, 2, 1100, 100, 750, 900, 180, 0, 1500, 1, 0);
			case SWORD_2H:
			case _2H_SWORD:
				return new WeaponStats(1, 2, 2400, 50, 700, 850, 240, 0, 2000, 3, 0);
			case POLEARM_2H:
			case _2H_POLEARM:
				return new WeaponStats(1, 2, 2800, 50, 700, 850, 240, 0, 2500, 4, 0);
			case STAFF_2H:
			case _2H_STAFF:
				return new WeaponStats(1, 2, 2000, 50, 700, 850, 240, 0, 2000, 3, 0);
			case BOW:
				return new WeaponStats(1, 2, 2400, 50, 750, 0, 240, 0, 25000, 1, 0);
			case CANNON_2H:
			case _2H_CANNON:
				return new WeaponStats(1, 2, 2000, 50, 700, 0, 240, 0, 25000, 1, 0);
			case HARP_2H:
			case _2H_HARP:
				return new WeaponStats(1, 2, 2400, 50, 700, 0, 240, 0, 25000, 1, 0);
			case BOOK_2H:
			case _2H_BOOK:
				return new WeaponStats(1, 2, 2200, 0, 0, 0, 320, 700, 2500, 1, 0);
			case ORB_2H:
			case _2H_ORB:
				return new WeaponStats(1, 2, 2200, 0, 0, 0, 320, 700, 2500, 1, 0);
			case BLADE_2H:
			case _2H_BLADE:
				return new WeaponStats(1, 2, 2200, 50, 750, 850, 240, 0, 2000, 2, 0);
			case _2H_RUNESWORD:
				return new WeaponStats(1, 2, 2400, 50, 700, 850, 240, 0, 2000, 2, 0);
			case _2H_DIMENSIONSWORD:
				return new WeaponStats(1, 2, 1600, 50, 750, 800, 240, 0, 1500, 2, 0);
			default:
				return new WeaponStats(1, 2, 1500, 50, 700, 700, 240, 0, 1500, 1, 0);
		}
	}

	public int getTempExchangeTime() {
		return temExchangeTime;
	}

	public int getExpireTime() {
		return expireTime;
	}

	public final WeaponStats getWeaponStats() {
		if (weaponStats != null) {
			return weaponStats;
		}
		if (isWeapon()) {
			return getDefaultWeaponStats(weaponType);
		}
		return emptyWeaponStats;
	}

	public int getActivationCount() {
		return activationCount;
	}

	public final int getFuncPetId() {
		return funcPetId;
	}

	public void modifyMask(boolean apply, int filter) {
		if (apply)
			mask |= filter;
		else
			mask &= ~filter;
	}

	public boolean isStackable() {
		return this.maxStackCount > 1;
	}

	public boolean hasAreaRestriction() {
		return useLimits.getUseArea() != null;
	}

	public ZoneName getUseArea() {
		return useLimits.getUseArea();
	}

	public TradeinList getTradeinList() {
		return tradeinList;
	}

	public Acquisition getAcquisition() {
		return acquisition;
	}

	public Improvement getImprovement() {
		return improvement;
	}

	public ItemUseLimits getUseLimits() {
		return useLimits;
	}

	public ItemPurchableLimits getPurchableLimits() {
		return purchableLimits;
	}

	public List<Integer> getOwnershipWorld() {
		return useLimits.getOwnershipWorld();
	}

	public boolean isEnchantmentStone() {
		return category == ItemCategory.ENCHANTMENT;
	}

	public boolean isCloth() {
		return armorType != null && equipmentType == EquipType.ARMOR;
	}

	public boolean isAccessory() {
		return category == ItemCategory.EARRINGS ||
				category == ItemCategory.RINGS ||
				category == ItemCategory.NECKLACE ||
				category == ItemCategory.BELT ||
				category == ItemCategory.HELMET;
	}

	public boolean isQuestUpdateItem() {
		return isQuestUpdateItem;
	}

	public void setQuestUpdateItem(boolean value) {
		this.isQuestUpdateItem = value;
	}

	public int getExtraInventoryId() {
		if (extraInventory == null) {
			return -1;
		}
		return extraInventory.getId();
	}

	public String getTag() {
		return tag;
	}
}