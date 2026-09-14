package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Efeito de registro de nota musical do Blending (Luminess).
 * Delega o registro da nota diretamente ao BlendingState do jogador.
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
