package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0129 (297) - SM_RECOMMENDED_PLAYERS_LIST
 * Official Classic 5.0 recommended players list notification dispatched during world entry.
 * Wire structure:
 *   - writeH(count)
 *   - for each player: writeS(playerName) [UTF-16LE null-terminated]
 * When no recommendations are available: writeH(0) (2 bytes).
 */
public class SM_RECOMMENDED_PLAYERS_LIST extends AionServerPacket {
	private final List<String> playerNames;
	private final byte[] rawPayload;

	/**
	 * Default constructor emitting an empty recommendation list (writeH(0)).
	 */
	public SM_RECOMMENDED_PLAYERS_LIST() {
		this(Collections.emptyList());
	}

	public SM_RECOMMENDED_PLAYERS_LIST(Collection<String> playerNames) {
		this.playerNames = playerNames != null ? new ArrayList<>(playerNames) : Collections.emptyList();
		this.rawPayload = null;
	}

	public SM_RECOMMENDED_PLAYERS_LIST(String... playerNames) {
		this(playerNames != null ? Arrays.asList(playerNames) : Collections.emptyList());
	}

	public SM_RECOMMENDED_PLAYERS_LIST(byte[] rawPayload) {
		this.playerNames = Collections.emptyList();
		this.rawPayload = rawPayload != null ? rawPayload.clone() : null;
	}

	public List<String> getPlayerNames() {
		return Collections.unmodifiableList(playerNames);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (rawPayload != null) {
			writeB(rawPayload);
			return;
		}
		if (playerNames == null || playerNames.isEmpty()) {
			writeH(0);
		} else {
			writeH(playerNames.size());
			for (String name : playerNames) {
				writeS(name);
			}
		}
	}
}
