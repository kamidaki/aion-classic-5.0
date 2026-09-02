/*
 * This file is part of aion-lightning <aion-lightning.com>.
 *
 *  aion-lightning is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  aion-lightning is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with aion-lightning.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.ai2;

import com.aionemu.commons.scripting.classlistener.AggregatedClassListener;
import com.aionemu.commons.scripting.classlistener.OnClassLoadUnloadListener;
import com.aionemu.commons.scripting.classlistener.ScheduledTaskClassListener;
import com.aionemu.commons.scripting.scriptmanager.ScriptManager;
import com.aionemu.gameserver.GameServerError;
import com.aionemu.gameserver.configs.main.AIConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.GameEngine;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CountDownLatch;

import static ch.lambdaj.Lambda.*;
import static ch.lambdaj.collection.LambdaCollections.with;

/**
 * @author ATracer
 */
public class AI2Engine implements GameEngine {

	private static final Logger log = LoggerFactory.getLogger(AI2Engine.class);
	private static ScriptManager scriptManager = new ScriptManager();
	public static final File INSTANCE_DESCRIPTOR_FILE = new File("./data/scripts/system/aihandlers.xml");

	private final Map<String, Class<? extends AbstractAI>> aiMap = new HashMap<String, Class<? extends AbstractAI>>();

	@Override
	public void load(CountDownLatch progressLatch) {
		log.info("AI2 engine load started");
		scriptManager = new ScriptManager();

		AggregatedClassListener acl = new AggregatedClassListener();
		acl.addClassListener(new OnClassLoadUnloadListener());
		acl.addClassListener(new ScheduledTaskClassListener());
		acl.addClassListener(new AI2HandlerClassListener());
		scriptManager.setGlobalClassListener(acl);

		try {
			scriptManager.load(INSTANCE_DESCRIPTOR_FILE);
			log.info("Loaded " + aiMap.size() + " AI2.");
			validateScripts();
		}
		catch (Exception e) {
			throw new GameServerError("Can't initialize ai handlers.", e);
		}
		finally {
			if (progressLatch != null)
				progressLatch.countDown();
		}
	}

	@Override
	public void shutdown() {
		log.info("AI2 engine shutdown started");
		scriptManager.shutdown();
		scriptManager = null;
		aiMap.clear();
		log.info("AI2 engine shutdown complete");
	}

	public void registerAI(Class<? extends AbstractAI> class1) {
		AIName nameAnnotation = class1.getAnnotation(AIName.class);
		if (nameAnnotation != null) {
			aiMap.put(nameAnnotation.value(), class1);
		}
	}

	public final AI2 setupAI(String name, Creature owner) {
		AbstractAI aiInstance = null;
		try {
			Class<? extends AbstractAI> aiClass = null;
			if (name != null) {
				aiClass = aiMap.get(name);
				if (aiClass == null) {
					for (Map.Entry<String, Class<? extends AbstractAI>> entry : aiMap.entrySet()) {
						if (entry.getKey().equalsIgnoreCase(name)) {
							aiClass = entry.getValue();
							break;
						}
					}
				}
			}
			if (aiClass == null) {
				aiClass = aiMap.get("aggressive");
				if (aiClass == null) {
					aiClass = aiMap.get("npc");
					if (aiClass == null) {
						aiClass = NpcAI2.class;
					}
				}
			}
			if (aiClass != null) {
				aiInstance = aiClass.newInstance();
				aiInstance.setOwner(owner);
				owner.setAi2(aiInstance);
				if (AIConfig.ONCREATE_DEBUG) {
					aiInstance.setLogging(true);
				}
			}
		}
		catch (Exception e) {
			log.error("[AI2] AI factory error: " + name, e);
		}
		return aiInstance;
	}

	/**
	 * @param aiName
	 * @param owner
	 */
	public void setupAI(AiNames aiName, Npc owner) {
		setupAI(aiName.getName(), owner);
	}
	
	private void validateScripts() {
		Collection<String> npcAINames = selectDistinct(with(DataManager.NPC_DATA.getNpcData().valueCollection()).extract(on(NpcTemplate.class).getAi()));
		npcAINames.removeAll(aiMap.keySet());
		if(npcAINames.size() > 0){
			log.warn("Bad AI names: " + join(npcAINames));
			try {
				File dir = new File("./log/Need_Implement");
				if (!dir.exists()) {
					dir.mkdirs();
				}
				File logFile = new File(dir, "bad_ai.log");
				java.io.PrintWriter pw = new java.io.PrintWriter(new java.io.FileWriter(logFile));
				java.util.List<String> sortedAiNames = new java.util.ArrayList<String>(npcAINames);
				java.util.Collections.sort(sortedAiNames);
				for (String badAi : sortedAiNames) {
					if (badAi != null && !badAi.isEmpty()) {
						pw.println(badAi);
					}
				}
				pw.flush();
				pw.close();
			} catch (Exception e) {
				log.error("Could not write bad AI log", e);
			}
		}
	}

	public static final AI2Engine getInstance() {
		return SingletonHolder.instance;
	}

	@SuppressWarnings("synthetic-access")
	private static class SingletonHolder {

		protected static final AI2Engine instance = new AI2Engine();
	}
}
