/* ---- Modal helpers ---- */

function openModal(date) {
  document.getElementById("event-form").reset();
  document.getElementById("event-date").value = date;
  document.getElementById("create-heading").textContent = "New Event — " + date;
  document.getElementById("event-modal").classList.remove("hidden");
  document.getElementById("event-title").focus();
}

function closeModal() {
  document.getElementById("event-modal").classList.add("hidden");
}

function openDetailModal() {
  document.getElementById("detail-modal").classList.remove("hidden");
}

function closeDetailModal() {
  document.getElementById("detail-modal").classList.add("hidden");
}

/* ---- Click delegation for day cells and event chips ---- */

document.addEventListener("click", function (e) {
  const chip = e.target.closest(".event-chip");
  if (chip) {
    e.stopPropagation();
    const eventId = chip.dataset.eventId;
    openDetailModal();
    htmx.ajax("GET", "/events/" + eventId, {
      target: "#detail-content",
      swap: "innerHTML",
    });
    return;
  }

  const cell = e.target.closest(".day-cell");
  if (cell && containerContains(cell)) {
    const date = cell.dataset.date;
    if (date) openModal(date);
  }
});

function containerContains(el) {
  const container = document.getElementById("calendar-container");
  return container && container.contains(el);
}

/* ---- HTMX: close modals after calendar swap ---- */

document.addEventListener("htmx:afterSwap", function (e) {
  if (e.detail.target && e.detail.target.id === "calendar-container") {
    closeModal();
    closeDetailModal();
  }
});
