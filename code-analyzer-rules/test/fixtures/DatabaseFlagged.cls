public without sharing class DatabaseFlagged {
    public static void write(List<Account> accounts, String soql) {
        Database.update(accounts, false);
        Database.insert(accounts);
        List<SObject> rows = Database.query(soql);
        Database.QueryLocator locator = Database.getQueryLocator(soql);
        Database.delete(accounts, false);
    }
}
