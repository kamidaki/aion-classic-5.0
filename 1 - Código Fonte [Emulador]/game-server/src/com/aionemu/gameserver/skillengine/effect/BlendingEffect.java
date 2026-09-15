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
 *
 * Separação estrita:
 * 1. Alvo: mantém os acúmulos (carvedSignet) de cada nota debuff.
 * 2. Jogador: mantém o BlendingState (sequência de notas utilizadas).
 * 3. Expiração: quando o efeito no alvo termina por tempo ou morte, BlendingState é resetado.
 * 4. Resolução de combo: remove os efeitos de notas do alvo antes de aplicar o finalizador.
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
		Creature target = effect.getEffected();
		int targetLiStacks = 0;

		// 1. Gerenciar acúmulos (carvedSignet) no efeito aplicado ao alvo
		if (target != null) {
			if (effect.getCarvedSignet() <= 0) {
				String currentStack = effect.getStack();
				String stackPrefix = getStackPrefix(currentStack);
				int count = 1;

				if (stackPrefix != null) {
					for (Effect active : target.getEffectController().getAbnormalEffects()) {
						if (active != effect && active.getStack() != null && active.getStack().startsWith(stackPrefix)) {
							count = active.getCarvedSignet() + 1;
							break;
						}
					}
				}

				if ("E".equals(note)) {
					count = Math.min(15, count);
				}
				effect.setCarvedSignet(count);
			}

			// Verificar quantidade de Li acumulados no alvo para o combo Do
			for (Effect active : target.getEffectController().getAbnormalEffects()) {
				if (active.getStack() != null && active.getStack().startsWith("LU_BLENDE")) {
					targetLiStacks = Math.max(targetLiStacks, active.getCarvedSignet());
				}
			}
			if ("E".equals(note)) {
				targetLiStacks = Math.max(targetLiStacks, effect.getCarvedSignet());
			}
		}

		// 2. Registrar nota no BlendingState do jogador e resolver combo
		if (effect.getEffector() instanceof Player player) {
			if (player.getPlayerClass() != com.aionemu.gameserver.model.PlayerClass.LUMINESS) {
				return;
			}
			BlendingNote blendingNote = BlendingNote.fromString(note);
			if (blendingNote != null) {
				player.getBlendingState().recordNote(blendingNote);
				Integer comboSkillId = player.getBlendingState().resolveCombo(targetLiStacks);
				if (comboSkillId != null) {
					player.getBlendingState().clear();
					if (target != null && !target.getLifeStats().isDead()) {
						// 3. Remover efeitos residuais das notas antes de disparar o finalizador oficial
						target.getEffectController().removeBlendingNoteEffects();
						SkillEngine.getInstance().getSkill(player, comboSkillId, 1, target).useWithoutPropSkill();
					}
				}
			}
		}
	}

	@Override
	public void endEffect(Effect effect) {
		if (effect.getEffector() instanceof Player player) {
			// Reseta o BlendingState quando o efeito no alvo termina por expiração de tempo ou morte do alvo
			if (effect.isEndedByTime() || effect.getEffected() == null || effect.getEffected().getLifeStats().isDead()) {
				player.getBlendingState().clear();
			}
		}
	}

	@Override
	public void calculate(Effect effect) {
		effect.addSuccessEffect(this);

		Creature target = effect.getEffected();
		if (target != null) {
			String currentStack = effect.getStack();
			String stackPrefix = getStackPrefix(currentStack);
			int count = 1;

			if (stackPrefix != null) {
				for (Effect active : target.getEffectController().getAbnormalEffects()) {
					if (active != effect && active.getStack() != null && active.getStack().startsWith(stackPrefix)) {
						count = active.getCarvedSignet() + 1;
						break;
					}
				}
			}

			if ("E".equals(note)) {
				count = Math.min(15, count);
			}
			effect.setCarvedSignet(count);
		}
	}

	public String getNote() {
		return note;
	}

	private static String getStackPrefix(String stack) {
		if (stack == null) {
			return null;
		}
		int idx = stack.lastIndexOf('_');
		return idx > 0 ? stack.substring(0, idx) : stack;
	}
}
