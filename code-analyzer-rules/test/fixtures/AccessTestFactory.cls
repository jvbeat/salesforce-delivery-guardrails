public class AccessTestFactory {
    public static List<Account> accounts() {
        List<Account> accounts = [SELECT Id FROM Account];
        Database.insert(accounts);
        return accounts;
    }
}
