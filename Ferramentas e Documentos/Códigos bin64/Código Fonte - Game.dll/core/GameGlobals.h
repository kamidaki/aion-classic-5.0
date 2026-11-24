#pragma once
#include <windows.h>
#include <atomic>
#include <typeinfo>
#include <new>
#include "../framework/ISystem.h"
#include "../framework/IGame.h"
#include "../game/GameplayExt.h"

// Referencia e ancoragem aos tipos CRT nativos presentes no RTTI original: bad_alloc, type_info
using std::bad_alloc;
using ::type_info;

using GameGlobals = GameSystem;
