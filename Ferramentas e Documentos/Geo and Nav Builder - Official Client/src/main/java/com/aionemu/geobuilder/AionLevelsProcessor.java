package com.aionemu.geobuilder;

import com.aionemu.geobuilder.entries.*;
import com.aionemu.geobuilder.loaders.BrushLstLoader;
import com.aionemu.geobuilder.loaders.CgfLoader;
import com.aionemu.geobuilder.loaders.EntityLoader;
import com.aionemu.geobuilder.loaders.ObjectsLstLoader;
import com.aionemu.geobuilder.meshData.CollisionIntention;
import com.aionemu.geobuilder.meshData.MeshData;
import com.aionemu.geobuilder.meshData.MeshFace;
import com.aionemu.geobuilder.meshData.ObjectMeshData;
import com.aionemu.geobuilder.pakaccessor.PakFile;
import com.aionemu.geobuilder.utils.Matrix4f;
import com.aionemu.geobuilder.utils.PathSanitizer;
import com.aionemu.geobuilder.utils.Vector3;
import com.aionemu.geobuilder.utils.XmlParser;
import com.beust.jcommander.Parameter;
import com.beust.jcommander.converters.PathConverter;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;

import org.recast4j.recast.RecastBuilder;
import org.recast4j.recast.RecastBuilder.RecastBuilderResult;
import org.recast4j.recast.RecastConfig;
import org.recast4j.recast.PolyMesh;
import org.recast4j.recast.geom.SimpleInputGeomProvider;
import org.recast4j.recast.RecastConstants;
import org.recast4j.recast.RecastBuilderConfig;
import org.recast4j.recast.AreaModification;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ShortBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.NotDirectoryException;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class AionLevelsProcessor {

  @Parameter(description = "<client path>", converter = PathConverter.class, required = true)
  protected Path clientPath;

  @Parameter(names = "-lvl", description = "Limit file generation to given level ID(s) (default: all levels) Example: -lvl 110010000 -lvl 110020000", order = 1)
  protected Set<String> levelIds;

  @Parameter(names = "-w", description = "Path to server world_maps.xml or client WorldId.xml (default: client WorldId.xml)", order = 2)
  protected Path worldIdPath;

  @Parameter(names = "-o", description = "Path to the output folder", order = 3)
  protected Path outPath = Path.of("./out");

  @Parameter(names = "-am", description = "Generate all terrain materials (default: only skill-using materials)", order = 4)
  protected boolean allTerrainMaterials;

  @Parameter(names = "-do", description = "Disable oxipng optimizer (used for improved terrain PNG compression)", order = 5)
  protected boolean disableOxipng;

  @Parameter(names = "-dc", description = "Disable mesh compacting (removal of unused or duplicate vertices and degenerate or duplicate faces)", order = 6)
  protected boolean disableMeshCompacting;

  @Parameter(names = "-ds", description = "Disable mesh sorting to keep original order of vertices, faces and the face winding order", order = 7)
  protected boolean disableMeshSorting;

  @Parameter(names = "-v", description = "Activate verbose logging", order = 8)
  protected boolean verbose;

  private static final Logger log = Logger.getLogger("GeoBuilder");
  private static final Logger oxipngLogger = Logger.getLogger("oxipng");

  static {
    System.setProperty("java.util.logging.SimpleFormatter.format", "%1$tT [%4$s] %5$s%6$s");
    log.setUseParentHandlers(false);
    oxipngLogger.setUseParentHandlers(false);
    StreamHandler consoleHandler = new StreamHandler(System.out, new SimpleFormatter() {
      @Override
      public String format(LogRecord record) {
        String msg = super.format(record);
        boolean isTemporaryLine = msg.endsWith("\r");
        if (isTemporaryLine) // remove carriage return char temporarily to insert the "Erase in Line" ANSI escape code before it
          msg = msg.substring(0, msg.length() - 1);
        if (record.getLevel() == Level.SEVERE)
          msg = "\u001B[31m" + msg + "\u001b[0m";
        else if (record.getLevel() == Level.WARNING)
          msg = "\u001B[33m" + msg + "\u001b[0m";
        else if (record.getLevel().intValue() < Level.INFO.intValue())
          msg = "\u001B[37m" + msg + "\u001b[0m";
        return isTemporaryLine ? msg + "\033[K\r" : msg + "\033[K" + System.lineSeparator();
      }
    }) {
      @Override
      public void publish(LogRecord record) {
        super.publish(record);
        flush();
      }
    };
    consoleHandler.setLevel(Level.ALL);
    log.addHandler(consoleHandler);
    oxipngLogger.addHandler(consoleHandler);
  }

  private final Set<String> requiredCgfs = ConcurrentHashMap.newKeySet();
  private final Set<String> requiredDoorCgas = ConcurrentHashMap.newKeySet();

  private final Set<String> processedCgfs = ConcurrentHashMap.newKeySet();
  private final Set<String> emptyCgfs = ConcurrentHashMap.newKeySet();

  protected void process() {
    log.setLevel(verbose ? Level.ALL : Level.INFO);
    oxipngLogger.setLevel(verbose ? Level.ALL : Level.WARNING);
    long time = System.currentTimeMillis();
    try {
      log.info("Loading available levels\r");
      List<LevelData> levels = findLevelsToProcess();
      if (!levels.isEmpty()) {
        Path geoOutPath = outPath.resolve("geo");
        Path navOutPath = outPath.resolve("nav");

        Files.createDirectories(geoOutPath);
        Files.createDirectories(navOutPath);

        boolean modelsMeshExists = Files.exists(geoOutPath.resolve("models.mesh"));
        List<LevelData> levelsToProcess = levels.stream().filter(l -> {
          boolean geoExists = Files.exists(geoOutPath.resolve(l.levelId + ".geo"));
          boolean navExists = Files.exists(navOutPath.resolve(l.levelId + ".nav"));
          boolean pngExists = !l.useTerrain || Files.exists(geoOutPath.resolve(l.levelId + ".png"));
          return !(geoExists && navExists && pngExists);
        }).toList();

        if (levelsToProcess.isEmpty() && modelsMeshExists) {
          log.info("All requested levels (" + levels.size() + ") already have .geo, .nav, models.mesh, and terrain files generated. Skipping all processing!");
          log.info("Output folder: " + outPath.toRealPath());
          log.info("Processing time: " + (System.currentTimeMillis() - time) / 1000 + " s");
          return;
        }

        int materialsCount = CgfLoader.loadMaterials(clientPath);
        log.info("Found " + materialsCount + " materials");
        Map<String, Short> houseAddresses = loadHouseAddresses();
        processLevels(levels, houseAddresses);
        Thread terrainTask = Thread.startVirtualThread(() -> createTerrains(geoOutPath, levels));
        List<Path> meshPaks = collectMeshFilePaths();
        Map<String, List<MeshData>> availableMeshes = createMeshes(geoOutPath, meshPaks, levels);
        createGeoFiles(geoOutPath, levels);
        if (terrainTask.isAlive()) {
          log.info("Waiting for terrain generation to finish\r");
          oxipngLogger.setLevel(verbose ? Level.ALL : Level.INFO);
          terrainTask.join();
        }
        createNavFiles(navOutPath, levels, availableMeshes);
        log.info("Output folder: " + outPath.toRealPath());
        log.info("Processing time: " + (System.currentTimeMillis() - time) / 1000 + " s");
      }
    } catch (Throwable t) {
      log.log(Level.SEVERE, "", t);
    }
  }

  private List<LevelData> findLevelsToProcess() throws JDOMException, IOException {
    // Read world_maps.xml or WorldId.xml and find Levels to process
    String worldIdXml = worldIdPath == null ? "client WorldId.xml" : worldIdPath.getFileName().toString();

    Path levelsRootFolder = clientPath.resolve("Levels");
    Map<String, File> levelsByName = Files.list(levelsRootFolder)
        .map(Path::toFile)
        .filter(file -> file.isDirectory() && !file.getName().equalsIgnoreCase("common"))
        .collect(Collectors.toMap(file -> file.getName().toLowerCase(), file -> file));
    log.fine("Found " + levelsByName.size() + " levels in " + levelsRootFolder);

    // read client maps
    Document document = worldIdPath == null ? XmlParser.parse(getClientWorldIdFile()) : new SAXBuilder().build(worldIdPath.toFile());
    Element rootNode = document.getRootElement();
    boolean clientXml = rootNode.getName().equalsIgnoreCase("world_id");
    List<Element> worldIdXmlLevels = clientXml ? rootNode.getChildren("data") : rootNode.getChildren("map");
    log.fine("Validating " + worldIdXmlLevels.size() + " levels referenced in " + worldIdXml);

    List<LevelData> levels = new ArrayList<>();
    // buggy client files are normal, only log warning when we generate from server file or -lvl parameter
    Level logLevel = levelIds == null && clientXml ? Level.FINE : Level.WARNING;
    for (Element element : worldIdXmlLevels) {
      String levelId = element.getAttributeValue("id");
      String levelName = clientXml ? element.getText() : element.getAttributeValue("cName");
      File levelClientFolder = levelsByName.remove(levelName.toLowerCase());
      if (levelIds == null || levelIds.contains(levelId)) {
        if (levelClientFolder == null) {
          log.log(logLevel, "Ignoring " + levelName + ": Folder missing in " + levelsRootFolder);
        } else {
          Path folderPath = levelClientFolder.toPath();
          List<Path> levelPaks;
          try (Stream<Path> s = Files.list(folderPath)) {
            levelPaks = s.filter(p -> p.getFileName().toString().toLowerCase().endsWith(".pak"))
                .sorted(Comparator.comparingInt(this::getLevelPakPriority))
                .collect(Collectors.toList());
          }
          boolean hasLevelPak = levelPaks.stream().anyMatch(p -> {
            String n = p.getFileName().toString().toLowerCase();
            return n.equals("level.pak") || (n.startsWith("z_") && n.contains("level"));
          });
          if (hasLevelPak)
            levels.add(new LevelData(levelId, levelName, folderPath, levelPaks));
          else
            log.log(logLevel, "Ignoring " + levelName + ": Level.pak / z_Level.pak missing");
        }
      }
    }
    if (!levelsByName.isEmpty()) {
      log.fine(levelsByName.size() + " levels from " + levelsRootFolder + " were not referenced in " + worldIdXml + ": " + levelsByName.values().stream().map(File::getName).sorted(String.CASE_INSENSITIVE_ORDER).collect(Collectors.joining(", ")));
    }
    if (levels.isEmpty() && levelIds != null && levelIds.size() == 1) {
      log.info("Level " + levelIds.iterator().next() + " wasn't found or is not processable");
    } else {
      String num = levelIds == null && clientXml ? levels.size() + "" : levels.size() + "/" + (levelIds == null ? worldIdXmlLevels.size() : levelIds.size());
      log.info("Found " + num + " processable level" + (levels.size() == 1 ? "" : "s"));
    }
    return levels;
  }

  private Map<String, Short> loadHouseAddresses() throws IOException {
    log.info("Loading available house addresses\r");
    Path housingPakPath = clientPath.resolve("Data/Housing/Housing.pak");
    if (!Files.exists(housingPakPath)) {
      log.warning("Housing.pak not found at " + housingPakPath + ", skipping house addresses loading.");
      return Collections.emptyMap();
    }
    try (PakFile pakFile = PakFile.open(housingPakPath)) {
      if (!pakFile.contains("client_housing_address.xml")) {
        log.warning("client_housing_address.xml not found in Housing.pak, skipping house addresses loading.");
        return Collections.emptyMap();
      }
      Document document = XmlParser.parse(pakFile.unpak("client_housing_address.xml"));
      Element rootNode = document.getRootElement();
      Map<String, Short> addressIdsByName = new HashMap<>();
      for (Element address : rootNode.getChildren("client_housing_address")) {
        String name = address.getChildText("name");
        short id = Short.parseShort(address.getChildText("id"));
        if (addressIdsByName.putIfAbsent(name, id) != null)
          log.warning("Duplicate house name in client_housing_address.xml: " + name);
      }
      log.info("Found " + addressIdsByName.size() + " house addresses");
      return addressIdsByName;
    }
  }


  private ByteBuffer getClientWorldIdFile() throws IOException {
    try (PakFile pakFile = PakFile.open(clientPath.resolve("Data/World/World.pak"))) {
      return pakFile.unpak("worldid.xml");
    }
  }

  private ByteBuffer getClientHouseAddressFile() throws IOException {
    try (PakFile pakFile = PakFile.open(clientPath.resolve("Data/Housing/Housing.pak"))) {
      return pakFile.unpak("client_housing_address.xml");
    }
  }

  private void processLevels(List<LevelData> levels, Map<String, Short> houseAddresses) {
    levels.parallelStream().forEach(level -> {
      parseLevelPak(level, houseAddresses);
      level.streamAllMeshFileNames().filter(m -> !isIgnored(m, level)).forEach(requiredCgfs::add);
    });
    log.info("Found " + requiredCgfs.size() + " mesh references in " + levels.size() + " level" + (levels.size() == 1 ? "" : "s"));
  }

  private int getLevelPakPriority(Path path) {
    String name = path.getFileName().toString().toLowerCase();
    if (name.startsWith("z_") && name.contains("level")) return 1;
    if (name.startsWith("z_") || name.startsWith("z")) return 2;
    if (name.equals("level.pak")) return 3;
    return 4;
  }

  private void parseLevelPak(LevelData level, Map<String, Short> houseAddresses) {
    String paksDesc = level.levelPakFiles.stream().map(p -> p.getFileName().toString()).collect(Collectors.joining(", "));
    log.info(level + ": Processing (" + paksDesc + ")\r");
    String levelName = level.levelName.toLowerCase();
    boolean needsBrushLst = !(level.isTestLevel() || levelName.contains("system_basic") || levelName.endsWith("prison"));

    List<PakFile> openPaks = new ArrayList<>();
    try {
      for (Path pakPath : level.levelPakFiles) {
        try {
          openPaks.add(PakFile.open(pakPath));
        } catch (Exception e) {
          log.warning(level + ": Failed to open pak " + pakPath.getFileName() + ": " + e.getMessage());
        }
      }
      if (openPaks.isEmpty()) {
        log.warning("No accessible pak files for " + level);
        return;
      }

      PakFile levelDataPak = findPakWithFile(openPaks, "leveldata.xml");
      if (levelDataPak != null) {
        processPakFile(levelDataPak, "leveldata.xml", level, buffer -> parseLevelData(buffer, level));
      } else {
        log.warning(level + ": leveldata.xml missing in all archives");
      }

      if (level.useTerrain) {
        PakFile terrainPak = findPakWithFile(openPaks, "terrain/land_map.h32");
        if (terrainPak != null) {
          processPakFile(terrainPak, "terrain/land_map.h32", level, buffer -> level.terrain.load(buffer, allTerrainMaterials));
        } else {
          log.warning(level + ": terrain/land_map.h32 missing in all archives");
        }
      } else {
        log.fine(level + ": skipped loading terrain (disabled in leveldata.xml)");
      }

      if (level.missionPath != null) {
        PakFile missionPak = findPakWithFile(openPaks, level.missionPath);
        if (missionPak != null) {
          processPakFile(missionPak, level.missionPath, level, buffer -> level.entityEntries = EntityLoader.loadPlaceables(buffer, houseAddresses));
          if (level.entityEntries != null) {
            level.entityEntries.stream().filter(e -> e.type == EntryType.DOOR).map(e -> e.mesh).forEach(requiredDoorCgas::add);
          }
        }
      }

      PakFile brushPak = findPakWithAnyFile(openPaks, "brush.lst", "brush.lstd");
      if (brushPak != null) {
        String brushFile = brushPak.contains("brush.lst") ? "brush.lst" : "brush.lstd";
        if (brushFile.equals("brush.lstd")) {
          log.fine(level + ": Using brush.lstd (newer client format)");
        }
        processPakFile(brushPak, brushFile, level, buffer -> level.brushMeshData = BrushLstLoader.load(buffer));
      } else {
        log.log(needsBrushLst ? Level.WARNING : Level.FINE, level + ": does not contain brush.lst or brush.lstd");
      }

      PakFile objectsPak = findPakWithFile(openPaks, "objects.lst");
      if (objectsPak != null) {
        processPakFile(objectsPak, "objects.lst", level, buffer -> ObjectsLstLoader.load(buffer, level));
      } else {
        log.fine(level + ": does not contain objects.lst");
      }
      log.info(level + ": Processing finished\r");
    } catch (Exception e) {
      log.log(Level.SEVERE, "Error processing " + level, e);
    } finally {
      for (PakFile pak : openPaks) {
        try { pak.close(); } catch (Exception ignored) {}
      }
    }
  }

  private PakFile findPakWithFile(List<PakFile> paks, String fileName) {
    for (PakFile pak : paks) {
      if (pak.contains(fileName)) {
        return pak;
      }
    }
    return null;
  }

  private PakFile findPakWithAnyFile(List<PakFile> paks, String... fileNames) {
    for (PakFile pak : paks) {
      for (String fn : fileNames) {
        if (pak.contains(fn)) {
          return pak;
        }
      }
    }
    return null;
  }

  private void parseLevelData(ByteBuffer leveldataXml, LevelData level) throws Exception {
    Element rootNode = XmlParser.parse(leveldataXml).getRootElement();
    Element levelInfo = rootNode.getChild("LevelInfo");
    int heightmapXSize = XmlParser.parseSafeInt(levelInfo, "HeightmapXSize", 0);
    int heightmapYSize = XmlParser.parseSafeInt(levelInfo, "HeightmapYSize", 0);
    int heightmapUnitSize = XmlParser.parseSafeInt(levelInfo, "HeightmapUnitSize", 0);

    Element surfaceTypes = rootNode.getChild("SurfaceTypes");
    List<Element> objects = surfaceTypes != null ? surfaceTypes.getChildren() : Collections.emptyList();
    level.terrain = new Terrain(heightmapXSize, heightmapYSize, heightmapUnitSize);
    level.terrain.materialIds = new byte[objects.size()];
    for (int i = 0; i < objects.size(); i++) {
      String material = objects.get(i).getAttributeValue("Material");
      if (material != null) {
        material = material.trim();
        if (!material.isEmpty()) {
          int matId = CgfLoader.getMaterialId(material);
          if (matId == -1) {
            log.warning(level + ": Missing material: " + material + ", using fallback ID 0");
            matId = 0;
          } else if (matId > 0xFF) {
            log.warning(level + ": Encountered out of range material ID " + matId + " for " + material + ", using fallback ID 0");
            matId = 0;
          }
          level.terrain.materialIds[i] = (byte) matId;
        }
      }
    }

    Element vegetationNode = rootNode.getChild("Vegetation");
    List<Element> vegetation = vegetationNode != null ? vegetationNode.getChildren() : Collections.emptyList();
    if (!vegetation.isEmpty()) {
      level.objectMeshData = new ObjectMeshData();
      level.objectMeshData.meshFiles = new ArrayList<>(vegetation.size());
      for (Element element : vegetation) {
        String fileName = element.getAttributeValue("FileName");
        if (fileName != null) {
          level.objectMeshData.meshFiles.add(PathSanitizer.sanitize(fileName));
        }
      }
    }

    Element missions = rootNode.getChild("Missions");
    Element mission = missions != null ? missions.getChild("Mission") : null;
    level.missionPath = mission != null ? mission.getAttributeValue("File") : null;

    boolean useTerrain = true;
    if (mission != null) {
      Element levelOption = mission.getChild("LevelOption");
      if (levelOption != null) {
        Element initialize = levelOption.getChild("Initialize");
        if (initialize != null) {
          useTerrain = XmlParser.parseBoolOrInt(initialize, "Render_Terrain", true);
        }
      }
    }
    level.useTerrain = useTerrain;
  }

  private void processPakFile(PakFile pakFile, String fileName, LevelData level, ThrowingConsumer<ByteBuffer> consumer) {
    log.fine(level + ": Processing " + fileName + '\r');
    try {
      consumer.consume(pakFile.unpak(fileName));
      log.fine(level + ": Processing " + fileName + " finished\r");
    } catch (Exception e) {
      log.log(Level.SEVERE, level + ": Error processing " + fileName, e);
    }
  }

  private List<Path> collectMeshFilePaths() throws IOException {
    log.info("Collecting mesh file paths\r");
    List<Path> clientMeshFiles = findMeshPaks("Levels/common", "Levels/idabpro", "Objects");

    if (clientMeshFiles.isEmpty())
      log.warning("Found no mesh archives in the Aion client");
    else
      log.info("Found " + clientMeshFiles.size() + " mesh archives");

    return clientMeshFiles;
  }

  private List<Path> findMeshPaks(String... rootFolders) throws IOException {
    List<Path> meshPaks = new ArrayList<>();
    for (String relativeFolderPath : rootFolders) {
      Path folder = clientPath.resolve(relativeFolderPath);
      if (!Files.isDirectory(folder))
        throw new NotDirectoryException(folder.toString());
      Files.find(folder, Integer.MAX_VALUE, (path, attributes) -> {
        if (!attributes.isRegularFile()) return false;
        String name = path.getFileName().toString().toLowerCase();
        return name.matches(".+_mesh.*\\.pak") || name.matches(".*meshes.*\\.pak")
            || name.equals("idabpro.pak") || (name.startsWith("z_") && name.endsWith(".pak"));
      }).forEach(meshPaks::add);
    }
    meshPaks.sort(Comparator.comparingInt(p -> p.getFileName().toString().toLowerCase().startsWith("z_") ? 0 : 1));
    return meshPaks;
  }

  private Map<String, List<MeshData>> createMeshes(Path outputFolder, List<Path> meshPaks, List<LevelData> levels) throws IOException {
    Map<String, List<MeshData>> availableMeshes = new ConcurrentHashMap<>();
    if (requiredCgfs.isEmpty()) {
      log.info("No referenced meshes, skipping generating mesh file");
      return availableMeshes;
    }
    log.info("Generating mesh file\r");
    AtomicInteger totalMeshes = new AtomicInteger(requiredCgfs.size());
    meshPaks.parallelStream().forEach(meshPakFile -> {
      if (requiredCgfs.isEmpty())
        return;
      try (PakFile pakFile = PakFile.open(meshPakFile, clientPath)) {
        processCgfFiles(pakFile, availableMeshes, totalMeshes);
      } catch (Exception e) {
        log.log(Level.SEVERE, "", e);
      }
    });
    List<String> missingMeshes = new ArrayList<>(requiredCgfs);
    int processedCount = processedCgfs.size() + missingMeshes.size();
    if (processedCount != totalMeshes.get()) // should only happen on parsing/processing error
      log.warning("Only " + processedCount + " of " + totalMeshes + " meshes have been successfully processed!");
    log.info("Found " + availableMeshes.size() + " valid meshes of " + totalMeshes + " total (skipped " + emptyCgfs.size() + " empty and " + missingMeshes.size() + " missing ones)");
    if (!missingMeshes.isEmpty()) {
      Set<String> missingTownGrowthMeshes = levels.stream().flatMap(l -> l.entityEntries.stream().flatMap(e -> e instanceof TownEntry townEntry ? townEntry.getHigherLevelMeshNames() : Stream.empty())).filter(missingMeshes::contains).collect(Collectors.toSet());
      Set<String> missingTestLevelMeshes = levels.stream().filter(LevelData::isTestLevel).flatMap(LevelData::streamAllMeshFileNames).filter(missingMeshes::contains).collect(Collectors.toSet());
      if (!missingTownGrowthMeshes.isEmpty()) {
        log.fine(missingTownGrowthMeshes.size() + " missing meshes are optional town growth meshes");
      }
      if (!missingTestLevelMeshes.isEmpty()) {
        log.fine(missingTestLevelMeshes.size() + " missing meshes are on test maps: " + missingTestLevelMeshes.stream().sorted().collect(Collectors.joining(", ")));
      }
      missingMeshes.removeAll(missingTownGrowthMeshes);
      missingMeshes.removeAll(missingTestLevelMeshes);
      if (!missingMeshes.isEmpty()) {
        log.warning(missingMeshes.size() + " missing meshes may exist in an unscanned archive: " + missingMeshes.stream().sorted().collect(Collectors.joining(", ")));
      }
    }
    if (!disableMeshCompacting)
      compact(availableMeshes.values());

    log.info("Merging duplicate meshes\r");
    if (!disableMeshSorting)
      availableMeshes.values().parallelStream().forEach(m -> m.forEach(MeshData::sort)); // this helps find duplicates
    Map<List<MeshData>, String> uniqueMeshes = availableMeshes.entrySet().stream()
        .sorted(Map.Entry.comparingByKey()) // sort to generate .mesh files with deterministic, comparable hashes
        .collect(Collectors.groupingBy(Map.Entry::getValue, LinkedHashMap::new, Collectors.mapping(Map.Entry::getKey, Collectors.joining("|"))));
    int duplicateCount = availableMeshes.size() - uniqueMeshes.size();
    String meshes = uniqueMeshes.size() + " unique meshes (" + duplicateCount + " duplicates have been merged)";
    log.info("Writing " + meshes + '\r');

    Path meshFile = outputFolder.resolve("models.mesh");
    try (DataOutputStream stream = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(meshFile)))) {
      uniqueMeshes.forEach((data, paths) -> writeMeshes(paths, data, stream));
    }
    log.info("Created " + meshFile.getFileName() + " with " + meshes);
    return availableMeshes;
  }

  private void compact(Collection<List<MeshData>> meshes) {
    log.info("Compacting meshes\r");
    AtomicInteger oldSize = new AtomicInteger(), newSize = new AtomicInteger();
    meshes.parallelStream().forEach(m -> m.parallelStream().forEach(meshData -> {
      oldSize.addAndGet(meshData.getSize());
      meshData.compact();
      newSize.addAndGet(meshData.getSize());
    }));
    log.info("Compacted meshes to " + Math.round(10000f * newSize.get() / oldSize.get()) / 100f + " % of their original size (before: " + (oldSize.get() / 1024 / 1024) + " MiB, after: " + (newSize.get() / 1024 / 1024) + " MiB)");
  }

  private void createTerrains(Path outputFolder, List<LevelData> levels) {
    log.info("Generating terrain files" + (disableOxipng ? '\r' : " using oxipng optimization"));
    Set<String> skipped = ConcurrentHashMap.newKeySet();
    Map<ShortBuffer, Terrain.Heightmap> heightmaps = new ConcurrentHashMap<>();
    Map<ByteBuffer, Terrain.Heightmap> materials = new ConcurrentHashMap<>();
    levels.parallelStream().forEach(level -> {
      if (!level.useTerrain) {
        skipped.add(level.levelId);
        return;
      }
      heightmaps.compute(level.terrain.heightmap, (k, heightmap) -> {
        if (heightmap == null)
          heightmap = level.terrain.createHeightmap();
        heightmap.fileNames.add(level.levelId);
        return heightmap;
      });
      if (level.terrain.materials != null) {
        materials.compute(level.terrain.materials, (k, matmap) -> {
          if (matmap == null)
            matmap = level.terrain.createMaterialmap();
          matmap.fileNames.add(level.levelId);
          return matmap;
        });
      }
    });
    Stream.concat(heightmaps.values().stream(), materials.values().stream())
        .parallel()
        .forEach(heightmap -> heightmap.write(outputFolder, disableOxipng, oxipngLogger));
    log.info("Created " + heightmaps.size() + " unique heightmaps and " + materials.size() + " unique material maps" + (skipped.isEmpty() ? "" : " (skipped " + skipped.size() + " levels with disabled terrain: " + skipped.stream().sorted().collect(Collectors.joining(", ")) + ")"));
  }

  private void createGeoFiles(Path outputFolder, List<LevelData> levels) {
    log.info("Generating geo files\r");
    Set<String> skipped = ConcurrentHashMap.newKeySet();
    AtomicInteger i = new AtomicInteger();
    AtomicInteger skippedExisting = new AtomicInteger();
    levels.parallelStream().forEach(level -> {
      try {
        Path geoFile = outputFolder.resolve(level.levelId + ".geo");
        if (Files.exists(geoFile)) {
          skippedExisting.incrementAndGet();
          log.info(level.levelName + ": " + level.levelId + ".geo already exists, skipping.\r");
          return;
        }
        if (createGeoFile(outputFolder, level)) {
          log.info("[" + i.incrementAndGet() + "/" + (levels.size() - skipped.size()) + "] " + level.levelName + ": " + level.levelId + ".geo Done\r");
        } else {
          skipped.add(level.levelId);
        }
      } catch (Exception e) {
        log.log(Level.SEVERE, "Error generating " + level.levelId + ".geo", e);
      }
    });
    log.info("Created " + i.get() + " geo file" + (i.get() == 1 ? "" : "s") + (skippedExisting.get() == 0 ? "" : " (" + skippedExisting.get() + " already existed)") + (skipped.isEmpty() ? "" : " (skipped " + skipped.size() + " levels without entities: " + skipped.stream().sorted().collect(Collectors.joining(", ")) + ")"));
    int notGenerated = levels.size() - i.get() - skipped.size() - skippedExisting.get();
    if (notGenerated > 0)
      log.warning(notGenerated + " file" + (notGenerated == 1 ? "" : "s") + " could not be generated.");
  }

  private boolean createGeoFile(Path outputFolder, LevelData level) throws IOException {
    if (level.streamAllMeshFileNames().findAny().isEmpty()) {
      return false;
    }
    Path geoFile = outputFolder.resolve(level.levelId + ".geo");
    if (Files.exists(geoFile)) {
      log.fine(level + ": Skipping existing " + level.levelId + ".geo");
      return true;
    }
    try (DataOutputStream stream = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(geoFile)))) {
      // brushes
      if (level.brushMeshData != null) {
        for (BrushEntry entry : level.brushMeshData.brushEntries) {
          String meshFileName = level.brushMeshData.meshFileNames.get(entry.meshIndex);
          if (shouldSkip(meshFileName, level))
            continue;
          byte[] meshFileNameBytes = meshFileName.getBytes(StandardCharsets.US_ASCII);
          stream.writeShort(meshFileNameBytes.length);
          stream.write(meshFileNameBytes);
          float[] matrix = entry.matrix;
          // pos vector
          for (int i = 0; i < 3; i++) { // 3, 7, 11
            stream.writeFloat(matrix[i * 4 + 3]);
          }
          // orientation matrix
          for (int i = 0; i < 3; i++) { // 0, 1, 2; 4, 5, 6; 8, 9, 10
            stream.writeFloat(matrix[i * 4]);
            stream.writeFloat(matrix[i * 4 + 1]);
            stream.writeFloat(matrix[i * 4 + 2]);
          }
          // scale, always 1 in brushList
          stream.writeFloat(1); // x
          stream.writeFloat(1); // y
          stream.writeFloat(1); // z
          stream.writeByte(entry.type.getId());
          stream.writeShort(entry.eventType);
          stream.writeByte(0);
        }
      }

      // vegetation
      if (level.objectMeshData != null) {
        for (ObjectEntry entry : level.objectMeshData.objectEntries) {
          String meshFileName = level.objectMeshData.meshFiles.get(entry.meshIndex);
          if (shouldSkip(meshFileName, level))
            continue;
          byte[] meshFileNameBytes = meshFileName.getBytes(StandardCharsets.US_ASCII);
          stream.writeShort(meshFileNameBytes.length);
          stream.write(meshFileNameBytes);
          // pos
          stream.writeFloat(entry.x);
          stream.writeFloat(entry.y);
          stream.writeFloat(entry.z);
          // transform
          Matrix4f matrix = Matrix4f.createRotationMatrix(entry.rotX, entry.rotY, entry.rotZ);
          stream.writeFloat(matrix.m11);
          stream.writeFloat(matrix.m21);
          stream.writeFloat(matrix.m31);
          stream.writeFloat(matrix.m12);
          stream.writeFloat(matrix.m22);
          stream.writeFloat(matrix.m32);
          stream.writeFloat(matrix.m13);
          stream.writeFloat(matrix.m23);
          stream.writeFloat(matrix.m33);


          stream.writeFloat(entry.scale); // x
          stream.writeFloat(entry.scale); // y
          stream.writeFloat(entry.scale); // z

          stream.writeByte(entry.type.getId());
          stream.writeShort(0); // event id
          stream.writeByte(0);
        }
      }

      for (EntityEntry entry : level.entityEntries) {
        if (entry instanceof HouseEntry houseEntry) {
          writeHouseEntry(houseEntry, stream, level);
        } else {
          writeEntityEntry(entry, stream, level);
        }
      }
    }
    return true;
  }

  private boolean shouldSkip(String meshFileName, LevelData level) {
    if (!processedCgfs.contains(meshFileName)) { // skip ignored or missing cgf
      if (!isIgnored(meshFileName, level) && !requiredCgfs.contains(meshFileName))
        log.warning(level + ": " + meshFileName + " was not processed");
      return true;
    }
    return emptyCgfs.contains(meshFileName);
  }

  private void writeHouseEntry(HouseEntry entry, DataOutputStream stream, LevelData level) throws IOException {
    for (String mesh : entry.meshes) {
      if (shouldSkip(mesh, level))
        continue;
      byte[] nameBytes = mesh.getBytes(StandardCharsets.US_ASCII);
      stream.writeShort(nameBytes.length);
      stream.write(nameBytes);

      stream.writeFloat(entry.pos.x);
      stream.writeFloat(entry.pos.y);
      stream.writeFloat(entry.pos.z);

      Matrix4f matrix = entry.getMatrix();
      stream.writeFloat(matrix.m11);
      stream.writeFloat(matrix.m21);
      stream.writeFloat(matrix.m31);
      stream.writeFloat(matrix.m12);
      stream.writeFloat(matrix.m22);
      stream.writeFloat(matrix.m32);
      stream.writeFloat(matrix.m13);
      stream.writeFloat(matrix.m23);
      stream.writeFloat(matrix.m33);

      stream.writeFloat(entry.scale.x);
      stream.writeFloat(entry.scale.y);
      stream.writeFloat(entry.scale.z);


      if (mesh.equalsIgnoreCase(entry.mesh)) {
        stream.writeByte(EntryType.HOUSE_DOOR.getId()); // node type 0 = none
      } else {
        stream.writeByte(entry.type.getId());
      }
      stream.writeShort(entry.address); // no static id
      stream.writeByte(0);
    }
  }

  private void writeEntityEntry(EntityEntry entry, DataOutputStream stream, LevelData level) throws IOException {
    if (shouldSkip(entry.mesh, level)) {
      return;
    }
    String name = entry instanceof DoorEntry doorEntry ? entry.mesh + doorEntry.suffix : entry.mesh;
    byte[] nameBytes = name.getBytes(StandardCharsets.US_ASCII);
    stream.writeShort(nameBytes.length);
    stream.write(nameBytes);

    stream.writeFloat(entry.pos.x);
    stream.writeFloat(entry.pos.y);
    stream.writeFloat(entry.pos.z);

    Matrix4f matrix = entry.getMatrix();
    stream.writeFloat(matrix.m11);
    stream.writeFloat(matrix.m21);
    stream.writeFloat(matrix.m31);
    stream.writeFloat(matrix.m12);
    stream.writeFloat(matrix.m22);
    stream.writeFloat(matrix.m32);
    stream.writeFloat(matrix.m13);
    stream.writeFloat(matrix.m23);
    stream.writeFloat(matrix.m33);

    stream.writeFloat(entry.scale.x);
    stream.writeFloat(entry.scale.y);
    stream.writeFloat(entry.scale.z);
    stream.writeByte(entry.type.getId());
    if (entry instanceof TownEntry townEntry) {
      stream.writeShort(townEntry.townId);
      stream.writeByte(townEntry.level);
    } else {
      stream.writeShort(entry.entityId);
      stream.writeByte(0);
    }
  }

  private void processCgfFiles(PakFile pakFile, Map<String, List<MeshData>> availableMeshes, AtomicInteger totalMeshes) {
    pakFile.getFileNames().parallelStream().forEach(name -> {
      if (!requiredCgfs.remove(name)) // not a required cgf or might also be a duplicate which has already been processed
        return;
      try {
        CgfLoader loader = new CgfLoader();
        ByteBuffer file = pakFile.unpak(name);
        loader.load(file);
        List<MeshData> meshes = new ArrayList<>();
        loader.traverseNodes(meshes);
        if (meshes.size() > 0) {
          if (availableMeshes.putIfAbsent(name, meshes) != null) // should never happen
            throw new IOException("Duplicate mesh name: " + name);
          if (requiredDoorCgas.contains(name)) {
            CgfLoader loaderState2 = loader.cloneAtTime(999999, file);
            List<MeshData> meshes2 = new ArrayList<>();
            loaderState2.traverseNodes(meshes2);
            String doorNameSecondaryState = name + "_state2";
            if (meshes2.size() > 0 && availableMeshes.putIfAbsent(doorNameSecondaryState, meshes2) == null) {
              if (BrushLstLoader.EVENT_MESHES.contains(name))
                meshes2.forEach(mesh -> mesh.collisionIntention |= CollisionIntention.EVENT.getId());
              processedCgfs.add(doorNameSecondaryState);
              totalMeshes.incrementAndGet();
            } else {
              emptyCgfs.add(doorNameSecondaryState);
              processedCgfs.add(doorNameSecondaryState);
            }
          }
          if (BrushLstLoader.EVENT_MESHES.contains(name))
            meshes.forEach(mesh -> mesh.collisionIntention |= CollisionIntention.EVENT.getId());
        } else {
          emptyCgfs.add(name);
        }
        processedCgfs.add(name);
        log.info("[" + processedCgfs.size() + "/" + totalMeshes + "] meshes processed\r");
      } catch (Exception e) {
        throw new RuntimeException("Error processing " + name, e);
      }
    });
  }

  private void writeMeshes(String path, List<MeshData> data, DataOutputStream stream) {
    try {
      byte[] nameBytes = path.getBytes(StandardCharsets.US_ASCII);
      if (nameBytes.length > 0xFFFF)
        throw new IOException("Data doesn't fit in short (nameBytes.length = " + nameBytes.length + ")");
      stream.writeShort(nameBytes.length);
      stream.write(nameBytes);
      if (data.size() > 0xFF)
        throw new IOException("Data doesn't fit in byte (data.size() = " + data.size() + ")");
      stream.writeByte(data.size());
      for (MeshData mesh : data) {
        if (mesh.vertices.size() > 0xFFFF)
          throw new IOException("Data doesn't fit in short (mesh.vertices.size() = " + mesh.vertices.size() + ")");
        stream.writeShort(mesh.vertices.size());
        for (Vector3 vec : mesh.vertices) {
          stream.writeFloat(vec.x);
          stream.writeFloat(vec.y);
          stream.writeFloat(vec.z);
        }
        if (mesh.faces.size() > 0xFFFF)
          throw new IOException("Data doesn't fit in short (mesh.faces.size() = " + mesh.faces.size() + ")");
        stream.writeShort(mesh.faces.size());
        int maxIndex = mesh.getMaxFaceVertexIndex();
        if (maxIndex > 0xFFFF)
          throw new IOException("MeshFace index " + maxIndex + " doesn't fit in short");
        if (maxIndex > 0xFF) {
          stream.writeByte(2);
          for (MeshFace face : mesh.faces) {
            stream.writeShort(face.v0);
            stream.writeShort(face.v1);
            stream.writeShort(face.v2);
          }
        } else {
          stream.writeByte(1);
          for (MeshFace face : mesh.faces) {
            stream.writeByte(face.v0);
            stream.writeByte(face.v1);
            stream.writeByte(face.v2);
          }
        }
        stream.writeByte(mesh.materialId);
        stream.writeByte(mesh.collisionIntention);
      }
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

  private void createNavFiles(Path outputFolder, List<LevelData> levels, Map<String, List<MeshData>> availableMeshes) {
    log.info("Generating nav files\r");
    Set<String> skipped = ConcurrentHashMap.newKeySet();
    AtomicInteger i = new AtomicInteger();
    AtomicInteger skippedExisting = new AtomicInteger();
    // Limit concurrent NAV builds to avoid heap exhaustion from simultaneous large geometry arrays
    int maxParallel = Math.max(1, Runtime.getRuntime().availableProcessors() / 2);
    Semaphore semaphore = new Semaphore(maxParallel);
    levels.parallelStream().forEach(level -> {
      Path navFile = outputFolder.resolve(level.levelId + ".nav");
      if (Files.exists(navFile)) {
        skippedExisting.incrementAndGet();
        log.info(level.levelName + ": " + level.levelId + ".nav already exists, skipping.\r");
        return;
      }
      try {
        semaphore.acquire();
      } catch (InterruptedException ie) {
        Thread.currentThread().interrupt();
        return;
      }
      try {
        if (createNavFile(outputFolder, level, availableMeshes)) {
          log.info("[" + i.incrementAndGet() + "/" + (levels.size() - skipped.size()) + "] " + level.levelName + ": " + level.levelId + ".nav Done\r");
        } else {
          skipped.add(level.levelId);
        }
      } catch (Exception e) {
        log.log(Level.SEVERE, "Error generating " + level.levelId + ".nav", e);
      } finally {
        semaphore.release();
      }
    });
    log.info("Created " + i.get() + " nav file" + (i.get() == 1 ? "" : "s") + (skippedExisting.get() == 0 ? "" : " (" + skippedExisting.get() + " already existed)") + (skipped.isEmpty() ? "" : " (skipped " + skipped.size() + " levels: " + skipped.stream().sorted().collect(Collectors.joining(", ")) + ")"));
  }

  private boolean createNavFile(Path outputFolder, LevelData level, Map<String, List<MeshData>> availableMeshes) throws IOException {
    Path navFile = outputFolder.resolve(level.levelId + ".nav");
    if (Files.exists(navFile)) {
      log.fine(level + ": Skipping existing " + level.levelId + ".nav");
      return true;
    }

    // Use primitive-backed lists to avoid boxing overhead of ArrayList<Float>/ArrayList<Integer>
    FloatList verticesList = new FloatList(1 << 18);
    IntList indicesList = new IntList(1 << 20);

    extractTerrainGeometry(level, verticesList, indicesList);
    extractStaticGeometry(level, availableMeshes, verticesList, indicesList);

    if (verticesList.size() == 0 || indicesList.size() == 0) {
      return false;
    }

    float[] vertices = verticesList.toArray();
    int[] indices   = indicesList.toArray();
    // Release accumulators before Recast allocation
    verticesList = null;
    indicesList  = null;

    NavMeshData navData = buildTiledNavMesh(vertices, indices);
    vertices = null;
    indices  = null;
    if (navData == null || navData.npolys == 0) {
      return false;
    }

    writeNavMeshFile(navFile, navData);
    return true;
  }

  private void extractTerrainGeometry(LevelData level, FloatList vertices, IntList indices) {
    if (level.useTerrain && level.terrain != null && level.terrain.heightmap != null) {
      com.aionemu.geobuilder.Terrain terrain = level.terrain;
      int hX = terrain.heightmapXSize;
      int hY = terrain.heightmapYSize;
      int unitSize = terrain.heightmapUnitSize;
      short[] hbArray = terrain.heightmap.array();

      int[] vertIndices = new int[hX * hY];
      Arrays.fill(vertIndices, -1);

      for (int gx = 0; gx < hX; gx++) {
        for (int gy = 0; gy < hY; gy++) {
          int idx = gy + gx * hY;
          short hVal = hbArray[idx];
          if (hVal != -1) {
            float x = gx * unitSize;
            float y = gy * unitSize;
            float z = Short.toUnsignedInt(hVal) * 2048f / 65536.0f;

            int vIdx = vertices.size() / 3;
            vertIndices[idx] = vIdx;

            vertices.add(x);
            vertices.add(z); // Recast Y is vertical height
            vertices.add(y); // Recast Z is Aion Y
          }
        }
      }

      for (int gx = 0; gx < hX - 1; gx++) {
        for (int gy = 0; gy < hY - 1; gy++) {
          int idx00 = gy + gx * hY;
          int idx01 = (gy + 1) + gx * hY;
          int idx10 = gy + (gx + 1) * hY;
          int idx11 = (gy + 1) + (gx + 1) * hY;

          int v00 = vertIndices[idx00];
          int v01 = vertIndices[idx01];
          int v10 = vertIndices[idx10];
          int v11 = vertIndices[idx11];

          if (v00 != -1 && v01 != -1 && v10 != -1) {
            indices.add(v00);
            indices.add(v01);
            indices.add(v10);
          }
          if (v11 != -1 && v01 != -1 && v10 != -1) {
            indices.add(v11);
            indices.add(v10);
            indices.add(v01);
          }
        }
      }
    }
  }

  private void extractStaticGeometry(LevelData level, Map<String, List<MeshData>> availableMeshes, FloatList vertices, IntList indices) {
    if (level.brushMeshData != null) {
      for (BrushEntry entry : level.brushMeshData.brushEntries) {
        String meshFileName = level.brushMeshData.meshFileNames.get(entry.meshIndex);
        if (shouldSkip(meshFileName, level))
          continue;
        List<MeshData> meshes = availableMeshes.get(meshFileName);
        if (meshes == null) continue;

        float[] matrix = entry.matrix;

        for (MeshData mesh : meshes) {
          if ((mesh.collisionIntention & (CollisionIntention.PHYSICAL.getId() | CollisionIntention.WALK.getId() | CollisionIntention.DOOR.getId() | CollisionIntention.PHYSICAL_SEE_THROUGH.getId())) == 0) {
            continue;
          }
          int vStart = vertices.size() / 3;
          for (Vector3 v : mesh.vertices) {
            float wx = matrix[0] * v.x + matrix[1] * v.y + matrix[2] * v.z + matrix[3];
            float wy = matrix[4] * v.x + matrix[5] * v.y + matrix[6] * v.z + matrix[7];
            float wz = matrix[8] * v.x + matrix[9] * v.y + matrix[10] * v.z + matrix[11];

            vertices.add(wx);
            vertices.add(wz);
            vertices.add(wy);
          }
          for (MeshFace face : mesh.faces) {
            indices.add(vStart + face.v0);
            indices.add(vStart + face.v2);
            indices.add(vStart + face.v1);
          }
        }
      }
    }

    if (level.objectMeshData != null) {
      for (ObjectEntry entry : level.objectMeshData.objectEntries) {
        String meshFileName = level.objectMeshData.meshFiles.get(entry.meshIndex);
        if (shouldSkip(meshFileName, level))
          continue;
        List<MeshData> meshes = availableMeshes.get(meshFileName);
        if (meshes == null) continue;

        Vector3 translation = new Vector3(entry.x, entry.y, entry.z);
        Vector3 scale = new Vector3(entry.scale, entry.scale, entry.scale);
        Matrix4f matrix = Matrix4f.createRotationMatrix(entry.rotX, entry.rotY, entry.rotZ);

        for (MeshData mesh : meshes) {
          if ((mesh.collisionIntention & (CollisionIntention.PHYSICAL.getId() | CollisionIntention.WALK.getId() | CollisionIntention.DOOR.getId() | CollisionIntention.PHYSICAL_SEE_THROUGH.getId())) == 0) {
            continue;
          }
          int vStart = vertices.size() / 3;
          for (Vector3 v : mesh.vertices) {
            float vx = v.x * scale.x;
            float vy = v.y * scale.y;
            float vz = v.z * scale.z;

            float wx = matrix.m11 * vx + matrix.m21 * vy + matrix.m31 * vz + translation.x;
            float wy = matrix.m12 * vx + matrix.m22 * vy + matrix.m32 * vz + translation.y;
            float wz = matrix.m13 * vx + matrix.m23 * vy + matrix.m33 * vz + translation.z;

            vertices.add(wx);
            vertices.add(wz);
            vertices.add(wy);
          }
          for (MeshFace face : mesh.faces) {
            indices.add(vStart + face.v0);
            indices.add(vStart + face.v2);
            indices.add(vStart + face.v1);
          }
        }
      }
    }

    for (EntityEntry entry : level.entityEntries) {
      if (entry instanceof HouseEntry houseEntry) {
        for (String mesh : houseEntry.meshes) {
          if (shouldSkip(mesh, level))
            continue;
          List<MeshData> meshes = availableMeshes.get(mesh);
          if (meshes == null) continue;

          Vector3 translation = houseEntry.pos;
          Vector3 scale = houseEntry.scale;
          Matrix4f matrix = houseEntry.getMatrix();

          for (MeshData meshData : meshes) {
            if ((meshData.collisionIntention & (CollisionIntention.PHYSICAL.getId() | CollisionIntention.WALK.getId() | CollisionIntention.DOOR.getId() | CollisionIntention.PHYSICAL_SEE_THROUGH.getId())) == 0) {
              continue;
            }
            int vStart = vertices.size() / 3;
            for (Vector3 v : meshData.vertices) {
              float vx = v.x * scale.x;
              float vy = v.y * scale.y;
              float vz = v.z * scale.z;

              float wx = matrix.m11 * vx + matrix.m21 * vy + matrix.m31 * vz + translation.x;
              float wy = matrix.m12 * vx + matrix.m22 * vy + matrix.m32 * vz + translation.y;
              float wz = matrix.m13 * vx + matrix.m23 * vy + matrix.m33 * vz + translation.z;

              vertices.add(wx);
              vertices.add(wz);
              vertices.add(wy);
            }
            for (MeshFace face : meshData.faces) {
              indices.add(vStart + face.v0);
              indices.add(vStart + face.v2);
              indices.add(vStart + face.v1);
            }
          }
        }
      } else {
        String meshKey = entry instanceof DoorEntry doorEntry ? entry.mesh + doorEntry.suffix : entry.mesh;
        if (shouldSkip(meshKey, level))
          continue;
        List<MeshData> meshes = availableMeshes.get(meshKey);
        if (meshes == null) continue;

        Vector3 translation = entry.pos;
        Vector3 scale = entry.scale;
        Matrix4f matrix = entry.getMatrix();

        for (MeshData meshData : meshes) {
          if ((meshData.collisionIntention & (CollisionIntention.PHYSICAL.getId() | CollisionIntention.WALK.getId() | CollisionIntention.DOOR.getId() | CollisionIntention.PHYSICAL_SEE_THROUGH.getId())) == 0) {
            continue;
          }
          int vStart = vertices.size() / 3;
          for (Vector3 v : meshData.vertices) {
            float vx = v.x * scale.x;
            float vy = v.y * scale.y;
            float vz = v.z * scale.z;

            float wx = matrix.m11 * vx + matrix.m21 * vy + matrix.m31 * vz + translation.x;
            float wy = matrix.m12 * vx + matrix.m22 * vy + matrix.m32 * vz + translation.y;
            float wz = matrix.m13 * vx + matrix.m23 * vy + matrix.m33 * vz + translation.z;

            vertices.add(wx);
            vertices.add(wz);
            vertices.add(wy);
          }
          for (MeshFace face : meshData.faces) {
            indices.add(vStart + face.v0);
            indices.add(vStart + face.v2);
            indices.add(vStart + face.v1);
          }
        }
      }
    }
  }

  private void writeIntLE(java.io.OutputStream stream, int value) throws IOException {
    stream.write(value & 0xFF);
    stream.write((value >>> 8) & 0xFF);
    stream.write((value >>> 16) & 0xFF);
    stream.write((value >>> 24) & 0xFF);
  }

  private void writeFloatLE(java.io.OutputStream stream, float value) throws IOException {
    writeIntLE(stream, Float.floatToRawIntBits(value));
  }

  private void writeNavMeshFile(Path navFile, NavMeshData navData) throws IOException {
    try (BufferedOutputStream stream = new BufferedOutputStream(Files.newOutputStream(navFile))) {
      int nverts = navData.verts.length / 3;
      writeIntLE(stream, nverts * 3);
      // navData.verts is in Recast space: [Recast-X, Recast-Y(height), Recast-Z]
      // Output order expected by server: Aion-X, Aion-Y, Aion-Z(height)
      for (int i = 0; i < nverts; i++) {
        writeFloatLE(stream, navData.verts[i * 3]);     // Recast X = Aion X
        writeFloatLE(stream, navData.verts[i * 3 + 2]); // Recast Z = Aion Y
        writeFloatLE(stream, navData.verts[i * 3 + 1]); // Recast Y = Aion Z (height)
      }
      writeIntLE(stream, navData.npolys);
      for (int i = 0; i < navData.npolys; i++) {
        // Swap vertices 1 and 2 to restore CCW winding in Aion space (nz > 0)
        // Swap adjacencies 0 and 2 so neighbor indices correspond to the new edge indices
        writeIntLE(stream, navData.polys[i * 6]);       // v0
        writeIntLE(stream, navData.polys[i * 6 + 2]);   // v2 -> v1
        writeIntLE(stream, navData.polys[i * 6 + 1]);   // v1 -> v2
        writeIntLE(stream, navData.polys[i * 6 + 5]);   // adj2 -> adj0
        writeIntLE(stream, navData.polys[i * 6 + 4]);   // adj1 -> adj1
        writeIntLE(stream, navData.polys[i * 6 + 3]);   // adj0 -> adj2
      }
    }
  }

  // -----------------------------------------------------------------------
  // Tiled NavMesh construction
  // -----------------------------------------------------------------------

  private NavMeshData buildTiledNavMesh(float[] srcVerts, int[] srcTris) {
    if (srcTris.length == 0) return null;

    float cellSize   = 0.4f;
    float cellHeight = 0.2f;
    float agentHeight = 2.0f;
    float agentRadius = 0.5f;
    float agentMaxClimb = 0.9f;
    float agentMaxSlope = 50.0f;
    int tileSize = 256;
    int borderSize = RecastConfig.calcBorder(agentRadius, cellSize);

    RecastConfig config = new RecastConfig(
        true, tileSize, tileSize, borderSize,
        RecastConstants.PartitionType.MONOTONE,
        cellSize, cellHeight,
        agentMaxSlope,
        true, true, true,
        agentHeight, agentRadius, agentMaxClimb,
        16.0f, // minRegionArea
        20.0f, // mergeRegionArea
        12.0f, // maxEdgeLen
        1.3f,  // maxSimplificationError
        3,     // maxVertsPerPoly — triangles only
        false, 6.0f, 1.0f,
        new AreaModification(1, 1));

    // Compute world bounds from raw vertex array
    float[] bmin = {Float.MAX_VALUE,  Float.MAX_VALUE,  Float.MAX_VALUE};
    float[] bmax = {-Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE};
    int nverts = srcVerts.length / 3;
    for (int i = 0; i < nverts; i++) {
      for (int j = 0; j < 3; j++) {
        float v = srcVerts[i * 3 + j];
        if (v < bmin[j]) bmin[j] = v;
        if (v > bmax[j]) bmax[j] = v;
      }
    }

    float tcs     = tileSize * cellSize;
    float clipPad = (borderSize + 2) * cellSize;

    int tilesX = Math.max(1, (int) Math.ceil((bmax[0] - bmin[0]) / tcs));
    int tilesZ = Math.max(1, (int) Math.ceil((bmax[2] - bmin[2]) / tcs));
    int totalTiles = tilesX * tilesZ;

    // Spatial binning: assign each triangle to overlapping tile bins in a single O(N) pass
    IntList[] tileTriBins = new IntList[totalTiles];
    int triCount = srcTris.length / 3;
    for (int t = 0; t < triCount; t++) {
      int vi0 = srcTris[t * 3], vi1 = srcTris[t * 3 + 1], vi2 = srcTris[t * 3 + 2];
      float x0 = srcVerts[vi0 * 3],     x1 = srcVerts[vi1 * 3],     x2 = srcVerts[vi2 * 3];
      float z0 = srcVerts[vi0 * 3 + 2], z1 = srcVerts[vi1 * 3 + 2], z2 = srcVerts[vi2 * 3 + 2];

      float triXMin = Math.min(x0, Math.min(x1, x2)) - clipPad;
      float triXMax = Math.max(x0, Math.max(x1, x2)) + clipPad;
      float triZMin = Math.min(z0, Math.min(z1, z2)) - clipPad;
      float triZMax = Math.max(z0, Math.max(z1, z2)) + clipPad;

      int minTX = Math.max(0, Math.min(tilesX - 1, (int) ((triXMin - bmin[0]) / tcs)));
      int maxTX = Math.max(0, Math.min(tilesX - 1, (int) ((triXMax - bmin[0]) / tcs)));
      int minTZ = Math.max(0, Math.min(tilesZ - 1, (int) ((triZMin - bmin[2]) / tcs)));
      int maxTZ = Math.max(0, Math.min(tilesZ - 1, (int) ((triZMax - bmin[2]) / tcs)));

      for (int tz = minTZ; tz <= maxTZ; tz++) {
        for (int tx = minTX; tx <= maxTX; tx++) {
          int idx = tz * tilesX + tx;
          if (tileTriBins[idx] == null) tileTriBins[idx] = new IntList(64);
          tileTriBins[idx].add(t);
        }
      }
    }

    List<TileData> tiles = Collections.synchronizedList(new ArrayList<>(totalTiles));

    java.util.stream.IntStream.range(0, totalTiles).parallel().forEach(tileIdx -> {
      IntList bin = tileTriBins[tileIdx];
      if (bin == null || bin.size() == 0) return;

      int tx = tileIdx % tilesX;
      int tz = tileIdx / tilesX;

      float[] tileBmin = {bmin[0] + tx * tcs, bmin[1], bmin[2] + tz * tcs};
      float[] tileBmax = {Math.min(bmin[0] + (tx + 1) * tcs, bmax[0]), bmax[1],
                          Math.min(bmin[2] + (tz + 1) * tcs, bmax[2])};

      ClippedGeom clipped = clipBinToTile(srcVerts, srcTris, bin, tileBmin, tileBmax, clipPad);
      if (clipped == null) return;

      try {
        RecastBuilder builder = new RecastBuilder();
        SimpleInputGeomProvider tileGeom = new SimpleInputGeomProvider(clipped.verts, clipped.tris);
        RecastBuilderConfig bcfg = new RecastBuilderConfig(config, bmin, bmax, tx, tz);
        RecastBuilderResult result = builder.build(tileGeom, bcfg);
        if (result != null && result.getMesh() != null && result.getMesh().npolys > 0) {
          tiles.add(new TileData(result.getMesh(), tileBmin, tileBmax, tx == tilesX - 1, tz == tilesZ - 1));
        }
      } catch (Exception e) {
        log.log(Level.WARNING, "NAV tile [" + tx + "," + tz + "] failed, skipping: " + e.getMessage());
      }
    });

    if (tiles.isEmpty()) return null;
    // Deterministic ordering before merge
    tiles.sort(Comparator.comparingDouble((TileData td) -> td.logicalBmin[2]).thenComparingDouble(td -> td.logicalBmin[0]));
    return mergeNavMeshTiles(tiles);
  }

  /**
   * Returns a minimal vertex+triangle array containing only triangles from candidate bin
   * whose axis-aligned bounding box overlaps [tileBmin − pad, tileBmax + pad].
   */
  private static ClippedGeom clipBinToTile(float[] srcVerts, int[] srcTris, IntList bin,
                                          float[] tileBmin, float[] tileBmax, float pad) {
    float xmin = tileBmin[0] - pad, xmax = tileBmax[0] + pad;
    float zmin = tileBmin[2] - pad, zmax = tileBmax[2] + pad;

    int candidateCount = bin.size();
    int[] candidates = bin.toArray();
    int[] validTris = new int[candidateCount];
    int validCount  = 0;

    for (int i = 0; i < candidateCount; i++) {
      int t = candidates[i];
      int vi0 = srcTris[t * 3], vi1 = srcTris[t * 3 + 1], vi2 = srcTris[t * 3 + 2];
      float x0 = srcVerts[vi0 * 3],     x1 = srcVerts[vi1 * 3],     x2 = srcVerts[vi2 * 3];
      float z0 = srcVerts[vi0 * 3 + 2], z1 = srcVerts[vi1 * 3 + 2], z2 = srcVerts[vi2 * 3 + 2];
      if (Math.max(x0, Math.max(x1, x2)) >= xmin && Math.min(x0, Math.min(x1, x2)) <= xmax
       && Math.max(z0, Math.max(z1, z2)) >= zmin && Math.min(z0, Math.min(z1, z2)) <= zmax) {
        validTris[validCount++] = t;
      }
    }

    if (validCount == 0) return null;

    Map<Integer, Integer> vertRemap = new HashMap<>(validCount * 2);
    FloatList newVerts = new FloatList(validCount * 9);
    int[]     newTris  = new int[validCount * 3];
    int newVI = 0, newTI = 0;

    for (int i = 0; i < validCount; i++) {
      int t = validTris[i];
      for (int j = 0; j < 3; j++) {
        int origVI = srcTris[t * 3 + j];
        Integer mapped = vertRemap.get(origVI);
        if (mapped == null) {
          mapped = newVI++;
          vertRemap.put(origVI, mapped);
          newVerts.add(srcVerts[origVI * 3]);
          newVerts.add(srcVerts[origVI * 3 + 1]);
          newVerts.add(srcVerts[origVI * 3 + 2]);
        }
        newTris[newTI++] = mapped;
      }
    }

    return new ClippedGeom(newVerts.toArray(), newTris);
  }

  private NavMeshData mergeNavMeshTiles(List<TileData> tiles) {
    HashMap<Long, Integer> vertexMap  = new HashMap<>(tiles.size() * 512);
    FloatList globalVerts = new FloatList(tiles.size() * 512 * 3);

    // Phase 1: build per-tile vertex remapping + mark which polygons are within logical tile bounds
    int[][] tileVertRemap    = new int[tiles.size()][];
    boolean[][] tileValidPoly = new boolean[tiles.size()][];

    for (int t = 0; t < tiles.size(); t++) {
      TileData td   = tiles.get(t);
      PolyMesh mesh = td.mesh;

      int[] remap = new int[mesh.nverts];
      for (int i = 0; i < mesh.nverts; i++) {
        float wx = mesh.bmin[0] + mesh.verts[i * 3]     * mesh.cs;
        float wy = mesh.bmin[1] + mesh.verts[i * 3 + 1] * mesh.ch;
        float wz = mesh.bmin[2] + mesh.verts[i * 3 + 2] * mesh.cs;
        long key = quantizeVertex(wx, wy, wz);
        Integer existing = vertexMap.get(key);
        if (existing == null) {
          int idx = globalVerts.size() / 3;
          vertexMap.put(key, idx);
          globalVerts.add(wx); globalVerts.add(wy); globalVerts.add(wz);
          remap[i] = idx;
        } else {
          remap[i] = existing;
        }
      }
      tileVertRemap[t] = remap;

      // Only keep polygons whose centroid falls within this tile's logical (non-border) bounds.
      // Border polygons will be present in an adjacent tile's logical region — keeping them both
      // would create duplicate triangles in the merged mesh.
      boolean[] valid = new boolean[mesh.npolys];
      for (int p = 0; p < mesh.npolys; p++) {
        float cx = 0, cz = 0;
        for (int vi = 0; vi < 3; vi++) {
          int vIdx = mesh.polys[p * 6 + vi];
          cx += mesh.bmin[0] + mesh.verts[vIdx * 3]     * mesh.cs;
          cz += mesh.bmin[2] + mesh.verts[vIdx * 3 + 2] * mesh.cs;
        }
        cx /= 3f; cz /= 3f;
        float eps = 1e-4f;
        boolean inX = (cx >= td.logicalBmin[0] - eps) && (td.isMaxX ? cx <= td.logicalBmax[0] + eps : cx < td.logicalBmax[0] - eps);
        boolean inZ = (cz >= td.logicalBmin[2] - eps) && (td.isMaxZ ? cz <= td.logicalBmax[2] + eps : cz < td.logicalBmax[2] - eps);
        valid[p] = inX && inZ;
      }
      tileValidPoly[t] = valid;
    }

    // Phase 2: assign global polygon indices to valid polygons
    int[][] tilePolyGlobal = new int[tiles.size()][];
    int globalPolyCount    = 0;
    for (int t = 0; t < tiles.size(); t++) {
      int npolys = tiles.get(t).mesh.npolys;
      int[] gIdx = new int[npolys];
      Arrays.fill(gIdx, -1);
      for (int p = 0; p < npolys; p++) {
        if (tileValidPoly[t][p]) gIdx[p] = globalPolyCount++;
      }
      tilePolyGlobal[t] = gIdx;
    }

    if (globalPolyCount == 0) return null;

    // Phase 3: populate global polygon array [v0,v1,v2, adj0,adj1,adj2] per poly
    int[] globalPolys = new int[globalPolyCount * 6];
    for (int t = 0; t < tiles.size(); t++) {
      TileData td   = tiles.get(t);
      PolyMesh mesh = td.mesh;
      int[]    remap     = tileVertRemap[t];
      boolean[]valid     = tileValidPoly[t];
      int[]    gIdx      = tilePolyGlobal[t];

      for (int p = 0; p < mesh.npolys; p++) {
        if (!valid[p]) continue;
        int gp = gIdx[p];
        globalPolys[gp * 6]     = remap[mesh.polys[p * 6]];
        globalPolys[gp * 6 + 1] = remap[mesh.polys[p * 6 + 1]];
        globalPolys[gp * 6 + 2] = remap[mesh.polys[p * 6 + 2]];

        for (int e = 0; e < 3; e++) {
          int adj = mesh.polys[p * 6 + 3 + e];
          if (adj == 0xffff || adj < 0 || adj >= mesh.npolys) {
            globalPolys[gp * 6 + 3 + e] = -1;
          } else {
            globalPolys[gp * 6 + 3 + e] = tilePolyGlobal[t][adj]; // -1 if border poly was filtered
          }
        }
      }
    }

    // Phase 4: rebuild cross-tile edge adjacency (edges that border between tiles)
    buildEdgeAdjacency(globalPolys, globalPolyCount);

    return new NavMeshData(globalVerts.toArray(), globalPolys, globalPolyCount);
  }

  private static void buildEdgeAdjacency(int[] polys, int npolys) {
    // Map directed edge va->vb to the polygon index that owns it.
    HashMap<Long, Integer> edgeMap = new HashMap<>(npolys * 3);
    for (int p = 0; p < npolys; p++) {
      for (int e = 0; e < 3; e++) {
        int va = polys[p * 6 + e];
        int vb = polys[p * 6 + (e + 1) % 3];
        edgeMap.put(encodeEdge(va, vb), p);
      }
    }
    // Fill in missing adjacency by finding polygons that share the reverse edge.
    for (int p = 0; p < npolys; p++) {
      for (int e = 0; e < 3; e++) {
        if (polys[p * 6 + 3 + e] != -1) continue; // already linked
        int va = polys[p * 6 + e];
        int vb = polys[p * 6 + (e + 1) % 3];
        Integer neighbor = edgeMap.get(encodeEdge(vb, va));
        if (neighbor != null && neighbor != p) {
          polys[p * 6 + 3 + e] = neighbor;
        }
      }
    }
  }

  private static long encodeEdge(int va, int vb) {
    return ((long) va << 32) | (vb & 0xFFFFFFFFL);
  }

  private static long quantizeVertex(float x, float y, float z) {
    // Centimetre precision; 21-bit fields cover ±10 485.76 m per axis (sufficient for all Aion zones)
    int ix = Math.round(x * 100f);
    int iy = Math.round(y * 100f);
    int iz = Math.round(z * 100f);
    return ((long) (ix & 0x1FFFFF)) | ((long) (iy & 0x1FFFFF) << 21) | ((long) (iz & 0x1FFFFF) << 42);
  }

  // -----------------------------------------------------------------------
  // Inner helper types
  // -----------------------------------------------------------------------

  /** Primitive float accumulator — avoids boxing overhead of ArrayList<Float>. */
  private static final class FloatList {
    private float[] data;
    private int count;
    FloatList(int capacity) { data = new float[capacity]; }
    void add(float v) {
      if (count == data.length) data = Arrays.copyOf(data, Math.max(count * 2, 16));
      data[count++] = v;
    }
    int size() { return count; }
    float[] toArray() { return Arrays.copyOf(data, count); }
  }

  /** Primitive int accumulator — avoids boxing overhead of ArrayList<Integer>. */
  private static final class IntList {
    private int[] data;
    private int count;
    IntList(int capacity) { data = new int[capacity]; }
    void add(int v) {
      if (count == data.length) data = Arrays.copyOf(data, Math.max(count * 2, 16));
      data[count++] = v;
    }
    int size() { return count; }
    int[] toArray() { return Arrays.copyOf(data, count); }
  }

  /** Merged nav-mesh ready to write: world-space vertices + [v0,v1,v2,adj0,adj1,adj2] polygons. */
  private static final class NavMeshData {
    final float[] verts;  // Recast-space: [X, Y(height), Z] per vertex
    final int[]   polys;  // 6 ints per polygon: 3 vertex indices + 3 adjacency (-1 = boundary)
    final int     npolys;
    NavMeshData(float[] verts, int[] polys, int npolys) {
      this.verts = verts; this.polys = polys; this.npolys = npolys;
    }
  }

  /** Pre-clipped geometry for a single tile (compact vertex + triangle arrays). */
  private static final class ClippedGeom {
    final float[] verts;
    final int[]   tris;
    ClippedGeom(float[] verts, int[] tris) { this.verts = verts; this.tris = tris; }
  }

  /** A single processed tile: its PolyMesh plus the logical (non-border-expanded) bounds. */
  private static final class TileData {
    final PolyMesh mesh;
    final float[]  logicalBmin;
    final float[]  logicalBmax;
    final boolean  isMaxX;
    final boolean  isMaxZ;
    TileData(PolyMesh mesh, float[] bmin, float[] bmax, boolean isMaxX, boolean isMaxZ) {
      this.mesh = mesh;
      this.logicalBmin = Arrays.copyOf(bmin, bmin.length);
      this.logicalBmax = Arrays.copyOf(bmax, bmax.length);
      this.isMaxX = isMaxX;
      this.isMaxZ = isMaxZ;
    }
  }

  private boolean isIgnored(String meshFileName, LevelData level) {
    String lower = meshFileName.toLowerCase();
    if (lower.endsWith("_light.cgf") || lower.contains("teleport_statue_light") || lower.contains("teleport_statue_dark")) {
      return true;
    }
    // TODO remove this method after figuring out the correct collision logic
    return switch (meshFileName) {
      // Door ID 145 is invisible and clickable but can be walked through (actual obstacle is elemental_alchemyroom_collisionwall.cgf)
      case "objects/npc/level_object/idyun_bridge/idyun_bridge_01a.cga" -> Set.of("300280000", "300620000").contains(level.levelId);
      // mesh collides in 300040000 x:676.4767 y:1196.3914 z:143.58203 but doesn't in instances 300280000 or 300620000 (near Vasharti)
      case "levels/common/light/structures/props/exterior/pr_l_caldron.cgf" -> Set.of("300280000", "300620000").contains(level.levelId);
      default -> false;
    };
  }

  @FunctionalInterface
  interface ThrowingConsumer<T> {
    void consume(T buffer) throws Exception;
  }
}
