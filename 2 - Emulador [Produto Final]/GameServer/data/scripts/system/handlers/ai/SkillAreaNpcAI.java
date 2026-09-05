package ai;

import com.aionemu.gameserver.model.gameobjects.Npc;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("skillarea")
public class SkillAreaNpcAI extends NpcAI {
	public SkillAreaNpcAI() {
		super();
	}

	public SkillAreaNpcAI(Npc owner) {
		super(owner);
	}

}