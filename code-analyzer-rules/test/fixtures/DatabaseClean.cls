public without sharing class DatabaseClean implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account WITH SYSTEM_MODE]);
    }
    public void execute(Database.BatchableContext bc, List<Account> accounts) {
        Database.update(accounts, false, AccessLevel.SYSTEM_MODE);
        Database.insert(accounts, AccessLevel.USER_MODE);
        List<SObject> rows = Database.query('SELECT Id FROM Account WITH SYSTEM_MODE');
        insert as system accounts;
    }
    public void finish(Database.BatchableContext bc) {}
}
