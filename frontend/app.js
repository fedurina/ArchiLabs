const API_BASE = "/api/v1";
const AUTH_HEADER = { "Authorization": "Bearer demo-token" };

const els = {
  // Rooms list
  btnRooms: document.getElementById("btnRooms"),
  btnRoomsCopy: document.getElementById("btnRoomsCopy"),
  outRooms: document.getElementById("outRooms"),
  roomsStatus: document.getElementById("roomsStatus"),
  roomsTime: document.getElementById("roomsTime"),

  // Create room
  roomNumber: document.getElementById("roomNumber"),
  roomFloor: document.getElementById("roomFloor"),
  roomType: document.getElementById("roomType"),
  roomStatus: document.getElementById("roomStatus"),
  btnCreateRoom: document.getElementById("btnCreateRoom"),
  btnCreateRoomRandom: document.getElementById("btnCreateRoomRandom"),
  outCreateRoom: document.getElementById("outCreateRoom"),
  createRoomStatus: document.getElementById("createRoomStatus"),
  createRoomTime: document.getElementById("createRoomTime"),

  // Create booking
  guestId: document.getElementById("guestId"),
  bookingRoomId: document.getElementById("bookingRoomId"),
  checkIn: document.getElementById("checkIn"),
  checkOut: document.getElementById("checkOut"),
  btnCreateBooking: document.getElementById("btnCreateBooking"),
  btnBookingCopy: document.getElementById("btnBookingCopy"),
  outCreateBooking: document.getElementById("outCreateBooking"),
  createBookingStatus: document.getElementById("createBookingStatus"),
  createBookingTime: document.getElementById("createBookingTime"),

  toast: document.getElementById("toast")
};

function nowISODate() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function setDefaultDates() {
  const inD = new Date();
  const outD = new Date();
  outD.setDate(outD.getDate() + 3);
  els.checkIn.value = nowISODate();
  const pad = (n) => String(n).padStart(2, "0");
  els.checkOut.value = `${outD.getFullYear()}-${pad(outD.getMonth() + 1)}-${pad(outD.getDate())}`;
}

function pretty(v) {
  return JSON.stringify(v, null, 2);
}

function setPill(el, kind, text) {
  el.classList.remove("ok", "err");
  if (kind === "ok") el.classList.add("ok");
  if (kind === "err") el.classList.add("err");
  el.textContent = text;
}

function setTime(el, ms) {
  el.textContent = ms != null ? `${ms} ms` : "—";
}

function toast(kind, title, msg) {
  const item = document.createElement("div");
  item.className = `toast-item ${kind}`;
  item.innerHTML = `<strong>${title}</strong><div>${msg}</div>`;
  els.toast.appendChild(item);
  setTimeout(() => item.remove(), 2600);
}

async function apiFetch(path, options = {}) {
  const started = performance.now();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...AUTH_HEADER,
      ...(options.headers || {})
    }
  });
  const ms = Math.round(performance.now() - started);

  const contentType = res.headers.get("content-type") || "";
  let bodyText = null;
  let bodyJson = null;

  try {
    if (contentType.includes("application/json")) {
      bodyJson = await res.json();
    } else {
      bodyText = await res.text();
    }
  } catch (e) {
    // fallback
    bodyText = await res.text().catch(() => "");
  }

  if (!res.ok) {
    const detail = bodyJson?.detail ? JSON.stringify(bodyJson.detail) : (bodyText || "Unknown error");
    const err = new Error(`HTTP ${res.status}: ${detail}`);
    err.status = res.status;
    err.payload = bodyJson ?? bodyText;
    err.ms = ms;
    throw err;
  }

  return { status: res.status, ms, data: bodyJson ?? bodyText };
}

async function loadRooms() {
  setPill(els.roomsStatus, null, "Загрузка…");
  try {
    const r = await apiFetch("/rooms", { method: "GET" });
    els.outRooms.textContent = pretty(r);
    setPill(els.roomsStatus, "ok", `${r.status} OK`);
    setTime(els.roomsTime, r.ms);
  } catch (e) {
    els.outRooms.textContent = pretty({ error: String(e), payload: e.payload ?? null });
    setPill(els.roomsStatus, "err", `${e.status || "ERR"} Ошибка`);
    setTime(els.roomsTime, e.ms);
    toast("err", "Rooms — ошибка", e.message);
  }
}

function makeRoomNumberUnique() {
  // делает номер уникальным, чтобы не ловить 409
  const suffix = String(Date.now()).slice(-4);
  const base = els.roomNumber.value.replace(/\D/g, "").slice(0, 2) || "30";
  els.roomNumber.value = `${base}${suffix}`;
  toast("ok", "Номер обновлён", `Поставила уникальный номер: ${els.roomNumber.value}`);
}

async function createRoom() {
  setPill(els.createRoomStatus, null, "Отправка…");
  try {
    const payload = {
      number: String(els.roomNumber.value || "").trim(),
      floor: Number(els.roomFloor.value),
      room_type: els.roomType.value,
      status: els.roomStatus.value
    };

    const r = await apiFetch("/rooms", { method: "POST", body: JSON.stringify(payload) });
    els.outCreateRoom.textContent = pretty(r);
    setPill(els.createRoomStatus, "ok", `${r.status} Created`);
    setTime(els.createRoomTime, r.ms);

    // авто-подстановка roomId в booking
    const roomId = r.data?.id;
    if (roomId) {
      els.bookingRoomId.value = roomId;
      toast("ok", "Номер создан", `roomId подставлен в бронирование`);
    } else {
      toast("err", "Номер создан", "Но id не найден в ответе");
    }

    // обновим список, чтобы было видно сразу
    await loadRooms();
  } catch (e) {
    els.outCreateRoom.textContent = pretty({ error: String(e), payload: e.payload ?? null });
    setPill(els.createRoomStatus, "err", `${e.status || "ERR"} Ошибка`);
    setTime(els.createRoomTime, e.ms);

    if (e.status === 409) {
      toast("err", "Конфликт (409)", "Похоже, номер с таким Number уже существует. Нажми «Сделать номер уникальным».");
    } else {
      toast("err", "Rooms — ошибка", e.message);
    }
  }
}

async function createBooking() {
  setPill(els.createBookingStatus, null, "Отправка…");
  try {
    const payload = {
      guest_id: Number(els.guestId.value),
      room_id: String(els.bookingRoomId.value || "").trim(),
      check_in_date: els.checkIn.value,
      check_out_date: els.checkOut.value
    };

    const r = await apiFetch("/bookings", { method: "POST", body: JSON.stringify(payload) });
    els.outCreateBooking.textContent = pretty(r);
    setPill(els.createBookingStatus, "ok", `${r.status} Created`);
    setTime(els.createBookingTime, r.ms);
    toast("ok", "Бронирование создано", `bookingId: ${r.data?.id || "—"}`);
  } catch (e) {
    els.outCreateBooking.textContent = pretty({ error: String(e), payload: e.payload ?? null });
    setPill(els.createBookingStatus, "err", `${e.status || "ERR"} Ошибка`);
    setTime(els.createBookingTime, e.ms);

    if (e.status === 422) {
      toast("err", "Ошибка данных (422)", "Проверь даты и что Room ID заполнен (UUID).");
    } else {
      toast("err", "Booking — ошибка", e.message);
    }
  }
}

async function copyFromEl(preEl) {
  const text = preEl.textContent || "";
  try {
    await navigator.clipboard.writeText(text);
    toast("ok", "Скопировано", "JSON скопирован в буфер обмена");
  } catch {
    toast("err", "Не удалось скопировать", "Разреши доступ к буферу обмена в браузере");
  }
}

els.btnRooms.addEventListener("click", loadRooms);
els.btnCreateRoom.addEventListener("click", createRoom);
els.btnCreateRoomRandom.addEventListener("click", makeRoomNumberUnique);
els.btnRoomsCopy.addEventListener("click", () => copyFromEl(els.outRooms));
els.btnBookingCopy.addEventListener("click", () => copyFromEl(els.outCreateBooking));
els.btnCreateBooking.addEventListener("click", createBooking);

// init
setDefaultDates();
loadRooms();