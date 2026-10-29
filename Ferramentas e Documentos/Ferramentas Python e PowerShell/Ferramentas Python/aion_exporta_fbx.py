"""
Exportador em lote do cliente Aion para FBX (Unreal), sempre a 30 quadros por segundo.

Roda dentro do Blender, sem interface, usando os plugins de
"Ferramentas e Documentos/Blender - Aion Plugins". Nada é gravado no cliente.

Uso (tudo depois do "--" é deste script):

  blender.exe -b --factory-startup --python aion_exporta_fbx.py -- --out D:\\saida [opções]

  --client DIR          raiz do cliente (padrão G:\\GFAion\\aionclassic)
  --out DIR             pasta de saída (obrigatória, fora do cliente)
  --modelo CAMINHO      .cgf relativo ao cliente; pode repetir
  --lista ARQUIVO       texto com um .cgf por linha (# comenta)
  --pc RAÇA:CLASSE      personagem jogável montado, ex. LM:GLADIATOR; pode repetir
  --nivel NOME          pasta de levels/, ex. lf1; pode repetir (não combina com modelo/pc)
  --anims A,B           só animações cujo nome contém algum dos trechos
  --max-anims N         limite de animações por modelo (0 = sem limite)
  --sem-anims           exporta só malha e esqueleto
  --anim-separada       um FBX por animação (só esqueleto), além do FBX da malha
  --glb                 grava também um .glb ao lado de cada FBX de malha
  --conferir            reimporta o que exportou e compara ossos e duração

O CAF guarda 160 ticks por quadro em 4800 ticks por segundo, ou seja, 30 fps.
A cena do Blender abre em 24; exportar assim deixa toda animação 25% mais lenta.

Saída: <out>/modelos/<nome>/, <out>/pc/<raça>_<classe>/, <out>/niveis/<nome>/ e
<out>/manifesto.json com ossos, triângulos e duração de cada animação.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

import addon_utils
import bpy

FPS = 30
PLUGINS = Path(__file__).resolve().parents[2] / "Blender - Aion Plugins"
PLUGIN_MODELOS = "importador-modelos3d-lostacademy"
PLUGIN_MAPAS = "importador-mapas-lostacademy"


def P(*a):
    print(*a, flush=True)


def le_args():
    ap = argparse.ArgumentParser(prog="aion_exporta_fbx.py")
    ap.add_argument("--client", default=r"G:\GFAion\aionclassic")
    ap.add_argument("--out", required=True)
    ap.add_argument("--modelo", action="append", default=[])
    ap.add_argument("--lista")
    ap.add_argument("--pc", action="append", default=[])
    ap.add_argument("--nivel", action="append", default=[])
    ap.add_argument("--anims", default="")
    ap.add_argument("--max-anims", type=int, default=0)
    ap.add_argument("--sem-anims", action="store_true")
    ap.add_argument("--anim-separada", action="store_true")
    ap.add_argument("--glb", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if a.lista:
        for linha in Path(a.lista).read_text(encoding="utf-8").splitlines():
            linha = linha.split("#")[0].strip()
            if linha:
                a.modelo.append(linha)
    a.client, a.out = Path(a.client).resolve(), Path(a.out).resolve()
    a.filtros = [f.strip().lower() for f in a.anims.split(",") if f.strip()]
    if a.nivel and (a.modelo or a.pc):
        ap.error("--nivel não combina com --modelo/--pc; rode em duas chamadas")
    if not (a.nivel or a.modelo or a.pc):
        ap.error("nada a exportar: informe --modelo, --lista, --pc ou --nivel")
    if a.client == a.out or a.client in a.out.parents:
        ap.error("--out não pode ficar dentro do cliente")
    return a


def fixa_fps():
    r = bpy.context.scene.render
    r.fps, r.fps_base = FPS, 1.0


def limpa_cena(plugin: str | None = PLUGIN_MODELOS):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if plugin:
        addon_utils.enable(plugin, default_set=False)
    fixa_fps()


def conta_cena() -> dict:
    malhas = [o for o in bpy.data.objects if o.type == "MESH"]
    rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    return {
        "malhas": len(malhas),
        "vertices": sum(len(o.data.vertices) for o in malhas),
        "triangulos": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in malhas),
        "ossos": sum(len(r.data.bones) for r in rigs),
    }


def valida_malhas() -> int:
    """Remove faces degeneradas/duplicadas que o FBX e o glTF rejeitam. Devolve quantas malhas mudaram."""
    return sum(1 for m in bpy.data.meshes if m.validate(verbose=False))


def prende_por_peso(rig) -> list[str]:
    """
    Arma, escudo e afins entram como objeto filho de osso. A Unreal não mantém esse vínculo numa
    malha com esqueleto, então cada um vira malha com peso 1 no próprio osso. Chamar em repouso.
    """
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    feitos = []
    for obj in list(rig.children):
        if obj.type != "MESH" or obj.parent_type != "BONE" or obj.parent_bone not in rig.data.bones:
            continue
        osso, mundo = obj.parent_bone, obj.matrix_world.copy()
        obj.parent_type = "OBJECT"
        obj.matrix_parent_inverse = rig.matrix_world.inverted()
        obj.matrix_world = mundo
        for g in list(obj.vertex_groups):
            obj.vertex_groups.remove(g)
        obj.vertex_groups.new(name=osso).add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        feitos.append(f"{obj.name}@{osso}")
    return feitos


def ativa_acao(rig, acao):
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = acao
    slots = getattr(acao, "slots", None)  # Blender 4.4+
    if slots and hasattr(rig.animation_data, "action_slot"):
        try:
            rig.animation_data.action_slot = slots[0]
        except Exception:
            pass
    if acao:
        cena = bpy.context.scene
        cena.frame_start, cena.frame_end = int(acao.frame_range[0]), int(acao.frame_range[1])
        cena.frame_set(cena.frame_start)


def exporta_fbx(destino: Path, malha: bool, anim: str):
    """anim: 'nao', 'todas' (todas as ações da cena) ou 'ativa' (só a ação ligada ao esqueleto)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(destino),
        use_selection=False,
        object_types={"ARMATURE", "MESH", "EMPTY"} if malha else {"ARMATURE"},
        add_leaf_bones=False,
        mesh_smooth_type="FACE",
        bake_anim=anim != "nao",
        bake_anim_use_all_actions=anim == "todas",
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_bones=True,
        bake_anim_simplify_factor=0.0,
        path_mode="COPY" if malha else "AUTO",
        embed_textures=malha,
    )


def exporta_glb(destino: Path):
    try:
        bpy.ops.export_scene.gltf(filepath=str(destino), export_format="GLB", export_animations=True)
    except Exception as e:
        P(f"    GLB falhou: {e!r}")


# ----------------------------------------------------------------------------
# Modelos e personagens
# ----------------------------------------------------------------------------

class Modelos:
    def __init__(self, a):
        self.a = a
        sys.path.insert(0, str(PLUGINS))
        addon_utils.enable(PLUGIN_MODELOS, default_set=False)
        mod = importlib.import_module(PLUGIN_MODELOS)
        self.mod = mod
        self.cp = mod.core.client_provider.AionClientProvider(a.client)
        self.mp = mod.providers.model_provider.ModelProvider(self.cp)
        self.AssetEntry = mod.indexer.asset_entry.AssetEntry
        self.Manequim = mod.providers.mannequin_provider.MannequinProvider
        self._cafs_pc: dict[str, list[str]] = {}

    def _passa(self, nome: str) -> bool:
        return not self.a.filtros or any(f in nome.lower() for f in self.a.filtros)

    def _corta(self, itens: list) -> list:
        return itens[: self.a.max_anims] if self.a.max_anims > 0 else itens

    def anims_do_cal(self, caminho: str) -> list[tuple[str, str]]:
        cal, _ = self.cp.resolve_animation_asset(caminho)
        return self._corta([(k, v) for k, v in (cal or {}).items() if self._passa(k)])

    def anims_do_pc(self, raca: str, classe: str) -> list[tuple[str, str]]:
        """Sem filtro: o conjunto básico da classe. Com filtro: busca nos PAKs de animação da raça."""
        if not self.a.filtros:
            return self._corta([(Path(caf).stem, caf) for _r, caf in self.Manequim.get_class_animations(raca, classe)])
        rg = raca.lower()
        if rg not in self._cafs_pc:
            nomes = set()
            for pak in sorted((self.a.client / "objects" / "pc" / rg / "animation").glob("*.pak")):
                nomes.update(n for n in self.cp.catalog.get_archive(pak).namelist() if n.lower().endswith(".caf"))
            self._cafs_pc[rg] = sorted(nomes)
        return self._corta([(Path(n).stem, n) for n in self._cafs_pc[rg] if self._passa(Path(n).stem)])

    def bytes_caf(self, caf: str, origem: str) -> bytes | None:
        d = self.cp.find_caf_bytes(caf, source_model_path=origem) if origem else None
        if not d:
            self.cp.ensure_category_paks_indexed(caf)
            d = self.cp.catalog.extract_file(caf) or self.cp.catalog.extract_file(Path(caf).name)
        return d

    def exporta(self, nome: str, pasta: Path, carrega, anims, origem: str) -> dict:
        """carrega() devolve o objeto raiz; anims(rig) devolve [(nome, caf)]."""
        limpa_cena()
        raiz = carrega()
        if raiz is None:
            raise RuntimeError("modelo não encontrado no cliente")
        for ac in list(bpy.data.actions):  # o manequim já traz um idle; as animações entram abaixo, pelo nome
            bpy.data.actions.remove(ac)
        rig = raiz if raiz.type == "ARMATURE" else None
        presos = prende_por_peso(rig) if rig else []
        reg = {"nome": nome, "origem": origem, "fps": FPS, "malhas_corrigidas": valida_malhas(), **conta_cena(),
               "presos_ao_osso": presos, "animacoes": []}
        fbx = pasta / f"{nome}.fbx"
        lista = [] if (self.a.sem_anims or rig is None) else anims(rig)
        separada = self.a.anim_separada or not lista

        if separada:  # malha em pose de repouso, antes de qualquer ação
            exporta_fbx(fbx, malha=True, anim="nao")
            if self.a.glb:
                exporta_glb(fbx.with_suffix(".glb"))

        if lista:
            b_nomes, _pos, b_anim = self.mp.skel_prov.extract_armature(rig)
            for chave, caf in lista:
                try:
                    dados = self.bytes_caf(caf, origem)
                    acao = dados and self.mp.anim_prov.load_animation(
                        rig_obj=rig, caf_bytes=dados, action_name=chave, bone_names=b_nomes, bone_anim=b_anim)
                    if not acao:
                        reg["animacoes"].append({"nome": chave, "caf": caf, "erro": "CAF ausente ou ilegível"})
                        continue
                    quadros = int(acao.frame_range[1] - acao.frame_range[0])
                    item = {"nome": chave, "caf": caf, "quadros": quadros, "segundos": round(quadros / FPS, 4)}
                    if separada:
                        ativa_acao(rig, acao)
                        arq = pasta / "anims" / f"{chave}.fbx"
                        exporta_fbx(arq, malha=False, anim="ativa")
                        item["arquivo"] = str(arq.relative_to(self.a.out)).replace("\\", "/")
                        ativa_acao(rig, None)
                        bpy.data.actions.remove(acao)
                    reg["animacoes"].append(item)
                except Exception as e:
                    reg["animacoes"].append({"nome": chave, "caf": caf, "erro": repr(e)[:200]})

        if not separada:
            exporta_fbx(fbx, malha=True, anim="todas")
            if self.a.glb:
                exporta_glb(fbx.with_suffix(".glb"))

        reg["arquivo"] = str(fbx.relative_to(self.a.out)).replace("\\", "/")
        if self.a.conferir:
            reg["conferencia"] = self.confere(fbx, pasta, reg, separada)
        return reg

    def confere(self, fbx: Path, pasta: Path, reg: dict, separada: bool) -> dict:
        """Reimporta numa cena nova (24 fps). O importador ajusta a cena pela taxa gravada no FBX, que tem de ser 30."""
        def fps_cena():
            r = bpy.context.scene.render
            return r.fps / r.fps_base

        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(fbx))
        c = conta_cena()
        r = {"ossos_ok": c["ossos"] == reg["ossos"], "triangulos_ok": c["triangulos"] == reg["triangulos"]}
        boas = [x for x in reg["animacoes"] if "erro" not in x]
        if boas:
            alvo = boas[0]
            if separada:
                bpy.ops.wm.read_factory_settings(use_empty=True)
                bpy.ops.import_scene.fbx(filepath=str(self.a.out / alvo["arquivo"]))
                acoes = list(bpy.data.actions)
            else:
                acoes = [x for x in bpy.data.actions if x.name.endswith(alvo["nome"])]
            if acoes:
                fps = fps_cena()
                seg = (acoes[0].frame_range[1] - acoes[0].frame_range[0]) / fps
                r["duracao_conferida"] = alvo["nome"]
                r["fps_no_fbx"] = round(fps, 3)
                r["segundos_no_fbx"] = round(seg, 4)
                r["duracao_ok"] = abs(fps - FPS) < 0.01 and abs(seg - alvo["segundos"]) <= 1.5 / FPS
            else:
                r["duracao_ok"] = False
        return r

    def roda(self) -> list[dict]:
        tarefas = []
        for caminho in self.a.modelo:
            caminho = caminho.replace("\\", "/").strip().lstrip("/")
            nome = Path(caminho).stem
            tarefas.append((nome, self.a.out / "modelos" / nome, caminho,
                            lambda c=caminho, n=nome: self.mp.load_model(
                                self.AssetEntry(asset_id=n, name=n, category="", model_path=c),
                                target_collection=bpy.context.scene.collection, load_animation=False),
                            lambda rig, c=caminho: self.anims_do_cal(c)))
        for spec in self.a.pc:
            raca, _, classe = spec.upper().partition(":")
            classe = classe or "GLADIATOR"
            nome = f"{raca.lower()}_{classe.lower()}"
            tarefas.append((nome, self.a.out / "pc" / nome, "",
                            lambda r=raca, cl=classe: self.Manequim.assemble_class_character(
                                self.cp, self.mp, r, cl, bpy.context.scene.collection),
                            lambda rig, r=raca, cl=classe: self.anims_do_pc(r, cl)))
        saida = []
        for i, (nome, pasta, origem, carrega, anims) in enumerate(tarefas, 1):
            t0 = time.time()
            try:
                reg = self.exporta(nome, pasta, carrega, anims, origem)
                ok = [x for x in reg["animacoes"] if "erro" not in x]
                P(f"[{i}/{len(tarefas)}] {nome}: {reg['triangulos']} tris, {reg['ossos']} ossos, "
                  f"{len(ok)}/{len(reg['animacoes'])} animações, {time.time() - t0:.1f}s"
                  + (f", conferência {reg['conferencia']}" if "conferencia" in reg else ""))
            except Exception as e:
                reg = {"nome": nome, "origem": origem, "erro": repr(e)[:300]}
                P(f"[{i}/{len(tarefas)}] {nome}: ERRO {e!r}")
                traceback.print_exc()
            saida.append(reg)
        return saida


# ----------------------------------------------------------------------------
# Níveis
# ----------------------------------------------------------------------------

def roda_niveis(a) -> list[dict]:
    raiz = PLUGINS / PLUGIN_MAPAS
    sys.path.insert(0, str(raiz / "_vendor"))
    sys.path.insert(0, str(raiz))
    trabalho = a.out / "_trabalho"
    cache = trabalho / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    limpa_cena(None)
    import core.pak_engine as pe
    # O plugin extrai para <cliente>/.aion_cache e <nível>/.aion_cache; aqui tudo vai para a pasta de saída.
    pe.AionClientPakResolver._init_cache_dir = lambda self: cache
    from importers.level_importer import import_level

    saida = []
    for i, nome in enumerate(a.nivel, 1):
        t0 = time.time()
        try:
            origem = next((d for d in (a.client / "levels").iterdir() if d.is_dir() and d.name.lower() == nome.lower()), None)
            if origem is None:
                raise RuntimeError("nível não existe em levels/")
            copia = trabalho / "levels" / origem.name
            if not copia.is_dir():
                shutil.copytree(origem, copia)
            limpa_cena(None)
            res = import_level(
                context=bpy.context, level_dir=copia, client_root=a.client, limited_preview=False,
                import_terrain=True, import_terrain_textures=True, import_buildings=True, import_structures=True,
                import_props=True, import_rocks=True, import_vegetation=True, import_trees=True, import_grass=False,
                import_water=True, import_collision=False, import_npcs=False, import_cga_entities=True,
                import_lod0=True, import_lod1=False, import_lod2=False, import_lod3=False, terrain_lod=2)
            fixa_fps()
            s = res.summary
            fbx = a.out / "niveis" / origem.name / f"{origem.name}.fbx"
            reg = {"nome": origem.name, "fps": FPS, "malhas_corrigidas": valida_malhas(), **conta_cena(),
                   "objetos": len(bpy.data.objects), "cgf_total": s.cgf_total, "cgf_importados": s.cgf_imported,
                   "cgf_falhos": s.cgf_failed, "terreno_vertices": s.terrain_vertices}
            exporta_fbx(fbx, malha=True, anim="nao")
            reg["arquivo"] = str(fbx.relative_to(a.out)).replace("\\", "/")
            reg["mb"] = round(fbx.stat().st_size / 1048576, 1)
            P(f"[{i}/{len(a.nivel)}] nível {origem.name}: {reg['cgf_importados']}/{reg['cgf_total']} modelos, "
              f"{reg['objetos']} objetos, {reg['mb']} MB, {time.time() - t0:.1f}s")
        except Exception as e:
            reg = {"nome": nome, "erro": repr(e)[:300]}
            P(f"[{i}/{len(a.nivel)}] nível {nome}: ERRO {e!r}")
            traceback.print_exc()
        saida.append(reg)
    return saida


def main():
    a = le_args()
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    P(f"cliente={a.client}\nsaida={a.out}\nfps={FPS}")
    chave = "niveis" if a.nivel else "modelos"
    feitos = roda_niveis(a) if a.nivel else Modelos(a).roda()

    manifesto = a.out / "manifesto.json"
    dados = json.loads(manifesto.read_text(encoding="utf-8")) if manifesto.is_file() else {}
    dados["fps"] = FPS
    atual = {x["nome"]: x for x in dados.get(chave, [])}
    atual.update({x["nome"]: x for x in feitos})
    dados[chave] = sorted(atual.values(), key=lambda x: x["nome"])
    manifesto.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    erros = [x["nome"] for x in feitos if "erro" in x]
    P(f"\n{len(feitos) - len(erros)}/{len(feitos)} exportados em {time.time() - t0:.1f}s; manifesto em {manifesto}")
    if erros:
        P("com erro:", ", ".join(erros))
        sys.exit(1)


if __name__ == "__main__":
    main()
