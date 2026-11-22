public without sharing class SoqlClean {
    public static List<Account> read(Set<Id> ids) {
        List<Account> a = [SELECT Id FROM Account WHERE Id IN :ids WITH SYSTEM_MODE];
        List<Account> b = [SELECT Id FROM Account WITH USER_MODE LIMIT 10];
        List<Account> c = [SELECT Id FROM Account WITH SECURITY_ENFORCED];
        return a;
    }
}
