package com.aionemu.gameserver.model.stats.listeners;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.stats.container.CreatureGameStats;
import com.aionemu.gameserver.model.templates.TitleTemplate;

/**
 * @author Lost Academy Team & Durak
 */
public class TitleChangeListener {

	public static void onBonusTitleChange(CreatureGameStats<?> cgs, int titleId, boolean isSet) {
		TitleTemplate tt = DataManager.TITLE_DATA.getTitleTemplate(titleId);
		if (tt == null || !tt.isAvailable()) {
			return;
		}
		if (!isSet) {
			cgs.endEffect(tt);
		} else {
			cgs.addEffect(tt, tt.getModifiers());
		}
	}
}
