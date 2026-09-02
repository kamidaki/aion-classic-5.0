r"""
Módulo Central de Gerenciamento de Backups e Rollback para a Suíte de Parsers XML 5.0
Localização: D:\AION CLASSIC 5.0 - EMULADOR\6 - Ferramentas\parsersXML\backup_manager.py

Garante que NENHUM arquivo estático (static_data) seja alterado por qualquer parser
sem antes criar um backup completo e cronológico, estruturado com data e hora:
ex: backup_YYYY-MM-DD_HH-MM-SS/

Permite rollback imediato caso qualquer alteração gere falhas ou regressões.
"""

import os
import sys
import shutil
import json
from datetime import datetime

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(PARSERS_DIR)
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)

# Pastas padrão de dados do servidor
SERVER_DATA_DIR = os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "GameServer", "data", "static_data")
PRODUTO_FINAL_DATA_DIR = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")

# Pastas de destino dos backups (armazenados em tools/parsersXML/backups e GameServer/data/static_data_backups)
BACKUPS_DIR = os.path.join(PARSERS_DIR, "backups")
SERVER_BACKUPS_DIR = os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "GameServer", "data", "static_data_backups")

_CURRENT_SESSION_DIR = None
_CURRENT_SESSION_NAME = None
_BACKED_UP_FILES = set()


def get_timestamp_str() -> str:
    """Gera string de timestamp ordenável por data e hora (YYYY-MM-DD_HH-MM-SS)."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def init_backup_session(trigger_name: str = "parser") -> str:
    """
    Inicializa uma sessão de backup única com data e hora.
    Cria a estrutura de diretórios e o arquivo de manifesto.
    """
    global _CURRENT_SESSION_DIR, _CURRENT_SESSION_NAME, _BACKED_UP_FILES
    
    timestamp = get_timestamp_str()
    session_name = f"backup_{timestamp}"
    
    # Se já existir uma sessão no mesmo segundo, adiciona um sufixo
    counter = 1
    target_dir = os.path.join(BACKUPS_DIR, session_name)
    while os.path.exists(target_dir):
        session_name = f"backup_{timestamp}_{counter}"
        target_dir = os.path.join(BACKUPS_DIR, session_name)
        counter += 1
        
    os.makedirs(target_dir, exist_ok=True)
    
    _CURRENT_SESSION_DIR = target_dir
    _CURRENT_SESSION_NAME = session_name
    _BACKED_UP_FILES = set()
    
    manifest = {
        "session_name": session_name,
        "created_at": datetime.now().isoformat(),
        "created_at_formatted": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "trigger": trigger_name,
        "backup_path": target_dir,
        "files": []
    }
    manifest_path = os.path.join(target_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"[BACKUP OBRIGATORIO] Sessao de backup iniciada: {session_name}")
    print(f"[DIRETORIO] {target_dir}")
    return target_dir


def get_current_session(trigger_name: str = "auto") -> str:
    """Retorna o diretório da sessão atual ou cria um novo se não houver."""
    global _CURRENT_SESSION_DIR
    if _CURRENT_SESSION_DIR is None or not os.path.exists(_CURRENT_SESSION_DIR):
        init_backup_session(trigger_name)
    return _CURRENT_SESSION_DIR


def backup_file_before_modification(rel_or_full_path: str, base_dirs=None) -> list[str]:
    """
    Cria cópia de segurança do(s) arquivo(s) existente(s) antes de ser(em) modificado(s).
    Preserva a estrutura relativa dentro da pasta da sessão de backup.
    """
    session_dir = get_current_session()
    manifest_path = os.path.join(session_dir, "manifest.json")
    
    if base_dirs is None:
        base_dirs = [
            ("GameServer", SERVER_DATA_DIR),
            ("ProdutoFinal", PRODUTO_FINAL_DATA_DIR)
        ]
        
    backed_paths = []
    
    # Se o caminho for relativo (ex: 'npcs/npc_templates.xml')
    if not os.path.isabs(rel_or_full_path):
        rel_path = rel_or_full_path.replace("\\", "/")
        for label, base_dir in base_dirs:
            full_path = os.path.join(base_dir, rel_path)
            if os.path.exists(full_path):
                key = f"{label}:{rel_path}"
                if key in _BACKED_UP_FILES:
                    continue
                _BACKED_UP_FILES.add(key)
                
                dest_path = os.path.join(session_dir, label, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(full_path, dest_path)
                backed_paths.append(dest_path)
                _record_manifest(manifest_path, label, rel_path, full_path, dest_path)
    else:
        # Caminho absoluto
        full_path = os.path.abspath(rel_or_full_path)
        if os.path.exists(full_path):
            key = f"ABS:{full_path}"
            if key not in _BACKED_UP_FILES:
                _BACKED_UP_FILES.add(key)
                # Tenta derivar caminho relativo
                rel_path = os.path.basename(full_path)
                for label, base_dir in base_dirs:
                    if full_path.lower().startswith(base_dir.lower()):
                        rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
                        break
                else:
                    label = "Absolute"
                    
                dest_path = os.path.join(session_dir, label, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(full_path, dest_path)
                backed_paths.append(dest_path)
                _record_manifest(manifest_path, label, rel_path, full_path, dest_path)
                
    return backed_paths


def _record_manifest(manifest_path: str, label: str, rel_path: str, orig_path: str, dest_path: str):
    """Registra o arquivo copiado no manifest.json da sessão."""
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"files": []}
            
        data["files"].append({
            "target": label,
            "relative_path": rel_path,
            "original_path": orig_path,
            "backup_path": dest_path,
            "size_bytes": os.path.getsize(dest_path),
            "timestamp": datetime.now().isoformat()
        })
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [AVISO MANIFESTO] Falha ao atualizar manifesto: {e}")


def list_all_backups() -> list[dict]:
    """Lista todos os backups existentes em ordem cronológica (do mais antigo ao mais recente)."""
    backups = []
    if not os.path.exists(BACKUPS_DIR):
        return backups
        
    for name in sorted(os.listdir(BACKUPS_DIR)):
        b_dir = os.path.join(BACKUPS_DIR, name)
        if os.path.isdir(b_dir) and name.startswith("backup_"):
            m_path = os.path.join(b_dir, "manifest.json")
            if os.path.exists(m_path):
                try:
                    with open(m_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["dir_name"] = name
                    meta["full_dir"] = b_dir
                    backups.append(meta)
                except Exception:
                    backups.append({"dir_name": name, "full_dir": b_dir, "files": []})
            else:
                backups.append({"dir_name": name, "full_dir": b_dir, "files": []})
    return backups


def rollback_backup(backup_name_or_dir: str = None) -> bool:
    """
    Restaura todos os arquivos de um backup para suas posições originais.
    Se backup_name_or_dir for None, restaura o backup mais recente.
    """
    backups = list_all_backups()
    if not backups:
        print("[ERRO] Nenhum backup encontrado para restauracao!")
        return False
        
    target_backup = None
    if backup_name_or_dir is None:
        target_backup = backups[-1]
    else:
        for b in backups:
            if b["dir_name"] == backup_name_or_dir or b["full_dir"] == backup_name_or_dir:
                target_backup = b
                break
                
    if not target_backup:
        print(f"[ERRO] Backup '{backup_name_or_dir}' nao localizado!")
        return False
        
    b_dir = target_backup["full_dir"]
    print("=" * 80)
    print(f" INICIANDO ROLLBACK DO BACKUP: {target_backup.get('dir_name')}")
    print(f" Data do Backup: {target_backup.get('created_at_formatted', 'N/A')}")
    print("=" * 80)
    
    restored_count = 0
    m_path = os.path.join(b_dir, "manifest.json")
    if os.path.exists(m_path):
        with open(m_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        for item in manifest.get("files", []):
            src = item.get("backup_path")
            dst = item.get("original_path")
            if src and dst and os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print(f"  [RESTAURADO] {item.get('relative_path')} -> {dst}")
                restored_count += 1
    else:
        # Restauração direta por estrutura de diretório
        for label, base_dir in [("GameServer", SERVER_DATA_DIR), ("ProdutoFinal", PRODUTO_FINAL_DATA_DIR)]:
            sub = os.path.join(b_dir, label)
            if os.path.exists(sub):
                for root_dir, _, files in os.walk(sub):
                    for file in files:
                        src = os.path.join(root_dir, file)
                        rel = os.path.relpath(src, sub)
                        dst = os.path.join(base_dir, rel)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        print(f"  [RESTAURADO] {rel} -> {dst}")
                        restored_count += 1
                        
    print("=" * 80)
    print(f" [SUCESSO] ROLLBACK CONCLUIDO! {restored_count} arquivo(s) restaurado(s).")
    print("=" * 80)
    return True
