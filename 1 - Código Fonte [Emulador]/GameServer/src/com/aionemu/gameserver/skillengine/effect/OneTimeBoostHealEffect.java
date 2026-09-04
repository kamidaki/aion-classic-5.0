package com.aionemu.gameserver.skillengine.effect;

import java.util.concurrent.Future;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * @revision Metaverse
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "OneTimeBoostHealEffect")
public class OneTimeBoostHealEffect extends BuffEffect {
	
	@XmlAttribute
	private int count = 0;
	
	@Override
	public void startEffect(final Effect effect) {
		super.startEffect(effect);
		final int stopCount = count;
		if (stopCount != 0) {
			if (effect.getEffected().getSkillNumber() > 0) {
				effect.getEffected().setSkillNumber(0);
			}
		}
		
		Future<?> task = ThreadPoolManager.getInstance().scheduleAtFixedRate(new Runnable() {

			@Override
			public void run() {
				onPeriodicAction(effect);
			}
		}, 500, 500);
		
		effect.setPeriodicTask(task, position);
		
	}
	
	@Override
	public void onPeriodicAction(Effect effect) {
		final int stopCount = count;
		if (stopCount != 0) {
			if (effect.getEffected().getSkillNumber() == stopCount) {
				effect.getEffected().getEffectController().removeEffect(effect.getSkillId());
			}
		}
	}
	
	@Override
	public void endEffect(Effect effect) {
		super.endEffect(effect);
		if (effect.getEffected().getSkillNumber() > 0)
			effect.getEffected().setSkillNumber(0);
	}

}
