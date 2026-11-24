import os
import glob

script = """
Synchronize canonical bulletproof CryMemoryManager.h across all 10 projects.
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIRS = [
    os.path.join(BASE_DIR, r"Código Fonte - Crysystem.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryInput.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryFont.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CrySoundSystem.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryScriptSystem.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryEntitySystem.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryPhysics.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryMovie.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - CryAnimation.dll\CryCommon"),
    os.path.join(BASE_DIR, r"Código Fonte - Cry3DEngine.dll\CryCommon"),
]

def patch_memory_manager(file_path):
    if not os.path.exists(file_path):
        return False
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Look for the helper constructor
    old_target = """#if defined(WIN32)
		if (pHandle)
			hSystem = (HMODULE)pHandle;
		else
			hSystem = LoadLibrary("CrySystem.dll"); 
#endif"""

    new_replacement = """#if defined(WIN32) || defined(WIN64) || defined(_WIN64)
		bool bLoaded = false;
		if (pHandle)
			hSystem = (HMODULE)pHandle;
		else
		{
			hSystem = GetModuleHandleA("CrySystem.dll");
			if (!hSystem)
			{
				hSystem = LoadLibraryA("CrySystem.dll");
				if (hSystem) bLoaded = true;
			}
		}
#endif"""

    old_cleanup = """#else
		if(!hSystem || !_CryMalloc || !_CryRealloc || !_CryReallocSize || !_CryFree || !_CryFreeSize)
		{
			MessageBox(NULL, "Could not access CrySystem.dll (check working directory)", "Memory Manager", MB_OK);
			if (hSystem)
				::FreeLibrary( hSystem );
			exit(1);
		};
		if (hSystem)
			::FreeLibrary( hSystem );
#endif"""

    new_cleanup = """#else
		if (bLoaded && hSystem)
			::FreeLibrary( hSystem );
#endif"""

    modified = False
    if old_target in content:
        content = content.replace(old_target, new_replacement)
        modified = True
    elif 'hSystem = GetModuleHandleA("CrySystem.dll");' not in content:
        # try more flexible replacement
        idx1 = content.find("explicit _CryMemoryManagerPoolHelper")
        if idx1 != -1:
            idx2 = content.find("#if defined(WIN32)", idx1)
            idx3 = content.find("#endif", idx2)
            if idx2 != -1 and idx3 != -1:
                content = content[:idx2] + new_replacement + content[idx3+6:]
                modified = True

    if old_cleanup in content:
        content = content.replace(old_cleanup, new_cleanup)
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched: {file_path}")
        return True
    else:
        print(f"Already patched or target not matched: {file_path}")
        return False

count = 0
for d in TARGET_DIRS:
    p = os.path.join(d, "CryMemoryManager.h")
    if patch_memory_manager(p):
        count += 1

print(f"Total files updated: {count}")
