package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.stats.container.PlayerLifeStats;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceMember;
import com.aionemu.gameserver.model.team.common.legacy.PlayerAllianceEvent;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SkillTargetSlot;
import com.aionemu.gameserver.world.WorldPosition;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ALLIANCE_MEMBER_INFO extends AionServerPacket {

	private Player player;
	private PlayerAllianceEvent event;
	private final int allianceId;
	private final int objectId;
	private final int slot;
	private List<Effect> abnormalEffects;

	public SM_ALLIANCE_MEMBER_INFO(PlayerAllianceMember member, PlayerAllianceEvent event, int slot) {
		this.player = member.getObject();
		this.event = event;
		this.allianceId = member.getAllianceId();
		this.objectId = member.getObjectId();
		this.slot = slot;
		switch (event) {
			case JOIN:
			case ENTER:
			case ENTER_OFFLINE:
			case UPDATE:
			case RECONNECT:
			case APPOINT_VICE_CAPTAIN: // Unused maybe...
			case DEMOTE_VICE_CAPTAIN:
			case APPOINT_CAPTAIN:
				abnormalEffects = player.getEffectController().getAbnormalEffectsToShow();
				break;
			case UPDATE_EFFECTS:
				abnormalEffects = player.getEffectController().getAbnormalEffectsToTargetSlot(slot);
				break;
		}
	}

	public SM_ALLIANCE_MEMBER_INFO(PlayerAllianceMember member, PlayerAllianceEvent event) {
		this(member, event, 0);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		PlayerCommonData pcd = player.getCommonData();
		WorldPosition wp = player.getPosition();

		/**
		 * Required so that when member is disconnected, and his playerAllianceGroup slot is changed, he will continue to appear as disconnected to the
		 * alliance.
		 */
		if (event == PlayerAllianceEvent.ENTER && !player.isOnline())
			event = PlayerAllianceEvent.ENTER_OFFLINE;

		writeD(event == PlayerAllianceEvent.LEAVE || event == PlayerAllianceEvent.BANNED ? 0 : allianceId); // 5.0: saída vai com grupo 0
		writeD(objectId);
		if (player.isOnline()) {
			PlayerLifeStats pls = player.getLifeStats();
			writeD(pls.getMaxHp());
			writeD(pls.getCurrentHp());
			writeD(pls.getMaxMp());
			writeD(pls.getCurrentMp());
			writeD(pls.getMaxFp());
			writeD(pls.getCurrentFp());
		} else {
			writeD(0);
			writeD(0);
			writeD(0);
			writeD(0);
			writeD(0);
			writeD(0);
		}

		writeD(0);// unk 3.5
		writeD(wp.getMapId());
		writeD(wp.getMapId() + wp.getInstanceId() - 1);
		writeF(wp.getX());
		writeF(wp.getY());
		writeF(wp.getZ());
		writeC(pcd.getPlayerClass().getClassId());
		writeC(pcd.getGender().getGenderId());
		writeC(pcd.getLevel());
		writeC(event.getId());
		writeC(1); // unk, always 0x01 since removal of Sarpan & Tiamaranta
		writeC(player.getFlyState()); // isFly
		writeC(0x0);
		// 5.0: os mesmos 9 bytes do SM_GROUP_MEMBER_INFO antes do nome, em todo evento
		writeC(0x00);
		writeD(0x00);
		writeD(0x00);
		switch (event) {
			case LEAVE:
			case BANNED:
			case MOVEMENT:
			case DISCONNECTED:
				break;
			case UPDATE_EFFECTS:
				writeD(0x00); // unk
				writeD(0x00); // unk
				writeEffects(slot);
				break;
			case JOIN:
			case ENTER:
			case ENTER_OFFLINE:
			case UPDATE:
			case RECONNECT:
			case APPOINT_VICE_CAPTAIN: // Unused maybe...
			case DEMOTE_VICE_CAPTAIN:
			case APPOINT_CAPTAIN:
				writeS(pcd.getName());
				writeD(0x00); // unk
				writeD(0x00); // unk
				if (player.isOnline()) {
					writeEffects(SkillTargetSlot.FULLSLOTS);
				} else {
					writeH(0);
				}
				break;
			case MEMBER_GROUP_CHANGE:
				writeS(pcd.getName());
				break;
		}
	}

	/**
	 * Mesmo formato do SM_GROUP_MEMBER_INFO: efeitos de 23 b (S_ABNORMAL_STATUS do 5.0) e um D por slot.
	 */
	private void writeEffects(int slots) {
		writeC(slots);
		writeH(abnormalEffects.size());
		for (Effect effect : abnormalEffects) {
			writeD(effect.getEffectorId());
			writeD(SM_ABNORMAL_EFFECT.effectorTemplateId(effect.getEffector()));
			writeH(effect.getSkillId());
			writeC(effect.getSkillLevel());
			writeC(effect.getTargetSlot().ordinal());
			writeD(effect.getRemainingTimeToDisplay());
			writeD(effect.getCarvedSignet());
			writeH(0);
			writeC(0);
		}
		for (int i = 0; i < SkillTargetSlot.values().length; i++)
			writeD(0x00);
	}

}
