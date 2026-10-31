import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.MaterialData;
import com.aionemu.gameserver.dataholders.ZoneData;
import com.aionemu.gameserver.geoEngine.GeoWorldLoader;
import com.aionemu.gameserver.geoEngine.models.GeoMap;

/**
 * Como o GeoRotas, mas para uma lista de rotas de um mapa (sem precisar de spot): para cada route_id da lista, conta os passos sem chão
 * do geo a até 1,5 m (o NpcMoveController cola o NPC no chão, então esse passo não é alcançado e o NPC fica preso ou sobe pela parede).
 * Uso: GeoRotasLista <mapa> <npc_walker.xml> <ids.txt (um route_id por linha)>
 * Saída: uma linha por rota: route_id passos_sem_chao total pior_distancia
 */
public class GeoRotasLista {
    public static void main(String[] a) throws Exception {
        try { roda(a); } catch (Throwable t) { t.printStackTrace(); } finally { System.exit(0); }
    }

    static void roda(String[] a) throws Exception {
        Constructor<MaterialData> c = MaterialData.class.getDeclaredConstructor();
        c.setAccessible(true);
        DataManager.MATERIAL_DATA = c.newInstance();
        Constructor<ZoneData> cz = ZoneData.class.getDeclaredConstructor();
        cz.setAccessible(true);
        DataManager.ZONE_DATA = cz.newInstance();
        GeoMap map = new GeoMap(Integer.parseInt(a[0]));
        GeoWorldLoader.load(List.of(map));
        Set<String> ids = new HashSet<>();
        for (String l : Files.readAllLines(Path.of(a[2])))
            if (!l.isBlank()) ids.add(l.trim().toUpperCase());
        Matcher mr = Pattern.compile("<walker_template route_id=\"(\\w+)\"[^>]*>(.*?)</walker_template>", Pattern.DOTALL).matcher(Files.readString(Path.of(a[1])));
        Pattern ps = Pattern.compile("x=\"([^\"]+)\" y=\"([^\"]+)\" z=\"([^\"]+)\"");
        while (mr.find()) {
            String rid = mr.group(1).toUpperCase();
            if (!ids.contains(rid))
                continue;
            int fora = 0, total = 0;
            double pior = 0;
            Matcher q = ps.matcher(mr.group(2));
            while (q.find()) {
                float x = Float.parseFloat(q.group(1)), y = Float.parseFloat(q.group(2)), z = Float.parseFloat(q.group(3));
                total++;
                float zc = map.getZ(x, y, z + 1.5f, z - 1.5f, 1);
                if (Float.isNaN(zc)) {
                    float zz = map.getZ(x, y, z + 20, z - 20, 1);
                    fora++;
                    pior = Math.max(pior, Float.isNaN(zz) ? 99 : Math.abs(zz - z));
                }
            }
            System.out.printf(Locale.ROOT, "%s %d %d %.1f%n", rid, fora, total, pior);
        }
    }
}
