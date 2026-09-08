package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.skillengine.model.DashStatus;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ShadowMoveEffect")
public class ShadowMoveEffect extends EffectTemplate {

	@XmlAttribute
	protected int direction;
	@XmlAttribute
	protected float distance;

	@Override
	public void applyEffect(Effect effect) {
	}

	@Override
	public void calculate(Effect effect) {
		effect.setDashStatus(DashStatus.DASH);
		final Creature effector = effect.getEffector();
		double radian = Math.toRadians(PositionUtil.convertHeadingToAngle(effector.getHeading()));
		float dist = distance > 0 ? distance : 15f;
		float x1 = (float) Math.cos(radian) * dist;
		float y1 = (float) Math.sin(radian) * dist;
		Vector3f closestCollision = GeoService.getInstance().getClosestCollision(effector, effector.getX() + x1, effector.getY() + y1, effector.getZ());
		byte h = effector.getHeading();
		World.getInstance().updatePosition(effector, closestCollision.getX(), closestCollision.getY(), closestCollision.getZ(), h);
		effect.getSkill().setTargetPosition(closestCollision.getX(), closestCollision.getY(), closestCollision.getZ(), h);
		super.calculate(effect);
	}
}
