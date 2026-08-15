# Занятие: Bounded Context

Карточка: [#p14](https://nikolay-e.github.io/learning/#p14). Читается после p12, p13,
p42 и p43 — она их собирает, а не вводит что-то новое.

## Задача, с которой всё начинается

Интернет-магазин. Слово «клиент» произносят два отдела:

- **биллинг** — кому выставлять счёт: юридическое имя, ИНН, платёжные методы, статус
  «заблокирован за долг»;
- **маркетинг** — кому слать кампании: имя как в письме, сегмент, согласие на рассылку,
  дата последнего открытия письма.

Соблазн очевидный: полей мало, `id` и `email` совпадают — сделать один класс `Customer`
и не плодить сущности. Через год у него двадцать полей, половина всегда `null`, а правка
формата платёжного метода требует регрессии маркетинговых рассылок.

## Слой 1 — то же самое без единой новой конструкции языка

Обычные классы, обычный метод. Ничего из Java 21 здесь не нужно.

```java
// billing/BillingCustomer.java
public final class BillingCustomer {
    private final String id;
    private final String legalName;
    private final String email;
    private final boolean suspendedForDebt;

    public BillingCustomer(String id, String legalName, String email, boolean suspendedForDebt) {
        this.id = id;
        this.legalName = legalName;
        this.email = email;
        this.suspendedForDebt = suspendedForDebt;
    }

    public String id() { return id; }
    public String legalName() { return legalName; }
    public String email() { return email; }
    public boolean suspendedForDebt() { return suspendedForDebt; }
}
```

```java
// marketing/MarketingContact.java
public final class MarketingContact {
    private final String id;
    private final String displayName;
    private final String email;
    private final boolean campaignsAllowed;

    public MarketingContact(String id, String displayName, String email, boolean campaignsAllowed) {
        this.id = id;
        this.displayName = displayName;
        this.email = email;
        this.campaignsAllowed = campaignsAllowed;
    }
    // геттеры опущены
}
```

Два класса лежат в разных пакетах и ничего друг о друге не знают. Перевод — отдельный
класс, и он живёт на стороне маркетинга: это маркетинг решает, кого он готов считать
своим контактом.

```java
// marketing/BillingToMarketingTranslator.java
public final class BillingToMarketingTranslator {

    // Единственное бизнес-решение этого класса: клиент, заблокированный за долг,
    // остаётся клиентом биллинга, но кампании ему не идут. Это решение маркетинга,
    // а не следствие структуры данных.
    public MarketingContact translate(BillingCustomer c) {
        boolean campaignsAllowed = !c.suspendedForDebt();
        return new MarketingContact(c.id(), c.legalName(), c.email(), campaignsAllowed);
    }
}
```

Обратите внимание, чего здесь нет: конструктора `MarketingContact(BillingCustomer)` и
статического `MarketingContact.from(billingCustomer)`. Оба выглядели бы удобнее и оба
спрятали бы строчку с решением внутрь типа, который к этому решению отношения не имеет.
`legalName → displayName` тоже не тождество: юридическое имя в письме читается как
ошибка, и рано или поздно правило разъедется. Пока перевод стоит отдельным классом,
разъезд ему ничего не стоит.

## Слой 2 — та же идея на Java 21

Три строки предисловия:

- `record Point(int x, int y)` — неизменяемый набор данных; конструктор, геттеры
  `x()`/`y()`, `equals`, `hashCode` и `toString` компилятор пишет сам.
- `enum` — тип с конечным перечисленным списком значений.
- `sealed interface X permits A, B` — тип с закрытым списком реализаций; в `switch` по
  нему компилятор проверяет, что разобраны все варианты.

```java
public record BillingCustomer(
    String id, String legalName, String email, BillingStatus status) {}

public enum BillingStatus { ACTIVE, SUSPENDED_FOR_DEBT, CLOSED }

public record MarketingContact(
    String id, String displayName, String email) {}
```

Решение «слать или не слать» перестаёт быть булевым полем внутри контакта и становится
самостоятельным типом — результатом перевода:

```java
public sealed interface SyncDecision permits Upsert, Suppress {}

public record Upsert(MarketingContact contact) implements SyncDecision {}
public record Suppress(String reason) implements SyncDecision {}

public final class BillingToMarketingTranslator {

    public SyncDecision translate(BillingCustomer c) {
        return switch (c.status()) {
            case ACTIVE -> new Upsert(new MarketingContact(c.id(), c.legalName(), c.email()));
            case SUSPENDED_FOR_DEBT -> new Suppress("должник");
            case CLOSED -> new Suppress("счёт закрыт");
        };
    }
}
```

Что изменилось по сути: ничего. Что изменилось на практике — забыть новый статус биллинга
стало невозможно, компилятор потребует разобрать его при появлении. `enum` вместо `boolean`
и `sealed` вместо `null` — это [p3](https://nikolay-e.github.io/learning/#p3),
приложенный к границе.

Что **не** изменилось и меняться не должно: перевод по-прежнему отдельный класс, и в нём
по-прежнему одна строчка бизнес-решения на каждый статус.

## Где здесь конфликт с DRY

Поля `id` и `email` дублируются в двух записях. Соблазн вынести `CommonCustomerFields`
или общий базовый тип — ровно то, против чего написана
[p43](https://nikolay-e.github.io/learning/#p43): это не одно знание в двух местах, а два
знания, сегодня выглядящие одинаково. Первая же правка («биллингу нужен второй email для
инвойсов») приезжает в общий тип флагом, который маркетингу никогда не понадобится.

## Вопросы самопроверки

1. Почему общий класс `Customer` для биллинга и маркетинга плох — назовите причину, не
   связанную с количеством `null`-полей.
2. Поля `id`, `email` и `name` совпадают у обоих типов. Почему это не доказывает, что тип
   один?
3. Где физически живёт код перевода в примере и почему именно там, а не в биллинге и не в
   «общем» модуле?
4. Чем `MarketingContact.from(billingCustomer)` хуже отдельного транслятора, если делает
   ровно то же самое?
5. Два одинаковых куска кода по разные стороны границы контекста — дублирование или
   совпадение? Что решает?
6. Обязательно ли разносить bounded contexts по разным сервисам? Что меняется, если оба
   живут в одном процессе?
