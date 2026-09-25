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
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.world.geo.GeoService;
import com.lostacademy.nav.NavService;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BackDashEffect")
public class BackDashEffect extends DamageEffect {

	@XmlAttribute(name = "distance")
	private float distance;

	@Override
	public void calculate(Effect effect) {
		effect.setDashStatus(DashStatus.BACKDASH);
		Creature effector = effect.getEffector();
		byte h = PositionUtil.getHeadingTowards(effector, effect.getEffected());
		float inverseAngle = PositionUtil.convertHeadingToAngle(h) + 180; // flip by 180 degrees for opposite direction
		Vector3f closestCollision = GeoService.getInstance().findMovementCollision(effector, inverseAngle, distance);
		float targetX = closestCollision.getX();
		float targetY = closestCollision.getY();
		float targetZ = closestCollision.getZ();
		if (GeoDataConfig.GEO_NAV_ENABLE) {
			float navZ = NavService.getInstance().getNavSurfaceZ(effector.getWorldId(), targetX, targetY, targetZ);
			if (!Float.isNaN(navZ)) {
				targetZ = navZ;
			}
		}
		effect.getSkill().setTargetPosition(targetX, targetY, targetZ, h);
		World.getInstance().updatePosition(effector, targetX, targetY, targetZ, h);
		super.calculate(effect);
	}
}
