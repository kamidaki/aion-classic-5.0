import java.lang.reflect.*;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.lostacademy.nav.*;

/** Imprime o caminho do NavService entre dois pontos: NavDebug <dir_nav> <mapa> x1 y1 z1 x2 y2 z2 */
public class NavDebug {
    public static void main(String[] a) throws Exception {
        try { roda(a); } catch (Throwable t) { t.printStackTrace(); } finally { System.exit(0); }
    }

    static void roda(String[] a) throws Exception {
        GeoDataConfig.GEO_NAV_ENABLE = true;
        GeoDataConfig.GEO_ENABLE = false;
        GeoDataConfig.GEO_NAV_DIR = a[0];
        int world = Integer.parseInt(a[1]);
        float[] p = new float[6];
        for (int i = 0; i < 6; i++) p[i] = Float.parseFloat(a[2 + i]);
        NavService ns = NavService.getInstance();
        NavData.getInstance().onPlayerEnterMap(world);
        Class<?> geo = Class.forName("com.aionemu.gameserver.geoEngine.scene.NavGeometry");
        Method nav = NavService.class.getDeclaredMethod("navigateFromLocationToLocation", int.class, geo, geo, float.class, float.class, float.class, float.class, float.class, float.class);
        nav.setAccessible(true);
        Method tile = NavService.class.getDeclaredMethod("getNavTile", int.class, float.class, float.class, float.class);
        tile.setAccessible(true);
        for (int k = 0; k < 2; k++) {
            Object t = tile.invoke(ns, world, p[k * 3], p[k * 3 + 1], p[k * 3 + 2]);
            System.out.println("tile " + k + ": " + descreve(t));
        }
        float[][] path = (float[][]) nav.invoke(ns, world, null, null, p[0], p[1], p[2], p[3], p[4], p[5]);
        System.out.println("caminho: " + (path == null ? "null" : path.length + " pontos"));
        if (path != null)
            for (float[] w : path) System.out.printf("   %.2f %.2f %.2f%n", w[0], w[1], w[2]);
    }

    static String descreve(Object t) throws Exception {
        if (t == null) return "null";
        StringBuilder sb = new StringBuilder();
        for (int e = 1; e <= 3; e++) {
            Method m = t.getClass().getMethod("getEndpoints", byte.class);
            float[][] ep = (float[][]) m.invoke(t, (byte) e);
            Method g = t.getClass().getMethod("getEdge" + e);
            sb.append(String.format(" e%d (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f) viz=%s", e, ep[0][0], ep[0][1], ep[0][2], ep[1][0], ep[1][1], ep[1][2], g.invoke(t) != null));
        }
        return sb.toString();
    }
}
