package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.items.GodStone;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.LegionService;

/**
 * Classic 5.0 AbstractPlayerInfoPacket
 */
public abstract class AbstractPlayerInfoPacket extends AionServerPacket {

	public static final int CHARNAME_MAX_LENGTH = 25;
	public static final int AREA_EQUIPAMENTO = 340;
	public static final int REGISTRO_LEN = 766;

	protected void writePlayerInfo(PlayerAccountData accPlData, AionConnection con) {
		PlayerCommonData pcd = accPlData.getPlayerCommonData();
		int playerId = pcd.getPlayerObjId();
		LegionMember legionMember = LegionService.getInstance().getLegionMember(pcd);
		PlayerAppearance playerAppearance = accPlData.getAppearance();

		writeD(playerId);
		writeS(pcd.getName(), CHARNAME_MAX_LENGTH);
		writeD(pcd.getGender().getGenderId());
		writeD(pcd.getRace().getRaceId());
		writeD(pcd.getPlayerClass().getClassId());
		writeD(playerAppearance.getVoice());
		writeD(playerAppearance.getSkinRGB());
		writeD(playerAppearance.getHairRGB());
		writeD(playerAppearance.getEyeRGB());
		writeD(playerAppearance.getLipRGB());
		writeC(playerAppearance.getFace());
		writeH(playerAppearance.getHair()); // H, como no S_PUT_USER (AionServerPacket.writeAppearance)
		writeC(playerAppearance.getTattoo());
		writeC(playerAppearance.getFaceContour());
		writeC(playerAppearance.getExpression());
		writeC(playerAppearance.getFaceExpression());
		writeC(playerAppearance.getJawLine());
		writeC(playerAppearance.getForehead());
		writeC(playerAppearance.getEyeHeight());
		writeC(playerAppearance.getEyeSpace());
		writeC(playerAppearance.getEyeWidth());
		writeC(playerAppearance.getEyeSize());
		writeC(playerAppearance.getEyeShape());
		writeC(playerAppearance.getEyeAngle());
		writeC(playerAppearance.getBrowHeight());
		writeC(playerAppearance.getBrowAngle());
		writeC(playerAppearance.getBrowShape());
		writeC(playerAppearance.getNose());
		writeC(playerAppearance.getNoseBridge());
		writeC(playerAppearance.getNoseWidth());
		writeC(playerAppearance.getNoseTip());
		writeC(playerAppearance.getCheek());
		writeC(playerAppearance.getLipHeight());
		writeC(playerAppearance.getMouthSize());
		writeC(playerAppearance.getLipSize());
		writeC(playerAppearance.getSmile());
		writeC(playerAppearance.getLipShape());
		writeC(playerAppearance.getJawHeigh());
		writeC(playerAppearance.getChinJut());
		writeC(playerAppearance.getEarShape());
		writeC(playerAppearance.getHeadSize());
		writeC(playerAppearance.getNeck());
		writeC(playerAppearance.getNeckLength());
		writeC(playerAppearance.getShoulderSize());
		writeC(playerAppearance.getTorso());
		writeC(playerAppearance.getChest());
		writeC(playerAppearance.getWaist());
		writeC(playerAppearance.getHips());
		writeC(playerAppearance.getArmThickness());
		writeC(playerAppearance.getHandSize());
		writeC(playerAppearance.getLegThickness());
		writeC(playerAppearance.getFootSize());
		writeC(playerAppearance.getFacialRate());
		writeC(0x00);
		writeC(playerAppearance.getArmLength());
		writeC(playerAppearance.getLegLength());
		writeC(playerAppearance.getShoulders());
		writeC(playerAppearance.getFaceShape());
		writeC(0x00);
		writeC(0x00);
		writeC(0x00);
		writeF(playerAppearance.getHeight());
		int raceSex = 100000 + pcd.getRace().getRaceId() * 2 + pcd.getGender().getGenderId();
		writeD(raceSex);
		writeD(pcd.getMapId());
		writeF(pcd.getX());
		writeF(pcd.getY());
		writeF(pcd.getZ());
		writeD(pcd.getHeading());
		writeD(pcd.getLevel());
		writeD(pcd.getTitleId());
		if (legionMember != null) {
			writeD(legionMember.getLegion().getLegionId());
			writeS(legionMember.getLegion().getName(), 40);
		} else {
			writeD(0);
			writeB(new byte[82]);
		}
		writeH(legionMember != null ? 1 : 0);
		writeD(pcd.getLastOnlineEpochSeconds());

		int itemsDataSize = 0;
		List<PlayerAccountData.VisibleItem> items = accPlData.getVisibleItems();
		if (items != null) {
			for (PlayerAccountData.VisibleItem item : items) {
				if (itemsDataSize >= AREA_EQUIPAMENTO) {
					break;
				}
				writeC(item.slotType());
				writeD(item.itemId());
				writeD(item.godStoneId());
				writeD(item.color() != null ? item.color() : 0);
				writeD(0);
				itemsDataSize += 17;
			}
		}
		byte[] stupidNc = new byte[AREA_EQUIPAMENTO - itemsDataSize];
		writeB(stupidNc);
		// 5.0: data de criação antes do tempo de exclusão (S 0xC7 e S 0xC8 oficiais: offset 608 da entrada, crescente na ordem de criação). Sem
		// ela tudo depois ficava 4 b adiantado, e o cliente lia o display/deny como tempo de exclusão e escondia quem tinha capacete/capa
		// escondido (20/10).
		writeD(pcd.getCreationDate() == null ? 0 : (int) (pcd.getCreationDate().getTime() / 1000));
		writeD(accPlData.getDeletionTimeInSeconds());
	}

	private long getAppearanceSlotMask(Item item) {
		if (item == null || item.getItemTemplate() == null) {
			return 0L;
		}
		long slot = item.getEquipmentSlot();
		if (item.getItemTemplate().isTwoHandWeapon()) {
			// Armas de duas mãos ocupam apenas MAIN_HAND na máscara de aparência 3D.
			// O bit SUB_HAND faria o cliente Classic 5.0 renderizar uma segunda arma na mão esquerda.
			if ((slot & ItemSlot.MAIN_HAND.getSlotIdMask()) != 0) {
				return ItemSlot.MAIN_HAND.getSlotIdMask();
			}
			return 0L;
		}
		if ((slot & ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask()) != 0) {
			return 0L;
		}
		return slot;
	}

	protected void writeEquippedItems(List<Item> items) {
		int mask = 0;
		if (items != null) {
			for (Item item : items) {
				mask |= (int) getAppearanceSlotMask(item);
			}
		}
		writeD(mask);
		for (int i = 0; i < 32; i++) {
			int bit = 1 << i;
			if ((mask & bit) != 0) {
				Item matchedItem = null;
				if (items != null) {
					for (Item item : items) {
						if ((getAppearanceSlotMask(item) & bit) != 0) {
							matchedItem = item;
							break;
						}
					}
				}
				if (matchedItem != null) {
					writeD(matchedItem.getItemSkinTemplate() != null ? matchedItem.getItemSkinTemplate().getTemplateId() : matchedItem.getItemId());
					GodStone godStone = matchedItem.getGodStone();
					writeD(godStone != null ? godStone.getItemId() : 0);
					writeD(matchedItem.getItemColor() != null ? matchedItem.getItemColor() : 0);
					writeB(new byte[8]);
				} else {
					writeB(new byte[20]);
				}
			}
		}
	}
}

