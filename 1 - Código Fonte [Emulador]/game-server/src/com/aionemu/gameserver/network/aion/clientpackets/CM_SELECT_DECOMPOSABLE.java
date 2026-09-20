package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.List;
import java.util.Set;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.actions.DecomposeAction;
import com.aionemu.gameserver.model.templates.item.actions.DecomposeAction.SelectableReward;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_USAGE_ANIMATION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SECONDARY_SHOW_DECOMPOSABLE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Escolha na janela de uma caixa selectable (C_SELECT_DISASSEMBLY_ITEM, 0xA9 na 5.0): [D obj][D 0][C indice].
 * <p>
 * Fluxo da subida 1-60 oficial (wrap_newc_supply_enchant_*): S_USE_ITEM com o casting_delay da caixa; no fim, S_USE_ITEM de fim, "usou",
 * "desembrulhou", a caixa sai, S_SELECT_DISASSEMBLY_ITEM_RESULT (0x105) [obj][0][0] e o item escolhido entra. Se o cast e interrompido: "cancelado",
 * S_SELECT_DISASSEMBLY_ITEM_RESULT [0][0][3] e S_USE_ITEM [end=3]; a janela nao volta (o jogador usa a caixa de novo).
 *
 * @author Lost Academy Team & Durak
 */
public class CM_SELECT_DECOMPOSABLE extends AionClientPacket {

	private int objectId;
	@SuppressWarnings("unused")
	private int unk;
	private int index;

	public CM_SELECT_DECOMPOSABLE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		objectId = readD();
		unk = readD();
		index = readUC();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || player.isDead() || !player.isSpawned())
			return;
		DecomposeAction.selectionClosed(player);
		Item item = player.getInventory().getItemByObjId(objectId);
		if (item == null)
			return;
		List<SelectableReward> rewards = DecomposeAction.getSelectableRewards(player, item.getItemId());
		// hasTask nao serve: o ITEM_USE de qualquer uso anterior ja concluido continua no mapa e bloquearia a escolha para sempre
		if (rewards == null || index >= rewards.size() || player.getController().hasScheduledTask(TaskId.ITEM_USE) || player.hasCooldown(item)) {
			reject(player);
			return;
		}
		if (player.getInventory().isFull()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_DECOMPOSE_ITEM_INVENTORY_IS_FULL());
			reject(player);
			return;
		}
		SelectableReward reward = rewards.get(index);
		DecomposeAction.castThen(player, item, DecomposeAction.CANCEL_END_CODE, () -> finish(player, item, reward), () -> reject(player));
	}

	/** Resultado "cancelado" (objeto 0), o mesmo que o oficial manda quando a barra de uso e interrompida: fecha a espera do cliente. */
	private static void reject(Player player) {
		PacketSendUtility.sendPacket(player, new SM_SECONDARY_SHOW_DECOMPOSABLE(0, SM_SECONDARY_SHOW_DECOMPOSABLE.CANCELED));
	}

	private static void finish(Player player, Item item, SelectableReward reward) {
		if (player.getInventory().getItemByObjId(item.getObjectId()) == null) {
			reject(player);
			return;
		}
		PacketSendUtility.broadcastPacket(player, new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), item.getObjectId(), item.getItemId(), 0, 1, 0),
			true);
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_USE_ITEM(item.getL10n()));
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_UNCOMPRESS_COMPRESSED_ITEM_SUCCEEDED(item.getL10n()));
		if (!player.getInventory().decreaseByObjectId(item.getObjectId(), 1)) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_DECOMPOSE_ITEM_NO_TARGET_ITEM());
			reject(player);
			return;
		}
		player.startCooldown(item);
		PacketSendUtility.sendPacket(player, new SM_SECONDARY_SHOW_DECOMPOSABLE(item.getObjectId(), SM_SECONDARY_SHOW_DECOMPOSABLE.OK));
		int count = Rnd.get(reward.minCount(), reward.maxCount());
		ItemService.addItem(player, reward.itemId(), count, true, reward.predicate());
	}

}
