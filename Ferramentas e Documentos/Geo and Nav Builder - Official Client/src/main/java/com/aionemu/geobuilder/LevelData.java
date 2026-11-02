package com.aionemu.geobuilder;

import com.aionemu.geobuilder.entries.EntityEntry;
import com.aionemu.geobuilder.meshData.BrushLstMeshData;
import com.aionemu.geobuilder.meshData.ObjectMeshData;

import java.nio.file.Path;
import java.util.Collections;
import java.util.List;
import java.util.stream.Stream;

public class LevelData {

  public final String levelId;
  public final String levelName;
  public final Path levelFolder;
  public final List<Path> levelPakFiles;
  public final Path clientLevelPakFile;
  public String missionPath;
  public boolean useTerrain;
  public volatile Terrain terrain;
  public volatile BrushLstMeshData brushMeshData;
  public volatile ObjectMeshData objectMeshData;
  public volatile List<EntityEntry> entityEntries = Collections.emptyList();

  public LevelData(String levelId, String levelName, Path clientLevelPakFile) {
    this(levelId, levelName, clientLevelPakFile != null ? clientLevelPakFile.getParent() : null,
        clientLevelPakFile != null ? List.of(clientLevelPakFile) : Collections.emptyList());
  }

  public LevelData(String levelId, String levelName, Path levelFolder, List<Path> levelPakFiles) {
    this.levelId = levelId;
    this.levelName = levelName;
    this.levelFolder = levelFolder;
    this.levelPakFiles = levelPakFiles != null ? List.copyOf(levelPakFiles) : Collections.emptyList();
    this.clientLevelPakFile = !this.levelPakFiles.isEmpty() ? this.levelPakFiles.get(0) : (levelFolder != null ? levelFolder.resolve("Level.pak") : null);
  }

  public boolean isTestLevel() {
    return levelId.charAt(0) == '9' && levelName.toLowerCase().contains("test") || levelName.equalsIgnoreCase("IDTest_Dungeon");
  }

  public Stream<String> streamAllMeshFileNames() {
    Stream<Stream<String>> streams = Stream.of(
      brushMeshData == null || brushMeshData.brushEntries == null || brushMeshData.meshFileNames == null ? Stream.empty() :
          brushMeshData.brushEntries.stream().mapToInt(o -> o.meshIndex).filter(idx -> idx >= 0 && idx < brushMeshData.meshFileNames.size()).distinct().mapToObj(brushMeshData.meshFileNames::get),
      objectMeshData == null || objectMeshData.objectEntries == null || objectMeshData.meshFiles == null ? Stream.empty() :
          objectMeshData.objectEntries.stream().mapToInt(o -> o.meshIndex).filter(idx -> idx >= 0 && idx < objectMeshData.meshFiles.size()).distinct().mapToObj(objectMeshData.meshFiles::get),
      entityEntries == null ? Stream.empty() : entityEntries.stream().flatMap(EntityEntry::getAllMeshNames)
    );
    return streams.flatMap(s->s);
  }

  @Override
  public String toString() {
    return '[' + levelId + "] " + levelName;
  }
}
