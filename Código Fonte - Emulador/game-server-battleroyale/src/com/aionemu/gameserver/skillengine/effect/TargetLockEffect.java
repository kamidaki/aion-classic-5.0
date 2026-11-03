package com.aionemu.gameserver.skillengine.effect;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Future;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.controllers.observer.DeathObserver;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * Classic target lock: links one caster to one target and applies the three
 * official damage modifiers while the link is active.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "TargetLockEffect")
public class TargetLockEffect extends EffectTemplate {

	private static final ConcurrentHashMap<Integer, Lock> LOCKS = new ConcurrentHashMap<>();

	@XmlAttribute(name = "focus_value")
	private int focusValue;
	@XmlAttribute(name = "focus_delta")
	private int focusDelta;
	@XmlAttribute(name = "cover_value")
	private int coverValue;
	@XmlAttribute(name = "cover_delta")
	private int coverDelta;
	@XmlAttribute(name = "focus_drop_value")
	private int focusDropValue;
	@XmlAttribute(name = "focus_drop_delta")
	private int focusDropDelta;
	@XmlAttribute(name = "range")
	private int range;
	@XmlAttribute(name = "checktime")
	private int checktime;
	@XmlAttribute(name = "skill_id")
	private int skillId;

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void startEffect(Effect effect) {
		Creature caster = effect.getEffector();
		Creature target = effect.getEffected();
		int level = effect.getSkillLevel();
		Lock lock = new Lock(target.getObjectId(),
			focusValue + focusDelta * level,
			coverValue + coverDelta * level,
			focusDropValue + focusDropDelta * level,
			effect);
		Lock previous = LOCKS.get(caster.getObjectId());
		if (previous != null && previous.effect() != effect)
			previous.effect().endEffect();
		LOCKS.put(caster.getObjectId(), lock);

		if (skillId > 0)
			SkillEngine.getInstance().applyEffectDirectly(skillId, caster, caster);
		effect.addObserver(caster, new DeathObserver(_ -> effect.endEffect()));

		if (checktime > 0 && range > 0) {
			Future<?> task = ThreadPoolManager.getInstance().scheduleAtFixedRate(() -> {
				if (!caster.isSpawned() || !target.isSpawned() || !PositionUtil.isInRange(caster, target, range, false))
					effect.endEffect();
			}, checktime, checktime);
			effect.setPeriodicTask(task, position);
		}
	}

	@Override
	public void endEffect(Effect effect) {
		Creature caster = effect.getEffector();
		Lock lock = LOCKS.get(caster.getObjectId());
		if (lock != null && lock.effect() == effect && LOCKS.remove(caster.getObjectId(), lock) && skillId > 0)
			caster.getEffectController().removeEffect(skillId);
	}

	public static float modifyDamage(Creature attacker, Creature attacked, float damage) {
		Lock attackLock = LOCKS.get(attacker.getObjectId());
		if (attackLock != null) {
			int percent = attacked.getObjectId() == attackLock.targetId()
				? 100 + attackLock.focusValue()
				: Math.max(0, 100 - attackLock.focusDropValue());
			damage *= percent / 100f;
		}
		Lock defenseLock = LOCKS.get(attacked.getObjectId());
		if (defenseLock != null && attacker.getObjectId() != defenseLock.targetId())
			damage *= Math.max(0, 100 - defenseLock.coverValue()) / 100f;
		return damage;
	}

	private record Lock(int targetId, int focusValue, int coverValue, int focusDropValue, Effect effect) {
	}
}
