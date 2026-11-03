package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.ItemStoneListDAO;
import com.aionemu.gameserver.dao.PlayerAppearanceDAO;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STATUS_OTHER;
import com.aionemu.gameserver.network.aion.serverpackets.SM_VIEW_PLAYER_DETAILS;
import com.aionemu.gameserver.services.ranking.RankingService;
import com.aionemu.gameserver.world.World;

/**
 * Lupa do ranking de Combat Talent, C 0x133 [D objeto][D aba][D posição][D classe ou -1] (16 b).
 * <p>
 * Capturas outros 2026-09-21 06:10 e 06_Sistemas_Novos 2026-10-20 02:17/02:23: a resposta é o S 0x02 (S_STATUS_OTHER) e o equipamento sem
 * estigmas em S 0x40 com C 0x10. Os ranqueados costumam estar offline, então os dados vêm do banco quando o jogador não está no mundo.
 */
public class CM_RANKING_PLAYER_DETAIL extends AionClientPacket {

	private int targetObjectId;
	private int rankingType;

	public CM_RANKING_PLAYER_DETAIL(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		targetObjectId = readD();
		rankingType = readD();
		readD(); // posição
		readD(); // classe da aba, ou -1
	}

	@Override
	protected void runImpl() {
		if (RankingService.getInstance().getEntry(rankingType, targetObjectId) == null)
			return;
		Player target = World.getInstance().getPlayer(targetObjectId);
		if (target != null) {
			sendPacket(new SM_STATUS_OTHER(target));
			SM_VIEW_PLAYER_DETAILS.of(targetObjectId, SM_VIEW_PLAYER_DETAILS.SOURCE_RANKING, target.getEquipment().getEquippedItemsWithoutStigma())
				.forEach(this::sendPacket);
			return;
		}
		PlayerCommonData pcd = PlayerDAO.loadPlayerCommonData(targetObjectId);
		PlayerAppearance appearance = PlayerAppearanceDAO.load(targetObjectId);
		if (pcd == null || appearance == null)
			return;
		List<Item> equipped = new ArrayList<>();
		for (Item item : InventoryDAO.loadItems(targetObjectId, StorageType.CUBE))
			if (item.isEquipped() && !ItemSlot.isStigma(item.getEquipmentSlot()))
				equipped.add(item);
		ItemStoneListDAO.load(equipped);
		sendPacket(new SM_STATUS_OTHER(pcd, appearance));
		SM_VIEW_PLAYER_DETAILS.of(targetObjectId, SM_VIEW_PLAYER_DETAILS.SOURCE_RANKING, equipped).forEach(this::sendPacket);
	}
}
