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
	 * Quanto o jogador para antes do centro do alvo, somado ao raio do alvo.
	 */
	public static final float STOP_GAP = 1.25f;

	/**
	 * 5.0 oficial: dash e flash do jogador param a max(front, side) do alvo + 1,25 m, sem depender do raio de quem avança. Fecha com ~60 medidas em 33
	 * NPCs (subida 1-60 e combate do Brawler): boneco de treino 1,60, Naga_EleAir 1,85, Drakan_Sc_F 1,77, Lizard_Fi_Armor 4,15, PagatiStrider 5,45. O
	 * npc_templates guarda o raio do cliente × scale / 200.
	 */
	public static float stopDistance(Creature target) {
		return target.getObjectTemplate().getBoundRadius().getMaxOfFrontAndSide() + STOP_GAP;
	}

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
			// 5.0 oficial (ST_tele_G1): na linha até o alvo, virado para ele
			double radian = Math.toRadians(PositionUtil.calculateAngleFrom(target, effector));
			float stop = stopDistance(target);
			x = target.getX() + (float) Math.cos(radian) * stop;
			y = target.getY() + (float) Math.sin(radian) * stop;
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
