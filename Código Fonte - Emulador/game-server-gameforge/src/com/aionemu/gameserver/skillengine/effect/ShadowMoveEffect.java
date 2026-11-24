package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.controllers.movement.PlayerMoveController;
import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.skillengine.model.DashStatus;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.EffectReserved;
import com.aionemu.gameserver.skillengine.model.EffectReserved.ResourceType;
import com.aionemu.gameserver.skillengine.model.Skill;
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
	public void calculate(Effect effect) {
		Skill skill = effect.getSkill();
		if (skill == null || !super.calculate(effect, null, null))
			return;
		effect.setDashStatus(DashStatus.RANDOMMOVELOC); // 5.0 oficial: dash 1 no 0x2B, não 2
		final Creature effector = effect.getEffector();
		Creature target = effect.getEffected();
		float x, y, z;
		byte h;
		if (target != null && !target.equals(effector)) {
			// 5.0 oficial (TH_MoveShadow_G1 duas vezes, de lados diferentes): sempre o mesmo ponto atrás do alvo, com o heading dele, à distância do dash
			double radian = Math.toRadians(PositionUtil.convertHeadingToAngle(target.getHeading()));
			float behind = MoveLocationEffect.stopDistance(target);
			x = target.getX() - (float) Math.cos(radian) * behind;
			y = target.getY() - (float) Math.sin(radian) * behind;
			z = target.getZ();
			h = target.getHeading();
		} else {
			double radian = Math.toRadians(PositionUtil.convertHeadingToAngle(effector.getHeading()));
			float dist = distance > 0 ? distance : 15f;
			x = effector.getX() + (float) Math.cos(radian) * dist;
			y = effector.getY() + (float) Math.sin(radian) * dist;
			z = effector.getZ();
			h = effector.getHeading();
		}
		Vector3f closestCollision = GeoService.getInstance().getClosestCollision(effector, x, y, z);
		skill.setTargetPosition(closestCollision.getX(), closestCollision.getY(), closestCollision.getZ(), h);
		// 5.0 oficial: um reserved de valor 0 no resultado
		effect.setReserveds(new EffectReserved(position, 0, ResourceType.HP, false), false);
	}

	@Override
	public void applyEffect(Effect effect) {
		Skill skill = effect.getSkill();
		if (skill == null)
			return;
		World.getInstance().updatePosition(effect.getEffector(), skill.getX(), skill.getY(), skill.getZ(), skill.getH());
		if (effect.getEffector().getMoveController() instanceof PlayerMoveController pmc)
			pmc.setHasMovedByRandomMoveLocEffect(skill);
	}
}
