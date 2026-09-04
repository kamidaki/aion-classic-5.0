package com.aionemu.gameserver.services.player;

import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.BindPointPosition;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.S_PUT_USER;
import com.aionemu.gameserver.network.aion.serverpackets.S_WIELD;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Servico de Troca de Faccao / Raca (Elyos <-> Asmodian) para o Classic 5.0.
 */
public class FactionChangeService {

    private static final Logger log = LoggerFactory.getLogger(FactionChangeService.class);
    private static final FactionChangeService instance = new FactionChangeService();

    public static FactionChangeService getInstance() {
        return instance;
    }

    public boolean changeFaction(Player player, Race targetRace) {
        if (player == null || targetRace == null || targetRace == Race.NONE) {
            return false;
        }
        if (player.getRace() == targetRace) {
            PacketSendUtility.sendMessage(player, "Voce ja pertence a faccao " + targetRace.name() + "!");
            return false;
        }

        // Troca de raca nos dados comuns
        player.getCommonData().setRace(targetRace);
        DAOManager.getDAO(PlayerDAO.class).storePlayer(player);

        // Realocar ponto de retorno / Bind Point para a capital da nova faccao
        int targetWorldId;
        float x, y, z;
        byte heading;

        if (targetRace == Race.ELYOS) {
            targetWorldId = 110010000; // Sanctum
            x = 1322.0f;
            y = 1511.0f;
            z = 568.0f;
            heading = 0;
        } else {
            targetWorldId = 120010000; // Pandaemonium
            x = 1679.0f;
            y = 1400.0f;
            z = 195.0f;
            heading = 0;
        }

        player.setBindPoint(new BindPointPosition(targetWorldId, x, y, z, heading));

        // Notificar cliente e atualizar aparencia
        PacketSendUtility.sendPacket(player, new S_PUT_USER(player, false));
        PacketSendUtility.sendPacket(player, new S_WIELD(player.getObjectId(), player.getEquipment().getEquippedItemsWithoutStigma()));
        PacketSendUtility.sendMessage(player, "[Troca de Faccao] Sua faccao foi alterada para " + targetRace.name() + " com sucesso!");

        // Teleportar para a nova capital
        TeleportService.teleportTo(player, targetWorldId, x, y, z, heading);

        log.info("[FactionChangeService] Jogador " + player.getName() + " alterou faccao para " + targetRace.name());
        return true;
    }
}
