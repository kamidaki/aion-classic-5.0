package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.network.aion.serverpackets.SM_HEADING_UPDATE;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SpellStatus;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SpinEffect")
public class SpinEffect extends EffectTemplate {

	@Override
	public void applyEffect(Effect effect) {
		effect.addToEffectedController();
	}

	@Override
	public void calculate(Effect effect) {
		if (effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.PULLED)
			|| effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.SPIN)
			|| effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.OPENAERIAL)
			|| effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.STAGGER)
			|| effect.getEffected().getEffectController().isAbnormalSet(AbnormalState.STUMBLE))
			return;
		super.calculate(effect, StatEnum.SPIN_RESISTANCE, SpellStatus.SPIN);
	}

	@Override
	public void startEffect(Effect effect) {
		final Creature effected = effect.getEffected();
		final Creature effector = effect.getEffector();
		effected.getController().cancelCurrentSkill(effector);
		if (effected instanceof Player player) {
			player.getFlyController().onStopGliding();
			player.getController().onStopMove();
		} else {
			effected.getController().onStopMove();
		}
		effected.getEffectController().removeParalyzeEffects();

		byte newHeading = effector.getHeading();
		effected.getPosition().setH(newHeading);
		World.getInstance().updatePosition(effected, effected.getX(), effected.getY(), effected.getZ(), newHeading);
		PacketSendUtility.broadcastPacketAndReceive(effected, new SM_HEADING_UPDATE(effected));

		effected.getEffectController().setAbnormal(AbnormalState.SPIN);
		effect.setAbnormal(AbnormalState.SPIN);
	}

	@Override
	public void endEffect(Effect effect) {
		effect.getEffected().getEffectController().unsetAbnormal(AbnormalState.SPIN);
	}
}
