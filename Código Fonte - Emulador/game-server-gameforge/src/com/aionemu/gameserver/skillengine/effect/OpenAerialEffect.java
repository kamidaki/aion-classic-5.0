package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.network.aion.serverpackets.SM_FORCED_MOVE;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SubEffectType;
import com.aionemu.gameserver.skillengine.model.SpellStatus;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.geo.GeoService;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.lostacademy.nav.NavService;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "OpenAerialEffect")
public class OpenAerialEffect extends EffectTemplate {

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void calculate(Effect effect) {
		if (effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.PULLED)
			|| effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.OPENAERIAL))
			return;

		if (!super.calculate(effect, StatEnum.OPENAERIAL_RESISTANCE, SpellStatus.OPENAERIAL))
			return;
		if (effect.isSubEffect())
			effect.setSubEffectType(SubEffectType.OPENAERIAL);
		float z = effect.getEffected().getZ();
		if (!effect.getEffected().isFlying()) {
			float groundZ = Float.NaN;
			if (GeoDataConfig.GEO_NAV_ENABLE) {
				groundZ = NavService.getInstance().getNavSurfaceZ(
					effect.getEffected().getWorldId(),
					effect.getEffected().getX(),
					effect.getEffected().getY(),
					effect.getEffected().getZ());
			}
			if (Float.isNaN(groundZ) && GeoDataConfig.GEO_ENABLE) {
				groundZ = GeoService.getInstance().getZ(
					effect.getEffected().getWorldId(),
					effect.getEffected().getX(),
					effect.getEffected().getY(),
					effect.getEffected().getZ() + 2,
					effect.getEffected().getZ() - 1,
					effect.getEffected().getInstanceId());
			}
			if (!Float.isNaN(groundZ)) {
				z = groundZ + 2.5f;
			} else {
				z += 2.5f;
			}
		}
		effect.setTargetLoc(effect.getEffected().getX(), effect.getEffected().getY(), z);
	}

	@Override
	public void startEffect(Effect effect) {
		final Creature effected = effect.getEffected();
		effected.getController().cancelCurrentSkill(effect.getEffector());
		effected.getEffectController().removeParalyzeEffects();
		effected.getEffectController().unsetAbnormal(AbnormalState.STUMBLE);
		if (effected instanceof Player player) {
			player.getFlyController().onStopGliding();
			player.getController().onStopMove();
		}
		World.getInstance().updatePosition(effected, effect.getTargetX(), effect.getTargetY(), effect.getTargetZ(), effected.getHeading());
		if (effected instanceof Player)
			PacketSendUtility.broadcastPacketAndReceive(effected, new SM_FORCED_MOVE(effect.getEffector(), effected.getObjectId(),
					effect.getTargetX(), effect.getTargetY(), effect.getTargetZ()));
		effect.setAbnormal(AbnormalState.OPENAERIAL);
		effected.getEffectController().setAbnormal(AbnormalState.OPENAERIAL);
	}

	@Override
	public void endEffect(Effect effect) {
		final Creature effected = effect.getEffected();
		effected.getEffectController().unsetAbnormal(AbnormalState.OPENAERIAL);
		if (!effected.isFlying()) {
			float groundZ = Float.NaN;
			if (GeoDataConfig.GEO_NAV_ENABLE) {
				groundZ = NavService.getInstance().getNavSurfaceZ(
					effected.getWorldId(),
					effected.getX(),
					effected.getY(),
					effected.getZ());
			}
			if (Float.isNaN(groundZ) && GeoDataConfig.GEO_ENABLE) {
				groundZ = GeoService.getInstance().getZ(
					effected.getWorldId(),
					effected.getX(),
					effected.getY(),
					effected.getZ() + 2,
					effected.getZ() - 4,
					effected.getInstanceId());
			}
			if (!Float.isNaN(groundZ)) {
				World.getInstance().updatePosition(effected, effected.getX(), effected.getY(), groundZ, effected.getHeading());
				if (effected instanceof Player)
					PacketSendUtility.broadcastPacketAndReceive(effected, new SM_FORCED_MOVE(effected, effected.getObjectId(),
							effected.getX(), effected.getY(), groundZ));
			}
		}
	}
}
