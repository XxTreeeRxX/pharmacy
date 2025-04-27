import tkinter as tk
from tkinter import ttk, messagebox
from enum import Enum, auto
from hashlib import sha256
import psycopg2
from psycopg2 import sql
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime, date
import logging
import csv
from datetime import datetime
import os

# Настройка логирования
logging.basicConfig(
    filename='pharmacy_app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Database:
    def __init__(self, dbname="pharmacy", user="zhunya", password="08051985", host="localhost", port="5432"):
        try:
            self.conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            self.cursor = self.conn.cursor()
            logging.info("Успешное подключение к базе данных")
        except psycopg2.Error as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            messagebox.showerror("Ошибка базы данных", f"Не удалось подключиться к базе данных: {e}")
            raise

    def get_simple_inventory_report(self):
        """Упрощенный отчет по остаткам"""
        query = """
        SELECT 
            m.medicine_id as id,
            m.name as medicine,
            m.quantity_in_stock as stock,
            s.name as supplier
        FROM medicines m
        LEFT JOIN suppliers s ON m.supplier_id = s.supplier_id
        ORDER BY m.quantity_in_stock ASC
        """
        return self.execute_query(query)

    def get_future_deliveries(self):
        """Будущие поставки"""
        query = """
        SELECT p.purchase_id, p.purchase_date, s.name as supplier, 
               m.name as medicine, pi.quantity, pi.price
        FROM purchases p
        JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
        JOIN medicines m ON pi.medicine_id = m.medicine_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.purchase_date > CURRENT_DATE
        ORDER BY p.purchase_date
        """
        return self.execute_query(query)

    def get_last_30days_sales(self):
        """Продажи за 30 дней"""
        query = """
        SELECT s.sale_id, s.sale_date, 
               m.name as medicine, si.quantity, si.price
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        JOIN medicines m ON si.medicine_id = m.medicine_id
        WHERE s.sale_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY s.sale_date DESC
        """
        return self.execute_query(query)

    def get_consumption_stats(self):
        """Статистика расхода"""
        query = """
        SELECT m.medicine_id, m.name, 
               COALESCE(SUM(si.quantity), 0) as total_sold,
               COALESCE(SUM(si.quantity), 0) / 30.0 as avg_daily_consumption,
               m.quantity_in_stock as current_stock
        FROM medicines m
        LEFT JOIN sale_items si ON m.medicine_id = si.medicine_id
        LEFT JOIN sales s ON si.sale_id = s.sale_id
        WHERE s.sale_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY m.medicine_id, m.name, m.quantity_in_stock
        ORDER BY avg_daily_consumption DESC
        """
        return self.execute_query(query)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True, return_id: bool = False):
        try:
            logging.debug(f"Выполнение запроса: {query} с параметрами: {params}")
            self.cursor.execute(query, params or ())
            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    result = self.cursor.fetchall()
                    logging.debug(f"Результат SELECT: {result}")
                    return result
                elif query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    if return_id and query.strip().upper().startswith('INSERT'):
                        result = self.cursor.fetchone()
                        self.conn.commit()
                        logging.debug(f"Результат INSERT (возврат ID): {result}")
                        return result
                    self.conn.commit()
                    logging.debug("Запрос INSERT/UPDATE/DELETE выполнен успешно")
                    return True
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Ошибка выполнения запроса: {query}. Параметры: {params}. Ошибка: {e}")
            return False

    def get_table_data(self, table_name: str) -> List[Dict]:
        try:
            logging.info(f"Получение данных таблицы: {table_name}")

            if table_name == 'prescriptions':
                query = """
                SELECT p.prescription_id, 
                       c.first_name || ' ' || c.last_name as customer, 
                       m.name as medicine, 
                       p.doctor_name, p.issue_date, p.expiration_date
                FROM prescriptions p
                LEFT JOIN customers c ON p.customer_id = c.customer_id
                LEFT JOIN medicines m ON p.medicine_id = m.medicine_id
                """
            elif table_name == 'purchases':
                query = """
                SELECT pu.purchase_id, pu.purchase_date, 
                       s.name as supplier, 
                       pu.total_amount
                FROM purchases pu
                LEFT JOIN suppliers s ON pu.supplier_id = s.supplier_id
                """
            elif table_name == 'sales':
                query = """
                SELECT s.sale_id, s.sale_date, 
                       c.first_name || ' ' || c.last_name as customer,
                       e.first_name || ' ' || e.last_name as employee,
                       s.total_amount
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.customer_id
                LEFT JOIN employees e ON s.employee_id = e.employee_id
                ORDER BY s.sale_date DESC
                """
            elif table_name == 'purchase_items':
                query = """
                SELECT pi.purchase_item_id, 
                       pi.purchase_id, 
                       m.name as medicine,
                       pi.quantity, pi.price
                FROM purchase_items pi
                LEFT JOIN medicines m ON pi.medicine_id = m.medicine_id
                """
            elif table_name == 'sale_items':
                query = """
                SELECT si.sale_item_id, 
                       si.sale_id, 
                       m.name as medicine,
                       si.quantity, si.price
                FROM sale_items si
                LEFT JOIN medicines m ON si.medicine_id = m.medicine_id
                """
            elif table_name == 'medicines':
                query = """
                SELECT m.medicine_id, m.name, m.description, m.manufacturer, 
                       m.price, m.quantity_in_stock, m.expiration_date,
                       s.name as supplier
                FROM medicines m
                LEFT JOIN suppliers s ON m.supplier_id = s.supplier_id
                ORDER BY m.quantity_in_stock ASC
                """
            elif table_name == 'app_users':
                query = "SELECT user_id, username, role FROM app_users"
            else:
                query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))

            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            data = [dict(zip(columns, row)) for row in self.cursor.fetchall()]

            logging.debug(f"Получено {len(data)} записей из таблицы {table_name}")
            return data
        except Exception as e:
            logging.error(f"Ошибка получения данных таблицы {table_name}: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            return []

    def get_table_columns(self, table_name: str) -> List[str]:
        column_names = {
            'customers': ['ID', 'Имя', 'Фамилия', 'Телефон', 'Email', 'Адрес'],
            'employees': ['ID', 'Имя', 'Фамилия', 'Должность', 'Телефон', 'Email', 'Дата найма', 'Зарплата'],
            'suppliers': ['ID', 'Название', 'Контактное лицо', 'Телефон', 'Email', 'Адрес'],
            'medicines': ['ID', 'Название', 'Описание', 'Производитель', 'Цена', 'Количество на складе',
                          'Срок годности', 'Поставщик'],
            'prescriptions': ['ID', 'Клиент', 'Лекарство', 'Имя врача', 'Дата выдачи', 'Срок действия'],
            'purchases': ['ID', 'Дата закупки', 'Поставщик', 'Общая сумма'],
            'sales': ['ID', 'Дата продажи', 'Клиент', 'Сотрудник', 'Общая сумма'],
            'purchase_items': ['ID', 'ID закупки', 'Лекарство', 'Количество', 'Цена'],
            'sale_items': ['ID', 'ID продажи', 'Лекарство', 'Количество', 'Цена'],
            'app_users': ['ID', 'Логин', 'Роль']
        }
        return column_names.get(table_name, [])

    def get_record(self, table_name: str, record_id: int) -> Optional[Dict]:
        """Получает одну запись по ID"""
        try:
            logging.info(f"Получение записи из {table_name} с ID {record_id}")

            db_columns = self._get_db_columns(table_name)
            if not db_columns:
                logging.error(f"Не найдены столбцы для таблицы {table_name}")
                return None

            pk_column = db_columns[0]  # Первый столбец - первичный ключ

            # Формируем запрос вручную (без sql.SQL, для упрощения)
            query = f"SELECT * FROM {table_name} WHERE {pk_column} = %s"

            self.cursor.execute(query, (record_id,))
            result = self.cursor.fetchone()

            if not result:
                logging.warning(f"Запись не найдена: таблица {table_name}, ID {record_id}")
                return None

            record = dict(zip(db_columns, result))
            logging.debug(f"Получена запись: {record}")
            return record
        except Exception as e:
            logging.error(f"Ошибка при получении записи из {table_name} с ID {record_id}: {e}")
            return None

    def get_sale_details(self, sale_id: int) -> Tuple[List[Dict], Dict]:
        """Возвращает детали продажи: список товаров и информацию о продаже"""
        try:
            logging.info(f"Получение деталей продажи с ID {sale_id}")

            sale_query = """
            SELECT s.sale_id, s.sale_date, s.total_amount,
                   c.first_name || ' ' || c.last_name as customer,
                   e.first_name || ' ' || e.last_name as employee
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.customer_id
            LEFT JOIN employees e ON s.employee_id = e.employee_id
            WHERE s.sale_id = %s
            """
            sale_info = self.execute_query(sale_query, (sale_id,))

            if not sale_info:
                logging.warning(f"Продажа с ID {sale_id} не найдена")
                return None, None

            items_query = """
            SELECT m.name, m.medicine_id, si.quantity, si.price, 
                   (si.quantity * si.price) as total
            FROM sale_items si
            JOIN medicines m ON si.medicine_id = m.medicine_id
            WHERE si.sale_id = %s
            ORDER BY m.name
            """
            items = self.execute_query(items_query, (sale_id,))

            sale_data = {
                'sale_id': sale_info[0][0],
                'sale_date': sale_info[0][1],
                'total_amount': sale_info[0][2],
                'customer': sale_info[0][3],
                'employee': sale_info[0][4]
            }

            items_data = [{
                'name': item[0],
                'medicine_id': item[1],
                'quantity': item[2],
                'price': item[3],
                'total': item[4]
            } for item in items]

            logging.debug(f"Детали продажи: {sale_data}")
            logging.debug(f"Товары в продаже: {items_data}")

            return items_data, sale_data
        except Exception as e:
            logging.error(f"Ошибка получения деталей продажи {sale_id}: {e}")
            return None, None

    def get_medicines_list(self):
        """Получает список всех лекарств с ценами и количеством"""
        query = """
        SELECT medicine_id, name, price, quantity_in_stock 
        FROM medicines 
        ORDER BY name
        """
        return self.execute_query(query)

    def get_customers_list(self):
        """Получает список всех клиентов"""
        query = """
        SELECT customer_id, first_name || ' ' || last_name as name 
        FROM customers 
        ORDER BY first_name
        """
        return self.execute_query(query)

    def get_employees_list(self):
        """Получает список всех сотрудников"""
        query = """
        SELECT employee_id, first_name || ' ' || last_name as name 
        FROM employees 
        ORDER BY first_name
        """
        return self.execute_query(query)

    def _get_db_columns(self, table_name: str) -> List[str]:
        db_columns = {
            'customers': ['customer_id', 'first_name', 'last_name', 'phone', 'email', 'address'],
            'employees': ['employee_id', 'first_name', 'last_name', 'position', 'phone', 'email', 'hire_date',
                          'salary'],
            'suppliers': ['supplier_id', 'name', 'contact_person', 'phone', 'email', 'address'],
            'medicines': ['medicine_id', 'name', 'description', 'manufacturer', 'price', 'quantity_in_stock',
                          'expiration_date', 'supplier_id'],
            'prescriptions': ['prescription_id', 'customer_id', 'medicine_id', 'doctor_name', 'issue_date',
                              'expiration_date'],
            'purchases': ['purchase_id', 'purchase_date', 'supplier_id', 'total_amount'],
            'sales': ['sale_id', 'sale_date', 'customer_id', 'employee_id', 'total_amount'],
            'purchase_items': ['purchase_item_id', 'purchase_id', 'medicine_id', 'quantity', 'price'],
            'sale_items': ['sale_item_id', 'sale_id', 'medicine_id', 'quantity', 'price'],
            'app_users': ['user_id', 'username', 'role']
        }
        return db_columns.get(table_name, [])

    def is_foreign_key(self, table_name: str, column_name: str) -> bool:
        """Проверяет, является ли столбец внешним ключом"""
        if not column_name.endswith('_id'):
            return False

        ref_table = column_name[:-3]
        return ref_table in self._get_db_columns(table_name)

    def get_referenced_table(self, table_name: str, column_name: str) -> Optional[str]:
        """Возвращает имя таблицы, на которую ссылается внешний ключ"""
        if not column_name.endswith('_id'):
            return None

        ref_table = column_name[:-3]
        if ref_table in self._get_db_columns(table_name):
            return ref_table
        return None

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
            logging.info("Соединение с базой данных закрыто")
        except Exception as e:
            logging.error(f"Ошибка при закрытии соединения с БД: {e}")

            def get_simple_inventory_report(self):
                """Упрощенный отчет по остаткам"""
                query = """
                SELECT 
                    m.medicine_id as id,
                    m.name as medicine,
                    m.quantity_in_stock as stock,
                    s.name as supplier
                FROM medicines m
                LEFT JOIN suppliers s ON m.supplier_id = s.supplier_id
                WHERE m.quantity_in_stock < 50  # Показываем только малое количество
                ORDER BY m.quantity_in_stock ASC
                """
                return self.execute_query(query)


class DataValidator:
    @staticmethod
    def validate_email(email):
        if not email:  # Пустое значение допустимо
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone):
        if not phone:  # Пустое значение допустимо
            return True
        pattern = r'^\+?[0-9]{10,15}$'
        return re.match(pattern, phone) is not None

    @staticmethod
    def validate_date(date_str):
        if not date_str:  # Пустое значение допустимо
            return True
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_number(value, min_val=None, max_val=None):
        if not value:  # Пустое значение допустимо
            return True
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False


class InventoryManager:
    def __init__(self, db):
        self.db = db
        logging.info("Инициализация InventoryManager")

    def check_availability(self, medicine_id, quantity):
        try:
            query = "SELECT quantity_in_stock FROM medicines WHERE medicine_id = %s"
            result = self.db.execute_query(query, (medicine_id,))
            if not result:
                logging.warning(f"Лекарство с ID {medicine_id} не найдено")
                return False
            available = result[0][0] >= quantity
            logging.debug(
                f"Проверка наличия: ID {medicine_id}, нужно {quantity}, есть {result[0][0]}, результат: {available}")
            return available
        except Exception as e:
            logging.error(f"Ошибка проверки наличия лекарства {medicine_id}: {e}")
            return False

    def update_inventory(self, medicine_id, quantity_change):
        try:
            query = "SELECT quantity_in_stock FROM medicines WHERE medicine_id = %s"
            result = self.db.execute_query(query, (medicine_id,))
            if not result:
                logging.warning(f"Лекарство с ID {medicine_id} не найдено")
                return False

            current_quantity = result[0][0]
            new_quantity = current_quantity + quantity_change

            if new_quantity < 0:
                logging.warning(
                    f"Недостаточное количество для обновления: ID {medicine_id}, текущее {current_quantity}, изменение {quantity_change}")
                return False

            update_query = "UPDATE medicines SET quantity_in_stock = %s WHERE medicine_id = %s"
            success = self.db.execute_query(update_query, (new_quantity, medicine_id), fetch=False)
            logging.debug(f"Обновление запасов: ID {medicine_id}, изменение {quantity_change}, успех: {success}")
            return success
        except Exception as e:
            logging.error(f"Ошибка обновления запасов для лекарства {medicine_id}: {e}")
            return False


class Role(Enum):
    ADMIN = auto()
    PHARMACIST = auto()
    MANAGER = auto()
    GUEST = auto()


class User:
    def __init__(self, username: str, password_hash: str, role: Role):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.user_id = None
        logging.debug(f"Создан пользователь: {username}, роль: {role.name}")


class AuthSystem:
    def __init__(self, db):
        self.db = db
        self.current_user = None
        self._create_users_table()
        logging.info("Инициализация AuthSystem")

    def _create_users_table(self):
        try:
            query = """
            CREATE TABLE IF NOT EXISTS app_users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL
            )
            """
            self.db.execute_query(query, fetch=False)

            admin_query = "SELECT * FROM app_users WHERE username = 'admin'"
            if not self.db.execute_query(admin_query):
                self.register('admin', 'admin123', Role.ADMIN)
                logging.info("Создан администратор по умолчанию")
        except Exception as e:
            logging.error(f"Ошибка создания таблицы пользователей: {e}")

    def hash_password(self, password: str) -> str:
        return sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str, role: Role) -> bool:
        try:
            password_hash = self.hash_password(password)
            query = """
            INSERT INTO app_users (username, password_hash, role)
            VALUES (%s, %s, %s)
            """
            success = self.db.execute_query(
                query,
                (username, password_hash, role.name),
                fetch=False
            )
            logging.debug(f"Регистрация пользователя {username}, успех: {success}")
            return success
        except Exception as e:
            logging.error(f"Ошибка регистрации пользователя {username}: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        try:
            query = "SELECT user_id, password_hash, role FROM app_users WHERE username = %s"
            result = self.db.execute_query(query, (username,))
            if not result:
                logging.warning(f"Пользователь {username} не найден")
                return False

            user_id, stored_hash, role_name = result[0]
            password_hash = self.hash_password(password)

            if password_hash == stored_hash:
                self.current_user = User(username, password_hash, Role[role_name])
                self.current_user.user_id = user_id
                logging.info(f"Успешный вход пользователя {username}")
                return True
            else:
                logging.warning(f"Неверный пароль для пользователя {username}")
                return False
        except Exception as e:
            logging.error(f"Ошибка входа пользователя {username}: {e}")
            return False

    def logout(self):
        if self.current_user:
            logging.info(f"Выход пользователя {self.current_user.username}")
        self.current_user = None

    def has_permission(self, required_role: Role) -> bool:
        if not self.current_user:
            logging.debug("Проверка прав: нет текущего пользователя")
            return False
        result = self.current_user.role.value <= required_role.value
        logging.debug(
            f"Проверка прав для {self.current_user.username}: требуется {required_role.name}, есть {self.current_user.role.name}, результат: {result}")
        return result


class EditDialog:
    def __init__(self, parent, db, table_name, record_id=None):
        self.parent = parent
        self.db = db
        self.table_name = table_name

        # Проверка и преобразование record_id
        if record_id is not None:
            try:
                self.record_id = int(record_id)
                self.is_new = False
                logging.debug(f"Создание диалога редактирования для таблицы {table_name}, ID {record_id}")
            except (ValueError, TypeError):
                messagebox.showerror("Ошибка", "Некорректный ID записи")
                logging.error(f"Некорректный ID записи: {record_id}")
                return
        else:
            self.is_new = True
            self.record_id = None
            logging.debug(f"Создание диалога добавления для таблицы {table_name}")

        self.window = tk.Toplevel(parent)
        self.window.title(f"{'Добавить' if self.is_new else 'Редактировать'} запись")
        self.window.geometry("600x500")
        self.window.grab_set()

        self.fields = {}
        self.validation_rules = self._get_validation_rules()

        try:
            self._setup_ui()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании формы: {str(e)}")
            self.window.destroy()
            logging.error(f"Ошибка создания формы редактирования: {e}")

    def _get_validation_rules(self):
        return {
            'email': DataValidator.validate_email,
            'phone': DataValidator.validate_phone,
            'date': DataValidator.validate_date,
            'price': lambda x: DataValidator.validate_number(x, min_val=0),
            'quantity': lambda x: DataValidator.validate_number(x, min_val=0),
            'salary': lambda x: DataValidator.validate_number(x, min_val=0),
            'total_amount': lambda x: DataValidator.validate_number(x, min_val=0),
        }

    def _setup_ui(self):
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Получаем структуру таблицы
        columns = self.db.get_table_columns(self.table_name)
        if not columns:
            messagebox.showerror("Ошибка", f"Не удалось получить столбцы для таблицы {self.table_name}")
            self.window.destroy()
            return

        db_columns = self.db._get_db_columns(self.table_name)
        if not db_columns:
            messagebox.showerror("Ошибка", f"Не удалось получить столбцы БД для таблицы {self.table_name}")
            self.window.destroy()
            return

        # Получаем данные записи, если редактируем существующую
        record_data = {}
        if not self.is_new:
            record_data = self.db.get_record(self.table_name, self.record_id)
            if not record_data:
                messagebox.showerror("Ошибка",
                                     f"Не удалось загрузить данные записи.\nТаблица: {self.table_name}\nID: {self.record_id}")
                self.window.destroy()
                return
            logging.debug(f"Данные записи для редактирования: {record_data}")

        # Создаем форму
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, (label, db_col) in enumerate(zip(columns, db_columns)):
            frame = ttk.Frame(scrollable_frame)
            frame.grid(row=i, column=0, sticky="ew", padx=5, pady=5)

            ttk.Label(frame, text=f"{label}:").pack(side="left")

            validator = None
            for key in self.validation_rules:
                if key in db_col.lower():
                    validator = self.validation_rules[key]
                    break

            if db_col.endswith('_id') and db_col != f"{self.table_name}_id":
                # Это поле внешнего ключа - создаем выпадающий список
                ref_table = db_col[:-3]
                options = self._get_foreign_key_options(ref_table)

                var = tk.StringVar()
                combo = ttk.Combobox(frame, textvariable=var, values=options, state="readonly")
                combo.pack(side="left", fill="x", expand=True, padx=5)

                # Устанавливаем текущее значение, если оно есть
                if db_col in record_data and record_data[db_col]:
                    for option in options:
                        if option.startswith(f"{record_data[db_col]} - "):
                            var.set(option)
                            break
                    else:
                        var.set("")  # Если не нашли соответствие

                self.fields[db_col] = ('combobox', var, validator)
            elif 'date' in db_col.lower():
                # Поле с датой - добавляем специальную обработку
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side="left", fill="x", expand=True, padx=5)

                # Устанавливаем текущее значение, если оно есть
                if db_col in record_data and record_data[db_col]:
                    if isinstance(record_data[db_col], (date, datetime)):
                        var.set(record_data[db_col].strftime('%Y-%m-%d'))
                    else:
                        # Попробуем преобразовать строку в дату
                        try:
                            dt = datetime.strptime(str(record_data[db_col]), '%Y-%m-%d')
                            var.set(dt.strftime('%Y-%m-%d'))
                        except ValueError:
                            var.set(str(record_data[db_col]))

                self.fields[db_col] = ('entry', var, validator)
            else:
                # Обычное текстовое поле
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side="left", fill="x", expand=True, padx=5)

                # Устанавливаем текущее значение, если оно есть
                if db_col in record_data:
                    var.set(str(record_data[db_col]) if record_data[db_col] is not None else "")

                self.fields[db_col] = ('entry', var, validator)

            if validator:
                ttk.Label(frame, text="*", foreground="red").pack(side="left")

        # Кнопки сохранения/отмены
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self._save_data,
            style='Accent.TButton'
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.window.destroy
        ).pack(side="right", padx=5)

    def _get_foreign_key_options(self, ref_table):
        """Получает варианты для выпадающего списка внешнего ключа"""
        try:
            logging.debug(f"Получение вариантов для внешнего ключа таблицы {ref_table}")

            if ref_table == 'customer':
                query = "SELECT customer_id, first_name || ' ' || last_name FROM customers ORDER BY first_name"
            elif ref_table == 'employee':
                query = "SELECT employee_id, first_name || ' ' || last_name FROM employees ORDER BY first_name"
            elif ref_table == 'supplier':
                query = """
                SELECT s.supplier_id, s.name || ' (Тел: ' || COALESCE(s.phone, 'нет') || ')' 
                FROM suppliers s
                ORDER BY s.name
                """
            elif ref_table == 'medicine':
                query = "SELECT medicine_id, name FROM medicines ORDER BY name"
            elif ref_table == 'purchase':
                query = "SELECT purchase_id, purchase_date FROM purchases ORDER BY purchase_date"
            elif ref_table == 'sale':
                query = "SELECT sale_id, sale_date FROM sales ORDER BY sale_date"
            else:
                query = f"SELECT {ref_table}_id, {ref_table}_name FROM {ref_table}s ORDER BY {ref_table}_name"

            result = self.db.execute_query(query)
            options = [f"{row[0]} - {row[1]}" for row in result] if result else []
            logging.debug(f"Получено {len(options)} вариантов для {ref_table}")
            return options
        except Exception as e:
            logging.error(f"Ошибка получения вариантов для внешнего ключа {ref_table}: {e}")
            return []

    def _save_data(self):
        """Сохраняет данные в базу"""
        errors = []
        data = {}
        for field, (field_type, var, validator) in self.fields.items():
            value = var.get().strip()

            # Пропускаем первичный ключ при добавлении новой записи
            if field == self.db._get_db_columns(self.table_name)[0] and self.is_new:
                continue

            # Проверяем обязательные поля
            if validator and not value:
                errors.append(f"Поле {field} обязательно для заполнения")
                continue

            # Проверяем валидацию
            if validator and not validator(value):
                errors.append(f"Некорректное значение для поля {field}")
                continue

            # Для combobox берем только ID (первая часть значения)
            if field_type == 'combobox':
                value = value.split(' - ')[0] if value else None

            # Для дат проверяем формат
            if 'date' in field.lower() and value:
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Некорректный формат даты для поля {field}. Используйте ГГГГ-ММ-ДД")
                    continue

            data[field] = value if value else None

        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return

        try:
            if self.is_new:
                # Добавляем новую запись (исключаем первичный ключ)
                columns = [col for col in data.keys() if col != self.db._get_db_columns(self.table_name)[0]]
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(self.table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join([sql.Placeholder()] * len(columns))
                )
                params = tuple(data[col] for col in columns)
            else:
                # Обновляем существующую запись
                id_column = self.db._get_db_columns(self.table_name)[0]
                set_clause = sql.SQL(', ').join(
                    sql.Composed([sql.Identifier(k), sql.SQL(' = '), sql.Placeholder()])
                    for k in data.keys() if k != id_column
                )
                query = sql.SQL("UPDATE {} SET {} WHERE {} = {}").format(
                    sql.Identifier(self.table_name),
                    set_clause,
                    sql.Identifier(id_column),
                    sql.Placeholder()
                )
                params = tuple(v for k, v in data.items() if k != id_column) + (self.record_id,)

            logging.debug(f"Запрос: {query.as_string(self.db.conn)} с параметрами: {params}")

            if self.db.execute_query(query, params, fetch=False):
                messagebox.showinfo("Успех", "Данные успешно сохранены")
                self.window.destroy()
                if hasattr(self.parent, 'refresh_table'):
                    self.parent.refresh_table()
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить данные")

        except Exception as e:
            logging.error(f"Ошибка сохранения данных: {e}")
            messagebox.showerror("Ошибка базы данных", f"Ошибка при сохранении: {str(e)}")


class PharmacyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Аптечная база данных")
        self.root.geometry("1200x700")
        logging.info("Запуск приложения PharmacyApp")

        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('Accent.TButton', foreground='white', background='#4a6baf')
        self.style.configure('TEntry', font=('Arial', 10), padding=5)
        self.style.configure('Treeview', font=('Arial', 10), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
        self.style.map('Treeview',
                       background=[('selected', '#4a6baf')],
                       foreground=[('selected', 'white')])

        try:
            self.db = Database()
            self.auth = AuthSystem(self.db)
            self.inventory_manager = InventoryManager(self.db)
            self._setup_ui()
        except Exception as e:
            logging.critical(f"Ошибка инициализации приложения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить приложение: {e}")
            self.root.destroy()

    def _setup_ui(self):
        self.menu_bar = tk.Menu(self.root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Выход", command=self.root.quit)
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)

        self.tables_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Таблицы", menu=self.tables_menu)

        self.user_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.user_menu.add_command(label="Войти", command=self.show_login)
        self.user_menu.add_command(label="Выйти", command=self.logout)
        self.menu_bar.add_cascade(label="Пользователь", menu=self.user_menu)

        self.reports_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.reports_menu.add_command(
            label="Простые остатки",
            command=self.show_simple_report
        )
        self.reports_menu.add_command(label="Будущие поставки", command=self.show_future_deliveries)
        self.reports_menu.add_command(label="Продажи за 30 дней", command=self.show_last_30days_sales)
        self.reports_menu.add_command(label="Статистика расхода", command=self.show_consumption_stats)
        self.menu_bar.add_cascade(label="Отчёты", menu=self.reports_menu)


        self.root.config(menu=self.menu_bar)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X)

        self.update_status()
        self.update_menu_state()
        self.root.config(menu=self.menu_bar)

    def update_status(self):
        if self.auth.current_user:
            status = f"Пользователь: {self.auth.current_user.username} | Роль: {self.auth.current_user.role.name}"
        else:
            status = "Гостевой режим"
        self.status_var.set(status)
        logging.debug(f"Обновление статуса: {status}")

    def update_menu_state(self):
        self.tables_menu.delete(0, tk.END)
        tables = [
            ('customers', 'Клиенты'),
            ('employees', 'Сотрудники'),
            ('suppliers', 'Поставщики'),
            ('medicines', 'Лекарства'),
            ('prescriptions', 'Рецепты'),
            ('purchases', 'Закупки'),
            ('sales', 'Продажи'),
            ('purchase_items', 'Позиции закупок'),
            ('sale_items', 'Позиции продаж')
        ]

        for table, label in tables:
            if self._check_table_access(table):
                self.tables_menu.add_command(
                    label=label,
                    command=lambda t=table: self.show_table(t)
                )

        self.user_menu.entryconfig("Войти", state=tk.NORMAL if not self.auth.current_user else tk.DISABLED)
        self.user_menu.entryconfig("Выйти", state=tk.NORMAL if self.auth.current_user else tk.DISABLED)

        # Показываем/скрываем меню отчетов
        if self.reports_menu:
            if self.auth.current_user and self.auth.current_user.role in [Role.ADMIN, Role.PHARMACIST, Role.MANAGER]:
                self.menu_bar.add_cascade(label="Отчёты", menu=self.reports_menu)
            else:
                self.menu_bar.delete("Отчёты")

        if self.auth.current_user and self.auth.current_user.role == Role.ADMIN:
            if hasattr(self, 'admin_menu'):
                self.menu_bar.delete(self.admin_menu)
            self.admin_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.admin_menu.add_command(label="Управление пользователями",
                                        command=self.show_user_management)
            self.menu_bar.add_cascade(label="Администрирование", menu=self.admin_menu)

        logging.debug("Обновлено состояние меню")

    def _check_table_access(self, table_name: str) -> bool:
        if not self.auth.current_user:
            return table_name == 'medicines'

        access_rules = {
            Role.ADMIN: [
                'customers', 'employees', 'suppliers', 'medicines',
                'prescriptions', 'purchases', 'sales',
                'purchase_items', 'sale_items', 'app_users'
            ],
            Role.PHARMACIST: [
                'customers', 'medicines', 'prescriptions', 'sales', 'sale_items'
            ],
            Role.MANAGER: [
                'suppliers', 'medicines', 'purchases', 'purchase_items'
            ],
            Role.GUEST: [
                'medicines'
            ]
        }

        return table_name in access_rules.get(self.auth.current_user.role, [])

    def show_login(self):
        login_window = tk.Toplevel(self.root)
        login_window.title("Вход в систему")

        ttk.Label(login_window, text="Логин:").grid(row=0, column=0, padx=5, pady=5)
        login_entry = ttk.Entry(login_window)
        login_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(login_window, text="Пароль:").grid(row=1, column=0, padx=5, pady=5)
        password_entry = ttk.Entry(login_window, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        def perform_login():
            username = login_entry.get()
            password = password_entry.get()

            if self.auth.login(username, password):
                messagebox.showinfo("Успех", "Вы успешно вошли в систему")
                login_window.destroy()
                self.update_status()
                self.update_menu_state()
            else:
                messagebox.showerror("Ошибка", "Неверный логин или пароль")

        ttk.Button(
            login_window,
            text="Войти",
            command=perform_login
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def logout(self):
        self.auth.logout()
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.update_status()
        self.update_menu_state()
        messagebox.showinfo("Выход", "Вы вышли из системы")

    def show_user_management(self):
        if not self.auth.current_user or self.auth.current_user.role != Role.ADMIN:
            messagebox.showerror("Ошибка", "Только администратор может управлять пользователями")
            return

        user_window = tk.Toplevel(self.root)
        user_window.title("Управление пользователями")
        user_window.geometry("500x400")

        tree_frame = ttk.Frame(user_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ["ID", "Логин", "Роль"]
        self.users_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscroll=scrollbar.set)

        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_users_table()

        form_frame = ttk.Frame(user_window)
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(form_frame, text="Логин:").grid(row=0, column=0, padx=5, pady=5)
        username_entry = ttk.Entry(form_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Пароль:").grid(row=1, column=0, padx=5, pady=5)
        password_entry = ttk.Entry(form_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Роль:").grid(row=2, column=0, padx=5, pady=5)
        role_var = tk.StringVar()
        role_combo = ttk.Combobox(form_frame, textvariable=role_var,
                                  values=["ADMIN", "PHARMACIST", "MANAGER", "GUEST"])
        role_combo.grid(row=2, column=1, padx=5, pady=5)
        role_combo.current(1)

        button_frame = ttk.Frame(user_window)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            button_frame,
            text="Добавить пользователя",
            command=lambda: self.add_user(username_entry, password_entry, role_var)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Удалить пользователя",
            command=self.delete_user
        ).pack(side=tk.LEFT, padx=5)

    def add_user(self, username_entry, password_entry, role_var):
        username = username_entry.get()
        password = password_entry.get()
        role = role_var.get()

        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        if self.auth.register(username, password, Role[role]):
            messagebox.showinfo("Успех", "Пользователь создан")
            self.refresh_users_table()
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Ошибка", "Не удалось создать пользователя")

    def delete_user(self):
        selected_items = self.users_tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
            return

        user_id = self.users_tree.item(selected_items[0])['values'][0]

        if str(user_id) == str(self.auth.current_user.user_id):
            messagebox.showerror("Ошибка", "Нельзя удалить текущего пользователя")
            return

        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Вы уверены, что хотите удалить пользователя?",
            icon='warning'
        )

        if confirm:
            query = "DELETE FROM app_users WHERE user_id = %s"
            if self.db.execute_query(query, (user_id,), fetch=False):
                messagebox.showinfo("Успех", "Пользователь удален")
                self.refresh_users_table()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить пользователя")

    def refresh_users_table(self):
        if hasattr(self, 'users_tree'):
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            users = self.db.execute_query("SELECT user_id, username, role FROM app_users")
            for user in users:
                self.users_tree.insert('', tk.END, values=user)

    def show_table(self, table_name: str):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        try:
            data = self.db.get_table_data(table_name)
            columns = self.db.get_table_columns(table_name)
            db_columns = self.db._get_db_columns(table_name)

            if not data or not columns or not db_columns:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные таблицы {table_name}")
                return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            return

        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(search_frame, textvariable=filter_var, values=columns)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.current(0)

        tree = ttk.Treeview(self.main_frame, columns=columns, show='headings')
        tree._table_name = table_name  # Сохраняем имя таблицы для обновления

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.W)

        self._table_data = data
        self._table_columns = columns
        self._db_columns = db_columns

        for row in data:
            tree.insert('', tk.END, values=[row[col] for col in row])

        def perform_search(*args):
            search_term = search_entry.get().lower()
            selected_col = filter_var.get()

            if not search_term:
                for item in tree.get_children():
                    tree.delete(item)
                for row in self._table_data:
                    tree.insert('', tk.END, values=[row[col] for col in row])
                return

            try:
                col_index = self._table_columns.index(selected_col)
                db_col = self._db_columns[col_index]
            except (ValueError, IndexError):
                db_col = selected_col

            filtered_data = [
                row for row in self._table_data
                if str(row.get(db_col, '')).lower().find(search_term) >= 0
            ]

            for item in tree.get_children():
                tree.delete(item)

            for row in filtered_data:
                tree.insert('', tk.END, values=[row[col] for col in row])

        search_entry.bind('<KeyRelease>', perform_search)

        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if self.auth.current_user and self.auth.current_user.role != Role.GUEST:
            button_frame = ttk.Frame(self.main_frame)
            button_frame.pack(fill=tk.X, pady=5)

            if table_name in ['customers', 'employees', 'suppliers', 'medicines', 'prescriptions', 'purchases',
                              'sales']:
                ttk.Button(
                    button_frame,
                    text="Добавить",
                    command=lambda: self.show_add_dialog(table_name)
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Редактировать",
                    command=lambda: self.show_edit_dialog(table_name, tree)
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Удалить",
                    command=lambda: self.delete_record(table_name, tree)
                ).pack(side=tk.LEFT, padx=5)

            if table_name == 'sales':
                ttk.Button(
                    button_frame,
                    text="Детали продажи",
                    command=lambda: self.show_sale_details(tree),
                    style='Accent.TButton'
                ).pack(side=tk.LEFT, padx=5)

    def show_add_dialog(self, table_name: str):
        if table_name == 'sales':
            self.show_add_sale_dialog()
        else:
            self.show_edit_dialog(table_name)

    def show_add_sale_dialog(self):
        sale_window = tk.Toplevel(self.root)
        sale_window.title("Добавить новую продажу")
        sale_window.geometry("800x600")

        # Выбор клиента
        ttk.Label(sale_window, text="Клиент:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        customers = self.db.get_customers_list()
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(sale_window, textvariable=customer_var,
                                      values=[f"{c[0]} - {c[1]}" for c in customers])
        customer_combo.grid(row=0, column=1, padx=5, pady=5, sticky='we')
        if customers:
            customer_combo.current(0)

        # Выбор сотрудника
        ttk.Label(sale_window, text="Сотрудник:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        employees = self.db.get_employees_list()
        employee_var = tk.StringVar()
        employee_combo = ttk.Combobox(sale_window, textvariable=employee_var,
                                      values=[f"{e[0]} - {e[1]}" for e in employees])
        employee_combo.grid(row=1, column=1, padx=5, pady=5, sticky='we')
        if employees:
            employee_combo.current(0)

        # Таблица с выбранными лекарствами
        ttk.Label(sale_window, text="Лекарства в продаже:").grid(row=2, column=0, columnspan=2, pady=5)

        tree_frame = ttk.Frame(sale_window)
        tree_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        columns = ["ID", "Название", "Количество", "Цена", "Сумма"]
        self.sale_items_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=5)

        for col in columns:
            self.sale_items_tree.heading(col, text=col)
            self.sale_items_tree.column(col, width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.sale_items_tree.yview)
        self.sale_items_tree.configure(yscroll=scrollbar.set)

        self.sale_items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки для работы с лекарствами
        medicine_buttons_frame = ttk.Frame(sale_window)
        medicine_buttons_frame.grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Button(
            medicine_buttons_frame,
            text="Добавить лекарство",
            command=lambda: self.add_medicine_to_sale(sale_window),
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            medicine_buttons_frame,
            text="Удалить лекарство",
            command=self.remove_medicine_from_sale
        ).pack(side=tk.LEFT, padx=5)

        # Общая сумма
        total_label = ttk.Label(sale_window, text="0.00")
        total_label.grid(row=5, column=1, padx=5, pady=5, sticky='w')
        ttk.Label(sale_window, text="Общая сумма:").grid(row=5, column=0, padx=5, pady=5, sticky='e')

        # Кнопки сохранения/отмены
        button_frame = ttk.Frame(sale_window)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame,
            text="Сохранить продажу",
            command=lambda: self.save_sale(customer_var, employee_var, total_label, sale_window),
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=sale_window.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Обновление общей суммы при изменении состава продажи
        def update_total():
            total = 0.0
            for child in self.sale_items_tree.get_children():
                values = self.sale_items_tree.item(child)['values']
                total += float(values[4])  # Сумма за позицию
            total_label.config(text=f"{total:.2f}")

        self.sale_items_tree.bind('<<TreeviewSelect>>', lambda e: update_total())
        self.sale_items_tree.bind('<ButtonRelease-1>', lambda e: update_total())
        self.sale_items_tree.bind('<KeyRelease>', lambda e: update_total())

    def add_medicine_to_sale(self, parent_window):
        add_window = tk.Toplevel(parent_window)
        add_window.title("Добавить лекарство")
        add_window.geometry("400x300")

        medicines = self.db.get_medicines_list()
        if not medicines:
            messagebox.showwarning("Предупреждение", "Нет доступных лекарств")
            add_window.destroy()
            return

        ttk.Label(add_window, text="Лекарство:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        medicine_var = tk.StringVar()
        medicine_combo = ttk.Combobox(add_window, textvariable=medicine_var,
                                      values=[f"{m[0]} - {m[1]} (Цена: {m[2]} руб., Остаток: {m[3]})" for m in
                                              medicines])
        medicine_combo.grid(row=0, column=1, padx=5, pady=5, sticky='we')
        medicine_combo.current(0)

        ttk.Label(add_window, text="Количество:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        quantity_var = tk.StringVar(value="1")
        quantity_entry = ttk.Entry(add_window, textvariable=quantity_var)
        quantity_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')

        def add_to_sale():
            try:
                medicine_id = int(medicine_var.get().split(' - ')[0])
                medicine_name = medicines[[m[0] for m in medicines].index(medicine_id)][1]
                price = medicines[[m[0] for m in medicines].index(medicine_id)][2]
                quantity = int(quantity_var.get())
                available = medicines[[m[0] for m in medicines].index(medicine_id)][3]

                if quantity <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть положительным")
                    return

                if quantity > available:
                    messagebox.showerror("Ошибка", "Недостаточное количество на складе")
                    return

                # Проверяем, не добавлено ли уже это лекарство
                for child in self.sale_items_tree.get_children():
                    if self.sale_items_tree.item(child)['values'][0] == medicine_id:
                        messagebox.showerror("Ошибка", "Это лекарство уже добавлено в продажу")
                        return

                total = price * quantity
                self.sale_items_tree.insert('', tk.END, values=(
                    medicine_id, medicine_name, quantity, price, total
                ))

                # Обновляем общую сумму
                self.update_sale_total(parent_window)
                add_window.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректные данные")

        ttk.Button(
            add_window,
            text="Добавить",
            command=add_to_sale,
            style='Accent.TButton'
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def remove_medicine_from_sale(self):
        selected_items = self.sale_items_tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите лекарство для удаления")
            return

        for item in selected_items:
            self.sale_items_tree.delete(item)

    def update_sale_total(self, sale_window):
        """Обновляет общую сумму в окне создания продажи"""
        total = 0.0
        for child in self.sale_items_tree.get_children():
            values = self.sale_items_tree.item(child)['values']
            total += float(values[4])  # Сумма за позицию

        # Находим виджет с общей суммой в окне продажи
        for widget in sale_window.winfo_children():
            if isinstance(widget, ttk.Label) and widget.grid_info()['row'] == 5 and widget.grid_info()['column'] == 1:
                widget.config(text=f"{total:.2f}")
                break

    def save_sale(self, customer_var, employee_var, total_label, sale_window):
        selected_items = list(self.sale_items_tree.get_children())
        if not selected_items:
            messagebox.showerror("Ошибка", "Добавьте хотя бы одно лекарство в продажу")
            return

        try:
            customer_id = int(customer_var.get().split(' - ')[0])
            employee_id = int(employee_var.get().split(' - ')[0])
            total_amount = float(total_label.cget("text"))
        except (ValueError, AttributeError):
            messagebox.showerror("Ошибка", "Некорректные данные клиента или сотрудника")
            return

        # Создаем запись о продаже
        query = """
        INSERT INTO sales (sale_date, customer_id, employee_id, total_amount)
        VALUES (CURRENT_TIMESTAMP, %s, %s, %s)
        RETURNING sale_id
        """
        result = self.db.execute_query(query, (customer_id, employee_id, total_amount), return_id=True)
        if not result:
            messagebox.showerror("Ошибка", "Не удалось создать продажу")
            return

        sale_id = result[0]

        # Добавляем товары в продажу
        for item in selected_items:
            values = self.sale_items_tree.item(item)['values']
            medicine_id = values[0]
            quantity = values[2]
            price = values[3]

            # Проверяем доступность
            if not self.inventory_manager.check_availability(medicine_id, quantity):
                messagebox.showerror("Ошибка",
                                     f"Недостаточно {self.sale_items_tree.item(item)['values'][1]} на складе")
                # Откатываем продажу
                self.db.execute_query("DELETE FROM sales WHERE sale_id = %s", (sale_id,), fetch=False)
                return

            # Добавляем позицию
            item_query = """
            INSERT INTO sale_items (sale_id, medicine_id, quantity, price)
            VALUES (%s, %s, %s, %s)
            """
            if not self.db.execute_query(item_query, (sale_id, medicine_id, quantity, price), fetch=False):
                messagebox.showerror("Ошибка", "Не удалось добавить товары в продажу")
                # Откатываем продажу
                self.db.execute_query("DELETE FROM sales WHERE sale_id = %s", (sale_id,), fetch=False)
                return

            # Обновляем остатки
            if not self.inventory_manager.update_inventory(medicine_id, -quantity):
                messagebox.showerror("Ошибка", "Не удалось обновить остатки")
                # Откатываем продажу
                self.db.execute_query("DELETE FROM sales WHERE sale_id = %s", (sale_id,), fetch=False)
                return

        messagebox.showinfo("Успех", "Продажа успешно создана")
        sale_window.destroy()
        self.show_table('sales')

    def show_sale_details(self, tree):
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите продажу")
            return

        sale_id = tree.item(selected_items[0])['values'][0]
        items, sale_info = self.db.get_sale_details(sale_id)

        if not sale_info:
            messagebox.showerror("Ошибка", "Не удалось загрузить данные о продаже")
            return

        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали продажи #{sale_id}")
        details_window.geometry("900x600")

        bold_font = ('Arial', 10, 'bold')
        header_font = ('Arial', 11, 'bold')

        info_frame = ttk.Frame(details_window, padding=10)
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="Информация о продаже:", font=header_font).grid(row=0, column=0, sticky='w',
                                                                                   columnspan=2)
        ttk.Label(info_frame, text=f"Номер продажи:", font=bold_font).grid(row=1, column=0, sticky='w')
        ttk.Label(info_frame, text=sale_info['sale_id']).grid(row=1, column=1, sticky='w')

        ttk.Label(info_frame, text="Дата:", font=bold_font).grid(row=2, column=0, sticky='w')
        ttk.Label(info_frame, text=sale_info['sale_date']).grid(row=2, column=1, sticky='w')

        ttk.Label(info_frame, text="Клиент:", font=bold_font).grid(row=3, column=0, sticky='w')
        ttk.Label(info_frame, text=sale_info['customer']).grid(row=3, column=1, sticky='w')

        ttk.Label(info_frame, text="Сотрудник:", font=bold_font).grid(row=4, column=0, sticky='w')
        ttk.Label(info_frame, text=sale_info['employee']).grid(row=4, column=1, sticky='w')

        ttk.Label(info_frame, text="Общая сумма:", font=bold_font).grid(row=5, column=0, sticky='w')
        ttk.Label(info_frame, text=f"{sale_info['total_amount']} руб.").grid(row=5, column=1, sticky='w')

        ttk.Label(details_window, text="Список товаров:", font=header_font, padding=10).pack()

        tree_frame = ttk.Frame(details_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ["Лекарство", "Код", "Кол-во", "Цена", "Сумма"]
        details_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)

        for col in columns:
            details_tree.heading(col, text=col)
            details_tree.column(col, width=120, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=details_tree.yview)
        details_tree.configure(yscroll=scrollbar.set)

        details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for item in items:
            details_tree.insert('', tk.END, values=(
                item['name'],
                item['medicine_id'],
                item['quantity'],
                f"{item['price']} руб.",
                f"{item['total']} руб."
            ))

        total_frame = ttk.Frame(details_window, padding=10)
        total_frame.pack(fill=tk.X)

        total_items = sum(item['quantity'] for item in items)
        ttk.Label(total_frame,
                  text=f"Итого: {len(items)} наименований, {total_items} шт. на сумму {sale_info['total_amount']} руб.",
                  font=bold_font).pack()

    def show_edit_dialog(self, table_name: str, tree=None):
        if not tree:
            # Создание новой записи
            EditDialog(self.root, self.db, table_name)
            return

        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Ошибка", "Выберите запись для редактирования")
            return

        record_id = tree.item(selected_items[0])['values'][0]
        EditDialog(self.root, self.db, table_name, record_id)

    def refresh_table(self):
        """Обновляет текущую открытую таблицу"""
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Treeview):
                table_name = getattr(widget, '_table_name', None)
                if table_name:
                    # Сохраняем позицию прокрутки
                    scroll_pos = widget.yview()

                    # Обновляем данные
                    self.show_table(table_name)

                    # Восстанавливаем позицию прокрутки
                    for w in self.main_frame.winfo_children():
                        if isinstance(w, ttk.Treeview) and getattr(w, '_table_name', None) == table_name:
                            w.yview_moveto(scroll_pos[0])
                            break
                    break

    def delete_record(self, table_name: str, tree):
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите записи для удаления")
            return

        items_info = []
        dependencies = {
            'sales': [('sale_items', 'sale_id')],
            'purchases': [('purchase_items', 'purchase_id')],
            'customers': [
                ('prescriptions', 'customer_id'),
                ('sales', 'customer_id')
            ],
            'medicines': [
                ('prescriptions', 'medicine_id'),
                ('sale_items', 'medicine_id'),
                ('purchase_items', 'medicine_id')
            ]
        }

        # Проверяем зависимости перед удалением
        dependent_records = {}
        for item in selected_items:
            values = tree.item(item)['values']
            record_id = values[0]
            items_info.append(f"{record_id} - {values[1] if len(values) > 1 else ''}")

            # Проверяем все зависимости для данной таблицы
            for dep_table, dep_column in dependencies.get(table_name, []):
                check_query = f"""
                SELECT COUNT(*) FROM {dep_table} WHERE {dep_column} = %s
                """
                result = self.db.execute_query(check_query, (record_id,))
                if result and result[0][0] > 0:
                    if record_id not in dependent_records:
                        dependent_records[record_id] = []
                    dependent_records[record_id].append((dep_table, result[0][0]))

        # Если есть зависимые записи
        if dependent_records:
            message = "Некоторые записи имеют связанные данные:\n\n"
            for record_id, deps in dependent_records.items():
                message += f"Запись ID {record_id}:\n"
                for dep_table, count in deps:
                    message += f"- {count} записей в таблице {dep_table}\n"
                message += "\n"

            message += "Вы хотите:\n"
            message += "1. Удалить ВСЕ связанные записи вместе с основной записью\n"
            message += "2. Отменить операцию удаления"

            choice = messagebox.askquestion(
                "Подтверждение удаления",
                message,
                icon='warning'
            )

            if choice != 'yes':
                messagebox.showinfo("Отмена", "Операция удаления отменена")
                return

        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить следующие записи?\n" +
            "\n".join(items_info),
            icon='warning'
        )

        if confirm:
            success = True
            for item in selected_items:
                item_values = tree.item(item)['values']
                record_id = item_values[0]

                try:
                    # Удаляем зависимые записи, если пользователь согласился
                    if record_id in dependent_records:
                        for dep_table, _ in dependent_records[record_id]:
                            dep_column = [col for col in dependencies[table_name] if col[0] == dep_table][0][1]
                            delete_dep_query = f"DELETE FROM {dep_table} WHERE {dep_column} = %s"
                            self.db.execute_query(delete_dep_query, (record_id,), fetch=False)

                    # Теперь удаляем основную запись
                    pk_column = self.db._get_db_columns(table_name)[0]
                    delete_main_query = f"DELETE FROM {table_name} WHERE {pk_column} = %s"
                    if not self.db.execute_query(delete_main_query, (record_id,), fetch=False):
                        success = False

                except Exception as e:
                    logging.error(f"Ошибка при удалении записи ID {record_id} из таблицы {table_name}: {e}")
                    success = False

            if success:
                messagebox.showinfo("Успех", "Записи и связанные данные успешно удалены")
                self.show_table(table_name)
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить некоторые записи")

    def add_reports_menu(self):
        """Добавляет меню отчетов самым простым способом"""
        self.reports_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.reports_menu.add_command(
            label="Простые остатки",
            command=self.show_simple_report
        )
        self.menu_bar.add_cascade(label="Отчёты", menu=self.reports_menu)

    def show_simple_report(self):
        """Показывает упрощенный отчет"""
        if not self.auth.current_user or self.auth.current_user.role not in [Role.ADMIN, Role.PHARMACIST, Role.MANAGER]:
            messagebox.showerror("Ошибка доступа",
                                 "Только администраторы, фармацевты и менеджеры могут просматривать отчеты")
            return
        self._show_generic_report(
            title="Простые остатки",
            query_func=self.db.get_simple_inventory_report,
            columns=['ID', 'Лекарство', 'Остаток', 'Поставщик'],
            column_widths=[50, 250, 80, 150]
        )

    def show_future_deliveries(self):
        """Отчет по будущим поставкам"""
        if not self.auth.current_user or self.auth.current_user.role not in [Role.ADMIN, Role.PHARMACIST, Role.MANAGER]:
            messagebox.showerror("Ошибка доступа",
                                 "Только администраторы, фармацевты и менеджеры могут просматривать отчеты")
            return
        self._show_generic_report(
            title="Будущие поставки",
            query_func=self.db.get_future_deliveries,
            columns=['ID', 'Дата', 'Поставщик', 'Лекарство', 'Кол-во', 'Цена'],
            column_widths=[50, 120, 150, 200, 80, 80]
        )

    def show_last_30days_sales(self):
        """Отчет по продажам"""
        if not self.auth.current_user or self.auth.current_user.role not in [Role.ADMIN, Role.PHARMACIST, Role.MANAGER]:
            messagebox.showerror("Ошибка доступа",
                                 "Только администраторы, фармацевты и менеджеры могут просматривать отчеты")
            return
        self._show_generic_report(
            title="Продажи за 30 дней",
            query_func=self.db.get_last_30days_sales,
            columns=['ID', 'Дата', 'Лекарство', 'Кол-во', 'Цена'],
            column_widths=[50, 120, 250, 80, 80]
        )

    def show_consumption_stats(self):
        """Отчет по расходу"""
        if not self.auth.current_user or self.auth.current_user.role not in [Role.ADMIN, Role.PHARMACIST, Role.MANAGER]:
            messagebox.showerror("Ошибка доступа",
                                 "Только администраторы, фармацевты и менеджеры могут просматривать отчеты")
            return
        self._show_generic_report(
            title="Статистика расхода",
            query_func=self.db.get_consumption_stats,
            columns=['ID', 'Лекарство', 'Продано', 'Ср. расход/день', 'Остаток'],
            column_widths=[50, 250, 80, 120, 80]
        )

    def _show_generic_report(self, title, query_func, columns, column_widths):
        """Универсальный метод для отображения отчетов"""

        # Проверка прав доступа
        if not self.auth.current_user or self.auth.current_user.role not in [Role.ADMIN, Role.PHARMACIST, Role.MANAGER]:
            messagebox.showerror("Ошибка доступа",
                                 "Только администраторы, фармацевты и менеджеры могут просматривать отчеты")
            logging.warning(f"Попытка доступа к отчету {title} без прав")
            return

        try:
            data = query_func()
            if not data:
                messagebox.showinfo("Информация", "Нет данных для отчета")
                return

            report_win = tk.Toplevel(self.root)
            report_win.title(title)
            report_win.geometry("1000x600")

            # Создаем Treeview
            tree = ttk.Treeview(report_win, columns=columns, show='headings')

            # Настраиваем колонки
            for col, width in zip(columns, column_widths):
                tree.heading(col, text=col)
                tree.column(col, width=width, anchor='center')

            # Заполняем данными
            for row in data:
                tree.insert('', 'end', values=[row.get(col.lower(), '') if isinstance(row, dict) else row[i]
                                               for i, col in enumerate(columns)])

            # Добавляем прокрутку
            scrollbar = ttk.Scrollbar(report_win, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            # Упаковываем
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Кнопка экспорта
            btn_export = ttk.Button(
                report_win,
                text="Экспорт в CSV",
                command=lambda: self._export_to_csv(data, title),
                style='Accent.TButton'
            )
            btn_export.pack(pady=5)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить отчет:\n{str(e)}")
            logging.error(f"Ошибка отчета {title}: {e}")

    def _export_to_csv(self, data, report_name):
        """Улучшенный экспорт в CSV"""
        from csv import writer
        from datetime import datetime
        import os

        if not data:
            messagebox.showwarning("Ошибка", "Нет данных для экспорта")
            return

        # Создаем имя файла
        filename = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                csv_writer = writer(f)

                # Заголовки (берём ключи первого элемента или индексы)
                if isinstance(data[0], dict):
                    csv_writer.writerow(data[0].keys())
                else:
                    csv_writer.writerow([f"Column_{i}" for i in range(len(data[0]))])

                # Данные
                for row in data:
                    if isinstance(row, dict):
                        csv_writer.writerow(row.values())
                    else:
                        csv_writer.writerow(row)

            messagebox.showinfo("Успех", f"Отчёт сохранён как:\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PharmacyApp(root)
    root.mainloop()