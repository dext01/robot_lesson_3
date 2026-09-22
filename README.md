# robot_lesson_3 — ПР03. Первая нода: поза и команда

Практика ПР03 курса «Введение в ROS 2» (НГУ, ФИТ, осень 2026).
Пакет `patrol` подписывается на `/turtle1/pose`, хранит последнюю
позу и каждые 0.1 с публикует `geometry_msgs/msg/Twist` в
относительный топик `cmd_vel`. Правильная связь с turtlesim
достигается remap-ом `cmd_vel:=/turtle1/cmd_vel` при запуске.

Пакет `turtle_bringup` перенесён из ПР02 без изменений — он запускает
`turtlesim_node` через `sim.launch.py`.

## Структура

```
src/
├── turtle_bringup/            # launch turtlesim (из ПР02)
└── patrol/
    ├── patrol/patrol.py       # нода + чистая функция choose_cmd
    ├── test/test_choose_cmd.py# unit-тесты choose_cmd
    ├── package.xml            # ament_python, deps: rclpy, geometry_msgs, turtlesim_msgs
    └── setup.py
evidence/pr03/
├── demo.md                    # разбор ролей rclpy и стадий опыта
├── tests.txt                  # pytest 3 passed
├── build.txt                  # colcon build (2 packages finished)
├── hz-fixed.txt               # средний темп 10.0 Hz за 10 c
├── topic-info-broken-*.txt    # /cmd_vel: 1 pub / 0 sub
├── topic-info-fixed.txt       # /turtle1/cmd_vel: 1 pub / 2 sub после remap
├── pose-*.txt                 # позы до/после сбоя и после исправления
└── report.json                # по общему шаблону course kit
AI_USAGE.md                    # декларация ИИ для ПР03
```

## Как воспроизвести

Внутри контейнера `pr03-local-demo`
(`osrf/ros:lyrical-desktop-full`), `ROS_DOMAIN_ID=16`:

```bash
source /opt/ros/lyrical/setup.bash
cd /work
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash

# терминал A — симулятор
ros2 launch turtle_bringup sim.launch.py

# терминал B — сломанный запуск: /cmd_vel, черепаха стоит
ros2 run patrol patrol

# терминал B (после Ctrl+C) — исправленный запуск: движение
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel

# терминал C — измерение частоты
timeout 12 ros2 topic hz /turtle1/cmd_vel --window 100
```

Unit-тесты чистой функции:

```bash
python3 -m pytest src/patrol/test/test_choose_cmd.py -v
```

## Критерии зачёта ПР03

* **Собрать**: подписка `/turtle1/pose` сохраняет последнее сообщение;
  таймер 0.1 с публикует `Twist`.
* **Сломать**: patrol без remap → `/cmd_vel`, `turtlesim` не получает
  команду.
* **Доказать**: `-r cmd_vel:=/turtle1/cmd_vel` → команда доходит,
  темп ≈ 10 Hz.

Подробности стадий — [`evidence/pr03/demo.md`](evidence/pr03/demo.md).
