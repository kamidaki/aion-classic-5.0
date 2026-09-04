package com.aionemu.gameserver.ai;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.lang.reflect.Constructor;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

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

/**
 * @author ATracer
 */
@SuppressWarnings("rawtypes")
public class AIEngine implements GameEngine {

	private static final Logger log = LoggerFactory.getLogger(AIEngine.class);
	private static ScriptManager scriptManager = new ScriptManager();
	public static final File INSTANCE_DESCRIPTOR_FILE = new File("./data/scripts/system/aihandlers.xml");

	private final Map<String, Class<? extends AbstractAI>> aiMap = new ConcurrentHashMap<>();

	private AIEngine() {
	}

	@Override
	public void load(CountDownLatch progressLatch) {
		log.info("AI engine load started");
		scriptManager = new ScriptManager();

		AggregatedClassListener acl = new AggregatedClassListener();
		acl.addClassListener(new OnClassLoadUnloadListener());
		acl.addClassListener(new ScheduledTaskClassListener());
		acl.addClassListener(new AIHandlerClassListener());
		scriptManager.setGlobalClassListener(acl);

		try {
			scriptManager.load(INSTANCE_DESCRIPTOR_FILE);
			log.info("Loaded " + aiMap.size() + " AI handlers.");
			validateScripts();
		} catch (Exception e) {
			throw new GameServerError("Can't initialize ai handlers.", e);
		} finally {
			if (progressLatch != null) {
				progressLatch.countDown();
			}
		}
	}

	@Override
	public void shutdown() {
		log.info("AI engine shutdown started");
		if (scriptManager != null) {
			scriptManager.shutdown();
			scriptManager = null;
		}
		aiMap.clear();
		log.info("AI engine shutdown complete");
	}

	public void reload() {
		shutdown();
		load(null);
	}

	@SuppressWarnings("unchecked")
	public void registerAI(Class<? extends AbstractAI> aiClass) {
		AIName nameAnnotation = aiClass.getAnnotation(AIName.class);
		if (nameAnnotation != null) {
			aiMap.put(nameAnnotation.value().toLowerCase(), aiClass);
		}
	}

	public final AI setupAI(String name, Creature owner) {
		AbstractAI aiInstance = null;
		try {
			Class<? extends AbstractAI> aiClass = null;
			if (name != null) {
				aiClass = aiMap.get(name.toLowerCase());
			}
			if (aiClass == null) {
				aiClass = aiMap.get("aggressive");
				if (aiClass == null) {
					aiClass = aiMap.get("npc");
					if (aiClass == null) {
						aiClass = NpcAI.class;
					}
				}
			}
			if (aiClass != null) {
				Constructor<?> ctor = null;
				for (Constructor<?> c : aiClass.getConstructors()) {
					if (c.getParameterCount() == 1 && c.getParameterTypes()[0].isAssignableFrom(owner.getClass())) {
						ctor = c;
						break;
					}
				}
				if (ctor != null) {
					aiInstance = (AbstractAI) ctor.newInstance(owner);
				} else {
					aiInstance = (AbstractAI) aiClass.getDeclaredConstructor().newInstance();
					aiInstance.setOwner(owner);
				}
				owner.setAi(aiInstance);
				if (AIConfig.ONCREATE_DEBUG) {
					aiInstance.setLogging(true);
				}
			}
		} catch (Exception e) {
			log.error("[AI] AI factory error: " + name, e);
		}
		return aiInstance;
	}

	public void setupAI(AiNames aiName, Npc owner) {
		setupAI(aiName.getName(), owner);
	}

	public AbstractAI newAI(String name, Creature owner) {
		return (AbstractAI) setupAI(name, owner);
	}

	private void validateScripts() {
		try {
			Set<String> npcAINames = new HashSet<>();
			for (NpcTemplate template : DataManager.NPC_DATA.getNpcData().valueCollection()) {
				if (template.getAi() != null && !template.getAi().isEmpty()) {
					npcAINames.add(template.getAi().toLowerCase());
				}
			}
			npcAINames.removeAll(aiMap.keySet());
			if (!npcAINames.isEmpty()) {
				log.warn("Missing AI handlers count: " + npcAINames.size());
				File dir = new File("./log/Need_Implement");
				if (!dir.exists()) {
					dir.mkdirs();
				}
				File logFile = new File(dir, "bad_ai.log");
				try (PrintWriter pw = new PrintWriter(new FileWriter(logFile))) {
					List<String> sortedAiNames = new ArrayList<>(npcAINames);
					Collections.sort(sortedAiNames);
					for (String badAi : sortedAiNames) {
						if (badAi != null && !badAi.isEmpty()) {
							pw.println(badAi);
						}
					}
					pw.flush();
				}
			}
		} catch (Exception e) {
			log.error("Could not validate AI scripts", e);
		}
	}

	public static AIEngine getInstance() {
		return SingletonHolder.instance;
	}

	private static class SingletonHolder {
		protected static final AIEngine instance = new AIEngine();
	}
}
