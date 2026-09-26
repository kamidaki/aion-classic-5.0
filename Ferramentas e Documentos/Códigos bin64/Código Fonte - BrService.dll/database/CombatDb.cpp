#include "CombatDb.h"
#include "sqlite3.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <mutex>
#include <deque>
#include <chrono>

namespace BrService {

static sqlite3* s_db = nullptr;
static std::mutex s_queueMutex;
static std::deque<StoredCombatEvent> s_eventQueue;
static HANDLE s_hWorkerThread = nullptr;
static HANDLE s_hWakeEvent = nullptr;
static bool s_running = false;

static std::string GetDbPath() {
    char path[MAX_PATH] = { 0 };
    GetModuleFileNameA(nullptr, path, MAX_PATH);
    char* lastSlash = strrchr(path, '\\');
    if (lastSlash) {
        strcpy_s(lastSlash + 1, MAX_PATH - (lastSlash - path + 1), "br_dps_history.db");
    } else {
        strcpy_s(path, MAX_PATH, "br_dps_history.db");
    }
    return std::string(path);
}

bool CombatDb::Initialize() {
    std::string dbPath = GetDbPath();
    int rc = sqlite3_open(dbPath.c_str(), &s_db);
    if (rc != SQLITE_OK) {
        LogError("Falha ao abrir SQLite em %s: %s", dbPath.c_str(), sqlite3_errmsg(s_db));
        return false;
    }

    // High performance PRAGMAs for fast async writes without locks
    sqlite3_exec(s_db, "PRAGMA journal_mode = WAL;", nullptr, nullptr, nullptr);
    sqlite3_exec(s_db, "PRAGMA synchronous = NORMAL;", nullptr, nullptr, nullptr);

    const char* schema =
        "CREATE TABLE IF NOT EXISTS combat_events ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  timestamp INTEGER NOT NULL,"
        "  attacker TEXT,"
        "  target TEXT,"
        "  skill_id INTEGER,"
        "  skill_name TEXT,"
        "  damage INTEGER,"
        "  is_crit INTEGER,"
        "  is_heal INTEGER"
        ");"
        "CREATE INDEX IF NOT EXISTS idx_combat_ts ON combat_events(timestamp);"
        "CREATE INDEX IF NOT EXISTS idx_combat_attacker ON combat_events(attacker);";

    char* errMsg = nullptr;
    rc = sqlite3_exec(s_db, schema, nullptr, nullptr, &errMsg);
    if (rc != SQLITE_OK) {
        LogError("Falha ao criar schema SQLite: %s", errMsg ? errMsg : "desconhecido");
        if (errMsg) sqlite3_free(errMsg);
    }

    // Purge records older than 24h on startup
    PurgeOldRecords(24);

    s_running = true;
    s_hWakeEvent = CreateEventA(nullptr, FALSE, FALSE, nullptr);
    s_hWorkerThread = CreateThread(nullptr, 0, WorkerThread, nullptr, 0, nullptr);

    LogInfo("CombatDb (SQLite3 WAL) inicializado com sucesso em %s", dbPath.c_str());
    return true;
}

void CombatDb::Shutdown() {
    s_running = false;
    if (s_hWakeEvent) {
        SetEvent(s_hWakeEvent);
    }
    if (s_hWorkerThread) {
        WaitForSingleObject(s_hWorkerThread, 2000);
        CloseHandle(s_hWorkerThread);
        s_hWorkerThread = nullptr;
    }
    if (s_hWakeEvent) {
        CloseHandle(s_hWakeEvent);
        s_hWakeEvent = nullptr;
    }
    if (s_db) {
        sqlite3_close(s_db);
        s_db = nullptr;
    }
}

void CombatDb::RecordEventAsync(const StoredCombatEvent& ev) {
    if (!s_running) return;
    {
        std::lock_guard<std::mutex> lock(s_queueMutex);
        if (s_eventQueue.size() >= 5000) {
            s_eventQueue.pop_front();
        }
        s_eventQueue.push_back(ev);
    }
    if (s_hWakeEvent) {
        SetEvent(s_hWakeEvent);
    }
}

void CombatDb::PurgeOldRecords(int maxAgeHours) {
    if (!s_db) return;

    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    uint64_t cutoff = ms - (static_cast<uint64_t>(maxAgeHours) * 3600ULL * 1000ULL);

    char sql[128];
    snprintf(sql, sizeof(sql), "DELETE FROM combat_events WHERE timestamp < %llu;", cutoff);

    char* err = nullptr;
    sqlite3_exec(s_db, sql, nullptr, nullptr, &err);
    if (err) {
        LogError("Erro ao purgar historico de 24h: %s", err);
        sqlite3_free(err);
    } else {
        LogInfo("Historico antigo (> 24h) purgado do banco SQLite com sucesso.");
    }
}

DWORD WINAPI CombatDb::WorkerThread(LPVOID /*param*/) {
    sqlite3_stmt* stmt = nullptr;
    const char* insertSql =
        "INSERT INTO combat_events (timestamp, attacker, target, skill_id, skill_name, damage, is_crit, is_heal) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?);";

    sqlite3_prepare_v2(s_db, insertSql, -1, &stmt, nullptr);

    while (s_running) {
        WaitForSingleObject(s_hWakeEvent, INFINITE);
        if (!s_running) break;

        std::deque<StoredCombatEvent> batch;
        {
            std::lock_guard<std::mutex> lock(s_queueMutex);
            batch.swap(s_eventQueue);
        }

        if (!batch.empty() && stmt) {
            sqlite3_exec(s_db, "BEGIN TRANSACTION;", nullptr, nullptr, nullptr);

            for (const auto& ev : batch) {
                sqlite3_reset(stmt);
                sqlite3_bind_int64(stmt, 1, static_cast<sqlite3_int64>(ev.timestamp));
                sqlite3_bind_text(stmt, 2, ev.attacker.c_str(), -1, SQLITE_TRANSIENT);
                sqlite3_bind_text(stmt, 3, ev.target.c_str(), -1, SQLITE_TRANSIENT);
                sqlite3_bind_int(stmt, 4, static_cast<int>(ev.skillId));
                sqlite3_bind_text(stmt, 5, ev.skillName.c_str(), -1, SQLITE_TRANSIENT);
                sqlite3_bind_int(stmt, 6, static_cast<int>(ev.damage));
                sqlite3_bind_int(stmt, 7, ev.isCrit ? 1 : 0);
                sqlite3_bind_int(stmt, 8, ev.isHeal ? 1 : 0);
                sqlite3_step(stmt);
            }

            sqlite3_exec(s_db, "COMMIT;", nullptr, nullptr, nullptr);
        }
    }

    if (stmt) {
        sqlite3_finalize(stmt);
    }
    return 0;
}

} // namespace BrService
