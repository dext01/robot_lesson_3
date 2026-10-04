# ПР03. Демонстрация ноды patrol

Дата опыта: **22 сентября 2026 года**. Хост — Ubuntu 25.04, эксперимент
внутри Docker-контейнера `pr03-local-demo` (образ
`osrf/ros:lyrical-desktop-full`, `ROS_DISTRO=lyrical`). Домен:
`ROS_DOMAIN_ID=16`. Рабочая директория внутри контейнера — `/work`,
смонтирована на `/home/stepan/robot/3_lesson` на хосте.

## Роли фрагментов rclpy

* **`rclpy.init(args=args)`** — инициализирует ROS-контекст в процессе:
  создаёт коммуникационный слой RMW, регистрирует процесс в DDS,
  выделяет глобальные ресурсы (allocator, guard conditions). Без `init`
  нельзя создать ни ноду, ни publisher/subscription.
* **`Node.__init__('patrol')`** — регистрирует ноду в графе, создаёт
  подписку `/turtle1/pose` (поле `_pose_sub`), publisher `cmd_vel` и
  таймер 0.1 с. Подписка и timer сохранены как поля объекта, иначе GC
  удалил бы их и callback не сработал бы.
* **`rclpy.spin(node)`** — блокирующий цикл: single-threaded executor
  забирает готовые события из wait-set и по очереди зовёт callback-и
  подписки и таймера. Внутри одной итерации callback-и не пересекаются
  между собой; таймер и подписка обрабатываются в одном потоке.
* **`callback` подписки** — `_on_pose(msg)` только сохраняет последнее
  сообщение в поле `_last_pose`. Никакой публикации из подписки нет:
  выбор команды сосредоточен в таймере, поэтому темп выхода стабильный
  и не зависит от частоты позы.
* **`callback` таймера** — `_on_timer()` вызывает чистую функцию
  `choose_cmd(self._last_pose)` и публикует полученный `Twist`. Пока
  позы нет — выдаёт нулевой Twist, после первой позы — постоянные
  `linear.x=0.5, angular.z=0.3`.
* **`Ctrl+C` → `KeyboardInterrupt`** — `rclpy.init` вызывается с
  `SignalHandlerOptions.NO`, поэтому SIGINT обрабатывает Python, а
  контекст rclpy остаётся живым до `finally`. `spin` возвращает
  управление, `finally` публикует нулевой `Twist`, затем
  `node.destroy_node()` и `rclpy.try_shutdown()`. Со стандартным
  обработчиком rclpy контекст закрывается раньше, и публикация в
  `finally` уже не проходит.

## Чистая функция `choose_cmd`

`choose_cmd(pose)` не зависит от rclpy и глобального состояния:
`None → нулевой Twist`, `Pose → Twist(linear.x=0.5, angular.z=0.3)`.
Три unit-теста в `src/patrol/test/test_choose_cmd.py` покрывают
случай отсутствия позы, обычную позу в центре поля и позу у края.
Результат pytest — [`tests.txt`](./tests.txt): `3 passed`.

## Стадия 1 · Собрать

Пакет собран:

```bash
colcon build --symlink-install --packages-select turtle_bringup patrol
```
Полный лог — [`build.txt`](./build.txt) (`Summary: 2 packages finished`).

Turtlesim запущен через launch из ПР02:

```bash
ros2 launch turtle_bringup sim.launch.py
```

Граф после запуска — [`nodes-launch.txt`](./nodes-launch.txt),
[`topics-before-patrol.txt`](./topics-before-patrol.txt): нода
`/turtlesim` и обычные топики turtlesim. Начальная поза —
[`pose-initial.txt`](./pose-initial.txt): `x=5.544, y=5.544, theta=0`.

## Стадия 2 · Сломать (publish в относительный `cmd_vel`)

```bash
ros2 run patrol patrol      # без remap → пишет в /cmd_vel
```

Через ~4 секунды сняты:

* [`nodes-broken.txt`](./nodes-broken.txt) — `/patrol` и `/turtlesim`
  обе живы;
* [`topics-broken.txt`](./topics-broken.txt) — появился новый топик
  `/cmd_vel` (относительный `cmd_vel` в namespace `/`);
* [`topic-info-broken-cmd_vel.txt`](./topic-info-broken-cmd_vel.txt) —
  **1 publisher (`/patrol`), 0 subscribers**;
* [`topic-info-broken-turtle1_cmd_vel.txt`](./topic-info-broken-turtle1_cmd_vel.txt)
  — **0 publishers, 2 subscribers** (первый — `/turtlesim`, второй —
  `_NODE_NAME_UNKNOWN_`; это DDS-призрак от прошлого GID через
  `network=host`, содержательно значим только `/turtlesim`);
* [`pose-after-broken.txt`](./pose-after-broken.txt) — поза та же
  `x=5.544, y=5.544, theta=0`, черепаха не двигалась.

Разрыв графа: patrol честно шлёт `Twist` 10 раз в секунду в `/cmd_vel`,
но подписчика у этого топика нет; `turtlesim` подписан на другое имя
`/turtle1/cmd_vel`, и DDS не связывает endpoint-ы разных имён, даже
если типы у них одинаковые. Правильного типа сообщения недостаточно —
имя топика первично.

## Стадия 3 · Доказать (`-r cmd_vel:=/turtle1/cmd_vel`)

Контейнер перезапущен, turtlesim поднят заново, начальная поза до
запуска patrol — [`pose-before-fixed.txt`](./pose-before-fixed.txt):
`x=5.544, y=5.544, theta=0`. Затем:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Граф после remap — [`topics-fixed.txt`](./topics-fixed.txt): топик
`/cmd_vel` **исчез**, patrol теперь публикует прямо в
`/turtle1/cmd_vel`. Из
[`topic-info-fixed.txt`](./topic-info-fixed.txt):

* Publishers `/turtle1/cmd_vel`: **1 (`/patrol`)**
* Subscribers `/turtle1/cmd_vel`: **2** (реальный `/turtlesim` +
  тот же `_NODE_NAME_UNKNOWN_`-призрак)

Измерение частоты команды за ~10 секунд:

```bash
timeout 12 ros2 topic hz /turtle1/cmd_vel --window 100
```

Лог — [`hz-fixed.txt`](./hz-fixed.txt). Итоговая строка:
`average rate: 9.999, min: 0.099s, max: 0.102s, std dev: 0.00058s,
window: 100` — реальная частота **≈ 10.0 Hz**, что совпадает с
теоретическим периодом таймера `0.1 с`. `std dev ≈ 0.6 мс` — jitter
однопоточного executor на idle-контейнере.

Поза после ~15 секунд движения — [`pose-after-fixed.txt`](./pose-after-fixed.txt):
`x=3.95, y=7.71, theta=-1.88`, `linear_velocity=0.5,
angular_velocity=0.3` — команда доходит и turtlesim крутит черепаху
ровно теми скоростями, что задаёт `choose_cmd`.

## Стадия 4 · Остановка

`Ctrl+C` в терминале с patrol → `spin()` вернул управление → в
`finally` отправлен нулевой `Twist` → нода уничтожена. Проверено через
`ros2 topic echo /cmd_vel --field linear.x`: после серии `0.5`
последним приходит `0.0`.

Завершение процесса само по себе не является командой торможения:
подписчик просто перестаёт получать сообщения, а что делать дальше,
решает он сам. Turtlesim останавливает черепаху, если команд нет
дольше 1 с, но другой робот может продолжить выполнять последнюю
команду. Поэтому явный нулевой `Twist` при остановке надёжнее.

## Сводка стадий

| Стадия      | Проявление                                    | Файлы evidence                                                                       |
|-------------|-----------------------------------------------|--------------------------------------------------------------------------------------|
| Собрать     | пакет собран, launch поднял `/turtlesim`      | `build.txt`, `tests.txt`, `nodes-launch.txt`, `pose-initial.txt`                     |
| Сломать     | patrol пишет в `/cmd_vel`, черепаха стоит     | `topics-broken.txt`, `topic-info-broken-*`, `pose-after-broken.txt`                  |
| Доказать    | remap на `/turtle1/cmd_vel`, hz ≈ 10.0        | `topics-fixed.txt`, `topic-info-fixed.txt`, `hz-fixed.txt`, `pose-after-fixed.txt`   |
