const FAKE_EVENTS = [
  { id: "f1", title: "Dinner at Sushi Spot", date: "2026-07-10", time: "19:00", description: "Birthday dinner for Mike" },
  { id: "f2", title: "Movie Night", date: "2026-07-12", time: "20:00", description: "New Marvel movie at the IMAX" },
  { id: "f3", title: "Hiking Trip", date: "2026-07-15", time: "08:00", description: "Trail run at Mt. Tam" },
  { id: "f4", title: "Game Night", date: "2026-07-20", time: "18:00", description: "Board games at Alex's place" },
  { id: "f5", title: "Farmers Market", date: "2026-07-25", time: "09:00", description: "Weekly farmers market run" },
  { id: "f6", title: "Beach Day", date: "2026-08-03", time: "11:00", description: "Santa Cruz beach trip with the crew" },
  { id: "f7", title: "Concert in the Park", date: "2026-08-08", time: "21:00", description: "Outdoor concert at Golden Gate Park" },
  { id: "f8", title: "Book Club", date: "2026-06-28", time: "15:00", description: "Discussing 'Project Hail Mary'" },
  { id: "f9", title: "Brunch", date: "2026-07-05", time: "10:30", description: "Bottomless mimosas at Cafe Flora" },
  { id: "f10", title: "Tennis Match", date: "2026-07-08", time: "07:00", description: "Doubles match at the club" },
];

let selectedEventId = null;

/* ---- localStorage helpers ---- */

function seedEvents() {
  if (!localStorage.getItem("fc_events_seeded")) {
    localStorage.setItem("fc_events", JSON.stringify(FAKE_EVENTS));
    localStorage.setItem("fc_events_seeded", "true");
  }
}

function getEvents() {
  try {
    return JSON.parse(localStorage.getItem("fc_events")) || [];
  } catch {
    return [];
  }
}

function saveEvents(events) {
  localStorage.setItem("fc_events", JSON.stringify(events));
}

function generateId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/* ---- Render events into the calendar grid ---- */

function renderEvents() {
  const container = document.getElementById("calendar-container");
  if (!container) return;
  const cells = container.querySelectorAll(".day-cell");
  const events = getEvents();

  cells.forEach((cell) => {
    const date = cell.dataset.date;
    if (!date) return;

    const oldEvents = cell.querySelector(".events");
    if (oldEvents) oldEvents.remove();

    const dayEvents = events.filter((e) => e.date === date);
    if (dayEvents.length === 0) return;

    const wrapper = document.createElement("div");
    wrapper.className = "events";

    dayEvents.forEach((ev) => {
      const chip = document.createElement("div");
      chip.className = "event-chip";
      chip.textContent = ev.title;
      chip.dataset.eventId = ev.id;
      wrapper.appendChild(chip);
    });

    cell.appendChild(wrapper);
  });
}

/* ---- Modal helpers ---- */

function openModal(date) {
  document.getElementById("event-date").value = date;
  document.querySelector(".modal-heading").textContent = "New Event — " + date;
  document.getElementById("event-form").reset();
  document.getElementById("event-form").querySelector("[name='date']").value = date;
  document.getElementById("event-modal").classList.remove("hidden");
  document.getElementById("event-title").focus();
}

function closeModal() {
  document.getElementById("event-modal").classList.add("hidden");
}

function showEventDetail(event) {
  selectedEventId = event.id;
  document.getElementById("detail-title").textContent = event.title;
  document.getElementById("detail-date").innerHTML = "<strong>Date:</strong> " + event.date;
  document.getElementById("detail-time").innerHTML = event.time
    ? "<strong>Time:</strong> " + event.time
    : "<strong>Time:</strong> —";
  document.getElementById("detail-desc").innerHTML = event.description
    ? "<strong>Description:</strong> " + event.description
    : "";
  document.getElementById("detail-modal").classList.remove("hidden");
}

function closeDetailModal() {
  selectedEventId = null;
  document.getElementById("detail-modal").classList.add("hidden");
}

function deleteEvent() {
  if (!selectedEventId) return;
  let events = getEvents().filter((e) => e.id !== selectedEventId);
  saveEvents(events);
  closeDetailModal();
  renderEvents();
}

/* ---- Event form submission ---- */

document.addEventListener("DOMContentLoaded", function () {
  seedEvents();
  renderEvents();

  const form = document.getElementById("event-form");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const date = form.querySelector("[name='date']").value;
    const title = form.querySelector("[name='title']").value.trim();
    const time = form.querySelector("[name='time']").value;
    const desc = form.querySelector("[name='description']").value.trim();

    if (!title) return;

    const events = getEvents();
    events.push({
      id: generateId(),
      title: title,
      date: date,
      time: time,
      description: desc,
    });
    saveEvents(events);
    closeModal();
    renderEvents();
  });
});

/* ---- HTMX: re-render events after month navigation ---- */

document.addEventListener("htmx:afterSwap", function (event) {
  if (event.detail && event.detail.target && event.detail.target.id === "calendar-container") {
    renderEvents();
  }
});

/* ---- Event delegation for day cells and chips ---- */

document.addEventListener("click", function (e) {
  const container = document.getElementById("calendar-container");
  if (!container) return;

  const chip = e.target.closest(".event-chip");
  if (chip) {
    e.stopPropagation();
    const eventId = chip.dataset.eventId;
    const events = getEvents();
    const ev = events.find((e) => e.id === eventId);
    if (ev) showEventDetail(ev);
    return;
  }

  const cell = e.target.closest(".day-cell");
  if (cell && container.contains(cell)) {
    const date = cell.dataset.date;
    if (date) openModal(date);
  }
});
