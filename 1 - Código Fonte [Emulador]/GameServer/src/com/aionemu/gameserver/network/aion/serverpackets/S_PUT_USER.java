package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.model.Gender;
import com.aionemu.gameserver.model.actions.PlayerMode;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.items.GodStone;
import com.aionemu.gameserver.model.team.legion.LegionEmblemType;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.List;

public class S_PUT_USER extends AionServerPacket {
    private final Player player;
    private boolean enemy;

    public S_PUT_USER(Player player, boolean enemy) {
        this.player = player;
        this.enemy = enemy;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        Player activePlayer = con.getActivePlayer();
        if (activePlayer == null || player == null) {
            return;
        }
        PlayerCommonData pcd = player.getCommonData();
        final int raceId;
        if (player.getAdminNeutral() > 1 || activePlayer.getAdminNeutral() > 1) {
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

        // 3. State/Legion + padding + flags (9 bytes: offsets 37..48)
        writeD(0x0114a1c5);
        writeB(new byte[3]);
        writeC(enemy ? 0x00 : 0x26); // marcador não-inimigo
        writeC(raceId);
        writeC(pcd.getPlayerClass().getClassId());
        writeC(genderId);

        // 4. Heading + padding + tag (11 bytes: offsets 48..59)
        writeD(player.getHeading());
        writeB(new byte[6]);
        writeC(0x03);

        // 5. Nome do jogador em UTF-16LE com terminador nulo
        String nameFormat = "%s";
        StringBuilder sb = new StringBuilder(nameFormat);
        if (player.getClientConnection() != null && AdminConfig.ADMIN_TAG_ENABLE) {
            switch (player.getClientConnection().getAccount().getAccessLevel()) {
                case 1: nameFormat = sb.insert(0, AdminConfig.ADMIN_TAG_1.substring(0, AdminConfig.ADMIN_TAG_1.length() - 3)).toString(); break;
                case 2: nameFormat = sb.insert(0, AdminConfig.ADMIN_TAG_2.substring(0, AdminConfig.ADMIN_TAG_2.length() - 3)).toString(); break;
                case 3: nameFormat = sb.insert(0, AdminConfig.ADMIN_TAG_3.substring(0, AdminConfig.ADMIN_TAG_3.length() - 3)).toString(); break;
                case 4: nameFormat = sb.insert(0, AdminConfig.ADMIN_TAG_4.substring(0, AdminConfig.ADMIN_TAG_4.length() - 3)).toString(); break;
                case 5: nameFormat = sb.insert(0, AdminConfig.ADMIN_TAG_5.substring(0, AdminConfig.ADMIN_TAG_5.length() - 3)).toString(); break;
            }
        }
        writeS(String.format(nameFormat, player.getName()));

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
        int mask = 0;
        for (Item item : items) {
            mask |= item.getEquipmentSlot();
        }
        writeD(mask);

        // 8. Itens equipados (20 bytes cada)
        for (Item item : items) {
            writeD(item.getItemSkinTemplate().getTemplateId());
            GodStone godStone = item.getGodStone();
            writeD(godStone != null ? godStone.getItemId() : 0);
            writeD(item.getItemColor());
            writeB(new byte[8]);
        }

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
        writeC(player.getGender() == Gender.FEMALE ? 6 : 5);
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
        // FIM do bloco de rosto (52 bytes de writeC acima) + height f32 confirmado pelo PCAP
        // PCAP Kamidaki: face[50]=0x00, face[51]=0x02 (voice), height=1.2f (feminina Elyos)
        writeF(playerAppearance.getHeight()); // altura do personagem (f32, offset 231 no PCAP de 333 bytes)

        // 10. Movimento, Escala, Física (46 bytes)
        writeF(0.25f); // scale
        writeF(2.0f);  // gravity
        writeF(player.getGameStats().getMovementSpeedFloat()); // move speed
        writeH(player.getGameStats().getAttackSpeed().getBase());
        writeH(player.getGameStats().getAttackSpeed().getCurrent());
        writeC(player.getPortAnimation());
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
        writeD(player.getPlayerAccount().getAccountSielEnergy().getType().getId());
        writeC(0);
        writeD(0x01000000);
        writeD(0); // tail[1]
        writeD(0); // tail[2]
        writeD(0); // tail[3]
        writeD(0); // tail[4]
        writeD(0); // tail[5] — confirmado no PCAP: D[5] em offset 327 antes do H(300)
        writeH(300);

    }
}