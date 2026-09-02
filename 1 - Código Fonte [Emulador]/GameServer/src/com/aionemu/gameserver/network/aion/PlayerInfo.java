package com.aionemu.gameserver.network.aion;

import com.aionemu.gameserver.model.Gender;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.items.GodStone;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Timestamp;

import java.util.List;

public abstract class PlayerInfo extends AionServerPacket {

    private static Logger log = LoggerFactory.getLogger(PlayerInfo.class);

    protected PlayerInfo() {
    }

    /**
     * Tamanho da area de equipamento dentro do registro de personagem do Classic 5.0:
     * 20 slots de 17 bytes, ocupando os offsets 268..608. Confirmado na captura oficial.
     */
    public static final int AREA_EQUIPAMENTO = 340;

    /** Tamanho total do registro de personagem no Classic 5.0, medido na captura. */
    public static final int REGISTRO_LEN = 766;

    protected void writePlayerInfo(PlayerAccountData accPlData) {
        PlayerCommonData pbd = accPlData.getPlayerCommonData();
        final int raceId = pbd.getRace().getRaceId();
        final int genderId = pbd.getGender().getGenderId();
        final PlayerAppearance playerAppearance = accPlData.getAppereance();
        writeD(pbd.getPlayerObjId());
        writeS(pbd.getName(), 52);
        writeD(genderId);
        writeD(raceId);
        writeD(pbd.getPlayerClass().getClassId());
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
        if (pbd.getGender() == Gender.FEMALE) {
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
        writeC(playerAppearance.getShoulderSize()); // shoulderSize
        writeC(playerAppearance.getTorso());
        writeC(playerAppearance.getChest());
        writeC(playerAppearance.getWaist());
        writeC(playerAppearance.getHips());
        writeC(playerAppearance.getArmThickness());
        writeC(playerAppearance.getHandSize());
        writeC(playerAppearance.getLegThickness());
        writeC(playerAppearance.getFootSize());
        writeC(playerAppearance.getFacialRate());
        writeC(0x00); // 0x00
        writeC(playerAppearance.getArmLength()); // armLength
        writeC(playerAppearance.getLegLength()); // legLength
        writeC(playerAppearance.getShoulders());
        writeC(playerAppearance.getFaceShape());
        writeC(0x00); // always 0 may be acessLevel
        writeC(0x00); // always 0 - unk
        writeC(0x00);
        writeF(playerAppearance.getHeight());
        int raceSex = 100000 + raceId * 2 + genderId;
        writeD(raceSex);
        writeD(pbd.getPosition().getMapId());
        writeF(pbd.getPosition().getX());
        writeF(pbd.getPosition().getY());
        writeF(pbd.getPosition().getZ());
        writeD(pbd.getPosition().getHeading());
        writeD(pbd.getLevel());
        writeD(pbd.getTitleId());
        if (accPlData.isLegionMember()) {
            writeD(accPlData.getLegion().getLegionId());
            writeS(accPlData.getLegion().getLegionName(), 82);
        } else {
            writeD(0x00);
            writeB(new byte[82]);
        }
        writeH(accPlData.isLegionMember() ? 0x01 : 0x00);
        // Offset 264 do registro. Na captura oficial 5.0 este campo traz um timestamp
        // real, nunca zero. O campo vai em segundos, como ja fazem Player.getLastOnline()
        // e Friend.getLastOnline() -- escrever getTime() cru mandava milissegundos, que
        // estouram o int.
        //
        // Offset 264 do registro: timestamp de ultima saida do mundo em segundos.
        // Para personagens recem-criados (lastOnline == null), deve ser 0 (conforme 4.8 Retail).
        // Se mandar timestamp recente (como creationDate ou now), o cliente calcula que o personagem
        // acabou de deslogar e impoe a trava de reconexao ("Preparando para reconectar 15s").
        Timestamp lastOnline = pbd.getLastOnline();
        writeD(lastOnline == null ? 0 : (int) (lastOnline.getTime() / 1000));

        int itemsDataSize = 0;
        List<Item> items = accPlData.getEquipment();
        for (Item item : items) {
            // Area de equipamento do registro 5.0: offsets 268..608 = 340 bytes,
            // 20 slots de 17 bytes (tipo + itemId + 12). Medido na captura oficial
            // (01_Login_World_Elyos): as entradas aparecem em 268, 285, 302, 319, 336,
            // 353, 370, 387, 404, 421 -- passo 17 -- e o proximo campo do registro,
            // o deletionTime, so comeca em 608. Estava reservando 272 (16 slots).
            if (itemsDataSize >= AREA_EQUIPAMENTO) {
                break;
            }
            ItemTemplate itemTemplate = item.getItemTemplate();
            if (itemTemplate == null) {
                continue;
            }
            long slot = item.getEquipmentSlot();
            if (slot == 393216 || slot == 131072 || slot == 262144) {
                continue;
            }
            if (itemTemplate.isArmor() || itemTemplate.isWeapon()) {
                if (itemTemplate.getItemSlot() <= ItemSlot.PANTS.getSlotIdMask()) {
                    writeC(slot == 2 || slot == 64 || slot == 256 ? 2 : 1);
                    writeD(item.getItemSkinTemplate().getTemplateId());
                    GodStone godStone = item.getGodStone();
                    writeD(godStone != null ? godStone.getItemId() : 0);
                    writeD(item.getItemColor());
                    writeD(0);//2.8
                    itemsDataSize += 17;
                }
            }
        }
        byte[] stupidNc = new byte[AREA_EQUIPAMENTO - itemsDataSize];
        writeB(stupidNc);
        // offset 608 do registro
        writeD(accPlData.getDeletionTimeInSeconds());
    }
}