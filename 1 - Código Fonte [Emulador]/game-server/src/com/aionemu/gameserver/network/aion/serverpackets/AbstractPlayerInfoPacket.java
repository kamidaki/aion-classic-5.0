package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.Gender;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.items.GodStone;
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
		writeC(playerAppearance.getHair());
		writeC(playerAppearance.getDeco());
		writeC(playerAppearance.getTattoo());
		writeC(playerAppearance.getFaceContour());
		writeC(playerAppearance.getExpression());
		if (pcd.getGender() == Gender.FEMALE) {
			writeC(6);
		} else {
			writeC(5);
		}
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
		writeD(accPlData.getDeletionTimeInSeconds());
	}

	protected void writeEquippedItems(List<Item> items) {
		int mask = 0;
		if (items != null) {
			for (Item item : items) {
				mask |= item.getEquipmentSlot();
			}
		}
		writeD(mask);
		for (int i = 0; i < 32; i++) {
			int bit = 1 << i;
			if ((mask & bit) != 0) {
				Item matchedItem = null;
				if (items != null) {
					for (Item item : items) {
						if ((item.getEquipmentSlot() & bit) != 0) {
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

