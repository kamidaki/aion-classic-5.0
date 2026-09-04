package com.aionemu.loginserver.taskmanager;


import com.aionemu.loginserver.model.Account;
import com.aionemu.loginserver.model.AccountSielEnergy;
import javolution.util.FastMap;

import java.util.Iterator;
import java.util.Map;


public class ExpireTimerTask extends AbstractPeriodicTaskManager {
    private FastMap<AccountSielEnergy, Account> expirables = new FastMap<>(2000);

    public ExpireTimerTask() {
        super(200);
    }

    public static ExpireTimerTask getInstance() {
        return SingletonHolder._instance;
    }

    public void addTask(AccountSielEnergy expirable, Account account) {
        writeLock();
        try {
            expirables.put(expirable, account);
        } finally {
            writeUnlock();
        }
    }

    public void removeAccount(Account account) {
        writeLock();
        try {
            for (Map.Entry<AccountSielEnergy, Account> entry : expirables.entrySet()) {
                if (entry.getValue() == account)
                    expirables.remove(entry.getKey());
            }
        } finally {
            writeUnlock();
        }
    }

    @Override
    public void run() {
        writeLock();
        try {
            long timeNow = System.currentTimeMillis();
            for (Iterator<Map.Entry<AccountSielEnergy, Account>> i = expirables.entrySet().iterator(); i.hasNext(); ) {
                Map.Entry<AccountSielEnergy, Account> entry = i.next();
                AccountSielEnergy expirable = entry.getKey();
                expirable.onBeat(timeNow,entry.getValue());
            }
        } finally {
            writeUnlock();
        }
    }

    @SuppressWarnings("synthetic-access")
    private static class SingletonHolder {
        protected static final ExpireTimerTask _instance = new ExpireTimerTask();
    }
}