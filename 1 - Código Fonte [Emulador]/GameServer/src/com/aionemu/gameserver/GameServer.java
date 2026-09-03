package com.aionemu.gameserver;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.Deflater;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.commons.network.NioServer;
import com.aionemu.commons.network.ServerCfg;
import com.aionemu.commons.services.CronService;
import com.aionemu.commons.utils.AEInfos;
import com.aionemu.gameserver.ai2.AI2Engine;
import com.aionemu.gameserver.cache.HTMLCache;
import com.aionemu.gameserver.configs.*;
import com.aionemu.gameserver.configs.main.*;
import com.aionemu.gameserver.configs.network.*;
import com.aionemu.gameserver.dao.PlayerDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.instance.InstanceEngine;
import com.aionemu.gameserver.model.GameEngine;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.siege.Influence;
import com.aionemu.gameserver.network.BannedMacManager;
import com.aionemu.gameserver.network.aion.GameConnectionFactoryImpl;
import com.aionemu.gameserver.network.chatserver.ChatServer;
import com.aionemu.gameserver.network.loginserver.LoginServer;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.services.*;
import com.aionemu.gameserver.services.abyss.AbyssRankUpdateService;
import com.aionemu.gameserver.services.drop.DropRegistrationService;
import com.aionemu.gameserver.services.instance.*;
import com.aionemu.gameserver.services.legion.GuildSearchService;
import com.aionemu.gameserver.services.player.BattlePassService;
import com.aionemu.gameserver.services.player.EventWindowService;
import com.aionemu.gameserver.services.player.PlayerLimitService;
import com.aionemu.gameserver.services.player.ShugoSweepService;
import com.aionemu.gameserver.spawnengine.SpawnEngine;
import com.aionemu.gameserver.spawnengine.TemporarySpawnEngine;
import com.aionemu.gameserver.taskmanager.TaskManagerFromDB;
import com.aionemu.gameserver.taskmanager.tasks.PacketBroadcaster;
import com.aionemu.gameserver.utils.*;
import com.aionemu.gameserver.utils.chathandlers.ChatProcessor;
import com.aionemu.gameserver.utils.cron.ThreadPoolManagerRunnableRunner;
import com.aionemu.gameserver.utils.gametime.DateTimeUtil;
import com.aionemu.gameserver.utils.gametime.GameTimeManager;
import com.aionemu.gameserver.utils.idfactory.IDFactory;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldEngine;
import com.aionemu.gameserver.world.geo.GeoService;
import com.aionemu.gameserver.world.zone.ZoneService;

import ch.qos.logback.classic.LoggerContext;
import ch.qos.logback.classic.joran.JoranConfigurator;
import ch.qos.logback.core.joran.spi.JoranException;

public class GameServer
{
	private static final Logger log = LoggerFactory.getLogger(GameServer.class);
	// FIX: volatile - estes campos sao escritos sempre dentro de `lock` (computeRatios/updateRatio),
	// mas eram lidos em getCountFor()/getRatiosFor()/displayRatios() sem lock nenhum. Sem volatile
	// nao ha garantia de visibilidade entre threads (a escrita ja e serializada pelo lock, entao
	// volatile aqui resolve a visibilidade da leitura sem precisar sincronizar o lado da leitura).
	private static volatile int ELYOS_COUNT = 0;
	private static volatile int ASMOS_COUNT = 0;
	private static volatile double ELYOS_RATIO = 0.0;
	private static volatile double ASMOS_RATIO = 0.0;

	private static final ReentrantLock lock = new ReentrantLock();
	public static HashSet<String> npcs_count = new HashSet<String>();
	private static Set<StartupHook> startUpHooks = new HashSet<StartupHook>();

	private static void initializeLogger() {
		new File("./log/backup/").mkdirs();
		// OTIMIZACAO: FilenameFilter anonimo -> lambda (interface funcional de um metodo so).
		File[] files = new File("log").listFiles((dir, name) -> name.endsWith(".log"));
		if (files != null && files.length > 0) {
			byte[] buf = new byte[1024];
			String outFilename = "./log/backup/" + new SimpleDateFormat("yyyy-MM-dd HHmmss").format(new Date()) + ".zip";
			boolean backupOk = false;
			// FIX: try-with-resources para garantir fechamento de out/in mesmo em erro
			// (antes, uma excecao no meio do loop deixava o ZipOutputStream e o FileInputStream
			// atual abertos - vazamento de handle de arquivo).
			try (ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(Paths.get(outFilename)))) {
				out.setMethod(ZipOutputStream.DEFLATED);
				out.setLevel(Deflater.BEST_COMPRESSION);
				for (File logFile : files) {
					try (FileInputStream in = new FileInputStream(logFile)) {
						out.putNextEntry(new ZipEntry(logFile.getName()));
						int len;
						while ((len = in.read(buf)) > 0) {
							out.write(buf, 0, len);
						}
						out.closeEntry();
					}
				}
				backupOk = true;
			} catch (IOException e) {
				// FIX: antes era um catch vazio - falha de backup era completamente silenciosa.
				log.warn("Failed to backup old log files into {}, keeping originals on disk", outFilename, e);
			}
			// FIX (bug de perda de dados): antes, cada .log original era apagado dentro do proprio
			// loop de escrita do zip, logo apos ser gravado. Se uma excecao estourasse no meio do
			// processo (ex: disco cheio no arquivo N), o zip nunca era fechado (ficava incompleto/
			// corrompido) mas os arquivos ja processados ja tinham sido apagados do disco - logs
			// perdidos permanentemente. Agora so apagamos os originais depois que o zip inteiro foi
			// escrito e fechado com sucesso.
			if (backupOk) {
				for (File logFile : files) {
					if (!logFile.delete()) {
						log.warn("Could not delete log file after backup: {}", logFile.getName());
					}
				}
			}
		}
		LoggerContext lc = (LoggerContext) LoggerFactory.getILoggerFactory();
		try {
			JoranConfigurator configurator = new JoranConfigurator();
			configurator.setContext(lc);
			lc.reset();
			configurator.doConfigure("config/slf4j-logback.xml");
		} catch (JoranException je) {
			throw new RuntimeException("Failed to configure loggers, shutting down...", je);
		}
	}

	// FIX: "throws InterruptedException" era morto - as duas unicas chamadas que poderiam
	// lancar isso (progressLatch.await()/progressLatch2.await()) ja eram capturadas
	// internamente mesmo no codigo original, entao a excecao nunca escapava deste metodo.
	public static void main(String[] args) {
		long start = System.currentTimeMillis();
		final GameEngine[] parallelEngines = {QuestEngine.getInstance(), InstanceEngine.getInstance(), AI2Engine.getInstance(), ChatProcessor.getInstance()};
		final GameEngine[] worldEngines = {WorldEngine.getInstance()};
		final CountDownLatch progressLatch = new CountDownLatch(parallelEngines.length);
		final CountDownLatch progressLatch2 = new CountDownLatch(worldEngines.length);
		initializeLogger();
		initUtilityServicesAndConfig();
		DataManager.getInstance();
		Util.printSection("IDFactory");
		IDFactory.getInstance();
		// OTIMIZACAO: for-each em vez de for indexado + "final int index = i" - o truque do
		// index existia so para capturar uma variavel "efetivamente final" na lambda; com
		// for-each cada iteracao ja cria uma variavel nova, entao a lambda captura direto.
		for (GameEngine engine : worldEngines) {
			ThreadPoolManager.getInstance().execute(() -> engine.load(progressLatch2));
		}
		try {
			progressLatch2.await();
		} catch (InterruptedException e1) {
			// FIX: antes o catch estava vazio e o flag de interrupcao era perdido. Restauramos
			// o flag (Thread.currentThread().interrupt()) para nao mascarar a interrupcao para
			// quem checar isso mais adiante, alem de logar o ocorrido.
			log.warn("Interrupted while waiting for world engines to load", e1);
			Thread.currentThread().interrupt();
		}
		Util.printSection("Zone");
		ZoneService.getInstance().load(null);
		Util.printSection("World");
		World.getInstance();
		Util.printSection("Drops");
		DropRegistrationService.getInstance();
		GameServer gs = new GameServer();
		DAOManager.getDAO(PlayerDAO.class).setPlayersOffline(false);
		BannedMacManager.getInstance();
		//Util.printSection("Cleaning");
		//DatabaseCleaningService.getInstance();
		//AbyssRankCleaningService.getInstance();
		Util.printSection("Geo Data");
		GeoService.getInstance().initializeGeo();
		System.gc();
		for (GameEngine engine : parallelEngines) {
			ThreadPoolManager.getInstance().execute(() -> engine.load(progressLatch));
		}
		try {
			progressLatch.await();
		} catch (InterruptedException e1) {
			log.warn("Interrupted while waiting for parallel engines to load", e1);
			Thread.currentThread().interrupt();
		}
		//Siege
		Util.printSection("Siege Location Data");
		SiegeService.getInstance().initSiegeLocations();
		//Rift
		Util.printSection("Rift Location Data");
		RiftService.getInstance().initRiftLocations();
		//Instance Rift
		Util.printSection("Instance Rift Location Data");
		InstanceRiftService.getInstance().initInstance();
		InstanceRiftService.getInstance().initInstanceLocations();
		SerialKillerService.getInstance().initSerialKillers();
		Util.printSection("Spawns");
		SpawnEngine.spawnAll();
		RiftService.getInstance().initRifts();
		TemporarySpawnEngine.spawnAll();
		Util.printSection("Limits");
		LimitedItemTradeService.getInstance().start();
		if (CustomConfig.LIMITS_ENABLED) {
			PlayerLimitService.getInstance().scheduleUpdate();
		}
		GameTimeManager.startClock();
		Util.printSection("Siege Schedule initialization");
		SiegeService.getInstance().initSieges();
		Util.printSection("TaskManagers");
		PacketBroadcaster.getInstance();
		GameTimeService.getInstance();
		AnnouncementService.getInstance();
		DebugService.getInstance();
		WeatherService.getInstance();
		BrokerService.getInstance();
		Influence.getInstance();
		ExchangeService.getInstance();
		PeriodicSaveService.getInstance();
		PetitionService.getInstance();
		if (AIConfig.SHOUTS_ENABLE) {
			NpcShoutsService.getInstance();
		}
		InstanceService.load();
		FlyRingService.getInstance();
		CuringZoneService.getInstance();
		RoadService.getInstance();
		HTMLCache.getInstance();
		if (RankingConfig.TOP_RANKING_UPDATE_SETTING) {
			AbyssRankUpdateService.getInstance().scheduleUpdateHour();
		} else {
			AbyssRankUpdateService.getInstance().scheduleUpdateMinute();
		}
		TaskManagerFromDB.getInstance();
		if (SiegeConfig.SIEGE_SHIELD_ENABLED) {
			ShieldService.getInstance().spawnAll();
		}
		//Dredgion & Tiak Research Base.
		if (AutoGroupConfig.AUTO_GROUP_ENABLED) {
			Util.printSection("[Dredgion]");
			DredgionService.getInstance().initDredgion();
			Util.printSection("[Tiak Research Base]");
			TiakResearchBaseService.getInstance().initTiakBase();
		}
		//Custom
		if (EventsConfig.ENABLE_EVENT_SERVICE) {
			EventService.getInstance().start();
		}
		BattlePassService.getInstance().init();
		EventWindowService.getInstance().onInit();
		AdminService.getInstance();
		Util.printSection("Guild");
		GuildSearchService.getInstance().onStart();

		Util.printSection("System");
		AEVersions.printFullVersionInfo();
		WebshopService.getInstance();
		RestartService.getInstance().onStart();
		ShugoSweepService.getInstance().init();
		QuestUpdateService.getInstance().onStart();
		System.gc();
		AEInfos.printAllInfos();
		Util.printSection("GameServerLog");
		log.info("Classic Server started in " + (System.currentTimeMillis() - start) / 1000 + " seconds.");
		System.out.println(
				"    ___    ________  _   __   ________    ___   __________ __________\n" +
						"   /   |  /  _/ __ \\/ | / /  / ____/ /   /   | / ___/ ___//  _/ ____/\n" +
						"  / /| |  / // / / /  |/ /  / /   / /   / /| | \\__ \\\\__ \\ / // /     \n" +
						" / ___ |_/ // /_/ / /|  /  / /___/ /___/ ___ |___/ /__/ // // /___   \n" +
						"/_/  |_/___/\\____/_/ |_/   \\____/_____/_/  |_/____/____/___/\\____/   ");
		System.out.println("                        Versão 5.0 EU (GameForge)");
		System.out.println("               Desenvolvido por: Lost Academy Team & Durak\n");
		gs.startServers();
		Runtime.getRuntime().addShutdownHook(ShutdownHook.getInstance());
		if (GSConfig.ENABLE_RATIO_LIMITATION) {
			// OTIMIZACAO: StartupHook anonimo -> lambda, ja que StartupHook e uma interface
			// funcional (um metodo so).
			addStartupHook(() -> {
				lock.lock();
				try {
					ASMOS_COUNT = DAOManager.getDAO(PlayerDAO.class).getCharacterCountForRace(Race.ASMODIANS);
					ELYOS_COUNT = DAOManager.getDAO(PlayerDAO.class).getCharacterCountForRace(Race.ELYOS);
					computeRatios();
				} catch (Exception e) {
					// FIX: antes era um catch vazio - se a query de uma das racas falhasse, o
					// ratio ficava calculado com dado parcial sem ninguem saber.
					log.warn("Failed to compute initial faction ratio", e);
				} finally {
					lock.unlock();
				}
				displayRatios(false);
			});
		}
		onStartup();
		ManagementService.getInstance().start();
		//InGameWebServer.getInstance().start();
	}

	private void startServers() {
		Util.printSection("Starting Network");
		NioServer nioServer = new NioServer(NetworkConfig.NIO_READ_WRITE_THREADS, new ServerCfg(NetworkConfig.GAME_BIND_ADDRESS, NetworkConfig.GAME_PORT, "Game Connections", new GameConnectionFactoryImpl()));
		LoginServer ls = LoginServer.getInstance();
		ChatServer cs = ChatServer.getInstance();
		ls.setNioServer(nioServer);
		cs.setNioServer(nioServer);
		nioServer.connect();
		ls.connect();
		if (GSConfig.ENABLE_CHAT_SERVER)
			cs.connect();
	}

	private static void initUtilityServicesAndConfig() {
		Thread.setDefaultUncaughtExceptionHandler(new ThreadUncaughtExceptionHandler());
		CronService.initSingleton(ThreadPoolManagerRunnableRunner.class);
		Config.load();
		DateTimeUtil.init();
		Util.printSection("DataBase");
		DatabaseFactory.init();
		DAOManager.init();
		Util.printSection("Threads");
		ThreadConfig.load();
		ThreadPoolManager.getInstance();
	}

	public static synchronized void addStartupHook(StartupHook hook) {
		if (startUpHooks != null)
			startUpHooks.add(hook);
		else
			hook.onStartup();
	}

	private synchronized static void onStartup() {
		final Set<StartupHook> startupHooks = startUpHooks;
		startUpHooks = null;
		for (StartupHook hook : startupHooks)
			hook.onStartup();
	}

	public static void updateRatio(Race race, int i) {
		lock.lock();
		try {
			switch (race) {
				case ASMODIANS:
					ASMOS_COUNT += i;
					break;
				case ELYOS:
					ELYOS_COUNT += i;
					break;
				default:
					break;
			}
			computeRatios();
		}
		catch (Exception e) {
			// FIX: antes era um catch vazio.
			log.warn("Failed to update faction ratio for race {}", race, e);
		}
		finally {
			lock.unlock();
		}
		displayRatios(true);
	}

	private static void computeRatios() {
		if (ASMOS_COUNT <= GSConfig.RATIO_MIN_CHARACTERS_COUNT && ELYOS_COUNT <= GSConfig.RATIO_MIN_CHARACTERS_COUNT) {
			ASMOS_RATIO = ELYOS_RATIO = 50.0;
		} else {
			ASMOS_RATIO = ASMOS_COUNT * 100.0 / (ASMOS_COUNT + ELYOS_COUNT);
			ELYOS_RATIO = ELYOS_COUNT * 100.0 / (ASMOS_COUNT + ELYOS_COUNT);
		}
	}

	private static void displayRatios(boolean updated) {
		log.info("FACTIONS RATIO " + (updated ? "UPDATED " : "") + ": E " + String.format("%.1f", ELYOS_RATIO) + " % / A " + String.format("%.1f", ASMOS_RATIO) + " %");
	}

	public static double getRatiosFor(Race race) {
		switch (race) {
			case ASMODIANS:
				return ASMOS_RATIO;
			case ELYOS:
				return ELYOS_RATIO;
			default:
				return 0.0;
		}
	}

	public static int getCountFor(Race race) {
		switch (race) {
			case ASMODIANS:
				return ASMOS_COUNT;
			case ELYOS:
				return ELYOS_COUNT;
			default:
				return 0;
		}
	}

	@FunctionalInterface
	public interface StartupHook {
		void onStartup();
	}
}