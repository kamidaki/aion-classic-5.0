package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;

public class CM_PLAY_MOVIE_END extends AionClientPacket
{
	@SuppressWarnings("unused")
    private int type;
    @SuppressWarnings("unused")
    private int targetObjectId;
    @SuppressWarnings("unused")
    private int dialogId;
    private int movieId;
    @SuppressWarnings("unused")
    private int unk;

	public CM_PLAY_MOVIE_END(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}
	
	@Override
    protected void readImpl() {
        type = readC();
        targetObjectId = readD();
        dialogId = readD();
        movieId = readH();
        unk = readD();
    }
	
	@Override
    protected void runImpl() {
        Player player = getConnection().getActivePlayer();
        QuestEngine.getInstance().onMovieEnd(new QuestEnv(null, player, 0, 0), movieId);
        if (player.getPosition().isInstanceMap()) {
            player.getPosition().getWorldMapInstance().getInstanceHandler().onPlayMovieEnd(player, movieId);
        } else {
            player.getPosition().getWorld().getWorldMap(player.getWorldId()).getWorldHandler().onPlayMovieEnd(player, movieId);
        }
    }
}