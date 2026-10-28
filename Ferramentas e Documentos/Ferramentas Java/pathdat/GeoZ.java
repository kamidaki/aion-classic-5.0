import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.MaterialData;
import com.aionemu.gameserver.geoEngine.GeoWorldLoader;
import com.aionemu.gameserver.geoEngine.models.GeoMap;

/** GeoZ <mapa> <entrada: x y z por linha> <saida>: superfície de colisão do geo logo abaixo de z+1 (até 1000 m abaixo) e logo acima. */
public class GeoZ {
    public static void main(String[] a) throws Exception {
        try {
            Constructor<MaterialData> c = MaterialData.class.getDeclaredConstructor(); c.setAccessible(true);
            DataManager.MATERIAL_DATA = c.newInstance();
            Constructor<com.aionemu.gameserver.dataholders.ZoneData> cz = com.aionemu.gameserver.dataholders.ZoneData.class.getDeclaredConstructor(); cz.setAccessible(true);
            DataManager.ZONE_DATA = cz.newInstance();
            GeoMap map = new GeoMap(Integer.parseInt(a[0]));
            GeoWorldLoader.load(List.of(map));
            StringBuilder out = new StringBuilder();
            for (String l : Files.readAllLines(Path.of(a[1]))) {
                String[] v = l.trim().split("\s+");
                if (v.length < 3) continue;
                float x = Float.parseFloat(v[0]), y = Float.parseFloat(v[1]), z = Float.parseFloat(v[2]);
                float abaixo = map.getZ(x, y, z + 1, z - 1000, 1);
                float acima = map.getZ(x, y, z + 30, z + 1, 1);
                out.append(l.trim()).append(' ').append(abaixo).append(' ').append(acima).append('\n');
            }
            Files.writeString(Path.of(a[2]), out);
        } catch (Throwable t) { t.printStackTrace(); } finally { System.exit(0); }
    }
}
