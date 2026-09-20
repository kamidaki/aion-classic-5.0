package com.aionemu.gameserver.skillengine.effect;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SKILL_COOLDOWN;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Reduz ou zera a recarga de um grupo de delay_id. No cliente: reserved1 = Delay_ID (lista em reserved2..8) ou Delay_ID_Range (reserved2..3), e
 * reserved11 = porcentagem da recarga restante que some (100 nas skills _high do Brawler).
 *
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SkillCooltimeResetEffect")
public class SkillCooltimeResetEffect extends EffectTemplate {

	@XmlAttribute(name = "first_cd")
	protected int firstCd;

	@XmlAttribute(name = "last_cd")
	protected int lastCd;

	@XmlList
	@XmlAttribute(name = "delay_ids")
	protected List<Integer> delayIds;

	@Override
	public void applyEffect(Effect effect) {
		Creature effected = effect.getEffected();
		if (effected == null || effected.getSkillCoolDowns() == null || effected.getSkillCoolDowns().isEmpty())
			return;

		long now = System.currentTimeMillis();
		Map<Integer, Long> resetSkillCoolDowns = new HashMap<>();
		for (Map.Entry<Integer, Long> entry : new HashMap<>(effected.getSkillCoolDowns()).entrySet()) {
			int cooldownId = entry.getKey();
			if (!matches(cooldownId))
				continue;
			long delay = entry.getValue() - now;
			if (delay <= 0) // 5.0 oficial: o 0x33 só traz as skills que ainda estavam em recarga
				continue;
			// delta = porcentagem da recarga restante; sem delta, value em ms
			delay = delta > 0 ? delay - delay * delta / 100 : delay - value;
			if (delay <= 0) {
				effected.removeSkillCoolDown(cooldownId);
				resetSkillCoolDowns.put(cooldownId, 0L);
			} else {
				effected.setSkillCoolDown(cooldownId, now + delay);
				resetSkillCoolDowns.put(cooldownId, now + delay);
			}
		}
		if (!resetSkillCoolDowns.isEmpty() && effected instanceof Player player)
			PacketSendUtility.sendPacket(player, new SM_SKILL_COOLDOWN(player, resetSkillCoolDowns, true));
	}

	private boolean matches(int cooldownId) {
		if (delayIds != null && !delayIds.isEmpty())
			return delayIds.contains(cooldownId);
		return cooldownId >= firstCd && cooldownId <= lastCd;
	}
}
