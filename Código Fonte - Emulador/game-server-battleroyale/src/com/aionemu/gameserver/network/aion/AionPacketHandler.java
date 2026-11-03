package com.aionemu.gameserver.network.aion;

import com.aionemu.commons.utils.NetworkUtils;
import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;

public class AionPacketHandler {

	private static final Logger log = LoggerFactory.getLogger(AionPacketHandler.class);

	private final Map<State, Map<Integer, AionClientPacket>> packetsPrototypes = new HashMap<>();

	/**
	 * Reads one packet from given ByteBuffer
	 * 
	 * @param data
	 * @param client
	 * @return AionClientPacket object from binary data
	 */
	public AionClientPacket handle(ByteBuffer data, AionConnection client) {
		State state = client.getState();
		int id = data.getShort() & 0xffff;
		/* Skip 3 bytes (static byte + flipped opcode). */
		data.position(data.position() + 3);

		int decOp = ((id ^ 0x36) - 0xC4) & 0xFFFF;
		log.debug(String.format("[REDE <- CLIENTE] Opcode=0x%04X (dec=0x%04X), State=%s, Bytes=%d", id, decOp, state, data.remaining()));

		return getPacket(state, id, data, client);
	}

	public void addPacketPrototype(AionClientPacket packetPrototype) {
		for (State state : packetPrototype.getValidStates()) {
			Map<Integer, AionClientPacket> stateMap = packetsPrototypes.computeIfAbsent(state, k -> new HashMap<>());
			stateMap.put(packetPrototype.getOpcode(), packetPrototype);
		}
	}

	public Map<State, Map<Integer, AionClientPacket>> getPacketsPrototypes() {
		return packetsPrototypes;
	}

	private AionClientPacket getPacket(State state, int id, ByteBuffer buf, AionConnection con) {
		Map<Integer, AionClientPacket> stateMap = packetsPrototypes.get(state);
		AionClientPacket prototype = stateMap != null ? stateMap.get(id) : null;
		if (prototype == null) {
			unknownPacket(state, id, buf);
			return null;
		}
		AionClientPacket res = prototype.clonePacket();
		if (res != null) {
			res.setBuffer(buf);
			res.setConnection(con);
			log.debug(String.format("[REDE RECONHECIDO] %s (Opcode=0x%04X, dec=0x%04X, State=%s)", res.getClass().getSimpleName(), id, ((id ^ 0x36) - 0xC4) & 0xFFFF, state));
		}
		return res;
	}

	/**
	 * Logs unknown packet.
	 */
	private void unknownPacket(State state, int id, ByteBuffer data) {
		int decOp = ((id ^ 0x36) - 0xC4) & 0xFFFF;
		String msg = String.format("[REDE DESCONHECIDO] Opcode=0x%04X (dec=0x%04X), State=%s, Bytes=%d", id, decOp, state.toString(), data.remaining());
		if (NetworkConfig.LOG_UNKNOWN_PACKETS)
			log.warn(msg + System.lineSeparator() + NetworkUtils.toHex(data.duplicate()));
		else
			log.debug(msg);
	}
}
