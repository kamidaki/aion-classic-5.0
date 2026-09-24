package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.Gender;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.CustomPlayerState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.items.GodStone;
import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_PLAYER_INFO extends AbstractPlayerInfoPacket {

	private final Player player;
	private boolean enemy;

	public SM_PLAYER_INFO(Player player) {
		this(player, false);
	}

	public SM_PLAYER_INFO(Player player, boolean enemy) {
		this.player = player;
		this.enemy = enemy;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		Player activePlayer = con.getActivePlayer();
		if (activePlayer == null || player == null)
			return;

		PlayerCommonData pcd = player.getCommonData();
		final int raceId;
		if (player.isInCustomState(CustomPlayerState.NEUTRAL_TO_ALL_PLAYERS) || activePlayer.isInCustomState(CustomPlayerState.NEUTRAL_TO_ALL_PLAYERS)) {
			raceId = activePlayer.getRace().getRaceId();
		} else if (activePlayer.isEnemy(player)) {
			raceId = (activePlayer.getRace().getRaceId() == 0 ? 1 : 0);
		} else {
			raceId = player.getRace().getRaceId();
		}
		final int genderId = pcd.getGender().getGenderId();
		final PlayerAppearance playerAppearance = player.getPlayerAppearance();

		// 1. Coordenadas 3D (X, Y, Z) e IDs base (24 bytes)
		writeF(player.getX());
		writeF(player.getY());
		writeF(player.getZ());
		writeD(player.getObjectId());
		writeD(pcd.getTemplateId());
		int model = player.getTransformModel().getModelId();
		writeD(model != 0 ? model : pcd.getTemplateId());

		// 2. 13 bytes padding (offsets 24..37)
		writeB(new byte[13]);

		// 3. Offsets 37..48 (constantes e marcadores Classic 5.0)
		writeB(new byte[3]);
		writeC(0x01);
		writeB(new byte[3]);
		writeC(enemy ? 0x00 : 0x26); // marcador não-inimigo
		writeC(raceId);
		writeC(pcd.getPlayerClass().getClassId());
		writeC(genderId);

		// 4. Offsets 48..59 (state e heading nos offsets medidos em captura oficial 5.0)
		writeC(player.getState());
		writeB(new byte[9]);
		writeC(player.getHeading());

		// 5. Nome do jogador em UTF-16LE com terminador nulo
		writeS(player.getName(true));

		// 6. Bloco de Título / Mentoring / Casting (16 bytes)
		writeH(pcd.getTitleId());
		writeH(player.getCommonData().isHaveMentorFlag() ? 1 : 0);
		writeH(player.getCastingSkillId());
		writeB(new byte[10]);

		// 7. Padding (2B) + %HP (4B) + Máscara de Equipamentos (4B) (10 bytes)
		writeH(0);
		int maxHp = player.getLifeStats().getMaxHp();
		int currHp = player.getLifeStats().getCurrentHp();
		writeD(maxHp > 0 ? (100 * currHp / maxHp) : 100);

		List<Item> items = player.getEquipment().getEquippedItemsWithoutStigma();
		writeEquippedItems(items);

		// 9. Bloco de aparência (72 bytes)
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
		writeC(pcd.getGender() == Gender.FEMALE ? 6 : 5);
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
		writeC(playerAppearance.getVoice());
		writeF(playerAppearance.getHeight());

		// 10. Movimento, Escala, Física (46 bytes)
		writeF(0.25f); // scale
		writeF(2.0f);  // gravity
		writeF(player.getGameStats().getMovementSpeedFloat()); // move speed
		writeH(player.getGameStats().getAttackSpeed().getBase());
		writeH(player.getGameStats().getAttackSpeed().getCurrent());
		writeC(player.getPortAnimationId());
		writeH(0); // store message empty
		writeF(0); // move vector X
		writeF(0); // move vector Y
		writeF(0); // move vector Z
		writeF(player.getX());
		writeF(player.getY());
		writeF(player.getZ());
		writeC(0x00); // move mask

		// 11. Bloco de cauda oficial (54 bytes)
		writeC(player.getVisualState());
		writeS(player.getCommonData().getNote());
		writeH(player.getLevel());
		writeH(player.getPlayerSettings().getDisplay());
		writeH(player.getPlayerSettings().getDeny());
		writeH(player.getAbyssRank().getRank().getId());
		writeH(0x00);
		writeD(player.getTarget() == null ? 0 : player.getTarget().getObjectId());
		writeC(0);
		writeD(player.getCurrentTeamId());
		writeC(player.isMentor() ? 1 : 0);
		writeD(0);
		writeC(0);
		writeD(0x01000000);
		writeD(0);
		writeD(0);
		writeD(0);
		writeD(0);
		writeD(0);
		writeH(300);
	}
}
