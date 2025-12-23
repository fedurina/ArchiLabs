## 1. Диаграмма контейнеров

Для ЛР3 переиспользуется диаграмма контейнеров из ЛР2, но явно выделяется контейнер, который детализируется на уровне компонентов и кода — **«Сервер прикладной логики»** (Backend / REST API). Вариант использования **«Гость бронирует конкретный номер»** реализуется именно через него.

* Гость работает через **веб-приложение для гостей**.
* Веб-приложение обращается к **серверу прикладной логики**.
* Сервер работает с **базой данных** и публикует события в **брокер сообщений**.
* События подхватывает **сервис интеграций**, который общается с **существующей системой бронирования** и **системой умных замков**.

<img width="1360" height="970" alt="dagram3 1" src="https://github.com/user-attachments/assets/4e7dd0b5-064e-4488-9353-512bfa57a2e2" />

Детализируется контейнер **«Сервер прикладной логики»**. На диаграмме также показаны внешние элементы из диаграммы контейнеров, с которыми он взаимодействует: **База данных**, **Брокер сообщений**, **Сервис интеграций**.

Именно компоненты этого сервера будут частично реализованы в коде.

* Контроллеры API — принимают HTTP-запросы от клиентских приложений.
* Модуль аутентификации и прав доступа — проверяет пользователя и его роль.
* Сервис бронирований — реализует сценарий «создать/изменить/отменить бронирование», проверяет возможность размещения.
* Сервис номерного фонда и статусов — отвечает за проверку состояния номера (доступен или нет на заданные даты).
* Сервис задач уборки и обслуживания — создаёт и ведёт задачи уборки и техобслуживания (в этой работе в коде не детализируется, но остается на диаграмме для целостности).
* Слой доступа к данным (репозитории) — выполняет чтение и запись сущностей в базу данных.
* Публикатор событий — формирует доменные события и отправляет их в брокер сообщений.
* Внутренний фасад интеграций — единая точка взаимодействия с сервисом интеграций.

<img width="1166" height="1206" alt="diagram3 2" src="https://github.com/user-attachments/assets/aa5f0271-764d-414a-a93e-7e89e9e54393" />

## 3. Диаграмма последовательностей

### 3.1. Вариант использования

Сценарий: гость через веб-приложение бронирует конкретный номер.

1. Гость выбирает даты и номер на веб-странице и нажимает «Забронировать».
2. Веб-приложение отправляет запрос на сервер.
3. Контроллер проверяет авторизацию, передаёт запрос в сервис бронирований.
4. Сервис бронирований проверяет доступность номера через сервис номерного фонда.
5. Сохраняется запись о бронировании в базе данных.
6. Публикуется событие «Бронирование создано» в брокер сообщений.
7. Сервис интеграций (за пределами этой диаграммы) позже синхронизирует бронь с внешней системой.

<img width="2040" height="855" alt="diagram3 3" src="https://github.com/user-attachments/assets/0a5ffe3c-a4e6-4c57-829a-98e65f37a7e8" />

## 4. Модель БД (диаграмма классов UML)

* **Guest (Гость)** — пользователь, который делает бронирования.
* **Room (Номер)** — конкретный номер в отеле.
* **RoomType (Тип номера)** — стандартный / комфорт / люкс и т.п.
* **Booking (Бронирование)** — факт бронирования конкретного номера конкретным гостем на период.
* **HousekeepingTask (Задача уборки)** — задача по уборке или обслуживанию номера.
* **StaffMember (Сотрудник)** — сотрудник отеля (уборка/техслужба), которому могут назначаться задачи.

<img width="1015" height="506" alt="diagrram3 4" src="https://github.com/user-attachments/assets/ce69d44b-c2d0-49c5-bc3e-d0d249f706ad" />


## 5. Применение основных принципов разработки (KISS, YAGNI, DRY, SOLID)

### 5.1. KISS — простой контроллер

контроллер делает минимум — проверка авторизации и делегирование в сервис

```python
from dataclasses import dataclass
from datetime import date
from typing import Protocol, List


@dataclass
class CreateBookingRequest:
    room_id: int
    check_in_date: date
    check_out_date: date


@dataclass
class BookingResponse:
    id: int
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: date

    @classmethod
    def from_domain(cls, booking: "Booking") -> "BookingResponse":
        return cls(
            id=booking.id,
            guest_id=booking.guest_id,
            room_id=booking.room_id,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
        )


class AuthService:
    """Простейший сервис аутентификации (заглушка)"""

    def get_guest_id_from_token(self, token: str) -> int:
        # проверка JWT/сессии
        # для примера вернём фиксированный id
        return 42


class BookingController:
    """KISS контроллер максимально простой"""

    def __init__(self, booking_service: "BookingService", auth_service: AuthService):
        self._booking_service = booking_service
        self._auth_service = auth_service

    def create_booking(self, request: CreateBookingRequest, auth_token: str) -> BookingResponse:
        # 1. Достаём гостя из токена
        guest_id = self._auth_service.get_guest_id_from_token(auth_token)
        # 2. Делегируем бизнес-логику в сервис
        booking = self._booking_service.create_booking(
            guest_id=guest_id,
            room_id=request.room_id,
            check_in=request.check_in_date,
            check_out=request.check_out_date,
        )
        # 3. Преобразуем доменную модель в DTO/ответ
        return BookingResponse.from_domain(booking)
```

**KISS**
Контроллер не лезет в БД, не публикует события, не проверяет доступность номера — он только связывает запрос, аутентификацию и сервис бронирований

---

### 5.2. Доменные модели и интерфейсы (для SOLID / DIP)

```python
@dataclass
class Booking:
    id: int
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: date


class BookingRepository(Protocol):
    """репозиторий бронирований (DIP, OCP)"""

    def save(self, booking: Booking) -> Booking:
        ...

    def find_bookings_for_room(self, room_id: int, check_in: date, check_out: date) -> List[Booking]:
        ...


class DomainEvent:
    """простейшее доменное событие"""
    pass


@dataclass
class BookingCreatedEvent(DomainEvent):
    booking: Booking


class DomainEventPublisher(Protocol):
    """публикация доменных событий (DIP)."""

    def publish(self, event: DomainEvent) -> None:
        ...
```

Пример простой in-memory реализации репозитория

```python
class InMemoryBookingRepository(BookingRepository):
    def __init__(self) -> None:
        self._items: List[Booking] = []
        self._next_id: int = 1

    def save(self, booking: Booking) -> Booking:
        if booking.id == 0:
            booking.id = self._next_id
            self._next_id += 1
        self._items.append(booking)
        return booking

    def find_bookings_for_room(self, room_id: int, check_in: date, check_out: date) -> List[Booking]:
        result = []
        for b in self._items:
            if b.room_id != room_id:
                continue
            # пересечение интервалов дат
            if not (b.check_out_date <= check_in or b.check_in_date >= check_out):
                result.append(b)
        return result
```

---

### 5.3. DRY + YAGNI + часть SOLID: сервис проверки доступности номера

```python
class InvalidDateRangeException(Exception):
    pass


class RoomAvailabilityService:
    """Проверка доступности номера"""

    def __init__(self, booking_repository: BookingRepository) -> None:
        self._booking_repository = booking_repository

    def is_room_available(self, room_id: int, check_in: date, check_out: date) -> bool:
        self._validate_dates(check_in, check_out)

        existing = self._booking_repository.find_bookings_for_room(room_id, check_in, check_out)
        return len(existing) == 0

    # DRY: общая проверка дат вынесена в отдельный метод
    def _validate_dates(self, check_in: date, check_out: date) -> None:
        if check_in is None or check_out is None or check_in >= check_out:
            raise InvalidDateRangeException(f"Некорректный диапазон дат: {check_in}–{check_out}")
```

**DRY**
Проверка диапазона дат написана один раз в `_validate_dates` и переиспользуется, а не копируется в разные методы.

**YAGNI**
Сервис только проверяет доступность номера по датам. Никаких “цен”, “предоплат”, “прогнозов спроса” — только то, что реально нужно для сценария.

---

### 5.4. YAGNI + SOLID: сервис бронирований

```python
class RoomNotAvailableException(Exception):
    pass


class BookingService:
    """
    Сервис бронирований:
    - использует RoomAvailabilityService
    - сохраняет бронирование
    - публикует событие
    """

    def __init__(
        self,
        room_availability_service: RoomAvailabilityService,
        booking_repository: BookingRepository,
        event_publisher: DomainEventPublisher,
    ) -> None:
        self._room_availability_service = room_availability_service
        self._booking_repository = booking_repository
        self._event_publisher = event_publisher

    def create_booking(self, guest_id: int, room_id: int, check_in: date, check_out: date) -> Booking:
        if not self._room_availability_service.is_room_available(room_id, check_in, check_out):
            raise RoomNotAvailableException(
                f"Номер {room_id} недоступен на даты {check_in}–{check_out}"
            )

        booking = Booking(
            id=0,
            guest_id=guest_id,
            room_id=room_id,
            check_in_date=check_in,
            check_out_date=check_out,
        )
        saved_booking = self._booking_repository.save(booking)

        self._event_publisher.publish(BookingCreatedEvent(saved_booking))

        return saved_booking
```

**YAGNI**
Реализован только метод `create_booking`, который нужен для выбранного use case. Нет методов перепланировок, переноса, частичных оплат и т.п.

**SOLID**

* **S (Single Responsibility)**:
  `BookingService` отвечает только за правила бронирования и публикацию события, не занимается HTTP, SQL и т.д.
* **D (Dependency Inversion)**:
  сервис зависит от `BookingRepository` и `DomainEventPublisher`, а не от конкретных классов.

---

### 5.5. SOLID: простой публикатор событий

```python
class SimpleEventPublisher(DomainEventPublisher):
    """публикатор событий"""

    def publish(self, event: DomainEvent) -> None:
        # отправка в брокер сообщений
        # для примера просто выводим в лог/консоль.
        print(f"[EVENT] {event}")
```

**SOLID (OCP / DIP)**

* Можно заменить `SimpleEventPublisher` на реализацию, которая отправляет данные в RabbitMQ / Kafka, не меняя кода `BookingService`.
* Сервис бронирований программирует против интерфейса `DomainEventPublisher`, а не против `print`.

---

### 5.6. Небольшой пример "склейки" (композиция)

```python
def build_application() -> BookingController:
    booking_repo = InMemoryBookingRepository()
    room_availability = RoomAvailabilityService(booking_repo)
    event_publisher = SimpleEventPublisher()
    booking_service = BookingService(room_availability, booking_repo, event_publisher)
    auth_service = AuthService()

    controller = BookingController(booking_service, auth_service)
    return controller
```


## 6. Дополнительные принципы разработки 

### 6.1. BDUF (Big Design Up Front)

Идея BDUF в том, чтобы как можно более подробно спроектировать всю систему заранее: продумать все уровни, все сценарии, все сущности — ещё до начала активной разработки.

В нашем случае мы действительно делаем часть работы «вперёд»: рисуем C4-диаграммы, продумываем архитектуру, описываем модель БД. Но при этом мы не пытаемся заранее распланировать абсолютно всё поведение системы на годы вперёд.

Система создаётся для высококлассных курортов, где требования легко могут меняться после первых сезонов эксплуатации: владельцы отелей могут захотеть новые отчёты, новые сценарии уборки, другие интеграции. Если пытаться «зарисовать всё идеально» до начала разработки, есть риск потратить много времени на проектирование функций, которые так и не пригодятся.

**Вывод:**
Мы используем BDUF в умеренном виде: проектируем общую архитектуру и ключевые сущности, но не стараемся заранее проработать все детали. Оставляем пространство для изменений после первых итераций и обратной связи от реальной эксплуатации.

### 6.2. SoC (Separation of Concerns)

Принцип разделения ответственности говорит: разные части системы должны отвечать за разные задачи, а не пытаться делать всё одновременно. Это помогает и в понимании системы, и в её поддержке.

В нашей системе этот принцип применяется довольно явно:

* на уровне архитектуры есть отдельные контейнеры: сервер прикладной логики, сервис интеграций, клиентские приложения, база данных, брокер сообщений;
* в коде разделены слои: контроллеры, доменные сервисы, репозитории, адаптеры для внешних систем.

Например, сервис интеграций занимается только обменом с внешними системами и не знает, как рисуется UI или как пользователь нажимает кнопку «Забронировать». А `BookingService` не отвечает ни за HTTP, ни за SQL — он работает с абстракциями репозитория и публикатора событий, не привязываясь к конкретной инфраструктуре.

**Вывод:**
SoC — один из базовых принципов, на которых строится архитектура этой системы: и диаграммы, и код организованы так, чтобы разные части решали разные задачи и не «перемешивали» ответственности.


### 6.3. MVP (Minimum Viable Product)

MVP — это подход, при котором сначала делается минимально жизнеспособная версия продукта: только те функции, без которых система не имеет смысла, но которые уже можно показать пользователям и получить от них обратную связь.

Для нашего проекта это вполне естественный путь. К началу пикового сезона отелю важна не «идеальная» система, а та, которая умеет:

* искать и показывать номера,
* оформлять бронирование,
* работать с мобильными ключами,
* хотя бы в базовом виде поддерживать задачи уборки.

А вот сложные аналитические отчёты, продвинутая оптимизация расписания уборок, дополнительные сценарии интеграций можно внедрять уже после того, как первая версия заработает в реальных условиях и станет понятно, что действительно нужно пользователям.

**Вывод:**
Система целенаправленно строится по принципам MVP: в первую очередь реализуются критически важные функции, позволяющие пережить пиковый сезон и собрать реальные отзывы, а дополнительные возможности добавляются позже, по мере необходимости.

### 6.4. PoC (Proof of Concept)

PoC — это небольшой эксперимент, который позволяет проверить, «живая» ли вообще идея или технология: можно ли реально интегрироваться с конкретным сервисом, работает ли протокол, адекватны ли задержки и т.п.

В нашем проекте PoC особенно актуален для самых рискованных мест — интеграций:

* с системой умных замков (важно убедиться, что мы можем надёжно выдавать и отзывать цифровые ключи);
* с уже существующей системой бронирования (нужно проверить, что её API действительно позволяет делать то, что требуется, и делает это достаточно быстро и стабильно).

Логичный шаг перед полноценной реализацией сервиса интеграций — собрать небольшой PoC: оформить одну тестовую бронь, отправить её во внешнюю систему, выдать и отозвать мобильный ключ, посмотреть, как ведут себя реальные API, какие ошибки возникают, какие задержки.

**Вывод:**
PoC имеет смысл использовать точечно, для самых рискованных частей системы (интеграции), а не для всей системы целиком. Это помогает снизить риски, не перегружая процесс разработки лишними экспериментами там, где всё и так понятно.
