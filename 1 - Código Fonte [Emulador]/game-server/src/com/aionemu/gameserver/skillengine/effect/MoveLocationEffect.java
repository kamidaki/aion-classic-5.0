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
 * Flash até o alvo (MoveLocation no cliente, reserved2 = alcance): ST_tele_G1, ALL_teleport e a arrancada dos ALL_GlideATK_*.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "MoveLocationEffect")
public class MoveLocationEffect extends EffectTemplate {

	/**
	 * 5.0 oficial (ST_tele_G1 duas vezes, de lados diferentes): o Brawler para a 1,6 m do alvo, na linha até ele, virado para o alvo. Não sai do
	 * bound_radius do alvo (0,25/0,35 no boneco de treino).
	 */
	public static final float STOP_DISTANCE = 1.6f;

	@XmlAttribute
	protected float distance;

	@Override
	public void calculate(Effect effect) {
		Skill skill = effect.getSkill();
		if (skill == null || !super.calculate(effect, null, null))
			return;
		effect.setDashStatus(DashStatus.RANDOMMOVELOC); // 5.0 oficial: dash 1 no 0x2B, seguido de heading e x/y/z do destino
		Creature effector = effect.getEffector();
		Creature target = effect.getEffected();
		boolean hasTarget = target != null && !target.equals(effector);
		float x, y;
		if (hasTarget) {
			double radian = Math.toRadians(PositionUtil.calculateAngleFrom(target, effector));
			x = target.getX() + (float) Math.cos(radian) * STOP_DISTANCE;
			y = target.getY() + (float) Math.sin(radian) * STOP_DISTANCE;
		} else {
			double radian = Math.toRadians(PositionUtil.convertHeadingToAngle(effector.getHeading()));
			float dist = distance > 0 ? distance : 20f;
			x = effector.getX() + (float) Math.cos(radian) * dist;
			y = effector.getY() + (float) Math.sin(radian) * dist;
		}
		Vector3f dest = GeoService.getInstance().getClosestCollision(effector, x, y, hasTarget ? target.getZ() : effector.getZ());
		byte heading = hasTarget ? PositionUtil.getHeadingTowards(dest.getX(), dest.getY(), target.getX(), target.getY()) : effector.getHeading();
		skill.setTargetPosition(dest.getX(), dest.getY(), dest.getZ(), heading);
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
