import java.io.*;
import java.lang.reflect.*;
import java.nio.*;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

import org.recast4j.recast.*;
import org.recast4j.recast.geom.SimpleInputGeomProvider;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.MaterialData;
import com.aionemu.gameserver.dataholders.ZoneData;
import com.aionemu.gameserver.geoEngine.GeoWorldLoader;
import com.aionemu.gameserver.geoEngine.collision.CollisionIntention;
import com.aionemu.gameserver.geoEngine.math.Matrix4f;
import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.geoEngine.models.GeoMap;
import com.aionemu.gameserver.geoEngine.models.Terrain;
import com.aionemu.gameserver.geoEngine.scene.DespawnableNode;
import com.aionemu.gameserver.geoEngine.scene.Geometry;
import com.aionemu.gameserver.geoEngine.scene.Node;

/**
 * Gera o .nav (formato do NavData do emulador) de um mapa a partir do geo do próprio servidor.
 *
 * Entrada: data/geo (PNG do relevo + models.mesh + <mapa>.geo), lido pelo GeoWorldLoader do JAR.
 * Geometria usada: relevo + modelos com colisão PHYSICAL, WALK (paredes nowalk) ou PHYSICAL_SEE_THROUGH;
 * ficam de fora portas, objetos de evento/PLACEABLE/casa e malhas só de material.
 * Recast (recast4j 1.5.12) em blocos; a malha detalhada de todos os blocos é soldada pelos vértices e os
 * vizinhos saem das arestas compartilhadas (aresta 1 = v0-v1, 2 = v1-v2, 3 = v2-v0).
 *
 * Saída (little-endian): [int nº floats][x y z ...][int nº triângulos]{[3 int vértices][3 int vizinhos ou -1]}.
 * Triângulos anti-horários vistos de cima (normal +Z), como o .nav herdado.
 *
 * Uso (pasta GameServer como diretório atual):
 *   java -Xmx9g -Dnav.sementes=data/static_data/spawns/Npcs/<mapa>_<nome>.xml -cp "libs/*;recast-1.5.12.jar;." GeraNav <mapa> <saida.nav> [xmin ymin xmax ymax]
 *
 * Padrões validados em Pandaemonium (25/10/2026) contra as 13 rotas oficiais das capturas: malha detalhada com amostra de 6 m e
 * erro de 0,5 m, polígono de até 12 m, agente com raio 0,2 m, altura 1,5 m, degrau 1,2 m, rampa 60° e chão do avesso aceito.
 * Todos mudam por -Dnav.*; ver as constantes abaixo.
 */
public class GeraNav {

	// agente (metros)
	static final float CELULA = 0.25f, ALTURA_CELULA = 0.15f;
	static final float AGENTE_ALTURA = Float.parseFloat(System.getProperty("nav.altura", "1.5"));
	static final float AGENTE_RAIO = Float.parseFloat(System.getProperty("nav.raio", "0.2"));
	static final float AGENTE_DEGRAU = Float.parseFloat(System.getProperty("nav.degrau", "1.2"));
	static final float RAMPA_MAX = Float.parseFloat(System.getProperty("nav.rampa", "60"));
	static final int BLOCO_CELULAS = 256; // 64 m
	static final boolean DETALHE = !"false".equals(System.getProperty("nav.detalhe")); // malha detalhada; -Dnav.detalhe=false usa só os polígonos
	static final boolean DUPLA_FACE = !"false".equals(System.getProperty("nav.duplaface")); // vira para cima chão modelado do avesso
	static final float LADO_MAX = Float.parseFloat(System.getProperty("nav.lado", "12")); // lado máximo do polígono (m)
	static final float AMOSTRA = Float.parseFloat(System.getProperty("nav.amostra", "6")); // distância entre amostras de altura (m)
	static final float ERRO_ALTURA = Float.parseFloat(System.getProperty("nav.erro", "0.5")); // erro máximo de altura da malha detalhada (m)
	static final float ERRO_CONTORNO = Float.parseFloat(System.getProperty("nav.contorno", "1.1")); // erro máximo do contorno (m)
	static final byte SOLIDO = (byte) (CollisionIntention.PHYSICAL.getId() | CollisionIntention.WALK.getId()
		| CollisionIntention.PHYSICAL_SEE_THROUGH.getId());

	public static void main(String[] a) throws Exception {
		try {
			roda(a);
		} catch (Throwable t) {
			t.printStackTrace();
			System.exit(1);
		}
		System.exit(0);
	}

	static void roda(String[] a) throws Exception {
		int mapa = Integer.parseInt(a[0]);
		Path saida = Path.of(a[1]);
		Constructor<MaterialData> cm = MaterialData.class.getDeclaredConstructor();
		cm.setAccessible(true);
		DataManager.MATERIAL_DATA = cm.newInstance();
		Constructor<ZoneData> cz = ZoneData.class.getDeclaredConstructor();
		cz.setAccessible(true);
		DataManager.ZONE_DATA = cz.newInstance();

		GeoMap geo = new GeoMap(mapa);
		GeoWorldLoader.load(List.of(geo));

		// recorte opcional da área (x/y do Aion); sem ele, o mapa inteiro
		float[] area = a.length >= 6
			? new float[] { Float.parseFloat(a[2]), Float.parseFloat(a[3]), Float.parseFloat(a[4]), Float.parseFloat(a[5]) }
			: null;
		FloatList v = new FloatList();
		IntList f = new IntList();
		int modelos = adicionaModelos(geo, v, f);
		int nModelo = f.n / 3;
		int relevo = adicionaRelevo(geo, v, f, area);
		System.out.printf("geometria: %d triângulos de modelos (%d objetos), %d do relevo%n", nModelo, modelos, relevo);

		// Recast é Y para cima: (x, y, z) do Aion -> (x, z, y), com a ordem dos vértices invertida
		float[] rv = new float[v.n];
		for (int i = 0; i < v.n; i += 3) {
			rv[i] = v.d[i];
			rv[i + 1] = v.d[i + 2];
			rv[i + 2] = v.d[i + 1];
		}
		int[] rf = new int[f.n];
		for (int i = 0; i < f.n; i += 3) {
			rf[i] = f.d[i];
			rf[i + 1] = f.d[i + 2];
			rf[i + 2] = f.d[i + 1];
		}
		Entrada entrada = new Entrada(rv, rf, area);

		RecastConfig cfg = new RecastConfig(true, BLOCO_CELULAS, BLOCO_CELULAS, RecastConfig.calcBorder(AGENTE_RAIO, CELULA),
			RecastConstants.PartitionType.WATERSHED, CELULA, ALTURA_CELULA, RAMPA_MAX, true, true, true, AGENTE_ALTURA, AGENTE_RAIO,
			AGENTE_DEGRAU, 2f, 20f, LADO_MAX, ERRO_CONTORNO, 6, true, AMOSTRA, ERRO_ALTURA, new AreaModification(0x3f));
		RecastConfig cfgPoligono = new RecastConfig(true, BLOCO_CELULAS, BLOCO_CELULAS, RecastConfig.calcBorder(AGENTE_RAIO, CELULA),
			RecastConstants.PartitionType.WATERSHED, CELULA, ALTURA_CELULA, RAMPA_MAX, true, true, true, AGENTE_ALTURA, AGENTE_RAIO,
			AGENTE_DEGRAU, 2f, 20f, LADO_MAX, ERRO_CONTORNO, 6, false, AMOSTRA, ERRO_ALTURA, new AreaModification(0x3f));
		java.util.concurrent.atomic.AtomicInteger semDetalhe = new java.util.concurrent.atomic.AtomicInteger();
		float[] bmin = entrada.getMeshBoundsMin(), bmax = entrada.getMeshBoundsMax();
		float lado = BLOCO_CELULAS * CELULA;
		int bx = (int) Math.ceil((bmax[0] - bmin[0]) / lado), bz = (int) Math.ceil((bmax[2] - bmin[2]) / lado);
		System.out.printf("recast: %d x %d blocos de %.0f m%n", bx, bz, lado);

		// um bloco por vez em cada thread; do resultado só fica a malha detalhada (triângulos soltos, no mundo do Recast)
		// recast4j 1.5.12 tem estado compartilhado entre threads: em paralelo, buildPolyDetail solta ConcurrentModificationException
		// e pode estragar blocos sem avisar. Padrão: uma thread (Pandaemonium leva ~95 s).
		int threads = Integer.getInteger("nav.threads", 1);
		ExecutorService pool = Executors.newFixedThreadPool(threads);
		List<Future<float[]>> futuros = new ArrayList<>();
		long t0 = System.currentTimeMillis();
		java.util.concurrent.atomic.AtomicInteger feitos = new java.util.concurrent.atomic.AtomicInteger();
		for (int z = 0; z < bz; z++)
			for (int x = 0; x < bx; x++) {
				int tx = x, tz = z;
				futuros.add(pool.submit(() -> {
					float[] tris;
					if (DETALHE) {
						try {
							tris = trianguloDetalhe(new RecastBuilder().build(entrada, new RecastBuilderConfig(cfg, bmin, bmax, tx, tz)).getMeshDetail());
						} catch (RuntimeException e) {
							// erro interno do recast4j na malha detalhada (ConcurrentModificationException em buildPolyDetail):
							// o bloco sai pelos polígonos, que não passam por essa etapa
							int n = semDetalhe.incrementAndGet();
							System.out.printf("   bloco %d,%d sem malha detalhada (%s), vai pelos polígonos [%d]%n", tx, tz, e.getClass().getSimpleName(), n);
							tris = triangulosPoligonos(new RecastBuilder().build(entrada, new RecastBuilderConfig(cfgPoligono, bmin, bmax, tx, tz)).getMesh());
						}
					} else
						tris = triangulosPoligonos(new RecastBuilder().build(entrada, new RecastBuilderConfig(cfg, bmin, bmax, tx, tz)).getMesh());
					int n = feitos.incrementAndGet();
					if (n % 50 == 0)
						System.out.printf("   %d/%d blocos (%d s)%n", n, bx * bz, (System.currentTimeMillis() - t0) / 1000);
					return tris;
				}));
			}
		List<float[]> blocos = new ArrayList<>();
		for (Future<float[]> fu : futuros)
			blocos.add(fu.get());
		pool.shutdown();
		System.out.printf("recast: %d blocos em %d s%n", blocos.size(), (System.currentTimeMillis() - t0) / 1000);

		grava(blocos, saida);
	}

	/**
	 * Polígonos convexos do Recast em leque, como [x y z]x3 no mundo do Recast. O A* do NavHelper usa incentro e raio inscrito de
	 * cada triângulo; com os triângulos finos da malha detalhada ele se perde, com polígonos inteiros não.
	 */
	static float[] triangulosPoligonos(PolyMesh pm) {
		if (pm == null || pm.npolys == 0)
			return new float[0];
		FloatList out = new FloatList(pm.npolys * 4 * 9);
		int nvp = pm.nvp;
		for (int p = 0; p < pm.npolys; p++) {
			int base = p * 2 * nvp;
			int n = 0;
			while (n < nvp && pm.polys[base + n] != RecastConstants.RC_MESH_NULL_IDX)
				n++;
			for (int k = 2; k < n; k++) {
				int[] vs = { pm.polys[base], pm.polys[base + k - 1], pm.polys[base + k] };
				for (int vi : vs)
					out.add(pm.bmin[0] + pm.verts[vi * 3] * pm.cs, pm.bmin[1] + pm.verts[vi * 3 + 1] * pm.ch, pm.bmin[2] + pm.verts[vi * 3 + 2] * pm.cs);
			}
		}
		return Arrays.copyOf(out.d, out.n);
	}

	/** Triângulos da malha detalhada como [x y z]x3 do Recast. */
	static float[] trianguloDetalhe(PolyMeshDetail dm) {
		if (dm == null || dm.ntris == 0)
			return new float[0];
		FloatList out = new FloatList(dm.ntris * 9);
		for (int m = 0; m < dm.nmeshes; m++) {
			int vb = dm.meshes[m * 4], tb = dm.meshes[m * 4 + 2], tn = dm.meshes[m * 4 + 3];
			for (int t = 0; t < tn; t++)
				for (int k = 0; k < 3; k++) {
					int vi = (vb + dm.tris[(tb + t) * 4 + k]) * 3;
					out.add(dm.verts[vi], dm.verts[vi + 1], dm.verts[vi + 2]);
				}
		}
		return Arrays.copyOf(out.d, out.n);
	}

	/** Entrada do Recast com um índice espacial só (o SimpleInputGeomProvider recria o índice a cada bloco). */
	static final class Entrada implements org.recast4j.recast.geom.InputGeomProvider {
		final org.recast4j.recast.geom.TriMesh malha;
		final float[] bmin = { Float.MAX_VALUE, Float.MAX_VALUE, Float.MAX_VALUE }, bmax = { -Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE };

		Entrada(float[] v, int[] f, float[] area) {
			malha = new org.recast4j.recast.geom.TriMesh(v, f);
			for (int i = 0; i < v.length; i += 3)
				for (int k = 0; k < 3; k++) {
					bmin[k] = Math.min(bmin[k], v[i + k]);
					bmax[k] = Math.max(bmax[k], v[i + k]);
				}
			if (area != null) {
				bmin[0] = Math.max(bmin[0], area[0]);
				bmin[2] = Math.max(bmin[2], area[1]);
				bmax[0] = Math.min(bmax[0], area[2]);
				bmax[2] = Math.min(bmax[2], area[3]);
			}
		}

		public float[] getMeshBoundsMin() {
			return bmin;
		}

		public float[] getMeshBoundsMax() {
			return bmax;
		}

		public Iterable<org.recast4j.recast.geom.TriMesh> meshes() {
			return List.of(malha);
		}

		public Iterable<ConvexVolume> convexVolumes() {
			return List.of();
		}
	}

	/** Modelos sólidos, já no mundo pela matriz da própria Geometry. */
	static int adicionaModelos(GeoMap geo, FloatList v, IntList f) {
		int[] cont = { 0 };
		Vector3f a = new Vector3f(), b = new Vector3f(), c = new Vector3f();
		geo.getGeometries().forEach(g -> {
			if ((g.getCollisionIntentions() & SOLIDO) == 0)
				return;
			for (Node p = g.getParent(); p != null; p = p.getParent())
				if (p instanceof DespawnableNode d && d.type != DespawnableNode.DespawnableType.NONE)
					return;
			Matrix4f m = g.getWorldMatrix();
			int n = g.getMesh().getTriangleCount();
			for (int t = 0; t < n; t++) {
				g.getMesh().getTriangle(t, a, b, c);
				int base = v.n / 3;
				Vector3f wa = m.mult(a, new Vector3f()), wb = m.mult(b, new Vector3f()), wc = m.mult(c, new Vector3f());
				v.add(wa);
				v.add(wb);
				v.add(wc);
				// a colisão do emulador não olha o lado da face; o Recast só aceita chão com normal para cima.
				// Face quase horizontal virada para baixo é chão modelado do avesso: entra com a normal para cima.
				float nx = (wb.y - wa.y) * (wc.z - wa.z) - (wb.z - wa.z) * (wc.y - wa.y);
				float ny = (wb.z - wa.z) * (wc.x - wa.x) - (wb.x - wa.x) * (wc.z - wa.z);
				float nz = (wb.x - wa.x) * (wc.y - wa.y) - (wb.y - wa.y) * (wc.x - wa.x);
				if (DUPLA_FACE && nz < 0 && -nz >= Math.cos(Math.toRadians(RAMPA_MAX)) * Math.sqrt(nx * nx + ny * ny + nz * nz))
					f.add(base, base + 2, base + 1);
				else
					f.add(base, base + 1, base + 2);
			}
			cont[0]++;
		});
		return cont[0];
	}

	/** Relevo: grade de 2 m do heightmap, mesma divisão em triângulos do Terrain. Buracos (-1) ficam de fora. */
	static int adicionaRelevo(GeoMap geo, FloatList v, IntList f, float[] area) throws Exception {
		Field ft = GeoMap.class.getDeclaredField("terrain");
		ft.setAccessible(true);
		Terrain terreno = (Terrain) ft.get(geo);
		if (terreno == null)
			return 0;
		Field fx = Terrain.class.getDeclaredField("heightmapXSize"), fy = Terrain.class.getDeclaredField("heightmapYSize");
		fx.setAccessible(true);
		fy.setAccessible(true);
		int nx = fx.getInt(terreno), ny = fy.getInt(terreno);
		Method z = Terrain.class.getDeclaredMethod("getZ", int.class, int.class);
		z.setAccessible(true);
		int[][] idx = new int[nx + 1][ny + 1];
		for (int i = 0; i <= nx; i++)
			for (int j = 0; j <= ny; j++) {
				// fora do recorte (com 8 m de folga para a borda dos blocos) o relevo não entra
				if (area != null && (i * 2f < area[0] - 8 || i * 2f > area[2] + 8 || j * 2f < area[1] - 8 || j * 2f > area[3] + 8)) {
					idx[i][j] = -1;
					continue;
				}
				float h = (float) z.invoke(terreno, i, j);
				if (Float.isNaN(h)) {
					idx[i][j] = -1;
					continue;
				}
				idx[i][j] = v.n / 3;
				v.add(i * 2f, j * 2f, h);
			}
		int tris = 0;
		for (int i = 0; i < nx; i++)
			for (int j = 0; j < ny; j++) {
				int p1 = idx[i][j], p2 = idx[i + 1][j], p3 = idx[i][j + 1], p4 = idx[i + 1][j + 1];
				// anti-horário visto de cima (x para a direita, y para cima)
				if (p1 >= 0 && p2 >= 0 && p3 >= 0) {
					f.add(p1, p2, p3);
					tris++;
				}
				if (p2 >= 0 && p4 >= 0 && p3 >= 0) {
					f.add(p2, p4, p3);
					tris++;
				}
			}
		return tris;
	}

	/** Junta a malha detalhada dos blocos, solda vértices, calcula vizinhos e grava o .nav. */
	static void grava(List<float[]> blocos, Path saida) throws IOException {
		FloatList verts = new FloatList();
		Map<Long, List<Integer>> porCelula = new HashMap<>();
		IntList tris = new IntList();
		for (float[] bt : blocos) {
			{
				for (int t = 0; t < bt.length; t += 9) {
					int[] id = new int[3];
					for (int k = 0; k < 3; k++) {
						int vi = t + k * 3;
						// de volta para o Aion: (x, y_recast, z_recast) -> (x, z_recast, y_recast)
						id[k] = solda(bt[vi], bt[vi + 2], bt[vi + 1], verts, porCelula);
					}
					if (id[0] == id[1] || id[1] == id[2] || id[0] == id[2])
						continue;
					// a troca de eixo inverte o sentido: garante normal +Z
					float ax = verts.d[id[0] * 3], ay = verts.d[id[0] * 3 + 1];
					float bx = verts.d[id[1] * 3], by = verts.d[id[1] * 3 + 1];
					float cx = verts.d[id[2] * 3], cy = verts.d[id[2] * 3 + 1];
					float nz = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
					if (Math.abs(nz) < 1e-6f)
						continue; // triângulo vertical/degenerado: o NavGeometry não aceita
					if (nz > 0)
						tris.add(id[0], id[1], id[2]);
					else
						tris.add(id[0], id[2], id[1]);
				}
			}
		}
		int nt = tris.n / 3;
		int[] viz = new int[nt * 3];
		Arrays.fill(viz, -1);
		Map<Long, Integer> aresta = new HashMap<>(nt * 4);
		int ligadas = 0, conflito = 0;
		for (int t = 0; t < nt; t++)
			for (int e = 0; e < 3; e++) {
				int p = tris.d[t * 3 + e], q = tris.d[t * 3 + (e + 1) % 3];
				long k = ((long) Math.min(p, q) << 32) | Math.max(p, q);
				Integer o = aresta.putIfAbsent(k, t * 3 + e);
				if (o != null) {
					if (o >= 0 && viz[o] == -1) {
						viz[o] = t;
						viz[t * 3 + e] = o / 3;
						ligadas++;
						aresta.put(k, -1);
					} else
						conflito++;
				}
			}
		String sementes = System.getProperty("nav.sementes");
		if (sementes != null) {
			int antes = nt;
			int[] r = mantemConectado(verts, tris, viz, sementes);
			nt = r[0];
			System.out.printf("conexão: %d spawns caíram na malha (%d fora); ficam %d de %d triângulos%n", r[1], r[2], nt, antes);
		}
		ByteBuffer bb = ByteBuffer.allocate(4 + verts.n * 4 + 4 + nt * 24).order(ByteOrder.LITTLE_ENDIAN);
		bb.putInt(verts.n);
		for (int i = 0; i < verts.n; i++)
			bb.putFloat(verts.d[i]);
		bb.putInt(nt);
		for (int t = 0; t < nt; t++) {
			bb.putInt(tris.d[t * 3]).putInt(tris.d[t * 3 + 1]).putInt(tris.d[t * 3 + 2]);
			bb.putInt(viz[t * 3]).putInt(viz[t * 3 + 1]).putInt(viz[t * 3 + 2]);
		}
		bb.flip();
		Files.createDirectories(saida.toAbsolutePath().getParent());
		try (FileChannel ch = FileChannel.open(saida, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)) {
			ch.write(bb);
		}
		System.out.printf("nav: %d vértices, %d triângulos, %d arestas ligadas, %d arestas com 3+ triângulos -> %s%n", verts.n / 3, nt, ligadas,
			conflito, saida);
	}

	/**
	 * Fica só a parte da malha ligada a algum spawn (os &lt;spot x y z&gt; dos XMLs em nav.sementes, separados por ';'): ilhas em
	 * telhado, encosta ou montanha que nenhum NPC alcança saem. Compacta vértices e triângulos no lugar e refaz os índices dos
	 * vizinhos. Devolve {triângulos restantes, spawns na malha, spawns fora}.
	 */
	static int[] mantemConectado(FloatList verts, IntList tris, int[] viz, String sementes) throws IOException {
		int nt = tris.n / 3;
		// índice 2D dos triângulos em células de 4 m
		Map<Long, List<Integer>> grade = new HashMap<>();
		for (int t = 0; t < nt; t++) {
			float minx = Float.MAX_VALUE, miny = Float.MAX_VALUE, maxx = -Float.MAX_VALUE, maxy = -Float.MAX_VALUE;
			for (int k = 0; k < 3; k++) {
				int v = tris.d[t * 3 + k] * 3;
				minx = Math.min(minx, verts.d[v]);
				maxx = Math.max(maxx, verts.d[v]);
				miny = Math.min(miny, verts.d[v + 1]);
				maxy = Math.max(maxy, verts.d[v + 1]);
			}
			for (int cx = (int) Math.floor(minx / 4); cx <= (int) Math.floor(maxx / 4); cx++)
				for (int cy = (int) Math.floor(miny / 4); cy <= (int) Math.floor(maxy / 4); cy++)
					grade.computeIfAbsent(((long) cx << 32) | (cy & 0xffffffffL), k -> new ArrayList<>()).add(t);
		}
		boolean[] vivo = new boolean[nt];
		ArrayDeque<Integer> fila = new ArrayDeque<>();
		int dentro = 0, fora = 0;
		java.util.regex.Pattern spot = java.util.regex.Pattern.compile("<spot\\b[^>]*?\\bx=\"([-\\d.]+)\"[^>]*?\\by=\"([-\\d.]+)\"[^>]*?\\bz=\"([-\\d.]+)\"");
		for (String arq : sementes.split(";")) {
			String txt = Files.readString(Path.of(arq)).replaceAll("(?s)<!--.*?-->", "");
			java.util.regex.Matcher m = spot.matcher(txt);
			while (m.find()) {
				float x = Float.parseFloat(m.group(1)), y = Float.parseFloat(m.group(2)), z = Float.parseFloat(m.group(3));
				int melhor = -1;
				float dz = 3.5f;
				List<Integer> l = grade.get(((long) (int) Math.floor(x / 4) << 32) | ((int) Math.floor(y / 4) & 0xffffffffL));
				if (l != null)
					for (int t : l) {
						float h = alturaNoTriangulo(verts, tris, t, x, y);
						if (!Float.isNaN(h) && Math.abs(h - z) < dz) {
							dz = Math.abs(h - z);
							melhor = t;
						}
					}
				if (melhor < 0) {
					fora++;
					continue;
				}
				dentro++;
				if (!vivo[melhor]) {
					vivo[melhor] = true;
					fila.add(melhor);
				}
			}
		}
		while (!fila.isEmpty()) {
			int t = fila.poll();
			for (int e = 0; e < 3; e++) {
				int o = viz[t * 3 + e];
				if (o >= 0 && !vivo[o]) {
					vivo[o] = true;
					fila.add(o);
				}
			}
		}
		// renumera triângulos e vértices que ficam
		int[] novoT = new int[nt];
		Arrays.fill(novoT, -1);
		int n = 0;
		for (int t = 0; t < nt; t++)
			if (vivo[t])
				novoT[t] = n++;
		int[] novoV = new int[verts.n / 3];
		Arrays.fill(novoV, -1);
		int nv = 0;
		float[] vd = new float[verts.n];
		for (int t = 0; t < nt; t++)
			if (vivo[t])
				for (int k = 0; k < 3; k++) {
					int v = tris.d[t * 3 + k];
					if (novoV[v] < 0) {
						novoV[v] = nv;
						System.arraycopy(verts.d, v * 3, vd, nv * 3, 3);
						nv++;
					}
				}
		for (int t = 0; t < nt; t++) {
			int d = novoT[t];
			if (d < 0)
				continue;
			for (int k = 0; k < 3; k++) {
				tris.d[d * 3 + k] = novoV[tris.d[t * 3 + k]];
				int o = viz[t * 3 + k];
				viz[d * 3 + k] = o >= 0 ? novoT[o] : -1;
			}
		}
		tris.n = n * 3;
		verts.d = vd;
		verts.n = nv * 3;
		return new int[] { n, dentro, fora };
	}

	/** Altura do triângulo no ponto x/y, ou NaN se o ponto está fora dele. */
	static float alturaNoTriangulo(FloatList verts, IntList tris, int t, float x, float y) {
		int a = tris.d[t * 3] * 3, b = tris.d[t * 3 + 1] * 3, c = tris.d[t * 3 + 2] * 3;
		float[] d = verts.d;
		float det = (d[b + 1] - d[c + 1]) * (d[a] - d[c]) + (d[c] - d[b]) * (d[a + 1] - d[c + 1]);
		if (Math.abs(det) < 1e-9f)
			return Float.NaN;
		float l1 = ((d[b + 1] - d[c + 1]) * (x - d[c]) + (d[c] - d[b]) * (y - d[c + 1])) / det;
		float l2 = ((d[c + 1] - d[a + 1]) * (x - d[c]) + (d[a] - d[c]) * (y - d[c + 1])) / det;
		float l3 = 1 - l1 - l2;
		if (l1 < -1e-4f || l2 < -1e-4f || l3 < -1e-4f)
			return Float.NaN;
		return l1 * d[a + 2] + l2 * d[b + 2] + l3 * d[c + 2];
	}

	/** Mesmo vértice dos dois lados da borda de um bloco: x/y a 1 cm e altura a até 0,6 m. */
	static int solda(float x, float y, float z, FloatList verts, Map<Long, List<Integer>> porCelula) {
		long k = ((long) Math.round(x * 100) << 32) | (Math.round(y * 100) & 0xffffffffL);
		List<Integer> l = porCelula.computeIfAbsent(k, kk -> new ArrayList<>(1));
		for (int i : l)
			if (Math.abs(verts.d[i * 3 + 2] - z) < 0.6f)
				return i;
		int id = verts.n / 3;
		verts.add(x, y, z);
		l.add(id);
		return id;
	}

	static final class FloatList {
		float[] d;
		int n;

		FloatList() {
			this(1 << 20);
		}

		FloatList(int cap) {
			d = new float[Math.max(16, cap)];
		}

		void add(float... x) {
			if (n + x.length > d.length)
				d = Arrays.copyOf(d, Math.max(d.length * 2, n + x.length));
			System.arraycopy(x, 0, d, n, x.length);
			n += x.length;
		}

		void add(Vector3f p) {
			add(p.x, p.y, p.z);
		}
	}

	static final class IntList {
		int[] d = new int[1 << 20];
		int n;

		void add(int... x) {
			if (n + x.length > d.length)
				d = Arrays.copyOf(d, Math.max(d.length * 2, n + x.length));
			System.arraycopy(x, 0, d, n, x.length);
			n += x.length;
		}
	}
}
