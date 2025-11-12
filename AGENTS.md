# AGENTS.md

## agents
- name: coder
  role: "Write and modify code on request"
  tools: [git, shell]
- name: runner
  role: "Run and test the project"
  tools: [shell]

## tasks
- id: setup
  for: coder
  goal: "Инициализировать проект и подготовить зависимые файлы"
  steps:
    - "Создай файл requirements.txt (если Python) или package.json (если Node) — пока пустой базовый минимум"
    - "Добавь простой скрипт запуска: run.sh"

- id: hello
  for: runner
  goal: "Запустить проект или скрипт проверки"
  steps:
    - "Если есть run.sh — запусти его"
    - "Иначе выведи 'OK: nothing to run yet'"
