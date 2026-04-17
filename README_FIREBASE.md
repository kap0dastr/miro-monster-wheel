# Настройка Firebase для «Колеса монстров»

Нужна синхронизация между участниками ретро — используем Firebase Realtime Database (бесплатный тариф). Весь процесс ~5 минут.

## Шаг 1. Создай Firebase-проект

1. Открой https://console.firebase.google.com/
2. Войди под аккаунтом `vsnubvs@gmail.com`
3. Нажми **"Add project"** (Создать проект)
4. Имя проекта: `miro-dnd-retro` (или любое)
5. **Google Analytics** можно выключить (не нужна для этого)
6. Нажми **"Create project"**, подожди ~30 сек

## Шаг 2. Создай Realtime Database

1. В левом меню: **Build → Realtime Database**
2. Нажми **"Create Database"**
3. Локация: **europe-west1** (Бельгия — ближе всего)
4. Режим безопасности: выбери **"Start in test mode"**
   - Это разрешает чтение/запись всем, но только 30 дней
   - Потом я покажу как поставить постоянные правила
5. Нажми **"Enable"**

## Шаг 3. Добавь Web App и скопируй конфиг

1. В левом меню сверху: **Project Overview** → значок шестерёнки → **Project settings**
2. Прокрути вниз до **"Your apps"** → нажми иконку **`</>` (Web)**
3. App nickname: `miro-wheel`
4. **Firebase Hosting — НЕ включать** (нам не нужен)
5. Нажми **"Register app"**
6. Появится блок кода с `const firebaseConfig = { ... }` — это то что нужно

## Шаг 4. Перенеси конфиг в `config.yaml`

Скопируй значения из `firebaseConfig` в секцию `firebase:` в файле `config.yaml`:

```yaml
firebase:
  apiKey: "AIzaSy..."
  authDomain: "miro-dnd-retro.firebaseapp.com"
  databaseURL: "https://miro-dnd-retro-default-rtdb.europe-west1.firebasedatabase.app"
  projectId: "miro-dnd-retro"
  storageBucket: "miro-dnd-retro.appspot.com"
  messagingSenderId: "123456789"
  appId: "1:123456789:web:abc123"
```

**ВАЖНО:** если `databaseURL` отсутствует в конфиге Firebase — значит в Шаге 2 БД не создалась. Вернись и сделай.

## Шаг 5. Готово

Скажи мне что конфиг заполнен — я соберу приложение и задеплою его на CodeSandbox, встрою в твою Miro-доску.

---

## FAQ

**Безопасно ли хранить apiKey в публичном коде?**
Да — это публичный ключ для идентификации проекта, не секрет. Защита делается через правила БД (см. ниже).

**Что с правилами безопасности после 30 дней test mode?**
Перед окончанием я дам нормальные правила: чтение/запись только в нашу ветку `/miro-wheel/...`, без доступа к другим данным.

**Сколько это стоит?**
Бесплатный план Firebase Spark: 100 одновременных подключений и 1 ГБ хранилища. Для ретро команды — с запасом в 100 раз.
