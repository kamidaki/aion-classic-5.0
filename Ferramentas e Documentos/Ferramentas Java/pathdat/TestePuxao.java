import java.nio.file.Path;
import java.util.List;
import java.util.Random;
import com.lostacademy.nativepath.PathDatGrid;
import com.lostacademy.nativepath.PathDatMap;

/** Taxa de recusa do retaAndavel (canPullTarget) entre pontos de chão a 8-20 m: java TestePuxao <data> <mapa> <dat> x y raio */
public class TestePuxao {
	public static void main(String[] a) throws Exception {
		Path data = Path.of(a[0]);
		PathDatMap m = PathDatMap.carrega(Path.of(a[2]), 3072, TesteVoltas.terreno(data.resolve("geo/" + a[1] + ".png")));
		float cx = Float.parseFloat(a[3]), cy = Float.parseFloat(a[4]), raio = Float.parseFloat(a[5]);
		PathDatGrid[] gs = { new PathDatGrid(m, true, false), new PathDatGrid(m, false, false), new PathDatGrid(m, false, true) };
		String[] nomes = { "seguePiso, sem queda (atual)", "sem seguePiso, sem queda", "sem seguePiso, com queda" };
		int[] ok = new int[3];
		int n = 0;
		Random r = new Random(3);
		while (n < 2000) {
			float x1 = cx + (r.nextFloat() * 2 - 1) * raio, y1 = cy + (r.nextFloat() * 2 - 1) * raio;
			double ang = r.nextDouble() * Math.PI * 2, d = 8 + r.nextDouble() * 12;
			float x2 = (float) (x1 + Math.cos(ang) * d), y2 = (float) (y1 + Math.sin(ang) * d);
			List<PathDatMap.Piso> p1 = m.pisos((int) (x1 / .5f), (int) (y1 / .5f)).stream().filter(PathDatMap.Piso::livre).toList();
			List<PathDatMap.Piso> p2 = m.pisos((int) (x2 / .5f), (int) (y2 / .5f)).stream().filter(PathDatMap.Piso::livre).toList();
			if (p1.isEmpty() || p2.isEmpty()) continue;
			float z1 = p1.get(0).z(), z2 = p2.get(0).z();
			if (Math.abs(z1 - z2) > 3) continue;          // mesmo nível, como num puxão comum
			n++;
			for (int i = 0; i < 3; i++)
				if (gs[i].retaAndavel(x1, y1, z1, x2, y2, z2)) ok[i]++;
		}
		for (int i = 0; i < 3; i++) System.out.printf("%-30s aceita %.1f%%%n", nomes[i], 100.0 * ok[i] / n);
	}
}
