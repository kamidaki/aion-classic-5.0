import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import com.lostacademy.nativepath.PathDatGrid;
import com.lostacademy.nativepath.PathDatMap;

/** java TesteCarga <data> <mapa> <dat> x y z raio n : n destinos aleatórios (piso livre) até raio m de (x,y,z), modo do servidor. */
public class TesteCarga {
	public static void main(String[] a) throws Exception {
		Path data = Path.of(a[0]);
		PathDatMap m = PathDatMap.carrega(Path.of(a[2]), 3072, TesteVoltas.terreno(data.resolve("geo/" + a[1] + ".png")));
		float x = Float.parseFloat(a[3]), y = Float.parseFloat(a[4]), z = Float.parseFloat(a[5]), raio = Float.parseFloat(a[6]);
		int n = Integer.parseInt(a[7]);
		PathDatGrid g = new PathDatGrid(m, true, false);
		Random r = new Random(7);
		double[] tOk = new double[n], tFalha = new double[n];
		int ok = 0, falha = 0;
		for (int k = 0; k < n; k++) {
			float tx = x + (r.nextFloat() * 2 - 1) * raio, ty = y + (r.nextFloat() * 2 - 1) * raio;
			List<PathDatMap.Piso> p = m.pisos((int) (tx / 0.5f), (int) (ty / 0.5f));
			p = p.stream().filter(PathDatMap.Piso::livre).toList();
			if (p.isEmpty()) { k--; continue; }
			float tz = p.get(r.nextInt(p.size())).z();
			long t0 = System.nanoTime();
			List<float[]> c = g.encontra(x, y, z, tx, ty, tz, 100_000, 100f);
			double ms = (System.nanoTime() - t0) / 1e6;
			if (c != null) tOk[ok++] = ms; else tFalha[falha++] = ms;
		}
		tOk = Arrays.copyOf(tOk, ok); tFalha = Arrays.copyOf(tFalha, falha);
		Arrays.sort(tOk); Arrays.sort(tFalha);
		System.out.printf("com caminho: %d, mediana %.1f ms, p95 %.1f ms, máx %.1f ms%n", ok, q(tOk, .5), q(tOk, .95), q(tOk, 1));
		System.out.printf("sem caminho: %d, mediana %.1f ms, p95 %.1f ms, máx %.1f ms%n", falha, q(tFalha, .5), q(tFalha, .95), q(tFalha, 1));
	}
	static double q(double[] v, double p) { return v.length == 0 ? 0 : v[Math.min(v.length - 1, (int) (p * v.length))]; }
}
