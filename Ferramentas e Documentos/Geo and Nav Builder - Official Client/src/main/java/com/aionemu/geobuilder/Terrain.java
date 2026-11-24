package com.aionemu.geobuilder;

import com.aionemu.geobuilder.loaders.CgfLoader;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.color.ColorSpace;
import java.awt.image.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ShortBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;

public class Terrain {

  private static final int TERRAIN_CUTOUT_MARKER = -1;

  public final int heightmapXSize, heightmapYSize, heightmapUnitSize;
  public ShortBuffer heightmap;
  public byte[] materialIds;
  public ByteBuffer materials;

  public Terrain(int heightmapXSize, int heightmapYSize, int heightmapUnitSize) {
    this.heightmapXSize = heightmapXSize;
    this.heightmapYSize = heightmapYSize;
    this.heightmapUnitSize = heightmapUnitSize;
  }

  public void load(ByteBuffer landMapH32, boolean allTerrainMaterials) throws IOException {
    boolean hasMaterials = false;
    heightmap = ShortBuffer.allocate(heightmapXSize * heightmapYSize);
    materials = ByteBuffer.allocate(heightmap.capacity());
    int outOfRangeCount = 0;
    for (int i = 0; i < heightmap.capacity(); i++) {
      short z = landMapH32.getShort();
      if (z == TERRAIN_CUTOUT_MARKER) {
        int x = i / heightmapYSize * heightmapUnitSize;
        int y = i % heightmapYSize * heightmapUnitSize;
        throw new IOException("Encountered reserved value " + z + " at x: " + x + " y: " + y);
      }
      int materialIndex = Byte.toUnsignedInt(landMapH32.get());
      boolean isTerrainCutout = materialIndex == 0x3F;
      byte materialId;
      if (isTerrainCutout) {
        materialId = 0;
      } else if (materialIds == null || materialIndex >= materialIds.length) {
        // Newer 7.x clients may reference material indices that exceed the surface types
        // declared in leveldata.xml (e.g. map has 1 surface type but terrain uses index 5).
        // Treat as "no special material" — safe fallback that preserves terrain geometry.
        outOfRangeCount++;
        materialId = 0;
      } else {
        materialId = materialIds[materialIndex];
      }
      if (!allTerrainMaterials && !CgfLoader.isUseSkillMaterial(Byte.toUnsignedInt(materialId)))
        materialId = 0;
      if (materialId != 0 && !hasMaterials)
        hasMaterials = true;
      heightmap.put(isTerrainCutout ? (short) TERRAIN_CUTOUT_MARKER : z);
      materials.put(materialId);
    }
    if (outOfRangeCount > 0) {
      Logger.getLogger("GeoBuilder").fine("Terrain: " + outOfRangeCount + " out-of-range material index(es) were reset to 0 (materialIds.length=" + (materialIds != null ? materialIds.length : 0) + ")");
    }
    if (landMapH32.remaining() > 0) {
      throw new IOException("Terrain data was not fully read.");
    }
    heightmap.flip();
    if (!hasMaterials) {
      materials = null;
    } else {
      materials.flip();
    }
  }

  public Heightmap createHeightmap() {
    return new Heightmap(heightmap.array(), heightmapXSize, heightmapYSize, "");
  }

  public Heightmap createMaterialmap() {
    return new Heightmap(materials.array(), heightmapXSize, heightmapYSize, "_materials");
  }

  public static class Heightmap {
    private final BufferedImage image;
    private final String fileNameSuffix;
    public final List<String> fileNames = new ArrayList<>();

    private Heightmap(byte[] data, int xSize, int ySize, String fileNameSuffix) {
      // we need these cumbersome initializers if we want to avoid array copies
      ColorModel colorModel = new ComponentColorModel(ColorSpace.getInstance(ColorSpace.CS_GRAY), new int[] { 8 }, false, true, Transparency.OPAQUE, DataBuffer.TYPE_BYTE);
      WritableRaster raster = (WritableRaster) Raster.createRaster(colorModel.createCompatibleSampleModel(xSize, ySize), new DataBufferByte(data, data.length), null);
      this.image = new BufferedImage(colorModel, raster, colorModel.isAlphaPremultiplied(), null);
      this.fileNameSuffix = fileNameSuffix;
    }

    private Heightmap(short[] data, int xSize, int ySize, String fileNameSuffix) {
      // we need these cumbersome initializers if we want to avoid array copies
      ColorModel colorModel = new ComponentColorModel(ColorSpace.getInstance(ColorSpace.CS_GRAY), new int[] { 16 }, false, true, Transparency.OPAQUE, DataBuffer.TYPE_USHORT);
      WritableRaster raster = (WritableRaster) Raster.createRaster(colorModel.createCompatibleSampleModel(xSize, ySize), new DataBufferUShort(data, data.length), null);
      this.image = new BufferedImage(colorModel, raster, colorModel.isAlphaPremultiplied(), null);
      this.fileNameSuffix = fileNameSuffix;
    }

    public void write(Path outputFolder, boolean disableOxipng, Logger oxipngLogger) {
      List<String> fileNames = this.fileNames;
      String fileNameStart = fileNames.stream().sorted().collect(Collectors.joining(","));
      Path file = outputFolder.resolve(fileNameStart + fileNameSuffix + ".png");
      if (Files.exists(file)) {
        return;
      }
      try {
        Path oxipng = disableOxipng ? null : findOxipngPath();
        if (oxipng != null)
          writeOptimized(image, file, oxipng.toString(), oxipngLogger);
        else
          ImageIO.write(image, "png", file.toFile());
      } catch (IOException e) {
        throw new RuntimeException(e);
      }
    }

    private static Path findOxipngPath() {
      boolean isWindows = System.getProperty("os.name").toLowerCase().startsWith("windows");
      String binaryName = isWindows ? "oxipng.exe" : "oxipng";

      Path p1 = Path.of("./oxipng", binaryName);
      if (Files.isRegularFile(p1)) return p1.toAbsolutePath();

      try {
        Path jarLocation = Path.of(Terrain.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path jarDir = Files.isDirectory(jarLocation) ? jarLocation : jarLocation.getParent();
        if (jarDir != null) {
          Path p2 = jarDir.resolve("oxipng").resolve(binaryName);
          if (Files.isRegularFile(p2)) return p2.toAbsolutePath();
          if (jarDir.getParent() != null) {
            Path p3 = jarDir.getParent().resolve("oxipng").resolve(binaryName);
            if (Files.isRegularFile(p3)) return p3.toAbsolutePath();
          }
        }
      } catch (Exception ignored) {}

      Path p4 = Path.of("Ferramentas [Emulador e Client]/GeoBuilder/oxipng", binaryName);
      if (Files.isRegularFile(p4)) return p4.toAbsolutePath();

      Path p5 = Path.of("F:/Aion Live Clássico - América do Sul/ZONA DE CUSTOM/LOST ACADEMY/Ferramentas [Emulador e Client]/GeoBuilder/oxipng", binaryName);
      if (Files.isRegularFile(p5)) return p5.toAbsolutePath();

      return null;
    }

    private void writeOptimized(BufferedImage image, Path file, String oxipng, Logger log) {
      try {
        Process process = new ProcessBuilder(oxipng, "-o", "max", "--fast", "--nb", "-s", "--out", file.toString(), "-").start();
        try (OutputStream outputStream = process.getOutputStream()) {
          ImageIO.write(image, "png", outputStream);
        } catch (IOException ignored) { // ignore broken pipe errors here since we log error messages from the process
        }
        try (BufferedReader reader = process.errorReader()) {
          reader.lines().takeWhile(l -> process.isAlive()).forEach(l -> log.info("[oxipng] " + l + '\r'));
          int exitCode = process.waitFor();
          String result = reader.lines().collect(Collectors.joining("\n"));
          if (exitCode != 0) {
            log.warning("oxipng process terminated with exit code " + exitCode + ", falling back to standard PNG");
            ImageIO.write(image, "png", file.toFile());
          } else if (!result.isEmpty()) {
            log.info("[oxipng] " + result + '\r');
          }
        }
      } catch (IOException | InterruptedException e) {
        log.warning("oxipng execution failed (" + e.getMessage() + "), falling back to standard PNG");
        try {
          ImageIO.write(image, "png", file.toFile());
        } catch (IOException ioEx) {
          log.log(Level.SEVERE, "Error saving PNG", ioEx);
        }
      }
    }
  }
}
