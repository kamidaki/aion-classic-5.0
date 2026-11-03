package com.aionemu.gameserver.network.aion;

import java.util.EnumSet;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.network.packet.BaseClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AionClientPacket extends BaseClientPacket<AionConnection> implements Cloneable {

	private static final Logger log = LoggerFactory.getLogger(AionClientPacket.class);

	private final Set<State> validStates;

	/**
	 * Constructs new client packet instance with varargs State.
	 * 
	 * @param opcode
	 *          packet id
	 * @param state
	 *          connection valid state
	 * @param restStates
	 *          rest of connection valid state (optional - if there are more than one)
	 */
	protected AionClientPacket(int opcode, State state, State... restStates) {
		super(opcode);
		this.validStates = EnumSet.of(state, restStates);
	}

	/**
	 * Constructs new client packet instance with Set<State>.
	 * 
	 * @param opcode
	 *          packet id
	 * @param validStates
	 *          connection valid states
	 */
	protected AionClientPacket(int opcode, Set<State> validStates) {
		super(opcode);
		this.validStates = validStates;
	}

	@Override
	public final void run() {
		try {
			if (isValid()) // run only if packet is still valid (connection state didn't change, for example due to logout)
				runImpl();
		} catch (Throwable e) {
			String name = getConnection().getAccount() != null ? getConnection().getAccount().getName() : getConnection().getIP();
			log.error("Error handling client (" + name + ") message: " + this, e);
		}
	}

	/**
	 * Send new AionServerPacket to connection that is owner of this packet. This method is equivalent to: getConnection().sendPacket(msg);
	 * 
	 * @param msg
	 */
	protected void sendPacket(AionServerPacket msg) {
		getConnection().sendPacket(msg);
	}

	/**
	 * Clones this packet object.
	 * 
	 * @return AionClientPacket
	 */
	public AionClientPacket clonePacket() {
		try {
			return (AionClientPacket) super.clone();
		} catch (CloneNotSupportedException e) {
			return null;
		}
	}

	/**
	 * Reads a fixed size string from the buffer, omitting not present trailing characters for the return value.
	 */
	protected final String readS(int characterCount) {
		String string = readS(); // read byte length = characters * 2 + 2
		if (string != null && string.length() < characterCount)
			readB((characterCount - string.length()) * 2);
		else if (string == null)
			readB(characterCount * 2);
		return string;
	}

	/**
	 * Checks if the packet is still valid for its connection.
	 * 
	 * @return True if packet is still valid and should be processed.
	 */
	public final boolean isValid() {
		State state = getConnection().getState();
		boolean valid = validStates != null && validStates.contains(state);
		if (!valid) {
			log.info(this + " won't be processed cuz its valid state don't match current connection state: " + state);
		}
		return valid;
	}

	public Set<State> getValidStates() {
		return validStates;
	}

	public int getOpcode() {
		return getOpCode();
	}

	@Override
	protected int getOpCodeZeroPadding() {
		return 3;
	}
}
