# Blender — Plugins do Aion Classic 5.0

Plugins oficiais do projeto **[Aion Classic 5.0 — Lost Academy Group](https://github.com/kamidaki/aion-classic-5.0/)** para visualização, inspeção e edição de mapas e modelos 3D do Aion diretamente no **Blender 4.0 a 5.2+ LTS** (100% Python nativo, sem dependências externas).

---

## Plugins Disponíveis

| Plugin | Pacote Instalável (`.zip`) | Documentação | Finalidade |
| :--- | :--- | :--- | :--- |
| **Importador e Editor de Mapas** (`importador-mapas-lostacademy`) | [`importador-mapas-lostacademy.zip`](./importador-mapas-lostacademy.zip) | [`README.md`](./importador-mapas-lostacademy/README.md) · [`CONTEXT.md`](./importador-mapas-lostacademy/CONTEXT.md) | Importa mapas completos (`Level.pak`), terreno (`land_map.h32`), luzes, água, colisões, NPCs e permite edição visual com salvamento direto no `Level.pak`. |
| **Importador de Modelos 3D** (`importador-modelos3d-lostacademy`) | [`importador-modelos3d-lostacademy.zip`](./importador-modelos3d-lostacademy.zip) | [`README.md`](./importador-modelos3d-lostacademy/README.md) · [`CONTEXT.md`](./importador-modelos3d-lostacademy/CONTEXT.md) | Biblioteca visual de ativos, visualizador 3D, player de animações `.cal`/`.caf`, editor de CGF/esqueletos/UVs/materiais e exportação segura com backups `.bak`/`.pak.bak`. |

---

## Instalação Rápida no Blender

1. No Blender (**4.0 a 5.2+ LTS**), abra **Editar (Edit)** > **Preferências (Preferences)** > **Extensões / Add-ons**.
2. No menu de opções (canto superior direito), selecione **Instalar a partir do disco... (Install from Disk...)**.
3. Escolha o `.zip` desejado:
   - [`importador-mapas-lostacademy.zip`](./importador-mapas-lostacademy.zip)
   - [`importador-modelos3d-lostacademy.zip`](./importador-modelos3d-lostacademy.zip)
4. Ative a caixa de seleção do add-on recém-instalado e abra o painel lateral (`N`) na Viewport 3D.

> [!NOTE]
> A geração dos arquivos de **Geodata (`.geo` / `.mesh` / `.png`)** e **NavMesh (`.nav`)** para o emulador **não depende do Blender** — utilize a ferramenta nativa Java/Recast4j documentada em [`../Geo and Nav Builder - Official Client/README.md`](../Geo%20and%20Nav%20Builder%20-%20Official%20Client/README.md).
