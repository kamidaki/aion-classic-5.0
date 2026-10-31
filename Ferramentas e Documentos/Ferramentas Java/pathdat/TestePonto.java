import java.nio.file.Path;
import java.util.List;
import com.lostacademy.nativepath.PathDatGrid;
import com.lostacademy.nativepath.PathDatMap;

/** java TestePonto <data> <mapa> <dat> x1 y1 z1 x2 y2 z2 : caminho do servidor entre dois pontos. */
public class TestePonto {
	public static void main(String[] a) throws Exception {
		Path data = Path.of(a[0]);
		PathDatMap m = PathDatMap.carrega(Path.of(a[2]), 3072, TesteVoltas.terreno(data.resolve("geo/" + a[1] + ".png")));
		float[] v = new float[6];
		for (int i = 0; i < 6; i++) v[i] = Float.parseFloat(a[3 + i]);
		for (boolean queda : new boolean[] { true, false }) {
			boolean piso = true;
			PathDatGrid g = new PathDatGrid(m, piso, queda);
			long b = g.noEm(v[3], v[4], v[5]);
			float[] pb = b == 0 ? null : g.ponto(b);
			long t0 = System.nanoTime();
			List<float[]> r = g.encontra(v[0], v[1], v[2], v[3], v[4], v[5], 100_000, queda ? Float.MAX_VALUE : 100f);
			System.out.printf("%-26s destino escolhido %s em %.1f ms: ", queda ? "oficial (cai, sem limite)" : "servidor (anda, 100 m)", pb == null ? "nenhum" : String.format("(%.2f,%.2f,%.2f)", pb[0], pb[1], pb[2]),
				(System.nanoTime() - t0) / 1e6);
			if (r == null) System.out.println("SEM CAMINHO");
			else { StringBuilder s = new StringBuilder(); for (float[] p : r) s.append(String.format("(%.2f,%.2f,%.2f) ", p[0], p[1], p[2])); System.out.println(r.size() + " pontos " + s); }
		}
	}
}
