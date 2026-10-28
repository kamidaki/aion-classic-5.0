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
 * Para cada spot com walker_id de um XML de spawn, mede a distância vertical entre cada passo da rota e o chão do geo mais perto.
 * Passo a mais de 1,5 m do chão nunca é alcançado pelo NpcMoveController (o NPC é colado no chão).
 * Uso: GeoRotas <mapa> <spawn.xml> <npc_walker.xml>
 */
public class GeoRotas {
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
        Map<String, List<float[]>> rotas = new HashMap<>();
        Matcher mr = Pattern.compile("<walker_template route_id=\"(\\w+)\"[^>]*>(.*?)</walker_template>", Pattern.DOTALL).matcher(Files.readString(Path.of(a[2])));
        Pattern ps = Pattern.compile("x=\"([^\"]+)\" y=\"([^\"]+)\" z=\"([^\"]+)\"");
        while (mr.find()) {
            List<float[]> l = new ArrayList<>();
            Matcher q = ps.matcher(mr.group(2));
            while (q.find())
                l.add(new float[] { Float.parseFloat(q.group(1)), Float.parseFloat(q.group(2)), Float.parseFloat(q.group(3)) });
            rotas.put(mr.group(1), l);
        }
        String txt = Files.readString(Path.of(a[1])).replaceAll("(?s)<!--.*?-->", "");
        Matcher sp = Pattern.compile("<spawn\\b[^>]*npc_id=\"(\\d+)\"[^>]*>(.*?)</spawn>", Pattern.DOTALL).matcher(txt);
        Pattern pw = Pattern.compile("<spot\\b[^>]*?\\bx=\"([-\\d.]+)\"[^>]*?\\by=\"([-\\d.]+)\"[^>]*?walker_id=\"(\\w+)\"");
        int ok = 0, ruins = 0;
        while (sp.find()) {
            Matcher m = pw.matcher(sp.group(2));
            while (m.find()) {
                List<float[]> st = rotas.get(m.group(3));
                if (st == null) {
                    System.out.printf("SEM_ROTA npc %s %s%n", sp.group(1), m.group(3));
                    continue;
                }
                int fora = 0;
                double pior = 0;
                for (float[] s : st) {
                    float z = map.getZ(s[0], s[1], s[2] + 1.5f, s[2] - 1.5f, 1);
                    if (Float.isNaN(z)) {
                        // chão mais perto num intervalo maior, só para medir
                        float zz = map.getZ(s[0], s[1], s[2] + 20, s[2] - 20, 1);
                        fora++;
                        pior = Math.max(pior, Float.isNaN(zz) ? 99 : Math.abs(zz - s[2]));
                    }
                }
                if (fora == 0) ok++;
                else {
                    ruins++;
                    System.out.printf("RUIM npc %s spot (%s,%s) rota %s: %d de %d passos a mais de 1,5 m do chão (pior %.1f m)%n", sp.group(1), m.group(1),
                        m.group(2), m.group(3).substring(0, 8), fora, st.size(), pior);
                }
            }
        }
        System.out.printf("TOTAL rotas ok=%d ruins=%d%n", ok, ruins);
    }
}
