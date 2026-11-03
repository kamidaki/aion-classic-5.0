package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.CustomPlayerState;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_PLAY_MOVIE extends AionServerPacket {

	private final boolean isMovie;
	private final int objectId;
	private final int questId;
	private final int cutsceneId;
	private final boolean canSkip;

	public SM_PLAY_MOVIE(boolean isCutsceneMovie, int objectId, int questId, int cutsceneId, boolean canSkip) {
		this.isMovie = isCutsceneMovie;
		this.objectId = objectId;
		this.questId = questId;
		this.cutsceneId = cutsceneId;
		this.canSkip = canSkip;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		var activePlayer = con.getActivePlayer();
		if (activePlayer != null) {
			activePlayer.setCustomState(CustomPlayerState.WATCHING_CUTSCENE);
			com.lostacademy.Dps_Meter.DpsService.sendPlayerState(activePlayer, true, true);
		}
		writeC(isMovie ? 1 : 0); // if 1: CutSceneMovies else CutScenes
		writeD(objectId);
		writeD(questId);
		writeD(cutsceneId);
		writeC(0); // unknown
		writeC(canSkip ? 0 : 1);
	}
}
