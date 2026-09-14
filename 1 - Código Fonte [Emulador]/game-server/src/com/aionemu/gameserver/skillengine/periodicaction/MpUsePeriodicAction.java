package com.aionemu.gameserver.skillengine.periodicaction;

import javax.xml.bind.annotation.XmlAttribute;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * @author Lost Academy Team & Durak
 */
public class MpUsePeriodicAction extends PeriodicAction {

	@XmlAttribute(name = "value")
	protected int value;

	@XmlAttribute
	protected boolean ratio;

	@Override
	public void act(Effect effect) {
		Creature effected = effect.getEffected();
		int maxMp = effected.getGameStats().getMaxMp().getCurrent();
		int requiredMp = ratio ? (int) (maxMp * (value / 100f)) : value;
		if (effected.getLifeStats().getCurrentMp() < requiredMp) {
			effect.endEffect();
			return;
		}
		effected.getLifeStats().reduceMp(requiredMp);
	}

}
