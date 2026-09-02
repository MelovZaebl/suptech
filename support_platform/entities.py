from datetime import datetime


# Базовый класс для всех участников платформы (операторы и пользователи).
# Хранит ФИО, город, дату рождения и автоматически генерируемый ID.
class Person:
    def __init__(self, full_name, city, birth_date, person_id=None):
        self.person_id = person_id  # Присваивается платформой при добавлении
        self.full_name = full_name
        self.city = city
        self.birth_date = birth_date

    @property
    def age(self):
        """Вычисляет текущий возраст по дате рождения."""
        today = datetime.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def to_dict(self):
        """Сериализация в словарь для JSON-экспорта."""
        return {
            "id": self.person_id,
            "full_name": self.full_name,
            "city": self.city,
            "birth_date": self.birth_date.strftime("%Y-%m-%d"),
            "age": self.age,
        }

    def __repr__(self):
        return f"<{type(self).__name__} {self.person_id} {self.full_name}>"


# Оператор поддержки. Расширяет Person: хранит должность, стаж,
# множество текущих открытых чатов и историю закрытых.
class Operator(Person):
    def __init__(self, full_name, city, birth_date, position, experience_years,
                 person_id=None):
        super().__init__(full_name, city, birth_date, person_id)
        self.position = position          # "Младший специалист" или "Старший специалист"
        self.experience_years = experience_years
        self.open_chats = set()           # ID чатов, которые оператор сейчас ведёт
        self.served_chat_ids = []         # ID всех чатов, которые оператор когда-либо закрыл

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "position": self.position,
            "experience_years": self.experience_years,
        })
        return data

    @property
    def is_free(self):
        """Оператор свободен, если у него нет активных чатов (макс. 1)."""
        return not self.open_chats

    def take_chat(self, chat_id):
        """Назначить чат оператору (добавить в текущие)."""
        self.open_chats.add(chat_id)

    def release_chat(self, chat_id):
        """Освободить оператора после закрытия чата (переместить в историю)."""
        self.open_chats.discard(chat_id)
        self.served_chat_ids.append(chat_id)


# Пользователь платформы. Наследует Person без изменений.
class User(Person):
    pass


# Модель чата поддержки. Хранит всё состояние:
# статус (open/closed), оператора, сообщения, оценку CSAT.
class Chat:
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    def __init__(self, chat_id, user, operator, topic, created_at,
                 first_message=None):
        self.chat_id = chat_id
        self.user = user                   # Пользователь, создавший чат
        self.operator = operator           # Оператор (или None, если чат в очереди)
        self.topic = topic                 # Тема обращения
        self.created_at = created_at       # Время создания
        self.status = self.STATUS_OPEN
        self.closed_at = None
        self.csat = None                   # Оценка 1-5 (последняя, если чат переоткрывался)
        self.messages = []                 # Список сообщений: [{author, name, text, time}]
        # Добавляем первое сообщение пользователя, если передано
        if first_message:
            self.add_message("user", first_message, created_at)

    @property
    def is_queued(self):
        """Чат в очереди: открыт, но оператор ещё не назначен."""
        return self.status == self.STATUS_OPEN and self.operator is None

    @property
    def is_closed(self):
        """Чат закрыт оператором."""
        return self.status == self.STATUS_CLOSED

    def add_message(self, author_role, text, time=None):
        """Добавить сообщение в чат (автор: 'user' или 'operator')."""
        time = time or datetime.now()
        if author_role == "user":
            name = self.user.full_name
        elif author_role == "operator":
            name = self.operator.full_name if self.operator else "система"
        else:
            name = "система"
        self.messages.append({"author": author_role, "name": name,
                              "text": text, "time": time})

    def close(self, now=None):
        """Закрыть чат оператором."""
        if self.is_closed:
            raise ValueError(f"Чат #{self.chat_id} уже закрыт")
        self.status = self.STATUS_CLOSED
        self.closed_at = now or datetime.now()

    def rate(self, score):
        """Оценить чат (CSAT 1-5). Последняя оценка перезаписывает предыдущую."""
        if not self.is_closed:
            raise ValueError(
                f"Чат #{self.chat_id} ещё не закрыт оператором — оценка невозможна")
        if not 1 <= score <= 5:
            raise ValueError("CSAT должен быть целым числом от 1 до 5")
        self.csat = score

    def to_dict(self):
        """Сериализация чата в словарь для JSON-экспорта."""
        return {
            "chat_id": self.chat_id,
            "topic": self.topic,
            "status": self.status,
            "operator_assigned": self.operator is not None,
            "user": {"id": self.user.person_id, "full_name": self.user.full_name},
            "operator": (
                {"id": self.operator.person_id, "full_name": self.operator.full_name}
                if self.operator else None
            ),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "closed_at": (self.closed_at.strftime("%Y-%m-%d %H:%M:%S")
                          if self.closed_at else None),
            "csat": self.csat,
            "messages": [
                {"author": m["author"], "name": m["name"], "text": m["text"],
                 "time": m["time"].strftime("%Y-%m-%d %H:%M:%S")}
                for m in self.messages
            ],
        }

    def __repr__(self):
        return (f"<Chat #{self.chat_id} [{self.status}] "
                f"user={self.user.person_id} op="
                f"{self.operator.person_id if self.operator else None} "
                f"csat={self.csat}>")
