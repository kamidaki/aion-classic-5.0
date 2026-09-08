package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "CarveSignetEffect")
public class CarveSignetEffect extends DamageEffect {

	@XmlAttribute(name = "signet_increment")
	protected int signetIncrement = 1;
	@XmlAttribute(name = "signet_cap")
	protected Integer signetCap;
	@XmlAttribute(name = "signet_id")
	protected Integer signetId;
	@XmlAttribute(name = "signetid")
	protected Integer signetIdAlt;
	@XmlAttribute(name = "signetlvl")
	protected Integer signetLvl;
	@XmlAttribute(name = "signetlvlstart")
	protected Integer signetLvlStart;
	@XmlAttribute(required = true)
	protected String signet;
	@XmlAttribute
	protected int prob = 100;

	@Override
	public void applyEffect(Effect effect) {
		super.applyEffect(effect);

		if (Rnd.chance() >= prob)
			return;

		int targetCap = signetCap != null ? signetCap : (signetLvl != null ? signetLvl : 5);
		int targetSignetId = signetId != null ? signetId : (signetIdAlt != null ? signetIdAlt : 0);
		int nextSignetLevel = signetIncrement;
		Effect activeSignet = effect.getEffected().getEffectController().getAbnormalEffect(signet);
		if (activeSignet != null) {
			activeSignet.endEffect();
			nextSignetLevel = Math.min(activeSignet.getCarvedSignet() + signetIncrement, Math.max(targetCap, activeSignet.getCarvedSignet()));
		}
		if (targetSignetId > 0) {
			Effect signetEffect = SkillEngine.getInstance().applyEffect(targetSignetId + nextSignetLevel - 1, effect.getEffector(), effect.getEffected());
			if (signetEffect != null) {
				signetEffect.setCarvedSignet(nextSignetLevel);
			}
		}
	}
}
