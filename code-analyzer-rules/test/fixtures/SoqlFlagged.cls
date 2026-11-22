public without sharing class SoqlFlagged {
    public static List<Account> read(Set<Id> ids) {
        List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :ids];
        Integer total = [SELECT COUNT() FROM Contact];
        for (Contact c : [SELECT Id FROM Contact LIMIT 5]) {
            accounts.add(new Account(Id = c.AccountId));
        }
        return accounts;
    }
}
