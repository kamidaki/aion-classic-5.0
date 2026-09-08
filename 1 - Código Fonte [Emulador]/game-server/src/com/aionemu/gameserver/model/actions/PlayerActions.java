package com.aionemu.gameserver.model.actions;

import com.aionemu.gameserver.model.gameobjects.player.InRoll;
import com.aionemu.gameserver.model.gameobjects.player.Player;

/**
 * @author Lost Academy Team & Durak
 */
public class PlayerActions {

	public static boolean isInPlayerMode(Player player, PlayerMode mode) {
		switch (mode) {
			case IN_ROLL:
				return player.inRoll != null;
		}
		return false;
	}

	public static void setPlayerMode(Player player, PlayerMode mode, Object obj) {
		switch (mode) {
			case IN_ROLL:
				player.inRoll = (InRoll) obj;
				break;
		}
	}

	public static boolean unsetPlayerMode(Player player, PlayerMode mode) {
		switch (mode) {
			case IN_ROLL:
				if (player.inRoll == null)
					return false;
				player.inRoll = null;
				return true;
			default:
				return false;
		}
	}

}
