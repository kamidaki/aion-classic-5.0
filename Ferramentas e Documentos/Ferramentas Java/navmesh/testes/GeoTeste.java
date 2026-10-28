import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.MaterialData;
import com.aionemu.gameserver.geoEngine.GeoWorldLoader;
import com.aionemu.gameserver.geoEngine.models.GeoMap;

/** Carrega o geo de um mapa e mede, em cada passo das rotas novas, o chão do geo e a passagem até o passo seguinte. */
public class GeoTeste {
    public static void main(String[] a) throws Exception {
        try { roda(a); } catch (Throwable t) { t.printStackTrace(); } finally { System.exit(0); }
    }

    static void roda(String[] a) throws Exception {
        Constructor<MaterialData> c = MaterialData.class.getDeclaredConstructor();
        c.setAccessible(true);
        DataManager.MATERIAL_DATA = c.newInstance();
        Constructor<com.aionemu.gameserver.dataholders.ZoneData> cz = com.aionemu.gameserver.dataholders.ZoneData.class.getDeclaredConstructor();
        cz.setAccessible(true);
        DataManager.ZONE_DATA = cz.newInstance();
        int world = Integer.parseInt(a[1]);
        GeoMap map = new GeoMap(world);
        GeoWorldLoader.load(List.of(map));
        String walker = new String(Files.readAllBytes(Path.of(a[0])), "UTF-8");
        int ini = walker.indexOf("gera_50_capitais_movimento.py");
        Pattern p = Pattern.compile("<!-- (\\S+) npc (\\d+) \\(([^)]*)\\) -->\\s*<walker_template route_id=\"\\w+\"([^>]*)>(.*?)</walker_template>", Pattern.DOTALL);
        Pattern ps = Pattern.compile("x=\"([^\"]+)\" y=\"([^\"]+)\" z=\"([^\"]+)\"");
        Matcher m = p.matcher(walker.substring(ini));
        while (m.find()) {
            if ((m.group(1).startsWith("110") ? 110010000 : 120010000) != world)
                continue;
            List<float[]> st = new ArrayList<>();
            Matcher q = ps.matcher(m.group(5));
            while (q.find())
                st.add(new float[] { Float.parseFloat(q.group(1)), Float.parseFloat(q.group(2)), Float.parseFloat(q.group(3)) });
            int semChao = 0, bloqueio = 0;
            double dz = 0;
            StringBuilder ex = new StringBuilder();
            for (int i = 0; i < st.size(); i++) {
                float[] s = st.get(i), t = st.get((i + 1) % st.size());
                float z = map.getZ(s[0], s[1], s[2] + 2, s[2] - 2, 1);
                if (Float.isNaN(z)) {
                    semChao++;
                    if (ex.length() < 150) ex.append(String.format(" sem chão (%.0f,%.0f,%.1f)", s[0], s[1], s[2]));
                } else
                    dz = Math.max(dz, Math.abs(z - s[2]));
                if (!map.canPass(s[0], s[1], s[2] + 1, t[0], t[1], t[2] + 1, 0, 1)) {
                    bloqueio++;
                    if (ex.length() < 300) ex.append(String.format(" [bloqueio (%.0f,%.0f)->(%.0f,%.0f)]", s[0], s[1], t[0], t[1]));
                }
            }
            System.out.printf("RES npc %s passos=%d sem_chao=%d bloqueio=%d dZ_max=%.2f%s%n", m.group(2), st.size(), semChao, bloqueio, dz, ex);
        }
    }
}
