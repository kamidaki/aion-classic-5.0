import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.lostacademy.nav.*;

public class NavTeste {
    public static void main(String[] a) throws Exception {
        try { roda(a); } catch (Throwable t) { t.printStackTrace(); } finally { System.exit(0); }
    }
    static void roda(String[] a) throws Exception {
        GeoDataConfig.GEO_NAV_ENABLE = true;
        GeoDataConfig.GEO_ENABLE = false;
        if (a.length > 1)
            GeoDataConfig.GEO_NAV_DIR = a[1];
        String walker = new String(Files.readAllBytes(Path.of(a[0])), "UTF-8");
        int ini = walker.indexOf("gera_50_capitais_movimento.py");
        Pattern p = Pattern.compile("<!-- (\\S+) npc (\\d+) \\(([^)]*)\\) -->\\s*<walker_template route_id=\"\\w+\"([^>]*)>(.*?)</walker_template>", Pattern.DOTALL);
        Pattern ps = Pattern.compile("x=\"([^\"]+)\" y=\"([^\"]+)\" z=\"([^\"]+)\"");
        NavService ns = NavService.getInstance();
        Class<?> geo = Class.forName("com.aionemu.gameserver.geoEngine.scene.NavGeometry");
        Method nav = NavService.class.getDeclaredMethod("navigateFromLocationToLocation", int.class, geo, geo, float.class, float.class, float.class, float.class, float.class, float.class);
        nav.setAccessible(true);
        Method tile = NavService.class.getDeclaredMethod("getNavTile", int.class, float.class, float.class, float.class);
        tile.setAccessible(true);
        NavData.getInstance().onPlayerEnterMap(110010000);
        NavData.getInstance().onPlayerEnterMap(120010000);
        Matcher m = p.matcher(walker.substring(ini));
        while (m.find()) {
            int world = m.group(1).startsWith("110") ? 110010000 : 120010000;
            List<float[]> st = new ArrayList<>();
            Matcher q = ps.matcher(m.group(5));
            while (q.find())
                st.add(new float[] { Float.parseFloat(q.group(1)), Float.parseFloat(q.group(2)), Float.parseFloat(q.group(3)) });
            boolean wb = m.group(4).contains("WALK_BACK");
            if (wb)
                for (int i = st.size() - 2; i > 0; i--)
                    st.add(st.get(i));
            int falha = 0, fora = 0, desvio = 0;
            double zdif = 0;
            StringBuilder ex = new StringBuilder();
            for (int i = 0; i < st.size(); i++) {
                float[] s = st.get(i), t = st.get((i + 1) % st.size());
                if (tile.invoke(ns, world, s[0], s[1], s[2]) == null)
                    fora++;
                float z = ns.getNavSurfaceZ(world, s[0], s[1], s[2]);
                if (!Float.isNaN(z))
                    zdif = Math.max(zdif, Math.abs(z - s[2]));
                float[][] path = (float[][]) nav.invoke(ns, world, null, null, s[0], s[1], s[2], t[0], t[1], t[2]);
                if (path == null || path.length == 0) {
                    falha++;
                    if (ex.length() < 150)
                        ex.append(String.format(" (%.0f,%.0f)->(%.0f,%.0f)", s[0], s[1], t[0], t[1]));
                    continue;
                }
                float[] fim = path[path.length - 1];
                double d = Math.hypot(fim[0] - t[0], fim[1] - t[1]);
                double len = 0;
                float[] prev = s;
                for (float[] w : path) {
                    len += Math.hypot(w[0] - prev[0], w[1] - prev[1]);
                    prev = w;
                }
                double reto = Math.hypot(t[0] - s[0], t[1] - s[1]);
                if (d > 1.0 || len > reto * 1.5 + 2) {
                    desvio++;
                    if (ex.length() < 300)
                        ex.append(String.format(" [desvio (%.0f,%.0f)->(%.0f,%.0f) fim a %.1f m, %.0f m vs %.0f m]", s[0], s[1], t[0], t[1], d, len, reto));
                }
            }
            System.out.printf("RES %s npc %s %s passos=%d fora_da_malha=%d sem_caminho=%d desvio=%d dZ_max=%.1f%s%n", m.group(1), m.group(2),
                wb ? "WALK_BACK" : "NORMAL", st.size(), fora, falha, desvio, zdif, ex);
        }
        System.exit(0);
    }
}
