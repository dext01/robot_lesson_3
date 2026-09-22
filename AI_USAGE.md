# Использование ИИ

## ПР03 — модель и инструмент

Claude (Anthropic), интерфейс Claude Code CLI. Использовался как
ассистент, не автор.

`ai_used: true`.

## Что делал студент самостоятельно

- Разобрал условие ПР03 (подписка на позу, таймер, публикация Twist в
  относительный `cmd_vel`, разрыв через имя топика и лечение через
  remap).
- Настроил и запустил отдельный Docker-контейнер `pr03-local-demo` на
  `osrf/ros:lyrical-desktop-full` с bind-mount на
  `/home/stepan/robot/3_lesson`, `ROS_DOMAIN_ID=16`, X11-сокет
  проброшен для окна turtlesim.
- Скопировал `turtle_bringup` из ПР02 в новый workspace, не меняя
  содержимого, чтобы использовать проверенный `sim.launch.py`.
- Выбрал имя пакета `patrol`, зависимости `rclpy`, `geometry_msgs`,
  `turtlesim_msgs` (тип позы под Lyrical получен через
  `ros2 topic type /turtle1/pose`).
- Провёл эксперимент: запуск без remap → `/cmd_vel` не связан с
  turtlesim → черепаха стоит; запуск с `-r cmd_vel:=/turtle1/cmd_vel`
  → черепаха едет, `ros2 topic hz` за 10 секунд подтвердил ~10 Hz.
- Сверил числа позы и частоту в отчётах с реальным stdout из
  `evidence/pr03/*.txt`.

## В чём помогал ИИ

- Подсказал минимальную структуру ноды `PatrolNode` (подписка +
  таймер как поля объекта, публикация в относительный `cmd_vel`,
  корректный shutdown с финальным нулевым Twist).
- Помог выделить чистую функцию `choose_cmd(pose) -> Twist`, чтобы её
  можно было тестировать без `rclpy.init()`.
- Сформулировал три юнит-теста (нет позы, обычная поза, поза на краю
  поля).
- Оформил `evidence/pr03/demo.md`, `report.json`, `README.md` по
  собранному stdout.
- Собрал CI workflow: сборка `turtle_bringup` и `patrol`, прогон
  pytest, проверка установленного launch.
- Разъяснил роли `rclpy.init`, `spin`, callback-ов и корректной
  остановки, чтобы разобрать «Ctrl+C ≠ команда торможения».

## Что НЕ делал ИИ

- Не выдумывал значения. Все числа
  (`hz ≈ 10.0`, поза после сбоя `x=5.544 y=5.544 theta=0`, поза
  после исправления `x=3.95 y=7.71 theta=-1.88`,
  `linear_velocity=0.5, angular_velocity=0.3`) получены прогоном
  реальных команд, полный stdout сохранён в `evidence/pr03/`.
- Не подделывал stdout: файлы `evidence/pr03/*.txt` — прямой вывод
  инструментов ROS 2 без правки.
- Не заменял защиту опыта: демонстрация будет живой у преподавателя.

## Файлы, где ИИ участвовал в оформлении

- `src/patrol/patrol/patrol.py` — код ноды и `choose_cmd`.
- `src/patrol/test/test_choose_cmd.py` — юнит-тесты.
- `src/patrol/package.xml`, `src/patrol/setup.py` — заполнение
  maintainer/description.
- `evidence/pr03/demo.md`, `evidence/pr03/report.json` — оформление
  отчёта.
- `README.md`, `AI_USAGE.md` — обзор репо и эта декларация.
- `.github/workflows/pr03.yml` — CI.

Остальные `evidence/pr03/*.txt` — прямой stdout, не редактировался.

## Проверка

- Образ Docker: `osrf/ros:lyrical-desktop-full`, `ROS_DISTRO=lyrical`.
- `python3 -m pytest src/patrol/test/test_choose_cmd.py` → `3 passed`.
- `colcon build --symlink-install --packages-select turtle_bringup patrol`
  → `Summary: 2 packages finished`.
- Числа в `demo.md` и `report.json` сверены с
  `evidence/pr03/*.txt`.
- `python3 -m json.tool evidence/pr03/report.json` проходит.

Переписка, личные промпты и секреты в репозитории не публикуются.
