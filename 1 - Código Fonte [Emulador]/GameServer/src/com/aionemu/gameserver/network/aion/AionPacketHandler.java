package com.aionemu.gameserver.network.aion;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.ColorChat;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.Util;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;


public class AionPacketHandler {

	/**
	 * logger for this class
	 */
	private static final Logger log = LoggerFactory.getLogger(AionPacketHandler.class);

	private final Map<State, Map<Integer, AionClientPacket>> packetsPrototypes = new HashMap<State, Map<Integer, AionClientPacket>>();

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
		/* Second opcodec. */
		data.position(data.position() + 3);

		int decOp = ((id ^ 0x36) - 0xC4) & 0xFFFF;
		int bytes = data.remaining();
		String hex = WireTrace.ativo() ? WireTrace.hexDe(data, data.position(), bytes) : "";
		if (log.isDebugEnabled()) {
			log.debug(String.format("[REDE <- CLIENTE] Opcode=0x%04X (dec=0x%04X), State=%s, Bytes=%d", id, decOp, state, data.remaining()));
		}

		AionClientPacket recebido = getPacket(state, id, data, client);
		WireTrace.cliente(client, id, decOp, bytes, recebido == null ? "?" : recebido.getPacketName(), hex);
		return recebido;
	}

	public void addPacketPrototype(AionClientPacket packetPrototype) {
		for (State state : packetPrototype.getValidStates()) {
			Map<Integer, AionClientPacket> stateMap = packetsPrototypes.get(state);
			if (stateMap == null) {
				stateMap = new HashMap<Integer, AionClientPacket>();
				packetsPrototypes.put(state, stateMap);
			}
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
		res.setBuffer(buf);
		res.setConnection(con);
		if (con.getState().equals(AionConnection.State.IN_GAME) && con.getActivePlayer() != null && con.getActivePlayer().getPlayerAccount() != null && con.getActivePlayer().getPlayerAccount().getAccessLevel() == 5 && NetworkConfig.DISPLAY_PACKETS) {
			log.info("0x" + Integer.toHexString(res.getOpcode()).toUpperCase() + " : " + res.getPacketName());
			PacketSendUtility.sendMessage(con.getActivePlayer(), ColorChat.colorChat("0x" +Integer.toHexString(res.getOpcode()).toUpperCase() + " : " + res.getPacketName(), "1 0 5 0"));
		}
		return res;
	}

	/**
	 * Logs unknown packet.
	 * 
	 * @param state
	 * @param id
	 * @param data
	 * @throws Exception 
	 */
	private void unknownPacket(State state, int id, ByteBuffer data) {
		int decOp = ((id ^ 0x36) - 0xC4) & 0xFFFF;
		log.warn(String.format("[REDE DESCONHECIDO] Opcode=0x%04X (dec=0x%04X), State=%s \n%s", id, decOp, state.toString(),
			Util.toHex(data)));
	}
}