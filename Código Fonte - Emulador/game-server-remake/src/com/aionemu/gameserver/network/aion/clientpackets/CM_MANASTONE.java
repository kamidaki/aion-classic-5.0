package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.actions.EnchantItemAction;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.EnchantService;
import com.aionemu.gameserver.services.ClassicEnchantService;
import com.aionemu.gameserver.services.StigmaService;
import com.aionemu.gameserver.services.item.ItemSocketService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_MANASTONE extends AionClientPacket {

	private static final int SOCKET_FLAGS = Item.MAX_BASIC_STONES;

	private int actionType;
	private int targetFusedSlot;
	private int stoneUniqueId;
	private int targetItemUniqueId;
	private int supplementUniqueId;
	private List<Integer> slotsToClear;

	/**
	 * @param opcode
	 */
	public CM_MANASTONE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		actionType = readUC();
		targetFusedSlot = readUC();
		targetItemUniqueId = readD();
		switch (actionType) {
			case 1:
			case 2:
			case 4:
			case 8:
				stoneUniqueId = readD();
				supplementUniqueId = readD();
				if (actionType == 1) {
					// The 5.0 enchant window appends 24 bytes (38 total), including the client cost preview.
					// Costs and material counts are always taken from canonical server rules.
					while (getRemainingBytes() > 0) readUC();
				}
				break;
			case 3:
				// Classic 5.0 removal window (game menu, no NPC). Body measured on the official server is 26 bytes:
				// the 6 read above, an unused int, then a flag per socket slot, of which only MAX_BASIC_STONES can be set.
				readD();
				slotsToClear = new ArrayList<>();
				for (int slot = 0; slot < SOCKET_FLAGS; slot++)
					if (readUC() != 0)
						slotsToClear.add(slot);
				break;
		}
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || player.isTrading() || player.isDead()) return;

		switch (actionType) {
			case 1: // enchant stone
			case 2: { // add manastone
				Item stone = player.getInventory().getItemByObjId(stoneUniqueId);
				if (stone == null)
					return;
				Item targetItem = player.getEquipment().getEquippedItemByObjId(targetItemUniqueId);
				if (targetItem == null && (targetItem = player.getInventory().getItemByObjId(targetItemUniqueId)) == null) {
					sendPacket(actionType == 1 ? SM_SYSTEM_MESSAGE.STR_ENCHANT_ITEM_NO_TARGET_ITEM() : SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_OPTION_NO_TARGET_ITEM());
					return;
				}

				if (actionType == 1 && stone.getItemTemplate().isEnchantEssence()) {
					if (supplementUniqueId == 0) ClassicEnchantService.enchant(player, stone, targetItem);
				} else if (stone.getItemTemplate().isStigma() && targetItem.getItemTemplate().isStigma()) {
					StigmaService.chargeStigma(player, targetItem, stone);
				} else {
					boolean isFusionSlot = (targetFusedSlot != 1); // the 5.0 client sends 1 for the main item (seen on armor)
					if (targetItem.hasFusionedItem() && targetItem.getFusionedItem() != null && targetItem.getFusionedItem().getObjectId() == targetItemUniqueId) {
						isFusionSlot = true;
					}
					EnchantItemAction action = new EnchantItemAction();
					if (action.canAct(player, stone, targetItem)) {
						Item supplement = player.getInventory().getItemByObjId(supplementUniqueId);
						if (supplement != null) {
							if (supplement.getItemId() / 100000 != 1661) // suppliment id check
								return;
						}
						action.act(player, stone, targetItem, supplement, isFusionSlot ? 1 : 0);
					}
				}
				break;
			}
			case 3: { // remove manastones
				Item targetItem = player.getEquipment().getEquippedItemByObjId(targetItemUniqueId);
				if (targetItem == null && (targetItem = player.getInventory().getItemByObjId(targetItemUniqueId)) == null) {
					sendPacket(SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_NOT_FIND());
					return;
				}
				boolean isFusionSlot = targetFusedSlot != 1 || (targetItem.hasFusionedItem() && targetItem.getFusionedItem() != null
					&& targetItem.getFusionedItem().getObjectId() == targetItemUniqueId);
				ItemSocketService.clearManastones(player, targetItem, isFusionSlot, slotsToClear);
				break;
			}
			case 4: // add godstone
				Item weaponItem = player.getInventory().getItemByObjId(targetItemUniqueId);
				if (weaponItem == null) {
					boolean isEquipped = player.getEquipment().getEquippedItemByObjId(targetItemUniqueId) != null;
					sendPacket(isEquipped ? SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CANNOT_GIVE_PROC_TO_EQUIPPED_ITEM() : SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_NO_TARGET_ITEM());
					return;
				}
				ItemSocketService.socketGodstone(player, weaponItem, stoneUniqueId);
				break;
			case 8: // amplification
				EnchantService.amplifyItem(player, targetItemUniqueId, supplementUniqueId, stoneUniqueId);
				break;
		}
	}

}
