import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.lostacademy.nav.*;

/** Diz quais spots de um XML de spawn caem na navmesh: NavSpots <dir_nav> <mapa> <spawn.xml> */
public class NavSpots {
    public static void main(String[] a) throws Exception {
        try { roda(a); } catch (Throwable t) { t.printStackTrace(); } finally { System.exit(0); }
    }

    static void roda(String[] a) throws Exception {
        GeoDataConfig.GEO_NAV_ENABLE = true;
        GeoDataConfig.GEO_ENABLE = false;
        GeoDataConfig.GEO_NAV_DIR = a[0];
        int world = Integer.parseInt(a[1]);
        NavService ns = NavService.getInstance();
        NavData.getInstance().onPlayerEnterMap(world);
        Method tile = NavService.class.getDeclaredMethod("getNavTile", int.class, float.class, float.class, float.class);
        tile.setAccessible(true);
        String txt = Files.readString(Path.of(a[2])).replaceAll("(?s)<!--.*?-->", "");
        Matcher sp = Pattern.compile("<spawn\\b[^>]*npc_id=\"(\\d+)\"[^>]*>(.*?)</spawn>", Pattern.DOTALL).matcher(txt);
        Pattern pt = Pattern.compile("<spot\\b[^>]*?\\bx=\"([-\\d.]+)\"[^>]*?\\by=\"([-\\d.]+)\"[^>]*?\\bz=\"([-\\d.]+)\"([^>]*)");
        int dentro = 0, fora = 0;
        while (sp.find()) {
            Matcher m = pt.matcher(sp.group(2));
            while (m.find()) {
                float x = Float.parseFloat(m.group(1)), y = Float.parseFloat(m.group(2)), z = Float.parseFloat(m.group(3));
                boolean ok = tile.invoke(ns, world, x, y, z) != null;
                if (ok) dentro++;
                else {
                    fora++;
                    float sz = ns.getNavSurfaceZ(world, x, y, z);
                    boolean anda = m.group(4).contains("walker_id") || m.group(4).contains("random_walk");
                    System.out.printf("FORA npc %s (%.1f, %.1f, %.1f)%s malha mais perto z=%.1f%n", sp.group(1), x, y, z, anda ? " [anda]" : "", sz);
                }
            }
        }
        System.out.printf("TOTAL dentro=%d fora=%d%n", dentro, fora);
    }
}
