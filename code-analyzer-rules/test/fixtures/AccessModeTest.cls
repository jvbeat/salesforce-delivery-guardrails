@IsTest
private class AccessModeTest {
    @IsTest
    static void readsWithoutMode() {
        List<Account> accounts = [SELECT Id FROM Account];
        Database.insert(accounts);
        System.assertEquals(0, accounts.size());
    }
}
