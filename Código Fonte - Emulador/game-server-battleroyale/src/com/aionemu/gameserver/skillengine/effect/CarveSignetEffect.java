package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;

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
		int nextSignetLevel = signetLvlStart != null ? signetLvlStart : signetIncrement;
		Effect activeSignet = effect.getEffected().getEffectController().getAbnormalEffect(signet);
		if (activeSignet != null) {
			int currentLevel = activeSignet.getCarvedSignet() > 0 ? activeSignet.getCarvedSignet() : activeSignet.getSkillLevel();
			if (currentLevel <= 0 && targetSignetId > 0) {
				currentLevel = Math.max(1, activeSignet.getSkillId() - targetSignetId + 1);
			}
			if (signetLvlStart != null) {
				nextSignetLevel = Math.max(signetLvlStart, currentLevel);
			} else {
				nextSignetLevel = Math.min(currentLevel + signetIncrement, Math.max(targetCap, currentLevel));
			}
			activeSignet.endEffect();
		}

		effect.setCarvedSignet(nextSignetLevel);

		if (targetSignetId > 0) {
			SkillTemplate template = DataManager.SKILL_DATA.getSkillTemplate(targetSignetId + nextSignetLevel - 1);
			if (template != null) {
				Effect signetEffect = new Effect(effect.getEffector(), effect.getEffected(), template, nextSignetLevel, null, null);
				signetEffect.setCarvedSignet(nextSignetLevel);
				signetEffect.initialize();
				signetEffect.applyEffect();
			}
		}
	}
}
