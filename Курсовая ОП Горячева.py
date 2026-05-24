import sqlite3
import os

DATABASE = "tasks.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS priorities (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL UNIQUE,
            level INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            subject_id  INTEGER NOT NULL,
            priority_id INTEGER NOT NULL,
            deadline    TEXT,
            done        INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (subject_id)  REFERENCES subjects(id),
            FOREIGN KEY (priority_id) REFERENCES priorities(id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        subjects = [
            "Математика",
            "Физика",
            "Основы программирования",
            "История",
            "Английский язык",
            "Другое"
        ]
        for name in subjects:
            cursor.execute("INSERT INTO subjects (name) VALUES (?)", (name,))

    cursor.execute("SELECT COUNT(*) FROM priorities")
    if cursor.fetchone()[0] == 0:
        priorities = [
            ("Высокий", 1),
            ("Средний", 2),
            ("Низкий",  3)
        ]
        for name, level in priorities:
            cursor.execute(
                "INSERT INTO priorities (name, level) VALUES (?, ?)",
                (name, level)
            )

    conn.commit()
    conn.close()

def get_all_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM subjects ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_priorities():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM priorities ORDER BY level")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tasks.id,
               tasks.title,
               subjects.name  AS subject,
               priorities.name AS priority,
               tasks.deadline,
               tasks.done
        FROM tasks
        JOIN subjects   ON tasks.subject_id  = subjects.id
        JOIN priorities ON tasks.priority_id = priorities.id
        ORDER BY tasks.done ASC, priorities.level ASC, tasks.id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_task_db(title, subject_id, priority_id, deadline):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, subject_id, priority_id, deadline, done)
        VALUES (?, ?, ?, ?, 0)
    """, (title, subject_id, priority_id, deadline))
    conn.commit()
    conn.close()


def mark_task_done(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_task_db(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_statistics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subjects.name AS subject,
               COUNT(tasks.id)   AS total,
               SUM(tasks.done)   AS done_count
        FROM subjects
        JOIN tasks ON subjects.id = tasks.subject_id
        GROUP BY subjects.id
        ORDER BY total DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_task():
    print("\n=== Новая задача ===")
    title = input("Название задачи: ").strip()
    if title == "":
        print("Ошибка: название не может быть пустым.")
        return

    subjects = get_all_subjects()
    print("\nВыберите предмет:")
    for subj in subjects:
        print(str(subj["id"]) + ". " + subj["name"])
    choice = input("Введите номер: ").strip()
    subject_id = None
    if choice.isdigit():
        for subj in subjects:
            if subj["id"] == int(choice):
                subject_id = subj["id"]
                break
    if subject_id is None:
        for subj in subjects:
            if subj["name"] == "Другое":
                subject_id = subj["id"]
                break

    priorities = get_all_priorities()
    print("\nВыберите приоритет:")
    for pr in priorities:
        print(str(pr["id"]) + ". " + pr["name"])
    p_choice = input("Введите номер: ").strip()
    priority_id = priorities[0]["id"]
    if p_choice.isdigit():
        for pr in priorities:
            if pr["id"] == int(p_choice):
                priority_id = pr["id"]
                break

    deadline = input("Дедлайн (ДД.ММ.ГГГГ) или Enter для пропуска: ").strip()

    add_task_db(title, subject_id, priority_id, deadline)
    print("Задача \"" + title + "\" добавлена.")


def view_tasks():
    tasks = get_all_tasks()
    if len(tasks) == 0:
        print("\nСписок задач пуст.")
        return

    print("\n" + "-" * 65)
    print("  ID   Название             Предмет          Дедлайн    Статус")
    print("-" * 65)
    for t in tasks:
        if t["done"]:
            status = "Выполнено"
        else:
            status = t["priority"]

        title_short = t["title"]
        if len(title_short) > 20:
            title_short = title_short[:18] + ".."

        subj_short = t["subject"]
        if len(subj_short) > 15:
            subj_short = subj_short[:13] + ".."

        dl = t["deadline"]
        if not dl:
            dl = "-"

        row_id = str(t["id"])
        print("  " + row_id.ljust(5) + title_short.ljust(21) +
              subj_short.ljust(17) + dl.ljust(11) + status)

    print("-" * 65)
    done_count = sum(1 for t in tasks if t["done"])
    print("Всего: " + str(len(tasks)) + ", выполнено: " + str(done_count))
    print()


def mark_done():
    view_tasks()
    entry = input("Введите ID задачи: ").strip()
    if not entry.isdigit():
        print("Ошибка: введите число.")
        return

    task_id = int(entry)
    tasks = get_all_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        print("Ошибка: задача с таким ID не найдена.")
        return
    if found["done"]:
        print("Задача уже выполнена.")
        return

    mark_task_done(task_id)
    print("Задача \"" + found["title"] + "\" отмечена выполненной.")


def delete_task():
    view_tasks()
    entry = input("Введите ID задачи для удаления: ").strip()
    if not entry.isdigit():
        print("Ошибка: введите число.")
        return

    task_id = int(entry)
    tasks = get_all_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        print("Ошибка: задача с таким ID не найдена.")
        return

    delete_task_db(task_id)
    print("Задача \"" + found["title"] + "\" удалена.")


def show_statistics():
    tasks = get_all_tasks()
    if len(tasks) == 0:
        print("\nЗадач пока нет.")
        return

    total_all = len(tasks)
    done_all = sum(1 for t in tasks if t["done"])

    print("\n=== Статистика ===")
    print("Всего задач:  " + str(total_all))
    print("Выполнено:    " + str(done_all))
    print("Активных:     " + str(total_all - done_all))

    stats = get_statistics()
    if len(stats) > 0:
        print("\nПо предметам:")
        print("  " + "Предмет".ljust(25) + "Всего   Выполнено")
        print("  " + "-" * 40)
        for row in stats:
            done_count = row["done_count"] if row["done_count"] else 0
            print("  " + row["subject"].ljust(25) +
                  str(row["total"]).ljust(8) + str(done_count))
    print()


def print_menu():
    print("\n==========================================")
    print("       МЕНЕДЖЕР УЧЕБНЫХ ЗАДАЧ")
    print("==========================================")
    print("  1. Показать все задачи")
    print("  2. Добавить задачу")
    print("  3. Отметить задачу выполненной")
    print("  4. Удалить задачу")
    print("  5. Статистика")
    print("  0. Выход")
    print("==========================================")


def main():
    print("Добро пожаловать в Менеджер учебных задач!")
    init_db()

    while True:
        print_menu()
        choice = input("Выберите пункт меню: ").strip()

        if choice == "1":
            view_tasks()
        elif choice == "2":
            add_task()
        elif choice == "3":
            mark_done()
        elif choice == "4":
            delete_task()
        elif choice == "5":
            show_statistics()
        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неверный пункт. Попробуйте снова.")


main()