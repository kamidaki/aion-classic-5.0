package com.aionemu.gameserver.model.siege;

import java.util.List;

import com.aionemu.gameserver.model.templates.siegelocation.SiegeLocationTemplate;

/**
 * @author Lost Academy Team & Durak
 */
public class OutpostLocation extends SiegeLocation {

	public OutpostLocation(SiegeLocationTemplate template) {
		super(template);
	}

	@Override
	public int getNextState() {
		return isVulnerable() ? STATE_INVULNERABLE : STATE_VULNERABLE;
	}

	/**
	 * @return Fortresses that must be captured to own this outpost
	 */
	public List<Integer> getFortressDependency() {
		return getTemplate().getFortressDependency();
	}

	/**
	 * Shouldn't be necessary anymore, but re-check packets first before removing this.
	 * Silentera entrances do not depend on fortresses since 4.x.
	 */
	public boolean isSilenteraAllowed() {
		return true;
	}
}
