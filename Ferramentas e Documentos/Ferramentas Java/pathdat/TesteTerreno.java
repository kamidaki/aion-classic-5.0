import java.awt.image.DataBufferUShort;
import java.io.File;
import java.util.Random;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import com.aionemu.gameserver.geoEngine.models.Terrain;

/** Confere Terrain.getHeight (servidor) contra o cálculo do TesteVoltas e roda as voltas com o terreno do servidor. */
public class TesteTerreno {
	public static void main(String[] a) throws Exception {
		String data = a[0];
		for (int mapa : new int[] { 220010000, 220040000 }) {
			File png = new File(data + "/geo/" + mapa + ".png");
			BufferedImage im = ImageIO.read(png);
			Terrain t = new Terrain();
			t.setHeightmap(((DataBufferUShort) im.getRaster().getDataBuffer()).getData(), im.getWidth(), im.getHeight());
			var ref = TesteVoltas.terreno(png.toPath());
			Random r = new Random(1);
			double max = 0;
			int nan = 0;
			for (int k = 0; k < 200000; k++) {
				float x = 2 + r.nextFloat() * 3060, y = 2 + r.nextFloat() * 3060;
				float z1 = t.getHeight(x, y), z2 = ref.z(x, y);
				if (Float.isNaN(z1) != Float.isNaN(z2)) nan++;
				else if (!Float.isNaN(z1)) max = Math.max(max, Math.abs(z1 - z2));
			}
			System.out.printf("%d: diferença máxima %.5f m, NaN divergente %d de 200000%n", mapa, max, nan);
		}
	}
}
