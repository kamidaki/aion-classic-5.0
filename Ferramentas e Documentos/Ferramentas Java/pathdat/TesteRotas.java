import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.lostacademy.nativepath.PathDatGrid;
import com.lostacademy.nativepath.PathDatMap;

/**
 * Confere as rotas do npc_walker usadas nos spawns contra a grade do path.dat no modo do servidor (sem queda): cada passo tem de
 * alcançar o seguinte (e o último o primeiro, nas rotas em circuito).
 * <p>
 * Uso: java TesteRotas &lt;data do game-server&gt;
 */
public class TesteRotas {

	/** piso livre mais perto de q nas células vizinhas (a rota pode passar rente a uma parede) */
	static float nearPiso(PathDatGrid g, float[] q) {
		float best = Float.NaN;
		for (int dx = -2; dx <= 2; dx++)
			for (int dy = -2; dy <= 2; dy++) {
				float z = g.alturaPiso(q[0] + dx * 0.5f, q[1] + dy * 0.5f, q[2]);
				if (!Float.isNaN(z) && (Float.isNaN(best) || Math.abs(z - q[2]) < Math.abs(best - q[2])))
					best = z;
			}
		return best;
	}

	public static void main(String[] a) throws Exception {
		Path data = Path.of(a[0]);
		// rota -> mapa (pelos spawns)
		Map<String, Integer> rotaMapa = new HashMap<>();
		Pattern pMapa = Pattern.compile("<spawn_map[^>]*map_id=\"(\\d+)\"");
		Pattern pRota = Pattern.compile("walker_id=\"([0-9A-Fa-f]+)\"");
		try (var arqs = Files.walk(data.resolve("static_data/spawns"))) {
			for (Path f : arqs.filter(p -> p.toString().endsWith(".xml")).toList()) {
				String x = Files.readString(f).replaceAll("(?s)<!--.*?-->", "");
				Matcher mm = pMapa.matcher(x);
				int mapa = mm.find() ? Integer.parseInt(mm.group(1)) : -1;
				Matcher mr = pRota.matcher(x);
				while (mr.find())
					rotaMapa.putIfAbsent(mr.group(1).toUpperCase(), mapa);
			}
		}
		// rotas
		String w = Files.readString(data.resolve("static_data/npc_walker/npc_walker.xml")).replaceAll("(?s)<!--.*?-->", "");
		Matcher mt = Pattern.compile("(?s)<walker_template([^>]*)>(.*?)</walker_template>").matcher(w);
		Pattern pPasso = Pattern.compile("<routestep[^>]*?x=\"([-\\d.]+)\"[^>]*?y=\"([-\\d.]+)\"[^>]*?z=\"([-\\d.]+)\"");
		Map<Integer, List<Object[]>> porMapa = new TreeMap<>();
		while (mt.find()) {
			Matcher id = Pattern.compile("route_id=\"([0-9A-Fa-f]+)\"").matcher(mt.group(1));
			if (!id.find())
				continue;
			Integer mapa = rotaMapa.get(id.group(1).toUpperCase());
			if (mapa == null)
				continue;
			boolean volta = mt.group(1).contains("WALK_BACK") || mt.group(1).contains("reversed=\"true\"");
			List<float[]> passos = new ArrayList<>();
			Matcher mp = pPasso.matcher(mt.group(2));
			while (mp.find())
				passos.add(new float[] { Float.parseFloat(mp.group(1)), Float.parseFloat(mp.group(2)), Float.parseFloat(mp.group(3)) });
			if (passos.size() >= 2)
				porMapa.computeIfAbsent(mapa, k -> new ArrayList<>()).add(new Object[] { id.group(1), passos, volta });
		}
		int totRotas = 0, totTrechos = 0, totFalhas = 0, rotasRuins = 0;
		for (var e : porMapa.entrySet()) {
			int mapa = e.getKey();
			File[] dirs = data.resolve("native-path").toFile().listFiles((d, n) -> n.startsWith(mapa + "_"));
			if (dirs == null || dirs.length == 0) {
				System.out.printf("%d: sem path.dat (%d rotas ficam na navmesh)%n", mapa, e.getValue().size());
				continue;
			}
			File dat = dirs[0].listFiles((d, n) -> n.endsWith(".dat"))[0];
			PathDatMap m = PathDatMap.carrega(dat.toPath(), 3072, TesteVoltas.terreno(data.resolve("geo/" + mapa + ".png")));
			PathDatGrid g = new PathDatGrid(m, true, false);
			int falhas = 0, trechos = 0, ruins = 0, aereos = 0;
			long t0 = System.nanoTime();
			Map<String, String> exemplos = new LinkedHashMap<>();
			for (Object[] r : e.getValue()) {
				@SuppressWarnings("unchecked")
				List<float[]> p = (List<float[]>) r[1];
				boolean volta = (Boolean) r[2];
				int n = p.size(), f0 = falhas;
				boolean aerea = false;
				for (float[] q : p) {
					float pz = g.alturaPiso(q[0], q[1], q[2]);
					if (Float.isNaN(pz) ? Float.isNaN(nearPiso(g, q)) : Math.abs(pz - q[2]) > PathDatGrid.TOLERANCIA_PONTO && Math.abs(nearPiso(g, q) - q[2]) > PathDatGrid.TOLERANCIA_PONTO)
						aerea = true;
				}
				if (aerea) {
					aereos++;
					continue;
				}
				for (int i = 0; i < n; i++) {
					List<int[]> pares = new ArrayList<>();
					if (i + 1 < n)
						pares.add(new int[] { i, i + 1 });
					else if (!volta)
						pares.add(new int[] { i, 0 });
					if (volta && i + 1 < n)
						pares.add(new int[] { i + 1, i });
					for (int[] q : pares) {
						float[] s = p.get(q[0]), d = p.get(q[1]);
						trechos++;
						if (g.encontra(s[0], s[1], s[2], d[0], d[1], d[2], 100_000) == null) {
							falhas++;
							if (exemplos.size() < 6)
								exemplos.put((String) r[0] + " " + q[0] + "->" + q[1],
									String.format("(%.1f,%.1f,%.1f)->(%.1f,%.1f,%.1f) piso origem %.2f destino %.2f", s[0], s[1], s[2], d[0], d[1], d[2],
										g.alturaPiso(s[0], s[1], s[2]), g.alturaPiso(d[0], d[1], d[2])));
						}
					}
				}
				if (falhas > f0)
					ruins++;
			}
			System.out.printf("%d: %d rotas (%d aéreas), %d trechos, %d sem caminho (%d rotas afetadas), %.0f ms%n", mapa, e.getValue().size(), aereos, trechos, falhas, ruins,
				(System.nanoTime() - t0) / 1e6);
			exemplos.forEach((k, v) -> System.out.println("     " + k + " " + v));
			totRotas += e.getValue().size();
			totTrechos += trechos;
			totFalhas += falhas;
			rotasRuins += ruins;
		}
		System.out.printf("%nTOTAL: %d rotas, %d trechos, %d sem caminho, %d rotas afetadas%n", totRotas, totTrechos, totFalhas, rotasRuins);
	}
}
