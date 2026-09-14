package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Efeito de registro de nota musical do Blending (Luminess).
 * Registra a nota no BlendingState do jogador e, quando as 3 notas formam
 * um combo oficial, dispara o finalizador correspondente (9000..9008).
 *
 * @author Antigravity
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BlendingEffect")
public class BlendingEffect extends EffectTemplate {

	@XmlAttribute(name = "note")
	protected String note;

	@Override
	public void applyEffect(Effect effect) {
		if (effect.getEffector() instanceof Player player) {
			BlendingNote blendingNote = BlendingNote.fromString(note);
			if (blendingNote != null) {
				player.getBlendingState().recordNote(blendingNote);
				Integer comboSkillId = player.getBlendingState().resolveCombo();
				if (comboSkillId != null) {
					player.getBlendingState().clear();
					Creature target = effect.getEffected();
					if (target != null && !target.getLifeStats().isDead()) {
						SkillEngine.getInstance().getSkill(player, comboSkillId, 1, target).useWithoutPropSkill();
					}
				}
			}
		}
	}

	@Override
	public void calculate(Effect effect) {
		effect.addSuccessEffect(this);
	}

	public String getNote() {
		return note;
	}
}
