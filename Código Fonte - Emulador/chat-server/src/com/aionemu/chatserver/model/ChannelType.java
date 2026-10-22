package com.aionemu.chatserver.model;

import java.util.HashMap;
import java.util.Map;

/**
 * @author Lost Academy Team & Durak
 */
public enum ChannelType {

	REGION("public"),
	TRADE("trade"),
	LFG("partyFind"),
	JOB("job"),
	LANG("User"),
	GOTCHA("gotcha"); // 5.0: canal do sorteio, o cliente entra ao logar

	private static final Map<String, ChannelType> channelByIdentifier = new HashMap<>();

	private final String identifier;

	static {
		for (ChannelType ct : values())
			channelByIdentifier.put(ct.getIdentifier(), ct);
	}

	ChannelType(String identifier) {
		this.identifier = identifier;
	}

	public String getIdentifier() {
		return identifier;
	}

	public static ChannelType getByIdentifier(String identifier) {
		return channelByIdentifier.get(identifier);
	}
}