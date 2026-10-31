import java.awt.image.Raster;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.imageio.ImageIO;

import com.lostacademy.nativepath.PathDatGrid;
import com.lostacademy.nativepath.PathDatMap;

/**
 * Teste fora do jogo do PathDatMap/PathDatGrid contra voltas oficiais de mobs (voltas_oficiais.tsv, exportado pelo
 * pathdat/voltas_captura.py das capturas de 27/10/2026).
 * <p>
 * Uso: java TesteVoltas &lt;data do game-server&gt; voltas_oficiais.tsv
 */
public class TesteVoltas {

	/** Mesmo cálculo do geoEngine.models.Terrain (triângulos p1,p2,p3 e p2,p3,p4; borda = 0; 0xFFFF = buraco). */
	static PathDatMap.Terreno terreno(Path png) throws Exception {
		if (!Files.exists(png))
			return (x, y) -> Float.NaN;
		Raster r = ImageIO.read(png.toFile()).getRaster();
		int w = r.getWidth(), h = r.getHeight();
		return (x, y) -> {
			int i = (int) (x / 2), j = (int) (y / 2);
			float fx = x / 2 - i, fy = y / 2 - j;
			float z1 = hz(r, w, h, i, j), z2 = hz(r, w, h, i, j + 1), z3 = hz(r, w, h, i + 1, j), z4 = hz(r, w, h, i + 1, j + 1);
			if (fx + fy <= 1)
				return z1 + (z3 - z1) * fx + (z2 - z1) * fy;
			return z4 + (z2 - z4) * (1 - fx) + (z3 - z4) * (1 - fy);
		};
	}

	static float hz(Raster r, int w, int h, int i, int j) {
		if (i <= 0 || j <= 0 || i >= h || j >= w)
			return 0;
		int v = r.getSample(j, i, 0);
		return v == 0xFFFF ? Float.NaN : v * 2048f / 65536f;
	}

	static double afastamento(float[] q, List<float[]> C) {
		double best = 1e9;
		for (int k = 0; k + 1 < C.size(); k++) {
			float[] a = C.get(k), b = C.get(k + 1);
			double dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
			double f = L == 0 ? 0 : Math.max(0, Math.min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L));
			best = Math.min(best, Math.hypot(a[0] + dx * f - q[0], a[1] + dy * f - q[1]));
		}
		return best;
	}

	static double comprimento(List<float[]> C) {
		double s = 0;
		for (int k = 0; k + 1 < C.size(); k++)
			s += Math.hypot(C.get(k + 1)[0] - C.get(k)[0], C.get(k + 1)[1] - C.get(k)[1]);
		return s;
	}

	public static void main(String[] a) throws Exception {
		Path data = Path.of(a[0]);
		Map<Integer, PathDatMap> mapas = new HashMap<>();
		int ok = 0, ok1 = 0, n = 0, retasOficial = 0, retasPiso = 0;
		long tempo = 0;
		for (String linha : Files.readAllLines(Path.of(a[1]))) {
			String[] c = linha.split("\t");
			int mapa = Integer.parseInt(c[0]);
			PathDatMap m = mapas.get(mapa);
			if (m == null) {
				File dir = data.resolve("native-path").toFile().listFiles((d, nome) -> nome.startsWith(mapa + "_"))[0];
				File dat = dir.listFiles((d, nome) -> nome.endsWith(".dat"))[0];
				long t0 = System.nanoTime();
				m = PathDatMap.carrega(dat.toPath(), 3072, terreno(data.resolve("geo/" + mapa + ".png")));
				System.out.printf("%d carregado em %d ms (%d m)%n", mapa, (System.nanoTime() - t0) / 1_000_000, m.getTamanho());
				mapas.put(mapa, m);
			}
			List<float[]> ofic = new ArrayList<>();
			for (String p : c[3].split(";")) {
				String[] v = p.split(",");
				ofic.add(new float[] { Float.parseFloat(v[0]), Float.parseFloat(v[1]), Float.parseFloat(v[2]) });
			}
			float[] ini = ofic.get(0), fim = ofic.get(ofic.size() - 1);
			long t0 = System.nanoTime();
			List<float[]> C = new PathDatGrid(m, false).encontra(ini[0], ini[1], ini[2], fim[0], fim[1], fim[2], 300_000);
			tempo += System.nanoTime() - t0;
			List<float[]> P = new PathDatGrid(m, true).encontra(ini[0], ini[1], ini[2], fim[0], fim[1], fim[2], 300_000);
			n++;
			if (C == null) {
				System.out.printf("%s %s t=%s: SEM CAMINHO%n", c[0], c[1], c[2]);
				continue;
			}
			C.add(0, ini);
			double desvio = 0;
			for (float[] q : ofic)
				desvio = Math.max(desvio, afastamento(q, C));
			ok += desvio <= 1.5 ? 1 : 0;
			ok1 += desvio <= 1.0 ? 1 : 0;
			retasOficial += C.size() - 1;
			retasPiso += P == null ? 0 : P.size();
			System.out.printf("%s %s t=%6s: oficial %d trechos %6.1f m | Java %d trechos %6.1f m | afastamento %.2f m | seguindo o piso %d trechos%n",
				c[0], c[1], c[2], ofic.size() - 1, comprimento(ofic), C.size() - 1, comprimento(C), desvio, P == null ? -1 : P.size());
		}
		System.out.printf("%n%d de %d voltas <= 1,5 m (%d <= 1,0 m); busca média %.1f ms; trechos: como o oficial %d, seguindo o piso %d%n",
			ok, n, ok1, tempo / 1e6 / n, retasOficial, retasPiso);
	}
}
